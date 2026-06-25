#!/bin/bash
# ==============================================================================
# Revolutionary Technology Company - Master MRI Pipeline Daemon
# Sequentially orchestrates Classification, QA, Resampling, Defacing, and Alerts.
# ==============================================================================

# Core Spool Directory Paths
WATCH_DIR="/workspace/incoming_dicom"
STAGE_CLASSIFY="/workspace/stage_classified"
STAGE_RESAMPLE="/workspace/stage_resampled"
STAGE_FINAL="/workspace/processed_output"
ERROR_SPOOL="/workspace/error_spool"

# Python Executable Pipelines
SCRIPT_CLASSIFY="/workspace/pipeline/pipelines/classify_series.py"
SCRIPT_QA="/workspace/pipeline/pipelines/detect_artifacts.py"
SCRIPT_RESAMPLE="/workspace/pipeline/pipelines/resample_volume.py"
SCRIPT_DEFACE="/workspace/pipeline/pipelines/deface_volume.py"
SCRIPT_METRICS="/workspace/pipeline/pipelines/track_metrics.py"
SCRIPT_DASHBOARD="/workspace/pipeline/pipelines/generate_dashboard.py"
SCRIPT_ALERT="/workspace/pipeline/pipelines/send_alert.py"

# Runtime Constraints
SETTLE_TIME_SECONDS=5
LOG_FILE="/var/log/mri_pipeline_daemon.log"
QA_JSON_LOG="/tmp/mri_qa_audit.json"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Master Pipeline Daemon Initialized..." | tee -a "$LOG_FILE"

# Guarantee physical folder arrays exist on disk space
mkdir -p "$WATCH_DIR" "$STAGE_CLASSIFY" "$STAGE_RESAMPLE" "$STAGE_FINAL" "$ERROR_SPOOL"

