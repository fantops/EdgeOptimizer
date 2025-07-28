#!/usr/bin/env python3
"""
Simplified chatbot using EdgeOptimizer's modular components
"""

import sys
import os

# Add parent directory to path to import optimizer modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.model_manager import get_model_manager
from optimizer.config import get_config_manager
from typing import Dict, Any


class SimpleChatbot:
    """Simplified chatbot interface using EdgeOptimizer's ModelManager"""
    
    def __init__(self, model_name: str = None):
        # Load configuration to get default model if none specified
        self.config_manager = get_config_manager()
        
        if model_name is None:
            # Try to get default model from optimizer config
            optimizer_config = self.config_manager.load_config("optimizer_config", required=False)
            model_name = optimizer_config.get("model_settings", {}).get("default_local_model", "gpt2")
        
        self.model_name = model_name
        self.model_manager = get_model_manager()
        self.device = "cpu"  # Use CPU for edge compatibility
        
        # Pre-load the model
        print(f"🤖 Initializing SimpleChatbot with {model_name}")
        model_info = self.model_manager.load_model(model_name, self.device)
        
        if model_info["status"] == "error":
            print(f"⚠️ Model loading failed, will use mock responses")
            self.model = None
            self.tokenizer = None
        else:
            self.model = model_info["model"]
            self.tokenizer = model_info["tokenizer"]
        
    def run_inference(self, prompt: str, max_length: int = None, **kwargs) -> Dict[str, Any]:
        """Run inference using the model manager"""
        try:
            # Get default max_length from config if not specified
            if max_length is None:
                optimizer_config = self.config_manager.load_config("optimizer_config", required=False)
                max_length = optimizer_config.get("model_settings", {}).get("max_tokens", 50)
            
            if self.model is None or self.tokenizer is None:
                # Fallback for testing
                import time
                start_time = time.time()
                response = f"Mock response to: {prompt[:30]}..."
                inference_time = time.time() - start_time
                return {
                    "response": response,
                    "inference_time": inference_time,
                    "success": True,
                    "model_name": self.model_name,
                    "method": "mock"
                }
            
            # Use model manager for inference
            result = self.model_manager.run_inference(
                model_name=self.model_name,
                prompt=prompt,
                max_length=max_length,
                device=self.device,
                **kwargs
            )
            
            # Add method info
            result["method"] = "local"
            return result
            
        except Exception as e:
            import time
            return {
                "response": f"Error during inference: {e}",
                "inference_time": 0,
                "success": False,
                "model_name": self.model_name,
                "error": str(e),
                "method": "error"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return self.model_manager.get_model_info(self.model_name, self.device)
