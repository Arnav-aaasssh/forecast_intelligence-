import os
import glob
import time
import json
from pathlib import Path

def find_todos():
    print("--- TODOs, FIXMEs, and Placeholders ---")
    root_dir = "d:/project_1 imp docs/Forecast review"
    extensions = [".py"]
    keywords = ["TODO", "FIXME", "placeholder", "dummy", "pass"]
    
    for ext in extensions:
        for filepath in Path(root_dir).rglob(f"*{ext}"):
            if ".venv" in str(filepath) or "__pycache__" in str(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        for kw in keywords:
                            if kw.lower() in line.lower():
                                print(f"{filepath.relative_to(root_dir)}:{i+1} : {line.strip()}")
            except Exception:
                pass

def check_artifacts():
    print("\n--- ARTIFACTS VERIFICATION ---")
    output_dir = Path("d:/project_1 imp docs/Forecast review/reports/output")
    expected_files = [
        "forecast_review.html",
        "forecast_review.json",
        "executive_summary.md",
        "manager_summary.md",
        "email_summary.md",
        "teams_summary.json"
    ]
    
    for fname in expected_files:
        fpath = output_dir / fname
        if fpath.exists():
            stat = fpath.stat()
            size = stat.st_size
            mtime = time.ctime(stat.st_mtime)
            print(f"[FOUND] {fname} - Size: {size} bytes - Modified: {mtime}")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read(500)
                print(f"  Content Preview: {content[:100].strip()}...")
        else:
            print(f"[MISSING] {fname}")

if __name__ == "__main__":
    find_todos()
    check_artifacts()
