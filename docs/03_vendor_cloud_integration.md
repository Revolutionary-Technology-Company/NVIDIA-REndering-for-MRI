# Tutorial 3: Native Integration with Vendor Scanners & Cloud PACS

This tutorial explains how to securely bridge your legacy hardware (like the **Siemens Avanto 1.5T** or older **GE 1.5T** setups) and modern scanners directly to cloud-native AI infrastructures using the RTX 6000 node as a TLS-encrypted processing gateway.

## 🏗️ Architecture
[Physical Scanners] ──(DICOM Cleartext)──> [Local RTX 6000 Node]\
│\
(TLS 1.3 Wrapper)\
▼\
[Secure Cloud PACS]

## 🚀 Setup Steps

### Step 1: Handle Legacy Transfers (Siemens Avanto Fix)
Legacy scanners often do not natively support modern compressed DICOM Transfer Syntaxes. Our RTX 6000 edge server fixes this by acting as a translation bridge.

Configure the local pipeline properties inside `/config/router.json`:

```json
{
  "Source_Scanners": [
    {"Name": "GE_15T", "AET": "GE_MR_SCANNER", "IP": "10.0.1.50"},
    {"Name": "Siemens_3T", "AET": "SIEMENS_3T_MR", "IP": "10.0.1.51"},
    {"Name": "Siemens_Avanto", "AET": "AVANTO_OUTPATIENT", "IP": "10.0.1.52"}
  ],
  "Translation_Settings": {
    "Incoming_Syntax": "ImplicitVRLittleEndian",
    "Target_Syntax": "ExplicitVRLittleEndian",
    "GPU_Compression_Level": "Lossless_JPEG2000"
  }
}
```

### Step 2: Establish the Secure Cloud Tunnel
Because you are shifting images outside your local hospital network to a **Cloud PACS**, all traffic must be wrapped in a secure tunnel. Configure your `docker-compose.yml` to utilize a reverse proxy wrapper (like Nginx or Stunnel) with the GPU routing node:

```yaml
version: '3.8'

services:
  dicom-router:
    image: orthanc/orthanc
    ports:
      - "11104:104"
    volumes:
      - ./config/router.json:/etc/orthanc/orthanc.json:ro
    environment:
      - GPU_ACCELERATION=true

  secure-tunnel:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./config/nginx-tls.conf:/etc/nginx/nginx.conf:ro
      - /etc/ssl/certs/hospital_pacs.crt:/etc/ssl/certs/pacs.crt:ro
```

### Step 3: Deployment Testing
Deploy the environment gateway using:
```bash
docker-compose -f docker-compose.cloud.yml up -d
```

---

## 🔒 Cybersecurity Auditing
1. Confirm that port `11104` is strictly isolated within the internal hospital imaging VLAN.
2. Verify that outward communication on port `443` is locked down exclusively to the specific, whitelisted IP addresses of your Cloud PACS provider.
