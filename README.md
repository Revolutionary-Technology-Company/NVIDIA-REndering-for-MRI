# 🏥 NVIDIA RTX 6000 Ada Rendering Pipeline for MRI (GE & Siemens)

[![MRI NVIDIA Pipeline CI](https://github.com)](https://github.com)
[![Port Infrastructure](https://shields.io)](http://localhost:9920)
[![DICOM Ingestion](https://shields.io)](#)

This repository contains the containerized orchestration framework, asynchronous multicore pipelines, and GPU acceleration modules to optimize and secure MRI workflows. It functions as a secure edge intermediary node connecting physical hospital scanners (**GE 1.5T**, **Siemens 3T**, and **Siemens Avanto 1.5T**) to an offsite **Cloud-Based PACS**.

---

## 🏗️ System Architecture & Workflow Pipeline

[ PHYSICAL SCANNER ARRAY ]\
(GE 1.5T - Siemens 3T - Siemens Avanto 1.5T)\
│\
│ DICOM C-STORE (Raw / Uncompressed)\
▼\
┌──────────────────────────────────────────────────────────────────┐\
│ NVIDIA RTX 6000 Ada Edge Server Node │\
│ │\
│ Stage 1: Ingestion & Hanging Protocol Layout Stabilization │\
│ └─ `classify_series.py` (TR/TE Physics Classification) │\
│ Stage 2: Accelerated K-Space Quality Assurance │\
│ └─ `detect_artifacts.py` (CUDA 2D FFT Blur Audit) │\
│ Stage 3: Cross-Vendor Isotropic Resampling │\
│ └─ `resample_volume.py` (3D Trilinear 1mm Scaling) │\
│ Stage 4: Volumetric Face-Plane De-identification │\
│ └─ `deface_volume.py` (Spatial HIPAA Privacy Guard) │\
└──────────────────────────────────────────────────────────────────┘\
│\
│ TLS 1.3 Wrapping via Router Tunnel\
▼\
[ SECURE CLOUD PACS ]


## ⚙️ Core Pipeline Modules

The processing matrix sequentially executes the following scripts inside the container environment:

* **`pipelines/classify_series.py`**: Standardizes erratic scanner pulse naming strings into uniform hanging protocols using exact Echo Time (TE), Repetition Time (TR), and patient orientation cosine vectors.
* **`pipelines/detect_artifacts.py`**: Executes an asynchronous 2D Fast Fourier Transform (`torch.fft.fft2`) on the GPU to measure high-frequency noise ratios, automatically flagging motion-blurred scans while the patient is on-table.
* **`pipelines/resample_volume.py`**: Normalizes multi-vendor data grids (thick slices vs high-density arrays) into uniform 1.0mm isotropic voxels via hardware-accelerated trilinear interpolation.
* **`pipelines/deface_volume.py`**: Enforces HIPAA Safe Harbor compliance on high-resolution 3D head scans by mathematically zeroing out voxel matrices along the facial geometry plane to prevent 3D facial reconstruction.

---

## 🚀 Getting Started

### 📋 Prerequisites
* **Host System:** Ubuntu Server 22.04 LTS / 24.04 LTS
* **Hardware:** 1x NVIDIA RTX 6000 Ada Generation GPU (48GB VRAM pool)
* **Drivers:** NVIDIA Driver >= 535 + [NVIDIA Container Toolkit](https://nvidia.com) installed.
* **Network:** Static internal IP address with port `11104` (DICOM Ingestion) and `9920` (Intranet Dashboard) open.

### 🛠️ Installation & Deployment
1. Clone this repository to your local clinical edge server:
   ```bash
   git clone https://github.com
   cd NVIDIA-REndering-for-MRI
   ```
2. Launch the complete containerized infrastructure stack (Edge Router, CUDA Worker, Secure Nginx Server):
   ```bash
   docker compose up -d
   ```
3. Verify that the RTX 6000 Ada GPU and its 48GB VRAM pool are successfully mapped:
   ```bash
   docker exec -it rtx6000_mri_worker nvidia-smi
   ```

---

## 🖥️ System Operations & Monitoring

### 📈 Local Intranet Dashboard (Port `9920`)
A responsive monitoring dashboard (`pipelines/generate_dashboard.py`) is rebuilt automatically at the conclusion of every scan cycle. It is securely served via an internal Nginx proxy locked to your hospital's subnet (`10.0.0.0/8`). 
* Access URL: `http://[YOUR_SERVER_IP]:9920`

### 🚨 Outage & Failure Alert Routing
If a sequence loop triggers an unrecoverable processing failure or data corruption event, `pipelines/send_alert.py` runs instantly, outputting structured rich-text markdown notifications directly to your clinical engineering team's **Slack** or **Microsoft Teams** channels via secure webhooks.

### 📋 Technical Troubleshooting
For comprehensive triage guidelines, memory recovery procedures (OOM faults), and network disaster recovery steps, refer directly to the **[On-Call Operations Runbook (docs/OPERATIONS.md)](docs/OPERATIONS.md)**.

---

## 🤝 Verification & CI Testing

This repository enforces quality gates on all code submissions. The full end-to-end integration and computation matrix is validated automatically by a Python simulation script using mock DICOM voxel layers.

To execute the unit tests locally before pushing to production:
```bash
python3 tests/test_pipeline.py
```
*Note: GitHub Actions executes this test suite on every `push` and `pull_request` to the `main` branch.*

---

## 📄 Clinical Disclaimer
*This software framework is intended for clinical workflow acceleration, research data standardization, and edge routing management. All pipeline components must be validated in accordance with your specific institutional security policies, HIPAA regulations, and medical device compliance guidelines before diagnostic implementation.*
