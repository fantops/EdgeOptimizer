#!/usr/bin/env python3
"""
EdgeOptimizer Main Application
A power-aware local LLM chatbot with system optimization
"""

import sys
from app.chatbot import SimpleChatbot
from optimizer.agent import EdgeOptimizerAgent
from optimizer.config import get_config_manager
from optimizer.logger import get_logger, log_system_status


def main():
    """Main application loop with enhanced optimization"""
    print("🚀 EdgeOptimizer - Power-Aware Local AI")
    print("=" * 50)
    
    # Initialize logging
    logger = get_logger("Main")
    logger.info("EdgeOptimizer application starting")
    
    try:
        # Load configuration first
        config_manager = get_config_manager()
        optimizer_config = config_manager.load_config("optimizer_config")
        
        # Get model settings from config
        model_settings = optimizer_config.get("model_settings", {})
        default_model = model_settings.get("default_local_model", "gpt2")
        max_tokens = model_settings.get("max_tokens", 50)
        
        print(f"📖 Using model: {default_model}")
        print(f"🔢 Max tokens: {max_tokens}")
        logger.info(f"Configuration loaded - Model: {default_model}, Max tokens: {max_tokens}")
        
        # Initialize components
        print("Initializing components...")
        chatbot = SimpleChatbot(default_model)
        agent = EdgeOptimizerAgent()
        
        print("✅ EdgeOptimizer ready!")
        print("\nCommands:")
        print("  'info' - Show system status")
        print("  'status' - Show detailed system metrics")
        print("  'models' - Show loaded models")
        print("  'monitor' - Start continuous monitoring")
        print("  'quit' - Exit")
        print("  Or type any message for AI response")
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! EdgeOptimizer shutting down...")
                    agent.cleanup()
                    break
                
                elif user_input.lower() == 'info':
                    agent.log_status()
                
                elif user_input.lower() == 'status':
                    status = agent.get_system_status()
                    print("\n📊 Detailed System Status:")
                    print(f"   🔋 Battery: {status['battery_status']}")
                    print(f"   💻 CPU: {status['power_metrics'].get('cpu_percent')}%")
                    print(f"   🧠 Memory: {status['power_metrics'].get('memory_percent')}%")
                    print(f"   🤖 Models loaded: {len(status['loaded_models'])}")
                    
                elif user_input.lower() == 'models':
                    models = agent.model_manager.list_loaded_models()
                    print(f"\n🤖 Loaded Models ({len(models)}):")
                    for key, info in models.items():
                        print(f"   - {info['model_name']} on {info['device']}")
                
                elif user_input.lower() == 'monitor':
                    print("Starting monitoring mode (Ctrl+C to stop)...")
                    agent.start_monitoring(interval=10.0)
                
                elif user_input:
                    # Run optimized inference using config settings
                    print("🔥 EdgeOptimizer: Running optimized inference...")
                    
                    result = agent.run_optimized_inference(
                        prompt=user_input,
                        model_name=default_model,
                        max_length=max_tokens
                    )
                    
                    if result["success"]:
                        print(f"🤖 EdgeOptimizer ({result['inference_method']}): {result['response']}")
                        print(f"⏱️  Time: {result['inference_time']:.3f}s")
                    else:
                        print(f"⚠️ {result['response']}")
                        
                    # Show optimization decision if interesting
                    decision = result["optimization_decision"]
                    if not decision["can_run_local"]:
                        print(f"💡 Optimization: {', '.join(decision['reasons'])}")
                
            except KeyboardInterrupt:
                print("\n👋 EdgeOptimizer interrupted. Shutting down...")
                agent.cleanup()
                break
            except EOFError:
                print("\n👋 EdgeOptimizer shutting down...")
                agent.cleanup()
                break
    
    except Exception as e:
        print(f"❌ Failed to initialize EdgeOptimizer: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
