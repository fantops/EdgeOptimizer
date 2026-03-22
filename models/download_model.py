#!/usr/bin/env python3
"""
Model Downloader for EdgeOptimizer
Downloads and converts lightweight models suitable for edge devices
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import onnxruntime as ort
from pathlib import Path

# Default Hugging Face model for ONNX export (small, works well on macOS CPU)
DEFAULT_HF_MODEL = "gpt2"


class ModelDownloader:
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

    def download_tiny_model(self, model_name: str = DEFAULT_HF_MODEL):
        """Download a small causal LM and export to ONNX as models/model.onnx."""
        print(f"Downloading {model_name}...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )

            tokenizer.save_pretrained(self.models_dir / "tokenizer")
            torch.save(model.state_dict(), self.models_dir / "model.pt")
            self.convert_to_onnx(model, tokenizer)

            print("✅ Model downloaded and converted successfully!")
            return True

        except Exception as e:
            print(f"❌ Error downloading {model_name}: {e}")
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
            self.models_dir / "model.onnx",
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
            onnx_path = self.models_dir / "model.onnx"
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
        print("1. Copy configs/experiment_config.template.json → configs/experiment_config.json")
        print("2. Set OPENAI_API_KEY (or cloud token) — see README.md")
        print("3. Run: python experiments/power_comparison.py")
        print("4. Check results under experiments/")
    else:
        print("\n❌ Model download failed. Please check your internet connection.")

if __name__ == "__main__":
    main() 