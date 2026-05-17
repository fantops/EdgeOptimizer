#!/usr/bin/env python3
"""EdgeOptimizer profile CLI — workload-agnostic.

Profile **any** ONNX model across the four signals (EP assignment, energy,
system utilisation, version matrix) and gate the result against a baseline
+ config thresholds.

Example
-------

    # Generic: any ONNX model, synthetic inputs.
    python -m profiler.profile_cli \
        --model path/to/model.onnx \
        --iterations 10 \
        --baseline logs/baseline.json \
        --out logs/run.json

    # Specific EP (helpful on Windows with QNN / OpenVINO / DML installed):
    python -m profiler.profile_cli --model m.onnx --providers QNNExecutionProvider CPUExecutionProvider

Pass ``--no-energy``, ``--no-sampler``, or ``--no-profile`` to skip
individual collectors during dev.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Allow running both as module and as script.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, os.path.dirname(_THIS_DIR))

from profiler import (
    EPAssignmentTracker,
    EnergyAttributor,
    SystemSampler,
    RegressionGate,
    VersionMatrix,
)
from profiler.gates import GateConfig
from app.runner import run_onnx_synthetic


def _load_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="edgeopt-profile")
    p.add_argument("--model", required=True, help="Path to ONNX model")
    p.add_argument("--iterations", type=int, default=10,
                   help="Forward passes to run (default 10)")
    p.add_argument("--providers", nargs="+", default=None,
                   help="Explicit ORT EP list (e.g. QNNExecutionProvider CPUExecutionProvider)")
    p.add_argument("--seq-len", type=int, default=16,
                   help="Value to substitute for symbolic sequence-length dims")
    p.add_argument("--app", default=None,
                   help="App name passed to CrossMon (for app-scoped sampling)")
    p.add_argument("--duration", type=float, default=3.0,
                   help="Seconds of system sampling around the run")
    p.add_argument("--baseline", default=None, help="Path to baseline JSON")
    p.add_argument("--gates-config", default="configs/gates_config.json")
    p.add_argument("--out", default=None, help="Where to write the combined run JSON")
    p.add_argument("--no-energy", action="store_true")
    p.add_argument("--no-sampler", action="store_true")
    p.add_argument("--no-profile", action="store_true",
                   help="Skip ORT op-level profiling (EP assignment)")
    args = p.parse_args(argv)

    # 1. Version matrix --------------------------------------------------
    sampler = None if args.no_sampler else SystemSampler()
    vm = VersionMatrix.capture(
        model_path=args.model,
        crossmon_bin=sampler._locate_crossmon() if sampler else None,
    )

    # 2. Build a session with ORT profiling enabled ----------------------
    import onnxruntime as ort
    so = ort.SessionOptions()
    if not args.no_profile:
        EPAssignmentTracker.enable(so)

    # 3. Energy window opens ---------------------------------------------
    energy = None if args.no_energy else EnergyAttributor()
    if energy:
        energy.begin()

    # 4. Run the workload ------------------------------------------------
    run = run_onnx_synthetic(
        model_path=args.model,
        iterations=args.iterations,
        providers=args.providers,
        session_options=so,
        seq_len=args.seq_len,
    )

    # 5. Energy window closes + system sampling --------------------------
    energy_sample = energy.end() if energy else None
    samples = (sampler.sample_window(duration_s=args.duration, app_name=args.app)
               if sampler else [])

    # 6. EP-assignment summary (requires a session handle to end profiling)
    ep_summary: Dict[str, Any] = {}
    if not args.no_profile:
        # Re-open a tiny session just to call end_profiling on a new session
        # is not meaningful — instead, the runner already wrote a profiling
        # JSON during `sess.run`. We reconstruct the path from cwd:
        # ORT default profile name is `onnxruntime_profile_*.json`.
        import glob
        candidates = sorted(glob.glob("onnxruntime_profile_*.json"),
                            key=os.path.getmtime, reverse=True)
        if candidates:
            ep_summary = EPAssignmentTracker().summarise(
                candidates[0], model_name=os.path.basename(args.model))

    # 7. Build profile record -------------------------------------------
    record: Dict[str, Any] = {
        "model":                  args.model,
        "iterations":             run.iterations,
        "providers_used":         run.providers,
        "input_shapes":           run.input_shapes,
        "avg_inference_ms":       run.avg_ms,
        "min_inference_ms":       run.min_ms,
        "energy_per_inference_j": ((energy_sample.joules / run.iterations)
                                   if energy_sample and run.iterations else 0.0),
        "energy_source":          energy_sample.source if energy_sample else "skipped",
        "system_summary":         SystemSampler.summarise(samples) if samples else {},
        "version_matrix":         vm.to_dict(),
        **ep_summary,
    }

    # 8. Gates -----------------------------------------------------------
    gate_cfg_data = _load_json(args.gates_config) or {}
    gate_cfg = GateConfig.from_dict(gate_cfg_data.get("gates", {}))
    gate_results = RegressionGate(gate_cfg).evaluate(
        record, baseline=_load_json(args.baseline))
    record["gates"] = [g.as_dict() for g in gate_results]

    # 9. Output ----------------------------------------------------------
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
        print(f"Wrote {args.out}")

    failed = [g for g in gate_results if not g.passed]
    print(f"\nProviders: {record['providers_used']}")
    print(f"NPU op %:  {record.get('npu_op_pct', 'n/a')}")
    print(f"Latency:   avg {record['avg_inference_ms']:.2f} ms / "
          f"min {record['min_inference_ms']:.2f} ms ({record['iterations']} iters)")
    print(f"Energy:    {record['energy_per_inference_j']:.4f} J/inference "
          f"(source={record['energy_source']})")
    print(f"Gates:     {len(gate_results) - len(failed)}/{len(gate_results)} passed")
    for g in failed:
        print(f"  FAIL {g.name}: observed={g.observed} threshold={g.threshold}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
