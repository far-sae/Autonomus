# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### Prerequisites
✅ Python 3.11+
✅ Node.js 18+
✅ PostgreSQL 15+ (or Docker)
✅ AWS CLI (optional, for AWS integration)

---

## Option 1: Automated Setup

```bash
# Clone and setup
git clone <your-repo>
cd Autonomus
./scripts/quickstart.sh

# The script will:
# - Create Python virtual environment
# - Install all dependencies
# - Setup .env files
# - Ready to configure
```

---

## Option 2: Manual Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Database Setup

```bash
# Start PostgreSQL (local or Docker)
docker run -d \
  --name compliance-db \
  -e POSTGRES_USER=complianceuser \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=compliance_db \
  -p 5432:5432 \
  postgres:15

# Run migrations
alembic upgrade head

# Create admin user
python -c "
import asyncio
from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.user import User

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
        print('✓ Admin user created: admin@example.com / admin123')

asyncio.run(create_admin())
"
```

### 3. Start Backend

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API endpoint
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Start development server
npm start

# Or build for production
npm run build
```

---

## 🎯 First Steps

### 1. Login
- Navigate to http://localhost:3000
- Login with `admin@example.com` / `admin123`

### 2. Add Cloud Account

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# Save the token, then:
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "compliance_frameworks": ["ISO27001", "SOC2", "GDPR"],
    "contact_email": "compliance@example.com"
  }'

curl -X POST http://localhost:8000/api/v1/cloud-accounts \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": 1,
    "name": "AWS Production",
    "provider": "aws",
    "account_id": "123456789012",
    "region": "us-east-1",
    "credentials": {
      "role_arn": "arn:aws:iam::123456789012:role/ComplianceScanner"
    }
  }'
```

### 3. Run First Scan

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"account_id": 1}'

# Or use the dashboard "Run Scan" button
```

### 4. View Results
- Check compliance score on dashboard
- View failed controls
- Test remediation (dry-run first!)
- Export audit report

---

## 🔧 Configuration

### AWS IAM Role Setup

```bash
# Create read-only scanner role
aws iam create-role \
  --role-name ComplianceScanner \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_COMPLIANCE_ACCOUNT:root"
      },
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach read-only policy
aws iam attach-role-policy \
  --role-name ComplianceScanner \
  --policy-arn arn:aws:iam::aws:policy/SecurityAudit
```

### Environment Variables (.env)

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/compliance_db
SECRET_KEY=<use: openssl rand -hex 32>

# AWS (if using AWS integration)
AWS_DEFAULT_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# S3 Evidence (optional for local dev)
EVIDENCE_BUCKET_NAME=compliance-evidence-local

# Optional
ENABLE_AUTO_REMEDIATION=false  # Safety: keep false
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📊 Test the System

### 1. Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}
```

### 2. Get API Docs
Open: http://localhost:8000/docs (Swagger UI)

### 3. Test Control
```python
# backend/test_control.py
import asyncio
from app.services.aws_client import AWSClient
from app.controls.aws_controls import S3PublicAccessControl

async def test():
    client = AWSClient({'role_arn': 'arn:aws:iam::...'})
    control = S3PublicAccessControl(client)
    findings = await control.detect()
    print(f"Found {len(findings)} violations")
    for f in findings:
        print(f"- {f.resource_id}: {f.finding_details}")

asyncio.run(test())
```

---

## 🐳 Docker Deployment

```bash
# Build backend
cd backend
docker build -t compliance-backend .

# Run with Docker Compose
cat > docker-compose.yml << 'YAML'
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: complianceuser
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: compliance_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    image: compliance-backend
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+asyncpg://complianceuser:changeme@db:5432/compliance_db
      SECRET_KEY: your-secret-key

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000

volumes:
  pgdata:
YAML

docker-compose up
```

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check database connection
psql -h localhost -U complianceuser -d compliance_db

# Check Python version
python --version  # Must be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend errors
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Database migration errors
```bash
# Reset migrations (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head

# Or create new migration
alembic revision --autogenerate -m "Initial"
alembic upgrade head
```

### AWS connection issues
```bash
# Test AWS credentials
aws sts get-caller-identity

# Test assume role
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/ComplianceScanner \
  --role-session-name test
```

---

## 📚 Next Steps

1. ✅ Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment
2. ✅ Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. ✅ Check [README.md](README.md) for full documentation
4. ✅ Add more cloud accounts
5. ✅ Customize controls for your needs
6. ✅ Set up monitoring and alerting

---

## 💡 Pro Tips

- Always use dry-run mode first before remediating
- Export audit reports regularly for compliance evidence
- Monitor the audit logs for security events
- Keep the SECRET_KEY safe and rotate regularly
- Use AWS Secrets Manager for production credentials
- Enable Multi-AZ for production database
- Set up automated backups

---

**🎉 You're ready to start automating compliance!**

For help: Check docs or open an issue.
