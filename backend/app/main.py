"""Main FastAPI application - Autonomous Compliance & Security Automation Platform."""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, require_role
)
from app.db.session import get_db, init_db
from app.models import User, Organization, CloudAccount, ControlResult, AuditLog
from app.services.detection_engine import DetectionEngine
from app.services.remediation_engine import RemediationEngine
from app.services.evidence_engine import EvidenceEngine

app = FastAPI(
    title="Autonomous Compliance & Security Platform",
    description="Production-ready compliance automation with detection, remediation, and evidence generation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"

class OrganizationCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    compliance_frameworks: List[str] = []
    contact_email: Optional[EmailStr] = None

class CloudAccountCreate(BaseModel):
    organization_id: int
    name: str
    provider: str
    account_id: str
    region: str = "us-east-1"
    credentials: dict

class ScanRequest(BaseModel):
    account_id: int
    control_ids: Optional[List[str]] = None

class RemediationRequest(BaseModel):
    finding_id: int
    dry_run: bool = True
    approved_by: Optional[str] = None

# Startup/Shutdown
@app.on_event("startup")
async def startup():
    await init_db()

# Auth Endpoints
@app.post("/api/v1/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/auth/register", status_code=201)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    await db.commit()
    return {"message": "User created successfully"}

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

# Organization Endpoints
@app.post("/api/v1/organizations", status_code=201)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    org = Organization(**org_data.dict())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@app.get("/api/v1/organizations")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Organization))
    return result.scalars().all()

@app.get("/api/v1/organizations/{org_id}")
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

# Cloud Account Endpoints
@app.post("/api/v1/cloud-accounts", status_code=201)
async def create_cloud_account(
    account_data: CloudAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "user"]))
):
    account = CloudAccount(**account_data.dict())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

@app.get("/api/v1/cloud-accounts")
async def list_cloud_accounts(
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(CloudAccount)
    if organization_id:
        query = query.where(CloudAccount.organization_id == organization_id)
    result = await db.execute(query)
    return result.scalars().all()

# Detection Endpoints
@app.post("/api/v1/scans")
async def run_scan(
    scan_request: ScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    engine = DetectionEngine(db)
    result = await engine.scan_account(
        scan_request.account_id,
        scan_request.control_ids
    )
    return result

@app.get("/api/v1/compliance-score")
async def get_compliance_score(
    account_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    engine = DetectionEngine(db)
    score = await engine.get_compliance_score(account_id, organization_id)
    return score

@app.get("/api/v1/findings")
async def list_findings(
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(ControlResult)
    if account_id:
        query = query.where(ControlResult.cloud_account_id == account_id)
    if status:
        query = query.where(ControlResult.status == status)
    if severity:
        query = query.where(ControlResult.risk_level == severity)
    
    query = query.order_by(ControlResult.detected_at.desc()).limit(100)
    result = await db.execute(query)
    findings = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "control_id": f.control_id,
            "status": f.status,
            "severity": f.risk_level,
            "resource_id": f.resource_id,
            "resource_type": f.resource_type,
            "finding_details": f.finding_details,
            "detected_at": f.detected_at.isoformat() if f.detected_at else None,
            "can_remediate": f.result_metadata.get('can_auto_remediate', False) if f.result_metadata else False
        }
        for f in findings
    ]

# Remediation Endpoints
@app.post("/api/v1/remediations")
async def remediate_finding(
    remediation_request: RemediationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    engine = RemediationEngine(db)
    result = await engine.remediate_finding(
        remediation_request.finding_id,
        remediation_request.dry_run,
        remediation_request.approved_by or current_user.email
    )
    return result

@app.post("/api/v1/remediations/{finding_id}/rollback")
async def rollback_remediation(
    finding_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    engine = RemediationEngine(db)
    result = await engine.rollback_remediation(finding_id, current_user.email)
    return result

# Evidence & Audit Endpoints
@app.post("/api/v1/audit-reports")
async def generate_audit_report(
    organization_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "auditor"]))
):
    engine = EvidenceEngine(db)
    report = await engine.export_audit_report(
        organization_id, start_date, end_date, format
    )
    return report

@app.get("/api/v1/audit-logs")
async def list_audit_logs(
    organization_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "auditor"]))
):
    query = select(AuditLog)
    if organization_id:
        query = query.where(AuditLog.organization_id == organization_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type,
            "action": log.action,
            "actor": log.actor,
            "control_id": log.control_id,
            "resource_id": log.resource_id,
            "success": log.success
        }
        for log in logs
    ]

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
