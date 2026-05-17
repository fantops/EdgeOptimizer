"""Workload runners.

``run_onnx_synthetic`` — load any ONNX model, generate synthetic inputs
from its declared input shapes, run N forward passes. No tokenizer, no
torch, no transformers required. This is the workload primitive used by
the profiler.
"""

from .runner import run_onnx_synthetic, RunResult

__all__ = ["run_onnx_synthetic", "RunResult"]
