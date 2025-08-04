# EdgeOptimizer 🚀
**Power-Aware AI Inference Comparison Platform**

Compare power consumption between local and cloud AI inference with real-time monitoring and detailed analysis.

## ✨ Key Features

🔋 **Real-Time Power Monitoring**: Hardware-level power consumption analysis with actual wattage estimation  
⚡ **Local vs Cloud Comparison**: Data-driven power efficiency analysis  
📊 **Comprehensive Logging**: Organized experiment tracking and results  
� **Ready to Use**: GPT-2 (local) + Mistral-7B (cloud) integration

## 🚀 Quick Start

### **1. Installation**
```bash
# Clone the repository
git clone https://github.com/fantops/EdgeOptimizer.git
cd EdgeOptimizer

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp configs/experiment_config.json.example configs/experiment_config.json
# Edit configs/experiment_config.json with your HuggingFace API key
```

### **2. Power Comparison Experiments**
```bash
# Quick 30-second local inference test
cd experiments
python3 power_comparison.py local 30

# 10-minute comprehensive comparison
python3 power_comparison.py both 600

# Cloud-only testing
python3 power_comparison.py cloud 120
```

### **3. Understanding Results**
```json
{
  "power_breakdown": {
    "estimated_watts": 57.9,
    "processing_overhead_watts": 49.9,
    "cpu_contribution_percent": 75.2,
    "efficiency_score": 3.0
  },
  "recommendation": "LOCAL inference is more power efficient"
}
```

## 📊 Example Results (10-minute comparison)
| Metric | Local Inference | Cloud Inference | Winner |
|--------|----------------|-----------------|---------|
| **Average Power** | 57.9W | 58.4W | 🏆 Local |
| **Response Time** | 11.3s | 17.7s | 🏆 Local |
| **Processing Overhead** | 49.9W | 50.4W | 🏆 Local |
| **Battery Impact** | -24.7%/hour | -12.8%/hour | 🏆 Local |

## ⚙️ Configuration

### **HuggingFace API Setup**
Edit `configs/experiment_config.json`:
```json
{
  "cloud_api_key": "hf_your_token_here",
  "cloud_model": "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
  "experiment_duration": 300,
  "test_prompts": [
    "What is machine learning?",
    "How does a neural network work?",
    "Explain quantum computing"
  ]
}
```

## 📁 Project Structure

```
EdgeOptimizer/
├── app/
│   └── chatbot.py              # SimpleChatbot using ModelManager
├── optimizer/                  # Core modular components
│   ├── __init__.py            # Exports all components
│   ├── agent.py               # EdgeOptimizerAgent (main orchestrator)
│   ├── cloud_inference.py    # Multi-provider cloud API manager
│   ├── config.py              # ConfigManager with validation
│   ├── experiment_runner.py   # Reusable experiment framework
│   ├── logging_config.py      # Centralized logging system
│   ├── model_manager.py       # Local model management with caching
│   └── monitor.py             # SystemMonitor and PowerTracker
├── experiments/
│   ├── power_comparison.py    # Main power comparison script
│   └── enhanced_power_monitor.py # Advanced power tracking
├── configs/
│   ├── experiment_config.json # Experiment and API settings
│   └── optimizer_config.json  # Power management configuration
├── logs/                      # Organized logging structure
│   ├── power_analysis/       # Power consumption logs
│   ├── experiments/          # Experiment result logs
│   ├── system/              # System operation logs
│   └── archive/             # Archived old logs
├── main.py                    # Configuration-driven main application
└── requirements.txt           # Python dependencies
```

## 🔧 Core Components

### Core Modules
- **`SystemMonitor`** - Battery, CPU, memory, temperature monitoring
- **`ModelManager`** - Local model loading, caching, and inference with singleton pattern
- **`ConfigManager`** - JSON configuration loading with path resolution and validation
- **`CloudInferenceManager`** - Multi-provider API support (HuggingFace, OpenAI)
- **`ExperimentRunner`** - Reusable experiment orchestration with power integration
- **`EdgeOptimizerAgent`** - Intelligent power-aware inference routing
- **`PowerTracker`** - Specialized power monitoring for experiments

## 📊 Log Management

### **Log Analysis Commands**
```python
# Import log utilities
from optimizer.logging_config import EdgeOptimizerLogger, cleanup_logs

# View log summary
logger = EdgeOptimizerLogger()
summary = logger.get_log_summary()
print(summary)

# Clean up old logs (keep 10 most recent)
archived = cleanup_logs(keep_recent=10)
print(f"Archived {archived} old log files")
```
## 📈 Performance Benchmarks

### **Real-World Results** (MacBook Pro, M1 Pro)
| Test Duration | Local Power | Cloud Power | Local Speed | Cloud Speed | Winner |
|---------------|-------------|-------------|-------------|-------------|---------|
| 1 minute | 29.5W | N/A | 9.8s avg | N/A | 🏆 Local |
| 10 minutes | 57.9W | 58.4W | 11.3s avg | 17.7s avg | 🏆 Local |
| 30 minutes | 56.2W | 59.1W | 10.9s avg | 18.2s avg | 🏆 Local |

**Key Insights:**
- Local inference consistently uses 0.5-3W less power
- Local responses are 36-67% faster than cloud
- Processing overhead stable at ~50W during AI inference

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Interested in contributing? See our [Contributing Guide](CONTRIBUTING.md) for development guidelines and power comparison best practices.
