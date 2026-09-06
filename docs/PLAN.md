# AgentEval-RLHF: Agentic Development Life Cycle (ADLC) Plan

## ADLC Phase Overview
This project follows the **Agentic Development Life Cycle (ADLC)**, structured specifically for non-deterministic AI agent architectures:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Agentic Development Life Cycle (ADLC)                 │
├─────────────────┬──────────────────┬───────────────────┬────────────────────┤
│ Phase 1:        │ Phase 2:         │ Phase 3:          │ Phase 4:           │
│ Specification & │ Agent Sandbox &  │ Dual Evaluation   │ HITL Curation &    │
│ Prompt Design   │ Execution Layer  │ Pipeline          │ Dataset Export     │
└─────────────────┴──────────────────┴───────────────────┴────────────────────┘
```

---

## Phase 1: Core System Architecture & Schemas (Day 1)
- [x] Finalize `CONTEXT.md`, `PLAN.md`, and `ARCHITECTURE.md`.
- [ ] Define Pydantic models for `TaskRequest`, `ExecutionTrace`, `JudgeResult`, and `DPODataPair`.
- [ ] Set up project structure, virtual environments, and `.env` template.

## Phase 2: Isolated Sandbox Engine (Day 2)
- [ ] Build Python sandbox runner using `subprocess` with timeout (5s) and resource limits.
- [ ] Build C++ sandbox runner (`g++` compilation + execution test runner).
- [ ] Implement error capturing (stdout, stderr, exit codes).

## Phase 3: Dual Evaluation & Multi-Judge Engine (Day 3)
- [ ] Integrate Groq / Ollama / OpenAI adapter layer for LLM inference.
- [ ] Construct LLM-as-a-Judge prompt templates with structured JSON output enforcement.
- [ ] Implement scoring synthesizer (combines deterministic test boolean + judge qualitative score).

## Phase 4: HITL Interface & Dataset Exporter (Day 4)
- [ ] Build Streamlit Human Curation Portal.
- [ ] Implement interactive trace inspector and code editor UI.
- [ ] Implement export functionality for `sft_dataset.jsonl` and `dpo_dataset.jsonl`.
- [ ] Build Docker containerization setup and write production deployment documentation.