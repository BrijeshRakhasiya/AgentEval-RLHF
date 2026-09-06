import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .models import TaskRequest, ExecutionTrace, JudgeResult, EvaluationResponse, DPODatasetEntry
    from .sandbox import PythonSandbox, CPPSandbox
    from .judge import run_llm_judge
    from .router import ConfidenceRouter
    from .observability import ObservabilityTracer
except ImportError:
    from models import TaskRequest, ExecutionTrace, JudgeResult, EvaluationResponse, DPODatasetEntry
    from sandbox import PythonSandbox, CPPSandbox
    from judge import run_llm_judge
    from router import ConfidenceRouter
    from observability import ObservabilityTracer

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
    Synthesizes deterministic sandbox test outcome with multi-dimensional LLM judge scores.
    - Deterministic Sandbox Pass/Fail: 40%
    - LLM Judge Correctness Score: 30%
    - LLM Judge Security Score: 30%
    """
    deterministic_score = 5.0 if trace.passed else 1.0
    correctness = float(judge.correctness_score)
    security = float(judge.security_score)

    if trace.security_flags:
        security = min(security, 1.0)

    combined = (0.4 * deterministic_score) + (0.3 * correctness) + (0.3 * security)
    return round(combined, 2)


@app.post("/evaluate/python", response_model=EvaluationResponse)
def evaluate_python(request: TaskRequest):
    """
    Evaluates Python agent output, triggers ConfidenceRouter (RLAIF Auto-Flywheel vs HITL Queue).
    """
    try:
        trace = PythonSandbox.run(code=request.code, test_cases=request.test_cases)
        exec_log = (
            f"Test Suite Status: {'PASSED' if trace.passed else 'FAILED'}\n"
            f"Exit Code: {trace.exit_code}\n"
            f"Execution Time: {trace.execution_time}s\n"
            f"Static Analysis Security Report:\n{trace.static_analysis_report}\n"
            f"Standard Output:\n{trace.stdout}\n"
            f"Standard Error:\n{trace.stderr}"
        )
        judge = run_llm_judge(prompt=request.prompt, generated_code=request.code, execution_log=exec_log)
        combined = compute_combined_score(trace, judge)

        # Route through RLAIF Data Flywheel
        routing_info = ConfidenceRouter.evaluate_and_route(
            task_id=request.task_id,
            prompt=request.prompt,
            code=request.code,
            language="python",
            trace=trace,
            judge=judge,
            combined_score=combined
        )

        # Log Observability Telemetry Trace
        ObservabilityTracer.log_evaluation_trace(
            task_id=request.task_id,
            language="python",
            prompt=request.prompt,
            code=request.code,
            trace_data=trace.model_dump(),
            judge_data=judge.model_dump(),
            combined_score=combined,
            routing_info=routing_info
        )

        return EvaluationResponse(
            task_id=request.task_id,
            language="python",
            execution_trace=trace,
            judge_result=judge,
            combined_score=combined,
            routing_info=routing_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Python evaluation failed: {str(e)}")


@app.post("/evaluate/cpp", response_model=EvaluationResponse)
def evaluate_cpp(request: TaskRequest):
    """
    Evaluates C++ agent output, triggers ConfidenceRouter (RLAIF Auto-Flywheel vs HITL Queue).
    """
    try:
        trace = CPPSandbox.run(code=request.code, test_cases=request.test_cases)
        exec_log = (
            f"Test Suite Status: {'PASSED' if trace.passed else 'FAILED'}\n"
            f"Exit Code: {trace.exit_code}\n"
            f"Execution Time: {trace.execution_time}s\n"
            f"Static Analysis Security Report:\n{trace.static_analysis_report}\n"
            f"Standard Output:\n{trace.stdout}\n"
            f"Standard Error:\n{trace.stderr}"
        )
        judge = run_llm_judge(prompt=request.prompt, generated_code=request.code, execution_log=exec_log)
        combined = compute_combined_score(trace, judge)

        # Route through RLAIF Data Flywheel
        routing_info = ConfidenceRouter.evaluate_and_route(
            task_id=request.task_id,
            prompt=request.prompt,
            code=request.code,
            language="cpp",
            trace=trace,
            judge=judge,
            combined_score=combined
        )

        # Log Observability Telemetry Trace
        ObservabilityTracer.log_evaluation_trace(
            task_id=request.task_id,
            language="cpp",
            prompt=request.prompt,
            code=request.code,
            trace_data=trace.model_dump(),
            judge_data=judge.model_dump(),
            combined_score=combined,
            routing_info=routing_info
        )

        return EvaluationResponse(
            task_id=request.task_id,
            language="cpp",
            execution_trace=trace,
            judge_result=judge,
            combined_score=combined,
            routing_info=routing_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"C++ evaluation failed: {str(e)}")


@app.get("/queue/hitl")
def get_hitl_queue():
    """
    Returns pending low/medium confidence evaluations awaiting human curation.
    """
    return {
        "status": "success",
        "queue_count": len(ConfidenceRouter.get_hitl_queue()),
        "items": ConfidenceRouter.get_hitl_queue()
    }


@app.post("/queue/hitl/approve")
def approve_hitl_item(queue_id: str, entry: DPODatasetEntry):
    """
    Approve human-curated DPO entry from HITL queue and export to jsonl.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    dpo_path = os.path.join(data_dir, "dpo_dataset.jsonl")

    try:
        with open(dpo_path, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        
        ConfidenceRouter.remove_from_queue(queue_id)
        return {
            "status": "success",
            "message": f"Successfully approved queue item '{queue_id}' and exported to {dpo_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve HITL queue item: {str(e)}")


@app.post("/export/dpo")
def export_dpo(entry: DPODatasetEntry):
    """
    Appends human-verified DPO pair to data/dpo_dataset.jsonl.
    """
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
