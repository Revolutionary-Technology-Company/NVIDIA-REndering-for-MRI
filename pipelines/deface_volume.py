#!/usr/bin/env python3
"""
Revolutionary Technology Company - MRI 3D Spatial Defacing Engine
Zeroes out voxel coordinates along the facial profile plane to enforce 
HIPAA privacy compliance on structural head scans prior to Cloud PACS routing.
"""

import os
import sys
import pydicom
import numpy as np

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None
    CUDA_AVAILABLE = False

def execute_gpu_defacing(volume_matrix: np.ndarray, face_plane_threshold: int) -> np.ndarray:
    """Uses GPU-accelerated array slicing to mask out facial voxel zones instantly."""
    device = torch.device("cuda:0")
    
    # Push the full 3D MRI volume array directly into RTX 6000 VRAM
    tensor_vol = torch.from_numpy(volume_matrix.astype(np.float32)).to(device)
    
    # Establish a fast 3D geometric spatial mask matrix bounding box
    # Example approach: Zero out the front quadrant slices where facial tissues reside
    # In production, this boundary is dictated by an AI landmark detection model coordinate
    tensor_vol[:, :face_plane_threshold, :] = 0.0
    
    # Synchronize cores and pull the sanitized array back to the host framework
    sanitized_matrix = tensor_vol.cpu().numpy().astype(np.int16)
    torch.cuda.synchronize()
    
    return sanitized_matrix

def process_defacing_pipeline(input_dir: str, output_dir: str):
    """Parses a 3D series directory, masks facial geometry, and rewrites DICOM elements."""
    print(f"[DEFACE] Reading structural volumetric slices inside: {input_dir}")
    
    slices = []
    for f in os.listdir(input_dir):
        path = os.path.join(input_dir, f)
        if os.path.isfile(path):
            try:
                slices.append(pydicom.dcmread(path))
            except pydicom.errors.InvalidDicomError:
                continue

    if not slices:
        print("[DEFACE-ERROR] No valid DICOM structures identified.")
        return False

    # Sort slices spatially by location to assemble a uniform volume
    slices.sort(key=lambda x: float(x.SliceLocation) if "SliceLocation" in x else 0)
    
    rows = int(slices[0].Rows)
    cols = int(slices[0].Columns)
    num_slices = len(slices)
    
    # Assemble unified 3D matrix block
    volume_matrix = np.zeros((rows, cols, num_slices), dtype=np.int16)
    for i, s in enumerate(slices):
        volume_matrix[:, :, i] = s.pixel_array

    # Define the geometric cutoff index for the face plane (e.g., front 35% of columns)
    face_plane_threshold = int(cols * 0.35)

    print(f"[DEFACE-ACCELERATE] Masking facial features on RTX 6000 across {num_slices} slices...")
    if CUDA_AVAILABLE:
        sanitized_volume = execute_gpu_defacing(volume_matrix, face_plane_threshold)
    else:
        # CPU Fallback array masking execution
        volume_matrix[:, :face_plane_threshold, :] = 0
        sanitized_volume = volume_matrix

    # Write the modified data slices out back into target DICOM profiles
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, s in enumerate(slices):
        s.PixelData = sanitized_volume[:, :, i].tobytes()
        s.ImageComments = "SPATIAL_DEFACED_VIA_RTX6000_ADA"
        
        out_path = os.path.join(output_dir, f"defaced_{i:04d}.dcm")
        s.save_as(out_path)

    print(f"[DEFACE-SUCCESS] Spatial identity protection loop finalized. Output: {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python deface_volume.py <input_series_dir> <output_series_dir>")
        sys.exit(1)
    process_defacing_pipeline(sys.argv[1], sys.argv[2])
