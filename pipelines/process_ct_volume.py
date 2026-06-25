#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multicore CT Dose Audit & Lung Segmenter
Asynchronous multiprocess I/O pipeline with parallel CUDA stream thresholding.
"""

import os
import sys
import time
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
    """Isolated worker process to scale, threshold, and save a single CT slice."""
    input_path, output_path, slope, intercept, ctdi, dlp = args
    try:
        start_time = time.time()
        ds = pydicom.dcmread(input_path)
        if ds.get("Modality") != "CT":
            return False, "Skipped non-CT file"

        # Extract raw voxel matrix and scale to Hounsfield Units (HU)
        pixel_array = ds.pixel_array.astype(np.float32)
        hu_array = (pixel_array * slope) + intercept

        if CUDA_AVAILABLE:
            device = torch.device("cuda:0")
            stream = torch.cuda.Stream(device=device)
            with torch.cuda.stream(stream):
                tensor_slice = torch.from_numpy(hu_array).to(device, non_blocking=True)
                # Create lung mask threshold loop (-900 HU to -400 HU)
                mask = (tensor_slice >= -900) & (tensor_slice <= -400)
                segmented_tensor = torch.where(mask, tensor_slice, torch.tensor(0.0, device=device))
                
                # Convert back to raw scanner integer space
                final_tensor = (segmented_tensor - intercept) / slope
                processed_pixels = final_tensor.cpu().numpy()
            stream.synchronize()
        else:
            segmented_hu = np.where((hu_array >= -900) & (hu_array <= -400), hu_array, 0)
            processed_pixels = (segmented_hu - intercept) / slope

        # Save slice data back to file disk
        processed_pixels = np.clip(processed_pixels, 0, 65535).astype(np.uint16)
        ds.PixelData = processed_pixels.tobytes()
        ds.ImageComments = f"CT_MULTICORE_SEGMENTED_RTX6000;CTDI={ctdi};DLP={dlp}"
        ds.save_as(output_path)
        
        return True, f"Processed CT slice in {time.time() - start_time:.4f}s"
    except Exception as e:
        return False, str(e)

def parallel_process_ct_volume(input_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    if not files: return

    # Extract sample metadata to apply global vendor calibration constants
    sample = pydicom.dcmread(files[0], stop_before_pixels=True)
    slope = float(sample.get("RescaleSlope", 1))
    intercept = float(sample.get("RescaleIntercept", 0))
    ctdi = str(sample.get((0x0018, 0x9345), "N/A"))
    dlp = str(sample.get((0x0018, 0x9346), "N/A"))

    task_args = []
    for f in files:
        out_f = os.path.join(output_dir, "segmented_" + os.path.basename(f))
        task_args.append((f, out_f, slope, intercept, ctdi, dlp))

    print(f"[CT-MULTICORE] Distributing {len(files)} slices across {cpu_count()} CPU cores...")
    with Pool(processes=cpu_count()) as pool:
        _ = pool.map(worker_process_ct_slice, task_args)

if __name__ == "__main__":
    parallel_process_ct_volume(sys.argv[1], sys.argv[2])
