from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # aws, azure, gcp
    account_id = Column(String(255), nullable=False)  # AWS Account ID, Azure Subscription ID
    region = Column(String(100), default="us-east-1")
    
    # Credentials - encrypted in production
    credentials = Column(JSON, nullable=False)  # role_arn for AWS, service principal for Azure
    
    is_active = Column(Boolean, default=True)
    last_scan_at = Column(DateTime(timezone=True))
    last_scan_status = Column(String(50))  # success, failed, in_progress
    account_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="cloud_accounts")
    control_results = relationship("ControlResult", back_populates="cloud_account", cascade="all, delete-orphan")
