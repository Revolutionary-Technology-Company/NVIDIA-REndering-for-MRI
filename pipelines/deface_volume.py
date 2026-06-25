#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multicore 3D Spatial Defacing Engine
GPU-accelerated geometric privacy masking combined with multicore slice reconstruction.
"""

import os
import sys
import pydicom
import numpy as np
from multiprocessing import Pool, cpu_count

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None
    CUDA_AVAILABLE = False

def worker_write_defaced_slice(args):
    """Writes a pre-masked slice out to disk using independent worker cores."""
    slice_bytes, template_path, output_path = args
    try:
        ds = pydicom.dcmread(template_path)
        ds.PixelData = slice_bytes
        ds.ImageComments = "SPATIAL_DEFACED_MULTICORE_RTX6000"
        ds.save_as(output_path)
        return True
    except Exception:
        return False

def run_parallel_defacing(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    slices = [pydicom.dcmread(f) for f in files]
    slices.sort(key=lambda x: float(x.SliceLocation) if "SliceLocation" in x else 0)

    rows, cols, num_slices = int(slices[0].Rows), int(slices[0].Columns), len(slices)
    volume_matrix = np.zeros((rows, cols, num_slices), dtype=np.int16)
    for i, s in enumerate(slices):
        volume_matrix[:, :, i] = s.pixel_array

    face_cutoff = int(cols * 0.35)

    # High-speed GPU Face-Plane Matrix masking pass
    if CUDA_AVAILABLE:
        device = torch.device("cuda:0")
        tensor_vol = torch.from_numpy(volume_matrix.astype(np.float32)).to(device)
        tensor_vol[:, :face_cutoff, :] = 0.0
        sanitized_volume = tensor_vol.cpu().numpy().astype(np.int16)
        torch.cuda.synchronize()
    else:
        volume_matrix[:, :face_cutoff, :] = 0
        sanitized_volume = volume_matrix

    # Distribute modified slice rendering across all CPU cores
    task_args = []
    for i, s in enumerate(slices):
        out_path = os.path.join(output_dir, f"defaced_slice_{i:04d}.dcm")
        task_args.append((sanitized_volume[:, :, i].tobytes(), s.filename, out_path))

    print(f"[DEFACE-MULTICORE] Distributing slice conversion to {cpu_count()} worker cores...")
    with Pool(processes=cpu_count()) as pool:
        _ = pool.map(worker_write_defaced_slice, task_args)

if __name__ == "__main__":
    run_parallel_defacing(sys.argv[1], sys.argv[2])
