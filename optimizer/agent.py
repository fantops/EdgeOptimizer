import json
import os
import time

import psutil

_CONFIG_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs")
)


class EdgeOptimizerAgent:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(_CONFIG_DIR, "optimizer_config.json")
        with open(config_path, encoding="utf-8") as f:
            self.config = json.load(f)

    def should_run(self):
        battery = psutil.sensors_battery()
        if battery and battery.percent < self.config["battery_threshold"]:
            return False
        return True

    def log_status(self):
        print(f"Battery level OK: {psutil.sensors_battery().percent}%") 