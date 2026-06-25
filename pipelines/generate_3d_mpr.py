#!/usr/bin/env python3
"""
Revolutionary Technology Company - Advanced 3D Voxel Reformat Engine
Processes 2D MRI slices into a unified 3D matrix. Generates Multi-Planar 
Reformats (MPR) using high-performance matrix manipulation.
"""

import os
import sys
import pydicom
import numpy as np

def build_3d_mpr_volume(input_dir: str, output_dir: str):
    """Parses individual slices to generate orthogonal planes from 3D voxel block arrays."""
    print(f"[3D-ENGINE] Scanning structural inputs inside: {input_dir}")
    
    # Read files and sort by slice location to ensure volume continuity
    slices = []
    for f in os.listdir(input_dir):
        path = os.path.join(input_dir, f)
        if os.path.isfile(path):
            try:
                slices.append(pydicom.dcmread(path))
            except pydicom.errors.InvalidDicomError:
                continue

    if not slices:
        print("[3D-ENGINE-ERROR] Zero valid medical DICOM elements extracted.")
        return False

    # Sort slices chronologically by spatial positioning axis
    slices.sort(key=lambda x: float(x.SliceLocation) if "SliceLocation" in x else 0)
    
    # Extract dimensions to assemble matrix array bounds
    sample_slice = slices[0]
    rows = int(sample_slice.Rows)
    cols = int(sample_slice.Columns)
    num_slices = len(slices)
    
    print(f"[3D-ENGINE] Reassembling unified spatial voxel grid: ({rows} x {cols} x {num_slices})")
    
    # Construct unified 3D NumPy matrix
    voxel_3d = np.zeros((rows, cols, num_slices), dtype=np.int16)
    for i, s in enumerate(slices):
        voxel_3d[:, :, i] = s.pixel_array

    # Generate Coronal and Sagittal volumetric plane reformats via array axis rotations
    print("[3D-ENGINE] Calculating Orthogonal Multi-Planar Reformats (MPR)...")
    coronal_view = voxel_3d[:, cols // 2, :]   # Extracted Coronal Plane slice slice
    sagittal_view = voxel_3d[rows // 2, :, :]  # Extracted Sagittal Plane slice slice

    # Create destination block path
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save calculated views as independent 2D structural arrays to upload to your Cloud PACS
    np.save(os.path.join(output_dir, "mpr_coronal_plane.npy"), coronal_view)
    np.save(os.path.join(output_dir, "mpr_sagittal_plane.npy"), sagittal_view)
    
    print(f"[3D-ENGINE-SUCCESS] Volumetric Multi-Planar matrices exported successfully to: {output_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_3d_mpr.py <input_volume_dir> <output_matrix_dir>")
        sys.exit(1)
    build_3d_mpr_volume(sys.argv[1], sys.argv[2])
