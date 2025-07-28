# EdgeOptimizer
A modular, power-aware LLM chatbot for edge devices with comprehensive system optimization and power monitoring.

## ✨ Current Status
🎉 **Fully Working**: Local GPT-2 + Cloud Mistral-7B via HuggingFace Router API  
📊 **Enhanced Experiments**: Command-line power comparison (local/cloud/both)  
🔧 **Modular Architecture**: 67% code reduction with 7 reusable components

## Features
- **Modular Architecture**: 7 specialized components for maximum reusability
- **Configuration-Driven**: JSON-based configuration system eliminates hardcoded values
- **Working Cloud API**: HuggingFace Router API with Mistral-7B-Instruct model
- **Comprehensive Power Monitoring**: Battery, CPU, memory, and thermal tracking
- **Intelligent Power Management**: Automatic inference routing based on system status
- **Experiment Framework**: Reusable components for power comparison studies

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Configuration
```bash
python setup.py
```
This will create your config files from templates and set up the logs directory.

### 3. Configure API Access
Edit `configs/experiment_config.json` and add your HuggingFace token:
```json
{
  "cloud_api_key": "hf_your_actual_token_here"
}
```

### 4. Run the Main Application
```bash
python main.py
```

### 5. Run Power Comparison Experiment
```bash
python experiments/power_comparison.py
```

## Commands in Main App
- `info` - Show model information and system details
- `status` - Show comprehensive system status
- `quit` or `exit` - Shutdown the application
- Any question - Get AI response with power-aware routing

## Configuration

### Core Configuration Files
- `configs/optimizer_config.json` - Power thresholds and agent settings
- `configs/experiment_config.json` - Experiment settings and API configuration

### Key Settings
```json
// optimizer_config.json - Power management
{
  "battery_threshold": 20,      // Minimum battery % for local inference
  "high_temp_limit": 70,        // Temperature threshold (°C)
  "power_monitoring": true      // Enable comprehensive monitoring
}

// experiment_config.json - Cloud APIs and experiments
{
  "cloud_provider": "huggingface",     // "huggingface" or "openai"
  "use_mock_cloud": false,             // Set true for simulated responses
  "local_model": "gpt2",               // HuggingFace model name
  "experiment_duration": 180           // Test duration in seconds
}
```

## Project Structure
```
EdgeOptimizer/
├── app/
│   └── chatbot.py              # SimpleChatbot using ModelManager
├── optimizer/                  # 🆕 Modular core components
│   ├── __init__.py            # Exports all components
│   ├── agent.py               # EdgeOptimizerAgent (main orchestrator)
│   ├── cloud_inference.py    # Multi-provider cloud API manager
│   ├── config.py              # ConfigManager with validation
│   ├── experiment_runner.py   # Reusable experiment framework
│   ├── model_manager.py       # Local model management with caching
│   └── monitor.py             # SystemMonitor and PowerTracker
├── configs/
│   ├── experiment_config.json # Experiment and API settings
│   └── optimizer_config.json  # Power management configuration
├── experiments/
│   ├── power_comparison.py    # 67% reduced using modular components
│   └── README.md              # Detailed experiment documentation
├── main.py                    # Configuration-driven main application
└── requirements.txt           # Python dependencies
```

## Modular Components

### Core Modules
- **`SystemMonitor`** - Battery, CPU, memory, temperature monitoring
- **`ModelManager`** - Local model loading, caching, and inference with singleton pattern
- **`ConfigManager`** - JSON configuration loading with path resolution and validation
- **`CloudInferenceManager`** - Multi-provider API support (HuggingFace, OpenAI)
- **`ExperimentRunner`** - Reusable experiment orchestration with power integration
- **`EdgeOptimizerAgent`** - Intelligent power-aware inference routing
- **`PowerTracker`** - Specialized power monitoring for experiments

### Usage Example
```python
from optimizer import get_model_manager, get_config_manager, SystemMonitor

# Get shared instances
model_manager = get_model_manager()
config = get_config_manager()
monitor = SystemMonitor()

# Configuration-driven model loading
model_name = config.get_nested('inference_settings.local_model', 'gpt2')
model_manager.load_model(model_name)

# Power-aware inference
if monitor.is_power_sufficient():
    response = model_manager.run_inference(prompt)
else:
    print("Power insufficient for local inference")
```

## Power Comparison Experiments

The enhanced power comparison experiment demonstrates the effectiveness of the modular architecture with flexible testing options:

### Enhanced Features
- **Command-line arguments**: Choose local, cloud, or both
- **Flexible duration**: Custom experiment length
- **API testing**: Verify connections before experiments
- **67% code reduction** using shared modular components

### Running Experiments

