#!/usr/bin/env python3
"""Agentic-CLI triage report generator.

Consumes one or two ``profile_cli`` run JSONs and emits a Markdown report
listing failed gates, the largest version-matrix diffs, and the EP-fallback
op classes most responsible for the regression. This is the "2-hour WPA
triage → 15-minute report" workflow referenced in the EdgeOptimizer narrative.

The intent is for this to be the deterministic backbone that a Copilot CLI
agent then narrates / hyperlinks. The hard data lives here; the LLM only
formats and prioritises.

Usage:

    python -m profiler.triage_report --run logs/run_b.json
    python -m profiler.triage_report --run logs/run_b.json --baseline logs/run_a.json -o report.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, os.path.dirname(_THIS_DIR))

from profiler.version_matrix import VersionMatrix


def _load(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _top_fallback_classes(run: Dict[str, Any], n: int = 5) -> List[Dict[str, Any]]:
    classes = (run.get("by_layer_class") or {}).items()
    ranked = sorted(classes, key=lambda kv: float(kv[1].get("npu_pct", 100)))
    out: List[Dict[str, Any]] = []
    for name, info in ranked[:n]:
        out.append({
            "op":      name,
            "npu_pct": info.get("npu_pct"),
            "ops":     info.get("ops_total"),
            "by_ep":   info.get("ops_by_ep"),
        })
    return out


def build_report(run: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# EdgeOptimizer triage report\n")
    lines.append(f"_Model: `{run.get('model','?')}`_\n")

    # 1. Gate status -------------------------------------------------------
    gates = run.get("gates") or []
    failed = [g for g in gates if not g.get("passed")]
    lines.append("## 1. Gate status\n")
    lines.append(f"- Total gates: **{len(gates)}**")
    lines.append(f"- Failed: **{len(failed)}**\n")
    if failed:
        lines.append("| Gate | Observed | Threshold | Baseline | Detail |")
        lines.append("|---|---:|---:|---:|---|")
        for g in failed:
            lines.append(
                f"| `{g['gate']}` | {g.get('observed')} | {g.get('threshold')} | "
                f"{g.get('baseline','—')} | {g.get('detail','')} |")
    lines.append("")

    # 2. Headline numbers --------------------------------------------------
    lines.append("## 2. Headline numbers\n")
    lines.append(f"- `npu_op_pct`: **{run.get('npu_op_pct','?')}**")
    lines.append(f"- `avg_inference_ms`: **{run.get('avg_inference_ms','?'):.2f}**"
                 if isinstance(run.get("avg_inference_ms"), (int, float))
                 else "- `avg_inference_ms`: ?")
    lines.append(f"- `energy_per_inference_j`: **{run.get('energy_per_inference_j','?')}** "
                 f"(source=`{run.get('energy_source','?')}`)\n")

    # 3. EP fallback worst offenders --------------------------------------
    fallbacks = _top_fallback_classes(run)
    if fallbacks:
        lines.append("## 3. Worst-fallback op classes\n")
        lines.append("| Op | NPU % | Total ops | By EP |")
        lines.append("|---|---:|---:|---|")
        for f in fallbacks:
            lines.append(f"| `{f['op']}` | {f['npu_pct']} | {f['ops']} | "
                         f"`{f['by_ep']}` |")
        lines.append("")

    # 4. Version-matrix diff ----------------------------------------------
    if baseline:
        lines.append("## 4. Version-matrix diff (baseline → run)\n")
        a = baseline.get("version_matrix") or {}
        b = run.get("version_matrix") or {}
        rows = VersionMatrix.diff(a, b)
        if not rows:
            lines.append("_No version-matrix differences detected._\n")
        else:
            lines.append("| Key | Before | After |")
            lines.append("|---|---|---|")
            for r in rows:
                lines.append(f"| `{r['key']}` | `{r['before']}` | `{r['after']}` |")
            lines.append("")

    # 5. Next actions ------------------------------------------------------
    lines.append("## 5. Suggested next actions\n")
    if failed:
        for g in failed:
            name = g["gate"]
            if name.startswith("npu_op_pct"):
                lines.append(f"- Investigate EP fallback — diff vendor compiler "
                             f"log for op classes in §3.")
            elif "energy" in name:
                lines.append("- Re-run with `--no-energy=false`; cross-check "
                             "against CrossMon GPU/NPU utilisation in §2.")
            elif "latency" in name:
                lines.append("- Bisect on the version-matrix diff rows in §4 "
                             "(EP / ORT / SDK / model build, one at a time).")
    else:
        lines.append("- All gates passed. Promote this run as the new baseline.\n")
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="edgeopt-triage")
    p.add_argument("--run", required=True, help="Run JSON to triage")
    p.add_argument("--baseline", default=None, help="Optional baseline JSON")
    p.add_argument("-o", "--out", default=None, help="Output Markdown path")
    args = p.parse_args(argv)
    run = _load(args.run)
    baseline = _load(args.baseline) if args.baseline else None
    md = build_report(run, baseline)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
