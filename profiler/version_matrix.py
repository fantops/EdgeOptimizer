"""Version matrix capture.

Cross-vendor NPU regressions almost always trace to one cell of a 4-D matrix:
``EP × ORT × SDK/driver × model-build``. Pinning that cell at the time of every
run is the first thing a triage engineer asks for.

This module captures what's reachable from a Python process. Driver/SDK
versions on Windows come from registry / DXCore on the corporate tool; here
we record what's importable and what shipped with the active venv.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VersionMatrix:
    captured_at: str = ""
    host: Dict[str, str] = field(default_factory=dict)
    python: Dict[str, str] = field(default_factory=dict)
    onnxruntime: Dict[str, Any] = field(default_factory=dict)
    packages: Dict[str, str] = field(default_factory=dict)
    model: Dict[str, Any] = field(default_factory=dict)
    crossmon: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    @classmethod
    def capture(cls, model_path: Optional[str] = None,
                crossmon_bin: Optional[str] = None) -> "VersionMatrix":
        from datetime import datetime
        vm = cls(captured_at=datetime.utcnow().isoformat() + "Z")

        vm.host = {
            "system":   platform.system(),
            "release":  platform.release(),
            "machine":  platform.machine(),
            "platform": platform.platform(),
        }
        vm.python = {
            "version":     sys.version.split()[0],
            "implementation": platform.python_implementation(),
        }

        # ORT details
        try:
            import onnxruntime as ort
            vm.onnxruntime = {
                "version":   ort.__version__,
                "providers": ort.get_available_providers(),
                "device":    ort.get_device(),
            }
        except ImportError:
            vm.onnxruntime = {"version": "not-installed"}

        # Tracked packages (best-effort)
        for pkg in ("numpy", "torch", "transformers", "psutil", "onnx"):
            try:
                mod = importlib.import_module(pkg)
                vm.packages[pkg] = getattr(mod, "__version__", "unknown")
            except ImportError:
                vm.packages[pkg] = "not-installed"

        if model_path and os.path.isfile(model_path):
            stat = os.stat(model_path)
            vm.model = {
                "path":      model_path,
                "size_mb":   round(stat.st_size / (1024 * 1024), 2),
                "mtime":     stat.st_mtime,
            }

        if crossmon_bin and os.path.isfile(crossmon_bin):
            sha = _git_sha(os.path.dirname(crossmon_bin))
            vm.crossmon = {"binary": crossmon_bin, "git_sha": sha or "unknown"}

        return vm

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "captured_at": self.captured_at,
            "host":        self.host,
            "python":      self.python,
            "onnxruntime": self.onnxruntime,
            "packages":    self.packages,
            "model":       self.model,
            "crossmon":    self.crossmon,
        }

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    # ------------------------------------------------------------------
    @staticmethod
    def diff(a: Dict[str, Any], b: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flat key-by-key diff. Returns rows where the value changed."""
        rows: List[Dict[str, Any]] = []

        def walk(prefix: str, va: Any, vb: Any) -> None:
            if isinstance(va, dict) and isinstance(vb, dict):
                for k in sorted(set(va) | set(vb)):
                    walk(f"{prefix}.{k}" if prefix else k, va.get(k), vb.get(k))
            elif va != vb:
                rows.append({"key": prefix, "before": va, "after": vb})

        walk("", a, b)
        return rows


def _git_sha(path: str) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None
