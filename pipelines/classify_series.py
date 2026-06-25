#!/usr/bin/env python3
"""
Revolutionary Technology Company - MRI Series Classification Engine
Standardizes erratic GE & Siemens pulse sequence naming conventions into uniform 
hanging protocols based on physical DICOM metadata constraints and orientation vectors.
"""

import os
import sys
import pydicom
import numpy as np

def determine_spatial_orientation(image_orientation_patient):
    """
    Analyzes the directional cosine vectors of the slice plane 
    to classify the spatial orientation (Axial, Coronal, Sagittal).
    """
    if not image_orientation_patient or len(image_orientation_patient) < 6:
        return "UNKNOWN_PLANE"
    
    # Extract orientation directional cosines
    row_cos = np.array(image_orientation_patient[0:3])
    col_cos = np.array(image_orientation_patient[3:6])
    
    # Compute the cross product to get the slice normal vector
    normal = np.cross(row_cos, col_cos)
    abs_normal = np.abs(normal)
    
    max_index = np.argmax(abs_normal)
    if max_index == 0:
        return "SAGITTAL"
    elif max_index == 1:
        return "CORONAL"
    elif max_index == 2:
        return "AXIAL"
    return "UNKNOWN_PLANE"

def classify_pulse_sequence(te, tr, ti, sequence_name):
    """
    Classifies tissue weight contrast using standard physics rules:
    - T1-Weighted: Short TR (< 800ms), Short TE (< 30ms)
    - T2-Weighted: Long TR (> 2000ms), Long TE (> 80ms)
    - PD-Weighted: Long TR (> 2000ms), Short TE (< 30ms)
    - FLAIR: Long TR, Long TE, and presence of Inversion Time (~1800-2500ms)
    """
    # Clean sequence string checks for explicit vendor naming patterns
    seq_str = str(sequence_name).upper()
    if "FLAIR" in seq_str or "IR" in seq_str:
        if ti and float(ti) > 1000:
            return "FLAIR"

    if tr and te:
        tr_val = float(tr)
        te_val = float(te)
        
        if tr_val < 800 and te_val < 30:
            return "T1"
        elif tr_val > 2000 and te_val > 80:
            return "T2"
        elif tr_val > 2000 and te_val < 40:
            return "PD"
            
    # Fallback heuristic flags if explicit numerical tags are missing
    if "T1" in seq_str: return "T1"
    if "T2" in seq_str: return "T2"
    
    return "STRUCTURAL_MISC"

def sort_and_classify_study(input_dir: str, output_base_dir: str):
    """Parses incoming folder paths, classifies files, and standardizes file trees."""
    print(f"[CLASSIFY] Ingesting files from directory: {input_dir}")
    
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)

    processed_count = 0
    
    for root_dir, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root_dir, file)
            try:
                ds = pydicom.dcmread(file_path, stop_before_pixels=True) # Fast meta-only read
                
                if ds.get("Modality") != "MR":
                    continue
                
                # Fetch key imaging physics parameters
                te = ds.get("EchoTime")
                tr = ds.get("RepetitionTime")
                ti = ds.get("InversionTime")
                seq_name = ds.get("SequenceName", ds.get("SeriesDescription", "UNKNOWN"))
                orientation_vectors = ds.get("ImageOrientationPatient")

                # Run classification algorithms
                contrast_type = classify_pulse_sequence(te, tr, ti, seq_name)
                plane_type = determine_spatial_orientation(orientation_vectors)
                
                # Formulate structural naming target path
                standardized_protocol = f"{plane_type}_{contrast_type}"
                target_destination_dir = os.path.join(output_base_dir, standardized_protocol)
                
                if not os.path.exists(target_destination_dir):
                    os.makedirs(target_destination_dir)

                # Re-load full DICOM data payload to copy physical data over safely
                full_ds = pydicom.dcmread(file_path)
                
                # Update header metadata with uniform standardized descriptors
                full_ds.SeriesDescription = standardized_protocol
                full_ds.ProtocolName = standardized_protocol
                full_ds.ImageComments = f"CLASSIFIED_BY_RTX6000_NODE; ORIG_NAME={seq_name}"
                
                destination_file_path = os.path.join(target_destination_dir, file)
                full_ds.save_as(destination_file_path)
                processed_count += 1

            except Exception as e:
                print(f"[CLASSIFY-WARN] Skipping corrupt or unparseable element {file}: {str(e)}")
                continue

    print(f"[CLASSIFY-SUCCESS] Processed {processed_count} instances. Organized trees built inside: {output_base_dir}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python classify_series.py <input_unorganized_dir> <output_standardized_dir>")
        sys.exit(1)
        
    sort_and_classify_study(sys.argv, sys.argv)
