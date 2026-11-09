"""Run every program of Assignment 3 and save its output next to the source file."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROGRAMS = [
    ("Q1", "rainfall.py", "output.txt"),
    ("Q2", "complete_the_code.py", "complete_output.txt"),
    ("Q2", "bus_stops.py", "output.txt"),
    ("Q3", "complete_the_code.py", "complete_output.txt"),
    ("Q3", "complaints.py", "output.txt"),
    ("Q4", "complete_the_code.py", "complete_output.txt"),
    ("Q4", "electives.py", "output.txt"),
    ("Q5", "sensors.py", "output.txt"),
    ("Q6", "railway.py", "output.txt"),
    ("Q7", "contacts.py", "output.txt"),
]

for folder, script, out in PROGRAMS:
    print(f"Running {folder}/{script} ...", flush=True)
    res = subprocess.run([sys.executable, script], cwd=os.path.join(ROOT, folder),
                         capture_output=True, text=True)
    with open(os.path.join(ROOT, folder, out), "w", encoding="utf-8") as f:
        f.write(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(f"{folder}/{script} failed")
print("All programs ran successfully. Now run:  python build_report.py --github <your repository URL>")
