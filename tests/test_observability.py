import os
import sys
import json
import pytest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.observability import ObservabilityTracer


def test_observability_local_telemetry_logging(tmp_path):
    """Verifies ObservabilityTracer logs evaluation traces cleanly."""
    task_id = "OBS-TEST-001"
    trace_data = {"passed": True, "execution_time": 0.1, "exit_code": 0, "security_flags": []}
    judge_data = {"score": 5, "correctness_score": 5, "security_score": 5, "complexity_rating": "O(1)"}
    routing_info = {"routed_to": "rlaif_auto"}

    payload = ObservabilityTracer.log_evaluation_trace(
        task_id=task_id,
        language="python",
        prompt="Test prompt",
        code="def foo(): pass",
        trace_data=trace_data,
        judge_data=judge_data,
        combined_score=5.0,
        routing_info=routing_info
    )

    assert payload["task_id"] == "OBS-TEST-001"
    assert payload["combined_score"] == 5.0
    assert payload["routing_destination"] == "rlaif_auto"

    # Check local JSONL file exists in data directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "data", "telemetry_traces.jsonl")
    assert os.path.exists(log_path)
