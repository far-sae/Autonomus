# Autonomous Compliance & Security Automation Platform

## Production-Ready Enterprise Compliance Automation

### Overview

A comprehensive, production-grade compliance automation platform that:
- **Detects** compliance violations across AWS and Azure environments
- **Auto-remediates** issues with dry-run, approval workflows, and rollback
- **Generates evidence** with immutable audit trails and PDF exports
- **Maps** to ISO 27001, SOC 2, and GDPR frameworks

## Architecture

### Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: React 18, Material-UI, Recharts
- **Infrastructure**: AWS (ECS Fargate, RDS, S3, VPC), Terraform
- **Integrations**: AWS SDK (boto3), Azure SDK, Microsoft Graph API

### Core Components

#### 1. Detection Engine
- Scans cloud environments using read-only IAM roles
- Evaluates 20+ compliance controls
- Generates immutable findings with evidence snapshots
- Supports parallel scanning for performance

#### 2. Remediation Engine
- **Dry-run mode**: Simulate fixes without applying changes
- **Approval workflow**: Requires explicit approval for high-risk fixes
- **Rollback capability**: Revert changes if issues arise
- **Full audit trail**: Every action logged with before/after states

#### 3. Evidence Engine
- Stores immutable snapshots in encrypted S3
- Generates PDF and JSON audit reports
- Provides read-only auditor access
- Retention: 7 years (configurable)

#### 4. Compliance-as-Code
- Machine-readable control definitions
- Framework mappings (ISO 27001, SOC 2, GDPR)
- Version-controlled in Git
- Extensible for custom controls

### Database Schema

```
organizations
  ├── cloud_accounts (AWS, Azure, M365)
  │     └── control_results (findings)
  │           └── audit_logs (immutable)
  ├── users (RBAC: admin, user, auditor)
  └── controls (library)
```

## Implemented Controls (20+)

### AWS Controls
1. **AWS-IAM-001**: MFA enforcement (Critical)
2. **AWS-IAM-002**: Disable unused credentials (High)
3. **AWS-IAM-003**: Strong password policy (High)
4. **AWS-S3-001**: Block public access (Critical) ✓ Auto-remediate
5. **AWS-S3-002**: S3 encryption (High) ✓ Auto-remediate
6. **AWS-S3-003**: S3 versioning (Medium) ✓ Auto-remediate
7. **AWS-S3-004**: S3 access logging (Medium)
8. **AWS-CT-001**: CloudTrail enabled (Critical)
9. **AWS-EC2-001**: No public IPs (High)
10. **AWS-EC2-002**: EBS encryption (High)
11. **AWS-SG-001**: Security groups no 0.0.0.0/0 (Critical) ✓ Auto-remediate
12. **AWS-KMS-001**: KMS key rotation (Medium) ✓ Auto-remediate
13. **AWS-RDS-001**: RDS encryption (High)
14. **AWS-RDS-002**: RDS not public (Critical)
15. **AWS-RDS-003**: RDS backups (Medium)
16. **AWS-VPC-001**: VPC flow logs (Medium)
17. **AWS-ELB-001**: ELB access logs (Medium)
18. **AWS-CONFIG-001**: AWS Config enabled (Medium)
19. **AWS-GD-001**: GuardDuty enabled (High)
20. **AWS-SNS-001**: SNS encryption (Medium)
21. **AWS-LAMBDA-001**: Lambda in VPC (Low)

## Deployment Guide

### Prerequisites
- AWS CLI configured
- Terraform >= 1.0
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use RDS)

### Step 1: Infrastructure Setup

```bash
cd infrastructure

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
db_username = "complianceadmin"
db_password = "CHANGE_ME_SECURE_PASSWORD"
evidence_bucket_name = "your-org-compliance-evidence"
EOF

# Plan and apply
terraform plan
terraform apply

# Save outputs
terraform output > ../backend/.terraform-outputs
```

### Step 2: Database Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your values
# DATABASE_URL from Terraform output
# SECRET_KEY: openssl rand -hex 32
# AWS credentials, etc.

# Run migrations (create Alembic if needed)
alembic upgrade head

# Create initial admin user
python -c "
from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.user import User
import asyncio

