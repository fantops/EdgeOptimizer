#!/usr/bin/env python3
"""
Experiment Monitor for EdgeOptimizer
Monitor running experiments and display progress
"""

import os
import time
import json
from datetime import datetime

def monitor_experiment_logs():
    """Monitor the latest experiment log file"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print("❌ No logs directory found")
        return
    
    # Find the latest power comparison log
    log_files = [f for f in os.listdir(log_dir) if f.startswith("power_comparison_")]
    if not log_files:
        print("❌ No experiment logs found")
        return
    
    latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
    log_path = os.path.join(log_dir, latest_log)
    
    print(f"📊 Monitoring experiment log: {latest_log}")
    print("Press Ctrl+C to stop monitoring or wait 30 seconds for auto-timeout")
    print("=" * 50)
    
    # Follow the log file
    with open(log_path, 'r') as f:
        # Go to end of file
        f.seek(0, 2)  
        
        timeout_counter = 0
        max_timeout = 30  # 30 seconds timeout
        
        try:
            while timeout_counter < max_timeout:
                line = f.readline()
                if line:
                    print(line.strip())
                    timeout_counter = 0  # Reset timeout if we get new content
                else:
                    time.sleep(1)
                    timeout_counter += 1
                    if timeout_counter % 10 == 0:  # Show progress every 10 seconds
                        print(f"⏱️  Waiting for new log entries... ({timeout_counter}/{max_timeout}s)")
            
            print("\n⏰ Monitoring timeout reached (30s). Use option 2 for quick results view.")
            
        except KeyboardInterrupt:
            print("\n👋 Stopped monitoring")

def show_recent_results():
    """Show recent experiment results"""
    logs_dir = "logs"
    
    # Look for result files
    result_files = []
    if os.path.exists(logs_dir):
        result_files = [f for f in os.listdir(logs_dir) 
                       if f.startswith("power_comparison_results_") and f.endswith(".json")]
    
    if not result_files:
        print("❌ No experiment results found")
        return
    
    # Show the latest 3 results
    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
    
    print("📊 Recent Experiment Results:")
    print("=" * 50)
    
    for i, result_file in enumerate(result_files[:3]):
        result_path = os.path.join(logs_dir, result_file)
        try:
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            timestamp = result_file.split('_')[-2] + '_' + result_file.split('_')[-1].replace('.json', '')
            
            experiment_info = data.get('experiment_info', {})
            duration = experiment_info.get('duration', 0)
            
            print(f"\n{i+1}. {timestamp} - Duration: {duration}s")
            
            summary = data.get('summary', {})
            if 'local' in summary:
                local = summary['local']
                print(f"   📱 Local: {local.get('total_tests', 0)} tests, "
                      f"{local.get('success_rate', 0)*100:.1f}% success, "
                      f"{local.get('avg_inference_time', 0):.2f}s avg")
            
            if 'cloud' in summary:
                cloud = summary['cloud']
                print(f"   ☁️  Cloud: {cloud.get('total_tests', 0)} tests, "
                      f"{cloud.get('success_rate', 0)*100:.1f}% success, "
                      f"{cloud.get('avg_inference_time', 0):.2f}s avg")
            
        except Exception as e:
            print(f"   ❌ Error reading {result_file}: {e}")

def main():
    """Main monitor function"""
    print("🔍 EdgeOptimizer Experiment Monitor")
    print("Choose an option:")
    print("1. Monitor live experiment logs (auto-timeout after 30s)")
    print("2. Show recent results (recommended for completed experiments)")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        monitor_experiment_logs()
    elif choice == "2":
        show_recent_results()
    elif choice == "3":
        show_recent_results()
        print("\n" + "="*50)
        monitor_experiment_logs()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
