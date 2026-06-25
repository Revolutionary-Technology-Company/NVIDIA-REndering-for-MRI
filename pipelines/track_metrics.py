#!/usr/bin/env python3
"""
Revolutionary Technology Company - MRI Pipeline Metrics Logger
Records processing throughput, data size, and VRAM/CPU runtime profiles 
into an auditable metrics.json framework for hospital IT compliance.
"""

import sys
import os
import json
import time
from datetime import datetime

METRICS_FILE = "/workspace/pipeline/metrics.json"

def log_audit_metrics(status: str, total_files: int, duration: float, error_msg: str = ""):
    """Appends structural execution history parameters to the auditing system matrix."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Calculate throughput metrics (Slices processed per second)
    throughput = round(total_files / duration, 2) if duration > 0 else 0.0

    new_entry = {
        "timestamp": timestamp,
        "execution_status": status,
        "processed_slices_count": total_files,
        "total_runtime_seconds": round(duration, 3),
        "throughput_slices_per_sec": throughput,
        "system_errors": error_msg if error_msg else "None"
    }

    # Read current tracking block file if it exists, otherwise initialize an array list
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except (json.JSONDecodeError, IOError):
            data = []
    else:
        data = []

    # Append the fresh system run matrix and overwrite safely
    data.append(new_entry)
    
    # Keep file size clean by only maintaining the last 1,000 runs
    if len(data) > 1000:
        data = data[-1000:]

    with open(METRICS_FILE, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python track_metrics.py <SUCCESS|FAILURE> <total_files> <duration_seconds> [error_message]")
        sys.exit(1)

    status_arg = sys.argv[1]
    files_arg = int(sys.argv[2])
    duration_arg = float(sys.argv[3])
    err_arg = sys.argv[4] if len(sys.argv) > 4 else ""

    log_audit_metrics(status_arg, files_arg, duration_arg, err_arg)
