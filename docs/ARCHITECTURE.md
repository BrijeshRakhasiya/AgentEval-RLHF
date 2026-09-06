# AgentEval-RLHF: Technical Architecture & System Design (v2.0)

## 1. High-Level Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │      CLI / FastAPI Core API Gateway     │
                    └────────────────────┬────────────────────┘
                                         │
            ┌────────────────────────────┴────────────────────────────┐
            ▼                                                         ▼
┌─────────────────────────┐                               ┌─────────────────────────┐
│ Zero-Trust Sandbox &    │                               │ Structured LLM Judge    │
│ Static Analyzer         │                               │ (Instructor / Pydantic) │
│ (E2B / Docker + Bandit) │                               │ (Multi-Dimensional)     │
└───────────┬─────────────┘                               └───────────┬─────────────┘
            │                                                         │
            └────────────────────────────┬────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │      RLAIF Confidence Router            │
                    │ (Auto-Approve High Confidence / Route)  │
                    └────────────────────┬────────────────────┘
                                         │
            ┌────────────────────────────┴────────────────────────────┐
            ▼                                                         ▼
┌─────────────────────────┐                               ┌─────────────────────────┐
│ Auto-Generated DPO Pair │                               │ Smart HITL Dashboard    │
│ (Strong Model Rewrite)  │                               │ (Streamlit Edge-Cases)  │
└───────────┬─────────────┘                               └───────────┬─────────────┘
            │                                                         │
            └────────────────────────────┬────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │  Observability & Data Exporter Engine   │
                    │  (LangSmith / Phoenix + JSONL Export)   │
                    └─────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Backend Core (FastAPI & CLI)
- **Framework:** FastAPI (`uvicorn` ASGI server) for webhooks/dashboard, Typer/Click for local CLI execution.
- **Key Endpoints & Commands:**
  - `POST /evaluate/agent`: Accepts agent trajectory, tool logs, and generated code. Routes to sandbox and judge.
  - `POST /evaluate/repo`: Accepts `git_repo_url`, `issue_description`, and patch. Clones repo and runs native test suites (SWE-bench style).
  - `CLI agent-eval run`: Terminal command for rapid local evaluation and DPO export without the web UI.

### 2.2 Zero-Trust Execution & Static Analysis (Phase 1)
- **Static Analyzer (`src/analyzer.py`):** Runs pre-flight security and linting checks using `bandit` (Python) and `cppcheck` (C++) to flag vulnerabilities (e.g., `eval()`, shell injection) before execution.
- **Secure Sandbox (`src/sandbox.py`):** Replaces legacy subprocess with ephemeral, isolated microVMs (via `e2b-code-interpreter`) or strictly constrained Docker containers (gVisor).
- **Security Controls:** 100% host isolation, strict memory/CPU limits, network egress blocking, and guaranteed environment teardown.

### 2.3 Structured LLM-as-a-Judge (Phase 2)
- **Inference Engine:** NVIDIA NIM API / OpenAI-compatible endpoints utilizing `instructor` for guaranteed schema enforcement.
- **Multi-Dimensional Evaluation:** Replaces single 1-5 score with granular metrics:
  - `correctness_score` (Pass/Fail logic)
  - `security_score` (Based on static analysis)
  - `complexity_rating` (Time/Space efficiency)
  - `edge_case_handling` (Robustness)
- **Output Standard:** Native Pydantic structured outputs. Zero regex fallbacks; malformed LLM outputs are automatically retried by the `instructor` library.

### 2.4 RLAIF Data Flywheel & Smart HITL (Phase 3)
- **Confidence Router (`src/router.py`):** The brain of the data flywheel.
  - **High Confidence (Score ≥ 4.5 & Tests Pass):** Automatically triggers a stronger model (e.g., `deepseek-v4-pro`) to rewrite and optimize the code into the "Chosen" DPO pair.
  - **Low/Medium Confidence (Score < 4.5 or Tests Fail):** Routed to the Human-in-the-Loop queue.
- **Smart HITL Dashboard (`src/app.py`):** Streamlit interface optimized for expert review. Features side-by-side code diffs, execution trace inspectors, and one-click approval for RLAIF edge-cases.

### 2.5 Observability & Export Engine (Phase 4)
- **Telemetry (`src/observability.py`):** Logs all `TaskRequest` → `ExecutionTrace` → `JudgeResult` flows to LangSmith or Arize Phoenix for drift detection, latency monitoring, and performance auditing.
- **Data Exporter:** Native, append-only formatting into Hugging Face / OpenAI compatible `.jsonl` files for Supervised Fine-Tuning (SFT) and Direct Preference Optimization (DPO).

---

## 3. Data Format Standardizations

### 3.1 Execution Trace Schema (Enhanced)
```json
{
  "task_id": "TASK-2026-001",
  "sandbox_type": "e2b_microvm",
  "passed": true,
  "stdout": "All 5 tests passed.",
  "stderr": "",
  "execution_time": 1.24,
  "security_flags": [],
  "static_analysis_report": "No vulnerabilities detected."
}
```

### 3.2 Direct Preference Optimization (DPO) Schema (v2.0)
```json
{
  "task_id": "TASK-2026-001",
  "prompt": "Write a C++ function to check if a binary tree is balanced.",
  "chosen": "... (Optimized, secure implementation) ...",
  "rejected": "... (Original model output) ...",
  "human_rating": 5,
  "judge_scores": {
    "correctness": 5,
    "security": 5,
    "complexity": "O(N)"
  },
  "generation_method": "rlaif_auto",
  "timestamp": "2026-09-06T11:10:00Z"
}
```

---

### 💡 What Changed in this Architecture Doc:
1. **The Diagram is Now a Flywheel**: It visually shows the data flowing through the Static Analyzer, Secure Sandbox, Structured Judge, and finally splitting at the **RLAIF Router** (Auto-approve vs. Human Review).
2. **Zero-Trust is Front and Center**: Explicitly calls out E2B/Docker and pre-flight static analysis (`bandit`/`cppcheck`), which is exactly what enterprise platforms like micro1 require.
3. **Structured Outputs**: Replaced the vague "Strict JSON schema validation" with specific `instructor` / Pydantic enforcement, eliminating the regex parsing bottleneck.
4. **Upgraded Data Schemas**: The JSON examples now include the new multi-dimensional scores, security flags, and the crucial `generation_method` tag (`rlaif_auto` vs `human_curated`).

You now have a complete, perfectly aligned set of documentation (`CONTEXT.md`, `PLAN.md`, `ARCHITECTURE.md`) for your v2.0 upgrade. 

Whenever you are ready to start coding, just say **"Let's build Phase 1"** and I will write the exact Python code for the new `src/sandbox.py` and `src/analyzer.py`!