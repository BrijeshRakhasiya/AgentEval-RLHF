import os
import json
import re
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Try importing ChatNVIDIA from langchain_nvidia_ai_endpoints with ChatOpenAI fallback
try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    HAS_CHAT_NVIDIA = True
except ImportError:
    HAS_CHAT_NVIDIA = False

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from .models import JudgeResult
except ImportError:
    from models import JudgeResult

load_dotenv()

# Top 5 Fallback Model Routing Chain (User-provided & NIM high-capacity models)
FALLBACK_MODELS = [
    "meta/llama-3.2-11b-vision-instruct",
    "meta/muse-glimmer-30b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nemotron-3-ultra-550b-a55b",
    "deepseek-ai/deepseek-v4-pro-0813"
]

logger = logging.getLogger("AgentEval.Judge")


def get_judge_llm(model_name: str):
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set. Please set it in .env or system environment.")

    model_kwargs = {}
    if "nemotron" in model_name:
        model_kwargs["chat_template_kwargs"] = {"enable_thinking": True}
    elif "deepseek" in model_name:
        model_kwargs["chat_template_kwargs"] = {"thinking": False}

    if HAS_CHAT_NVIDIA:
        try:
            return ChatNVIDIA(
                model=model_name,
                api_key=api_key,
                temperature=0.2,
                max_completion_tokens=1024,
                timeout=30,
                model_kwargs=model_kwargs
            )
        except Exception:
            pass

    # Fallback to ChatOpenAI endpoint
    extra_body = model_kwargs.get("chat_template_kwargs")
    openai_kwargs = {"extra_body": {"chat_template_kwargs": extra_body}} if extra_body else {}
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        model=model_name,
        temperature=0.2,
        max_tokens=1024,
        timeout=30,
        **openai_kwargs
    )


def run_llm_judge(prompt: str, generated_code: str, execution_log: str, model_chain: Optional[List[str]] = None) -> JudgeResult:
    """
    Evaluates generated code against problem specification and execution trace using an LLM Model Router.
    Automatically iterates through a 5-model fallback chain if a model is retired (410), rate-limited, or unavailable.
    """
    models_to_try = model_chain if model_chain else FALLBACK_MODELS
    last_error = ""

    system_prompt = (
        "You are an expert AI Code Quality & Correctness Judge for an RLHF evaluation system.\n"
        "Your task is to evaluate code submitted by an AI agent based on the problem prompt, "
        "the generated source code, and its execution trace log (stdout, stderr, pass/fail status).\n\n"
        "Scoring Rubric (Integer 1-5):\n"
        "1: Completely incorrect, syntax error, or complete execution failure.\n"
        "2: Fails most tests, logic is significantly flawed.\n"
        "3: Partially working, passes some tests but lacks edge-case handling or has minor bugs.\n"
        "4: Mostly correct, passes execution tests, minor style or performance improvements possible.\n"
        "5: Perfect implementation, fully correct, optimal, clean, and passes all tests.\n\n"
        "CRITICAL REQUIREMENT:\n"
        "You MUST respond ONLY with a raw valid JSON object. Do not include markdown code block formatting or preambles.\n"
        "The JSON MUST follow this exact schema:\n"
        "{\n"
        '  "score": <integer 1 to 5>,\n'
        '  "reasoning": "<concise explanation summarizing correctness, code quality, and execution analysis>"\n'
        "}"
    )

    user_content = (
        f"### Problem Prompt:\n{prompt}\n\n"
        f"### Generated Code:\n{generated_code}\n\n"
        f"### Execution Trace Log:\n{execution_log}"
    )

    for model_name in models_to_try:
        try:
            llm = get_judge_llm(model_name)
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            raw_text = str(response.content).strip()

            # Extract JSON from response text
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                score = int(data.get("score", 3))
                score = max(1, min(5, score))
                reasoning = str(data.get("reasoning", "No reasoning provided by judge."))
                # Tag reasoning with the model that successfully evaluated it
                reasoning = f"[Evaluated by {model_name}] {reasoning}"
                return JudgeResult(score=score, reasoning=reasoning)
            else:
                last_error = f"Model '{model_name}' did not return valid JSON format."
                continue
        except Exception as e:
            err_msg = str(e)
            last_error = f"Model '{model_name}' failed: {err_msg[:120]}"
            print(f"[Router Alert] {last_error} -> Trying next fallback model...")
            continue

    # Fallback response if all models in routing chain failed
    return JudgeResult(
        score=1,
        reasoning=f"LLM Judge Routing Chain Exhausted. Last Error: {last_error}"
    )
