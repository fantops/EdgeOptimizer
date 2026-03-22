# EdgeOptimizer

Power-aware local LLM inference using ONNX Runtime, with optional cloud comparison. **Primary development and testing target: macOS** (Apple Silicon and Intel). The same stack also runs on Linux and Windows (including Windows on ARM) where ONNX Runtime and Python dependencies are supported.

## Features

- Local inference via ONNX (default: GPT-2 exported to `models/model.onnx`)
- System-aware scheduling in `optimizer/`
- Power-oriented experiments comparing local vs cloud inference
- Config-driven experiments (copy the template; do not commit secrets)

## Quick start (macOS)

### 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Download and export a small model

```bash
python models/download_model.py
```

This downloads **gpt2** from Hugging Face and writes `models/model.onnx` plus `models/tokenizer/` (both are gitignored).

### 3. Experiment config (no secrets in git)

```bash
cp configs/experiment_config.template.json configs/experiment_config.json
```

Edit `configs/experiment_config.json` and set your cloud credentials, **or** rely on environment variables (see below).

### 4. API keys (recommended)

- **OpenAI:** `export OPENAI_API_KEY='your-key'`  
  If you use OpenAI, set `cloud_api_url` to `https://api.openai.com/v1/chat/completions` and choose a model under `openai_settings` in the template.
- **Hugging Face Inference:** set `cloud_api_key` to an HF token and use the URL in the template, or set `HUGGINGFACE_HUB_TOKEN`.

Never commit `configs/experiment_config.json` (it is listed in `.gitignore`).

### 5. Run the chatbot (local ONNX)

```bash
python main.py
```

### 6. Power comparison experiment

```bash
python experiments/power_comparison.py
```

## Structure

- `app/` — ONNX chatbot (`OnnxChatbot` in `chatbot.py`)
- `optimizer/` — Monitoring and scheduling agent
- `dashboard/templates/` — Reserved for a future UI
- `models/` — Download script; generated `model.onnx` and tokenizer (not in repo)
- `configs/` — `optimizer_config.json` (tracked); `experiment_config.template.json` (tracked); `experiment_config.json` (local only)
- `experiments/` — Power experiments

## Layout

```
EdgeOptimizer/
├── app/
│   └── chatbot.py
├── optimizer/
├── dashboard/
│   └── templates/
├── models/
│   └── download_model.py
├── configs/
├── experiments/
├── tests/
├── main.py
├── requirements.txt
└── README.md
```

## Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
# or
python tests/run_tests.py
```

Smoke checks (imports, psutil, optional config file):

```bash
python test_chatbot.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
