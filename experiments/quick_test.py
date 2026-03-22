#!/usr/bin/env python3
"""
Quick test version of power consumption experiment
Works without full model download for immediate testing
"""

import time
import psutil
import json
import requests
from datetime import datetime
import os

class QuickPowerTest:
    def __init__(self, duration=60):  # 1 minute test
        self.duration = duration
        self.results = {
            "local": {"power_readings": [], "timestamps": [], "inference_times": []},
            "cloud": {"power_readings": [], "timestamps": [], "inference_times": []}
        }
        self.running = False
        
    def measure_power(self):
        """Measure current power consumption"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "battery_percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != -1 else None
                }
            else:
                return {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent
                }
        except Exception as e:
            return {"error": str(e)}
    
    def run_local_inference(self, prompt):
        """Simulate local inference"""
        try:
            start_time = time.time()
            
            # Simulate processing time
            time.sleep(0.05)  # 50ms simulation
            
            inference_time = time.time() - start_time
            
            return {
                "response": f"Local response to: {prompt[:30]}...",
                "inference_time": inference_time,
                "success": True
            }
            
        except Exception as e:
            return {
                "response": f"Local inference error: {e}",
                "inference_time": 0,
                "success": False
            }
    
    def run_cloud_inference(self, prompt):
        """Run cloud inference via API"""
        try:
            # Load config
            with open('configs/experiment_config.json', 'r') as f:
                config = json.load(f)
            
            headers = {
                "Authorization": f"Bearer {config['cloud_api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50  # Shorter response for testing
            }
            
            start_time = time.time()
            response = requests.post(
                config['cloud_api_url'],
                headers=headers,
                json=data,
                timeout=30
            )
            inference_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "response": response.json()['choices'][0]['message']['content'],
                    "inference_time": inference_time,
                    "success": True
                }
            else:
                return {
                    "response": f"Cloud API error: {response.status_code}",
                    "inference_time": inference_time,
                    "success": False
                }
                
        except Exception as e:
            return {
                "response": f"Cloud inference error: {e}",
                "inference_time": 0,
                "success": False
            }
    
    def run_quick_test(self):
        """Run a quick power consumption test"""
        print(f"🚀 Quick Power Test (Duration: {self.duration} seconds)")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        
        test_prompts = [
            "What is AI?",
            "Explain machine learning",
            "What is edge computing?",
            "How does a neural network work?"
        ]
        
        prompt_index = 0
        
        while time.time() - start_time < self.duration:
            current_time = time.time() - start_time
            print(f"\n⏱️  Time elapsed: {current_time:.1f}s")
            
            prompt = test_prompts[prompt_index % len(test_prompts)]
            
            # Measure power before inference
            power_before = self.measure_power()
            
            # Test local inference
            print(f"🤖 [LOCAL] Processing: {prompt[:30]}...")
            local_result = self.run_local_inference(prompt)
            print(f"✅ [LOCAL] Response: {local_result['response'][:50]}...")
            print(f"⏱️  [LOCAL] Time: {local_result['inference_time']:.3f}s")
            
            # Test cloud inference
            print(f"☁️  [CLOUD] Processing: {prompt[:30]}...")
            cloud_result = self.run_cloud_inference(prompt)
            print(f"✅ [CLOUD] Response: {cloud_result['response'][:50]}...")
            print(f"⏱️  [CLOUD] Time: {cloud_result['inference_time']:.3f}s")
            
            # Measure power after inference
            power_after = self.measure_power()
            
            # Store results
            timestamp = datetime.now().isoformat()
            
            self.results["local"]["power_readings"].append(power_before)
            self.results["local"]["timestamps"].append(timestamp)
            self.results["local"]["inference_times"].append(local_result["inference_time"])
            
            self.results["cloud"]["power_readings"].append(power_after)
            self.results["cloud"]["timestamps"].append(timestamp)
            self.results["cloud"]["inference_times"].append(cloud_result["inference_time"])
            
            prompt_index += 1
            time.sleep(5)  # Wait 5 seconds between tests
        
        self.running = False
        self.save_results()
        print("\n✅ Quick test completed!")
    
    def save_results(self):
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"experiments/quick_test_results_{timestamp}.json"
        
        os.makedirs("experiments", exist_ok=True)
        
        summary = self.generate_summary()
        
        with open(filename, 'w') as f:
            json.dump({
                "test_duration": self.duration,
                "results": self.results,
                "summary": summary
            }, f, indent=2)
        
        print(f"📊 Results saved to: {filename}")
        print(f"📈 Summary: {summary}")
    
    def generate_summary(self):
        """Generate summary statistics"""
        summary = {}
        
        for mode in ["local", "cloud"]:
            if self.results[mode]["power_readings"]:
                readings = self.results[mode]["power_readings"]
                
                if "battery_percent" in readings[0]:
                    battery_levels = [r.get("battery_percent", 100) for r in readings]
                    summary[mode] = {
                        "initial_battery": battery_levels[0],
                        "final_battery": battery_levels[-1],
                        "battery_drain": battery_levels[0] - battery_levels[-1],
                        "avg_inference_time": sum(self.results[mode]["inference_times"]) / len(self.results[mode]["inference_times"]) if self.results[mode]["inference_times"] else 0,
                        "total_inferences": len(self.results[mode]["inference_times"])
                    }
                else:
                    cpu_levels = [r.get("cpu_percent", 0) for r in readings]
                    summary[mode] = {
                        "avg_cpu_percent": sum(cpu_levels) / len(cpu_levels),
                        "max_cpu_percent": max(cpu_levels),
                        "avg_inference_time": sum(self.results[mode]["inference_times"]) / len(self.results[mode]["inference_times"]) if self.results[mode]["inference_times"] else 0,
                        "total_inferences": len(self.results[mode]["inference_times"])
                    }
        
        return summary

if __name__ == "__main__":
    test = QuickPowerTest(duration=60)  # 1 minute test
    test.run_quick_test() 