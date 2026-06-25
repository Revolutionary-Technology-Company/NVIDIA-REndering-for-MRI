#!/usr/bin/env python3
"""
Revolutionary Technology Company - Medical AI Gateway Wrapper
Validates and forwards incoming MRI scans to FDA-cleared third-party AI engines
(e.g., SubtleMR / DeepResolve) hosted locally on our NVIDIA RTX 6000 infrastructure.
"""

import os
import sys
import pydicom
import requests

# Simulated Local AI Vendor REST API endpoint running via NVIDIA Triton/IGX Stack
AI_VENDOR_API_URL = "http://localhost:8501/v1/models/fda_mri_recon:predict"

def inspect_and_route_scan(input_path: str, output_path: str):
    """
    Validates scan parameters for sequences that benefit most from deep-learning denoising
    (e.g., Fast T2-Weighted or T1-weighted structural brain protocols).
    """
    try:
        ds = pydicom.dcmread(input_path)
        
        # Extract foundational DICOM metadata fields safely
        modality = ds.get("Modality", "UNKNOWN")
        sequence = ds.get("SequenceName", "UNKNOWN")
        manufacturer = ds.get("Manufacturer", "UNKNOWN")
        
        if modality != "MR":
            print(f"[GATEWAY-SKIP] Non-MRI data rejected: {os.path.basename(input_path)}")
            return False

        print(f"[GATEWAY-INGEST] Processing {manufacturer} scan file. Pulse Sequence: {sequence}")

        # Package raw uncompressed pixel data matrices for third-party inference container
        raw_pixels = ds.pixel_array.astype(float).tolist()
        payload = {
            "inputs": [
                {"name": "mri_raw_voxels", "shape": list(ds.pixel_array.shape), "datatype": "FP32", "data": raw_pixels}
            ]
        }

        # Dispatch transmission to the local vendor AI engine running on our RTX 6000 hardware
        print(f"[GATEWAY-FORWARD] Transmitting raw matrices to FDA-cleared inference stack...")
        response = requests.post(AI_VENDOR_API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            ai_data = response.json()
            # Extract corrected, denoised/sharpened matrix payload from vendor response
            processed_pixels = ai_data["outputs"][0]["data"]
            
            # Cast back safely to clinical unsigned 16-bit format
            enhanced_array = pydicom.pixel_data_handlers.util.convert_pixel_data(processed_pixels)
            ds.PixelData = enhanced_array.tobytes()
            
            # Tag header so Cloud PACS recognizes the AI augmentation event
            ds.ImageComments = "AI-ENHANCED_RECONSTRUCTION_RTX6000"
            ds.save_as(output_path)
            print(f"[GATEWAY-SUCCESS] Enhanced scan file written safely -> {output_path}")
            return True
        else:
            print(f"[GATEWAY-ERROR] Vendor AI engine returned status error code: {response.status_code}")
            return False

    except Exception as e:
        print(f"[GATEWAY-CRITICAL] Pipeline transmission routing failure: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python route_to_ai_recon.py <input.dcm> <output.dcm>")
        sys.exit(1)
    inspect_and_route_scan(sys.argv[1], sys.argv[2])
