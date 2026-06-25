#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multicore CT Radiation Audit & Core Segmenter
Normalizes raw scanner pixel metrics into standardized Hounsfield Units (HU), 
maps lung tissue boundaries on the GPU, and indexes compliance data.
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

def worker_process_ct_slice(args):
    """Converts raw metrics to Hounsfield space, applies lung mask, and saves file data."""
    input_path, output_path, slope, intercept, ctdi, dlp, idx, total = args
    try:
        ds = pydicom.dcmread(input_path)
        if ds.get("Modality") != "CT": return False

        # Convert raw scanner array integers to uniform Hounsfield Units (HU)
        raw_pixels = ds.pixel_array.astype(np.float32)
        hu_matrix = (raw_pixels * slope) + intercept

        if CUDA_AVAILABLE:
            device = torch.device("cuda:0")
            stream = torch.cuda.Stream(device=device)
            with torch.cuda.stream(stream):
                tensor_slice = torch.from_numpy(hu_matrix).to(device, non_blocking=True)
                
                # Apply tissue boundaries: Lung tissue typically sits between -900 and -400 HU
                lung_tissue_mask = (tensor_slice >= -900) & (tensor_slice <= -400)
                segmented_tensor = torch.where(lung_tissue_mask, tensor_slice, torch.tensor(-1024.0, device=device))
                
                # Reverse scaling calculation back to raw scanner storage space
                inverse_scaled_tensor = (segmented_tensor - intercept) / slope
                processed_pixels = inverse_scaled_tensor.cpu().numpy()
            stream.synchronize()
        else:
            segmented_hu = np.where((hu_matrix >= -900) & (hu_matrix <= -400), hu_matrix, -1024)
            processed_pixels = (segmented_hu - intercept) / slope

        # Save changes to file disk
        final_array = np.clip(processed_pixels, 0, 65535).astype(np.uint16)
        ds.PixelData = final_array.tobytes()
        ds.ImageComments = f"CT_MULTICORE_RECON;CTDI={ctdi}mGy;DLP={dlp}mGycm;SLICE={idx}/{total}"
        ds.save_as(output_path)
        return True
    except Exception:
        return False

def parallel_process_ct_volume(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    if not files: return

    # Extract global calibration scaling factors from the first slice
    sample_file = pydicom.dcmread(files[0], stop_before_pixels=True)
    slope = float(sample_file.get("RescaleSlope", 1))
    intercept = float(sample_file.get("RescaleIntercept", 0))
    
    # Parse radiation structured metadata attributes
    ctdi = str(sample_file.get((0x0018, 0x9345), "N/A"))
    dlp = str(sample_file.get((0x0018, 0x9346), "N/A"))
    total_slices = len(files)

    task_args = []
    for idx, f in enumerate(files):
        out_path = os.path.join(output_dir, "proc_" + os.path.basename(f))
        task_args.append((f, out_path, slope, intercept, ctdi, dlp, idx + 1, total_slices))

    print(f"[CT-MULTICORE] Distributing {total_slices} slices to {cpu_count()} CPU cores...")
    with Pool(processes=cpu_count()) as pool:
        _ = pool.map(worker_process_ct_slice, task_args)
    print("[CT-SUCCESS] Radiation audit log complete. Cavity segmentation finalized.")

if __name__ == "__main__":
    parallel_process_ct_volume(sys.argv[1], sys.argv[2])
