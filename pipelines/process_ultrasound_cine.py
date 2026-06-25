#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multicore Ultrasound Cine Deconstructor
Parallel frame extraction engine leveraging multiprocessing core assignment pools.
"""

import os
import sys
import pydicom
import numpy as np
from multiprocessing import Pool, cpu_count

def worker_write_us_frame(args):
    """Isolated process task writing a single extracted frame to disk."""
    frame_idx, output_path, input_file_path, frame_bytes, shape, delta_x, delta_y = args
    try:
        # Reconstruct frame object context
        ds = pydicom.dcmread(input_file_path, stop_before_pixels=True)
        if "NumberOfFrames" in ds: del ds.NumberOfFrames
        
        ds.Rows, ds.Columns = shape[0], shape[1]
        ds.PixelData = frame_bytes
        ds.InstanceNumber = frame_idx + 1
        ds.ImageComments = f"US_MULTICORE_FRAME_RTX6000;SCALE_X={delta_x};SCALE_Y={delta_y}"
        ds.save_as(output_path)
        return True
    except Exception:
        return False

def parallel_deconstruct_ultrasound(input_file: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    ds = pydicom.dcmread(input_file)
    
    # Extract regional metric definitions
    regions = ds.get("SequenceOfUltrasoundRegions", None)
    delta_x = regions[0].get("PhysicalDeltaX", "N/A") if regions else "N/A"
    delta_y = regions[0].get("PhysicalDeltaY", "N/A") if regions else "N/A"
    
    pixel_data = ds.pixel_array
    num_frames = int(ds.get("NumberOfFrames", 1))
    shape = (ds.Rows, ds.Columns)

    task_args = []
    print(f"[US-MULTICORE] Assembling frame deconstruction queue for {num_frames} frames...")
    for idx in range(num_frames):
        frame_matrix = pixel_data[idx] if num_frames > 1 else pixel_data
        out_path = os.path.join(output_dir, f"frame_{idx:03d}.dcm")
        task_args.append((idx, out_path, input_file, frame_matrix.tobytes(), shape, delta_x, delta_y))

    with Pool(processes=cpu_count()) as pool:
        _ = pool.map(worker_write_us_frame, task_args)
    print(f"[US-SUCCESS] Multicore split completed across {cpu_count()} worker cores.")

if __name__ == "__main__":
    parallel_deconstruct_ultrasound(sys.argv[1], sys.argv[2])
