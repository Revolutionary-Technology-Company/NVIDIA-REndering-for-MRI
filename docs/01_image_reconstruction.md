# Tutorial 1: AI-Enhanced Image Reconstruction (Scan Time Acceleration)

This tutorial covers setting up the NVIDIA RTX 6000 Ada server as an inline, edge AI-inference node. This pipeline ingests raw, noisy, or undersampled volumes directly from the scanners, runs a deep-learning reconstruction model via NVIDIA Triton, and outputs high-fidelity DICOMs.

## 🏗️ Workflow Diagram
[GE / Siemens Scanner] ──(C-STORE Raw)──> [Orthanc Listener]\
│\
(Python Hook)\
▼\
[Cloud PACS] <───(C-STORE Clean)─── [NVIDIA Triton Server (GPU)]

## 📋 Prerequisites
1. **Docker & NVIDIA Container Toolkit** installed on your GPU node server.
2. The **NVIDIA Triton Inference Server** container image pulled:
   ```bash
   docker pull nvcr.io/nvidia/tritonimages:24.01-py3
   ```
3. Custom or third-party (e.g., Subtle Medical/DeepResolve equivalent) TensorRT weight files placed in `/models/mri_recon/1/model.plan`.

## 🚀 Setup Steps

### Step 1: Configure the Edge DICOM Listener
We use an open-source DICOM server (Orthanc) to intercept images. Create an automated Python routing hook (`config/route_recon.py`):

```python
import pydicom
import requests

def ReceivedInstanceCallback(instance_id, dicom_bytes, metadata):
    # Parse DICOM to ensure it's a structural MRI sequence needing denoising
    ds = pydicom.dcmread(dicom_bytes)
    modality = ds.get("Modality", "UNKNOWN")
    
    if modality == "MR":
        # Extract pixel data matrix and ship it to the local Triton server
        # (Replace with your actual TensorRT-MRI network payload configuration)
        print(f"Processing MR Series: {ds.SeriesDescription} via RTX 6000 Ada...")
        
        # Post-inference, automatically forward the enhanced DICOM to Cloud PACS
        # requests.post('http://localhost:8042/modalities/cloud-pacs/store', data=instance_id)
```

### Step 2: Spin Up the Stack
Run the orchestration stack configured to utilize your RTX 6000 Ada GPU:

```bash
docker-compose -f docker-compose.recon.yml up -d
```

### Step 3: Configure Scanner Destination
On your **GE 1.5T**, **Siemens 3T**, or **Siemens Avanto**, add a new Target/Destination in the system network settings:
* **AE Title:** `NVIDIA_RECON`
* **IP Address:** `[Your_RTX6000_Server_IP]`
* **Port:** `11104`

---

## 🛑 Validation & Testing
Send a non-clinical test phantom sequence from the Siemens 3T console. Verify logs via:
```bash
docker logs triton-inference-server
```
Look for successful execution flags showing CUDA core allocation on Device 0.
