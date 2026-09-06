import os
import sys
from fastapi.testclient import TestClient

# Ensure root and src directory are on Python path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.models import TaskRequest, DPODatasetEntry
from src.sandbox import PythonSandbox, CPPSandbox
from src.main import app

client = TestClient(app)

def test_python_sandbox():
    print("Testing PythonSandbox...")
    code = "def add(a, b):\n    return a + b\n"
    tests = "assert add(2, 3) == 5\nassert add(-1, 1) == 0\nprint('Passed!')"
    trace = PythonSandbox.run(code, tests)
    assert trace.passed is True
    assert "Passed!" in trace.stdout
    print("PythonSandbox PASSED!")

def test_cpp_sandbox():
    print("Testing CPPSandbox...")
    code = "#include <iostream>\nint mult(int a, int b) { return a * b; }\n"
    tests = "int main() { if (mult(3, 4) == 12) std::cout << \"CPP Passed!\"; return 0; }\n"
    trace = CPPSandbox.run(code, tests)
    if "g++ compiler not found" in trace.stderr:
        print("CPPSandbox SKIPPED (g++ not installed on local host)")
    else:
        assert trace.passed is True
        assert "CPP Passed!" in trace.stdout
        print("CPPSandbox PASSED!")

def test_dpo_export():
    print("Testing DPO Export Endpoint...")
    payload = {
        "task_id": "TEST-DPO-001",
        "prompt": "Test prompt",
        "chosen": "def foo(): pass",
        "rejected": "def foo(): fail",
        "human_rating": 5,
        "judge_score": 4,
        "timestamp": "2026-09-06T12:00:00Z"
    }
    response = client.post("/export/dpo", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    print("DPO Export Endpoint PASSED!")

if __name__ == "__main__":
    test_python_sandbox()
    test_cpp_sandbox()
    test_dpo_export()
    print("ALL UNIT TESTS COMPLETED SUCCESSFULLY!")
