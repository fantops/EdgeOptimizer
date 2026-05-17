"""Workload runners for the profiler.

Two runners ship in-tree:

* ``run_onnx_synthetic`` — load any ONNX model, generate synthetic inputs
  from its declared input shapes, run one forward pass. **No tokenizer, no
  torch, no transformers required.** This is the default workload for
  ``profile_cli`` so the profiler stays reusable across arbitrary models.

* ``OnnxChatbot`` (in ``chatbot.py``) — kept as a sample real-world workload
  for ``main.py chat`` and for manual experiments. Optional dependency.
"""

from .runner import run_onnx_synthetic, RunResult

__all__ = ["run_onnx_synthetic", "RunResult"]
