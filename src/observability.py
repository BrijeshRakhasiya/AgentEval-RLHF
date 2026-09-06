import os
import json
import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:
    from langsmith import Client as LangSmithClient
    HAS_LANGSMITH = True
except ImportError:
    HAS_LANGSMITH = False

load_dotenv()

LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "Agentic Evaluation")


class ObservabilityTracer:
    """
    Enterprise Observability Telemetry engine.
    Streams TaskRequest -> ExecutionTrace -> JudgeResult traces to LangSmith
    or falls back to local structured JSON telemetry logs.
    """

    _client: Optional[Any] = None

    @classmethod
    def get_client(cls):
        if cls._client is None and HAS_LANGSMITH:
            api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
            if api_key:
                try:
                    cls._client = LangSmithClient(api_key=api_key)
                except Exception as e:
                    print(f"[Observability Alert] LangSmith client initialization warning: {str(e)}")
        return cls._client

    @classmethod
    def log_evaluation_trace(
        cls,
        task_id: str,
        language: str,
        prompt: str,
        code: str,
        trace_data: Dict[str, Any],
        judge_data: Dict[str, Any],
        combined_score: float,
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Logs complete multi-step agent evaluation telemetry trace.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run_payload = {
            "task_id": task_id,
            "language": language,
            "prompt": prompt,
            "code_length": len(code),
            "execution_passed": trace_data.get("passed", False),
            "execution_time": trace_data.get("execution_time", 0.0),
            "exit_code": trace_data.get("exit_code", 0),
            "security_flags_count": len(trace_data.get("security_flags", [])),
            "judge_score": judge_data.get("score", 1),
            "correctness_score": judge_data.get("correctness_score", 1),
            "security_score": judge_data.get("security_score", 1),
            "complexity_rating": judge_data.get("complexity_rating", "O(1)"),
            "combined_score": combined_score,
            "routing_destination": routing_info.get("routed_to", "unknown"),
            "timestamp": timestamp
        }

        # 1. Attempt LangSmith Telemetry Log
        client = cls.get_client()
        if client:
            try:
                client.create_run(
                    name=f"AgentEval-{task_id}",
                    run_type="chain",
                    inputs={"prompt": prompt, "code": code},
                    outputs={
                        "combined_score": combined_score,
                        "judge_result": judge_data,
                        "execution_trace": trace_data,
                        "routing": routing_info
                    },
                    project_name=LANGSMITH_PROJECT
                )
                run_payload["telemetry_backend"] = "LangSmith"
            except Exception as err:
                run_payload["telemetry_backend"] = f"LangSmith Error ({str(err)[:50]})"
        else:
            run_payload["telemetry_backend"] = "LocalJSONL"

        # 2. Local Append Log (Guaranteed Audit Trail)
        cls._append_local_trace(run_payload)

        return run_payload

    @staticmethod
    def _append_local_trace(payload: Dict[str, Any]):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        log_path = os.path.join(data_dir, "telemetry_traces.jsonl")

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass
