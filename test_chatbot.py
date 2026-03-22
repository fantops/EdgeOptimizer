#!/usr/bin/env python3
"""
Simple test script for EdgeOptimizer chatbot
Tests basic functionality without requiring model download
"""

import os
import time
import psutil
import json

def test_power_monitoring():
    """Test power monitoring functionality"""
    print("🔋 Testing Power Monitoring...")
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            print(f"✅ Battery: {battery.percent}%")
            print(f"✅ Plugged in: {battery.power_plugged}")
            if battery.secsleft != -1:
                print(f"✅ Time left: {battery.secsleft} seconds")
        else:
            print("⚠️  No battery info available")
            
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        print(f"✅ CPU: {cpu_percent}%")
        print(f"✅ Memory: {memory_percent}%")
        
        return True
    except Exception as e:
        print(f"❌ Power monitoring error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n⚙️  Testing Configuration Loading...")
    
    try:
        with open('configs/optimizer_config.json', 'r') as f:
            config = json.load(f)
        print(f"✅ Optimizer config loaded: {config}")
        
        exp_path = 'configs/experiment_config.json'
        if not os.path.exists(exp_path):
            exp_path = 'configs/experiment_config.template.json'
        with open(exp_path, 'r') as f:
            exp_config = json.load(f)
        print(f"✅ Experiment config loaded ({exp_path}): {len(exp_config['test_prompts'])} test prompts")
        
        return True
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        return False

def test_imports():
    """Test all required imports"""
    print("\n📦 Testing Imports...")
    
    try:
        import onnxruntime as ort
        print("✅ ONNX Runtime imported")
        
        import torch
        print("✅ PyTorch imported")
        
        import transformers
        print("✅ Transformers imported")
        
        import numpy as np
        print("✅ NumPy imported")
        
        import requests
        print("✅ Requests imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_simple_inference():
    """Test simple inference simulation"""
    print("\n🤖 Testing Simple Inference...")
    
    try:
        # Simulate inference time
        start_time = time.time()
        time.sleep(0.1)  # Simulate processing
        inference_time = time.time() - start_time
        
        print(f"✅ Simulated inference time: {inference_time:.3f}s")
        return True
    except Exception as e:
        print(f"❌ Inference test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 EdgeOptimizer Test Suite")
    print("=" * 40)
    
    tests = [
        ("Power Monitoring", test_power_monitoring),
        ("Configuration Loading", test_config_loading),
        ("Import Dependencies", test_imports),
        ("Simple Inference", test_simple_inference)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! EdgeOptimizer is ready for experiments.")
        print("\n🚀 Next steps:")
        print("1. Wait for model download to complete")
        print("2. Run: python experiments/power_comparison.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main() 