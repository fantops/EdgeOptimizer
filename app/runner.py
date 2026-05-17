"""Generic ONNX workload runner.

Loads any ONNX model through ``onnxruntime``, infers reasonable shapes for
its declared inputs (substituting ``1`` for symbolic / dynamic dims), and
runs ``N`` forward passes with synthetic numpy data.

This is what makes the profiler reusable for *other* applications — drop
any ``.onnx`` file in and you get the same four signals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import onnxruntime as ort


_DTYPE_MAP = {
    "tensor(float)":   np.float32,
    "tensor(float16)": np.float16,
    "tensor(double)":  np.float64,
    "tensor(int8)":    np.int8,
    "tensor(uint8)":   np.uint8,
    "tensor(int32)":   np.int32,
    "tensor(int64)":   np.int64,
    "tensor(bool)":    np.bool_,
}


@dataclass
class RunResult:
    iterations: int
    latencies_ms: List[float] = field(default_factory=list)
    input_shapes: Dict[str, List[int]] = field(default_factory=dict)
    providers: List[str] = field(default_factory=list)

    @property
    def avg_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0


def _resolve_shape(decl_shape: List[Any], default_dim: int = 1) -> List[int]:
    """Replace ``None`` / strings (symbolic dims) with ``default_dim``."""
    out: List[int] = []
    for d in decl_shape:
        if isinstance(d, int) and d > 0:
            out.append(d)
        else:
            out.append(default_dim)
    return out


def _synthetic_input(meta_dtype: str, shape: List[int],
                     vocab_size: int = 1000) -> np.ndarray:
    dtype = _DTYPE_MAP.get(meta_dtype, np.float32)
    if np.issubdtype(dtype, np.integer):
        # Likely token IDs / class indices — bound the range.
        return np.random.randint(0, vocab_size, size=shape, dtype=dtype)
    if dtype == np.bool_:
        return np.random.randint(0, 2, size=shape).astype(np.bool_)
    return np.random.rand(*shape).astype(dtype)


def run_onnx_synthetic(model_path: str,
                       iterations: int = 1,
                       providers: Optional[List[str]] = None,
                       session_options: Optional[ort.SessionOptions] = None,
                       seed: Optional[int] = 0,
                       seq_len: int = 16) -> RunResult:
    """Run ``iterations`` forward passes with synthetic inputs.

    Parameters
    ----------
    model_path : path to ``.onnx`` file.
    iterations : number of forward passes (for warm + measure).
    providers  : optional explicit EP list; ORT default otherwise.
    seq_len    : value substituted for symbolic sequence-length dims.
    """
    if seed is not None:
        np.random.seed(seed)

    so = session_options or ort.SessionOptions()
    sess = ort.InferenceSession(
        model_path,
        sess_options=so,
        providers=providers or ort.get_available_providers(),
    )

    feeds: Dict[str, np.ndarray] = {}
    input_shapes: Dict[str, List[int]] = {}
    for inp in sess.get_inputs():
        shape = _resolve_shape(inp.shape, default_dim=seq_len if "seq" in (inp.name or "").lower() else 1)
        feeds[inp.name] = _synthetic_input(inp.type, shape)
        input_shapes[inp.name] = shape

    latencies: List[float] = []
    for _ in range(max(iterations, 1)):
        t0 = time.perf_counter()
        sess.run(None, feeds)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    return RunResult(
        iterations=len(latencies),
        latencies_ms=latencies,
        input_shapes=input_shapes,
        providers=sess.get_providers(),
    )
