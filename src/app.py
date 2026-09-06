import datetime
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AgentEval-RLHF | HITL Curation Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366F1, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #9CA3AF;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ AgentEval-RLHF Curation Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Language Agent Sandbox Evaluation & Human-in-the-Loop DPO Dataset Exporter</div>', unsafe_allow_html=True)

# 5 High-Reasoning Benchmark Preloads
BENCHMARKS = {
    "Custom / Manual Input": None,
    "Python: 1. LIS via Patience Sorting (O(N log N))": {
        "lang": "Python",
        "task_id": "REASONING-PY-001",
        "prompt": "Write a Python function `length_of_lis(nums: list[int]) -> int` that returns the length of the longest strictly increasing subsequence in O(N log N) time complexity using binary search (patience sorting).",
        "code": """import bisect

def length_of_lis(nums: list[int]) -> int:
    if not nums:
        return 0
    tails = []
    for num in nums:
        idx = bisect.bisect_left(tails, num)
        if idx == len(tails):
            tails.append(num)
        else:
            tails[idx] = num
    return len(tails)""",
        "tests": """assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4
assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4
assert length_of_lis([7, 7, 7, 7, 7]) == 1
print("All LIS O(N log N) tests passed!")"""
    },
    "Python: 2. Topological Sort (Subtle Cycle Bug)": {
        "lang": "Python",
        "task_id": "REASONING-PY-002",
        "prompt": "Write a Python function `can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool` that determines if a student can finish all courses given prerequisite pairs using Kahn's algorithm (indegree BFS).",
        "code": """from collections import deque

def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    indegree = [0] * num_courses
    adj = [[] for _ in range(num_courses)]
    for dest, src in prerequisites:
        adj[src].append(dest)
        indegree[dest] += 1

    queue = deque([i for i in range(num_courses) if indegree[i] == 0])

    while queue:
        curr = queue.popleft()
        for neighbor in adj[curr]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    return True # BUG: Forgot to check if total processed nodes == num_courses!""",
        "tests": """assert can_finish(2, [[1, 0]]) == True
assert can_finish(2, [[1, 0], [0, 1]]) == False
print("All Topological Sort tests passed!")"""
    },
    "Python: 3. LRU Cache Design (O(1) Pass)": {
        "lang": "Python",
        "task_id": "REASONING-PY-003",
        "prompt": "Design an LRUCache class in Python with `get(key: int) -> int` and `put(key: int, value: int)` operating in O(1) time complexity using collections.OrderedDict.",
        "code": """from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)""",
        "tests": """lru = LRUCache(2)
lru.put(1, 1)
lru.put(2, 2)
assert lru.get(1) == 1
lru.put(3, 3) # evicts key 2
assert lru.get(2) == -1
lru.put(4, 4) # evicts key 1
assert lru.get(1) == -1
assert lru.get(3) == 3
assert lru.get(4) == 4
print("All LRU Cache tests passed!")"""
    },
    "C++: 4. Fast Exponentiation (O(log N) Pass)": {
        "lang": "C++",
        "task_id": "REASONING-CPP-004",
        "prompt": "Write a C++ function `double myPow(double x, int n)` calculating x raised to the power n in O(log n) time handling negative powers and overflow safely.",
        "code": """#include <iostream>
#include <cassert>
#include <cmath>

double myPow(double x, int n) {
    long long N = n;
    if (N < 0) {
        x = 1.0 / x;
        N = -N;
    }
    double ans = 1.0;
    double current_product = x;
    for (long long i = N; i > 0; i /= 2) {
        if (i % 2 == 1) {
            ans = ans * current_product;
        }
        current_product = current_product * current_product;
    }
    return ans;
}""",
        "tests": """int main() {
    assert(std::abs(myPow(2.0, 10) - 1024.0) < 1e-5);
    assert(std::abs(myPow(2.1, 3) - 9.261) < 1e-5);
    assert(std::abs(myPow(2.0, -2) - 0.25) < 1e-5);
    std::cout << "All C++ Fast Exponentiation tests passed!" << std::endl;
    return 0;
}"""
    },
    "C++: 5. Binary Search Bounds (Off-By-One Bug)": {
        "lang": "C++",
        "task_id": "REASONING-CPP-005",
        "prompt": "Write a C++ function `int searchRangeFirst(const std::vector<int>& nums, int target)` returning the first index of target in sorted array or -1 if not found.",
        "code": """#include <vector>
#include <iostream>
#include <cassert>

int searchRangeFirst(const std::vector<int>& nums, int target) {
    int low = 0, high = nums.size(); // BUG: high should be nums.size() - 1 or condition loop check mismatch
    int ans = -1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (mid >= 0 && mid < nums.size() && nums[mid] == target) {
            ans = mid;
            high = mid - 1;
        } else if (mid >= 0 && mid < nums.size() && nums[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return ans;
}""",
        "tests": """int main() {
    std::vector<int> nums = {5, 7, 7, 8, 8, 10};
    assert(searchRangeFirst(nums, 8) == 3);
    assert(searchRangeFirst(nums, 6) == -1);
    std::cout << "All Binary Search Range tests passed!" << std::endl;
    return 0;
}"""
    }
}

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings & Benchmarks")

    preset = st.selectbox("Load Reasoning Benchmark Task", list(BENCHMARKS.keys()))

    if preset and BENCHMARKS[preset]:
        data = BENCHMARKS[preset]
        st.session_state["task_id"] = data["task_id"]
        st.session_state["prompt"] = data["prompt"]
        st.session_state["code"] = data["code"]
        st.session_state["tests"] = data["tests"]
        st.session_state["language"] = data["lang"]
        if "eval_result" in st.session_state:
            del st.session_state["eval_result"]

    language = st.selectbox(
        "Language / Sandbox Target",
        ["Python", "C++"],
        index=0 if st.session_state.get("language") != "C++" else 1
    )
    backend_url = st.text_input("Backend API Gateway URL", value=BACKEND_URL)

    st.divider()
    st.subheader("🌐 System Connectivity")
    try:
        r = requests.get(f"{backend_url}/", timeout=2.0)
        if r.status_code == 200:
            st.success(f"Backend API Online (`{r.json().get('service')}`)")
        else:
            st.error(f"Backend API HTTP {r.status_code}")
    except Exception:
        st.warning(f"Backend API Unreachable at {backend_url}")

