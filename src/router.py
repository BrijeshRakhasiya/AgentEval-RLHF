import os
import json
import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

try:
    from .models import ExecutionTrace, JudgeResult, DPODatasetEntry
except ImportError:
    from models import ExecutionTrace, JudgeResult, DPODatasetEntry

load_dotenv()

# Global in-memory queue for low/medium confidence evaluations awaiting human curation
HITL_QUEUE: List[Dict[str, Any]] = []


def get_openai_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not set in environment.")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        timeout=30.0
    )


class ConfidenceRouter:
    """
    RLAIF Data Flywheel & Confidence Router.
    Routes passing high-confidence evaluations (score >= 4.5 & clean tests) to RLAIF auto-rewrite
    and auto-exports them to data/dpo_dataset.jsonl.
    Routes low/medium confidence or failing evaluations to the HITL curation queue.
    """

    @staticmethod
    def generate_rlaif_chosen(prompt: str, raw_code: str, language: str = "python", execution_log: Optional[str] = None) -> str:
        """
        Queries a high-capability NIM model to generate an optimal, bug-free, clean 'Chosen' completion.
        If execution_log is provided, fixes logic bugs, edge cases, and removes security vulnerabilities.
        """
        try:
            client = get_openai_client()
            system_prompt = (
                f"You are an elite AI Code Repair & Optimization Assistant specializing in {language}.\n"
                "Given a problem prompt, original agent code, and execution trace / error log:\n"
                "1. If the code failed or has security warnings, FIX all logic bugs, edge cases, and remove any security vulnerabilities (eval, os.system, strcpy).\n"
                "2. Produce the absolute optimal, cleanest, safest, and most readable implementation possible.\n"
                "Respond ONLY with raw executable source code. Do NOT wrap code in markdown block quotes or preambles."
            )

            user_prompt = f"### Problem Prompt:\n{prompt}\n\n### Original Implementation:\n{raw_code}"
            if execution_log:
                user_prompt += f"\n\n### Execution & Error Log:\n{execution_log}"

            res = client.chat.completions.create(
                model="meta/llama-3.2-11b-vision-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            raw_text = res.choices[0].message.content or raw_code
            # Strip markdown fence if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 2 and lines[-1].startswith("```"):
                    cleaned = "\n".join(lines[1:-1]).strip()
            return cleaned
        except Exception as e:
            print(f"[Router Alert] RLAIF Code Optimization query failed: {str(e)}")
            return raw_code

    @classmethod
    def evaluate_and_route(
        cls,
        task_id: str,
        prompt: str,
        code: str,
        language: str,
        trace: ExecutionTrace,
        judge: JudgeResult,
        combined_score: float
    ) -> Dict[str, Any]:
        """
        Determines whether evaluation can be auto-curated via RLAIF or requires HITL review.
        """
        is_high_confidence = (
            trace.passed is True
            and combined_score >= 4.5
            and not trace.security_flags
        )

        exec_log_summary = f"Exit code: {trace.exit_code}\nStderr: {trace.stderr}\nSecurity flags: {trace.security_flags}"

        if is_high_confidence:
            # High Confidence RLAIF Auto-Flywheel Path
            chosen_code = cls.generate_rlaif_chosen(prompt, code, language, exec_log_summary)

            entry = DPODatasetEntry(
                task_id=task_id,
                prompt=prompt,
                chosen=chosen_code,
                rejected=code,
                human_rating=5,
                judge_score=judge.score,
                correctness_score=judge.correctness_score,
                security_score=judge.security_score,
                complexity_rating=judge.complexity_rating,
                generation_method="rlaif_auto",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
            )

            cls._export_dpo_entry(entry)

            return {
                "routed_to": "rlaif_auto",
                "auto_exported": True,
                "generation_method": "rlaif_auto",
                "chosen_code": chosen_code,
                "message": "High-confidence trajectory automatically curated and exported to dpo_dataset.jsonl via RLAIF Data Flywheel!"
            }
        else:
            # Low/Medium Confidence HITL Queue Path
            suggested_code = cls.generate_rlaif_chosen(prompt, code, language, exec_log_summary)
            queue_item = {
                "queue_id": f"HITL-{task_id}-{int(datetime.datetime.now().timestamp())}",
                "task_id": task_id,
                "language": language,
                "prompt": prompt,
                "rejected_code": code,
                "suggested_chosen_code": suggested_code,
                "execution_trace": trace.model_dump(),
                "judge_result": judge.model_dump(),
                "combined_score": combined_score,
                "queued_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            HITL_QUEUE.append(queue_item)

            return {
                "routed_to": "hitl_queue",
                "auto_exported": False,
                "generation_method": "human_curated",
                "queue_id": queue_item["queue_id"],
                "message": "Low/Medium confidence or failing trajectory routed to Streamlit HITL Edge-Case Queue for human curation."
            }

    @staticmethod
    def _export_dpo_entry(entry: DPODatasetEntry) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        dpo_path = os.path.join(data_dir, "dpo_dataset.jsonl")

        with open(dpo_path, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")
        return dpo_path

    @staticmethod
    def get_hitl_queue() -> List[Dict[str, Any]]:
        return HITL_QUEUE

    @staticmethod
    def remove_from_queue(queue_id: str) -> bool:
        global HITL_QUEUE
        initial_len = len(HITL_QUEUE)
        HITL_QUEUE[:] = [item for item in HITL_QUEUE if item.get("queue_id") != queue_id]
        return len(HITL_QUEUE) < initial_len
