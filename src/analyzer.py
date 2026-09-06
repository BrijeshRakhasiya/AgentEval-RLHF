import os
import re
import sys
import tempfile
import subprocess
from typing import List


class StaticAnalyzer:
    """
    Pre-flight security static analysis scanner using bandit (Python), cppcheck (C++),
    and pattern inspection guards.
    """

    @staticmethod
    def analyze_python(code: str) -> List[str]:
        security_flags: List[str] = []

        # 1. High-risk static pattern matching guards
        patterns = [
            (r"\beval\s*\(", "SECURITY WARNING: Use of eval() detected (Code Injection Risk)"),
            (r"\bexec\s*\(", "SECURITY WARNING: Use of exec() detected (Dynamic Execution Risk)"),
            (r"os\.system\s*\(", "SECURITY WARNING: Use of os.system() detected (Shell Command Injection Risk)"),
            (r"subprocess\.(Popen|call|run)\s*\(.*shell\s*=\s*True", "SECURITY WARNING: Subprocess invoked with shell=True"),
            (r"__import__\s*\(", "SECURITY WARNING: Dynamic __import__() detected"),
            (r"shutil\.rmtree", "SECURITY WARNING: Recursive file deletion (rmtree) detected"),
        ]

        for pattern, warning in patterns:
            if re.search(pattern, code):
                security_flags.append(warning)

        # 2. Automated Bandit Security Scan
        tmp_file = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8")
        tmp_path = tmp_file.name
        try:
            tmp_file.write(code)
            tmp_file.flush()
            tmp_file.close()

            try:
                res = subprocess.run(
                    [sys.executable, "-m", "bandit", "-sk", "B101", "-r", tmp_path, "-f", "txt", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if res.stdout and ("Issue:" in res.stdout or "[B" in res.stdout):
                    for line in res.stdout.splitlines():
                        if "B101" in line:
                            continue  # Ignore assert statement flags in test scripts
                        if "Issue:" in line or "Severity:" in line or "[B" in line:
                            security_flags.append(f"BANDIT: {line.strip()}")
            except Exception:
                pass
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        return list(dict.fromkeys(security_flags))

    @staticmethod
    def analyze_cpp(code: str) -> List[str]:
        security_flags: List[str] = []

        # 1. High-risk C++ security pattern guards
        cpp_patterns = [
            (r"\bsystem\s*\(", "SECURITY WARNING: Use of C system() call detected"),
            (r"\bgets\s*\(", "SECURITY WARNING: Use of unsafe gets() function detected (Buffer Overflow Risk)"),
            (r"\bstrcpy\s*\(", "SECURITY WARNING: Use of unbounded strcpy() detected"),
            (r"\bdelete\s+\[\s*\]\s*delete", "SECURITY WARNING: Potential double free vulnerability detected"),
        ]

        for pattern, warning in cpp_patterns:
            if re.search(pattern, code):
                security_flags.append(warning)

        # 2. Cppcheck static scan (if cppcheck CLI tool is installed on host)
        tmp_file = tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False, encoding="utf-8")
        tmp_path = tmp_file.name
        try:
            tmp_file.write(code)
            tmp_file.flush()
            tmp_file.close()

            try:
                res = subprocess.run(
                    ["cppcheck", "--enable=warning,style", "--quiet", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if res.stderr:
                    for line in res.stderr.splitlines():
                        if line.strip():
                            security_flags.append(f"CPPCHECK: {line.strip()}")
            except FileNotFoundError:
                pass  # cppcheck is optional on local host
            except Exception:
                pass
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        return list(dict.fromkeys(security_flags))
