import time
import psutil
import json
import requests
import threading
from datetime import datetime
import os

class PowerConsumptionExperiment:
    def __init__(self, config_path="configs/experiment_config.json"):
        self.config = self.load_config(config_path)
        self.results = {
            "local": {"power_readings": [], "timestamps": [], "total_energy": 0, "inference_times": []},
            "cloud": {"power_readings": [], "timestamps": [], "total_energy": 0, "inference_times": []}
        }
        self.running = False
        
    def load_config(self, config_path):
        """Load experiment configuration"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "experiment_duration": 3600,  # 1 hour in seconds
                "sampling_interval": 5,  # seconds
                "local_model_path": "models/phi.onnx",
                "cloud_api_url": "https://api.openai.com/v1/chat/completions",
                "cloud_api_key": "YOUR_API_KEY_HERE",
                "test_prompts": [
                    "What is machine learning?",
                    "Explain quantum computing",
                    "How does a neural network work?",
                    "What are the benefits of edge computing?",
                    "Describe the differences between supervised and unsupervised learning",
                    "What is the role of activation functions in neural networks?",
                    "Explain the concept of overfitting in machine learning",
                    "How do convolutional neural networks work?",
                    "What is transfer learning and when is it useful?",
                    "Describe the transformer architecture"
                ]
            }
    
    def measure_power(self):
        """Measure current power consumption"""
        try:
            # Get battery info if available
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "battery_percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != -1 else None
                }
            else:
                # Fallback to CPU usage as proxy
                return {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent
                }
        except Exception as e:
            print(f"Error measuring power: {e}")
            return {"error": str(e)}
    
    def run_local_inference(self, prompt):
        """Run local inference using ONNX model"""
        try:
            # Import and use the enhanced chatbot
            from app.chatbot import PhiChatbot
            
            # Initialize chatbot (will load model)
            chatbot = PhiChatbot(self.config["local_model_path"])
            
            # Run inference
            result = chatbot.run_inference(prompt)
            
            return {
                "response": result["response"],
                "inference_time": result["inference_time"],
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
            headers = {
                "Authorization": f"Bearer {self.config['cloud_api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            }
            
            start_time = time.time()
            response = requests.post(
                self.config['cloud_api_url'],
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
    
    def power_monitoring_thread(self, mode):
        """Background thread for continuous power monitoring"""
        start_time = time.time()
        
        while self.running:
            timestamp = datetime.now().isoformat()
            power_data = self.measure_power()
            
            self.results[mode]["power_readings"].append(power_data)
            self.results[mode]["timestamps"].append(timestamp)
            
            # Calculate energy consumption (simplified)
            if "battery_percent" in power_data:
                # Estimate energy based on battery drain
                if len(self.results[mode]["power_readings"]) > 1:
                    prev_battery = self.results[mode]["power_readings"][-2].get("battery_percent", 100)
                    current_battery = power_data["battery_percent"]
                    battery_drain = prev_battery - current_battery
                    # Rough energy estimation (mAh)
                    self.results[mode]["total_energy"] += battery_drain * 0.1
            
            time.sleep(self.config["sampling_interval"])
    
    def run_experiment(self, mode="both"):
        """Run the power consumption experiment"""
        print(f"Starting {mode} power consumption experiment...")
        print(f"Duration: {self.config['experiment_duration']} seconds")
        print(f"Sampling interval: {self.config['sampling_interval']} seconds")
        
        self.running = True
        start_time = time.time()
        
        # Start power monitoring threads
        threads = []
        if mode in ["local", "both"]:
            local_thread = threading.Thread(
                target=self.power_monitoring_thread, 
                args=("local",)
            )
            local_thread.start()
            threads.append(local_thread)
        
        if mode in ["cloud", "both"]:
            cloud_thread = threading.Thread(
                target=self.power_monitoring_thread, 
                args=("cloud",)
            )
            cloud_thread.start()
            threads.append(cloud_thread)
        
        # Run inference loops
        prompt_index = 0
        while time.time() - start_time < self.config["experiment_duration"]:
            prompt = self.config["test_prompts"][prompt_index % len(self.config["test_prompts"])]
            
            if mode in ["local", "both"]:
                print(f"[LOCAL] Processing: {prompt[:30]}...")
                result = self.run_local_inference(prompt)
                print(f"[LOCAL] Response: {result['response'][:50]}...")
                print(f"[LOCAL] Time: {result['inference_time']:.3f}s")
                self.results["local"]["inference_times"].append(result["inference_time"])
            
            if mode in ["cloud", "both"]:
                print(f"[CLOUD] Processing: {prompt[:30]}...")
                result = self.run_cloud_inference(prompt)
                print(f"[CLOUD] Response: {result['response'][:50]}...")
                print(f"[CLOUD] Time: {result['inference_time']:.3f}s")
                self.results["cloud"]["inference_times"].append(result["inference_time"])
            
            prompt_index += 1
            time.sleep(10)  # Wait between prompts
        
        # Stop monitoring
        self.running = False
        
        # Wait for threads to finish
        for thread in threads:
            thread.join()
        
        # Save results
        self.save_results()
        print("Experiment completed!")
    
    def save_results(self):
        """Save experiment results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"experiments/results_power_comparison_{timestamp}.json"
        
        os.makedirs("experiments", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump({
                "experiment_config": self.config,
                "results": self.results,
                "summary": self.generate_summary()
            }, f, indent=2)
        
        print(f"Results saved to: {filename}")
    
    def generate_summary(self):
        """Generate summary statistics"""
        summary = {}
        
        for mode in ["local", "cloud"]:
            if self.results[mode]["power_readings"]:
                readings = self.results[mode]["power_readings"]
                
                # Calculate averages
                if "battery_percent" in readings[0]:
                    battery_levels = [r.get("battery_percent", 100) for r in readings]
                    summary[mode] = {
                        "initial_battery": battery_levels[0],
                        "final_battery": battery_levels[-1],
                        "battery_drain": battery_levels[0] - battery_levels[-1],
                        "total_energy_estimate": self.results[mode]["total_energy"],
                        "readings_count": len(readings),
                        "avg_inference_time": sum(self.results[mode]["inference_times"]) / len(self.results[mode]["inference_times"]) if self.results[mode]["inference_times"] else 0,
                        "total_inferences": len(self.results[mode]["inference_times"])
                    }
                else:
                    # CPU-based metrics
                    cpu_levels = [r.get("cpu_percent", 0) for r in readings]
                    summary[mode] = {
                        "avg_cpu_percent": sum(cpu_levels) / len(cpu_levels),
                        "max_cpu_percent": max(cpu_levels),
                        "readings_count": len(readings),
                        "avg_inference_time": sum(self.results[mode]["inference_times"]) / len(self.results[mode]["inference_times"]) if self.results[mode]["inference_times"] else 0,
                        "total_inferences": len(self.results[mode]["inference_times"])
                    }
        
        return summary

if __name__ == "__main__":
    experiment = PowerConsumptionExperiment()
    
    print("Power Consumption Experiment")
    print("1. Local only")
    print("2. Cloud only") 
    print("3. Both (comparison)")
    
    choice = input("Select experiment mode (1-3): ").strip()
    
    if choice == "1":
        experiment.run_experiment("local")
    elif choice == "2":
        experiment.run_experiment("cloud")
    elif choice == "3":
        experiment.run_experiment("both")
    else:
        print("Invalid choice. Running both comparison...")
        experiment.run_experiment("both") 