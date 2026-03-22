"""Configuration helpers for EdgeOptimizer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

_DEFAULT_OPTIMIZER = Path(__file__).resolve().parent.parent / "configs" / "optimizer_config.json"


class ConfigManager:
    """Loads JSON configs from disk (optimizer and experiments)."""

    def __init__(self, optimizer_config_path: Optional[os.PathLike[str]] = None):
        self.optimizer_config_path = Path(
            optimizer_config_path or _DEFAULT_OPTIMIZER
        )
        self._optimizer: Dict[str, Any] = {}
        if self.optimizer_config_path.is_file():
            with open(self.optimizer_config_path, encoding="utf-8") as f:
                self._optimizer = json.load(f)

    def get_optimizer_config(self) -> Dict[str, Any]:
        return dict(self._optimizer)


def get_config_manager(optimizer_config_path: Optional[os.PathLike[str]] = None) -> ConfigManager:
    return ConfigManager(optimizer_config_path)


def load_config(path: os.PathLike[str]) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
