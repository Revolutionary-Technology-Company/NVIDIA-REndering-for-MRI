#!/usr/bin/env python3
"""
Revolutionary Technology Company - Ultrasound Cine-Loop Frame Extractor
Deconstructs multi-frame video blocks and verifies spatial calibration tags.
"""

import os
import sys
import pydicom
import numpy as np

def extract_ultrasound_metadata(ds: pydicom.dataset.Dataset):
    """Parses region calibration vectors to establish physical pixel measurements (mm/pixel)."""
    regions = ds.get("SequenceOfUltrasoundRegions", None)
    if regions:
        region = regions[0]
        physical_delta_x = region.get("PhysicalDeltaX", None)
        physical_delta_y = region.get("PhysicalDeltaY", None)
        return {"mm_per_pixel_x": physical_delta_x, "mm_per_pixel_y": physical_delta_y}
    return {"mm_per_pixel_x": "Unknown", "mm_per_pixel_y": "Unknown"}

def process_ultrasound_file(input_file: str, output_dir: str):
    print(f"[US-PIPELINE] Ingesting file: {input_file}")
    ds = pydicom.dcmread(input_file)
    
    if ds.get("Modality") != "US":
        print("[US-ERROR] File modality is not Ultrasound.")
        return False

    # Extract mm-per-pixel measurement parameters
    spatial_calibration = extract_ultrasound_metadata(ds)
    print(f"[US-CALIBRATION] Measured spatial scaling vectors: {spatial_calibration}")

    # Verify if file is a moving video clip (Cine-Loop) or a static frame
    num_frames = int(ds.get("NumberOfFrames", 1))
    print(f"[US-GEOMETRY] Located {num_frames} frames inside multi-frame video block.")

    pixel_data = ds.pixel_array
    os.makedirs(output_dir, exist_ok=True)

    # Deconstruct cine-loop frame allocations sequentially
    for frame_idx in range(num_frames):
        # Extract a single 2D image plane (Handles RGB Doppler color grids or Grayscale)
        if num_frames > 1:
            frame_matrix = pixel_data[frame_idx, :, :, :] if len(pixel_data.shape) == 4 else pixel_data[frame_idx, :, :]
        else:
            frame_matrix = pixel_data

        # Clone basic metadata structures to save independent image slices
        frame_ds = pydicom.dcmread(input_file)
        if "NumberOfFrames" in frame_ds:
            del frame_ds.NumberOfFrames
            
        frame_ds.Rows, frame_ds.Columns = frame_matrix.shape[0], frame_matrix.shape[1]
        frame_ds.PixelData = frame_matrix.tobytes()
        frame_ds.InstanceNumber = frame_idx + 1
        frame_ds.ImageComments = f"US_FRAME_EXTRACTED_RTX6000;SCALE_X={spatial_calibration['mm_per_pixel_x']}"
        
        output_file_path = os.path.join(output_dir, f"us_frame_{frame_idx:03d}.dcm")
        frame_ds.save_as(output_file_path)

    print(f"[US-SUCCESS] Deconstructed {num_frames} ultrasound loops into destination directory: {output_dir}")
    return True

if __name__ == "__main__":
    process_ultrasound_file(sys.argv[1], sys.argv[2])
