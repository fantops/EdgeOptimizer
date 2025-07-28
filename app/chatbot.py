import onnxruntime as ort
import json
import torch
from transformers import AutoTokenizer
import numpy as np
import time

class PhiChatbot:
    def __init__(self, model_path="models/phi.onnx"):
        self.model_path = model_path
        self.session = None
        self.tokenizer = None
        self.load_model()
        
    def load_model(self):
        """Load ONNX model and tokenizer"""
        try:
            # Load ONNX model
            self.session = ort.InferenceSession(self.model_path)
            print(f"✅ Loaded ONNX model: {self.model_path}")
            
            # Load tokenizer
            try:
                self.tokenizer = AutoTokenizer.from_pretrained("models/tokenizer")
                print("✅ Loaded tokenizer")
            except:
                # Fallback to GPT-2 tokenizer if custom tokenizer not found
                self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
                print("✅ Loaded GPT-2 tokenizer as fallback")
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Please run: python models/download_model.py")
            raise
    
    def tokenize_input(self, text):
        """Tokenize input text"""
        try:
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Tokenize with padding
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            return inputs['input_ids'].numpy()
            
        except Exception as e:
            print(f"❌ Tokenization error: {e}")
            # Return dummy input as fallback
            return np.array([[101, 2009, 2003, 1037, 3978, 102]])
    
    def run_inference(self, input_text):
        """Run inference on input text"""
        try:
            start_time = time.time()
            
            # Tokenize input
            input_ids = self.tokenize_input(input_text)
            
            # Run ONNX inference
            outputs = self.session.run(
                None, 
                {"input_ids": input_ids}
            )
            
            # Get logits
            logits = outputs[0]
            
            # Generate response (simplified - just get next token)
            next_token = np.argmax(logits[0, -1, :])
            
            # Decode response
            response_tokens = [next_token]
            response_text = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            inference_time = time.time() - start_time
            
            return {
                "response": response_text,
                "inference_time": inference_time,
                "input_length": len(input_ids[0]),
                "model_path": self.model_path
            }
            
        except Exception as e:
            return {
                "response": f"Inference error: {e}",
                "inference_time": 0,
                "input_length": 0,
                "model_path": self.model_path
            }

if __name__ == "__main__":
    chatbot = PhiChatbot()
    print("🤖 EdgeOptimizer Chatbot Ready!")
    print("Type 'quit' to exit")
    
    while True:
        try:
            prompt = input("\nYou: ")
            if prompt.lower() == 'quit':
                break
                
            result = chatbot.run_inference(prompt)
            print(f"Bot: {result['response']}")
            print(f"[Inference time: {result['inference_time']:.3f}s]")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}") 