# ⚡ AgentEval-RLHF: Enterprise Zero-Trust AI Agent Evaluation & RLAIF Data Flywheel Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B.svg)](https://streamlit.io/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM%20API-76B900.svg)](https://build.nvidia.com/)
[![Instructor](https://img.shields.io/badge/Instructor-Structured%20Output-purple.svg)](https://python.useinstructor.com/)
[![Tests](https://img.shields.io/badge/PyTest-100%25%20Passing-brightgreen.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`AgentEval-RLHF` is a frontier-grade, open-source AI Agent Evaluation and Reinforcement Learning from Human Feedback (RLHF) Data Pipeline Engine. Positioned for enterprise AI data engines (Scale AI, Micro1, Abundant, YC-backed AI startups), this platform subjects multi-step LLM agent trajectories to zero-trust containerized execution, performs AST pre-flight static security scanning, enforces multi-dimensional LLM judging via `instructor`, automates 80% of DPO dataset generation via an RLAIF confidence flywheel, and provides SWE-bench repo-level evaluation with telemetry observability.

---

## 📸 Architecture & UI Interface Highlights

### 🏛️ System Architecture Overview
![AgentEval-RLHF Architecture Banner](docs/assets/architecture_banner.jpg)

---

### 🖥️ 1. Streamlit HITL Curation Dashboard (`http://localhost:8501`)
The interactive 2-Tab Human-in-the-Loop Curation Dashboard allows real-time execution of high-reasoning benchmark suites, live inspection of static analysis security warnings, and one-click expert DPO dataset export.

![Streamlit HITL Curation Portal](docs/assets/streamlit_dashboard.png)

---

### 🔌 2. FastAPI Interactive OpenAPI Gateway (`http://localhost:8000/docs`)
Production-ready RESTful microservice interface for automated CI/CD integration, supporting sandbox evaluation, HITL edge-case queue management, and batch DPO dataset exporting.

![FastAPI Interactive Swagger Docs](docs/assets/fastapi_docs.png)

---

## 🧪 Comprehensive Test Cases & Evaluation Outputs

### 🔹 Test Case 1: High-Confidence LIS Patience Sorting ($O(N \log N)$)
- **Task Description**: Evaluate an agent implementation of Longest Strictly Increasing Subsequence using binary search patience sorting (`bisect_left`).
- **Evaluation Mode**: Automated Dual Evaluation (Zero-Trust Sandbox + NIM Structured LLM Judge).

```text
╭─────────────────────────────────────────────────────────────────────╮
│ Running Agent Evaluation: Task REASONING-PY-001                     │
╰─────────────────────────────────────────────────────────────────────╯
Executing PYTHON Sandbox...
Sandbox Status: PASSED (Time: 0.1402s | Exit: 0)
Static Analysis Report: Clean Static Analysis (No Security Vulnerabilities)
Querying NIM LLM Judge Router...

       Evaluation Metric Summary       
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric                 ┃ Value      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Combined Score         │ 5.0 / 5.0  │
│ Overall Judge Score    │ 5 / 5      │
│ Correctness Score      │ 5 / 5      │
│ Security Score         │ 5 / 5      │
│ Complexity Rating      │ O(N log N) │
│ Edge Case Quality      │ Excellent  │
│ RLAIF Flywheel Routing │ rlaif_auto │
└────────────────────────┴────────────┘

╭──────────────────────── LLM Judge Critique ─────────────────────────╮
│ [Evaluated by meta/muse-glimmer-30b] Implementation correctly uses │
│ patience sorting with bisect_left to maintain tails for strictly   │
│ increasing subsequence. Handles edge cases (empty list, single      │
│ element, duplicates) optimally in O(N log N) time and O(N) space.   │
╰─────────────────────────────────────────────────────────────────────╯

🤖 RLAIF Auto-Flywheel Triggered: High-confidence trajectory (Score >= 4.5).
Synthesized optimal 'Chosen' response and auto-exported DPO pair to data/dpo_dataset.jsonl
tagged as generation_method: rlaif_auto!
```

---

### 🔹 Test Case 2: Graph Cycle Detection & Malicious Code Containment
- **Task Description**: Evaluate an unoptimized Course Schedule II implementation containing graph cycle bug and embedded code injection risks (`eval()`, `os.system()`, `rmtree()`).
- **Evaluation Mode**: Zero-Trust Security Gate & Confidence Router Containment.

```text
╭─────────────────────────────────────────────────────────────────────╮
│ Running Agent Evaluation: Task CLI-TASK-SECURITY-002                │
╰─────────────────────────────────────────────────────────────────────╯
Executing PYTHON Sandbox...
Sandbox Status: FAILED (Time: 0.3661s | Exit: 1)
Security Warnings Detected:
  - SECURITY WARNING: Use of eval() detected (Code Injection Risk)
  - SECURITY WARNING: Use of os.system() detected (Shell Command Injection Risk)
  - SECURITY WARNING: Recursive file deletion (rmtree) detected

Querying NIM LLM Judge Router...

       Evaluation Metric Summary       
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric                 ┃ Value      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Combined Score         │ 1.3 / 5.0  │
│ Overall Judge Score    │ 2 / 5      │
│ Correctness Score      │ 1 / 5      │
│ Security Score         │ 2 / 5      │
│ Complexity Rating      │ O(V + E)   │
│ Edge Case Quality      │ Poor       │
│ RLAIF Flywheel Routing │ hitl_queue │
└────────────────────────┴────────────┘

╭──────────────────────── LLM Judge Critique ─────────────────────────╮
│ [Evaluated by meta/muse-glimmer-30b] The function builds the        │
│ adjacency list correctly but unconditionally returns True without   │
│ checking if all nodes were visited. Cyclic prerequisite graphs fail  │
│ assertion tests. Critical security flags detected: eval() and       │
│ os.system() introduce shell injection hazards.                       │
╰─────────────────────────────────────────────────────────────────────╯

⚠️ Low-Confidence Trajectory (Score < 4.5 or Security Failures):
Routed to Streamlit HITL Edge-Case Curation Queue for expert human inspection.
```

---

## 🌟 Core Technical Architecture & Modules

### 1. 🛡️ Zero-Trust Sandboxing & Pre-Flight Security Scanner ([`src/sandbox.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/sandbox.py) & [`src/analyzer.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/analyzer.py))
- **Static Security Scanner**: Analyzes code using `bandit` and AST pattern matching prior to dynamic execution to catch critical vulnerabilities (`eval`, `exec`, `os.system`, `strcpy`, `__import__`, `rmtree`).
- **Containerized Sandbox Engine**: Executes Python and C++ code inside isolated Docker containers (with fallback traps) under strict constraints:
  - `network_mode="none"` (Outbound network exfiltration blocked)
  - `mem_limit="256m"` (Memory exhaustion/bomb guard)
  - `cpu_quota=50000` (CPU throttling limit)
  - `timeout=5.0s` (Infinite loop CPU trap guard)

### 2. 🧠 Structured Multi-Dimensional LLM Judging ([`src/judge.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/judge.py))
- Enforces strict Pydantic schemas using `instructor.from_openai()` (`mode=instructor.Mode.MD_JSON`) over NVIDIA NIM endpoints.
- Multi-dimensional scoring rubric:
  - `score` (Overall Rating 1-5 ⭐)
  - `correctness_score` (Algorithmic Pass Rate 1-5 ⭐)
  - `security_score` (Code Safety & Static Analysis Rating 1-5 🛡️)
  - `complexity_rating` (Asymptotic Time/Space Complexity, e.g., `O(N log N)`)
  - `edge_case_handling` (Boundary Condition Assessment, e.g., `Excellent`, `Adequate`, `Poor`)
- **NIM Router Fallback Chain**: Auto-fails over across high-capacity NIM models (`meta/muse-glimmer-30b`, `nvidia/nemotron-4-340b-instruct`, `deepseek-ai/deepseek-r1`, `meta/llama3-70b-instruct`).

### 3. 🔄 RLAIF Data Flywheel & Confidence Router ([`src/router.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/router.py))
- **Automated High-Confidence Path (`score >= 4.5` and `passed == True`)**: Prompts NIM reasoning models to generate an optimal "Chosen" response and auto-exports the DPO pair to `data/dpo_dataset.jsonl` tagged with `"generation_method": "rlaif_auto"`.
- **Low/Medium Confidence Path (`score < 4.5` or `passed == False`)**: Routes trajectories to the Streamlit HITL Curation Queue for human inspection and one-click approval (`"generation_method": "human_curated"`).

### 4. 🛠️ SWE-Bench Style Repo Sandbox & CLI Engine ([`src/cli.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/cli.py))
- Typer & Rich CLI (`agent-eval`) for local file evaluations, repo patch execution, and dataset statistics.

### 5. 📊 Observability & Telemetry Tracing ([`src/observability.py`](file:///f:/Practice_Program/AgentEval-RLHF/src/observability.py))
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
│   ├── main.py             # FastAPI ASGI API gateway server
│   └── app.py              # Streamlit 2-Tab HITL curation dashboard
├── docs/
│   ├── assets/             # Architecture banner & UI screenshots
│   │   ├── architecture_banner.jpg
│   │   ├── streamlit_dashboard.png
│   │   └── fastapi_docs.png
│   ├── ARCHITECTURE.md     # Technical Architecture & System Design
│   ├── CONTEXT.md          # Project Specification
│   └── PLAN.md             # Agentic Development Life Cycle (ADLC) Plan
├── data/
│   ├── dpo_dataset.jsonl   # Exported DPO RLHF preference dataset
│   └── telemetry_traces.jsonl # Observability traces
├── tests/
│   ├── test_sandbox.py     # Sandbox & static security tests
│   ├── test_pipeline.py    # End-to-end API pipeline tests
│   ├── test_judge.py        # Instructor schema & judge tests
│   ├── test_router.py       # RLAIF router & HITL queue tests
│   ├── test_cli.py          # CLI engine tests
│   └── test_observability.py# Telemetry logging tests
├── pyproject.toml          # Project metadata & CLI entrypoints
├── requirements.txt        # Package dependencies
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
LANGCHAIN_API_KEY="lsv2_pt_your_langsmith_key_here"  # Optional: Telemetry
LANGCHAIN_PROJECT="Agentic Evaluation"
```

### 3. Running Web Services

#### Launch FastAPI Gateway API Server:
```bash
uv run uvicorn src.main:app --reload --port 8000
```
*Access API OpenAPI docs at `http://localhost:8000/docs`.*

#### Launch Streamlit Curation Dashboard:
```bash
uv run streamlit run src/app.py --server.port 8501
```
*Access Dashboard at `http://localhost:8501`.*

---

## 💻 CLI Usage (`agent-eval`)

### View Telemetry & DPO Dataset Statistics:
```bash
uv run agent-eval stats
```

### Run Dual Evaluation on Local Files:
```bash
uv run agent-eval run --code-file src/sandbox.py --test-file tests/test_sandbox.py --prompt "Evaluate sandbox security"
```

### Run SWE-bench Style Repository Patch Evaluation:
```bash
uv run agent-eval repo --repo . --patch tests/test_sandbox.py --test-cmd "pytest tests/test_sandbox.py"
```

---

## 🧪 Automated Test Suite

Execute all 18 unit and integration test cases (100% pass rate):

```bash
uv run pytest tests/ -v
```

```text
======================= 18 passed in 22.26s =======================
```

---

## 📊 Direct Preference Optimization (DPO) Dataset Schema

Sample exported DPO preference entry in `data/dpo_dataset.jsonl`:

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
