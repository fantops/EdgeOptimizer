#!/usr/bin/env python3
"""EdgeOptimizer entry point.

* ``python main.py profile ...`` — workload-agnostic ONNX profiler (the
  CV-story flow). Pass any ``.onnx`` and it runs synthetic-input forward
  passes through the four-signal pipeline.
* ``python main.py chat`` — interactive ONNX chatbot loop with the
  battery-aware scheduler in ``optimizer/agent.py``. Sample workload.
  Requires the optional ``torch`` + ``transformers`` extras (see
  ``requirements.txt``).
"""

from __future__ import annotations

import argparse
import sys
import time


def _cmd_profile(rest):
    from profiler.profile_cli import main as profile_main
    return profile_main(rest)


def _cmd_chat(_rest):
    from app.chatbot import OnnxChatbot
    from optimizer.agent import EdgeOptimizerAgent

    chatbot = OnnxChatbot("models/model.onnx")
    agent = EdgeOptimizerAgent()
    print("Chat mode. Ctrl+C to exit.")
    while True:
        try:
            if agent.should_run():
                prompt = input("You: ")
                print("Bot:", chatbot.run_inference(prompt))
            else:
                print("[EdgeOptimizer] Inference skipped to save power.")
                time.sleep(10)
        except (KeyboardInterrupt, EOFError):
            print()
            return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="edgeoptimizer")
    parser.add_argument("command", nargs="?", default="profile",
                        choices=("profile", "chat"))
    args, rest = parser.parse_known_args(argv)
    if args.command == "profile":
        return _cmd_profile(rest)
    return _cmd_chat(rest)


if __name__ == "__main__":
    sys.exit(main())
