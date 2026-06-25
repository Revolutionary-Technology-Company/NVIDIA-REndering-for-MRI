#!/usr/bin/env python3
"""
Revolutionary Technology Company - Multi-Modality Pipeline Verification Engine
Comprehensive unit test harness validating MRI, CT, and Ultrasound pipelines.
Ensures zero continuous integration (CI) regressions across all system components.
"""

import os
import sys
import unittest
import shutil
import numpy as np
import pydicom
from pydicom.dataset import FileMetaDataset, Dataset

# Ensure scripts can import pipeline files locally
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMultiModalityPipelineE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Build isolation sandbox directories and synthetic multi-modality data layers."""
        cls.test_root = "/tmp/multimodality_pipeline_test_sandbox"
        cls.watch_dir = os.path.join(cls.test_root, "incoming_dicom")
        cls.stage_classify = os.path.join(cls.test_root, "stage_classified")
        cls.stage_resample = os.path.join(cls.test_root, "stage_resampled")
        cls.stage_final = os.path.join(cls.test_root, "processed_output")
        cls.metrics_file = os.path.join(cls.test_root, "metrics.json")
        cls.qa_log = os.path.join(cls.test_root, "qa_audit.json")

        if os.path.exists(cls.test_root):
            shutil.rmtree(cls.test_root)

        os.makedirs(cls.watch_dir)
        cls.generate_synthetic_mri()

    @classmethod
    def tearDownClass(cls):
        """Purge temporary files to maintain host system storage cleanliness."""
        print("\n[TEST-TEARDOWN] Flushing multi-modality validation sandboxes...")
        if os.path.exists(cls.test_root):
            shutil.rmtree(cls.test_root)

    @classmethod
    def generate_synthetic_mri(cls):
        """Fabricates mock 3D MRI series data layer structures."""
        print("\n[TEST-SETUP] Fabricating structural MRI test series...")
        for i in range(5):
            ds = cls.create_base_dicom(i, modality="MR")
            ds.PatientName = "TEST^MRI^PATIENT"
            ds.SeriesDescription = "Axial T2 TSE"
            ds.SequenceName = "t2_tse_ax"
            ds.EchoTime = 90.0
            ds.RepetitionTime = 4000.0
            ds.SliceLocation = i * 2.5
            ds.SliceThickness = 2.5
            ds.PixelSpacing = [0.5, 0.5]
            ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
            
            pixel_matrix = np.ones((128, 128), dtype=np.uint16) * 500
            pixel_matrix[40:80, :40] = 2000
            ds.Rows, ds.Columns = pixel_matrix.shape
            ds.PixelData = pixel_matrix.tobytes()
            ds.save_as(os.path.join(cls.watch_dir, f"mri_slice_{i:03d}.dcm"), write_like_original=False)

    @classmethod
    def create_base_dicom(cls, index, modality="MR"):
        """Utility wrapper establishing standard clinical DICOM header envelopes."""
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
        file_meta.MediaStorageSOPInstanceUID = f"1.2.3.4.5.6.7.{modality}.{index}"
        file_meta.ImplementationClassUID = '1.2.3.4.5.6'
        file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'

        ds = Dataset()
        ds.file_meta = file_meta
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.Modality = modality
        ds.PatientID = f"PT-{modality}-99"
        ds.InstanceNumber = index + 1
        return ds

    def test_mri_pipeline_execution(self):
        """Validates classification, artifact checking, and 3D resampling profiles for MRI."""
        from pipelines.classify_series import sort_and_classify_study
        from pipelines.detect_artifacts import run_artifact_detection_pipeline
        from pipelines.resample_volume import run_resampling_pipeline
        from pipelines.deface_volume import process_defacing_pipeline

        print("\n[TEST] Verifying MRI End-to-End Execution Sequence...")
        
        # 1. Classification
        self.assertTrue(sort_and_classify_study(self.watch_dir, self.stage_classify))
        
        # 2. Fast Fourier Transform QA check
        mri_target_path = os.path.join(self.stage_classify, "AXIAL_T2")
        self.assertFalse(run_artifact_detection_pipeline(mri_target_path, self.qa_log))
        
        # 3. Isotropic Resampling
        self.assertTrue(run_resampling_pipeline(mri_target_path, self.stage_resample))
        
        # 4. Spatial Defacing
        self.assertTrue(process_defacing_pipeline(self.stage_resample, self.stage_final))

    def test_ct_pipeline_execution(self):
        """Validates radiation index parsing and Hounsfield Unit (HU) isolation for CT logs."""
        from pipelines.process_ct_volume import run_ct_pipeline
        print("\n[TEST] Verifying CT Radiation Audit & Segmentation Sequence...")
        
        ct_input_dir = os.path.join(self.test_root, "ct_input")
        ct_output_dir = os.path.join(self.test_root, "ct_output")
        os.makedirs(ct_input_dir)

        # Build structural synthetic CT file slice containing explicit vendor dose metadata
        ds = self.create_base_dicom(0, modality="CT")
        ds.PatientName = "TEST^CT^PATIENT"
        ds.Rows, ds.Columns = 128, 128
        ds.RescaleSlope = "1"
        ds.RescaleIntercept = "-1024"
        ds.add_new((0x0018, 0x9345), "DS", "15.4")   # CTDIvol parameter element
        ds.add_new((0x0018, 0x9346), "DS", "450.2")  # DLP parameter element
        
        # Simulate air voxel metrics inside lung zone (-700 HU after slope shift)
        ct_pixels = np.ones((128, 128), dtype=np.int16) * 324
        ds.PixelData = ct_pixels.tobytes()
        ds.save_as(os.path.join(ct_input_dir, "ct_slice.dcm"), write_like_original=False)

        # Trigger execution runtime logic check
        run_ct_pipeline(ct_input_dir, ct_output_dir)
        self.assertTrue(os.path.exists(os.path.join(ct_output_dir, "segmented_ct_0000.dcm")))

    def test_us_pipeline_execution(self):
        """Validates frame extraction array tracking and ultrasound spatial calibrations."""
        from pipelines.process_ultrasound_cine import process_ultrasound_file
        print("\n[TEST] Verifying Ultrasound Multi-Frame Cine Deconstruction...")
        
        us_input_dir = os.path.join(self.test_root, "us_input")
        us_output_dir = os.path.join(self.test_root, "us_output")
        os.makedirs(us_input_dir)

        ds = self.create_base_dicom(0, modality="US")
        ds.PatientName = "TEST^US^PATIENT"
        ds.NumberOfFrames = "3"
        ds.Rows, ds.Columns = 64, 64
        
        # Formulate spatial calibration sub-sequence structures
        region_ds = Dataset()
        region_ds.PhysicalDeltaX = 0.15
        region_ds.PhysicalDeltaY = 0.15
        ds.SequenceOfUltrasoundRegions = [region_ds]

        # Generate a multi-frame 3D matrix block simulating a cine-loop clip
        us_video_block = np.ones((3, 64, 64), dtype=np.uint8) * 128
        ds.PixelData = us_video_block.tobytes()
        
        us_file_path = os.path.join(us_input_dir, "us_cine.dcm")
        ds.save_as(us_file_path, write_like_original=False)

        # Trigger extraction loop execution verification check
        self.assertTrue(process_ultrasound_file(us_file_path, us_output_dir))
        self.assertEqual(len(os.listdir(us_output_dir)), 3)

    def test_multimodality_metrics_and_dashboard_compilation(self):
        """Enforces validation testing on multi-modality data compilation logs."""
        from pipelines.track_metrics import log_audit_metrics
        from pipelines.generate_dashboard import generate_html_dashboard
        print("\n[TEST] Verifying Multi-Modality Audit Logging & Metrics Compilation...")

        # Inject testing paths to shield active production logs
        import pipelines.track_metrics
        import pipelines.generate_dashboard
        pipelines.track_metrics.METRICS_FILE = self.metrics_file
        pipelines.generate_dashboard.METRICS_FILE = self.metrics_file
        pipelines.generate_dashboard.HTML_OUTPUT_FILE = os.path.join(self.test_root, "dashboard.html")

        # Sequentially write mock audit entries using the new 5-argument syntax mapping parameters
        log_audit_metrics("SUCCESS", 160, 2.451, "MR", "")
        log_audit_metrics("SUCCESS", 512, 4.102, "CT", "")
        log_audit_metrics("FAILURE", 90, 0.812, "US", "Cine loop array frame extraction timeout error.")

        self.assertTrue(os.path.exists(self.metrics_file))

        # Compile presentation files
        generate_html_dashboard()
        self.assertTrue(os.path.exists(pipelines.generate_dashboard.HTML_OUTPUT_FILE))

if __name__ == "__main__":
    unittest.main()
