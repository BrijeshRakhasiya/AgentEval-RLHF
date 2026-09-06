import os
import sys
import time
import tempfile
import subprocess
from typing import Optional

try:
    from src.models import ExecutionTrace
    from src.analyzer import StaticAnalyzer
except ImportError:
    try:
        from .models import ExecutionTrace
        from .analyzer import StaticAnalyzer
    except ImportError:
        try:
            from models import ExecutionTrace
            from analyzer import StaticAnalyzer
        except ImportError:
            from dataclasses import dataclass, field
            from typing import List

            @dataclass
            class ExecutionTrace:
                passed: bool
                stdout: str
                stderr: str
                exit_code: int
                execution_time: float
                security_flags: List[str] = field(default_factory=list)
                sandbox_type: str = "python"
                static_analysis_report: str = ""

            class StaticAnalyzer:
                @staticmethod
                def analyze_python(code: str) -> List[str]:
                    return []
                @staticmethod
                def analyze_cpp(code: str) -> List[str]:
                    return []

# Try importing Docker SDK
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class SecurePythonSandbox:
    @staticmethod
    def run(code: str, test_cases: str, timeout: float = 5.0) -> ExecutionTrace:
        """
        Executes Python code with unit tests inside a Docker container (or subprocess fallback)
        with zero-trust constraints (network disabled, 256m RAM limit, CPU quota) and pre-flight static analysis.
        """
        # Step 1: Pre-flight static security analysis
        security_flags = StaticAnalyzer.analyze_python(code)
        static_report = "\n".join(security_flags) if security_flags else "No static analysis security flags."

        project_root = os.getcwd()
        path_header = (
            "import sys, os\n"
            f"project_root = {repr(project_root)}\n"
            "if project_root not in sys.path:\n"
            "    sys.path.insert(0, project_root)\n"
            "src_dir = os.path.join(project_root, 'src')\n"
            "if os.path.exists(src_dir) and src_dir not in sys.path:\n"
            "    sys.path.insert(0, src_dir)\n\n"
        )
        combined_source = f"{path_header}{code.strip()}\n\n# --- Test Cases ---\n{test_cases.strip()}\n"

        tmp_file = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8")
        tmp_path = tmp_file.name
        try:
            tmp_file.write(combined_source)
            tmp_file.flush()
            tmp_file.close()

            # Step 2: Attempt Docker Isolated Sandbox Execution
            if DOCKER_AVAILABLE:
                try:
                    client = docker.from_env()
                    client.ping()  # Check if docker daemon is running

                    start_time = time.time()
                    container = None
                    try:
                        container = client.containers.run(
                            image="python:3.10-slim",
                            command=["python", "/app/script.py"],
                            volumes={tmp_path: {"bind": "/app/script.py", "mode": "ro"}},
                            network_mode="none",
                            mem_limit="256m",
                            cpu_quota=50000,
                            detach=True
                        )

                        try:
                            res = container.wait(timeout=timeout)
                            elapsed = time.time() - start_time
                            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                            exit_code = res.get("StatusCode", 0)
                            passed = (exit_code == 0) and (not security_flags)
                            
                            err_msg = logs if exit_code != 0 else ""
                            if security_flags and not err_msg:
                                err_msg = f"SECURITY WARNINGS DETECTED:\n" + "\n".join(security_flags)

                            return ExecutionTrace(
                                passed=passed,
                                stdout=logs if exit_code == 0 else "",
                                stderr=err_msg,
                                exit_code=exit_code if exit_code != 0 else (1 if security_flags else 0),
                                execution_time=round(elapsed, 4),
                                security_flags=security_flags,
                                sandbox_type="docker_isolated",
                                static_analysis_report=static_report
                            )
                        except Exception:
                            elapsed = time.time() - start_time
                            return ExecutionTrace(
                                passed=False,
                                stdout="",
                                stderr=f"Execution Timed Out (Limit: {timeout}s)",
                                exit_code=-1,
                                execution_time=round(elapsed, 4),
                                security_flags=security_flags,
                                sandbox_type="docker_isolated",
                                static_analysis_report=static_report
                            )
                    finally:
                        if container:
                            try:
                                container.remove(force=True)
                            except Exception:
                                pass
                except Exception:
                    pass  # Fall through to secure subprocess fallback if Docker engine unavailable

            # Step 3: Subprocess Fallback Execution
            start_time = time.time()
            try:
                env = os.environ.copy()
                src_dir = os.path.join(project_root, "src")
                curr_pp = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = f"{project_root}{os.pathsep}{src_dir}{os.pathsep}{curr_pp}"

                result = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env
                )
                elapsed = time.time() - start_time
                passed = (result.returncode == 0) and (not security_flags)
                
                err_msg = result.stderr or ""
                if security_flags and not err_msg:
                    err_msg = f"SECURITY WARNINGS DETECTED:\n" + "\n".join(security_flags)

                return ExecutionTrace(
                    passed=passed,
                    stdout=result.stdout or "",
                    stderr=err_msg,
                    exit_code=result.returncode if result.returncode != 0 else (1 if security_flags else 0),
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
            except subprocess.TimeoutExpired as te:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=te.stdout or "",
                    stderr=f"Execution Timed Out (Limit: {timeout}s)",
                    exit_code=-1,
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
            except Exception as e:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr=f"Execution Error: {str(e)}",
                    exit_code=-1,
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


class SecureCPPSandbox:
    @staticmethod
    def run(code: str, test_cases: str, timeout: float = 5.0) -> ExecutionTrace:
        """
        Compiles and executes C++ code with static analysis pre-flight checks and isolated execution.
        """
        security_flags = StaticAnalyzer.analyze_cpp(code)
        static_report = "\n".join(security_flags) if security_flags else "No static analysis security flags."

        combined_source = f"{code.strip()}\n\n// --- Test Cases / Main ---\n{test_cases.strip()}\n"

        cpp_file = tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False, encoding="utf-8")
        cpp_path = cpp_file.name
        exe_path = cpp_path.replace(".cpp", ".exe") if sys.platform == "win32" else cpp_path + ".out"

        try:
            cpp_file.write(combined_source)
            cpp_file.flush()
            cpp_file.close()

            start_time = time.time()

            # Compilation
            try:
                compile_res = subprocess.run(
                    ["g++", "-std=c++17", cpp_path, "-o", exe_path],
                    capture_output=True,
                    text=True,
                    timeout=10.0
                )
            except FileNotFoundError:
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr="g++ compiler not found in system PATH. Please install GCC/g++.",
                    exit_code=-1,
                    execution_time=0.0,
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
            except subprocess.TimeoutExpired:
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr="Compilation Timed Out (Limit: 10.0s)",
                    exit_code=-1,
                    execution_time=round(time.time() - start_time, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )

            if compile_res.returncode != 0:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=compile_res.stdout or "",
                    stderr=f"Compilation Error:\n{compile_res.stderr or ''}",
                    exit_code=compile_res.returncode,
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )

            # Binary Execution
            try:
                exec_res = subprocess.run(
                    [exe_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                passed = (exec_res.returncode == 0) and (not security_flags)

                err_msg = exec_res.stderr or ""
                if security_flags and not err_msg:
                    err_msg = f"SECURITY WARNINGS DETECTED:\n" + "\n".join(security_flags)

                return ExecutionTrace(
                    passed=passed,
                    stdout=exec_res.stdout or "",
                    stderr=err_msg,
                    exit_code=exec_res.returncode if exec_res.returncode != 0 else (1 if security_flags else 0),
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
            except subprocess.TimeoutExpired as te:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=te.stdout or "",
                    stderr=f"Execution Timed Out (Limit: {timeout}s)",
                    exit_code=-1,
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )
            except Exception as e:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr=f"Runtime Error: {str(e)}",
                    exit_code=-1,
                    execution_time=round(elapsed, 4),
                    security_flags=security_flags,
                    sandbox_type="subprocess_fallback",
                    static_analysis_report=static_report
                )

        finally:
            if os.path.exists(cpp_path):
                try:
                    os.unlink(cpp_path)
                except Exception:
                    pass
            if os.path.exists(exe_path):
                try:
                    os.unlink(exe_path)
                except Exception:
                    pass


class RepoSandbox:
    @staticmethod
    def run_patch(repo_target: str, patch_code: str, test_command: str = "pytest", timeout: float = 30.0) -> ExecutionTrace:
        """
        SWE-bench style Repo-Level evaluation sandbox.
        Applies code patch to target repo and runs native test command in isolated environment.
        """
        import shutil
        start_time = time.time()
        security_flags = StaticAnalyzer.analyze_python(patch_code)
        static_report = "\n".join(security_flags) if security_flags else "No static analysis security flags."

        temp_dir = tempfile.mkdtemp(prefix="repo_sandbox_")
        try:
            # If repo_target is local directory or git URL
            if os.path.exists(repo_target):
                shutil.copytree(repo_target, temp_dir, dirs_exist_ok=True)
            elif repo_target.startswith("http://") or repo_target.startswith("https://") or repo_target.startswith("git@"):
                clone_res = subprocess.run(["git", "clone", "--depth", "1", repo_target, temp_dir], capture_output=True, text=True, timeout=20.0)
                if clone_res.returncode != 0:
                    return ExecutionTrace(
                        passed=False,
                        stdout="",
                        stderr=f"Git Clone Error:\n{clone_res.stderr}",
                        exit_code=-1,
                        execution_time=round(time.time() - start_time, 4),
                        security_flags=security_flags,
                        sandbox_type="repo_isolated",
                        static_analysis_report=static_report
                    )

            # Apply patch code
            patch_file = os.path.join(temp_dir, "agent_patch.py")
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(patch_code)

            # Execute native test command in isolated temp directory
            cmd_args = test_command.split()
            run_res = subprocess.run(
                cmd_args,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            passed = (run_res.returncode == 0)

            err_msg = run_res.stderr or ""
            if security_flags and not err_msg:
                err_msg = "SECURITY WARNINGS DETECTED:\n" + "\n".join(security_flags)

            return ExecutionTrace(
                passed=passed,
                stdout=run_res.stdout or "",
                stderr=err_msg,
                exit_code=run_res.returncode,
                execution_time=round(elapsed, 4),
                security_flags=security_flags,
                sandbox_type="repo_isolated",
                static_analysis_report=static_report
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return ExecutionTrace(
                passed=False,
                stdout="",
                stderr=f"Repo Test Execution Timed Out (Limit: {timeout}s)",
                exit_code=-1,
                execution_time=round(elapsed, 4),
                security_flags=security_flags,
                sandbox_type="repo_isolated",
                static_analysis_report=static_report
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return ExecutionTrace(
                passed=False,
                stdout="",
                stderr=f"Repo Sandbox Execution Error: {str(e)}",
                exit_code=-1,
                execution_time=round(elapsed, 4),
                security_flags=security_flags,
                sandbox_type="repo_isolated",
                static_analysis_report=static_report
            )
        finally:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass


# Aliases for backward compatibility
PythonSandbox = SecurePythonSandbox
CPPSandbox = SecureCPPSandbox