**Basic Usage**:
```bash
# Run both local and cloud comparison (default)
python experiments/power_comparison.py

# Run only local inference
python experiments/power_comparison.py local

# Run only cloud inference  
python experiments/power_comparison.py cloud

# Custom duration (60 seconds)
python experiments/power_comparison.py both 60

# Test API connections first
python experiments/power_comparison.py --test-api
```

**Monitoring Experiments**:
```bash
# Monitor recent experiment results
python monitor_experiments.py

# Choose option 2 to see recent results without live monitoring
```

**Current Model Configuration**:
- **Local**: GPT-2 (small, efficient, ~500MB)
- **Cloud**: Mistral-7B-Instruct (large, powerful, via HuggingFace Router)

### Results Analysis
Results saved to `logs/power_comparison_results_YYYYMMDD_HHMMSS.json` with:
- Raw power readings with timestamps
- Battery drain comparison (local vs cloud)
- CPU and memory usage analysis
- Inference performance metrics (response times, success rates)
- Energy consumption estimates

### Recent Test Results
```
CLOUD (Mistral-7B):
  Success rate: 100.0%
  Avg response time: 10.3s
  CPU usage: 18.3% average, 55.7% peak
  
LOCAL (GPT-2):
  Success rate: ~95%+ 
  Avg response time: <1s
  CPU usage: Sustained during inference
```

### Example Analysis
```python
import json

# Load experiment results
with open('logs/power_comparison_results_*.json') as f:
    data = json.load(f)

# Compare power efficiency
local_drain = data['summary']['local']['battery_drain']
cloud_drain = data['summary']['cloud']['battery_drain'] 
efficiency_ratio = cloud_drain / local_drain

print(f"Cloud inference uses {efficiency_ratio:.1f}x more battery than local")
```

- Predictive power management with ML
- Real-time model switching based on query complexity

## API Setup

### HuggingFace Router API (Recommended)
1. **Get Your HuggingFace Token**:
   - Go to [https://huggingface.co](https://huggingface.co) → Settings → Access Tokens
   - Create a new token with "Read" permissions
   - Copy the token (starts with `hf_...`)

2. **Configure in experiment_config.json**:
```json
{
  "cloud_api_url": "https://router.huggingface.co/v1",
  "cloud_api_key": "hf_your_actual_token_here",
  "cloud_provider": "huggingface",
  "inference_settings": {
    "cloud_model": "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
    "use_mock_cloud": false
  }
}
```

### OpenAI API (Alternative)
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```
```json
// In experiment_config.json  
{
  "cloud_provider": "openai",
  "use_mock_cloud": false
}
```

### Mock Mode (Development)
```json
{
  "use_mock_cloud": true  // Simulated responses, no API calls
}
```

## Performance Benefits

The modular architecture provides significant improvements:

| Metric | Before | After | Improvement |
|--------|--------|--------|-------------|
| Power comparison code | 400+ lines | 133 lines | 67% reduction |
| Configuration management | Hardcoded | JSON-driven | 100% configurable |
| Code reusability | Monolithic | 7 modules | High reusability |
| Model management | Manual | Cached + Singleton | Optimized memory |
| API support | Single provider | Multi-provider | Flexible |

## Logging & Configuration

### Logging System
- **Application Logs**: `logs/edgeoptimizer.log` - Main application events and system status
- **Experiment Logs**: `logs/power_comparison_YYYYMMDD_HHMMSS.log` - Detailed experiment tracking with individual test results
- **Result Files**: `logs/power_comparison_results_YYYYMMDD_HHMMSS.json` - Structured experiment data
- **Log Directory**: Automatically created and ignored by git
- **Log Levels**: INFO level for normal operation, includes timestamps and component names

**Monitoring Tools**:
```bash
# View recent experiment summaries
python monitor_experiments.py
# Choose option 2 for quick results view (recommended)

# View detailed logs manually
tail -f logs/power_comparison_YYYYMMDD_HHMMSS.log
```

### Configuration Management
- **Template System**: `configs/experiment_config.template.json` (safe for git)
- **User Config**: `configs/experiment_config.json` (contains API keys, git-ignored)
- **Setup Script**: Run `python setup.py` to initialize configs from templates
- **Environment Variables**: API keys can also be set via environment variables

## Notes
- **Automatic Model Caching**: Models downloaded via HuggingFace are automatically cached
- **Singleton Pattern**: ModelManager and ConfigManager ensure efficient resource usage  
- **Power-Aware Routing**: Automatically switches between local and cloud inference
- **Cross-Platform**: Works on macOS, Linux, and Windows with appropriate monitoring
- **Development Ready**: Mock mode enables testing without API costs
- **Secure Configuration**: API keys are kept out of version control automatically
