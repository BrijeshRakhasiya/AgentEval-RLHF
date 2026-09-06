import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .models import TaskRequest, ExecutionTrace, JudgeResult, EvaluationResponse, DPODatasetEntry
    from .sandbox import PythonSandbox, CPPSandbox
    from .judge import run_llm_judge
except ImportError:
    from models import TaskRequest, ExecutionTrace, JudgeResult, EvaluationResponse, DPODatasetEntry
    from sandbox import PythonSandbox, CPPSandbox
    from judge import run_llm_judge

app = FastAPI(
    title="AgentEval-RLHF Engine",
    description="Enterprise Multi-Language AI Agent Evaluation & RLHF Data Pipeline Engine",
    version="1.0.0"
)

# Enable CORS for Streamlit HITL dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "AgentEval-RLHF API Gateway Server",
        "version": "1.0.0"
    }


def compute_combined_score(trace: ExecutionTrace, judge: JudgeResult) -> float:
    """
    Synthesizes deterministic sandbox test outcome with qualitative judge score.
    - Sandbox Pass/Fail contributes 50% (5.0 for pass, 1.0 for fail)
    - LLM Judge Score contributes 50% (1.0 - 5.0)
    """
    deterministic_score = 5.0 if trace.passed else 1.0
    combined = (0.5 * deterministic_score) + (0.5 * float(judge.score))
    return round(combined, 2)


@app.post("/evaluate/python", response_model=EvaluationResponse)
def evaluate_python(request: TaskRequest):
    """
    Evaluates Python agent output by running PythonSandbox tests and LLM Judge critique.
    """
    try:
        trace = PythonSandbox.run(code=request.code, test_cases=request.test_cases)
        exec_log = (
            f"Test Suite Status: {'PASSED' if trace.passed else 'FAILED'}\n"
            f"Exit Code: {trace.exit_code}\n"
            f"Execution Time: {trace.execution_time}s\n"
            f"Standard Output:\n{trace.stdout}\n"
            f"Standard Error:\n{trace.stderr}"
        )
        judge = run_llm_judge(prompt=request.prompt, generated_code=request.code, execution_log=exec_log)
        combined = compute_combined_score(trace, judge)

        return EvaluationResponse(
            task_id=request.task_id,
            language="python",
            execution_trace=trace,
            judge_result=judge,
            combined_score=combined
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Python evaluation failed: {str(e)}")


@app.post("/evaluate/cpp", response_model=EvaluationResponse)
def evaluate_cpp(request: TaskRequest):
    """
    Evaluates C++ agent output by compiling with g++ and running CPPSandbox tests + LLM Judge critique.
    """
    try:
        trace = CPPSandbox.run(code=request.code, test_cases=request.test_cases)
        exec_log = (
            f"Test Suite Status: {'PASSED' if trace.passed else 'FAILED'}\n"
            f"Exit Code: {trace.exit_code}\n"
            f"Execution Time: {trace.execution_time}s\n"
            f"Standard Output:\n{trace.stdout}\n"
            f"Standard Error:\n{trace.stderr}"
        )
        judge = run_llm_judge(prompt=request.prompt, generated_code=request.code, execution_log=exec_log)
        combined = compute_combined_score(trace, judge)

        return EvaluationResponse(
            task_id=request.task_id,
            language="cpp",
            execution_trace=trace,
            judge_result=judge,
            combined_score=combined
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"C++ evaluation failed: {str(e)}")


@app.post("/export/dpo")
def export_dpo(entry: DPODatasetEntry):
    """
    Appends human-verified DPO pair to data/dpo_dataset.jsonl.
    """
    # Create data directory if it does not exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    dpo_path = os.path.join(data_dir, "dpo_dataset.jsonl")
    try:
        with open(dpo_path, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        return {
            "status": "success",
            "message": f"Entry for task '{entry.task_id}' successfully exported to {dpo_path}",
            "file": os.path.abspath(dpo_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append DPO entry: {str(e)}")
