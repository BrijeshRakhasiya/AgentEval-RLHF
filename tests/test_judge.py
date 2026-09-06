import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.models import JudgeResult
from src.judge import run_llm_judge, FALLBACK_MODELS

load_dotenv()


def test_judge_result_schema_validation():
    """Verifies JudgeResult Pydantic schema validation for multi-dimensional metrics."""
    result = JudgeResult(
        score=4,
        correctness_score=5,
        security_score=4,
        complexity_rating="O(N log N)",
        edge_case_handling="Excellent",
        reasoning="Code passes all tests cleanly with patience sorting."
    )
    assert result.score == 4
    assert result.correctness_score == 5
    assert result.security_score == 4
    assert result.complexity_rating == "O(N log N)"
    assert result.edge_case_handling == "Excellent"

    # Test score validation out-of-bounds (must be 1 to 5)
    with pytest.raises(ValueError):
        JudgeResult(
            score=6,
            correctness_score=5,
            security_score=5,
            complexity_rating="O(1)",
            edge_case_handling="Good",
            reasoning="Invalid score test"
        )


def test_judge_fallback_routing_on_error():
    """Verifies that model routing iterates through FALLBACK_MODELS if the primary model fails."""
    mock_failing_client = MagicMock()
    # First model call raises RuntimeError, second model call succeeds
    mock_successful_response = JudgeResult(
        score=5,
        correctness_score=5,
        security_score=5,
        complexity_rating="O(N)",
        edge_case_handling="Adequate",
        reasoning="Successfully evaluated after model fallback."
    )
    
    mock_failing_client.chat.completions.create.side_effect = [
        RuntimeError("Model 410 Gone error"),
        mock_successful_response
    ]

    with patch("src.judge.get_instructor_client", return_value=mock_failing_client):
        result = run_llm_judge(
            prompt="Test prompt",
            generated_code="def foo(): return 42",
            execution_log="Test log"
        )

    assert result.score == 5
    assert "[Evaluated by" in result.reasoning
    assert mock_failing_client.chat.completions.create.call_count == 2


@pytest.mark.skipif(not os.getenv("NVIDIA_API_KEY"), reason="NVIDIA_API_KEY required for live test")
def test_live_instructor_llm_judge():
    """End-to-end live test querying NVIDIA NIM API via Instructor."""
    prompt = "Write a Python function `add(a: int, b: int) -> int`."
    code = "def add(a: int, b: int) -> int:\n    return a + b"
    exec_log = "Test Suite Status: PASSED\nExit Code: 0\nExecution Time: 0.05s\nStandard Output:\nAll tests passed!\nStandard Error:\n"

    result = run_llm_judge(prompt=prompt, generated_code=code, execution_log=exec_log)

    assert isinstance(result, JudgeResult)
    assert 1 <= result.score <= 5
    assert 1 <= result.correctness_score <= 5
    assert 1 <= result.security_score <= 5
    assert len(result.reasoning) > 0
    assert "[Evaluated by" in result.reasoning
