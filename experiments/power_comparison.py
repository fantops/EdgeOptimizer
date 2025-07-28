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

# Add parent directory to path to import optimizer modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.monitor import PowerTracker
from optimizer.model_manager import get_model_manager  
from optimizer.config import get_config_manager
from optimizer.cloud_inference import CloudInferenceManager
from optimizer.experiment_runner import PowerExperimentRunner

# Setup experiment logging
def setup_experiment_logging():
    """Setup logging for power comparison experiments"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{log_dir}/power_comparison_{timestamp}.log"
    
    # Create a specific logger for this experiment
    logger = logging.getLogger('PowerComparison')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_experiment_logging()


class PowerComparisonExperiment:
    """Enhanced power comparison experiment with mode selection"""
    
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
        
        print(f"🧪 Power Comparison Experiment Initialized")
        print(f"🎯 Mode: {self.mode.upper()}")
        print(f"📖 Local model: {self.config.get('inference_settings', {}).get('local_model', 'gpt2')}")
        print(f"☁️  Cloud provider: {self.cloud_manager.provider}")
        print(f"⏱️  Duration: {duration} seconds")
        
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
        """Run the power comparison experiment based on selected mode"""
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
            logger.info("Starting LOCAL inference tests")
            print(f"\n📍 Running LOCAL inference tests...")
            local_results = self.experiment_runner.run_phase_with_power(
                phase_name="local",
                test_function=self.run_local_inference,
                prompts=test_prompts,
                interval=5
            )
            all_results["local"] = local_results
            logger.info(f"LOCAL tests completed - {len(local_results.get('inference_times', []))} tests")
            
        if self.mode in ["cloud", "both"]:
            logger.info("Starting CLOUD inference tests")
            print(f"\n☁️  Running CLOUD inference tests...")
            cloud_results = self.experiment_runner.run_phase_with_power(
                phase_name="cloud",
                test_function=self.run_cloud_inference,
                prompts=test_prompts,
                interval=5
            )
            all_results["cloud"] = cloud_results
            logger.info(f"CLOUD tests completed - {len(cloud_results.get('inference_times', []))} tests")
        
        # Save and display results
        logger.info("Saving experiment results and generating summary")
        filename = self.experiment_runner.save_results(all_results, include_summary=True)
        
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
