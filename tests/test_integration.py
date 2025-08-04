#!/usr/bin/env python3
"""
Basic Integration Tests for EdgeOptimizer
Tests core functionality and imports for power comparison platform
"""

import sys
import os
import unittest
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBasicImports(unittest.TestCase):
    """Test that all essential modules import correctly"""
    
    def test_main_module_import(self):
        """Test main module imports without errors"""
        try:
            import main
            self.assertTrue(True, "Main module imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")
    
    def test_optimizer_components_import(self):
        """Test optimizer components import correctly"""
        try:
            from optimizer import (
                get_model_manager,
                get_config_manager,
                PowerTracker,
                SystemMonitor
            )
            self.assertTrue(True, "Optimizer components imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import optimizer components: {e}")
    
    def test_power_comparison_import(self):
        """Test power comparison module imports"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            import power_comparison
            self.assertTrue(True, "Power comparison module imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import power_comparison: {e}")
    
    def test_enhanced_power_monitor_import(self):
        """Test enhanced power monitor imports"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            from enhanced_power_monitor import PowerConsumptionMonitor
            self.assertTrue(True, "Enhanced power monitor imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import enhanced_power_monitor: {e}")
    
    def test_logging_config_import(self):
        """Test centralized logging system imports"""
        try:
            from optimizer.logging_config import EdgeOptimizerLogger, get_logger
            self.assertTrue(True, "Logging system imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import logging system: {e}")


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration file loading and validation"""
    
    def setUp(self):
        """Set up test configuration"""
        self.test_config = {
            "experiment_duration": 60,
            "cloud_api_key": "test_key",
            "cloud_model": "test_model",
            "test_prompts": ["Test prompt"]
        }
        
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_config, self.temp_config)
        self.temp_config.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager can be initialized"""
        try:
            from optimizer.config import ConfigManager
            config_manager = ConfigManager()
            self.assertIsNotNone(config_manager, "ConfigManager initialized successfully")
        except Exception as e:
            self.fail(f"Failed to initialize ConfigManager: {e}")
    
    def test_json_config_loading(self):
        """Test JSON configuration loading"""
        try:
            with open(self.temp_config.name, 'r') as f:
                loaded_config = json.load(f)
            
            self.assertEqual(loaded_config['experiment_duration'], 60)
            self.assertEqual(loaded_config['cloud_api_key'], "test_key")
            self.assertTrue(True, "JSON config loaded successfully")
        except Exception as e:
            self.fail(f"Failed to load JSON config: {e}")


class TestPowerMonitoring(unittest.TestCase):
    """Test power monitoring functionality"""
    
    def test_system_monitor_initialization(self):
        """Test SystemMonitor can be initialized"""
        try:
            from optimizer.monitor import SystemMonitor
            monitor = SystemMonitor()
            self.assertIsNotNone(monitor, "SystemMonitor initialized successfully")
        except Exception as e:
            self.fail(f"Failed to initialize SystemMonitor: {e}")
    
    def test_power_tracker_initialization(self):
        """Test PowerTracker can be initialized"""
        try:
            from optimizer.monitor import PowerTracker
            tracker = PowerTracker()
            self.assertIsNotNone(tracker, "PowerTracker initialized successfully")
        except Exception as e:
            self.fail(f"Failed to initialize PowerTracker: {e}")
    
    def test_enhanced_power_monitor_initialization(self):
        """Test PowerConsumptionMonitor can be initialized"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            from enhanced_power_monitor import PowerConsumptionMonitor
            monitor = PowerConsumptionMonitor()
            self.assertIsNotNone(monitor, "PowerConsumptionMonitor initialized successfully")
        except Exception as e:
            self.fail(f"Failed to initialize PowerConsumptionMonitor: {e}")
    
    def test_power_metrics_collection(self):
        """Test basic power metrics can be collected"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            from enhanced_power_monitor import PowerConsumptionMonitor
            
            monitor = PowerConsumptionMonitor()
            metrics = monitor.get_detailed_power_metrics()
            
            # Check that essential metrics are present
            self.assertIn('estimated_power_draw', metrics)
            self.assertIn('cpu_power', metrics)
            self.assertTrue(True, "Power metrics collected successfully")
        except Exception as e:
            self.fail(f"Failed to collect power metrics: {e}")


class TestLoggingSystem(unittest.TestCase):
    """Test centralized logging system"""
    
    def test_edge_optimizer_logger_initialization(self):
        """Test EdgeOptimizerLogger can be initialized"""
        try:
            from optimizer.logging_config import EdgeOptimizerLogger
            logger = EdgeOptimizerLogger()
            self.assertIsNotNone(logger, "EdgeOptimizerLogger initialized successfully")
        except Exception as e:
            self.fail(f"Failed to initialize EdgeOptimizerLogger: {e}")
    
    def test_get_logger_function(self):
        """Test get_logger function works"""
        try:
            from optimizer.logging_config import get_logger
            logger = get_logger('TestLogger', 'system')
            self.assertIsNotNone(logger, "get_logger function works")
        except Exception as e:
            self.fail(f"Failed to get logger: {e}")
    
    def test_log_directory_creation(self):
        """Test log directories are created properly"""
        try:
            from optimizer.logging_config import EdgeOptimizerLogger
            logger_manager = EdgeOptimizerLogger()
            
            # Check that log directories exist
            base_dir = Path("logs")
            expected_dirs = ["power_analysis", "experiments", "system", "archive"]
            
            for dir_name in expected_dirs:
                dir_path = base_dir / dir_name
                self.assertTrue(dir_path.exists(), f"Log directory {dir_name} should exist")
                
            self.assertTrue(True, "Log directories created successfully")
        except Exception as e:
            self.fail(f"Failed to create log directories: {e}")


class TestExperimentWorkflow(unittest.TestCase):
    """Test basic experiment workflow components"""
    
    def test_experiment_runner_import(self):
        """Test ExperimentRunner can be imported"""
        try:
            from optimizer.experiment_runner import ExperimentRunner
            self.assertTrue(True, "ExperimentRunner imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import ExperimentRunner: {e}")
    
    def test_power_comparison_help(self):
        """Test power comparison script has help functionality"""
        try:
            import subprocess
            result = subprocess.run([
                'python3', 
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments', 'power_comparison.py'),
                '--help'
            ], capture_output=True, text=True, timeout=10)
            
            self.assertEqual(result.returncode, 0, "Power comparison help should work")
            self.assertIn('EdgeOptimizer Power Comparison', result.stdout)
            self.assertTrue(True, "Power comparison help works")
        except Exception as e:
            self.fail(f"Power comparison help failed: {e}")


if __name__ == '__main__':
    print("🧪 Running EdgeOptimizer Integration Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestBasicImports,
        TestConfigurationLoading,
        TestPowerMonitoring,
        TestLoggingSystem,
        TestExperimentWorkflow
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed! EdgeOptimizer is ready.")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        print("🔧 Please fix issues before proceeding")
    
    print(f"📊 Tests run: {result.testsRun}")
    print(f"⏱️  Time: {result.testsRun} tests completed")
