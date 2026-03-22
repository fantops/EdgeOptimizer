from app.chatbot import OnnxChatbot
from optimizer.agent import EdgeOptimizerAgent
import time

if __name__ == "__main__":
    chatbot = OnnxChatbot("models/model.onnx")
    agent = EdgeOptimizerAgent()

    while True:
        if agent.should_run():
            prompt = input("You: ")
            print("Bot:", chatbot.run_inference(prompt))
        else:
            print("[EdgeOptimizer] Inference skipped to save power.")
            time.sleep(10)
