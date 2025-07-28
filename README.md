# EdgeOptimizer
A power-aware local LLM chatbot running on Windows ARM using ONNX Runtime and the Phi model.

## Features
- Local inference using Phi ONNX model
- System-aware scheduling agent
- Power optimization based on battery/thermal status
- Power consumption experiments and analysis

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Model
```bash
python models/download_model.py
```

### 3. Run Power Experiment
```bash
python experiments/power_comparison.py
```

**Note:** OpenAI API key is already configured for cloud inference comparison.

## Run
```bash
python main.py
```

## Structure
- `app/`: Chatbot logic using Phi model
- `optimizer/`: Agent that monitors system and defers inference if needed
- `dashboard/`: Optional UI (to be developed)
- `models/`: Model files (e.g., phi.onnx)
- `configs/`: Configuration files (e.g., optimizer_config.json)
- `experiments/`: Power consumption experiments

## Directory Layout
```
edgeoptimizer/
├── app/
│   ├── chatbot.py
│   └── __init__.py
├── optimizer/
│   ├── agent.py
│   ├── config.py
│   ├── monitor.py
│   ├── model_manager.py
│   └── __init__.py
├── dashboard/
│   ├── app.py
│   └── templates/
├── models/
│   ├── phi.onnx
│   ├── tokenizer/
│   └── download_model.py
├── configs/
│   ├── optimizer_config.json
│   └── experiment_config.json
├── experiments/
│   ├── power_comparison.py
│   └── README.md
├── README.md
├── requirements.txt
└── main.py
```

## Power Consumption Experiments

Run comprehensive power consumption experiments to compare local vs cloud inference:

```bash
# Download model first
python models/download_model.py

# Run power experiment
python experiments/power_comparison.py
```

The experiment will:
- Run local inference using ONNX model
- Run cloud inference via OpenAI API
- Measure power consumption continuously
- Save detailed results for analysis

### Experiment Modes
1. **Local only**: Run local inference for 1 hour
2. **Cloud only**: Run cloud inference for 1 hour  
3. **Both**: Run both simultaneously for comparison

### Results
Results are saved to `experiments/results_power_comparison_YYYYMMDD_HHMMSS.json` with:
- Raw power readings with timestamps
- Summary statistics (battery drain, CPU averages, etc.)
- Inference time comparisons
- Energy consumption estimates

See `experiments/README.md` for detailed instructions.

## Configuration

### Experiment Settings
Edit `configs/experiment_config.json` to customize:
- Experiment duration (default: 1 hour)
- Sampling interval (default: 5 seconds)
- Test prompts
- Power measurement options

### Optimizer Settings
Edit `configs/optimizer_config.json` to adjust:
- Battery threshold (default: 20%)
- Temperature limits (default: 70°C)

## Development

### Adding Your Own Model
1. Place your ONNX model in `models/`
2. Update `app/chatbot.py` if needed
3. Test with `python app/chatbot.py`

### Extending the Optimizer
- Add new monitoring in `optimizer/monitor.py`
- Implement power prediction in `optimizer/model_manager.py`
- Create hybrid strategies in `optimizer/agent.py`

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License
MIT License - see [LICENSE](LICENSE) file.
