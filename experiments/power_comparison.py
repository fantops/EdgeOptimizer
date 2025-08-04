#!/usr/bin/env python3
"""
Power Comparison Experiment for EdgeOptimizer
Enhanced with command line arguments for flexible testing
Usage: python power_comparison.py [local|cloud|both] [duration_seconds]
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path to import optimizer modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.monitor import PowerTracker
from optimizer.model_manager import get_model_manager  
from optimizer.config import get_config_manager
from optimizer.cloud_inference import CloudInferenceManager
from optimizer.experiment_runner import PowerExperimentRunner

# Import enhanced power monitoring
from enhanced_power_monitor import PowerConsumptionMonitor

# Import centralized logging
from optimizer.logging_config import get_logger, save_experiment_results

# Setup experiment logging using centralized system
def setup_experiment_logging():
    """Setup logging for power comparison experiments using centralized system"""
    return get_logger('PowerComparison', 'experiments')

logger = setup_experiment_logging()


class PowerComparisonExperiment:
    """Enhanced power comparison experiment with advanced power monitoring"""
    
    def __init__(self, mode: str = "both", duration: int = 300):
        self.mode = mode.lower()
        
        # Validate mode
        if self.mode not in ["local", "cloud", "both"]:
            raise ValueError(f"Invalid mode '{mode}'. Use 'local', 'cloud', or 'both'")
            
        # Load configuration
        self.config_manager = get_config_manager()
        self.config = self.config_manager.load_config("experiment_config")
        
        # Initialize modular components
        self.model_manager = get_model_manager()
        self.power_tracker = PowerTracker()
        self.cloud_manager = CloudInferenceManager(self.config)
        self.experiment_runner = PowerExperimentRunner(duration, self.power_tracker, logger)
        
        # Initialize enhanced power monitoring
        self.power_monitor = PowerConsumptionMonitor(sampling_rate=0.1)  # High frequency monitoring
        
        print(f"🧪 Power Comparison Experiment Initialized")
        print(f"🎯 Mode: {self.mode.upper()}")
        print(f"📖 Local model: {self.config.get('inference_settings', {}).get('local_model', 'gpt2')}")
        print(f"☁️  Cloud provider: {self.cloud_manager.provider}")
        print(f"⏱️  Duration: {duration} seconds")
        print(f"⚡ Enhanced power monitoring enabled (0.1s sampling)")
        
        # Set power baseline
        self.power_monitor.set_baseline()
        
    def run_local_inference(self, prompt: str) -> dict:
        """Run local inference using ModelManager"""
        model_name = self.config.get("inference_settings", {}).get("local_model", "gpt2")
        max_tokens = self.config.get("inference_settings", {}).get("local_max_tokens", 50)
        device = self.config.get("inference_settings", {}).get("local_device", "cpu")
        temperature = self.config.get("inference_settings", {}).get("temperature", 0.7)
        
        return self.model_manager.run_inference(
            model_name=model_name,
            prompt=prompt,
            max_length=max_tokens,
            device=device,
            temperature=temperature
        )
    
    def run_cloud_inference(self, prompt: str) -> dict:
        """Run cloud inference using CloudInferenceManager"""
        return self.cloud_manager.run_inference(prompt)
    
    def run_experiment(self):
        """Run the power comparison experiment with enhanced power monitoring"""
        print(f"\n🚀 Starting {self.mode.upper()} power comparison experiment...")
        
        # Get test prompts from config
        test_prompts = self.config.get("test_prompts", [
            "What is machine learning?",
            "How does a neural network work?",
            "Explain quantum computing"
        ])
        
        all_results = {}
        
        # Run experiments based on mode
        if self.mode in ["local", "both"]:
            logger.info("Starting LOCAL inference tests with enhanced power monitoring")
            print(f"\n📍 Running LOCAL inference tests with detailed power monitoring...")
            
            # Start enhanced power monitoring for local phase
            self.power_monitor.start_continuous_monitoring("local")
            
            local_results = self.experiment_runner.run_phase_with_power(
                phase_name="local",
                test_function=self.run_local_inference,
                prompts=test_prompts,
                interval=5
            )
            
            # Stop monitoring and analyze power consumption
            self.power_monitor.stop_monitoring()
            local_power_analysis = self.power_monitor.analyze_power_consumption("local")
            
            local_results["power_analysis"] = local_power_analysis
            all_results["local"] = local_results
            logger.info(f"LOCAL tests completed - {len(local_results.get('inference_times', []))} tests")
            
            # Print local power summary
            self._print_phase_power_summary("LOCAL", local_power_analysis)
            
        if self.mode in ["cloud", "both"]:
            logger.info("Starting CLOUD inference tests with enhanced power monitoring")
            print(f"\n☁️  Running CLOUD inference tests with detailed power monitoring...")
            
            # Start enhanced power monitoring for cloud phase
            self.power_monitor.start_continuous_monitoring("cloud")
            
            cloud_results = self.experiment_runner.run_phase_with_power(
                phase_name="cloud",
                test_function=self.run_cloud_inference,
                prompts=test_prompts,
                interval=5
            )
            
            # Stop monitoring and analyze power consumption
            self.power_monitor.stop_monitoring()
            cloud_power_analysis = self.power_monitor.analyze_power_consumption("cloud")
            
            cloud_results["power_analysis"] = cloud_power_analysis
            all_results["cloud"] = cloud_results
            logger.info(f"CLOUD tests completed - {len(cloud_results.get('inference_times', []))} tests")
            
            # Print cloud power summary
            self._print_phase_power_summary("CLOUD", cloud_power_analysis)
        
        # Enhanced power comparison analysis
        if "local" in all_results and "cloud" in all_results:
            print(f"\n🔋 Generating comprehensive power consumption comparison...")
            power_comparison = self.power_monitor.compare_power_consumption("local", "cloud")
            all_results["power_comparison"] = power_comparison
            
            # Print detailed power comparison
            self.power_monitor.print_power_summary(power_comparison)
            
            # Save detailed power analysis
            self.power_monitor.save_power_analysis(power_comparison)
        
        # Save and display results using centralized logging
        logger.info("Saving experiment results and generating summary")
        filename = save_experiment_results(all_results, "power_comparison")
        
        # Generate and print summary
        summary = self.experiment_runner.generate_summary(all_results)
        self.experiment_runner.print_summary(summary)
        
        logger.info("Experiment completed successfully")
        print(f"\n✅ Experiment completed!")
        if "local" in all_results:
            print(f"📊 Local tests: {len(all_results['local']['inference_times'])}")
        if "cloud" in all_results:
            print(f"📊 Cloud tests: {len(all_results['cloud']['inference_times'])}")
        print(f"📁 Results saved to: {filename}")
        
        return all_results
    
    def _print_phase_power_summary(self, phase_name: str, power_analysis: Dict[str, Any]):
        """Print power consumption summary for a specific phase"""
        if "error" in power_analysis:
            print(f"⚠️  Could not analyze power consumption for {phase_name}: {power_analysis['error']}")
            return
        
        print(f"\n⚡ {phase_name} POWER CONSUMPTION SUMMARY:")
        print("=" * 50)
        
        power_data = power_analysis["power_consumption"]
        print(f"📊 Power Score: {power_data['avg_power_score']:.2f} (peak: {power_data['peak_power_score']:.2f})")
        
        # Add actual power consumption estimates if available
        if "estimated_watts" in power_analysis.get("power_breakdown", {}):
            breakdown = power_analysis["power_breakdown"]
            print(f"⚡ Estimated Power: {breakdown['estimated_watts']:.1f}W avg (peak: {breakdown.get('peak_watts', breakdown['estimated_watts']):.1f}W)")
            print(f"   🔧 Processing overhead: {breakdown.get('processing_overhead_watts', 0):.1f}W")
            print(f"   💻 CPU contribution: {breakdown.get('cpu_contribution_percent', 0):.1f}%")
            if breakdown.get('efficiency', {}):
                efficiency = breakdown['efficiency']
                print(f"   📈 Power efficiency: {efficiency.get('efficiency_score', 0):.1f}/100")
        
        if power_analysis["battery"]["available"]:
            battery = power_analysis["battery"]
            # Enhanced battery drain reporting with better explanations
            initial_pct = battery.get('initial_percent', 0)
            final_pct = battery.get('final_percent', 0)
            drain_pct = battery['total_drain_percent']
            drain_rate = battery['drain_rate_per_hour']
            power_source = battery.get('power_source', 'Unknown')
            
            print(f"🔋 Battery Analysis:")
            print(f"   Initial: {initial_pct:.1f}% → Final: {final_pct:.1f}% (Power: {power_source})")
            
            if drain_pct > 0:
                print(f"   ⬇️  Power Drain: {drain_pct:.3f}% ({drain_rate:.3f}%/hour)")
                if battery["estimated_remaining_hours"] < 100:
                    print(f"   ⏱️  Est. remaining: {battery['estimated_remaining_hours']:.1f} hours")
            elif drain_pct < 0:
                print(f"   ⬆️  Battery Charged: {abs(drain_pct):.3f}% during test (plugged in)")
                print(f"   🔌 Charging rate: {abs(drain_rate):.3f}%/hour")
            else:
                print(f"   🔹 No battery change detected")
        else:
            print(f"🔋 Battery: Not available (likely desktop/AC powered)")
        
        cpu_data = power_analysis["cpu_power"]
        print(f"💻 CPU: {cpu_data['avg_usage_percent']:.1f}% avg (peak: {cpu_data['peak_usage_percent']:.1f}%)")
        print(f"🔥 CPU Power Score: {cpu_data['avg_power_score']:.2f}")
        
        if power_analysis["thermal"]["available"]:
            thermal = power_analysis["thermal"]
            print(f"🌡️  Thermal: {thermal['avg_temperature']:.1f}°C avg (peak: {thermal['peak_temperature']:.1f}°C)")
            print(f"📈 Temperature rise: {thermal['temperature_rise']:.1f}°C")
        
        print("=" * 50)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="EdgeOptimizer Power Comparison Experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python power_comparison.py                    # Run both local and cloud (default)
  python power_comparison.py local             # Run only local inference
  python power_comparison.py cloud             # Run only cloud inference  
  python power_comparison.py both 300          # Run both for 300 seconds
  python power_comparison.py cloud 60          # Run cloud only for 60 seconds
        """
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        default='both',
        choices=['local', 'cloud', 'both'],
        help='Experiment mode: local, cloud, or both (default: both)'
    )
    
    parser.add_argument(
        'duration',
        nargs='?', 
        type=int,
        help='Experiment duration in seconds (default: from config file)'
    )
    
    parser.add_argument(
        '--test-api',
        action='store_true',
        help='Test API connection before running experiment'
    )
    
    return parser.parse_args()


