# Autonomous Compliance & Security Automation Platform

## 🚀 Production-Ready Enterprise Compliance Automation

A comprehensive, production-grade platform that autonomously detects, remediates, and proves compliance across cloud environments.

[![Tech Stack](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![AWS](https://img.shields.io/badge/Cloud-AWS-orange.svg)](https://aws.amazon.com/)

---

## 🎯 Features

### Core Capabilities

✅ **Autonomous Detection**
- 20+ production-ready compliance controls
- Scans AWS (IAM, S3, EC2, RDS, CloudTrail, KMS, VPC, etc.)
- Azure & Microsoft 365/Entra ID integration ready
- Real-time violation detection

✅ **Safe Auto-Remediation**
- Dry-run mode for testing
- Approval workflow for high-risk fixes
- Full rollback capability
- Immutable audit trail

✅ **Compliance-as-Code**
- Machine-readable control definitions
- Mapped to ISO 27001, SOC 2, GDPR
- Version-controlled
- Extensible for custom controls

✅ **Evidence & Audit**
- Immutable before/after state snapshots
- PDF and JSON audit reports
- Read-only auditor access
- S3-backed evidence storage

✅ **Production Dashboard**
- Real-time compliance score
- Control status visualization
- Finding remediation interface
- Audit export functionality

---

## 📊 Implemented Controls

### AWS (21 Controls)

| ID | Control | Severity | Auto-Remediate | Frameworks |
|----|---------|----------|----------------|------------|
| AWS-IAM-001 | MFA Enforcement | Critical | ❌ | ISO 27001, SOC 2, GDPR |
| AWS-IAM-002 | Disable Unused Credentials | High | ✅ | ISO 27001, SOC 2 |
| AWS-IAM-003 | Strong Password Policy | High | ✅ | ISO 27001, SOC 2 |
| AWS-S3-001 | Block Public Access | Critical | ✅ | ISO 27001, SOC 2, GDPR |
| AWS-S3-002 | S3 Encryption | High | ✅ | ISO 27001, SOC 2, GDPR |
| AWS-S3-003 | S3 Versioning | Medium | ✅ | ISO 27001, SOC 2 |
| AWS-S3-004 | S3 Access Logging | Medium | ❌ | ISO 27001, SOC 2 |
| AWS-CT-001 | CloudTrail Enabled | Critical | ❌ | ISO 27001, SOC 2, GDPR |
| AWS-EC2-001 | No Public IPs | High | ❌ | ISO 27001, SOC 2 |
| AWS-EC2-002 | EBS Encryption | High | ❌ | ISO 27001, SOC 2, GDPR |
| AWS-SG-001 | Security Group 0.0.0.0/0 | Critical | ✅ | ISO 27001, SOC 2, GDPR |
| AWS-KMS-001 | KMS Key Rotation | Medium | ✅ | ISO 27001, SOC 2 |
| AWS-RDS-001 | RDS Encryption | High | ❌ | ISO 27001, GDPR |
| AWS-RDS-002 | RDS Not Public | Critical | ❌ | ISO 27001, SOC 2 |
| AWS-RDS-003 | RDS Backups | Medium | ✅ | ISO 27001, SOC 2 |
| AWS-VPC-001 | VPC Flow Logs | Medium | ❌ | ISO 27001, SOC 2 |
| AWS-ELB-001 | ELB Access Logs | Medium | ❌ | ISO 27001, SOC 2 |
| AWS-CONFIG-001 | AWS Config Enabled | Medium | ❌ | ISO 27001, SOC 2 |
| AWS-GD-001 | GuardDuty Enabled | High | ❌ | ISO 27001, SOC 2 |
| AWS-SNS-001 | SNS Encryption | Medium | ❌ | ISO 27001, SOC 2 |
| AWS-LAMBDA-001 | Lambda in VPC | Low | ❌ | ISO 27001, SOC 2 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Dashboard (Material-UI)               │
│  Compliance Score │ Findings Table │ Remediation │ Audit Export  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/REST API
┌────────────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  Detection   │ Remediation  │  Evidence    │    Auth      │  │
│  │   Engine     │   Engine     │   Engine     │   (JWT)      │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│           │                │              │                      │
│  ┌────────┴────────┬───────┴─────┬────────┴────────┐            │
│  │  AWS Client     │ Azure Client│  Audit Logger   │            │
│  └─────────────────┴─────────────┴─────────────────┘            │
└──────────────────────┬──────────────────┬──────────────────────┘
                       │                  │
         ┌─────────────┴──────┐   ┌───────┴────────┐
         │  PostgreSQL (RDS)  │   │  S3 Evidence   │
         │  - Organizations   │   │  - Snapshots   │
         │  - Cloud Accounts  │   │  - Audit PDFs  │
         │  - Control Results │   │  - Encrypted   │
         │  - Audit Logs      │   └────────────────┘
         └────────────────────┘
```

### Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), Pydantic
- **Frontend**: React 18, Material-UI, Recharts, Axios
- **Database**: PostgreSQL 15+ (AWS RDS Multi-AZ)
- **Storage**: AWS S3 (encrypted, versioned)
- **Infrastructure**: Terraform, AWS ECS Fargate, VPC, ALB
- **Cloud SDKs**: Boto3 (AWS), Azure SDK, Microsoft Graph

---

## 🚦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or AWS RDS)
- AWS CLI configured
- Terraform 1.0+ (for production deployment)

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd Autonomus

# Run quick start script
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh

# Configure backend
cd backend
cp .env.example .env
# Edit .env with your database and AWS credentials

# Run migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Start backend
uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm start

# Access dashboard at http://localhost:3000
```

### Production Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions.

```bash
# Deploy infrastructure
cd infrastructure
terraform init
terraform plan
terraform apply

# Deploy backend to ECS
docker build -t compliance-backend backend/
docker tag compliance-backend:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# Deploy frontend to S3
cd frontend
npm run build
aws s3 sync build/ s3://your-frontend-bucket/
```

---

## 📁 Project Structure

```
Autonomus/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── core/              # Config, security, dependencies
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   │   ├── detection_engine.py      # Compliance scanning
│   │   │   ├── remediation_engine.py    # Auto-fix with rollback
│   │   │   ├── evidence_engine.py       # Audit trail & reports
│   │   │   ├── aws_client.py            # AWS integration
│   │   │   └── azure_client.py          # Azure integration
│   │   ├── controls/          # Compliance controls
│   │   │   ├── base.py                  # Base control class
│   │   │   ├── aws_controls.py          # 20+ AWS controls
│   │   │   └── azure_controls.py        # Azure controls
│   │   └── main.py            # FastAPI application
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main dashboard
│   │   └── index.js
│   ├── public/
│   └── package.json
├── infrastructure/
│   ├── main.tf                # Terraform: VPC, RDS, ECS, S3
│   └── variables.tf
├── scripts/
│   └── quickstart.sh          # Setup script
├── DEPLOYMENT_GUIDE.md        # Comprehensive deployment guide
└── README.md
```

---

## 🔐 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (Admin, User, Auditor)
- Secure password hashing (bcrypt)
- Session management

### Data Protection
- All data encrypted at rest (RDS, S3)
- TLS 1.2+ for all connections
- S3 versioning and lifecycle policies
- Immutable audit logs

### Infrastructure Security
- Private subnets for backend and database
- Security groups with least privilege
- IAM roles with minimal permissions
- VPC Flow Logs enabled
- AWS Secrets Manager integration ready

### Compliance
- Immutable audit trail
- Before/after state snapshots
- 7-year retention (configurable)
- Read-only auditor role
- PDF audit reports with timestamps

---

## 📖 API Documentation

### Authentication
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=admin123

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Run Compliance Scan
```http
POST /api/v1/scans
Authorization: Bearer <token>
Content-Type: application/json

{
  "account_id": 1,
  "control_ids": ["AWS-S3-001", "AWS-IAM-001"]  // optional
}

Response:
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": {
    "total_controls": 20,
    "pass": 15,
    "fail": 5,
    "error": 0
  }
}
```

### Remediate Finding
```http
POST /api/v1/remediations
Authorization: Bearer <token>
Content-Type: application/json

{
  "finding_id": 123,
  "dry_run": false,
  "approved_by": "admin@example.com"
}

Response:
{
  "success": true,
  "message": "Remediation executed successfully",
  "before_state": {...},
  "after_state": {...}
}
```

### Export Audit Report
```http
POST /api/v1/audit-reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "organization_id": 1,
  "format": "pdf"
}

Response:
{
  "report_key": "audit-reports/1/20241216_143022.pdf",
  "download_url": "https://s3.amazonaws.com/...",
  "total_audit_logs": 1234,
  "total_findings": 567
}
```

Full API documentation available at: `http://localhost:8000/docs` (Swagger UI)

---

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_detection_engine.py -v
```

---

## 🛠️ Extending the Platform

### Adding a New Control

```python
# backend/app/controls/aws_controls.py

class NewSecurityControl(BaseControl):
    control_id = "AWS-XXX-001"
    title = "My Security Control"
    severity = "high"
    category = "Security"
    description = "Ensures XYZ is configured"
    frameworks = {"ISO27001": ["A.X.Y"], "SOC2": ["CCX.Y"]}
    
    async def detect(self) -> List[ControlFinding]:
        findings = []
        # Your detection logic here
        resources = self.client.describe_xyz()
        for resource in resources:
            if not resource.get('is_secure'):
                findings.append(ControlFinding(
                    status="FAIL",
                    resource_id=resource['id'],
                    resource_type="XYZ::Resource",
                    finding_details={"issue": "Not secure"},
                    evidence={"resource": resource},
                    can_auto_remediate=True
                ))
        return findings
    
    async def remediate(self, finding, dry_run=True):
        if dry_run:
            return RemediationResult(True, finding.resource_id, 
                                     finding.evidence, {"fixed": True}, 
                                     finding.evidence)
        # Your remediation logic here
        client = self.client.get_client('xyz')
        client.secure_resource(ResourceId=finding.evidence['resource']['id'])
        return RemediationResult(True, finding.resource_id,
                                 finding.evidence, {"fixed": True},
                                 finding.evidence)

# Register the control
AWS_CONTROLS.append(NewSecurityControl)
```

---

## 📊 Monitoring & Operations

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Application logs
docker logs -f compliance-backend

# Database logs
aws rds describe-db-log-files --db-instance-identifier compliance-db

# CloudWatch Logs
aws logs tail /ecs/compliance-backend --follow
```

### Metrics
- Compliance score trends
- Scan duration and frequency
- Remediation success rate
- API response times
- Database connection pool stats

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

Enterprise/Commercial License - Contact for licensing inquiries

---

## 🆘 Support

- **Documentation**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Issues**: Open an issue on GitHub
- **Email**: farazs156@gmail.com

---

## 🎉 Acknowledgments

Built with production-ready security, scalability, and compliance best practices.

**Key Technologies:**
- FastAPI for high-performance async API
- SQLAlchemy for robust database operations
- React & Material-UI for modern dashboard
- Terraform for infrastructure as code
- AWS for cloud-native deployment

---

**🚀 Ready to automate your compliance? Get started now!**
