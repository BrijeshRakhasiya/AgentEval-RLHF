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


class JudgeResult(BaseModel):
    score: int = Field(..., ge=1, le=5, description="Qualitative evaluation score from 1 to 5")
    reasoning: str = Field(..., description="Detailed explanation/critique behind the assigned score")

    @field_validator("score")
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


class DPODatasetEntry(BaseModel):
    task_id: str
    prompt: str
    chosen: str = Field(..., description="Human-curated / corrected optimal code snippet")
    rejected: str = Field(..., description="Original model-generated raw code snippet")
    human_rating: int = Field(..., ge=1, le=5, description="Human expert rating (1-5)")
    judge_score: int = Field(..., ge=1, le=5, description="Automated LLM Judge score (1-5)")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp")

    @field_validator("human_rating", "judge_score")
    @classmethod
    def validate_ratings(cls, v: int) -> int:
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return v
