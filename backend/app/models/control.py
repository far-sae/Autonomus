from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class Control(Base):
    __tablename__ = "controls"
    
    id = Column(Integer, primary_key=True, index=True)
    control_id = Column(String(100), unique=True, nullable=False, index=True)  # e.g., AWS-IAM-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # IAM, Storage, Network, Encryption, etc.
    severity = Column(String(50), nullable=False)  # critical, high, medium, low
    
    # Compliance mappings
    frameworks = Column(JSON, default=dict)  # {"ISO27001": ["A.9.2.1"], "SOC2": ["CC6.1"], "GDPR": ["Art.32"]}
    
    # Provider-specific
    provider = Column(String(50), nullable=False)  # aws, azure, m365, all
    resource_types = Column(JSON, default=list)  # ["IAM::User", "S3::Bucket"]
    
    # Implementation
    detection_logic = Column(Text)  # Python code or query
    remediation_logic = Column(Text)  # Python code for auto-fix
    can_auto_remediate = Column(Boolean, default=False)
    remediation_risk = Column(String(50), default="low")  # low, medium, high
    
    # Additional metadata
    references = Column(JSON, default=list)  # URLs to documentation
    is_active = Column(Boolean, default=True)
    control_metadata = Column(JSON, default=dict)
