#!/Users/diyao/Desktop/files/amazon-env/bin/python
# ↑↑↑ This shebang line uses your venv python directly — no activation needed ever

import subprocess
import sys
from datetime import datetime

# ←←←←←←←←←←←←←←← EDIT ONLY THESE TWO LINES ANYTIME ←←←←←←←←←←←←←←←
URL = "https://www.amazon.ca/dp/B0DGJJKWW7"
PHONE = "+17786289926"
# →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→

# Run the real checker
result = subprocess.run(
    [
        sys.executable,  # uses the same python (the shebang one)
        "/Users/diyao/Desktop/files/amazon_checker.py",
        URL,
        "--phone",
        PHONE,
    ],
    capture_output=True,
    text=True,
)

# Simple log inside your logs folder
log_dir = "/Users/diyao/Desktop/files/logs"
with open(f"{log_dir}/wrapper_runs.log", "a") as f:
    f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | Exit code: {result.returncode}\n")

# Send everything to launchd logs too
print(f"{datetime.now():%Y-%m-%d %H:%M:%S} | Checking {URL}")
print(result.stdout)
if result.stderr:
    print("ERROR:", result.stderr, file=sys.stderr)
