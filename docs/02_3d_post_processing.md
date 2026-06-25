# Tutorial 2: Post-Processing & Advanced 3D Visualization Workstation

This tutorial outlines how to configure a dedicated medical imaging workstation equipped with the RTX 6000 Ada (48GB VRAM) to handle ultra-high-resolution multi-planar reformatting (MPR) and intensive 3D volume rendering.

## 📋 Hardware Verification
Because rendering requires lightning-fast texture memory mapping, ensure your Ubuntu or Windows 11 Pro system is communicating optimally with the GPU. Open a terminal/command prompt and run:

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
```
*Expected Output:*
```text
name, driver_version, memory.total [MiB]
NVIDIA RTX 6000 Ada Generation, 535.154.05, 49140 MiB
```

## 🚀 Setup Steps

### Step 1: Install CUDA Toolkit & Imaging Libraries
Install the specialized medical imaging packages needed to map large MRI voxel grids directly into the 48GB VRAM pool:

```bash
# Update drivers and core toolkits
sudo apt-get install -y cuda-toolkit-12-2

# Install Python volumetric processing dependencies
pip install cupy-cuda12x pydicom SimpleITK trimesh
```

### Step 2: Running the 3D Voxel Engine
Use the baseline pipeline script provided in this repository to convert stacked 2D MRI slices into a unified 3D matrix inside the GPU's memory:

```bash
python pipelines/render_3d_volume.py \
  --input_dir ./sample_data/siemens_3t_brain/ \
  --output_mesh ./output/brain_model.obj \
  --cuda_accelerate True
```

### Step 3: Cloud PACS Integration
1. Open your Cloud PACS viewer utility dashboard.
2. Under "External 3D Rendering Tool Paths," add the network protocol pointing to your workstation node IP.
3. This allows radiologists to click "Open in 3D Workstation" directly from the cloud browser interface, shifting the compute load to the RTX 6000.

---

## ⚡ Performance Optimization Tips
* **VRAM Allocation:** The RTX 6000 Ada holds 48GB of memory. You can concurrently pre-cache up to 10 massive high-resolution 3D multi-echo sequences without performance degradation.
* **ECC Memory:** Ensure Error Correction Code (ECC) is **enabled** on the GPU via your NVIDIA Control Panel to prevent memory bit-flips during critical clinical diagnostic rendering.
