#!/usr/bin/env python3
"""
Enhanced Power Consumption Monitor for EdgeOptimizer
Focuses specifically on detailed power consumption analysis between local and cloud inference
"""

import psutil
import time
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict
import statistics
import sys
import os

# Add parent directory to path to import optimizer modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.logging_config import save_power_analysis, get_logger

class PowerConsumptionMonitor:
    """Advanced power consumption monitoring with detailed energy analysis"""
    
    def __init__(self, sampling_rate: float = 0.1):
        self.sampling_rate = sampling_rate  # Higher frequency for power monitoring
        self.is_monitoring = False
        self.monitor_thread = None
        self.power_data = defaultdict(list)
        self.baseline_power = None
        
    def get_detailed_power_metrics(self) -> Dict[str, Any]:
        """Get comprehensive power consumption metrics"""
        timestamp = datetime.now()
        
        # Battery information (primary power metric)
        battery_info = self._get_battery_power_info()
        
        # CPU power indicators
        cpu_info = self._get_cpu_power_metrics()
        
        # Memory power impact
        memory_info = self._get_memory_power_metrics()
        
        # Thermal power indicators
        thermal_info = self._get_thermal_power_metrics()
        
        # System load power impact
        system_load = self._get_system_load_metrics()
        
        return {
            "timestamp": timestamp.isoformat(),
            "battery": battery_info,
            "cpu_power": cpu_info,
            "memory_power": memory_info,
            "thermal": thermal_info,
            "system_load": system_load,
            "estimated_power_draw": self._estimate_power_draw(cpu_info, memory_info, thermal_info)
        }
    
    def _get_battery_power_info(self) -> Dict[str, Any]:
        """Get detailed battery and power information"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return {
                    "available": False,
                    "is_plugged": True,  # Assume desktop/plugged system
                    "power_source": "AC"
                }
            
            # Calculate power drain rate if we have baseline
            drain_rate = 0
            if self.baseline_power and "battery" in self.baseline_power:
                time_diff = (datetime.now() - datetime.fromisoformat(self.baseline_power["timestamp"])).total_seconds()
                if time_diff > 0:
                    percent_diff = self.baseline_power["battery"]["percent"] - battery.percent
                    drain_rate = (percent_diff / time_diff) * 3600  # % per hour
            
            return {
                "available": True,
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "time_left_seconds": battery.secsleft if battery.secsleft != -1 else None,
                "time_left_hours": battery.secsleft / 3600 if battery.secsleft != -1 else None,
                "estimated_drain_rate_per_hour": drain_rate,
                "power_source": "AC" if battery.power_plugged else "Battery"
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _get_cpu_power_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics that correlate with power consumption"""
        try:
            # CPU usage (higher usage = more power)
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_per_core = psutil.cpu_percent(percpu=True, interval=None)
            
            # CPU frequency (higher frequency = more power)
            cpu_freq = psutil.cpu_freq()
            
            # CPU load average
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Estimate CPU power impact (normalized 0-100)
            cpu_power_score = self._calculate_cpu_power_score(cpu_percent, cpu_freq)
            
            return {
                "usage_percent": cpu_percent,
                "usage_per_core": cpu_per_core,
                "frequency_current_mhz": cpu_freq.current if cpu_freq else 0,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else 0,
                "frequency_utilization": (cpu_freq.current / cpu_freq.max * 100) if cpu_freq and cpu_freq.max else 0,
                "load_average_1min": load_avg[0],
                "load_average_5min": load_avg[1],
                "load_average_15min": load_avg[2],
                "power_impact_score": cpu_power_score,
                "core_count": psutil.cpu_count(logical=True)
            }
        except Exception as e:
            return {"error": str(e), "power_impact_score": 0}
    
    def _calculate_cpu_power_score(self, cpu_percent: float, cpu_freq) -> float:
        """Calculate a power impact score for CPU (0-100)"""
        try:
            # Base power from CPU usage
            usage_score = cpu_percent
            
            # Additional power from high frequency
            freq_score = 0
            if cpu_freq and cpu_freq.max:
                freq_ratio = cpu_freq.current / cpu_freq.max
                freq_score = freq_ratio * 30  # Up to 30 points for frequency
            
            # Combined score (capped at 100)
            total_score = min(usage_score + freq_score, 100)
            return round(total_score, 2)
        except:
            return cpu_percent  # Fallback to just CPU usage
    
    def _get_memory_power_metrics(self) -> Dict[str, Any]:
        """Get memory metrics that impact power consumption"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Memory usage affects power (more RAM usage = slightly more power)
            memory_power_score = memory.percent * 0.3  # Memory has lower power impact than CPU
            
            return {
                "usage_percent": memory.percent,
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3),
                "swap_usage_percent": swap.percent,
                "swap_used_gb": swap.used / (1024**3),
                "power_impact_score": round(memory_power_score, 2)
            }
        except Exception as e:
            return {"error": str(e), "power_impact_score": 0}
    
    def _get_thermal_power_metrics(self) -> Dict[str, Any]:
        """Get thermal metrics that indicate power consumption"""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return {"available": False, "power_impact_score": 0}
            
            all_temps = []
            hottest_sensor = {"name": "", "temp": 0}
            
            for sensor_name, entries in temps.items():
                sensor_temps = []
                for entry in entries:
                    if entry.current:
                        all_temps.append(entry.current)
                        sensor_temps.append(entry.current)
                        
                        # Track hottest sensor
                        if entry.current > hottest_sensor["temp"]:
                            hottest_sensor = {"name": sensor_name, "temp": entry.current}
                
                if sensor_temps:
                    print(f"   🌡️ {sensor_name}: {max(sensor_temps):.1f}°C")
            
            if not all_temps:
                return {"available": False, "power_impact_score": 0}
            
            avg_temp = sum(all_temps) / len(all_temps)
            max_temp = max(all_temps)
            
            # Calculate thermal power impact (higher temps = more power consumption)
            # Assume normal operating temp is 35°C, high performance is 70°C+
            thermal_power_score = max(0, min(100, (avg_temp - 35) * 2))
            
            return {
                "available": True,
                "average_temperature": round(avg_temp, 1),
                "max_temperature": round(max_temp, 1),
                "hottest_sensor": hottest_sensor["name"],
                "hottest_temperature": round(hottest_sensor["temp"], 1),
                "sensor_count": len(all_temps),
                "power_impact_score": round(thermal_power_score, 2)
            }
        except Exception as e:
            return {"available": False, "error": str(e), "power_impact_score": 0}
    
    def _get_system_load_metrics(self) -> Dict[str, Any]:
        """Get system load metrics that affect power consumption"""
        try:
            # Process count (more processes = more power)
            process_count = len(psutil.pids())
            
            # Disk I/O (disk activity = power consumption)
            disk_io = psutil.disk_io_counters()
            
            # Network I/O (less power impact but still measurable)
            net_io = psutil.net_io_counters()
            
            return {
                "process_count": process_count,
                "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
                "disk_write_bytes": disk_io.write_bytes if disk_io else 0,
                "network_bytes_sent": net_io.bytes_sent if net_io else 0,
                "network_bytes_recv": net_io.bytes_recv if net_io else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _estimate_power_draw(self, cpu_info: dict, memory_info: dict, thermal_info: dict) -> Dict[str, Any]:
        """Enhanced power draw estimation with actual wattage calculations"""
        try:
            # Enhanced power calculation based on actual system characteristics
            # Base power consumption varies by device type
            base_power = self._estimate_base_power()
            
            # CPU power contribution (primary factor for processing tasks)
            cpu_usage = cpu_info.get("usage_percent", 0)
            cpu_freq_ratio = cpu_info.get("frequency_utilization", 0) / 100
            cpu_cores = cpu_info.get("core_count", 4)
            
            # More sophisticated CPU power calculation
            cpu_power = self._calculate_cpu_power_consumption(cpu_usage, cpu_freq_ratio, cpu_cores)
            
            # Memory power contribution
            memory_usage = memory_info.get("usage_percent", 0)
            memory_gb = memory_info.get("total_gb", 8)
            memory_power = self._calculate_memory_power_consumption(memory_usage, memory_gb)
            
            # Thermal impact on power draw
            thermal_power = self._calculate_thermal_power_impact(thermal_info)
            
            # System load additional power
            load_power = self._calculate_system_load_power(cpu_info)
            
            total_power = base_power + cpu_power + memory_power + thermal_power + load_power
            
            # Calculate a normalized power score (0-100)
            max_estimated_power = self._get_max_system_power()
            power_score = min((total_power / max_estimated_power) * 100, 100)
            
            # Determine power level with more granular categories
            power_level = self._categorize_power_level(power_score)
            
            # Calculate power efficiency metrics
            efficiency_metrics = self._calculate_power_efficiency(cpu_usage, total_power)
            
            return {
                "estimated_watts": round(total_power, 2),
                "total_power_score": round(power_score, 2),
                "power_level": power_level,
                "breakdown": {
                    "base_power_watts": round(base_power, 2),
                    "cpu_power_watts": round(cpu_power, 2),
                    "memory_power_watts": round(memory_power, 2),
                    "thermal_power_watts": round(thermal_power, 2),
                    "system_load_watts": round(load_power, 2)
                },
                "efficiency": efficiency_metrics,
                "cpu_contribution_percent": round(cpu_power / total_power * 100, 1) if total_power > 0 else 0,
                "processing_overhead_watts": round(total_power - base_power, 2),
                # Legacy compatibility
                "cpu_contribution": round(cpu_power / total_power * 100 * 0.6, 2) if total_power > 0 else 0,
                "thermal_contribution": round(thermal_power / total_power * 100 * 0.3, 2) if total_power > 0 else 0,
                "memory_contribution": round(memory_power / total_power * 100 * 0.1, 2) if total_power > 0 else 0
            }
        except Exception as e:
            return {"error": str(e), "total_power_score": 0, "power_level": "Unknown"}
    
    def _estimate_base_power(self) -> float:
        """Estimate base system power consumption"""
        # Try to detect system type for better base power estimate
        try:
            # Check if this looks like a laptop vs desktop
            battery = psutil.sensors_battery()
            if battery:
                return 8.0  # Laptop base power (lower)
            else:
                return 25.0  # Desktop base power (higher)
        except:
            return 15.0  # Default fallback
    
    def _calculate_cpu_power_consumption(self, usage_percent: float, freq_ratio: float, core_count: int) -> float:
        """Calculate CPU power consumption with advanced modeling"""
        # Base CPU power per core (varies by architecture)
        base_cpu_power_per_core = 2.5  # Watts per core at idle
        max_cpu_power_per_core = 15.0   # Watts per core at 100% load
        
        # Power scales non-linearly with usage (more realistic)
        usage_factor = (usage_percent / 100) ** 1.3  # Non-linear scaling
        
        # Frequency scaling impact (higher frequency = more power)
        freq_multiplier = 1 + (freq_ratio * 0.8)  # Up to 80% more power at max frequency
        
        # Calculate per-core power then scale by core count
        core_power = base_cpu_power_per_core + (max_cpu_power_per_core * usage_factor * freq_multiplier)
        total_cpu_power = core_power * min(core_count, 8)  # Cap at 8 cores for calculation
        
        return total_cpu_power
    
    def _calculate_memory_power_consumption(self, usage_percent: float, total_gb: float) -> float:
        """Calculate memory power consumption"""
        # Memory power is relatively constant but increases with capacity and usage
        base_memory_power = total_gb * 0.3  # ~0.3W per GB
        usage_additional = (usage_percent / 100) * total_gb * 0.1  # Additional power for active memory
        
        return base_memory_power + usage_additional
    
    def _calculate_thermal_power_impact(self, thermal_info: Dict) -> float:
        """Calculate additional power due to thermal conditions"""
        if not thermal_info.get("available", False):
            return 0.0
        
        avg_temp = thermal_info.get("average_temperature", 50)
        
        # Higher temperatures indicate more power draw and thermal throttling overhead
        if avg_temp > 60:
            # Exponential increase in power for cooling and thermal management
            thermal_factor = min((avg_temp - 60) ** 1.5 * 0.2, 15)  # Up to 15W additional
            return thermal_factor
        
        return 0.0
    
    def _calculate_system_load_power(self, cpu_info: Dict) -> float:
        """Calculate additional power from system load"""
        load_avg = cpu_info.get("load_average_1min", 0)
        core_count = cpu_info.get("core_count", 4)
        
        # High system load indicates more background processes and I/O
        if load_avg > core_count:
            overload_factor = (load_avg - core_count) / core_count
            return min(overload_factor * 5, 10)  # Up to 10W for system overload
        
        return 0.0
    
    def _get_max_system_power(self) -> float:
        """Get estimated maximum system power consumption"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return 65.0  # Laptop max power
            else:
                return 150.0  # Desktop max power
        except:
            return 100.0  # Default fallback
    
    def _categorize_power_level(self, power_score: float) -> str:
        """Categorize power level with more granular levels"""
        if power_score < 10:
            return "Idle"
        elif power_score < 25:
            return "Low"
        elif power_score < 45:
            return "Medium"
        elif power_score < 65:
            return "High"
        elif power_score < 85:
            return "Very High"
        else:
            return "Maximum"
    
    def _calculate_power_efficiency(self, cpu_usage: float, total_power: float) -> Dict[str, Any]:
        """Calculate power efficiency metrics"""
        if cpu_usage == 0:
            efficiency_score = 100  # Perfect efficiency at idle
        else:
            # Higher efficiency = more work per watt
            work_per_watt = cpu_usage / total_power if total_power > 0 else 0
            efficiency_score = min(work_per_watt * 10, 100)  # Normalize to 0-100
        
        return {
            "efficiency_score": round(efficiency_score, 2),
            "work_per_watt": round(cpu_usage / total_power, 3) if total_power > 0 else 0,
            "watts_per_cpu_percent": round(total_power / cpu_usage, 3) if cpu_usage > 0 else total_power
        }
    
    def set_baseline(self):
        """Set baseline power consumption for comparison"""
        self.baseline_power = self.get_detailed_power_metrics()
        print(f"🔋 Power baseline set:")
        
        if self.baseline_power["battery"]["available"]:
            battery_info = self.baseline_power["battery"]
            power_source = battery_info.get("power_source", "Unknown")
            is_plugged = battery_info.get("power_plugged", False)
            battery_pct = battery_info.get("percent", 0)
            
            print(f"   Battery: {battery_pct:.1f}% ({power_source})")
            if is_plugged:
                print(f"   🔌 Device is plugged in (will charge during test)")
            else:
                print(f"   🔋 Running on battery power (will drain during test)")
        else:
            print(f"   Battery: Not detected (AC powered system)")
            
        power_score = self.baseline_power['estimated_power_draw']['total_power_score']
        power_level = self.baseline_power['estimated_power_draw']['power_level']
        print(f"   CPU Power Score: {power_score:.2f}")
        print(f"   Power Level: {power_level}")
    
    def start_continuous_monitoring(self, phase_name: str):
        """Start continuous power monitoring for a specific phase"""
        if self.is_monitoring:
            self.stop_monitoring()
        
        self.is_monitoring = True
        self.power_data[phase_name] = []
        
        def monitor_loop():
            while self.is_monitoring:
                power_snapshot = self.get_detailed_power_metrics()
                self.power_data[phase_name].append(power_snapshot)
                time.sleep(self.sampling_rate)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"🔍 Started continuous power monitoring for '{phase_name}' phase")
    
    def stop_monitoring(self):
        """Stop continuous power monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            print("⏹️  Stopped power monitoring")
    
    def analyze_power_consumption(self, phase_name: str) -> Dict[str, Any]:
        """Analyze power consumption data for a specific phase"""
        if phase_name not in self.power_data or not self.power_data[phase_name]:
            return {"error": f"No power data for phase: {phase_name}"}
        
        data = self.power_data[phase_name]
        duration_seconds = len(data) * self.sampling_rate
        
        # Extract power metrics
        power_scores = [d["estimated_power_draw"]["total_power_score"] for d in data]
        cpu_scores = [d["cpu_power"]["power_impact_score"] for d in data if "power_impact_score" in d["cpu_power"]]
        
        # Extract actual wattage estimates (new enhanced data)
        wattage_estimates = [d["estimated_power_draw"].get("estimated_watts", 0) for d in data if "estimated_watts" in d["estimated_power_draw"]]
        cpu_contribution_pcts = [d["estimated_power_draw"].get("cpu_contribution_percent", 0) for d in data if "cpu_contribution_percent" in d["estimated_power_draw"]]
        processing_overheads = [d["estimated_power_draw"].get("processing_overhead_watts", 0) for d in data if "processing_overhead_watts" in d["estimated_power_draw"]]
        efficiency_scores = [d["estimated_power_draw"].get("efficiency", {}).get("efficiency_score", 0) for d in data if "efficiency" in d["estimated_power_draw"]]
        
        # Battery analysis (if available)
        battery_analysis = self._analyze_battery_consumption(data)
        
        # CPU power analysis
        cpu_usage = [d["cpu_power"]["usage_percent"] for d in data if "usage_percent" in d["cpu_power"]]
        cpu_freq = [d["cpu_power"]["frequency_current_mhz"] for d in data if "frequency_current_mhz" in d["cpu_power"]]
        
        # Memory power analysis
        memory_usage = [d["memory_power"]["usage_percent"] for d in data if "usage_percent" in d["memory_power"]]
        
        # Thermal analysis
        thermal_analysis = self._analyze_thermal_data(data)
        
        # Enhanced power breakdown analysis
        power_breakdown = {}
        if wattage_estimates:
            power_breakdown = {
                "estimated_watts": statistics.mean(wattage_estimates),
                "peak_watts": max(wattage_estimates),
                "min_watts": min(wattage_estimates),
                "processing_overhead_watts": statistics.mean(processing_overheads) if processing_overheads else 0,
                "cpu_contribution_percent": statistics.mean(cpu_contribution_pcts) if cpu_contribution_pcts else 0,
                "efficiency": {
                    "efficiency_score": statistics.mean(efficiency_scores) if efficiency_scores else 0
                }
            }
        
        return {
            "phase": phase_name,
            "duration_seconds": duration_seconds,
            "sample_count": len(data),
            "power_consumption": {
                "avg_power_score": statistics.mean(power_scores) if power_scores else 0,
                "peak_power_score": max(power_scores) if power_scores else 0,
                "min_power_score": min(power_scores) if power_scores else 0,
                "power_score_stddev": statistics.stdev(power_scores) if len(power_scores) > 1 else 0
            },
            "power_breakdown": power_breakdown,  # New enhanced wattage data
            "battery": battery_analysis,
            "cpu_power": {
                "avg_usage_percent": statistics.mean(cpu_usage) if cpu_usage else 0,
                "peak_usage_percent": max(cpu_usage) if cpu_usage else 0,
                "avg_frequency_mhz": statistics.mean(cpu_freq) if cpu_freq else 0,
                "avg_power_score": statistics.mean(cpu_scores) if cpu_scores else 0
            },
            "memory_power": {
                "avg_usage_percent": statistics.mean(memory_usage) if memory_usage else 0,
                "peak_usage_percent": max(memory_usage) if memory_usage else 0
            },
            "thermal": thermal_analysis
        }
    
    def _analyze_battery_consumption(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze battery power consumption patterns"""
        battery_data = [d["battery"] for d in data if d["battery"]["available"]]
        
        if not battery_data:
            return {"available": False, "analysis": "No battery data available"}
        
        battery_levels = [b["percent"] for b in battery_data]
        
        if len(battery_levels) < 2:
            return {"available": True, "analysis": "Insufficient data for drain analysis"}
        
        # Calculate battery drain
        initial_level = battery_levels[0]
        final_level = battery_levels[-1]
        total_drain = initial_level - final_level
        duration_hours = len(data) * self.sampling_rate / 3600
        
        drain_rate_per_hour = total_drain / duration_hours if duration_hours > 0 else 0
        
        return {
            "available": True,
            "initial_percent": initial_level,
            "final_percent": final_level,
            "total_drain_percent": round(total_drain, 3),
            "drain_rate_per_hour": round(drain_rate_per_hour, 3),
            "estimated_remaining_hours": final_level / drain_rate_per_hour if drain_rate_per_hour > 0 else float('inf'),
            "power_source": battery_data[0]["power_source"]
        }
    
    def _analyze_thermal_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze thermal patterns during power consumption"""
        thermal_data = [d["thermal"] for d in data if d["thermal"]["available"]]
        
        if not thermal_data:
            return {"available": False}
        
        avg_temps = [t["average_temperature"] for t in thermal_data]
        max_temps = [t["max_temperature"] for t in thermal_data]
        
        return {
            "available": True,
            "avg_temperature": round(statistics.mean(avg_temps), 1),
            "peak_temperature": round(max(max_temps), 1),
            "temperature_rise": round(max(avg_temps) - min(avg_temps), 1),
            "thermal_stability": "Stable" if max(avg_temps) - min(avg_temps) < 5 else "Variable"
        }
    
    def compare_power_consumption(self, local_phase: str, cloud_phase: str) -> Dict[str, Any]:
        """Compare power consumption between local and cloud inference phases"""
        local_analysis = self.analyze_power_consumption(local_phase)
        cloud_analysis = self.analyze_power_consumption(cloud_phase)
        
        if "error" in local_analysis or "error" in cloud_analysis:
            return {"error": "Cannot compare phases due to missing data"}
        
        # Power efficiency comparison
        local_power = local_analysis["power_consumption"]["avg_power_score"]
        cloud_power = cloud_analysis["power_consumption"]["avg_power_score"]
        
        # Battery efficiency comparison
        battery_comparison = {}
        if (local_analysis["battery"]["available"] and 
            cloud_analysis["battery"]["available"]):
            
            local_drain = local_analysis["battery"]["drain_rate_per_hour"]
            cloud_drain = cloud_analysis["battery"]["drain_rate_per_hour"]
            
            battery_comparison = {
                "local_drain_rate": local_drain,
                "cloud_drain_rate": cloud_drain,
                "local_more_efficient": local_drain < cloud_drain,
                "efficiency_difference": round(cloud_drain - local_drain, 3)
            }
        
        # CPU power efficiency
        local_cpu = local_analysis["cpu_power"]["avg_power_score"]
        cloud_cpu = cloud_analysis["cpu_power"]["avg_power_score"]
        
        return {
            "comparison_summary": {
                "local_avg_power_score": local_power,
                "cloud_avg_power_score": cloud_power,
                "local_more_efficient": local_power < cloud_power,
                "power_difference": round(cloud_power - local_power, 2)
            },
            "battery_efficiency": battery_comparison,
            "cpu_efficiency": {
                "local_cpu_power_score": local_cpu,
                "cloud_cpu_power_score": cloud_cpu,
                "local_cpu_more_intensive": local_cpu > cloud_cpu,
                "cpu_power_difference": round(local_cpu - cloud_cpu, 2)
            },
            "recommendation": self._generate_power_recommendation(local_analysis, cloud_analysis),
            "detailed_local": local_analysis,
            "detailed_cloud": cloud_analysis
        }
    
    def _generate_power_recommendation(self, local_analysis: Dict, cloud_analysis: Dict) -> str:
        """Generate a power efficiency recommendation"""
        local_power = local_analysis["power_consumption"]["avg_power_score"]
        cloud_power = cloud_analysis["power_consumption"]["avg_power_score"]
        
        local_battery = local_analysis["battery"]
        cloud_battery = cloud_analysis["battery"]
        
        # Primary recommendation based on overall power scores
        if local_power < cloud_power:
            base_rec = "LOCAL inference is more power efficient"
        else:
            base_rec = "CLOUD inference is more power efficient"
        
        # Additional context
        context = []
        
        if local_battery["available"] and cloud_battery["available"]:
            local_drain = local_battery["drain_rate_per_hour"]
            cloud_drain = cloud_battery["drain_rate_per_hour"]
            
            if abs(local_drain - cloud_drain) < 0.1:
                context.append("battery drain rates are similar")
            elif local_drain < cloud_drain:
                context.append("local inference drains battery slower")
            else:
                context.append("cloud inference drains battery slower")
        
        # CPU usage context
        local_cpu = local_analysis["cpu_power"]["avg_usage_percent"]
        cloud_cpu = cloud_analysis["cpu_power"]["avg_usage_percent"]
        
        if local_cpu > cloud_cpu + 10:
            context.append("local inference uses significantly more CPU")
        elif cloud_cpu > local_cpu + 10:
            context.append("cloud inference uses significantly more CPU")
        
        if context:
            return f"{base_rec} ({', '.join(context)})"
        else:
            return base_rec
    
    def save_power_analysis(self, comparison_results: Dict[str, Any], filename: str = None):
        """Save detailed power analysis results using centralized logging"""
        if filename is None:
            # Use centralized logging system
            filename = save_power_analysis(comparison_results, "comparison")
        else:
            # Legacy support - save to specified location
            import os
            os.makedirs("logs", exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(comparison_results, f, indent=2, default=str)
        
        print(f"💾 Power analysis saved to: {filename}")
        return filename
    
    def print_power_summary(self, comparison_results: Dict[str, Any]):
        """Print a comprehensive power consumption summary"""
        print("\n" + "="*70)
        print("⚡ POWER CONSUMPTION ANALYSIS SUMMARY")
        print("="*70)
        
        summary = comparison_results["comparison_summary"]
        
        print(f"\n🔋 Overall Power Efficiency:")
        print(f"   Local Power Score:  {summary['local_avg_power_score']:.2f}")
        print(f"   Cloud Power Score:  {summary['cloud_avg_power_score']:.2f}")
        print(f"   Difference:         {summary['power_difference']:+.2f}")
        
        if summary["local_more_efficient"]:
            print(f"   Winner: 🏆 LOCAL is more power efficient")
        else:
            print(f"   Winner: 🏆 CLOUD is more power efficient")
        
        if "battery_efficiency" in comparison_results and comparison_results["battery_efficiency"]:
            battery = comparison_results["battery_efficiency"]
            print(f"\n🔋 Battery Drain Analysis:")
            print(f"   Local Drain Rate:   {battery['local_drain_rate']:.3f}%/hour")
            print(f"   Cloud Drain Rate:   {battery['cloud_drain_rate']:.3f}%/hour")
            print(f"   Difference:         {battery['efficiency_difference']:+.3f}%/hour")
            
            # Enhanced battery explanation
            if battery['local_drain_rate'] < 0 or battery['cloud_drain_rate'] < 0:
                print(f"   📌 Note: Negative drain = battery charging (device plugged in)")
            
            if battery["local_more_efficient"]:
                print(f"   Battery Winner: 🏆 LOCAL drains battery slower")
            else:
                print(f"   Battery Winner: 🏆 CLOUD drains battery slower")
        else:
            print(f"\n🔋 Battery Drain Analysis:")
            print(f"   📌 Battery analysis not available (likely AC powered/desktop)")
        
        cpu_eff = comparison_results["cpu_efficiency"]
        print(f"\n💻 CPU Power Impact:")
        print(f"   Local CPU Power:    {cpu_eff['local_cpu_power_score']:.2f}")
        print(f"   Cloud CPU Power:    {cpu_eff['cloud_cpu_power_score']:.2f}")
        print(f"   Difference:         {cpu_eff['cpu_power_difference']:+.2f}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {comparison_results['recommendation']}")
        
        print("="*70)
