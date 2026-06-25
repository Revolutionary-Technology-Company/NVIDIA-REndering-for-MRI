# 📋 Clinical Deployment Verification & Sign-Off Checklist

**System:** Multi-Modality Enterprise Edge Hub (MRI / CT / US)  
**Target Installation Site:** [Insert Hospital Name/Clinic Site Code]  
**Deployment Date:** [Insert Date]  
**Lead Clinical Engineer:** [Insert Name]  

This checklist must be executed and signed off in full before transitioning a newly installed edge-compute node from staging into an active clinical production environment.

---

## 🛠️ Phase 1: Hardware & Physical Environment Verification
* [ ] **Physical Mounting:** The host system is securely mounted in the datacenter rack or placed in a dedicated climate-controlled server closet with adequate airflow.
* [ ] **Power Redundancy:** The server is plugged into an active Uninterruptible Power Supply (UPS) or backup emergency hospital power grid.
* [ ] **GPU Seating:** The NVIDIA RTX 6000 Ada is locked into a true PCIe Gen 4.0/5.0 x16 motherboard slot and connected via factory-approved power cables.
* [ ] **ECC Memory Check:** Run `nvidia-smi -q -d RESET` and verify that **Error Correction Code (ECC)** memory is reported as `Enabled` for both volatile and aggregate memory registers.

---

## 🔒 Phase 2: Network & Security Hardening Verification
* [ ] **VLAN Isolation:** Host system is registered on a dedicated, isolated Biomedical/Radiology equipment VLAN subnet.
* [ ] **Firewall Inbound Rules:** Confirmed that local port `11104` is open *only* to the IP addresses of the 14 authorized GE, Siemens, Philips, and Sonosite scanners.
* [ ] **Firewall Outbound Rules:** Confirmed that outbound port `443` is locked down to communicate exclusively with the destination URL of the secure Cloud PACS provider.
* [ ] **Dashboard Lock:** Attempt to access the dashboard on port `9920` from a machine outside the authorized hospital intranet (`10.0.0.0/8`). Verify the connection is dropped or returns an access error code.

---

## 🚀 Phase 3: Software & Pipeline Automation Verification
* [ ] **Pre-Flight Initialization:** Run `sudo ./setup.sh` on the host machine and confirm all stages (1 through 5) return a green `✅ SUCCESS` status tag.
* [ ] **Container Runtime State:** Run `docker compose ps` and verify all three core services report a healthy status:
  * `mri_edge_listener` (Up/Healthy)
  * `rtx6000_mri_worker` (Up/Healthy)
  * `mri_dashboard_server` (Up/Healthy)
* [ ] **Log Maintenance Check:** Confirm the system log file is initialized on the host disk and can accept append strings:
  * Path: `/var/log/mri_pipeline_daemon.log`

---

## 🧪 Phase 4: Multi-Modality Data Flow Test & Sign-Off
* [ ] **Synthetic Test Suit:** Run the continuous integration test harness inside the workspace:
  ```bash
  python3 tests/test_pipeline.py
  ```
  Verify that all multi-modality tests (`test_mri_pipeline_execution`, `test_ct_pipeline_execution`, `test_us_pipeline_execution`, `test_multimodality_metrics_and_dashboard_compilation`) return `OK`.
* [ ] **Hardware Stress Test:** Execute the heavy parallel processing workload simulator:
  ```bash
  docker exec -it rtx6000_mri_worker python3 /workspace/pipeline/tests/benchmark_gpu.py
  ```
  Verify that the combined throughput exceeds **100+ frames per second (FPS)** under full simultaneous load, and that the run is logged inside `metrics.json`.
* [ ] **Physical Scanner Handshake:** Visit at least one physical scanner console (e.g., the Emergency Department Siemens Force CT or the Main Campus Siemens 3T MRI). Execute a `C-ECHO` ping to AE Title `NVIDIA_MRI_PROC` on port `11104` and confirm a successful response.
* [ ] **Cloud PACS Destination Check:** Push a non-clinical QA test phantom series from a scanner console. Log into the Cloud PACS viewer utility, verify the study successfully bypassed security/quality gates, and confirm the patient identity is mapped to `ANON_MR_ROUTED`.

---

## 📝 Clinical Sign-Off Registry

By signing below, the engineering team certifies that the multi-modality processing node has passed all infrastructure compliance, cybersecurity hardening, and execution checks, and is authorized for active clinical diagnostics.

**Lead Clinical Engineer Signature:**  
____________________________________  Date: _____________

**Lead PACS / Imaging IT Analyst Signature:**  
____________________________________  Date: _____________

**Director of Medical Informatics/Designee Approval:**  
____________________________________  Date: _____________
