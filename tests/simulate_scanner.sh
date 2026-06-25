#!/bin/bash
# Revolutionary Technology Company - Scanner Simulator

echo "============================================="
echo "⚙️  Simulating Scan Push: Siemens 3T -> NVIDIA Router"
echo "============================================="

# 1. Install dcmtk if missing to gain access to storescu
if ! command -v storescu &> /dev/null; then
    echo "[!] dcmtk toolkit not found. Installing..."
    sudo apt-get update && sudo apt-get install -y dcmtk
fi

# 2. Create a dummy DICOM test file structural layer
echo "Creating dummy MRI slice raw volume..."
echo "MOCK_RAW_MRI_DATA" > /tmp/test_mri_slice.dcm

# 3. Use storescu to simulate a transmission to your new Docker network node
echo "Sending DICOM stream payload to port 11104..."
storescu -aec SIEMENS_3T_MR -aet NVIDIA_MRI_PROC 127.0.0.1 11104 /tmp/test_mri_slice.dcm

echo "============================================="
echo "🏁 Simulation complete. Check 'docker logs mri_edge_listener'"
echo "============================================="
