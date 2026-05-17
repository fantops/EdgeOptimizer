"""Regression gates.

A profiler is only useful if its numbers gate something. Each gate takes a
profile-summary dict (the merged output of ``ep_tracker``, ``energy``, and
``system_sampler``) and a baseline dict, and returns a ``GateResult``.

The two gates that matter in cross-vendor NPU work:

* ``npu_op_pct`` per layer-class — catches silent EP fallback (the screen-region
  detector bug class in [day20]).
* energy-per-inference — catches DVFS / scheduler-stall regressions invisible
  at the ORT layer.

Both are configurable via ``configs/gates_config.json``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GateResult:
    name: str
    passed: bool
    observed: float
    threshold: float
    baseline: Optional[float] = None
    detail: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gate":      self.name,
            "passed":    self.passed,
            "observed":  self.observed,
            "threshold": self.threshold,
            "baseline":  self.baseline,
            "detail":    self.detail,
        }


@dataclass
class GateConfig:
    npu_op_pct_floor: float = 90.0           # overall NPU op % must clear this
    npu_op_pct_floor_per_class: float = 80.0 # per-layer-class floor
    energy_per_inference_max_j: float = 5.0  # absolute ceiling
    energy_regression_max_pct: float = 20.0  # vs baseline
    latency_regression_max_pct: float = 25.0 # vs baseline

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GateConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class RegressionGate:
    def __init__(self, config: Optional[GateConfig] = None) -> None:
        self.config = config or GateConfig()

    # ------------------------------------------------------------------
    def evaluate(self,
                 profile: Dict[str, Any],
                 baseline: Optional[Dict[str, Any]] = None) -> List[GateResult]:
        results: List[GateResult] = []
        results.append(self._gate_npu_pct(profile))
        results.extend(self._gate_per_class(profile))
        results.append(self._gate_energy_absolute(profile))
        if baseline:
            results.append(self._gate_energy_regression(profile, baseline))
            results.append(self._gate_latency_regression(profile, baseline))
        return results

    # ------------------------------------------------------------------
    def _gate_npu_pct(self, profile: Dict[str, Any]) -> GateResult:
        observed = float(profile.get("npu_op_pct", 0.0))
        threshold = self.config.npu_op_pct_floor
        return GateResult(
            name="npu_op_pct_overall",
            passed=observed >= threshold,
            observed=observed,
            threshold=threshold,
            detail="Fraction of ops scheduled on an NPU EP.",
        )

    def _gate_per_class(self, profile: Dict[str, Any]) -> List[GateResult]:
        out: List[GateResult] = []
        floor = self.config.npu_op_pct_floor_per_class
        for op, info in (profile.get("by_layer_class") or {}).items():
            pct = float(info.get("npu_pct", 0.0))
            out.append(GateResult(
                name=f"npu_op_pct_class[{op}]",
                passed=pct >= floor,
                observed=pct,
                threshold=floor,
                detail=f"NPU % for op-class {op}",
            ))
        return out

    def _gate_energy_absolute(self, profile: Dict[str, Any]) -> GateResult:
        energy = float(profile.get("energy_per_inference_j", 0.0))
        cap = self.config.energy_per_inference_max_j
        return GateResult(
            name="energy_per_inference_absolute",
            passed=energy <= cap if energy > 0 else True,
            observed=energy,
            threshold=cap,
            detail="Absolute joules per inference ceiling.",
        )

    def _gate_energy_regression(self, profile: Dict[str, Any],
                                baseline: Dict[str, Any]) -> GateResult:
        obs = float(profile.get("energy_per_inference_j", 0.0))
        base = float(baseline.get("energy_per_inference_j", 0.0))
        pct = ((obs - base) / base * 100.0) if base > 0 else 0.0
        return GateResult(
            name="energy_per_inference_regression",
            passed=pct <= self.config.energy_regression_max_pct,
            observed=pct,
            threshold=self.config.energy_regression_max_pct,
            baseline=base,
            detail="% increase in J/inference vs baseline.",
        )

    def _gate_latency_regression(self, profile: Dict[str, Any],
                                 baseline: Dict[str, Any]) -> GateResult:
        obs = float(profile.get("avg_inference_ms", 0.0))
        base = float(baseline.get("avg_inference_ms", 0.0))
        pct = ((obs - base) / base * 100.0) if base > 0 else 0.0
        return GateResult(
            name="latency_regression",
            passed=pct <= self.config.latency_regression_max_pct,
            observed=pct,
            threshold=self.config.latency_regression_max_pct,
            baseline=base,
            detail="% increase in mean inference latency vs baseline.",
        )
