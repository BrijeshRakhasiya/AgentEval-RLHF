import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.models import ExecutionTrace, JudgeResult, DPODatasetEntry
from src.router import ConfidenceRouter, HITL_QUEUE
from src.main import app

client = TestClient(app)


def test_confidence_router_high_confidence_auto_flywheel():
    """Verifies high-confidence evaluation triggers RLAIF auto-rewrite and auto-export."""
    trace = ExecutionTrace(
        passed=True,
        stdout="All LRU Cache tests passed!",
        stderr="",
        exit_code=0,
        execution_time=0.2,
        security_flags=[],
        sandbox_type="docker_isolated",
        static_analysis_report="No security flags."
    )
    judge = JudgeResult(
        score=5,
        correctness_score=5,
        security_score=5,
        complexity_rating="O(1)",
        edge_case_handling="Excellent",
        reasoning="Optimal LRU Cache implementation."
    )

    with patch.object(ConfidenceRouter, "generate_rlaif_chosen", return_value="def optimal_lru(): pass"), \
         patch.object(ConfidenceRouter, "_export_dpo_entry") as mock_export:
        
        res = ConfidenceRouter.evaluate_and_route(
            task_id="HIGH-CONF-001",
            prompt="Design LRU Cache",
            code="class LRUCache: pass",
            language="python",
            trace=trace,
            judge=judge,
            combined_score=5.0
        )

        assert res["routed_to"] == "rlaif_auto"
        assert res["auto_exported"] is True
        assert res["generation_method"] == "rlaif_auto"
        mock_export.assert_called_once()


def test_confidence_router_low_confidence_hitl_queue():
    """Verifies low-confidence/failing evaluation routes to HITL Queue."""
    HITL_QUEUE.clear()
    trace = ExecutionTrace(
        passed=False,
        stdout="",
        stderr="AssertionError",
        exit_code=1,
        execution_time=0.3,
        security_flags=[],
        sandbox_type="docker_isolated",
        static_analysis_report="No security flags."
    )
    judge = JudgeResult(
        score=1,
        correctness_score=1,
        security_score=5,
        complexity_rating="O(V+E)",
        edge_case_handling="Poor",
        reasoning="Fails topological sort cycle check."
    )

    res = ConfidenceRouter.evaluate_and_route(
        task_id="LOW-CONF-002",
        prompt="Topological sort",
        code="def can_finish(): return True",
        language="python",
        trace=trace,
        judge=judge,
        combined_score=1.5
    )

    assert res["routed_to"] == "hitl_queue"
    assert res["auto_exported"] is False
    assert len(HITL_QUEUE) == 1
    assert HITL_QUEUE[0]["task_id"] == "LOW-CONF-002"


def test_hitl_queue_fastapi_endpoints():
    """Tests /queue/hitl GET and /queue/hitl/approve POST endpoints."""
    HITL_QUEUE.clear()
    HITL_QUEUE.append({
        "queue_id": "HITL-TEST-999",
        "task_id": "TEST-QUEUE-001",
        "language": "python",
        "prompt": "Test prompt",
        "rejected_code": "def foo(): fail",
        "suggested_chosen_code": "def foo(): pass",
        "execution_trace": {"passed": False, "exit_code": 1, "stdout": "", "stderr": "err"},
        "judge_result": {"score": 2, "reasoning": "bad"},
        "combined_score": 1.5,
        "queued_at": "2026-09-06T12:00:00Z"
    })

    # Test GET queue
    get_res = client.get("/queue/hitl")
    assert get_res.status_code == 200
    assert get_res.json()["queue_count"] == 1

    # Test POST approve
    approve_payload = {
        "task_id": "TEST-QUEUE-001",
        "prompt": "Test prompt",
        "chosen": "def foo(): fixed",
        "rejected": "def foo(): fail",
        "human_rating": 4,
        "judge_score": 2,
        "timestamp": "2026-09-06T12:05:00Z"
    }
    app_res = client.post("/queue/hitl/approve?queue_id=HITL-TEST-999", json=approve_payload)
    assert app_res.status_code == 200
    assert len(HITL_QUEUE) == 0
