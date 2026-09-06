# AgentEval-RLHF: Technical Architecture & System Design

## 1. High-Level Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          User / Input System            │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │     FastAPI Core API Gateway Server     │
                    └────────────────────┬────────────────────┘
                                         │
            ┌────────────────────────────┴────────────────────────────┐
            ▼                                                         ▼
┌─────────────────────────┐                               ┌─────────────────────────┐
│ Deterministic Sandbox   │                               │ LLM Qualitative Judge   │
│ Engine (Python / C++)   │                               │ Engine (Groq / Llama 3) │
└───────────┬─────────────┘                               └───────────┬─────────────┘
            │                                                         │
            └────────────────────────────┬────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ Consolidated Trace & Evaluation Result  │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │   Streamlit Human-in-the-Loop Portal    │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │  Data Exporter Engine (SFT & DPO JSONL) │
                    └─────────────────────────────────────────┘
```

## 2. Component Specifications

### 2.1 Backend Core (FastAPI)
- **Framework:** FastAPI (`uvicorn` ASGI server)
- **Endpoints:**
  - `POST /evaluate/python`: Accepts code prompt and pytest test-cases. Runs execution + judge scoring.
  - `POST /evaluate/cpp`: Accepts C++ prompt and gtest assertions. Compiles and executes.
  - `POST /export/dpo`: Ingests human-verified feedback and appends formatted DPO pairs to local JSONL storage.

### 2.2 Execution Sandbox Subsystem
- **Security Control:** Isolated temporary files (`tempfile` module), process timeouts (`5.0s`), restricted system calls.
- **Supported Environments:** Python 3.10+, G++ C++17 Compiler.

### 2.3 LLM-as-a-Judge Architecture
- **Inference Engine:** `langchain-groq` utilizing `llama-3.3-70b-versatile` (or local Ollama instance).
- **Output Standard:** Strict JSON schema validation with retry fallback mechanism.

### 2.4 Data Format Standardizations

#### Direct Preference Optimization (DPO) Schema
```json
{
  "task_id": "TASK-2026-001",
  "prompt": "Write a C++ function to check if a binary tree is balanced.",
  "chosen": "...",
  "rejected": "...",
  "human_rating": 5,
  "judge_score": 4,
  "timestamp": "2026-09-06T11:10:00Z"
}
```