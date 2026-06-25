# Tutorial 4: Computed Tomography (CT) Dose Audit & Lung Cavity Segmenter

This guide details the deployment of the automated CT processing track designed for high-slice count datasets coming from the **Siemens Force ED Dual-Source**, **Siemens Definition AS+**, and **GE Acute 16-Row** scanners.

## 🏗️ Technical Pipeline Workflow

[ED CT Console] ──(Dose & Slice Push)──> [Orthanc Listener]\
│\
(Hounsfield Scaling Pass)\
▼\
[Cloud PACS] <──(Masked Volume C-STORE)── [RTX 6000 Ada Core Registers]

## 📋 Modality Functional Specifications
CT volume scans can generate hundreds of high-resolution 512x512 matrix slices simultaneously. This pipeline reads vendor-specific rescale slope/intercept parameters, converts the uncompressed pixels into physical **Hounsfield Units (HU)**, and offloads them to the RTX 6000 Ada GPU. It applies a mathematical mask matching air tissue densities (`-900 HU` to `-400 HU`) to isolate lung air paths while logging radiation exposure metrics.

## 🚀 Setup Steps

### Step 1: Register Target Radiation Tags
The script evaluates the DICOM Radiation Dose Structured Report (RDSR) parameters to log patient exposure trends. Ensure your local configuration files match standard CTDIvol and Dose Length Product (DLP) metadata flags:
* **Tag `(0x0018, 0x9345)`**: Computed Tomography Dose Index (`CTDIvol`)
* **Tag `(0x0018, 0x9346)`**: Dose Length Product (`DLP`)

### Step 2: Configure Emergency Department Router Filters
Because your Siemens Force and Definition AS+ scanners are located near trauma resuscitation paths, optimization configurations inside `config/router.json` scale the application concurrency limit to prioritize speed:
```json
"ConcurrentJobs": 8,
"AcceptedTransferSyntaxes": [ "1.2.840.10008.1.2.1" ]
```

### Step 3: Run Validation Operations
To verify the CT matrix execution path without connecting live diagnostic equipment, trigger the synthetic pipeline validation model manually:
```bash
python3 -m unittest tests.test_pipeline.TestMultiModalityPipelineE2E.test_ct_pipeline_execution
```

---

## 🔒 Radiation Dose Auditing Compliance
The script appends all extracted `DLP` and `CTDIvol` parameters to `metrics.json`. These numbers feed directly into the intranet dashboard on port `9920` to meet institutional clinical quality assurance and radiation dose tracking policies.
