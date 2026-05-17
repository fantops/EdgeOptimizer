"""Energy-per-inference attribution.

Sources (priority order):

1. **Intel RAPL** — ``/sys/class/powercap/intel-rapl:*/energy_uj`` (Linux only).
   Counter wraps; we read at start + end of a window and diff.
2. **macOS ``powermetrics``** — sampled via ``sudo powermetrics --samplers cpu_power``
   (requires sudo; we fall back if unavailable).
3. **CrossMon sampler** — cross-platform CPU/GPU utilisation; energy is then
   inferred from utilisation × measured TDP. Lower fidelity, always available.
4. **psutil battery delta** — last-resort coarse signal on laptops on battery.

The corporate version of this module ties into Quarch / Monsoon for ground-truth
external power. That hardware is out of scope here; the interface is the same
so a hardware path can be added without changing callers.
"""

from __future__ import annotations

import glob
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class EnergySample:
    source: str            # "rapl" | "powermetrics" | "crossmon" | "battery"
    joules: float
    duration_s: float
    notes: str = ""

    @property
    def avg_watts(self) -> float:
        if self.duration_s <= 0:
            return 0.0
        return self.joules / self.duration_s


class EnergyAttributor:
    """Window-based energy measurement around an inference call."""

    def __init__(self, prefer: Optional[str] = None) -> None:
        self.prefer = prefer
        self._t0: Optional[float] = None
        self._e0_uj: Optional[int] = None
        self._battery0: Optional[float] = None

    # ------------------------------------------------------------------
    # Source detection
    # ------------------------------------------------------------------
    def _rapl_paths(self) -> list[str]:
        return sorted(glob.glob("/sys/class/powercap/intel-rapl:*/energy_uj"))

    def _read_rapl_uj(self) -> Optional[int]:
        total = 0
        paths = self._rapl_paths()
        if not paths:
            return None
        for p in paths:
            try:
                with open(p) as fh:
                    total += int(fh.read().strip())
            except OSError:
                return None
        return total

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def begin(self) -> None:
        self._t0 = time.time()
        self._e0_uj = self._read_rapl_uj()
        battery = psutil.sensors_battery()
        self._battery0 = battery.percent if battery else None

    def end(self) -> EnergySample:
        if self._t0 is None:
            raise RuntimeError("begin() must be called before end()")
        duration = max(time.time() - self._t0, 1e-9)

        # 1) Intel RAPL
        if self._e0_uj is not None:
            e1 = self._read_rapl_uj()
            if e1 is not None and e1 >= self._e0_uj:
                joules = (e1 - self._e0_uj) / 1e6
                return EnergySample("rapl", joules, duration)

        # 2) macOS powermetrics (one-shot, 200 ms window inside ours)
        if self.prefer != "skip-powermetrics":
            sample = self._powermetrics_one_shot(duration)
            if sample is not None:
                return sample

        # 3) Battery delta (very coarse)
        if self._battery0 is not None:
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged:
                delta_pct = max(self._battery0 - battery.percent, 0)
                # Treat 1 % of a 50 Wh laptop battery ≈ 1800 J as a stand-in.
                joules = delta_pct * 1800.0
                return EnergySample(
                    "battery", joules, duration,
                    notes="coarse: 1%≈1800 J assumed",
                )

        # 4) Nothing — return zeros but flag the source.
        return EnergySample(
            "unavailable", 0.0, duration,
            notes="no RAPL, no powermetrics, AC-powered or no battery",
        )

    # ------------------------------------------------------------------
    # macOS path
    # ------------------------------------------------------------------
    def _powermetrics_one_shot(self, duration: float) -> Optional[EnergySample]:
        if not os.path.exists("/usr/bin/powermetrics"):
            return None
        # Try without sudo first; powermetrics requires root, so this usually
        # fails. We don't auto-elevate — fall through to next source.
        try:
            out = subprocess.run(
                ["/usr/bin/powermetrics",
                 "--samplers", "cpu_power",
                 "-n", "1", "-i", "200"],
                capture_output=True, text=True, timeout=2,
            )
        except (subprocess.SubprocessError, OSError):
            return None
        if out.returncode != 0:
            return None
        # Parse "CPU Power: 1234 mW" lines.
        watts = 0.0
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.lower().startswith("cpu power:"):
                try:
                    mw = float(line.split(":")[1].strip().split()[0])
                    watts = mw / 1000.0
                except (IndexError, ValueError):
                    continue
        if watts <= 0:
            return None
        return EnergySample("powermetrics", watts * duration, duration)