async def create_admin():
    async with async_session_maker() as session:
        admin = User(
            email='admin@example.com',
            hashed_password=get_password_hash('admin123'),
            full_name='Admin User',
            role='admin',
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print('Admin user created')

asyncio.run(create_admin())
"
```

### Step 3: Backend Deployment

```bash
# Run locally for testing
uvicorn app.main:app --reload --port 8000

# Or containerize for production
docker build -t compliance-backend .
docker run -p 8000:8000 --env-file .env compliance-backend

# For ECS deployment
aws ecr create-repository --repository-name compliance-backend
docker tag compliance-backend:latest <ECR_URI>:latest
docker push <ECR_URI>:latest

# Create ECS task definition and service (see terraform)
```

### Step 4: Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Configure API endpoint
echo "REACT_APP_API_URL=http://your-alb-dns.us-east-1.elb.amazonaws.com" > .env

# Build for production
npm run build

# Deploy to S3 + CloudFront or serve via Node
# For S3:
aws s3 sync build/ s3://your-frontend-bucket/
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"

# Or serve with nginx/Node
npm install -g serve
serve -s build -l 3000
```

### Step 5: Configure Cloud Accounts

```bash
# Via API or UI, add cloud accounts

# AWS: Create read-only IAM role
aws iam create-role --role-name ComplianceScanner \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::YOUR_ACCOUNT:root"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name ComplianceScanner \
  --policy-arn arn:aws:iam::aws:policy/SecurityAudit

# Add account via API
curl -X POST http://localhost:8000/api/v1/cloud-accounts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": 1,
    "name": "Production AWS",
    "provider": "aws",
    "account_id": "123456789012",
    "region": "us-east-1",
    "credentials": {
      "role_arn": "arn:aws:iam::123456789012:role/ComplianceScanner"
    }
  }'
```

### Step 6: Run First Scan

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_id": 1}'

# Or use the UI dashboard
```

## Security Hardening

### 1. Secrets Management
```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret --name compliance/db-password \
  --secret-string "YOUR_DB_PASSWORD"

# Update code to fetch from Secrets Manager
```

### 2. Network Security
- All resources in private subnets
- ALB in public subnets only
- Security groups: least privilege
- NACLs for additional layer

### 3. Encryption
- RDS encrypted at rest
- S3 server-side encryption (AES-256)
- TLS 1.2+ for all connections
- Secrets encrypted with KMS

### 4. RBAC
- Admin: Full access
- User: Scan, view, remediate
- Auditor: Read-only, export reports

### 5. Audit Trail
- Every action logged
- Immutable logs (S3 Object Lock)
- 7-year retention
- CloudTrail for infrastructure changes

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Get JWT token
- `POST /api/v1/auth/register` - Register user (admin only)
- `GET /api/v1/auth/me` - Get current user

### Organizations
- `POST /api/v1/organizations` - Create org
- `GET /api/v1/organizations` - List orgs
- `GET /api/v1/organizations/{id}` - Get org details

### Cloud Accounts
- `POST /api/v1/cloud-accounts` - Add cloud account
- `GET /api/v1/cloud-accounts` - List accounts

### Scans & Findings
- `POST /api/v1/scans` - Run compliance scan
- `GET /api/v1/compliance-score` - Get compliance score
- `GET /api/v1/findings` - List findings

### Remediation
- `POST /api/v1/remediations` - Remediate finding (dry-run or execute)
- `POST /api/v1/remediations/{id}/rollback` - Rollback remediation

### Audit & Evidence
- `POST /api/v1/audit-reports` - Generate PDF/JSON audit report
- `GET /api/v1/audit-logs` - List audit logs

## Monitoring & Operations

### Health Checks
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# View application logs
docker logs -f compliance-backend

# CloudWatch Logs for ECS
aws logs tail /ecs/compliance-backend --follow
```

### Metrics
- ECS Container Insights enabled
- RDS Performance Insights
- Custom metrics: compliance score, scan duration, remediation count

### Alerts
- Critical findings > 10
- Scan failures
- Remediation failures
- Database connection errors

## Extending the Platform

### Adding New Controls

```python
# backend/app/controls/aws_controls.py

class NewControl(BaseControl):
    control_id = "AWS-XXX-001"
    title = "Control Title"
    severity = "high"
    category = "Category"
    description = "Description"
    frameworks = {"ISO27001": ["A.X.Y"], "SOC2": ["CCX.Y"]}
    
    async def detect(self) -> List[ControlFinding]:
        # Detection logic
        return findings
    
    async def remediate(self, finding, dry_run=True) -> RemediationResult:
        # Remediation logic
        return result

# Register
AWS_CONTROLS.append(NewControl)
```

### Adding Azure Controls
Create `backend/app/controls/azure_controls.py` following same pattern.

## Production Checklist

- [ ] Change all default passwords
- [ ] Configure AWS Secrets Manager
- [ ] Enable Multi-AZ RDS
- [ ] Configure CloudFront for frontend
- [ ] Enable AWS WAF
- [ ] Set up monitoring and alerting
- [ ] Configure backup retention
- [ ] Enable RDS automated backups
- [ ] Configure S3 lifecycle policies
- [ ] Set up log aggregation (CloudWatch/ELK)
- [ ] Implement rate limiting
- [ ] Configure CORS properly
- [ ] Enable API throttling
- [ ] Set up disaster recovery plan
- [ ] Document incident response procedures

## Cost Optimization

- Use Fargate Spot for non-critical workloads
- Enable S3 Intelligent-Tiering
- Use RDS Reserved Instances
- Implement auto-scaling
- Clean up old scan results (> 90 days)

## Support & Maintenance

- Review audit logs weekly
- Update controls monthly
- Patch dependencies monthly
- Review compliance scores daily
- Conduct security audits quarterly

## License

Enterprise/Commercial - Contact for licensing

---

**Built with production-ready security, scalability, and compliance in mind.**
