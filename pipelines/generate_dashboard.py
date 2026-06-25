#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multi-Modality IT Monitoring Dashboard
Parses metrics.json to generate a static, responsive HTML status page 
separating workloads and error trends for MRI, CT, and Ultrasound.
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

def calculate_modality_stats(metrics_list, target_modality):
    """Filters metrics and extracts summary data for a specific modality."""
    # Handle cases where modality might not be saved in older metrics logs
    modality_runs = [m for m in metrics_list if m.get("modality", "MR") == target_modality]
    
    total_runs = len(modality_runs)
    successful_runs = sum(1 for m in modality_runs if m.get("execution_status") == "SUCCESS")
    failed_runs = total_runs - successful_runs
    
    success_rate = round((successful_runs / total_runs) * 100, 1) if total_runs > 0 else 100.0
    total_slices = sum(m.get("processed_slices_count", 0) for m in modality_runs)
    
    avg_runtime = 0.0
    if successful_runs > 0:
        avg_runtime = round(sum(m.get("total_runtime_seconds", 0) for m in modality_runs if m.get("execution_status") == "SUCCESS") / successful_runs, 3)
        
    return {
        "total": total_runs,
        "success_rate": success_rate,
        "slices": total_slices,
        "avg_time": avg_runtime,
        "failed": failed_runs
    }

def generate_html_dashboard():
    """Compiles multi-modality metric trends into a unified clinical dashboard."""
    metrics_list = load_metrics()
    
    # Calculate standalone metrics per system category
    mri_stats = calculate_modality_stats(metrics_list, "MR")
    ct_stats = calculate_modality_stats(metrics_list, "CT")
    us_stats = calculate_modality_stats(metrics_list, "US")
    
    # Compile execution rows
    table_rows_html = ""
    for run in reversed(metrics_list[-50:]):
        status = run.get("execution_status", "UNKNOWN")
        modality_type = run.get("modality", "MR")
        status_badge_color = "#2ecc71" if status == "SUCCESS" else "#e74c3c"
        
        # Color coordinate the modality type label for clear scanning
        mod_color = "#3498db" if modality_type == "MR" else "#9b59b6" if modality_type == "CT" else "#e67e22"
        
        table_rows_html += f"""
        <tr>
            <td>{run.get('timestamp', 'N/A')}</td>
            <td><span style="background-color: {mod_color}; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">{modality_type}</span></td>
            <td><span style="background-color: {status_badge_color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem;">{status}</span></td>
            <td>{run.get('processed_slices_count', 0)}</td>
            <td>{run.get('total_runtime_seconds', 0)}s</td>
            <td>{run.get('throughput_slices_per_sec', 0)}</td>
            <td style="font-family: monospace; color: #7f8c8d; font-size: 0.9rem;">{run.get('system_errors', 'None')}</td>
        </tr>
        """

    if not table_rows_html:
        table_rows_html = "<tr><td colspan='7' style='text-align: center; color: #95a5a6;'>Waiting for scanner transmissions...</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <title>RTX 6000 Ada - Multi-Modality Edge Hub</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1300px; margin: 0 auto; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ecf0f1; padding-bottom: 20px; margin-bottom: 30px; }}
        h1 {{ margin: 0; color: #2c3e50; font-size: 1.8rem; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9rem; }}
        
        .modality-section {{ margin-bottom: 35px; }}
        .modality-title {{ font-size: 1.2rem; font-weight: bold; color: #34495e; margin-bottom: 15px; padding-left: 5px; border-left: 4px solid #333; }}
        .mri-border {{ border-left-color: #3498db; }}
        .ct-border {{ border-left-color: #9b59b6; }}
        .us-border {{ border-left-color: #e67e22; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; }}
        .card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); border-top: 4px solid #bdc3c7; }}
        .card.mri-theme {{ border-top-color: #3498db; }}
        .card.ct-theme {{ border-top-color: #9b59b6; }}
        .card.us-theme {{ border-top-color: #e67e22; }}
        .card-title {{ font-size: 0.8rem; text-transform: uppercase; color: #7f8c8d; letter-spacing: 0.5px; margin-bottom: 5px; }}
        .card-value {{ font-size: 1.5rem; font-weight: bold; color: #2c3e50; }}
        .card-sub {{ font-size: 0.8rem; color: #95a5a6; margin-top: 5px; }}
        
        .table-container {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.03); overflow: hidden; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #prev; }}
        th {{ background-color: #f8f9fa; color: #34495e; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
        tr:hover {{ background-color: #fdfefe; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>NVIDIA RTX 6000 Ada - Multi-Modality Enterprise Hub</h1>
                <div class="timestamp">Hospital Network Monitoring Console • Active Local Node Connection</div>
            </div>
            <div class="timestamp">Page Live Updated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</div>
        </header>

        <!-- MRI STATISTICS SECTION -->
        <div class="modality-section">
            <div class="modality-title mri-border">Magnetic Resonance Imaging (MRI) Analytics</div>
            <div class="grid">
                <div class="card mri-theme"><div class="card-title">Studies Managed</div><div class="card-value">{mri_stats['total']}</div></div>
                <div class="card mri-theme"><div class="card-title">SLA Success Rate</div><div class="card-value">{mri_stats['success_rate']}%</div></div>
                <div class="card mri-theme"><div class="card-title">Slices Scaled & Defaced</div><div class="card-value">{mri_stats['slices']}</div></div>
                <div class="card mri-theme"><div class="card-title">Avg GPU Compute Time</div><div class="card-value">{mri_stats['avg_time']}s</div></div>
            </div>
        </div>

        <!-- CT STATISTICS SECTION -->
        <div class="modality-section">
            <div class="modality-title ct-border">Computed Tomography (CT) Analytics</div>
            <div class="grid">
                <div class="card ct-theme"><div class="card-title">Studies Audited</div><div class="card-value">{ct_stats['total']}</div></div>
                <div class="card ct-theme"><div class="card-title">SLA Success Rate</div><div class="card-value">{ct_stats['success_rate']}%</div></div>
                <div class="card ct-theme"><div class="card-title">Dose Reports Indexed</div><div class="card-value">{ct_stats['slices']}</div></div>
                <div class="card ct-theme"><div class="card-title">Avg GPU Compute Time</div><div class="card-value">{ct_stats['avg_time']}s</div></div>
            </div>
        </div>

        <!-- ULTRASOUND STATISTICS SECTION -->
        <div class="modality-section">
            <div class="modality-title us-border">Ultrasound (US) Analytics</div>
            <div class="grid">
                <div class="card us-theme"><div class="card-title">Cine-Loops Extracted</div><div class="card-value">{us_stats['total']}</div></div>
                <div class="card us-theme"><div class="card-title">SLA Success Rate</div><div class="card-value">{us_stats['success_rate']}%</div></div>
                <div class="card us-theme"><div class="card-title">Frames Calibrated</div><div class="card-value">{us_stats['slices']}</div></div>
                <div class="card us-theme"><div class="card-title">Avg GPU Compute Time</div><div class="card-value">{us_stats['avg_time']}s</div></div>
            </div>
        </div>

        <h2>Unified System Audit Log (Last 50 Multi-Modality Requests)</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Timestamp (UTC)</th>
                        <th>Modality</th>
                        <th>Status</th>
                        <th>Data Volume</th>
                        <th>Compute Latency</th>
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
    print(f"[DASHBOARD] Multi-modality page compiled -> {HTML_OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html_dashboard()
