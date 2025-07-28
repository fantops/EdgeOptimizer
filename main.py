from app.chatbot import PhiChatbot
from optimizer.agent import EdgeOptimizerAgent
import time

if __name__ == "__main__":
    chatbot = PhiChatbot("models/phi.onnx")
    agent = EdgeOptimizerAgent()

    while True:
        if agent.should_run():
            prompt = input("You: ")
            print("Bot:", chatbot.run_inference(prompt))
        else:
            print("[EdgeOptimizer] Inference skipped to save power.")
            time.sleep(10)
