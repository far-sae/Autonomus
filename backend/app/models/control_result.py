from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ControlResult(Base):
    __tablename__ = "control_results"
    
    id = Column(Integer, primary_key=True, index=True)
    cloud_account_id = Column(Integer, ForeignKey("cloud_accounts.id"), nullable=False)
    control_id = Column(String(100), nullable=False, index=True)
    
    # Result
    status = Column(String(50), nullable=False)  # PASS, FAIL, FIXED, ERROR, MANUAL
    risk_level = Column(String(50))  # critical, high, medium, low
    
    # Details
    resource_id = Column(String(500))  # ARN, resource ID, etc.
    resource_type = Column(String(255))
    finding_details = Column(JSON, default=dict)
    
    # Evidence
    evidence_before = Column(JSON)  # State before remediation
    evidence_after = Column(JSON)  # State after remediation
    evidence_s3_key = Column(String(500))  # S3 key for detailed evidence
    
    # Remediation
    remediation_status = Column(String(50))  # pending, approved, executed, failed, rolled_back
    remediation_approved_by = Column(String(255))
    remediation_executed_at = Column(DateTime(timezone=True))
    remediation_details = Column(JSON, default=dict)
    rollback_data = Column(JSON)  # Data needed to rollback
    
    # Additional metadata
    scan_id = Column(String(100), index=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    result_metadata = Column(JSON, default=dict)
    
    # Relationships
    cloud_account = relationship("CloudAccount", back_populates="control_results")
    audit_logs = relationship("AuditLog", back_populates="control_result", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_control_account_status', 'control_id', 'cloud_account_id', 'status'),
        Index('idx_scan_id', 'scan_id'),
    )
