import onnxruntime as ort
import json

class PhiChatbot:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(model_path)
        # Add tokenizer loading if needed

    def run_inference(self, input_text):
        # Tokenization logic placeholder
        inputs = {"input_ids": [[101, 2009, 2003, 1037, 3978, 102]]}  # Example input
        outputs = self.session.run(None, inputs)
        # Post-processing placeholder
        return "<response>"

if __name__ == "__main__":
    chatbot = PhiChatbot("../models/phi.onnx")
    while True:
        prompt = input("You: ")
        print("Bot:", chatbot.run_inference(prompt)) 