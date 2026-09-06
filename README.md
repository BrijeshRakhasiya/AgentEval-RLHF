# ⚡ AgentEval-RLHF: Open-Source AI Agent Evaluation & RLHF Data Pipeline Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)](https://streamlit.io/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM%20API-76B900.svg)](https://build.nvidia.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`AgentEval-RLHF` is an enterprise-grade, open-source AI Agent Evaluation and Reinforcement Learning from Human Feedback (RLHF) Data Engine. Built to replicate frontier AI data infrastructure (such as Scale AI, Micro1, and frontier RLHF labs), this system executes multi-step LLM reasoning traces, subjects code outputs to dual deterministic and qualitative evaluations, enables Human-in-the-Loop (HITL) expert interventions, and exports fine-tuning artifacts (`DPO` pairs).

---

## 🏗️ System Architecture & End-to-End Pipeline

```
┌───────────────────────────┐      ┌───────────────────────────┐
│ Streamlit HITL Dashboard  │ ───► │ FastAPI Gateway (/main)   │
│  (app.py - Port 8501)     │      │   (main.py - Port 8000)   │
└───────────────────────────┘      └─────────────┬─────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
    ┌──────────────────────────────┐                            ┌──────────────────────────────┐
    │ 1. Subprocess Sandbox        │                            │ 2. Dual LLM-as-a-Judge Router│
    │  (PythonSandbox / CPPSandbox)│                            │  (NVIDIA NIM LLM Router)     │
    └──────────────┬───────────────┘                            └──────────────┬───────────────┘
                   │                                                           │
                   └─────────────────────────────┬─────────────────────────────┘
                                                 │
                                                 ▼
                                   ┌───────────────────────────┐
                                   │ 3. Score Synthesizer      │
                                   │ (Combined Score 1.0 - 5.0)│
                                   └─────────────┬─────────────┘
                                                 │
                                                 ▼
                                   ┌───────────────────────────┐
                                   │ 4. Human Expert Curation  │
                                   │ (Chosen vs Rejected Code) │
                                   └─────────────┬─────────────┘
                                                 │
                                                 ▼
                                   ┌───────────────────────────┐
                                   │ 5. DPO Dataset Exporter   │
                                   │ (data/dpo_dataset.jsonl)  │
                                   └───────────────────────────┘
```

---

## 🌟 Key Features & Technical Highlights

### 1. Dual Evaluation Engine (Deterministic + Qualitative)
- **Deterministic Subprocess Sandboxes**:
  - `PythonSandbox`: Writes code & unit test assertions to temporary files, executes via `subprocess.run` with a strict `5.0s` timeout guard, and captures `stdout`, `stderr`, runtime, and exit status.
  - `CPPSandbox`: Compiles source code and main assertion blocks using `g++ -std=c++17`, executes compiled binaries with a `5.0s` timeout, and captures compilation & runtime exceptions.
- **LLM-as-a-Judge Model Router (NVIDIA NIM)**:
  - Connects to NVIDIA NIM endpoints (`https://integrate.api.nvidia.com/v1`).
  - Features an **Automatic 5-Model Fallback Chain** (`meta/llama-3.2-11b-vision-instruct`, `nvidia/nemotron-3-ultra-550b-a55b`, `moonshotai/kimi-k3`, `deepseek-ai/deepseek-v4-pro-0813`, etc.) ensuring zero downtime if a model is retired or rate-limited.
  - Enforces strict raw JSON response parsing to return qualitative `score` (1-5) and detailed `reasoning`.

### 2. Human-in-the-Loop (HITL) Curation Dashboard
- 2-Column interactive portal built with Streamlit:
  - **Left Column**: Displays automated evaluation results, sandbox `stdout`/`stderr` logs, pass/fail status badge, LLM judge rating, and qualitative reasoning.
  - **Right Column**: Interactive code editor for expert annotators to refine raw completions into optimal **Chosen** responses, adjust rating sliders, and export DPO pairs.

### 3. Native Direct Preference Optimization (DPO) Exporter
- Automatically formats human-curated preference pairs into standardized `.jsonl` entries ready for downstream model fine-tuning (`Axolotl`, `Unsloth`, `TRL`, `HuggingFace`).

---

## 📂 Repository Structure

```
AgentEval-RLHF/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── models.py           # Pydantic data schemas & validators
│   ├── sandbox.py          # PythonSandbox & CPPSandbox execution engines
│   ├── judge.py            # NVIDIA NIM API integration & 5-Model LLM Router
│   ├── main.py             # FastAPI ASGI API gateway
│   └── app.py              # Streamlit HITL curation dashboard
├── docs/
│   ├── ARCHITECTURE.md     # Technical Architecture & System Design
│   ├── CONTEXT.md          # Project Specification
│   └── PLAN.md             # Agentic Development Life Cycle (ADLC) Plan
├── data/
│   └── dpo_dataset.jsonl   # Exported DPO RLHF dataset
├── tests/
│   └── test_pipeline.py    # End-to-end unit test suite
├── main.py                 # FastAPI Root Entrypoint Wrapper
├── app.py                  # Streamlit Root Entrypoint Wrapper
├── .env                    # Environment configuration
├── requirements.txt        # Dependencies
└── LICENSE                 # MIT License
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

Clone the repository and install dependencies using `uv` or `pip`:

```bash
git clone https://github.com/BrijeshRakhasiya/AgentEval-RLHF.git
cd AgentEval-RLHF

# Install dependencies using uv
uv sync
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
NVIDIA_API_KEY="nvapi-your-nvidia-api-key-here"
```

### 3. Launch Services

#### Start FastAPI API Server:
```bash
uv run uvicorn main:app --reload --port 8000
```
*API documentation available at `http://localhost:8000/docs`.*

#### Start Streamlit HITL Curation Dashboard:
```bash
uv run streamlit run app.py
```
*Dashboard available at `http://localhost:8501`.*

---

## 🧪 Verification & Testing

Run the automated test suite to verify sandbox execution and DPO export logic:

```bash
uv run python tests/test_pipeline.py
```

---

## 📊 Direct Preference Optimization (DPO) Schema

Exported entries in `data/dpo_dataset.jsonl` follow this standardized schema:

```json
{
  "task_id": "REASONING-PY-002",
  "prompt": "Write a Python function can_finish(num_courses, prerequisites) using Kahn's algorithm...",
  "chosen": "from collections import deque\n\ndef can_finish(num_courses, prerequisites):\n    indegree = [0] * num_courses\n    adj = [[] for _ in range(num_courses)]\n    for dest, src in prerequisites:\n        adj[src].append(dest)\n        indegree[dest] += 1\n    queue = deque([i for i in range(num_courses) if indegree[i] == 0])\n    visited_count = 0\n    while queue:\n        curr = queue.popleft()\n        visited_count += 1\n        for neighbor in adj[curr]:\n            indegree[neighbor] -= 1\n            if indegree[neighbor] == 0:\n                queue.append(neighbor)\n    return visited_count == num_courses",
  "rejected": "def can_finish(num_courses, prerequisites): return True",
  "human_rating": 5,
  "judge_score": 2,
  "timestamp": "2026-09-06T14:36:41Z"
}
```

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
