"""CrossMon-backed system sampler.

The ``tools/crossmon`` submodule is a small C++17 console tool that captures
CPU / Memory / GPU (and an NPU stub) utilisation on Windows + macOS. We invoke
its release binary from Python and parse its file output.

Why call out to a separate C++ tool instead of just ``psutil``:

* psutil has no NPU view, and on macOS its GPU support is non-existent.
* CrossMon already implements WMI / IOKit per-platform; reinventing that in
  Python adds maintenance cost and platform skew.
* Keeping the sampler in a separate process means the EdgeOptimizer Python
  side doesn't take a perf hit from sampling its own inference run.

If the CrossMon binary isn't built, we fall back to ``psutil`` so unit tests
and CI don't require the C++ toolchain.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import List, Optional

import psutil


_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

# CMake places the binary differently on each platform / generator:
#   macOS Unix Makefiles : build/crossmon            (Debug -> build/Debug/crossmon)
#   Linux Unix Makefiles : build/crossmon
#   Windows MSVC         : build/Release/crossmon.exe  /  build/Debug/crossmon.exe
_CROSSMON_CANDIDATES = (
    os.path.join("tools", "crossmon", "build", "crossmon"),
    os.path.join("tools", "crossmon", "build", "Debug", "crossmon"),
    os.path.join("tools", "crossmon", "build", "Release", "crossmon.exe"),
    os.path.join("tools", "crossmon", "build", "Debug", "crossmon.exe"),
    os.path.join("tools", "crossmon", "build", "crossmon.exe"),
)


@dataclass
class SystemSample:
    timestamp: float
    cpu_pct: float = 0.0
    mem_mb: float = 0.0
    mem_pct: float = 0.0
    gpu_pcts: List[float] = field(default_factory=list)
    npu_pct: float = 0.0
    source: str = "psutil"

    @property
    def gpu_avg(self) -> float:
        if not self.gpu_pcts:
            return 0.0
        return sum(self.gpu_pcts) / len(self.gpu_pcts)


class SystemSampler:
    """Sample CPU/Mem/GPU/NPU at a fixed interval for a fixed duration."""

    def __init__(self, crossmon_bin: Optional[str] = None) -> None:
        self.crossmon_bin = crossmon_bin or self._locate_crossmon()

    @staticmethod
    def _locate_crossmon() -> Optional[str]:
        for rel in _CROSSMON_CANDIDATES:
            path = os.path.join(_REPO_ROOT, rel)
            if os.path.isfile(path):
                # os.access(.., X_OK) is unreliable on Windows; trust the
                # filename suffix / file existence instead.
                return path
        # Also accept a `crossmon` (or `crossmon.exe`) on PATH.
        return shutil.which("crossmon")

    # ------------------------------------------------------------------
    # CrossMon path
    # ------------------------------------------------------------------
    def sample_window(self, duration_s: float, interval_ms: int = 500,
                      app_name: Optional[str] = None,
                      out_path: Optional[str] = None) -> List[SystemSample]:
        """Sample for ``duration_s`` seconds. Returns parsed samples."""
        if self.crossmon_bin:
            samples = self._sample_with_crossmon(duration_s, interval_ms, app_name, out_path)
            if samples:
                return samples
        return self._sample_with_psutil(duration_s, interval_ms)

    # CrossMon parsing -------------------------------------------------
    _LINE_RE = re.compile(
        r"CPU:\s*(?P<cpu>[\d.]+)%.*?"
        r"Memory:\s*(?P<mem_mb>\d+)\s*MB\s*\((?P<mem_pct>[\d.]+)%\).*?"
        r"(?:GPUs?:\s*(?P<gpus>[\d.,\s%]+).*?)?"
        r"(?:NPU:.*?(?P<npu>[\d.]+)%)?",
        re.IGNORECASE,
    )

    def _sample_with_crossmon(self, duration_s: float, interval_ms: int,
                              app_name: Optional[str],
                              out_path: Optional[str]) -> List[SystemSample]:
        out_path = out_path or os.path.join(_REPO_ROOT, "logs", "crossmon_run.txt")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cmd = [self.crossmon_bin, "-i", str(interval_ms), "-o", out_path]
        if app_name:
            cmd.append(app_name)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        except (OSError, FileNotFoundError):
            return []
        time.sleep(duration_s)
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

        return self._parse_crossmon_file(out_path)

    def _parse_crossmon_file(self, path: str) -> List[SystemSample]:
        if not os.path.isfile(path):
            return []
        out: List[SystemSample] = []
        now = time.time()
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                m = self._LINE_RE.search(line)
                if not m:
                    continue
                gpus_raw = m.group("gpus") or ""
                gpu_pcts = [float(x.strip().rstrip("%"))
                            for x in gpus_raw.split(",")
                            if x.strip().rstrip("%").replace(".", "", 1).isdigit()]
                out.append(SystemSample(
                    timestamp=now,
                    cpu_pct=float(m.group("cpu") or 0),
                    mem_mb=float(m.group("mem_mb") or 0),
                    mem_pct=float(m.group("mem_pct") or 0),
                    gpu_pcts=gpu_pcts,
                    npu_pct=float(m.group("npu") or 0),
                    source="crossmon",
                ))
        return out

    # ------------------------------------------------------------------
    # psutil fallback
    # ------------------------------------------------------------------
    def _sample_with_psutil(self, duration_s: float, interval_ms: int) -> List[SystemSample]:
        out: List[SystemSample] = []
        end = time.time() + duration_s
        interval_s = max(interval_ms / 1000.0, 0.05)
        while time.time() < end:
            vm = psutil.virtual_memory()
            out.append(SystemSample(
                timestamp=time.time(),
                cpu_pct=psutil.cpu_percent(interval=None),
                mem_mb=vm.used / (1024 * 1024),
                mem_pct=vm.percent,
                source="psutil",
            ))
            time.sleep(interval_s)
        return out

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    @staticmethod
    def summarise(samples: List[SystemSample]) -> dict:
        if not samples:
            return {}
        cpu = [s.cpu_pct for s in samples]
        mem = [s.mem_pct for s in samples]
        npu = [s.npu_pct for s in samples]
        gpu = [s.gpu_avg for s in samples]
        return {
            "samples":      len(samples),
            "source":       samples[0].source,
            "cpu_pct_avg":  sum(cpu) / len(cpu),
            "cpu_pct_max":  max(cpu),
            "mem_pct_avg":  sum(mem) / len(mem),
            "mem_pct_max":  max(mem),
            "gpu_pct_avg":  sum(gpu) / len(gpu),
            "npu_pct_avg":  sum(npu) / len(npu),
            "npu_pct_max":  max(npu),
        }
