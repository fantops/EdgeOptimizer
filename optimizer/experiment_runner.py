#!/usr/bin/env python3
"""
Experiment runner utilities for EdgeOptimizer
Centralized experiment management and result analysis
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Callable


class ExperimentRunner:
    """Base class for running comparative experiments"""
    
    def __init__(self, duration: int = 300, experiment_name: str = "experiment"):
        self.duration = duration
        self.experiment_name = experiment_name
        self.results = {}
        self.start_time = None
        self.logger = logging.getLogger('ExperimentRunner')
        
    def run_phase(self, 
                  phase_name: str,
                  test_function: Callable,
                  prompts: List[str],
                  duration: int = None,
                  interval: int = 5) -> Dict[str, Any]:
        """Run a single phase of the experiment"""
        
        if duration is None:
            duration = self.duration // 2  # Default to half the total duration
            
        print(f"\n🔥 Starting {phase_name} phase...")
        
        phase_results = {
            "power_readings": [],
            "timestamps": [],
            "inference_times": [],
            "responses": [],
            "metadata": []
        }
        
        phase_start = time.time()
        test_count = 0
        prompt_index = 0
        
        while time.time() - phase_start < duration:
            current_time = time.time() - (self.start_time or phase_start)
            prompt = prompts[prompt_index % len(prompts)]
            
            print(f"\n⏱️  [{current_time:.1f}s] {phase_name} #{test_count + 1}")
            print(f"📝 Prompt: {prompt}")
            
            # Run the test function
            result = test_function(prompt)
            
            # Store results
            phase_results["timestamps"].append(datetime.now().isoformat())
            phase_results["inference_times"].append(result.get("inference_time", 0))
            phase_results["responses"].append(str(result.get("response", ""))[:200])
            
            # Store metadata if available
            metadata = {key: value for key, value in result.items() 
                       if key not in ["response", "inference_time"]}
            phase_results["metadata"].append(metadata)
            
            print(f"✅ Response: {result.get('response', 'No response')}")
            print(f"⏱️  Time: {result.get('inference_time', 0):.3f}s")
            print("-" * 60)
            
            test_count += 1
            prompt_index += 1
            
            if test_count < 10:  # Don't sleep after the last test
                time.sleep(interval)
        
        return phase_results
    
    def save_results(self, results: Dict[str, Any], include_summary: bool = True) -> str:
        """Save experiment results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{self.experiment_name}_results_{timestamp}.json"
        
        os.makedirs("logs", exist_ok=True)
        
        final_results = {
            "experiment_info": {
                "name": self.experiment_name,
                "duration": self.duration,
                "timestamp": timestamp,
                "total_phases": len(results)
            },
            "results": results
        }
        
        if include_summary:
            final_results["summary"] = self.generate_summary(results)
        
        with open(filename, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        self.logger.info(f"Results saved to: {filename}")
        print(f"📊 Results saved to: {filename}")
        return filename
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for all phases"""
        summary = {}
        
        for phase_name, phase_data in results.items():
            if "inference_times" in phase_data:
                times = phase_data["inference_times"]
                if times:
                    summary[phase_name] = {
                        "total_tests": len(times),
                        "avg_inference_time": sum(times) / len(times),
                        "min_inference_time": min(times),
                        "max_inference_time": max(times),
                        "total_inference_time": sum(times)
                    }
                    
                    # Add success rate if available
                    metadata_list = phase_data.get("metadata", [])
                    if metadata_list:
                        success_count = sum(1 for m in metadata_list if m.get("success", False))
                        summary[phase_name]["success_rate"] = success_count / len(metadata_list)
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print experiment summary to console"""
        print("\n📈 Experiment Summary")
        print("=" * 50)
        
        for phase_name, stats in summary.items():
            print(f"\n{phase_name.upper()}:")
            print(f"  Tests: {stats.get('total_tests', 0)}")
            print(f"  Avg time: {stats.get('avg_inference_time', 0):.3f}s")
            print(f"  Total time: {stats.get('total_inference_time', 0):.3f}s")
            if "success_rate" in stats:
                print(f"  Success rate: {stats['success_rate']:.1%}")


class PowerExperimentRunner(ExperimentRunner):
    """Specialized experiment runner with power monitoring"""
    
    def __init__(self, duration: int = 300, power_tracker=None, logger=None):
        super().__init__(duration, "power_comparison")
        self.power_tracker = power_tracker
        if logger:
            self.logger = logger
        
    def run_phase_with_power(self,
                           phase_name: str,
                           test_function: Callable,
                           prompts: List[str],
                           duration: int = None,
                           interval: int = 5) -> Dict[str, Any]:
        """Run a phase with power monitoring"""
        
        if duration is None:
            duration = self.duration // 2
            
        self.logger.info(f"Starting {phase_name} phase with {len(prompts)} prompts, duration: {duration}s")
        print(f"\n🔥 Starting {phase_name} phase...")
        
        phase_results = {
            "power_readings": [],
            "timestamps": [],
            "inference_times": [],
            "responses": [],
            "metadata": []
        }
        
        phase_start = time.time()
        test_count = 0
        prompt_index = 0
        
        while time.time() - phase_start < duration:
            current_time = time.time() - (self.start_time or phase_start)
            prompt = prompts[prompt_index % len(prompts)]
            
            self.logger.info(f"[{current_time:.1f}s] {phase_name} #{test_count + 1} - Prompt: {prompt[:50]}...")
            print(f"\n⏱️  [{current_time:.1f}s] {phase_name} #{test_count + 1}")
            print(f"📝 Prompt: {prompt}")
            
            # Measure power before
            power_before = None
            if self.power_tracker:
                power_before = self.power_tracker.take_reading()
            
            # Run the test function
            result = test_function(prompt)
            
            # Measure power after
            power_after = None
            if self.power_tracker:
                power_after = self.power_tracker.take_reading()
            
            # Log the result
            if result.get("success"):
                self.logger.info(f"✅ {phase_name} #{test_count + 1} completed - Time: {result.get('inference_time', 0):.3f}s")
            else:
                self.logger.warning(f"❌ {phase_name} #{test_count + 1} failed - Error: {result.get('error', 'Unknown')}")
            
            # Store results
            if power_before and power_after:
                phase_results["power_readings"].append({
                    "before": power_before,
                    "after": power_after
                })
            
            phase_results["timestamps"].append(datetime.now().isoformat())
            phase_results["inference_times"].append(result.get("inference_time", 0))
            phase_results["responses"].append(str(result.get("response", ""))[:200])
            
            # Store metadata
            metadata = {key: value for key, value in result.items() 
                       if key not in ["response", "inference_time"]}
            phase_results["metadata"].append(metadata)
            
            print(f"✅ Response: {result.get('response', 'No response')}")
            print(f"⏱️  Time: {result.get('inference_time', 0):.3f}s")
            
            if power_after:
                print(f"🔋 CPU: {power_after.get('cpu_percent', 'N/A')}%, Memory: {power_after.get('memory_percent', 'N/A')}%")
            
            print("-" * 60)
            
            test_count += 1
            prompt_index += 1
            
            if test_count < 10:  # Don't sleep after the last test
                time.sleep(interval)
        
        self.logger.info(f"Completed {phase_name} phase - {test_count} tests completed")
        return phase_results
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary with power statistics"""
        summary = super().generate_summary(results)
        
        # Add power-specific statistics
        for phase_name, phase_data in results.items():
            if phase_name in summary and "power_readings" in phase_data:
                power_readings = phase_data["power_readings"]
                
                # Calculate CPU usage changes
                cpu_changes = []
                for reading in power_readings:
                    before = reading.get("before", {})
                    after = reading.get("after", {})
                    if "cpu_percent" in before and "cpu_percent" in after:
                        cpu_changes.append(after["cpu_percent"] - before["cpu_percent"])
                
                if cpu_changes:
                    summary[phase_name].update({
                        "avg_cpu_increase": sum(cpu_changes) / len(cpu_changes),
                        "max_cpu_increase": max(cpu_changes),
                        "min_cpu_increase": min(cpu_changes)
                    })
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print power experiment summary"""
        super().print_summary(summary)
        
        # Add power-specific information
        for phase_name, stats in summary.items():
            if "avg_cpu_increase" in stats:
                print(f"  Avg CPU increase: {stats['avg_cpu_increase']:.1f}%")
                print(f"  Max CPU increase: {stats['max_cpu_increase']:.1f}%")
