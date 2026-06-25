#!/usr/bin/env python3
"""
Revolutionary Technology Company - Cross-Vendor Resampling Engine
CUDA-Accelerated 3D Volumetric Isotropic Interpolation.
Normalizes voxel grids between Siemens 3T, GE 1.5T, and Siemens Avanto scanners.
"""

import os
import sys
import pydicom
import numpy as np

try:
    import torch
    import torch.nn.functional as F
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None
    F = None
    CUDA_AVAILABLE = False

def resample_volume_cuda(volume: np.ndarray, current_spacing: tuple, target_spacing: tuple = (1.0, 1.0, 1.0)) -> np.ndarray:
    """Performs GPU-accelerated 3D trilinear interpolation on the voxel grid."""
    device = torch.device("cuda:0")
    
    # Calculate new spatial dimensions based on spacing ratios
    orig_shape = volume.shape
    scale_factors = [current_spacing[i] / target_spacing[i] for i in range(3)]
    new_shape = [int(round(orig_shape[i] * scale_factors[i])) for i in range(3)]
    
    # Cast NumPy matrix block to torch tensor and upload directly to RTX 6000 VRAM
    # Shape transformation required for PyTorch 3D interpolate: (Batch, Channel, Depth, Height, Width)
    tensor_vol = torch.from_numpy(volume.astype(np.float32)).to(device)
    tensor_vol = tensor_vol.unsqueeze(0).unsqueeze(0) 
    
    print(f"[GPU-RESAMPLE] Interpolating voxel grid size from {orig_shape} to {tuple(new_shape)}...")
    
    # Execute hardware-accelerated 3D trilinear sampling
    resampled_tensor = F.interpolate(
        tensor_vol, 
        size=new_shape, 
        mode="trilinear", 
        align_corners=False
    )
    
    # Extract tensor from VRAM back to host RAM
    resampled_volume = resampled_tensor.squeeze(0).squeeze(0).cpu().numpy()
    torch.cuda.synchronize()
    
    return resampled_volume.astype(np.int16)

def resample_volume_cpu(volume: np.ndarray, current_spacing: tuple, target_spacing: tuple = (1.0, 1.0, 1.0)) -> np.ndarray:
    """CPU fallback using basic numpy matrix interpolation if CUDA stack is down."""
    from scipy.ndimage import zoom
    scale_factors = [current_spacing[i] / target_spacing[i] for i in range(3)]
    print(f"[CPU-RESAMPLE] Falling back to CPU interpolation for grid shape: {volume.shape}...")
    return zoom(volume, scale_factors, order=1).astype(np.int16)

def run_resampling_pipeline(input_dir: str, output_dir: str):
    """Parses a multi-slice folder volume, resamples spatial scaling, and generates isotropic outputs."""
    print(f"[RESAMPLE] Reading raw vendor slices inside: {input_dir}")
    
    slices = []
    for f in os.listdir(input_dir):
        path = os.path.join(input_dir, f)
        if os.path.isfile(path):
            try:
                slices.append(pydicom.dcmread(path))
            except pydicom.errors.InvalidDicomError:
                continue

    if not slices:
        print("[RESAMPLE-ERROR] No valid DICOM structures identified.")
        return False

    # Sort files chronologically along the spatial positioning axis
    slices.sort(key=lambda x: float(x.SliceLocation) if "SliceLocation" in x else 0)
    
    # Extract physical scanner scale resolutions
    sample = slices[0]
    pixel_spacing = sample.get("PixelSpacing", [1.0, 1.0])
    slice_thickness = sample.get("SliceThickness", 1.0)
    
    # Current spacing map layout: (Z-spacing, Y-spacing, X-spacing)
    current_spacing = (float(slice_thickness), float(pixel_spacing[0]), float(pixel_spacing[1]))
    target_spacing = (1.0, 1.0, 1.0) # Isotropic 1mm bounding goal
    
    # Reassemble matrix volume
    rows, cols = int(sample.Rows), int(sample.Columns)
    num_slices = len(slices)
    volume_matrix = np.zeros((num_slices, rows, cols), dtype=np.int16)
    
    for i, s in enumerate(slices):
        volume_matrix[i, :, :] = s.pixel_array

    # Trigger spatial interpolation routing
    if CUDA_AVAILABLE and F is not None:
        resampled_vol = resample_volume_cuda(volume_matrix, current_spacing, target_spacing)
    else:
        resampled_vol = resample_volume_cpu(volume_matrix, current_spacing, target_spacing)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save calculated isotropic volume blocks as a new uniform series loop
    # Using the baseline header metadata structure from the original scan series
    for i in range(resampled_vol.shape[0]):
        out_ds = pydicom.dcmread(os.path.join(input_dir, os.listdir(input_dir)[0])) # Clone base layout
        out_ds.Rows, out_ds.Columns = resampled_vol.shape[1], resampled_vol.shape[2]
        out_ds.PixelData = resampled_vol[i, :, :].tobytes()
        out_ds.PixelSpacing = [1.0, 1.0]
        out_ds.SliceThickness = 1.0
        out_ds.SliceLocation = i * 1.0
        out_ds.InstanceNumber = i + 1
        out_ds.SeriesDescription = f"ISOTROPIC_1MM_RTX6000"
        
        out_ds.save_as(os.path.join(output_dir, f"isotropic_slice_{i:04d}.dcm"))

    print(f"[RESAMPLE-SUCCESS] Isotropic processing completed. Normalized scans written to: {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python resample_volume.py <input_series_dir> <output_series_dir>")
        sys.exit(1)
    run_resampling_pipeline(sys.argv[1], sys.argv[2])
