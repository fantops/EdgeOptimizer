import psutil
import time
import json

class EdgeOptimizerAgent:
    def __init__(self, config_path="../configs/optimizer_config.json"):
        with open(config_path) as f:
            self.config = json.load(f)

    def should_run(self):
        battery = psutil.sensors_battery()
        if battery and battery.percent < self.config["battery_threshold"]:
            return False
        return True

    def log_status(self):
        print(f"Battery level OK: {psutil.sensors_battery().percent}%") 