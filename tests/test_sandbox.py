import os
import sys
import pytest

# Ensure workspace root and src directory are in Python path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.analyzer import StaticAnalyzer
from src.sandbox import SecurePythonSandbox, SecureCPPSandbox


def test_static_analyzer_python():
    print("Testing StaticAnalyzer.analyze_python...")
    clean_code = "def add(a, b):\n    return a + b\n"
    malicious_code = """
import os
def dangerous_func(x):
    eval("x + 1")
    os.system("rm -rf /")
    return x
"""
    clean_flags = StaticAnalyzer.analyze_python(clean_code)
    assert len(clean_flags) == 0

    malicious_flags = StaticAnalyzer.analyze_python(malicious_code)
    assert len(malicious_flags) >= 2
    assert any("eval()" in flag for flag in malicious_flags)
    assert any("os.system()" in flag for flag in malicious_flags)
    print("StaticAnalyzer Python test PASSED!")


def test_static_analyzer_cpp():
    print("Testing StaticAnalyzer.analyze_cpp...")
    clean_cpp = "int add(int a, int b) { return a + b; }"
    dangerous_cpp = """
#include <cstdlib>
int bad_func() {
    system("rm -rf /");
    return 0;
}
"""
    clean_flags = StaticAnalyzer.analyze_cpp(clean_cpp)
    assert len(clean_flags) == 0

    dangerous_flags = StaticAnalyzer.analyze_cpp(dangerous_cpp)
    assert len(dangerous_flags) >= 1
    assert any("system()" in flag for flag in dangerous_flags)
    print("StaticAnalyzer C++ test PASSED!")


def test_secure_python_sandbox_clean():
    print("Testing SecurePythonSandbox with clean code...")
    code = "def multiply(a, b):\n    return a * b\n"
    tests = "assert multiply(3, 4) == 12\nprint('Clean execution success')"
    trace = SecurePythonSandbox.run(code, tests)
    assert trace.passed is True
    assert "Clean execution success" in trace.stdout
    assert trace.execution_time > 0
    assert trace.sandbox_type in ["docker_isolated", "subprocess_fallback"]
    print("SecurePythonSandbox Clean execution PASSED!")


def test_secure_python_sandbox_malicious_containment():
    print("Testing SecurePythonSandbox with malicious code containment...")
    code = """
import os
def malicious():
    eval("1 + 1")
    os.system("echo Malicious Command Trapped")
    return True
"""
    tests = "assert malicious() == True"
    trace = SecurePythonSandbox.run(code, tests)
    assert len(trace.security_flags) >= 1
    assert trace.static_analysis_report != ""
    print("SecurePythonSandbox Malicious containment PASSED!")


def test_secure_python_sandbox_timeout():
    print("Testing SecurePythonSandbox timeout guard...")
    code = """
import time
def infinite_loop():
    while True:
        time.sleep(0.1)
"""
    tests = "infinite_loop()"
    trace = SecurePythonSandbox.run(code, tests, timeout=2.0)
    assert trace.passed is False
    assert "Timed Out" in trace.stderr
    print("SecurePythonSandbox Timeout guard PASSED!")


if __name__ == "__main__":
    test_static_analyzer_python()
    test_static_analyzer_cpp()
    test_secure_python_sandbox_clean()
    test_secure_python_sandbox_malicious_containment()
    test_secure_python_sandbox_timeout()
    print("ALL PHASE 1 SANDBOX TESTS PASSED SUCCESSFULLY!")
