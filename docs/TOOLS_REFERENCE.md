# CDSI Tools Reference Guide

**Author:** bdstest  
**Contact:** consulting@getcdsi.com  
**Website:** getcdsi.com

## 📋 Complete Tool Reference

### Assessment Tools

#### 1. CDSI Maturity Assessment
**Purpose:** Determine your organization's compliance maturity level  
**Location:** `tools/assessments/cdsi_maturity_assessment.py`  
**Usage:**
```bash
python tools/assessments/cdsi_maturity_assessment.py
```
**Features:**
- Interactive questionnaire
- 8 assessment areas
- Automated maturity level calculation
- Personalized advancement recommendations

#### 2. Enhanced PII Detector
**Purpose:** Detect personal data with international compliance patterns  
**Location:** `tools/compliance-aware/enhanced_pii_detector.py`  
**Usage:**
```bash
python tools/compliance-aware/enhanced_pii_detector.py
```
**Features:**
- US, EU, UK, Canadian ID patterns
- GDPR Article 9 special categories
- Healthcare (HIPAA) patterns
- Financial (PCI DSS) patterns
- Biometric data detection
- Risk assessment and compliance framework mapping

#### 3. Data Discovery Scanner
**Purpose:** Scan file systems for personal data  
**Location:** `tools/compliance-aware/data_discovery_scanner.py`  
**Usage:**
```bash
python tools/compliance-aware/data_discovery_scanner.py /path/to/scan
```
**Features:**
- File system scanning
- PII pattern matching
- Risk scoring
- Compliance recommendations
- JSON report export

### Reporting Tools

#### 4. Advanced Compliance Reporter
**Purpose:** Generate multi-format compliance reports  
**Location:** `tools/reports/advanced_reporter.py`  
**Usage:**
```bash
# Generate executive summary
python tools/reports/advanced_reporter.py --type executive

# Export to specific format
python tools/reports/advanced_reporter.py --format pdf

# Full audit report
python tools/reports/advanced_reporter.py --type audit
```
**Features:**
- Executive summaries
- Detailed audit reports
- Risk assessment matrices
- Multi-format export (JSON, CSV, XML, HTML, PDF)
- Compliance framework mapping

### Enterprise Integration

#### 5. Enterprise API
**Purpose:** REST API for compliance automation integration  
**Location:** `tools/integrations/enterprise_api.py`  
**Usage:**
```bash
# Start API server
python tools/integrations/enterprise_api.py

# Or use uvicorn for production
uvicorn tools.integrations.enterprise_api:app --host 0.0.0.0 --port 8000
```
**Endpoints:**
- `POST /api/v1/scans` - Initiate compliance scan
- `GET /api/v1/scans/{scan_id}` - Get scan results
- `POST /api/v1/assessments` - Conduct maturity assessment
- `POST /api/v1/webhooks` - Configure webhooks
- `GET /api/v1/frameworks` - List compliance frameworks
- `GET /api/v1/metrics/compliance` - Get compliance metrics

#### 6. SIEM Connector
**Purpose:** Stream compliance events to SIEM systems  
**Location:** `tools/integrations/siem_connector.py`  
**Usage:**
```bash
# Splunk integration
python tools/integrations/siem_connector.py --provider splunk --endpoint https://splunk:8088 --token YOUR_HEC_TOKEN

# Elasticsearch integration
python tools/integrations/siem_connector.py --provider elastic --endpoint https://elastic:9200 --api-key YOUR_KEY

# Generic webhook
python tools/integrations/siem_connector.py --provider generic --endpoint https://webhook.example.com
```
**Supported SIEM Systems:**
- Splunk
- Elasticsearch
- IBM QRadar
- Microsoft Sentinel
- Sumo Logic
- Generic webhooks

## 🚀 Common Use Cases

### Quick Compliance Check
```bash
# 1. Assess current maturity
python tools/assessments/cdsi_maturity_assessment.py

# 2. Scan for personal data
python tools/compliance-aware/data_discovery_scanner.py ./data

# 3. Generate compliance report
python tools/reports/advanced_reporter.py --type executive --format pdf
```

### Enterprise Integration Setup
```bash
# 1. Start API server
python tools/integrations/enterprise_api.py

# 2. Configure SIEM connector
python tools/integrations/siem_connector.py --provider splunk --config siem_config.json

# 3. Set up webhooks via API
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"url": "https://your-system.com/webhook", "events": ["scan_complete"]}'
```

### Continuous Compliance Monitoring
```bash
# Schedule regular scans (cron example)
0 2 * * * python /path/to/cdsi-tools/tools/compliance-aware/data_discovery_scanner.py /data

# Stream events to SIEM
python tools/integrations/siem_connector.py --provider elastic --continuous
```

## 📊 Tool Requirements

### Python Version
- Minimum: Python 3.6+
- Recommended: Python 3.8+

### Dependencies
- FastAPI (for enterprise API)
- aiohttp (for SIEM connector)
- Standard library for most tools

### System Requirements
- OS: Linux, macOS, Windows
- Memory: 512MB minimum
- Disk: Varies by scan size

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
export CDSI_API_KEY="your-api-key"
export CDSI_API_PORT=8000

# SIEM Configuration
export SIEM_ENDPOINT="https://siem.example.com"
export SIEM_API_KEY="your-siem-key"

# Scan Configuration
export CDSI_MAX_SCAN_FILES=10000
export CDSI_SCAN_TIMEOUT=3600
```

### Configuration Files
```bash
# Create config directory
mkdir ~/.cdsi

# API config
cat > ~/.cdsi/api_config.json <<EOF
{
  "port": 8000,
  "host": "0.0.0.0",
  "auth_enabled": true
}
EOF

# SIEM config
cat > ~/.cdsi/siem_config.json <<EOF
{
  "provider": "splunk",
  "endpoint": "https://splunk:8088",
  "batch_size": 100
}
EOF
```

## 📧 Support

**Consulting:** consulting@getcdsi.com  
**Documentation:** https://github.com/bdstest/cdsi-tools  
**Issues:** GitHub Issues

---

*CDSI provides technology implementation guidance only, not legal advice.*