#!/usr/bin/env python3
"""
Power Monitoring Validation Tests
Tests power monitoring functionality specifically
"""

import sys
import os
import unittest
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPowerMonitoringIntegration(unittest.TestCase):
    """Test power monitoring integration"""
    
    def test_power_monitor_workflow(self):
        """Test complete power monitoring workflow"""
        try:
            # Test enhanced power monitor
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            from enhanced_power_monitor import PowerConsumptionMonitor
            
            # Initialize monitor
            monitor = PowerConsumptionMonitor(sampling_rate=1.0)  # 1 second for testing
            self.assertIsNotNone(monitor)
            
            # Test baseline setting
            monitor.set_baseline()
            
            # Test metrics collection
            metrics = monitor.get_detailed_power_metrics()
            self.assertIsInstance(metrics, dict)
            self.assertIn('estimated_power_draw', metrics)
            self.assertIn('cpu_power', metrics)
            
            print("✅ Power monitoring workflow test passed")
            
        except ImportError as e:
            self.skipTest(f"Enhanced power monitor not available: {e}")
        except Exception as e:
            self.fail(f"Power monitoring workflow failed: {e}")
    
    def test_system_monitor_metrics(self):
        """Test system monitor can collect basic metrics"""
        try:
            from optimizer.monitor import SystemMonitor
            
            monitor = SystemMonitor()
            
            # Test power metrics collection
            power_metrics = monitor.get_power_metrics()
            self.assertIsInstance(power_metrics, dict)
            self.assertIn('timestamp', power_metrics)
            
            # Test battery status
            battery_status = monitor.get_battery_status()
            self.assertIsInstance(battery_status, dict)
            
            print("✅ System monitor metrics test passed")
            
        except Exception as e:
            self.fail(f"System monitor metrics failed: {e}")
    
    def test_power_calculation_components(self):
        """Test power calculation components work"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'experiments'))
            from enhanced_power_monitor import PowerConsumptionMonitor
            
            monitor = PowerConsumptionMonitor()
            
            # Test power estimation with proper parameters
            metrics = monitor.get_detailed_power_metrics()
            self.assertIsInstance(metrics, dict)
            
            # Should have key power metrics
            self.assertIn('estimated_power_draw', metrics)
            power_data = metrics['estimated_power_draw']
            self.assertIn('total_power_score', power_data)
            self.assertIn('power_level', power_data)
            
            print("✅ Power calculation components test passed")
            
        except ImportError as e:
            self.skipTest(f"Enhanced power monitor not available: {e}")
        except Exception as e:
            self.fail(f"Power calculation failed: {e}")


class TestExperimentComponents(unittest.TestCase):
    """Test experiment-related components"""
    
    def test_experiment_runner_basic(self):
        """Test ExperimentRunner basic functionality"""
        try:
            from optimizer.experiment_runner import ExperimentRunner
            
            # Test initialization
            runner = ExperimentRunner(duration=1)  # 1 second for testing
            self.assertIsNotNone(runner)
            
            print("✅ ExperimentRunner basic test passed")
            
        except Exception as e:
            self.fail(f"ExperimentRunner test failed: {e}")
    
    def test_power_experiment_runner(self):
        """Test PowerExperimentRunner if available"""
        try:
            from optimizer.experiment_runner import PowerExperimentRunner
            from optimizer.monitor import PowerTracker
            from optimizer.logging_config import get_logger
            
            # Create components
            power_tracker = PowerTracker()
            logger = get_logger('TestPowerExperiment', 'system')
            
            # Test initialization
            runner = PowerExperimentRunner(
                duration=1,  # 1 second for testing
                power_tracker=power_tracker,
                logger=logger
            )
            self.assertIsNotNone(runner)
            
            print("✅ PowerExperimentRunner test passed")
            
        except Exception as e:
            self.fail(f"PowerExperimentRunner test failed: {e}")


if __name__ == '__main__':
    print("⚡ Running Power Monitoring Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2)
