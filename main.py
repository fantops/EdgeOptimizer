#!/usr/bin/env python3
"""EdgeOptimizer entry point.

Thin passthrough to the profile CLI:

    python main.py --model path/to/any.onnx [profile_cli args...]
"""

from __future__ import annotations

import sys

from profiler.profile_cli import main as profile_main


if __name__ == "__main__":
    sys.exit(profile_main(sys.argv[1:]))