def test_api_connection(experiment):
    """Test API connections before running experiment"""
    print("🔍 Testing API connections...")
    
    # Test local model loading
    try:
        model_name = experiment.config.get("inference_settings", {}).get("local_model", "gpt2")
        print(f"  📍 Testing local model ({model_name})...")
        result = experiment.run_local_inference("Test")
        if result.get("success"):
            print(f"  ✅ Local model works (time: {result.get('inference_time', 0):.3f}s)")
        else:
            print(f"  ❌ Local model failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Local model error: {e}")
    
    # Test cloud API
    try:
        print(f"  ☁️  Testing cloud API ({experiment.cloud_manager.provider})...")
        result = experiment.run_cloud_inference("Test")
        if result.get("success"):
            print(f"  ✅ Cloud API works (time: {result.get('inference_time', 0):.3f}s)")
        else:
            print(f"  ❌ Cloud API failed: {result.get('response', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ Cloud API error: {e}")


def main():
    """Run the power comparison experiment with argument parsing"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        logger.info("Starting EdgeOptimizer Power Comparison Experiment")
        logger.info(f"Mode: {args.mode.upper()}, Test API: {args.test_api}")
        
        # Load config to get experiment duration
        config_manager = get_config_manager()
        experiment_config = config_manager.load_config("experiment_config")
        
        # Use provided duration or config default
        duration = args.duration if args.duration else experiment_config.get("experiment_duration", 180)
        
        logger.info(f"Experiment duration: {duration} seconds")
        logger.info(f"Local model: {experiment_config.get('inference_settings', {}).get('local_model', 'gpt2')}")
        logger.info(f"Cloud provider: {experiment_config.get('cloud_provider', 'huggingface')}")
        
        print(f"🧪 EdgeOptimizer Power Comparison Experiment")
        print(f"🎯 Mode: {args.mode.upper()}")
        print(f"⏱️  Duration: {duration} seconds")
        print(f"📖 Local model: {experiment_config.get('inference_settings', {}).get('local_model', 'gpt2')}")
        print(f"☁️  Cloud provider: {experiment_config.get('cloud_provider', 'huggingface')}")
        
        # Initialize experiment
        experiment = PowerComparisonExperiment(args.mode, duration)
        
        # Test API connections if requested
        if args.test_api:
            test_api_connection(experiment)
            print("\n" + "="*50)
        
        # Run the experiment
        experiment.run_experiment()
        
    except KeyboardInterrupt:
        print("\n🛑 Experiment interrupted by user")
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
