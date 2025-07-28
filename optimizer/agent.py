#!/usr/bin/env python3
"""
EdgeOptimizer Agent - Main orchestration component
Coordinates power monitoring, model management, and optimization decisions
"""

import time
import logging
import os
from typing import Dict, Any, Optional
from .monitor import SystemMonitor, PowerTracker
from .model_manager import get_model_manager
from .config import get_config_manager

# Setup logging
def setup_logging():
    """Configure logging for EdgeOptimizer"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/edgeoptimizer.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('EdgeOptimizer')

logger = setup_logging()


class EdgeOptimizerAgent:
    """Main agent for edge computing optimization and power management"""
    
    def __init__(self, config_path: str = "optimizer_config"):
        logger.info("Initializing EdgeOptimizer Agent")
        self.config_manager = get_config_manager()
        self.model_manager = get_model_manager()
        self.system_monitor = SystemMonitor()
        self.power_tracker = PowerTracker()
        
        # Load configuration
        self.config = self.config_manager.load_config(config_path)
        logger.info(f"Loaded configuration from {config_path}")
        
        # Initialize thresholds
        self.battery_threshold = self.config.get("battery_threshold", 20)
        self.cpu_threshold = self.config.get("cpu_threshold", 80)
        self.memory_threshold = self.config.get("memory_threshold", 85)
        self.temperature_threshold = self.config.get("temperature_threshold", 70)
        
        logger.info(f"Agent initialized with thresholds - Battery: {self.battery_threshold}%, CPU: {self.cpu_threshold}%, Memory: {self.memory_threshold}%, Temp: {self.temperature_threshold}°C")
        self.auto_fallback_cloud = self.config.get("auto_fallback_cloud", True)
        
        print(f"🤖 EdgeOptimizer Agent initialized")
        print(f"   Battery threshold: {self.battery_threshold}%")
        print(f"   CPU threshold: {self.cpu_threshold}%")
        print(f"   Memory threshold: {self.memory_threshold}%")

    def should_run_local(self) -> Dict[str, Any]:
        """Determine if local inference should run based on system conditions"""
        metrics = self.system_monitor.get_power_metrics()
        battery_status = self.system_monitor.get_battery_status()
        
        reasons = []
        can_run = True
        
        # Check battery level
        if battery_status.get("available") and battery_status["percent"] < self.battery_threshold:
            can_run = False
            reasons.append(f"Battery too low: {battery_status['percent']}% < {self.battery_threshold}%")
        
        # Check CPU usage
        if metrics.get("cpu_percent", 0) > self.cpu_threshold:
            can_run = False
            reasons.append(f"CPU usage too high: {metrics['cpu_percent']}% > {self.cpu_threshold}%")
        
        # Check memory usage
        if metrics.get("memory_percent", 0) > self.memory_threshold:
            can_run = False
            reasons.append(f"Memory usage too high: {metrics['memory_percent']}% > {self.memory_threshold}%")
        
        # Check temperature if available
        if metrics.get("avg_temperature") and metrics["avg_temperature"] > self.temperature_threshold:
            can_run = False
            reasons.append(f"Temperature too high: {metrics['avg_temperature']:.1f}°C > {self.temperature_threshold}°C")
        
        return {
            "can_run_local": can_run,
            "should_fallback_cloud": not can_run and self.auto_fallback_cloud,
            "reasons": reasons,
            "metrics": metrics,
            "battery_status": battery_status
        }
    
    def run_optimized_inference(self, 
                              prompt: str, 
                              model_name: str = None,
                              max_length: int = None,
                              prefer_local: bool = True) -> Dict[str, Any]:
        """Run inference with automatic optimization based on system conditions"""
        
        # Use config defaults if not specified
        if model_name is None:
            model_name = self.config.get("model_settings", {}).get("default_local_model", "gpt2")
        if max_length is None:
            max_length = self.config.get("model_settings", {}).get("max_tokens", 50)
        
        decision = self.should_run_local()
        start_time = time.time()
        
        result = {
            "prompt": prompt,
            "model_name": model_name,
            "optimization_decision": decision,
            "inference_method": None,
            "response": None,
            "inference_time": 0,
            "total_time": 0,
            "success": False
        }
        
        try:
            if decision["can_run_local"] and prefer_local:
                # Run local inference
                print(f"🔥 Running local inference with {model_name}...")
                inference_result = self.model_manager.run_inference(
                    model_name=model_name,
                    prompt=prompt,
                    max_length=max_length,
                    temperature=self.config.get("model_settings", {}).get("temperature", 0.7)
                )
                result.update({
                    "inference_method": "local",
                    "response": inference_result["response"],
                    "inference_time": inference_result["inference_time"],
                    "success": inference_result["success"]
                })
                
            elif decision["should_fallback_cloud"]:
                # Fallback to cloud inference
                print("☁️ Falling back to cloud inference...")
                result.update({
                    "inference_method": "cloud_fallback",
                    "response": f"Would run cloud inference for: {prompt[:50]}...",
                    "inference_time": 0.5,  # Mock cloud time
                    "success": True,
                    "note": "Cloud inference not implemented yet - this is a mock response"
                })
                
            else:
                # Skip inference due to conditions
                result.update({
                    "inference_method": "skipped",
                    "response": f"Inference skipped due to system conditions: {', '.join(decision['reasons'])}",
                    "inference_time": 0,
                    "success": False
                })
            
        except Exception as e:
            result.update({
                "inference_method": "error",
                "response": f"Error during optimized inference: {e}",
                "inference_time": 0,
                "success": False,
                "error": str(e)
            })
        
        result["total_time"] = time.time() - start_time
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        metrics = self.system_monitor.get_power_metrics()
        battery_status = self.system_monitor.get_battery_status()
        performance = self.system_monitor.get_performance_metrics()
        models = self.model_manager.list_loaded_models()
        decision = self.should_run_local()
        
        return {
            "timestamp": metrics.get("timestamp"),
            "power_metrics": metrics,
            "battery_status": battery_status,
            "performance_metrics": performance,
            "loaded_models": models,
            "optimization_decision": decision,
            "thresholds": {
                "battery": self.battery_threshold,
                "cpu": self.cpu_threshold,
                "memory": self.memory_threshold,
                "temperature": self.temperature_threshold
            }
        }
    
    def log_status(self):
        """Log current system status"""
        status = self.get_system_status()
        
        print("🔋 System Status:")
        if status["battery_status"].get("available"):
            battery = status["battery_status"]
            plugged = "🔌" if battery["power_plugged"] else "🔋"
            print(f"   {plugged} Battery: {battery['percent']}%")
        
        metrics = status["power_metrics"]
        print(f"   💻 CPU: {metrics.get('cpu_percent', 'N/A')}%")
        print(f"   🧠 Memory: {metrics.get('memory_percent', 'N/A')}%")
        
        if metrics.get("avg_temperature"):
            print(f"   🌡️  Temperature: {metrics['avg_temperature']:.1f}°C")
        
        decision = status["optimization_decision"]
        if decision["can_run_local"]:
            print("   ✅ Ready for local inference")
        else:
            print(f"   ⚠️  Local inference not recommended: {', '.join(decision['reasons'])}")
    
    def start_monitoring(self, interval: float = 30.0):
        """Start continuous system monitoring"""
        print(f"🔍 Starting system monitoring (every {interval}s)")
        
        try:
            while True:
                self.log_status()
                print("-" * 50)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up EdgeOptimizer Agent...")
        # Unload models to free memory if needed
        for model_key in list(self.model_manager.models.keys()):
            model_name, device = model_key.rsplit("_", 1)
            self.model_manager.unload_model(model_name, device) 