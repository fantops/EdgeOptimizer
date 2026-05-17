# EdgeOptimizer

**Workload-agnostic NPU inference profiler.** Point it at any ONNX model
and it captures four signals around the forward pass:

1. **EP assignment** — which ONNX Runtime Execution Provider actually ran
   each op (`npu_op_pct` overall + per layer-class).
2. **Energy per inference** — RAPL on Intel, `powermetrics` on macOS,
   CrossMon-derived fallback elsewhere.
3. **System utilisation** — CPU / Memory / GPU / NPU via the
   [CrossMon](tools/crossmon) sampler submodule.
4. **Version matrix** — EP × ORT × SDK × model build, pinned + auto-diffed
   against a baseline.

Regression gates fire on signals 1–3; a triage-report CLI consumes the JSON
and emits a Markdown report fit for an agentic-CLI workflow.

This is the personal / OSS port of the workflow used in multi-vendor NPU
validation across Intel Lunar Lake, AMD XDNA, and Qualcomm Hexagon HTP.
Same flow; data sources are what's reachable without vendor NDAs.

> **Scope-honest:** profile path runs on any ONNX model with synthetic
> inputs — no tokenizer, no torch, no transformers needed. The chatbot
> (`app/chatbot.py`) and battery-aware scheduler (`optimizer/agent.py`) are
> kept as **one sample workload**; everything else has been cut to keep the
> repo aligned with what's actually claimed.

---

## Layout

```
EdgeOptimizer/
├── app/
│   ├── runner.py          # Generic ONNX workload runner (synthetic inputs)
│   └── chatbot.py         # Sample workload — optional torch/transformers
├── optimizer/             # Power-aware scheduler used by chat mode
│   ├── agent.py
│   └── monitor.py
├── profiler/              # CV-story core
│   ├── ep_tracker.py      #   ORT profiling JSON → npu_op_pct per layer-class
│   ├── energy.py          #   RAPL / powermetrics / battery J/inference
│   ├── system_sampler.py  #   wraps tools/crossmon for CPU/Mem/GPU/NPU
│   ├── gates.py           #   regression gates
│   ├── version_matrix.py  #   EP × ORT × SDK × model pinning + diff
│   ├── profile_cli.py     #   `python -m profiler.profile_cli`
│   └── triage_report.py   #   Markdown triage report
├── tools/
│   └── crossmon/          # git submodule — C++17 cross-platform sampler
├── configs/
│   ├── optimizer_config.json
│   └── gates_config.json
├── models/
│   └── download_model.py  # optional — exports gpt2 for the chat workload
├── main.py                # `python main.py profile|chat`
├── requirements.txt
└── README.md
```

### Data flow

```
                              ┌──────────────────────────┐
                              │  profiler.profile_cli    │
                              │   (any .onnx model)      │
                              └──────────────┬───────────┘
              ┌──────────────────────────────┼──────────────────────────────┐
              ▼                              ▼                              ▼
   ┌────────────────────┐         ┌────────────────────┐         ┌───────────────────┐
   │ EnergyAttributor   │         │ app.runner          │         │ SystemSampler     │
   │ RAPL / powermetrics│         │ ORT + profile JSON  │         │ ──► CrossMon bin  │
   └─────────┬──────────┘         └────────┬───────────┘         └────────┬──────────┘
             │                             │                              │
             │                             ▼                              │
             │              ┌──────────────────────────┐                  │
             │              │ EPAssignmentTracker      │                  │
             │              │ per-op + per-layer-class │                  │
             │              └────────────┬─────────────┘                  │
             │                           │                                │
             └──────────────┬────────────┴────────────┬───────────────────┘
                            ▼                         ▼
                     ┌────────────────┐      ┌──────────────────┐
                     │ VersionMatrix  │      │ RegressionGate   │
                     └────────┬───────┘      └────────┬─────────┘
                              └──────────┬────────────┘
                                         ▼
                              ┌─────────────────────────┐
                              │ logs/run_<ts>.json      │
                              │   triage_report.py ─►   │
                              │   Markdown report       │
                              └─────────────────────────┘
```

---

## Quick start (macOS)

### 1. Clone with submodules

```bash
git clone --recurse-submodules https://github.com/fantops/EdgeOptimizer.git
cd EdgeOptimizer
# Or if already cloned:
git submodule update --init --recursive
```

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Build the CrossMon sampler (recommended)

```bash
cd tools/crossmon
./scripts/build_and_test_macos.sh release
cd -
```

If you skip this, `SystemSampler` falls back to `psutil` (no GPU / NPU data).

### 4. Profile any ONNX model

```bash
python main.py profile --model path/to/your_model.onnx \
    --iterations 20 --out logs/run.json
```

No tokenizer, no model-specific glue — the runner reads
`session.get_inputs()`, substitutes `1` for symbolic dims (or `--seq-len`
for sequence dims), and feeds synthetic numpy arrays.

### 5. Compare against a baseline

```bash
python -m profiler.triage_report \
    --run logs/run.json --baseline logs/baseline.json -o report.md
```

The Markdown report lists failed gates, worst-fallback op classes, and the
version-matrix diff rows (EP / ORT / SDK / model build cells that moved).

---

## Modes

### `python main.py profile ...`
The CV-story flow. Works on any ONNX model.

### `python main.py chat`
Sample workload: ONNX chatbot loop guarded by the battery-aware scheduler
in `optimizer/agent.py`. Requires the optional `torch` + `transformers`
extras (commented in `requirements.txt`) and an exported model at
`models/model.onnx` (use `python models/download_model.py`).

---

## CrossMon submodule

[`tools/crossmon`](tools/crossmon) is the cross-platform CPU / Memory /
GPU / NPU-stub sampler that feeds `profiler.system_sampler`. Standalone
repo with its own build scripts:

* Windows: `scripts\build_and_test_windows.bat release`
* macOS:   `./scripts/build_and_test_macos.sh release`

`SystemSampler` auto-discovers the binary at
`tools/crossmon/build/crossmon` (or `Debug/crossmon`), or any `crossmon`
on `PATH`.

---

## Configuration

| File | Purpose |
|---|---|
| `configs/gates_config.json` | Thresholds for the regression gates |
| `configs/optimizer_config.json` | Battery threshold for the chat-mode scheduler |

---

## Honest framing (the gap vs the corporate tool)

* No ETW provider here — public ORT profiling JSON only. The corporate
  version hooks `SessionState` events via ETW for higher-resolution per-op
  data.
* No Quarch / Monsoon ground-truth power. RAPL + `powermetrics` are good
  enough to demonstrate the flow.
* No Windows DXCore / vendor SDK version probes. `version_matrix.py`
  captures what's reachable from Python.
* NPU column in CrossMon on macOS is a stub — Apple doesn't expose ANE
  counters to user space.

Interfaces match the corporate tool, so a hardware-meter or ETW backend
can plug into `EnergyAttributor` / `EPAssignmentTracker` without touching
callers. Scaling up happens once I'm working somewhere that has those
backends to plug in.

---

## License

MIT — see [LICENSE](LICENSE).
