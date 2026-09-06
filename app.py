import sys
import os
import runpy

# Ensure project root and src directory are in Python path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "src"))

# Execute src/app.py inside Streamlit's __main__ execution context
src_app_path = os.path.join(base_dir, "src", "app.py")
runpy.run_path(src_app_path, run_name="__main__")
