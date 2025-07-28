# EdgeOptimizer
A power-aware local LLM chatbot running on Windows ARM using ONNX Runtime and the Phi model.

## Features
- Local inference using Phi ONNX model
- System-aware scheduling agent
- Power optimization based on battery/thermal status

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
│   └── phi.onnx (placeholder)
├── configs/
│   └── optimizer_config.json
├── README.md
├── requirements.txt
└── main.py
```
