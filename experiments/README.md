# Power Consumption Experiments

This directory contains experiments to measure and compare power consumption between local and cloud-based LLM inference.

## Power Comparison Experiment

### Overview
The `power_comparison.py` script runs LLM inference both locally (using ONNX) and via cloud API (OpenAI) for a specified duration, measuring power consumption throughout the experiment.

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download the model:**
   ```bash
   python models/download_model.py
   ```

3. **Run the experiment:**
   ```bash
   python experiments/power_comparison.py
   ```

**Note:** OpenAI API key is already configured in `configs/experiment_config.json`.

### Running the Experiment

```bash
python experiments/power_comparison.py
```

**Experiment Modes:**
- **Local only**: Run local inference for 1 hour
- **Cloud only**: Run cloud inference for 1 hour  
- **Both**: Run both simultaneously for comparison

### What Gets Measured

**Power Metrics:**
- Battery percentage (if available)
- CPU usage percentage
- Memory usage percentage
- Thermal data (if enabled)

**Inference Metrics:**
- Response times
- Success/failure rates
- Energy consumption estimates

### Results

Results are saved to `experiments/results_power_comparison_YYYYMMDD_HHMMSS.json` with:

- **Raw data**: Power readings with timestamps
- **Summary statistics**: Battery drain, CPU averages, etc.
- **Inference times**: Local vs cloud performance comparison
- **Energy estimates**: Power consumption analysis

### Analysis

After running experiments, you can:

1. **Compare power efficiency** between local vs cloud
2. **Optimize EdgeOptimizer thresholds** based on real data
3. **Identify power consumption patterns** during inference
4. **Plan hybrid strategies** (local for short queries, cloud for complex ones)

### Example Analysis

```python
import json

# Load results
with open('experiments/results_power_comparison_20241201_143022.json') as f:
    data = json.load(f)

# Compare battery drain
local_drain = data['summary']['local']['battery_drain']
cloud_drain = data['summary']['cloud']['battery_drain']

print(f"Local battery drain: {local_drain}%")
print(f"Cloud battery drain: {cloud_drain}%")
print(f"Power efficiency ratio: {cloud_drain/local_drain:.2f}x")

# Compare inference times
local_avg_time = data['summary']['local']['avg_inference_time']
cloud_avg_time = data['summary']['cloud']['avg_inference_time']

print(f"Local avg inference time: {local_avg_time:.3f}s")
print(f"Cloud avg inference time: {cloud_avg_time:.3f}s")
```

### Tips for Accurate Results

1. **Run on battery power** (not plugged in)
2. **Close other applications** to minimize interference
3. **Use consistent prompts** across runs
4. **Run multiple times** and average results
5. **Monitor system temperature** to avoid throttling

### Configuration

Edit `configs/experiment_config.json` to customize:

```json
{
  "experiment_duration": 3600,  // 1 hour in seconds
  "sampling_interval": 5,       // Power measurement frequency
  "test_prompts": [...],        // Custom test prompts
  "power_measurement": {
    "enable_battery_monitoring": true,
    "enable_cpu_monitoring": true,
    "enable_memory_monitoring": true
  }
}
```

### Next Steps

Based on your experiment results, you can:

- **Tune EdgeOptimizer thresholds** in `configs/optimizer_config.json`
- **Implement hybrid strategies** in `optimizer/agent.py`
- **Add power prediction** to `optimizer/monitor.py`
- **Create power-aware scheduling** algorithms 