# Fallback defaults
if language == "Python":
    default_task_id = "TASK-PY-001"
    default_prompt = "Write a Python function `is_palindrome(s: str) -> bool` that returns True if string s is a palindrome, ignoring non-alphanumeric characters and case."
    default_code = """def is_palindrome(s: str) -> bool:
    cleaned = ''.join(ch.lower() for ch in s if ch.isalnum())
    return cleaned == cleaned[::-1]"""
    default_tests = """assert is_palindrome("A man, a plan, a canal: Panama") == True
assert is_palindrome("race a car") == False
assert is_palindrome("") == True
print("All Python tests passed successfully!")"""
else:
    default_task_id = "TASK-CPP-001"
    default_prompt = "Write a C++ function `int maxSubArray(const std::vector<int>& nums)` implementing Kadane's algorithm to return the maximum subarray sum."
    default_code = """#include <vector>
#include <algorithm>
#include <iostream>
#include <cassert>

int maxSubArray(const std::vector<int>& nums) {
    int max_so_far = nums[0];
    int curr_max = nums[0];
    for (size_t i = 1; i < nums.size(); ++i) {
        curr_max = std::max(nums[i], curr_max + nums[i]);
        max_so_far = std::max(max_so_far, curr_max);
    }
    return max_so_far;
}"""
    default_tests = """int main() {
    std::vector<int> n1 = {-2,1,-3,4,-1,2,1,-5,4};
    assert(maxSubArray(n1) == 6);

    std::vector<int> n2 = {1};
    assert(maxSubArray(n2) == 1);

    std::cout << "All C++ tests passed successfully!" << std::endl;
    return 0;
}"""

st.subheader("📝 Task Definition & Submission")
col_input1, col_input2 = st.columns([1, 2])

with col_input1:
    task_id = st.text_input("Task ID", value=st.session_state.get("task_id", default_task_id))
    prompt = st.text_area("Problem Prompt", value=st.session_state.get("prompt", default_prompt), height=140)

