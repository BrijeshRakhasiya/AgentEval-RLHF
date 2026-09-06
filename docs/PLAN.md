# AgentEval-RLHF: Agentic Development Life Cycle (ADLC) Plan

## ADLC Phase Overview (v2.0 Frontier Upgrade)
This project follows the **Agentic Development Life Cycle (ADLC)**, structured specifically for non-deterministic AI agent architectures. We are now executing the **v2.0 Frontier Upgrade** to align with enterprise standards (micro1, Abundant).

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       Agentic Development Life Cycle (ADLC) - v2.0                  │
├─────────────────────┬──────────────────────┬──────────────────────┬─────────────────┤
│ Phase 1:            │ Phase 2:             │ Phase 3:             │ Phase 4:        │
│ Zero-Trust          │ Structured           │ RLAIF Data           │ Repo-Level,     │
│ Sandboxing &        │ Multi-Dimensional    │ Flywheel &           │ CLI &           │
│ Static Analysis     │ LLM Judging          │ Smart HITL Routing   │ Observability   │
└─────────────────────┴──────────────────────┴──────────────────────┴─────────────────┘
```

---

## Phase 1: Zero-Trust Sandboxing & Static Analysis (Sprint 1)
- **Objective:** Eliminate legacy subprocess security risks and support stateful, isolated execution with pre-flight security checks.
- **1.1 Dependency Upgrade:** Add `e2b-code-interpreter` (or `docker` SDK), `bandit` (Python security), and `cppcheck` (C++ security) to `pyproject.toml` / `requirements.txt`.
- **1.2 Refactor `src/sandbox.py`:** Replace `subprocess.run` with `SecurePythonSandbox` and `SecureCPPSandbox` classes utilizing E2B ephemeral microVMs or Docker containers.
- **1.3 Implement Static Analyzer:** Create `src/analyzer.py` to run `bandit` and `cppcheck` on incoming code strings before dynamic execution.
- **1.4 Update Pydantic Models:** Modify `ExecutionTrace` in `src/models.py` to include `security_flags: List[str]`, `sandbox_type: str`, and `static_analysis_report: str`.
- **1.5 Security Integration Tests:** Write tests in `tests/test_sandbox.py` to verify malicious code blocking (e.g., `os.system('rm -rf /')`), strict timeout enforcement, and guaranteed environment teardown.

---

## 🧠 Phase 2: Structured Evaluation & Multi-Dimensional Judging (Sprint 2)
- **Objective:** Replace brittle regex JSON parsing with guaranteed structured outputs and evaluate code across multiple dimensions.
- **2.1 Dependency Upgrade:** Add `instructor` and `pydantic` (latest) to dependencies.
- **2.2 Refactor `src/judge.py`:** Remove regex JSON extraction. Implement `instructor.from_openai()` (or native NIM structured outputs) to enforce the `JudgeResult` Pydantic schema natively.
- **2.3 Expand `JudgeResult` Schema:** Update `src/models.py` to include multi-dimensional metrics: `correctness_score: int`, `security_score: int`, `complexity_rating: str`, and `edge_case_handling: str`.
- **2.4 Upgrade System Prompts:** Rewrite the LLM Judge system prompt in `src/judge.py` to explicitly evaluate the `static_analysis_report` alongside the execution trace.
- **2.5 Validation Tests:** Write tests in `tests/test_judge.py` to guarantee 100% schema adherence and verify that malformed LLM outputs are automatically retried by `instructor`.

---

## 🔄 Phase 3: RLAIF Data Flywheel & Smart Routing (Sprint 3)
- **Objective:** Automate 80% of DPO pair generation via Reinforcement Learning from AI Feedback (RLAIF), reserving humans for high-value edge cases.
- **3.1 Build Confidence Router:** Create `src/router.py` and implement the `ConfidenceRouter` class.
- **3.2 Define Routing Logic:**
  - **High Confidence:** If `execution_trace.passed == True` AND `judge_result.combined_score >= 4.5` → Trigger a stronger model (e.g., `deepseek-v4-pro`) to auto-generate the optimized "Chosen" response.
  - **Low/Medium Confidence:** If `score < 4.5` or `passed == False` → Route to the HITL Queue.
- **3.3 Update Streamlit Dashboard:** Refactor `src/app.py` to add a "RLAIF Edge-Case Queue" tab. Show only medium/low-confidence pairs requiring human review, complete with a side-by-side code diff viewer.
- **3.4 Tagging & Metadata:** Ensure the `DPODatasetEntry` model automatically tags each exported pair with `"generation_method": "rlaif_auto"` or `"generation_method": "human_curated"`.

---

## 📊 Phase 4: Repo-Level Eval, CLI & Observability (Sprint 4)
- **Objective:** Support real-world, full-repository agent scenarios and provide enterprise-grade monitoring and developer experience.
- **4.1 Build the CLI:** Create `agent_eval/cli.py` using `typer` or `click`. Implement commands like `agent-eval run --file agent.py --tests test.py --export-dpo`.
- **4.2 Implement Repo-Level Sandbox:** Add a "Repo Mode" to `src/sandbox.py`. Allow passing a `git_repo_url` and `issue_description`. The sandbox will clone the repo, apply the generated code as a patch, and run the repo's native `pytest`/`make` test suite.
- **4.3 Integrate Observability:** Create `src/observability.py`. Log all `TaskRequest` → `ExecutionTrace` → `JudgeResult` flows to LangSmith or Arize Phoenix via OpenTelemetry or native SDKs.
- **4.4 Documentation & Polish:** Update `README.md` to highlight the v2.0 Top 1% features (E2B security, RLAIF flywheel, SWE-bench compatibility). Add a "Quickstart" section for the new CLI.

---

## ✅ Definition of Done (DoD) for v2.0
For each phase, the following must be true before merging to main:
- All new features have corresponding unit/integration tests in `tests/`.
- The `uv run pytest` suite passes with a 100% success rate.
- The `dpo_dataset.jsonl` output strictly validates against the updated Pydantic schemas.
- No hardcoded API keys or insecure subprocess calls remain in the active execution path.
- Observability traces are successfully visible in the configured telemetry backend.