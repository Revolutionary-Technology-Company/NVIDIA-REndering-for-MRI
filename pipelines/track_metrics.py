#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multi-Modality MRI/CT/US Metrics Logger
Records processing throughput, data size, and VRAM/CPU runtime profiles 
into an auditable metrics.json framework, segmented by clinical modality.
"""

import sys
import os
import json
from datetime import datetime

METRICS_FILE = "/workspace/pipeline/metrics.json"

def log_audit_metrics(status: str, total_files: int, duration: float, modality: str, error_msg: str = ""):
    """Appends structural execution history parameters to the auditing system matrix."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Calculate throughput metrics (Slices processed per second)
    throughput = round(total_files / duration, 2) if duration > 0 else 0.0

    # Validate and standardize modality tag input
    modality_clean = str(modality).upper().strip()
    if modality_clean not in ["MR", "CT", "US"]:
        modality_clean = "MR"  # Default fallback parameter

    new_entry = {
        "timestamp": timestamp,
        "modality": modality_clean,
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
    print(f"[METRICS] Successfully recorded entry for modality: {modality_clean}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python track_metrics.py <SUCCESS|FAILURE> <total_files> <duration_seconds> <MR|CT|US> [error_message]")
        sys.exit(1)

    status_arg = sys.argv[1]
    files_arg = int(sys.argv[2])
    duration_arg = float(sys.argv[3])
    modality_arg = sys.argv[4]
    err_arg = sys.argv[5] if len(sys.argv) > 5 else ""

    log_audit_metrics(status_arg, files_arg, duration_arg, modality_arg, err_arg)
