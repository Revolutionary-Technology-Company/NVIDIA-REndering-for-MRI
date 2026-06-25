# 🏥 NVIDIA RTX 6000 Ada Multi-Modality Enterprise Edge Hub

[![Multi-Modality Pipeline CI](https://github.com)](https://github.com)
[![Intranet Dashboard Server](https://shields.io)](http://localhost:9920)
[![DICOM Central Ingestion](https://shields.io)](#)

This repository contains the containerized orchestration framework, asynchronous multicore pipelines, and GPU acceleration modules to optimize and secure medical imaging workflows. It functions as a secure edge intermediary node connecting 14 physical hospital scanner units across **MRI**, **CT**, and **Ultrasound (US)** departments to an offsite **Cloud-Based PACS**.

---

## 🏗️ System Architecture & Workflow Pipeline



[ HANGING FLAGGED MODALITY ROUTING TOPOLOGY ]\
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐\
│ MRI SCANNERS │ CT SCANNERS │ ULTRASOUND UNITS │\
│ - GE 1.5T │ - Siemens Force ED Dual-Src │ - Philips iU22 (x4 Premium) │\
│ - Siemens 3T Main Campus │ - Siemens Definition AS+ │ - Sonosite Bedside Trauma │\
│ - Siemens Avanto 1.5T │ - Dual-Purpose Angio/Fluoro │ (x2 Portable Units) │\
│ │ - GE Acute 16-Row (x2 Units) │ │\
└──────────────────────────────┴──────────────┬───────────────┴──────────────────────────────┘\
│\
│ DICOM C-STORE Ingestion Stream\
▼\
┌────────────────────────────────────────────────────────────────────────────────────────────┐\
│ NVIDIA RTX 6000 Ada Multi-Modality Node │\
│ │\
│ 🧠 [MRI Track]: Protocol Classify ──> 2D FFT K-Space QA ──> 1mm Resampling ──> 3D Defacing │\
│ 🫁 [CT Track] : Radiation Dose Structured Report (RDSR) Audit ──> CUDA HU Lung Masking │\
│ 💓 [US Track] : Multi-Frame Cine-Loop Video Deconstruction ──> Spatial Delta Calibration │\
└────────────────────────────────────────────────────────────────────────────────────────────┘\
│\
│ TLS 1.3 Wrapping via Gateway Tunnel\
▼\
[ SECURE CLOUD PACS ]

## ⚙️ Core Multicore Pipeline Modules

The compute environment maps arriving datasets into distinct processing pathways based on the DICOM header modality tag, executing all operations using asynchronous `multiprocessing.Pool` allocations to fully saturate host CPU threads and GPU registers:

### 🧠 Magnetic Resonance Imaging (MRI Track)
* **`pipelines/classify_series.py`**: Resolves directional cosines to calculate exact 3D oblique planes, handles vendor-specific metadata tags across GE and Siemens, and maps contrast heuristics based on TR/TE physics boundaries in parallel.
* **`pipelines/detect_artifacts.py`**: Executes an asynchronous 2D Fast Fourier Transform (`torch.fft.fft2`) on the GPU to measure high-frequency noise ratios, automatically alerting clinical staff of motion blur or RF spikes.
* **`pipelines/resample_volume.py`**: Normalizes multi-vendor data grids (thick slices vs high-density arrays) into uniform 1.0mm isotropic voxels via hardware-accelerated trilinear interpolation.
* **`pipelines/deface_volume.py`**: Enforces HIPAA Safe Harbor privacy by mathematically zeroing out voxel matrices along the anterior facial geometry plane on the GPU, re-rendering output frames asynchronously across CPU worker pools.

### 🫁 Computed Tomography (CT Track)
* **`pipelines/process_ct_volume.py`**: Automates radiation dosage auditing by indexing the CTDIvol and Dose Length Product (DLP) parameters. It shifts high-density volumetric voxels onto the GPU to apply tissue boundary masks matching air spaces (`-900 HU` to `-400 HU`) to isolate lung cavities.

### 💓 Ultrasound (US Track)
* **`pipelines/process_ultrasound_cine.py`**: Ingests multi-frame video components (Cine-Loops) from bedside trauma or premium units and extracts them into independent frame sequences. It parses the `SequenceOfUltrasoundRegions` block to embed explicit spatial millimeter-per-pixel metadata layers into each frame concurrently.

---

## 🚀 Getting Started

### 📋 Prerequisites
* **Host System:** Ubuntu Server 22.04 LTS / 24.04 LTS
* **Hardware:** 1x NVIDIA RTX 6000 Ada Generation GPU (48GB VRAM pool)
* **Drivers:** NVIDIA Driver >= 535 + [NVIDIA Container Toolkit](https://nvidia.com) installed.
* **Network:** Static internal IP address with ports `11104` (DICOM Router) and `9920` (Intranet Dashboard Proxy) open.

### 🛠️ One-Click Server Initialization
We have built an entry-level pre-flight initialization script that creates the full directory tree map, downloads software requirements (`jq`, `dcmtk`, `bc`, Python packages), checks physical RTX 6000 hardware connectivity, and validates container definitions.

1. Clone the repository and execute the setup module:
   ```bash
   git clone https://github.com
   cd NVIDIA-REndering-for-MRI
   sudo ./setup.sh
   ```
2. Spin up the container orchestration layer:
   ```bash
   docker compose up -d
   ```
3. Audit active pipeline logs:
   ```bash
   docker exec -it rtx6000_mri_worker tail -f /var/log/mri_pipeline_daemon.log
   ```

---

## 🖥️ System Operations & Monitoring

### 📊 Segmented Multi-Modality Dashboard (Port `9920`)
A responsive internal web server (`pipelines/generate_dashboard.py`) runs at the completion of every incoming study. It processes performance stats and splits logs into distinct analytical widgets tracking study volumes, success metrics, and GPU latency speeds across **MRI**, **CT**, and **Ultrasound** independently based on data inside `metrics.json`.
* Protected Access URL: `http://[YOUR_SERVER_IP]:9920` (Enforced via Nginx to block traffic outside the `10.0.0.0/8` hospital intranet).

### 🚨 Critical Incident Alerting
If a sequence processing cycle crashes, `pipelines/send_alert.py` parses the stack trace error data and broadcasts rich-text markdown incident blocks to your clinical engineering team's **Slack** or **Microsoft Teams** workspace channels via webhooks.

### 📋 Operations, Troubleshooting, and Specifications Runbook
* For on-call triage steps and memory recovery procedures (OOM faults), consult the **[On-Call Operations Runbook (docs/OPERATIONS.md)](docs/OPERATIONS.md)**.
* For server deployment guidelines (CPU, power, PCIe layout), consult the **[Hardware Specification Sheet (docs/HARDWARE_SPECS.md)](docs/HARDWARE_SPECS.md)**.

---

## 🤝 Verification & Continuous Integration (CI)

Our system stability is protected by a multi-modality continuous integration test suite (`tests/test_pipeline.py`). It generates synthetic 3D MRI blocks, Hounsfield CT datasets, and multi-frame Ultrasound arrays to validate process pools and asynchronous CUDA stream queues.

To run the verification suite locally:
```bash
python3 tests/test_pipeline.py
```
*GitHub Actions executes this test harness automatically on every code push or pull request to the `main` branch to guarantee runtime infrastructure stability.*
