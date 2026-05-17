"""EdgeOptimizer profiler package.

Platform-level NPU / inference profiler. Each submodule owns one of the four
signals tracked by the corporate-scale tool this is modelled on:

* ``ep_tracker``     — which ONNX Runtime Execution Provider actually ran each op
* ``energy``         — energy-per-inference (RAPL on Intel; powermetrics on macOS;
                        CrossMon as cross-platform fallback)
* ``system_sampler`` — CPU / Memory / GPU / NPU utilisation via the CrossMon
                        submodule (``tools/crossmon``)
* ``gates``          — regression gates (e.g. ``npu_op_pct`` per layer-class)
* ``version_matrix`` — EP × ORT × SDK × model-build version pinning + diff
"""

from .ep_tracker import EPAssignmentTracker
from .energy import EnergyAttributor
from .system_sampler import SystemSampler
from .gates import RegressionGate, GateResult
from .version_matrix import VersionMatrix

__all__ = [
    "EPAssignmentTracker",
    "EnergyAttributor",
    "SystemSampler",
    "RegressionGate",
    "GateResult",
    "VersionMatrix",
]
