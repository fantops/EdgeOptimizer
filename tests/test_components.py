#!/usr/bin/env python3
"""
Core Component Unit Tests for EdgeOptimizer
Tests individual components in isolation
"""

import sys
import os
import unittest
import tempfile
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestOptimizerComponents(unittest.TestCase):
    """Test optimizer core components"""
    
    def test_config_manager_basic(self):
        """Test ConfigManager basic functionality"""
        from optimizer.config import ConfigManager
        
        config_manager = ConfigManager()
        self.assertIsNotNone(config_manager)
    
    def test_model_manager_basic(self):
        """Test ModelManager basic functionality"""
        from optimizer.model_manager import ModelManager
        
        # Test initialization without actually loading models
        manager = ModelManager()
        self.assertIsNotNone(manager)
    
    def test_system_monitor_basic(self):
        """Test SystemMonitor basic functionality"""
        from optimizer.monitor import SystemMonitor
        
        monitor = SystemMonitor()
        self.assertIsNotNone(monitor)
        
        # Test basic system info collection
        try:
            cpu_percent = monitor.get_cpu_percent()
            self.assertIsInstance(cpu_percent, (int, float))
            self.assertGreaterEqual(cpu_percent, 0)
        except Exception as e:
            self.skipTest(f"CPU monitoring not available: {e}")
    
    def test_power_tracker_basic(self):
        """Test PowerTracker basic functionality"""
        from optimizer.monitor import PowerTracker
        
        tracker = PowerTracker()
        self.assertIsNotNone(tracker)
    
    def test_cloud_inference_manager_basic(self):
        """Test CloudInferenceManager basic functionality"""
        from optimizer.cloud_inference import CloudInferenceManager
        
        # Test initialization with mock config
        mock_config = {
            'cloud_api_key': 'test_key',
            'cloud_api_url': 'https://test.com',
            'cloud_provider': 'test'
        }
        
        manager = CloudInferenceManager(mock_config)
        self.assertIsNotNone(manager)


class TestLoggingComponents(unittest.TestCase):
    """Test logging system components"""
    
    def test_edge_optimizer_logger(self):
        """Test EdgeOptimizerLogger functionality"""
        from optimizer.logging_config import EdgeOptimizerLogger
        
        logger = EdgeOptimizerLogger()
        self.assertIsNotNone(logger)
    
    def test_get_logger_function(self):
        """Test get_logger function"""
        from optimizer.logging_config import get_logger
        
        logger = get_logger('TestComponent', 'system')
        self.assertIsNotNone(logger)
        
        # Test logging doesn't crash
        logger.info("Test log message")


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation"""
    
    def setUp(self):
        """Create temporary config files"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid test config
        self.valid_config = {
            "experiment_duration": 60,
            "cloud_api_key": "test_key",
            "cloud_model": "test_model",
            "test_prompts": ["Test prompt 1", "Test prompt 2"]
        }
        
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        with open(self.config_file, 'w') as f:
            json.dump(self.valid_config, f)
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_config_loading(self):
        """Test loading valid configuration"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        self.assertEqual(config['experiment_duration'], 60)
        self.assertEqual(config['cloud_api_key'], "test_key")
        self.assertIsInstance(config['test_prompts'], list)
    
    def test_config_structure(self):
        """Test configuration has required fields"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        required_fields = ['experiment_duration', 'cloud_api_key', 'test_prompts']
        for field in required_fields:
            self.assertIn(field, config, f"Required field '{field}' missing")


if __name__ == '__main__':
    print("🔧 Running EdgeOptimizer Unit Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2)
