#!/usr/bin/env python3
"""
Revolutionary Technology Company - Hospital IT Monitoring Dashboard
Parses metrics.json to generate a static, responsive HTML status page 
displaying NVIDIA RTX 6000 AI and 3D volume processing throughput.
"""

import os
import sys
import json
from datetime import datetime

METRICS_FILE = "/workspace/pipeline/metrics.json"
HTML_OUTPUT_FILE = "/workspace/pipeline/dashboard.html"

def load_metrics():
    """Reads and validates the performance log registry."""
    if not os.path.exists(METRICS_FILE):
        return []
    try:
        with open(METRICS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def generate_html_dashboard():
    """Compiles log arrays into an auditable hospital IT dashboard layout."""
    metrics_list = load_metrics()
    
    # Calculate global tracking indicators
    total_runs = len(metrics_list)
    successful_runs = sum(1 for m in metrics_list if m.get("execution_status") == "SUCCESS")
    failed_runs = total_runs - successful_runs
    
    success_rate = round((successful_runs / total_runs) * 100, 1) if total_runs > 0 else 100.0
    total_slices = sum(m.get("processed_slices_count", 0) for m in metrics_list)
    
    avg_runtime = 0.0
    if successful_runs > 0:
        avg_runtime = round(sum(m.get("total_runtime_seconds", 0) for m in metrics_list if m.get("execution_status") == "SUCCESS") / successful_runs, 3)

    # Build individual row entries
    table_rows_html = ""
    # Display the last 50 runs, newest first
    for run in reversed(metrics_list[-50:]):
        status = run.get("execution_status", "UNKNOWN")
        status_badge_color = "#2ecc71" if status == "SUCCESS" else "#e74c3c"
        
        table_rows_html += f"""
        <tr>
            <td>{run.get('timestamp', 'N/A')}</td>
            <td><span style="background-color: {status_badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem;">{status}</span></td>
            <td>{run.get('processed_slices_count', 0)}</td>
            <td>{run.get('total_runtime_seconds', 0)}s</td>
            <td>{run.get('throughput_slices_per_sec', 0)}</td>
            <td style="font-family: monospace; color: #7f8c8d; font-size: 0.9rem;">{run.get('system_errors', 'None')}</td>
        </tr>
        """

    if not table_rows_html:
        table_rows_html = "<tr><td colspan='6' style='text-align: center; color: #95a5a6;'>No scan sequences logged yet. Waiting for input from GE/Siemens nodes...</td></tr>"

    # Core HTML/CSS template framework
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5"> <!-- Auto refresh page every 5 seconds -->
    <title>RTX 6000 Ada - MRI Pipeline Monitor</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 20px; margin-bottom: 30px; }}
        h1 {{ margin: 0; color: #2c3e50; font-size: 1.8rem; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); border-top: 4px solid #3498db; }}
        .card.success {{ border-top-color: #2ecc71; }}
        .card.failed {{ border-top-color: #e74c3c; }}
        .card-title {{ font-size: 0.85rem; text-transform: uppercase; color: #7f8c8d; letter-spacing: 0.5px; margin-bottom: 10px; }}
        .card-value {{ font-size: 1.8rem; font-weight: bold; color: #2c3e50; }}
        .table-container {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); overflow: hidden; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 15px; border-bottom: 1px solid #prev; }}
        th {{ background-color: #f8f9fa; color: #34495e; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }}
        tr:hover {{ background-color: #fdfefe; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>NVIDIA RTX 6000 Ada - MRI Processing Node</h1>
                <div class="timestamp">Hospital Network Monitoring Console • Active Local Node Connection</div>
            </div>
            <div class="timestamp">Page Live Updated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-title">Total Sequences Managed</div>
                <div class="card-value">{total_runs}</div>
            </div>
            <div class="card success">
                <div class="card-title">Operational SLA Success Rate</div>
                <div class="card-value">{success_rate}%</div>
            </div>
            <div class="card">
                <div class="card-title">Aggregated Slice Throughput</div>
                <div class="card-value">{total_slices}</div>
            </div>
            <div class="card">
                <div class="card-title">Avg GPU Compute Speed</div>
                <div class="card-value">{avg_runtime}s</div>
            </div>
        </div>

        <h2>Recent Volume Audit Log (Last 50 Series Requests)</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp (UTC)</th>
                        <th>Status</th>
                        <th>Slice Volume</th>
                        <th>Compute Delay</th>
                        <th>Throughput (img/sec)</th>
                        <th>System Diagnostics Reference</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

    with open(HTML_OUTPUT_FILE, "w") as f:
        f.write(html_content)
    print(f"[DASHBOARD] Live layout exported smoothly to: {HTML_OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html_dashboard()
