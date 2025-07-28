#!/usr/bin/env python3
"""
Model management utilities for EdgeOptimizer
Centralized model loading, caching, and inference management
"""

import os
import time
import json
import torch
from typing import Dict, Any, Optional, Union
from transformers import AutoTokenizer, AutoModelForCausalLM


class ModelManager:
    """Centralized model management for local inference"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/edgeoptimizer")
        self.models = {}  # Cache loaded models
        self.tokenizers = {}  # Cache tokenizers
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_model(self, model_name: str = "gpt2", device: str = "cpu") -> Dict[str, Any]:
        """Load a model and tokenizer with caching"""
        cache_key = f"{model_name}_{device}"
        
        # Return cached model if available
        if cache_key in self.models:
            return {
                "model": self.models[cache_key],
                "tokenizer": self.tokenizers[cache_key],
                "status": "cached",
                "model_name": model_name,
                "device": device
            }
        
        try:
            print(f"Loading {model_name} on {device}...")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            
            # Move to device
            device_obj = torch.device(device)
            model.to(device_obj)
            model.eval()
            
            # Cache the loaded model and tokenizer
            self.models[cache_key] = model
            self.tokenizers[cache_key] = tokenizer
            
            print(f"✅ Loaded {model_name} successfully")
            
            return {
                "model": model,
                "tokenizer": tokenizer,
                "status": "loaded",
                "model_name": model_name,
                "device": device
            }
            
        except Exception as e:
            print(f"❌ Error loading model {model_name}: {e}")
            return {
                "model": None,
                "tokenizer": None,
                "status": "error",
                "error": str(e),
                "model_name": model_name,
                "device": device
            }
    
    def run_inference(self, 
                     model_name: str,
                     prompt: str, 
                     max_length: int = 50,
                     device: str = "cpu",
                     temperature: float = 0.7,
                     **kwargs) -> Dict[str, Any]:
        """Run inference with a loaded model"""
        start_time = time.time()
        
        try:
            # Load model if not cached
            model_info = self.load_model(model_name, device)
            model = model_info["model"]
            tokenizer = model_info["tokenizer"]
            
            if model is None or tokenizer is None:
                return {
                    "response": f"Model loading failed: {model_info.get('error', 'Unknown error')}",
                    "inference_time": time.time() - start_time,
                    "success": False,
                    "model_name": model_name
                }
            
            # Tokenize input
            device_obj = torch.device(device)
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(device_obj)
            
            # Generate response
            with torch.no_grad():
                output = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=inputs.input_ids.shape[1] + max_length,
                    num_return_sequences=1,
                    do_sample=True,
                    temperature=temperature,
                    pad_token_id=tokenizer.eos_token_id,
                    no_repeat_ngram_size=2,
                    **kwargs
                )
            
            # Decode response
            response = tokenizer.decode(
                output[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            inference_time = time.time() - start_time
            
            return {
                "response": response,
                "inference_time": inference_time,
                "success": True,
                "model_name": model_name,
                "device": device
            }
            
        except Exception as e:
            inference_time = time.time() - start_time
            return {
                "response": f"Inference error: {e}",
                "inference_time": inference_time,
                "success": False,
                "model_name": model_name,
                "error": str(e)
            }
    
    def get_model_info(self, model_name: str, device: str = "cpu") -> Dict[str, Any]:
        """Get information about a loaded model"""
        cache_key = f"{model_name}_{device}"
        
        if cache_key not in self.models:
            return {"status": "not_loaded", "model_name": model_name}
        
        model = self.models[cache_key]
        
        try:
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            return {
                "model_name": model_name,
                "total_parameters": total_params,
                "trainable_parameters": trainable_params,
                "device": device,
                "status": "loaded",
                "memory_usage_mb": self._get_model_memory_usage(model)
            }
        except Exception as e:
            return {
                "model_name": model_name,
                "status": "error",
                "error": str(e)
            }
    
    def _get_model_memory_usage(self, model) -> float:
        """Estimate model memory usage in MB"""
        try:
            total_params = sum(p.numel() for p in model.parameters())
            # Rough estimate: 4 bytes per float32 parameter
            return (total_params * 4) / (1024 * 1024)
        except:
            return 0.0
    
    def unload_model(self, model_name: str, device: str = "cpu"):
        """Unload a model from cache to free memory"""
        cache_key = f"{model_name}_{device}"
        
        if cache_key in self.models:
            del self.models[cache_key]
            del self.tokenizers[cache_key]
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print(f"Unloaded {model_name} from {device}")
    
    def list_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """List all currently loaded models"""
        result = {}
        
        for cache_key in self.models.keys():
            model_name, device = cache_key.rsplit("_", 1)
            result[cache_key] = {
                "model_name": model_name,
                "device": device,
                "info": self.get_model_info(model_name, device)
            }
        
        return result


# Global model manager instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get the singleton model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
