# Local Browser Agent Runtime 🤖

A powerful, fully local browser automation agent runtime designed for privacy, visibility, and GPU-accelerated performance.

## 🚀 Features

- **Fully Local Inference**: Powered by Ollama (qwen2.5:7b) with GPU acceleration (RTX 4050 6GB compatible).
- **Zero Cloud Dependency**: Runs completely offline once the model is pulled.
- **Complete Visibility**: Dedicated monitoring dashboard opens instantly in an isolated browser window.
- **Auditable**: Detailed action/thought logs and deterministic execution graphs.
- **Replayable**: Video recordings and session manifests for every run.
- **Robust Recovery**: Exponential backoff and local-optimized retry logic.

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed and running.
- Pull the model: `ollama pull qwen2.5:7b`

### 2. Quick Start (Setup)
Run the automated setup script to create a virtual environment and install all dependencies:
```bash
./setup.sh
```

### 3. Running the Agent
Activate the environment and run a task:
```bash
source venv/bin/activate
python main.py "Open example.com and summarize the page content."
```

### 4. Performance Benchmarking
Test your local inference speed and VRAM efficiency:
```bash
python benchmark_local.py
```

## 📂 Project Structure
- `main.py`: Primary CLI entry point for local runtime.
- `benchmark_local.py`: Performance measurement tool.
- `src/core/ollama.py`: Local model provider and health checks.
- `src/agents/`: Core agent logic optimized for local models.
- `logs/`: Audit trails and performance metrics.
- `recordings/`: Video recordings of browser sessions.

---
*Built for privacy-conscious users who need transparent, observable AI execution.*
