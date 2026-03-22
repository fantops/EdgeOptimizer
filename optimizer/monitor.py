"""System and power sampling for EdgeOptimizer (psutil-based, macOS-friendly)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import psutil


class PowerTracker:
    """Lightweight snapshots for experiment runners (before/after inference)."""

    def take_reading(self) -> Dict[str, Any]:
        battery = psutil.sensors_battery()
        out: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
        }
        if battery:
            out["battery_percent"] = battery.percent
            out["power_plugged"] = battery.power_plugged
        return out


class SystemMonitor:
    """CPU, memory, and battery visibility for scheduling and experiments."""

    def get_cpu_percent(self) -> float:
        return float(psutil.cpu_percent(interval=0.1))

    def get_power_metrics(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
        }

    def get_battery_status(self) -> Dict[str, Any]:
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "secsleft": battery.secsleft,
            }
        return {"available": False}
