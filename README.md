# ⚡ AgentEval-RLHF: Open-Source AI Agent Evaluation & RLHF Data Pipeline Engine (v2.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)](https://streamlit.io/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM%20API-76B900.svg)](https://build.nvidia.com/)
[![Instructor](https://img.shields.io/badge/Instructor-Structured%20Output-purple.svg)](https://python.useinstructor.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`AgentEval-RLHF` is an enterprise-grade, open-source AI Agent Evaluation and Reinforcement Learning from Human Feedback (RLHF) Data Pipeline Engine (v2.0). Built to replicate frontier AI data infrastructure (Scale AI, Micro1, Abundant), this system executes multi-step LLM reasoning traces, subjects outputs to zero-trust sandboxed dynamic execution and pre-flight static security analysis, runs structured multi-dimensional judging via `instructor`, automates 80% of DPO dataset generation via an RLAIF confidence flywheel, and provides a CLI engine and LangSmith observability telemetry.

---

## 🏗️ System Architecture & v2.0 Data Flywheel Pipeline

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│ Streamlit HITL Dashboard  │ ───► │ FastAPI Gateway (/main)   │ ◄─── │ CLI Engine (agent-eval)   │
│  (app.py - Port 8501)     │      │   (main.py - Port 8000)   │      │ (src/cli.py)              │
└───────────────────────────┘      └─────────────┬─────────────┘      └───────────────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
    ┌──────────────────────────────┐                            ┌──────────────────────────────┐
    │ 1. Zero-Trust Sandbox        │                            │ 2. Structured LLM Judge      │
    │  (Docker / AST Static Scan)  │                            │  (Instructor + NIM Router)   │
    └──────────────┬───────────────┘                            └──────────────┬───────────────┘
                   │                                                           │
                   └─────────────────────────────┬─────────────────────────────┘
                                                 │
                                                 ▼
                                   ┌───────────────────────────┐
                                   │ 3. Multi-Dimensional Score│
                                   │ (Correctness/Security/Log)│
                                   └─────────────┬─────────────┘
                                                 │
                                                 ▼
                                   ┌───────────────────────────┐
                                   │ 4. RLAIF Confidence Router│
                                   │ (High vs Low/Medium Conf) │
                                   └───────┬───────────┬───────┘
                                           │           │
                 ┌─────────────────────────┘           └─────────────────────────┐
                 ▼                                                               ▼
  ┌──────────────────────────────┐                              ┌──────────────────────────────┐
  │ 5a. RLAIF Auto-Flywheel      │                              │ 5b. Streamlit HITL Queue     │
  │ (DeepSeek/Llama Auto-Export) │                              │ (Human Curator Review)       │
  └──────────────┬───────────────┘                              └──────────────┬───────────────┘
                 │                                                             │
                 └─────────────────────────────┬───────────────────────────────┘
                                               │
                                               ▼
                                 ┌───────────────────────────┐
                                 │ 6. DPO Dataset & Telemetry│
                                 │ (dpo_dataset.jsonl)       │
                                 └───────────────────────────┘
```

---

## 🌟 Core Modules & Technical Capabilities

### 1. 🛡️ Zero-Trust Sandboxing & Pre-Flight Static Security Analysis ([`src/sandbox.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/sandbox.py) & [`src/analyzer.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/analyzer.py))
- **Static Security Scanner**: Analyzes code using `bandit` and AST pattern matching before dynamic execution to flag injection risks (`eval`, `exec`, `os.system`, `strcpy`, `__import__`).
- **Containerized Sandbox Engine**: Executes Python and C++ code inside isolated Docker containers (or subprocess fallback traps) with strict resource limits:
  - `network_mode="none"` (Outbound network exfiltration blocked)
  - `mem_limit="256m"` (RAM memory bomb containment)
  - `timeout=5.0s` (Infinite loop CPU exhaustion guard)

### 2. 🧠 Structured Multi-Dimensional LLM Judging ([`src/judge.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/judge.py))
- Enforces strict Pydantic schema responses using `instructor.from_openai()` over NVIDIA NIM endpoints.
- Evaluates code across 5 distinct dimensions:
  - `score` (Overall Rating 1-5 ⭐)
  - `correctness_score` (Algorithmic Pass Rate 1-5 ⭐)
  - `security_score` (Code Safety & Static Analysis Rating 1-5 🛡️)
  - `complexity_rating` (Asymptotic Time/Space Complexity, e.g. `O(N log N)`)
  - `edge_case_handling` (Boundary Condition Assessment, e.g. `Excellent`, `Adequate`, `Poor`)
