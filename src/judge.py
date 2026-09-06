import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
import instructor
from openai import OpenAI

try:
    from .models import JudgeResult
except ImportError:
    from models import JudgeResult

load_dotenv()

# Top 5 Fallback Model Routing Chain (NIM high-capacity models)
FALLBACK_MODELS = [
    "meta/muse-glimmer-30b",
    "nvidia/nemotron-4-340b-instruct",
    "deepseek-ai/deepseek-r1",
    "meta/llama3-70b-instruct"
]

logger = logging.getLogger("AgentEval.Judge")


def get_instructor_client() -> instructor.Instructor:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set. Please set it in .env or system environment.")

    raw_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        timeout=30.0
    )
    return instructor.from_openai(raw_client, mode=instructor.Mode.MD_JSON)


def run_llm_judge(prompt: str, generated_code: str, execution_log: str, model_chain: Optional[List[str]] = None) -> JudgeResult:
    """
    Evaluates generated code against problem specification and execution trace using an Instructor-enforced LLM Router.
    Enforces multi-dimensional evaluation (score, correctness, security, complexity, edge_case_handling, reasoning).
    Iterates through fallback models if a model is retired (410), rate-limited, or unavailable.
    """
    models_to_try = model_chain if model_chain else FALLBACK_MODELS
    last_error = ""

    client = get_instructor_client()

    system_prompt = (
        "You are an expert AI Code Quality, Security, and Architectural Judge for an RLHF evaluation system.\n"
        "Your task is to evaluate code submitted by an AI agent based on:\n"
        "1. Problem Specification\n"
        "2. Generated Source Code\n"
        "3. Static Security Analysis Report & Execution Trace Log (stdout, stderr, exit code)\n\n"
        "Multi-Dimensional Scoring Rubric:\n"
        "- score (1-5): Overall rating combining correctness, safety, and performance.\n"
        "- correctness_score (1-5): Algorithmic correctness and pass rate on problem specs.\n"
        "- security_score (1-5): Code safety, absence of vulnerabilities (eval, os.system, strcpy, unhandled exceptions).\n"
        "- complexity_rating (str): Estimated asymptotic time/space complexity (e.g., 'O(N log N)', 'O(N)', 'O(1)').\n"
        "- edge_case_handling (str): Assessment of boundary conditions (e.g., 'Excellent', 'Adequate', 'Poor', 'Missing null checks').\n"
        "- reasoning (str): Concise critique detailing execution findings, security warnings, and optimization feedback.\n"
        "Be rigorous and accurate."
    )

    user_content = (
        f"### Problem Prompt:\n{prompt}\n\n"
        f"### Generated Code:\n{generated_code}\n\n"
        f"### Execution & Static Security Trace Log:\n{execution_log}"
    )

    for model_name in models_to_try:
        try:
            kwargs = {
                "model": model_name,
                "response_model": JudgeResult,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "max_retries": 2,
                "temperature": 0.2
            }
            if "nemotron" in model_name:
                kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}
            elif "deepseek" in model_name:
                kwargs["extra_body"] = {"chat_template_kwargs": {"thinking": False}}

            result: JudgeResult = client.chat.completions.create(**kwargs)
            result.reasoning = f"[Evaluated by {model_name}] {result.reasoning}"
            return result

        except Exception as e:
            err_msg = str(e)
            last_error = f"Model '{model_name}' failed: {err_msg[:120]}"
            print(f"[Router Alert] {last_error} -> Trying next fallback model...")
            continue

    # Fallback response if all models in routing chain failed
    return JudgeResult(
        score=1,
        correctness_score=1,
        security_score=1,
        complexity_rating="Unknown",
        edge_case_handling="Failed Execution",
        reasoning=f"LLM Judge Routing Chain Exhausted. Last Error: {last_error}"
    )
