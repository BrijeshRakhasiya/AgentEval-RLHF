from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TaskRequest(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the evaluation task")
    language: str = Field(..., description="Programming language: 'python' or 'cpp'")
    prompt: str = Field(..., description="Problem prompt / specification")
    code: str = Field(..., description="Generated source code to be executed")
    test_cases: str = Field(..., description="Unit test cases or main assertion code")


class ExecutionTrace(BaseModel):
    passed: bool = Field(..., description="True if code executed successfully and all tests passed")
    stdout: str = Field("", description="Standard output from execution")
    stderr: str = Field("", description="Standard error / compiler output")
    exit_code: int = Field(0, description="Process exit code")
    execution_time: float = Field(0.0, description="Execution runtime in seconds")
    security_flags: list[str] = Field(default_factory=list, description="Vulnerability flags from static security analysis")
    sandbox_type: str = Field("docker_isolated", description="Sandbox type (docker_isolated / subprocess_fallback)")
    static_analysis_report: str = Field("", description="Static security analysis report summary")


class JudgeResult(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Overall qualitative evaluation score from 1 to 5")
    correctness_score: int = Field(5, ge=1, le=5, description="Algorithmic correctness and specification compliance score from 1 to 5")
    security_score: int = Field(5, ge=1, le=5, description="Security and safety score from 1 to 5 based on static analysis and code practices")
    complexity_rating: str = Field("O(1)", description="Estimated time/space complexity rating (e.g. O(N log N), O(N^2))")
    edge_case_handling: str = Field("Adequate", description="Qualitative evaluation of boundary and edge case handling")
    reasoning: str = Field(..., description="Detailed explanation/critique behind the assigned score")

    @field_validator("score", "correctness_score", "security_score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError("Score must be an integer between 1 and 5.")
        return v


class EvaluationResponse(BaseModel):
    task_id: str
    language: str
    execution_trace: ExecutionTrace
    judge_result: JudgeResult
    combined_score: float = Field(..., description="Synthesized total score combining sandbox outcome and judge rating")
    routing_info: Optional[dict] = Field(None, description="RLAIF Flywheel routing info (rlaif_auto vs hitl_queue)")


class DPODatasetEntry(BaseModel):
    task_id: str
    prompt: str
    chosen: str = Field(..., description="Human-curated / corrected optimal code snippet")
    rejected: str = Field(..., description="Original model-generated raw code snippet")
    human_rating: int = Field(..., ge=1, le=5, description="Human expert rating (1-5)")
    judge_score: int = Field(..., ge=1, le=5, description="Automated LLM Judge score (1-5)")
    correctness_score: Optional[int] = Field(None, description="Algorithmic correctness rating (1-5)")
    security_score: Optional[int] = Field(None, description="Security and safety score (1-5)")
    complexity_rating: Optional[str] = Field(None, description="Time/space complexity rating")
    generation_method: str = Field("human_curated", description="DPO pair origin: 'human_curated' or 'rlaif_auto'")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp")

    @field_validator("human_rating", "judge_score")
    @classmethod
    def validate_ratings(cls, v: int) -> int:
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return v
