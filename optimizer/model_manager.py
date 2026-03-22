"""Model path and lifecycle helpers (minimal; extend for your deployment)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class ModelManager:
    """Tracks default local ONNX path and tokenizer directory."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = Path(models_dir or Path("models"))
        self.default_onnx = self.models_dir / "model.onnx"

    def onnx_path(self) -> Path:
        return self.default_onnx


def get_model_manager(models_dir: Optional[Path] = None) -> ModelManager:
    return ModelManager(models_dir)