while true; do
    if [ "$(ls -A "$WATCH_DIR" 2>/dev/null)" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📥 Raw stream detected. Verifying stability..." >> "$LOG_FILE"
        
        INITIAL_SIZE=$(du -sb "$WATCH_DIR" | awk '{print $1}')
        sleep "$SETTLE_TIME_SECONDS"
        CURRENT_SIZE=$(du -sb "$WATCH_DIR" | awk '{print $1}')
        
        if [ "$INITIAL_SIZE" -eq "$CURRENT_SIZE" ] && [ "$CURRENT_SIZE" -gt 0 ]; then
            TOTAL_FILES=$(ls -1 "$WATCH_DIR" | wc -l)
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Series transfer complete. Total raw slices: $TOTAL_FILES" | tee -a "$LOG_FILE"
            
            START_TIME=$(date +%s.%N)
            
            # ------------------------------------------------------------------
            # STAGE 1: Standardize Naming Protocols & Spatial Orientation
            # ------------------------------------------------------------------
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📦 Stage 1: Classifying volume protocols..." >> "$LOG_FILE"
            python3 "$SCRIPT_CLASSIFY" "$WATCH_DIR" "$STAGE_CLASSIFY" >> "$LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                echo "❌ Classification stage broken." >> "$LOG_FILE"
                mv "$WATCH_DIR"/* "$ERROR_SPOOL/"
                continue
            fi

            # ------------------------------------------------------------------
            # STAGE 2: Accelerated Quality Assurance (FFT Motion/RF Audit)
            # ------------------------------------------------------------------
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Stage 2: Auditing K-space metrics via RTX 6000..." >> "$LOG_FILE"
            python3 "$SCRIPT_QA" "$STAGE_CLASSIFY" "$QA_JSON_LOG" >> "$LOG_FILE" 2>&1
            QA_EXIT=$?
            
            # Read the JSON result flag to determine image stability
            IS_CORRUPT=$(jq '.series_flagged_for_rescan' "$QA_JSON_LOG" 2>/dev/null)

            if [ "$QA_EXIT" -ne 0 ] || [ "$IS_CORRUPT" = "true" ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ QA FAILED: High noise/motion artifact signatures located." | tee -a "$LOG_FILE"
                
                END_TIME=$(date +%s.%N)
                RUN_DURATION=$(awk "BEGIN {print $END_TIME - $START_TIME}")
                
                # Log incident failure indicators
                python3 "$SCRIPT_METRICS" "FAILURE" "$TOTAL_FILES" "$RUN_DURATION" "QA Failure: Image matrix motion limits breached."
                python3 "$SCRIPT_DASHBOARD"
                python3 "$SCRIPT_ALERT" "MRI Processing Outage: A recent volume series from the scanners failed high-frequency FFT QA limits. Image data isolated in error_spool. Request a re-scan sequence for this patient."
                
                mv "$STAGE_CLASSIFY"/* "$ERROR_SPOOL/"
                rm -rf "$WATCH_DIR"/*
                continue
            fi
            echo "[$(date '+%Y-%m-%d %H:%M:%S')]  QA Verification Passed." >> "$LOG_FILE"

            # ------------------------------------------------------------------
            # STAGE 3: Cross-Vendor Isotropic Resampling (1mm Cubes)
            # ------------------------------------------------------------------
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📐 Stage 3: Resampling spatial grids to 1.0mm isotropic..." >> "$LOG_FILE"
            python3 "$SCRIPT_RESAMPLE" "$STAGE_CLASSIFY" "$STAGE_RESAMPLE" >> "$LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                echo "❌ Resampling stage broken." >> "$LOG_FILE"
                mv "$STAGE_CLASSIFY"/* "$ERROR_SPOOL/"
                rm -rf "$WATCH_DIR"/*
                continue
            fi

            # Add this code block inside your master watch loop to support multi-modality parsing:
                FIRST_FILE=$(ls -1 "$WATCH_DIR" | head -n 1)
                MODALITY=$(docker exec rtx6000_mri_worker python3 -c "import pydicom; print(pydicom.dcmread('$WATCH_DIR/$FIRST_FILE', stop_before_pixels=True).get('Modality','UNKNOWN'))")

                case "$MODALITY" in
                    "MR")
                        # Run your existing 5-stage MRI loop
                        ;;
                    "CT")
                        python3 /workspace/pipeline/pipelines/process_ct_volume.py "$WATCH_DIR" "$STAGE_FINAL"
                        ;;
                    "US")
                        python3 /workspace/pipeline/pipelines/process_ultrasound_cine.py "$WATCH_DIR/$FIRST_FILE" "$STAGE_FINAL"
                        ;;
                    *)
                        echo "Modality $MODALITY not supported yet. Routing directly to Cloud PACS..."
                        ;;
                esac

            # ------------------------------------------------------------------
            # STAGE 4: Volumetric Spatial Anonymization (Defacing Privacy Guard)
            # ------------------------------------------------------------------
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 👤 Stage 4: Execution of spatial defacing security profiles..." >> "$LOG_FILE"
            python3 "$SCRIPT_DEFACE" "$STAGE_RESAMPLE" "$STAGE_FINAL" >> "$LOG_FILE" 2>&1
            if [ $? -ne 0 ]; then
                echo "❌ Defacing privacy guard broken." >> "$LOG_FILE"
                mv "$STAGE_RESAMPLE"/* "$ERROR_SPOOL/"
                rm -rf "$WATCH_DIR"/*
                continue
            fi

            # ------------------------------------------------------------------
            # STAGE 5: Complete Performance Logging & Dashboard Export
            # ------------------------------------------------------------------
            END_TIME=$(date +%s.%N)
            RUN_DURATION=$(awk "BEGIN {print $END_TIME - $START_TIME}")
            
            python3 "$SCRIPT_METRICS" "SUCCESS" "$TOTAL_FILES" "$RUN_DURATION"
            python3 "$SCRIPT_DASHBOARD"
            
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 Pipeline processing loop finalized successfully. Files ready for Cloud PACS ingestion." | tee -a "$LOG_FILE"
            
            # Clear temporary staging folders
            rm -rf "$WATCH_DIR"/*
            rm -rf "$STAGE_CLASSIFY"/*
            rm -rf "$STAGE_RESAMPLE"/*
        fi
    fi
    sleep 3
done
