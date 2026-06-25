#!/usr/bin/env python3
"""
Revolutionary Technology Company - MRI Pipeline Unit Tests
Automated validation testing for all five image-processing stages.
Designed to execute inside local development contexts and GitHub Actions CI.
"""

import os
import sys
import unittest
import shutil
import numpy as np
import pydicom
from pydicom.dataset import FileMetaDataset, Dataset

# Ensure scripts can import pipeline files locally if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMRIPipelineE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Build isolation sandbox directories and synthetic test matrices."""
        cls.test_root = "/tmp/mri_pipeline_test_sandbox"
        cls.watch_dir = os.path.join(cls.test_root, "incoming_dicom")
        cls.stage_classify = os.path.join(cls.test_root, "stage_classified")
        cls.stage_resample = os.path.join(cls.test_root, "stage_resampled")
        cls.stage_final = os.path.join(cls.test_root, "processed_output")
        cls.metrics_file = os.path.join(cls.test_root, "metrics.json")
        cls.qa_log = os.path.join(cls.test_root, "qa_audit.json")

        # Clean workspace anomalies if a previous test run crashed
        if os.path.exists(cls.test_root):
            shutil.rmtree(cls.test_root)

        os.makedirs(cls.watch_dir)

        # ----------------------------------------------------------------------
        # SYNTHETIC DICOM MATRIX GENERATION
        # Generates 5 valid synthetic slices to simulate a scanner transmission
        # ----------------------------------------------------------------------
        print("\n[TEST-SETUP] Fabricating synthetic structural MR data layers...")
        for i in range(5):
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'  # MR Image Storage
            file_meta.MediaStorageSOPInstanceUID = f"1.2.3.4.5.6.7.{i}"
            file_meta.ImplementationClassUID = '1.2.3.4.5.6'
            file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'  # Explicit VR Little Endian

            ds = Dataset()
            ds.file_meta = file_meta
            ds.is_little_endian = True
            ds.is_implicit_VR = False

            # Add core clinical metadata fields required by our pipeline
            ds.PatientName = "TEST^PATIENT"
            ds.PatientID = "PT-99402"
            ds.Modality = "MR"
            ds.Manufacturer = "SIEMENS"
            ds.SeriesDescription = "Axial T2 TSE"
            ds.SequenceName = "t2_tse_ax"
            ds.EchoTime = 90.0
            ds.RepetitionTime = 4000.0
            ds.SliceLocation = i * 2.5
            ds.SliceThickness = 2.5
            ds.PixelSpacing = [0.5, 0.5]
            ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0] # Standard Axial Plane Vector
            ds.InstanceNumber = i + 1

            # Generate synthetic 2D imaging voxels (with an isolated mock face structure)
            pixel_matrix = np.ones((128, 128), dtype=np.uint16) * 500
            pixel_matrix[40:80, :40] = 2000  # Inject mock high-intensity tissue anomaly
            ds.Rows, ds.Columns = pixel_matrix.shape
            ds.PixelData = pixel_matrix.tobytes()

            ds.save_as(os.path.join(cls.watch_dir, f"slice_{i:03d}.dcm"), write_like_original=False)

    @classmethod
    def tearDownClass(cls):
        """Purge all temporary testing sandboxes to keep the system storage pristine."""
        print("\n[TEST-TEARDOWN] Flushing temporary evaluation sandboxes...")
        if os.path.exists(cls.test_root):
            shutil.rmtree(cls.test_root)

    def test_stage1_classification(self):
        """Validates that erratic names resolve to clean hanging protocol directories."""
        from pipelines.classify_series import sort_and_classify_study
        print("\n[TEST] Executing Stage 1: Protocol Classification Verification...")
        
        success = sort_and_classify_study(self.watch_dir, self.stage_classify)
        self.assertTrue(success)
        
        # Verify standardized subfolder tree architecture was constructed properly
        expected_folder = os.path.join(self.stage_classify, "AXIAL_T2")
        self.assertTrue(os.path.isdir(expected_folder))
        self.assertGreater(len(os.listdir(expected_folder)), 0)

    def test_stage2_qa_artifact_detection(self):
        """Verifies that pristine synthetic matrix arrays successfully clear QA thresholds."""
        from pipelines.detect_artifacts import run_artifact_detection_pipeline
        print("\n[TEST] Executing Stage 2: Fast Fourier Transform QA Analytics Verification...")
        
        source_target = os.path.join(self.stage_classify, "AXIAL_T2")
        is_corrupted = run_artifact_detection_pipeline(source_target, self.qa_log)
        
        # Pristine data shapes should not be flagged for re-scans
        self.assertFalse(is_corrupted)
        self.assertTrue(os.path.exists(self.qa_log))

    def test_stage3_isotropic_resampling(self):
        """Checks that 3D matrix scaling reshapes slice configurations cleanly."""
        from pipelines.resample_volume import run_resampling_pipeline
        print("\n[TEST] Executing Stage 3: Isotropic 1mm Volumetric Resampling Verification...")
        
        source_target = os.path.join(self.stage_classify, "AXIAL_T2")
        success = run_resampling_pipeline(source_target, self.stage_resample)
        self.assertTrue(success)
        self.assertGreater(len(os.listdir(self.stage_resample)), 0)

    def test_stage4_spatial_defacing(self):
        """Verifies that privacy filters successfully overwrite facial quadrant zones."""
        from pipelines.deface_volume import process_defacing_pipeline
        print("\n[TEST] Executing Stage 4: Volumetric Face-Plane De-identification Verification...")
        
        success = process_defacing_pipeline(self.stage_resample, self.stage_final)
        self.assertTrue(success)
        
        # Sample an output slice file matrix block to verify voxels were zeroed out
        sample_out_file = os.path.join(self.stage_final, "defaced_0000.dcm")
        self.assertTrue(os.path.exists(sample_out_file))
        
        ds = pydicom.dcmread(sample_out_file)
        # Check that the front facial segment columns are cleanly zeroed out by the script
        self.assertEqual(ds.pixel_array[0, 0], 0)

    def test_stage5_auditing_and_dashboard_generation(self):
        """Ensures system logging files compile formatting configurations properly."""
        from pipelines.track_metrics import log_audit_metrics
        from pipelines.generate_dashboard import generate_html_dashboard
        print("\n[TEST] Executing Stage 5: Auditable Logging and Monitoring Verification...")
        
        # Override destination file strings to write cleanly inside the sandbox environment block
        import pipelines.track_metrics
        import pipelines.generate_dashboard
        pipelines.track_metrics.METRICS_FILE = self.metrics_file
        pipelines.generate_dashboard.METRICS_FILE = self.metrics_file
        pipelines.generate_dashboard.HTML_OUTPUT_FILE = os.path.join(self.test_root, "dashboard.html")

        # Mock log entry write
        log_audit_metrics("SUCCESS", 5, 1.420, "")
        self.assertTrue(os.path.exists(self.metrics_file))

        # Compile HTML presentation layers
        generate_html_dashboard()
        self.assertTrue(os.path.exists(pipelines.generate_dashboard.HTML_OUTPUT_FILE))

if __name__ == "__main__":
    unittest.main()
