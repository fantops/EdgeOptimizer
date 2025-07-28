#!/usr/bin/env python3
"""
Model Downloader for EdgeOptimizer
Downloads and converts lightweight models suitable for edge devices
"""

import os
import requests
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import onnx
import onnxruntime as ort
from pathlib import Path

class ModelDownloader:
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
    def download_tiny_model(self):
        """Download a tiny, efficient model for edge devices"""
        
        # Option 1: Microsoft Phi-2 (if available) - lightweight and efficient
        model_name = "microsoft/phi-2"
        
        # Option 2: TinyLlama - very small, good for edge
        # model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        # Option 3: GPT-2 small - well-tested, lightweight
        # model_name = "gpt2"
        
        print(f"Downloading {model_name}...")
        
        try:
            # Download tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Use float32 for compatibility
                low_cpu_mem_usage=True
            )
            
            # Save tokenizer
            tokenizer.save_pretrained(self.models_dir / "tokenizer")
            
            # Save PyTorch model
            torch.save(model.state_dict(), self.models_dir / "model.pt")
            
            # Convert to ONNX
            self.convert_to_onnx(model, tokenizer)
            
            print("✅ Model downloaded and converted successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {model_name}: {e}")
            print("Trying fallback model...")
            return self.download_fallback_model()
    
    def download_fallback_model(self):
        """Download a simpler fallback model"""
        try:
            # Use GPT-2 as fallback - very reliable
            model_name = "gpt2"
            
            print(f"Downloading fallback model: {model_name}")
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Save tokenizer
            tokenizer.save_pretrained(self.models_dir / "tokenizer")
            
            # Save PyTorch model
            torch.save(model.state_dict(), self.models_dir / "model.pt")
            
            # Convert to ONNX
            self.convert_to_onnx(model, tokenizer)
            
            print("✅ Fallback model downloaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading fallback model: {e}")
            return False
    
    def convert_to_onnx(self, model, tokenizer):
        """Convert PyTorch model to ONNX format"""
        print("Converting to ONNX format...")
        
        # Set model to evaluation mode
        model.eval()
        
        # Create dummy input
        dummy_input = torch.randint(0, tokenizer.vocab_size, (1, 10))
        
        # Export to ONNX
        torch.onnx.export(
            model,
            dummy_input,
            self.models_dir / "phi.onnx",
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input_ids'],
            output_names=['logits'],
            dynamic_axes={
                'input_ids': {0: 'batch_size', 1: 'sequence'},
                'logits': {0: 'batch_size', 1: 'sequence'}
            }
        )
        
        print("✅ ONNX conversion completed!")
    
    def verify_model(self):
        """Verify the downloaded model works"""
        try:
            # Test ONNX model
            onnx_path = self.models_dir / "phi.onnx"
            if onnx_path.exists():
                session = ort.InferenceSession(str(onnx_path))
                print("✅ ONNX model verification successful!")
                return True
            else:
                print("❌ ONNX model not found!")
                return False
        except Exception as e:
            print(f"❌ Model verification failed: {e}")
            return False

def main():
    print("🚀 EdgeOptimizer Model Downloader")
    print("=" * 40)
    
    downloader = ModelDownloader()
    
    # Download model
    success = downloader.download_tiny_model()
    
    if success:
        # Verify model
        downloader.verify_model()
        
        print("\n📋 Next Steps:")
        print("1. Add your OpenAI API key to configs/experiment_config.json")
        print("2. Run the power consumption experiment:")
        print("   python experiments/power_comparison.py")
        print("3. Check the results in experiments/ directory")
    else:
        print("\n❌ Model download failed. Please check your internet connection.")

if __name__ == "__main__":
    main() 