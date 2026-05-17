"""ONNX Runtime Execution Provider assignment tracker.

The single most important signal in cross-vendor NPU validation is **which EP
actually ran each op**. A silent fallback to the CPU EP looks identical at the
API level but costs 5-10× latency and 10-100× energy.

On a real platform-validation deployment this data comes from an ETW provider
hooked to ORT's ``SessionState`` events (Windows). For OSS / macOS we read what
ORT exposes through the public profiling JSON and reconstruct the same view.

Output schema (per session):

    {
      "model":        "<model name or path>",
      "providers":    ["QNNExecutionProvider", "CPUExecutionProvider"],
      "ops_total":    N,
      "ops_by_ep":    {"QNNExecutionProvider": n1, "CPUExecutionProvider": n2},
      "npu_op_pct":   float in [0, 100],
      "fallback_ops": [{"op": "MatMul", "from": "QNN", "to": "CPU"} ...],
      "by_layer_class": {"MatMul": {"npu_pct": 96.0, ...}, ...}
    }

``npu_op_pct`` is the headline number gated in regression — see ``gates.py``.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


# Map vendor EP name → "is this an NPU/accelerator EP?"
_NPU_EPS = {
    "QNNExecutionProvider",        # Qualcomm Hexagon HTP
    "OpenVINOExecutionProvider",   # Intel NPU / GPU
    "DmlExecutionProvider",        # AMD XDNA / Windows DirectML
    "VitisAIExecutionProvider",    # AMD Ryzen AI legacy
    "CoreMLExecutionProvider",     # Apple ANE (not a Copilot+ target but useful on dev box)
}


class EPAssignmentTracker:
    """Reconstruct per-op EP assignment from an ORT profiling JSON."""

    def __init__(self, npu_eps: Optional[Iterable[str]] = None) -> None:
        self.npu_eps = set(npu_eps) if npu_eps else set(_NPU_EPS)

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------
    @staticmethod
    def enable(session_options) -> None:
        """Turn on ORT profiling. Pass an ``onnxruntime.SessionOptions``.

        Kept as a static helper so callers don't have to import the tracker
        before constructing their session.
        """
        try:
            session_options.enable_profiling = True
        except AttributeError as exc:  # pragma: no cover - defensive
            raise TypeError("session_options must be onnxruntime.SessionOptions") from exc

    @staticmethod
    def end_and_collect(session) -> str:
        """Call ``session.end_profiling()`` and return the profile JSON path."""
        return session.end_profiling()

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------
    def summarise(self, profile_json_path: str, model_name: str = "") -> Dict[str, Any]:
        if not os.path.isfile(profile_json_path):
            raise FileNotFoundError(profile_json_path)

        with open(profile_json_path, encoding="utf-8") as fh:
            events = json.load(fh)

        ops_by_ep: Counter[str] = Counter()
        by_layer_class: Dict[str, Counter[str]] = defaultdict(Counter)
        fallback_ops: List[Dict[str, str]] = []
        providers_seen: set[str] = set()

        for ev in events:
            # ORT emits "kernel_time" events tagged with "provider" + "op_name".
            if not isinstance(ev, dict) or ev.get("cat") != "Node":
                continue
            args = ev.get("args") or {}
            ep = args.get("provider") or args.get("ep") or "Unknown"
            op = args.get("op_name") or ev.get("name") or "Unknown"
            providers_seen.add(ep)
            ops_by_ep[ep] += 1
            by_layer_class[op][ep] += 1

            # A fallback is any op that lives on the CPU EP while an NPU EP is in
            # the provider list — the assumption is: if you registered an NPU EP
            # you wanted that op on it.
            if ep == "CPUExecutionProvider":
                fallback_ops.append({"op": op, "from": "expected-NPU", "to": ep})

        total = sum(ops_by_ep.values()) or 1
        npu_ops = sum(c for ep, c in ops_by_ep.items() if ep in self.npu_eps)
        npu_op_pct = round(100.0 * npu_ops / total, 2)

        layer_class_summary: Dict[str, Dict[str, Any]] = {}
        for op, ep_counts in by_layer_class.items():
            op_total = sum(ep_counts.values()) or 1
            op_npu = sum(c for ep, c in ep_counts.items() if ep in self.npu_eps)
            layer_class_summary[op] = {
                "ops_total": op_total,
                "ops_by_ep": dict(ep_counts),
                "npu_pct": round(100.0 * op_npu / op_total, 2),
            }

        return {
            "model": model_name or os.path.basename(profile_json_path),
            "providers": sorted(providers_seen),
            "ops_total": total,
            "ops_by_ep": dict(ops_by_ep),
            "npu_op_pct": npu_op_pct,
            "fallback_ops": fallback_ops,
            "by_layer_class": layer_class_summary,
        }
