#!/usr/bin/env python3
"""
System monitoring utilities for EdgeOptimizer
Centralized power and system metrics collection
"""

import psutil
import time
from datetime import datetime
from typing import Dict, Optional, Any


class SystemMonitor:
    """Centralized system monitoring for power and performance metrics"""
    
    def __init__(self, measurement_interval: float = 0.1):
        self.measurement_interval = measurement_interval
        
    def get_power_metrics(self) -> Dict[str, Any]:
        """Get comprehensive power and system metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=self.measurement_interval),
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            }
            
            # Add battery info if available
            battery = psutil.sensors_battery()
            if battery:
                metrics.update({
                    "battery_percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != -1 else None
                })
            
            # Add temperature info if available (macOS/Linux)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get average temperature across all sensors
                    all_temps = []
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current:
                                all_temps.append(entry.current)
                    if all_temps:
                        metrics["avg_temperature"] = sum(all_temps) / len(all_temps)
            except (AttributeError, PermissionError):
                pass  # Temperature sensors not available on all systems
                
            return metrics
            
        except Exception as e:
            return {
                "error": str(e), 
                "timestamp": datetime.now().isoformat()
            }
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Get detailed battery information"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return {"available": False, "message": "No battery found"}
                
            return {
                "available": True,
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "time_left_seconds": battery.secsleft if battery.secsleft != -1 else None,
                "time_left_hours": (battery.secsleft / 3600) if battery.secsleft != -1 else None
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def is_power_sufficient(self, threshold: float = 20.0) -> bool:
        """Check if battery level is above threshold"""
        battery_status = self.get_battery_status()
        if not battery_status.get("available"):
            return True  # Assume sufficient if no battery (desktop)
        
        return battery_status["percent"] >= threshold
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get CPU and memory performance metrics"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent_per_core": psutil.cpu_percent(percpu=True, interval=self.measurement_interval),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            return {"error": str(e)}


class PowerTracker:
    """Track power consumption over time for experiments"""
    
    def __init__(self):
        self.monitor = SystemMonitor()
        self.readings = []
        
    def start_tracking(self):
        """Start a new tracking session"""
        self.readings = []
        return self.take_reading()
    
    def take_reading(self) -> Dict[str, Any]:
        """Take a power reading and store it"""
        reading = self.monitor.get_power_metrics()
        self.readings.append(reading)
        return reading
    
    def get_power_delta(self, before_reading: Dict[str, Any], after_reading: Dict[str, Any]) -> Dict[str, float]:
        """Calculate power consumption changes between two readings"""
        delta = {}
        
        for key in ["cpu_percent", "memory_percent", "battery_percent"]:
            if key in before_reading and key in after_reading:
                delta[f"{key}_change"] = after_reading[key] - before_reading[key]
                
        return delta
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics from all readings"""
        if not self.readings:
            return {}
            
        metrics = {}
        numeric_keys = ["cpu_percent", "memory_percent", "battery_percent", "cpu_freq"]
        
        for key in numeric_keys:
            values = [r.get(key) for r in self.readings if r.get(key) is not None]
            if values:
                metrics[f"avg_{key}"] = sum(values) / len(values)
                metrics[f"max_{key}"] = max(values)
                metrics[f"min_{key}"] = min(values)
        
        return metrics