- **5-Model Fallback Router Chain**: Automatically fails over across high-capacity NIM models (`meta/llama-3.2-11b-vision-instruct`, `meta/muse-glimmer-30b`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`, `nvidia/nemotron-3-ultra-550b-a55b`, `deepseek-ai/deepseek-v4-pro-0813`).

### 3. 🔄 RLAIF Data Flywheel & Confidence Router ([`src/router.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/router.py))
- **Automated High-Confidence Path (`score >= 4.5` and `passed == True`)**: Prompts NIM reasoning models to generate an optimal "Chosen" response and auto-exports the DPO pair to `data/dpo_dataset.jsonl` tagged with `"generation_method": "rlaif_auto"`.
- **Low/Medium Confidence Path (`score < 4.5` or `passed == False`)**: Routes trajectories to the Streamlit HITL Curation Queue for human inspection and one-click approval (`"generation_method": "human_curated"`).

### 4. 💻 Enterprise CLI Engine ([`src/cli.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/cli.py))
- Typer & Rich command line interface supporting local file evaluation, SWE-bench style repo-level patch execution, and dataset statistics.

### 5. 📊 Telemetry & LangSmith Observability ([`src/observability.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/observability.py))
- Streams complete evaluation traces to LangSmith (`LANGCHAIN_PROJECT="Agentic Evaluation"`) or fallback structured JSON logs (`data/telemetry_traces.jsonl`).

---

## 📂 Repository Structure

```
AgentEval-RLHF/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── models.py           # Pydantic data schemas & multi-dimensional validators
│   ├── analyzer.py         # Static security analyzer (Bandit + AST regex guards)
│   ├── sandbox.py          # SecurePythonSandbox, SecureCPPSandbox & RepoSandbox
│   ├── judge.py            # Instructor-enforced structured LLM judge & NIM router
│   ├── router.py           # RLAIF ConfidenceRouter & HITL Queue manager
│   ├── observability.py    # LangSmith telemetry & trace logger
│   ├── cli.py              # Typer & Rich CLI engine (`agent-eval`)
│   ├── main.py             # FastAPI ASGI API gateway
│   └── app.py              # Streamlit 2-Tab HITL curation dashboard
├── docs/
│   ├── ARCHITECTURE.md     # Technical Architecture & System Design
│   ├── CONTEXT.md          # Project Specification
│   └── PLAN.md             # Agentic Development Life Cycle (ADLC) Plan
├── data/
│   ├── dpo_dataset.jsonl   # Exported DPO RLHF dataset
│   └── telemetry_traces.jsonl # Observability traces
├── tests/
│   ├── test_sandbox.py     # Sandbox & static security tests
│   ├── test_pipeline.py    # End-to-end API pipeline tests
│   ├── test_judge.py        # Instructor schema & judge tests
│   ├── test_router.py       # RLAIF router & HITL queue tests
│   ├── test_cli.py          # CLI engine tests
│   └── test_observability.py# Telemetry logging tests
├── pyproject.toml          # Project configuration & script entrypoints
├── requirements.txt        # Dependencies
└── LICENSE                 # MIT License
```

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
git clone https://github.com/BrijeshRakhasiya/AgentEval-RLHF.git
cd AgentEval-RLHF

# Install dependencies using uv
uv sync
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
NVIDIA_API_KEY="nvapi-your-nvidia-api-key-here"
LANGCHAIN_API_KEY="lsv2_pt_your_langsmith_key_here"  # Optional: LangSmith telemetry
LANGCHAIN_PROJECT="Agentic Evaluation"
```

### 3. Running Services

#### Launch FastAPI API Server:
```bash
uv run uvicorn src.main:app --reload --port 8000
```

#### Launch Streamlit 2-Tab Curation Portal:
```bash
uv run streamlit run app.py
```
*Access Dashboard at `http://localhost:8501`.*

---

## 💻 CLI Usage (`agent-eval`)

### View Dataset & Telemetry Statistics:
```bash
uv run agent-eval stats
```

### Run Evaluation on Local Files:
```bash
uv run agent-eval run --code-file solution.py --test-file tests.py --prompt "Implement LRU Cache"
```

### Run SWE-bench Style Repo Patch Evaluation:
```bash
uv run agent-eval repo --repo ./my_repo --patch patch.py --test-cmd "pytest"
```

---

## 🧪 Automated Test Suite

Run the full pytest suite (100% pass rate):

```bash
uv run pytest -v
```

---

## 📊 Direct Preference Optimization (DPO) Schema

Exported entries in `data/dpo_dataset.jsonl`:

```json
{
  "task_id": "RLAIF-AUTO-001",
  "prompt": "Write a Python function length_of_lis(nums) in O(N log N)...",
  "chosen": "from typing import List\nimport bisect\n...",
  "rejected": "def length_of_lis(nums): ...",
  "human_rating": 5,
  "judge_score": 5,
  "correctness_score": 5,
  "security_score": 5,
  "complexity_rating": "O(N log N) time, O(N) space",
  "generation_method": "rlaif_auto",
  "timestamp": "2026-09-06T15:01:49.921888+00:00"
}
```

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

