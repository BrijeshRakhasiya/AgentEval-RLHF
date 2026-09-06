import os
import sys
import time
import tempfile
import subprocess

try:
    from .models import ExecutionTrace
except ImportError:
    from models import ExecutionTrace


class PythonSandbox:
    @staticmethod
    def run(code: str, test_cases: str, timeout: float = 5.0) -> ExecutionTrace:
        """
        Executes Python code with unit tests in an isolated temporary process with timeout.
        """
        combined_source = f"{code.strip()}\n\n# --- Test Cases ---\n{test_cases.strip()}\n"

        tmp_file = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8")
        tmp_path = tmp_file.name
        try:
            tmp_file.write(combined_source)
            tmp_file.flush()
            tmp_file.close()

            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                passed = (result.returncode == 0)
                return ExecutionTrace(
                    passed=passed,
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                    exit_code=result.returncode,
                    execution_time=round(elapsed, 4)
                )
            except subprocess.TimeoutExpired as te:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=te.stdout or "",
                    stderr=f"Execution Timed Out (Limit: {timeout}s)",
                    exit_code=-1,
                    execution_time=round(elapsed, 4)
                )
            except Exception as e:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr=f"Execution Error: {str(e)}",
                    exit_code=-1,
                    execution_time=round(elapsed, 4)
                )
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


class CPPSandbox:
    @staticmethod
    def run(code: str, test_cases: str, timeout: float = 5.0) -> ExecutionTrace:
        """
        Compiles C++ code using g++ -std=c++17 and executes the compiled binary with timeout.
        """
        combined_source = f"{code.strip()}\n\n// --- Test Cases / Main ---\n{test_cases.strip()}\n"

        cpp_file = tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False, encoding="utf-8")
        cpp_path = cpp_file.name
        exe_path = cpp_path.replace(".cpp", ".exe") if sys.platform == "win32" else cpp_path + ".out"

        try:
            cpp_file.write(combined_source)
            cpp_file.flush()
            cpp_file.close()

            start_time = time.time()

            # Step 1: Compilation
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
                    execution_time=0.0
                )
            except subprocess.TimeoutExpired:
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr="Compilation Timed Out (Limit: 10.0s)",
                    exit_code=-1,
                    execution_time=round(time.time() - start_time, 4)
                )

            if compile_res.returncode != 0:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=compile_res.stdout or "",
                    stderr=f"Compilation Error:\n{compile_res.stderr or ''}",
                    exit_code=compile_res.returncode,
                    execution_time=round(elapsed, 4)
                )

            # Step 2: Binary Execution
            try:
                exec_res = subprocess.run(
                    [exe_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                passed = (exec_res.returncode == 0)
                return ExecutionTrace(
                    passed=passed,
                    stdout=exec_res.stdout or "",
                    stderr=exec_res.stderr or "",
                    exit_code=exec_res.returncode,
                    execution_time=round(elapsed, 4)
                )
            except subprocess.TimeoutExpired as te:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout=te.stdout or "",
                    stderr=f"Execution Timed Out (Limit: {timeout}s)",
                    exit_code=-1,
                    execution_time=round(elapsed, 4)
                )
            except Exception as e:
                elapsed = time.time() - start_time
                return ExecutionTrace(
                    passed=False,
                    stdout="",
                    stderr=f"Runtime Error: {str(e)}",
                    exit_code=-1,
                    execution_time=round(elapsed, 4)
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