with col_input2:
    code = st.text_area("Generated Agent Code", value=st.session_state.get("code", default_code), height=140)
    test_cases = st.text_area("Test Cases / Main Assertions", value=st.session_state.get("tests", default_tests), height=120)

run_eval = st.button("🚀 Run Dual Evaluation (Sandbox + LLM Judge)", type="primary", use_container_width=True)

if run_eval:
    endpoint = f"{backend_url}/evaluate/{'python' if language == 'Python' else 'cpp'}"
    payload = {
        "task_id": task_id,
        "language": language.lower(),
        "prompt": prompt,
        "code": code,
        "test_cases": test_cases
    }
    with st.spinner(f"Executing {language} Sandbox and querying NVIDIA NIM LLM Judge..."):
        try:
            res = requests.post(endpoint, json=payload, timeout=60.0)
            if res.status_code == 200:
                st.session_state.eval_result = res.json()
                st.session_state.active_task_id = task_id
                st.session_state.active_prompt = prompt
                st.session_state.active_raw_code = code
                st.session_state.edited_code_area = code
                st.success("Evaluation completed successfully!")
            else:
                st.error(f"Evaluation request failed (HTTP {res.status_code}): {res.text}")
        except Exception as err:
            st.error(f"Failed to connect to backend: {str(err)}")

st.divider()

# Dashboard Output & HITL Curation
if "eval_result" in st.session_state:
    result = st.session_state.eval_result
    trace = result["execution_trace"]
    judge = result["judge_result"]
    combined = result["combined_score"]

    st.subheader("📊 Evaluation Dashboard & HITL Curation")
    col_left, col_right = st.columns([1, 1], gap="medium")

    # LEFT COLUMN: Raw Execution & Automated Critique
    with col_left:
        st.markdown("### 🤖 Automated Dual Evaluation")

        # Metric summary row
        m1, m2, m3 = st.columns(3)
        with m1:
            if trace["passed"]:
                st.metric("Sandbox Status", "PASSED ✅")
            else:
                st.metric("Sandbox Status", "FAILED ❌")
        with m2:
            st.metric("LLM Judge Rating", f"{judge['score']} / 5 ⭐")
        with m3:
            st.metric("Combined Score", f"{combined} / 5.0")

        st.markdown("**Sandbox Output Logs**")
        if trace["stdout"]:
            st.caption("Standard Output (stdout):")
            st.code(trace["stdout"], language="text")
        if trace["stderr"]:
            st.caption("Standard Error (stderr):")
            st.code(trace["stderr"], language="text")

        st.caption(f"Execution Runtime: `{trace['execution_time']}s` | Exit Code: `{trace['exit_code']}`")

        st.markdown("**LLM Judge Reasoning & Qualitative Critique**")
        st.info(judge["reasoning"])

    # RIGHT COLUMN: Human Curation & DPO Export
    with col_right:
        st.markdown("### 🧑‍💻 Human Expert Curation (RLHF)")
        st.caption("Edit the code below to produce the optimal 'Chosen' completion for Direct Preference Optimization (DPO).")

        edited_code = st.text_area(
            "Optimal Code (Chosen Candidate)",
            value=st.session_state.get("edited_code_area", code),
            height=260
        )

        human_rating = st.slider("Human Expert Rating (1 - 5 Stars)", min_value=1, max_value=5, value=int(judge["score"]))

        if st.button("💾 Export DPO Pair to JSONL", type="primary", use_container_width=True):
            dpo_endpoint = f"{backend_url}/export/dpo"
            dpo_payload = {
                "task_id": st.session_state.get("active_task_id", task_id),
                "prompt": st.session_state.get("active_prompt", prompt),
                "chosen": edited_code,
                "rejected": st.session_state.get("active_raw_code", code),
                "human_rating": human_rating,
                "judge_score": int(judge["score"]),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            try:
                export_res = requests.post(dpo_endpoint, json=dpo_payload, timeout=5.0)
                if export_res.status_code == 200:
                    data = export_res.json()
                    st.success(f"Successfully exported DPO pair for '{dpo_payload['task_id']}' to `data/dpo_dataset.jsonl`!")
                    st.json(data)
                else:
                    st.error(f"Export failed: {export_res.text}")
            except Exception as e:
                st.error(f"Failed to submit DPO entry: {str(e)}")
