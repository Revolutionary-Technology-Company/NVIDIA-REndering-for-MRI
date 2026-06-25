#!/bin/bash
# ==============================================================================
# Revolutionary Technology Company - MRI Pipeline Automation Daemon
# Monitors incoming spool volumes and executes the multicore processing 
# stack once a scanner finishes uploading a sequence/series volume.
# ==============================================================================

# Configuration Constants
WATCH_DIR="/workspace/incoming_dicom"
PROCESSED_DIR="/workspace/processed_output"
PIPELINE_SCRIPT="/workspace/pipeline/pipelines/reconstruct_mri_multicore.py"
SETTLE_TIME_SECONDS=5
LOG_FILE="/var/log/mri_pipeline_daemon.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Starting MRI Pipeline Watch Daemon..." | tee -a "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Watching directory: $WATCH_DIR" | tee -a "$LOG_FILE"

# Ensure runtime directories exist
mkdir -p "$WATCH_DIR"
mkdir -p "$PROCESSED_DIR"

while true; do
    # Check if there are any files inside the watch directory
    if [ "$(ls -A "$WATCH_DIR" 2>/dev/null)" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📥 Incoming data detected. Waiting for transmission to finish..." >> "$LOG_FILE"
        
        # Settle-down verification loop: Measure folder sizes until writing halts
        INITIAL_SIZE=$(du -sb "$WATCH_DIR" | awk '{print $1}')
        sleep "$SETTLE_TIME_SECONDS"
        CURRENT_SIZE=$(du -sb "$WATCH_DIR" | awk '{print $1}')
        
        if [ "$INITIAL_SIZE" -eq "$CURRENT_SIZE" ] && [ "$CURRENT_SIZE" -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Series transfer complete (Folder size stabilized at $CURRENT_SIZE bytes)." | tee -a "$LOG_FILE"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚡ Passing volume to NVIDIA RTX 6000 Multicore Engine..." | tee -a "$LOG_FILE"
            
            # Execute the high-throughput Python engine inside the host context
            python3 "$PIPELINE_SCRIPT" "$WATCH_DIR" "$PROCESSED_DIR" >> "$LOG_FILE" 2>&1
            
            if [ $? -eq 0 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧹 Cleaning up raw local spool directory..." >> "$LOG_FILE"
                # Purge raw slices safely to clear memory for the next scan sequence
                rm -rf "$WATCH_DIR"/*
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 Volume cycle finalized successfully." | tee -a "$LOG_FILE"
            else
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ CRITICAL: Multicore pipeline exited with an error status." | tee -a "$LOG_FILE"
                # Evacuate files to an error workspace block to prevent pipeline lockups
                mkdir -p "/workspace/error_spool"
                mv "$WATCH_DIR"/* "/workspace/error_spool/"
            fi
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏳ Scanner is still actively writing slices to disk. Polling..." >> "$LOG_FILE"
        fi
    fi
    
    # Idle poll spacing time
    sleep 3
done
