import os
import sys
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

try:
    from src.sandbox import PythonSandbox, CPPSandbox, RepoSandbox
    from src.judge import run_llm_judge
    from src.router import ConfidenceRouter
    from src.observability import ObservabilityTracer
except ImportError:
    from sandbox import PythonSandbox, CPPSandbox, RepoSandbox
    from judge import run_llm_judge
    from router import ConfidenceRouter
    from observability import ObservabilityTracer

app = typer.Typer(
    name="agent-eval",
    help="Enterprise AI Agent Evaluation Engine & RLHF Data Flywheel CLI",
    add_completion=False
)
console = Console(legacy_windows=False, force_terminal=True)


@app.command("run")
def run_evaluation(
    code_file: str = typer.Option(..., "--code-file", "-c", help="Path to generated agent code file"),
    test_file: str = typer.Option(..., "--test-file", "-t", help="Path to unit test assertion file"),
    prompt: str = typer.Option("Evaluate code correctness and security", "--prompt", "-p", help="Problem prompt / specification"),
    language: str = typer.Option("python", "--language", "-l", help="Target language: 'python' or 'cpp'"),
    task_id: str = typer.Option("CLI-TASK-001", "--task-id", help="Unique task identifier")
):
    """
    Executes zero-trust sandbox evaluation and LLM judge critique for code files.
    """
    console.print(Panel(f"[bold cyan]Running Agent Evaluation: Task {task_id}[/bold cyan]"))

    if not os.path.exists(code_file):
        console.print(f"[bold red]Error:[/bold red] Code file '{code_file}' not found.")
        raise typer.Exit(code=1)
    if not os.path.exists(test_file):
        console.print(f"[bold red]Error:[/bold red] Test file '{test_file}' not found.")
        raise typer.Exit(code=1)

    with open(code_file, "r", encoding="utf-8") as f:
        code = f.read()
    with open(test_file, "r", encoding="utf-8") as f:
        test_cases = f.read()

    console.print(f"[yellow]Executing {language.upper()} Sandbox...[/yellow]")
    if language.lower() == "python":
        trace = PythonSandbox.run(code, test_cases)
    else:
        trace = CPPSandbox.run(code, test_cases)

    status_str = "[bold green]PASSED[/bold green]" if trace.passed else "[bold red]FAILED[/bold red]"
    console.print(f"Sandbox Status: {status_str} (Time: {trace.execution_time}s | Exit: {trace.exit_code})")

    if trace.security_flags:
        console.print("[bold red]Security Warnings Detected:[/bold red]")
        for flag in trace.security_flags:
            console.print(f"  - {flag}")

    console.print("[yellow]Querying NIM LLM Judge Router...[/yellow]")
    exec_log = f"Status: {'PASSED' if trace.passed else 'FAILED'}\nStdout:\n{trace.stdout}\nStderr:\n{trace.stderr}"
    judge = run_llm_judge(prompt, code, exec_log)

    combined_score = round((0.4 * (5.0 if trace.passed else 1.0)) + (0.3 * judge.correctness_score) + (0.3 * judge.security_score), 2)

    routing_info = ConfidenceRouter.evaluate_and_route(
        task_id=task_id,
        prompt=prompt,
        code=code,
        language=language,
        trace=trace,
        judge=judge,
        combined_score=combined_score
    )

    ObservabilityTracer.log_evaluation_trace(
        task_id=task_id,
        language=language,
        prompt=prompt,
        code=code,
        trace_data=trace.model_dump(),
        judge_data=judge.model_dump(),
        combined_score=combined_score,
        routing_info=routing_info
    )

    # Print Formatted Evaluation Results Table
    table = Table(title="Evaluation Metric Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Combined Score", f"{combined_score} / 5.0")
    table.add_row("Overall Judge Score", f"{judge.score} / 5")
    table.add_row("Correctness Score", f"{judge.correctness_score} / 5")
    table.add_row("Security Score", f"{judge.security_score} / 5")
    table.add_row("Complexity Rating", judge.complexity_rating)
    table.add_row("Edge Case Quality", judge.edge_case_handling)
    table.add_row("RLAIF Flywheel Routing", routing_info.get("routed_to", "unknown"))

    console.print(table)
    console.print(Panel(f"[italic]{judge.reasoning}[/italic]", title="LLM Judge Critique"))


@app.command("repo")
def run_repo_evaluation(
    repo: str = typer.Option(..., "--repo", "-r", help="Git repo target path or URL"),
    patch: str = typer.Option(..., "--patch", "-p", help="Path to code patch file"),
    test_command: str = typer.Option("pytest", "--test-cmd", "-t", help="Native repository test command")
):
    """
    Executes SWE-bench style Repo-Level patch evaluation.
    """
    console.print(Panel(f"[bold cyan]Running Repo-Level Evaluation on '{repo}'[/bold cyan]"))

    if not os.path.exists(patch):
        console.print(f"[bold red]Error:[/bold red] Patch file '{patch}' not found.")
        raise typer.Exit(code=1)

    with open(patch, "r", encoding="utf-8") as f:
        patch_code = f.read()

    console.print(f"[yellow]Cloning/Preparing Repo & Running '{test_command}' in Isolated Sandbox...[/yellow]")
    trace = RepoSandbox.run_patch(repo_target=repo, patch_code=patch_code, test_command=test_command)

    status_str = "[bold green]PASSED[/bold green]" if trace.passed else "[bold red]FAILED[/bold red]"
    console.print(f"Repo Sandbox Status: {status_str} (Time: {trace.execution_time}s | Exit: {trace.exit_code})")

    if trace.stdout:
        console.print(Panel(trace.stdout[:500], title="Test Standard Output"))
    if trace.stderr:
        console.print(Panel(trace.stderr[:500], title="Test Standard Error"))


@app.command("stats")
def show_stats():
    """
    Displays DPO dataset statistics and RLAIF flywheel telemetry metrics.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dpo_path = os.path.join(base_dir, "data", "dpo_dataset.jsonl")
    telemetry_path = os.path.join(base_dir, "data", "telemetry_traces.jsonl")

    dpo_count = 0
    rlaif_count = 0
    human_count = 0

    if os.path.exists(dpo_path):
        with open(dpo_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    dpo_count += 1
                    try:
                        data = json.loads(line)
                        if data.get("generation_method") == "rlaif_auto":
                            rlaif_count += 1
                        else:
                            human_count += 1
                    except Exception:
                        pass

    telemetry_count = 0
    if os.path.exists(telemetry_path):
        with open(telemetry_path, "r", encoding="utf-8") as f:
            telemetry_count = sum(1 for line in f if line.strip())

    table = Table(title="AgentEval-RLHF Telemetry & Dataset Statistics", show_header=True, header_style="bold blue")
    table.add_column("Category", style="cyan")
    table.add_column("Count / Value", style="bold green")

    table.add_row("Total Exported DPO Pairs", str(dpo_count))
    table.add_row("RLAIF Auto-Curated Pairs", str(rlaif_count))
    table.add_row("Human Expert Curated Pairs", str(human_count))
    table.add_row("Logged Telemetry Traces", str(telemetry_count))
    table.add_row("DPO Dataset Path", os.path.abspath(dpo_path))

    console.print(table)


if __name__ == "__main__":
    app()
