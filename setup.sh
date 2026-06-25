#!/bin/bash
# ==============================================================================
# Revolutionary Technology Company - MRI Node Initialization Setup Script
# Handles directory building, driver verification, and package installations.
# ==============================================================================

# Ensure script is executed with administrative privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Please run this initialization script with root privileges (sudo ./setup.sh)"
    exit 1
fi

echo "======================================================================"
echo "🏥 Initializing NVIDIA RTX 6000 Ada MRI Pipeline Node Infrastructure"
echo "======================================================================"

# ------------------------------------------------------------------------------
# STAGE 1: Verify Core NVIDIA Driver Architecture & VRAM
# ------------------------------------------------------------------------------
echo -e "\n🔍 [STAGE 1] Checking physical GPU hardware environment..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ Error: NVIDIA proprietary drivers are not installed on this host."
    echo "   Please install the official NVIDIA Driver Suite (>= 535) before running setup."
    exit 1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,unit | head -n 1)

echo "✅ Found GPU Architecture: $GPU_NAME"
echo "✅ Total Dedicated VRAM  : $GPU_VRAM"

# ------------------------------------------------------------------------------
# STAGE 2: Install Core Linux OS Package Dependencies
# ------------------------------------------------------------------------------
echo -e "\n📦 [STAGE 2] Checking and downloading system software dependencies..."
apt-get update -y

PACKAGES=(docker.io docker-compose-v2 dcmtk jq bc python3-pip)
MISSING_PKGS=()

for pkg in "${PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" &> /dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo "📥 Downloading missing utilities: ${MISSING_PKGS[*]}..."
    apt-get install -y "${MISSING_PKGS[@]}"
else
    echo "✅ All core Linux system dependencies are already satisfied."
fi

# ------------------------------------------------------------------------------
# STAGE 3: Build Repository & Volume Spool Layout Structures
# ------------------------------------------------------------------------------
echo -e "\n📁 [STAGE 3] Constructing local pipeline data layout files and arrays..."
# Root repository workspace structures
mkdir -p config pipelines tests models tutorials docs

# Shared runtime volume spool arrays used by Docker mounts
mkdir -p /workspace/incoming_dicom
mkdir -p /workspace/stage_classified
mkdir -p /workspace/stage_resampled
mkdir -p /workspace/processed_output
mkdir -p /workspace/error_spool

# Adjust permissions so the application runner has unhindered read/write access
chmod -R 777 /workspace/

# Create a clean blank system log file block for the master daemon tracker
touch /var/log/mri_pipeline_daemon.log
chmod 666 /var/log/mri_pipeline_daemon.log

echo "✅ Directory maps constructed and volume permissions initialized."

# ------------------------------------------------------------------------------
# STAGE 4: Guarantee Script Executability Check
# ------------------------------------------------------------------------------
echo -e "\n🛡️ [STAGE 4] Adjusting runtime pipeline asset permissions..."
SCRIPT_PATHS=(
    "pipelines/anonymize.py"
    "pipelines/classify_series.py"
    "pipelines/detect_artifacts.py"
    "pipelines/resample_volume.py"
    "pipelines/deface_volume.py"
    "pipelines/track_metrics.py"
    "pipelines/generate_dashboard.py"
    "pipelines/send_alert.py"
    "tests/watch_spool.sh"
    "tests/simulate_scanner.sh"
    "tests/test_pipeline.py"
)

for script in "${SCRIPT_PATHS[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo "✅ Execution mask applied: $script"
    fi
done

# ------------------------------------------------------------------------------
# STAGE 5: Validate Orchestration Compose Layout Integrity
# ------------------------------------------------------------------------------
echo -e "\n🚀 [STAGE 5] Testing container orchestrator validation parameters..."
if [ -f "docker-compose.yml" ]; then
    docker compose config > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ docker-compose.yml layout and schema validation passed."
    else
        echo "❌ Error: docker-compose.yml configuration file failed validation checks."
        exit 1
    fi
else
    echo "⚠️  Warning: Core docker-compose.yml file missing from execution root."
fi

echo "======================================================================"
echo "🎉 SUCCESS: Initialization complete. Your hardware node is configured!"
echo "   To start the pipeline, run: docker compose up -d"
echo "======================================================================"
