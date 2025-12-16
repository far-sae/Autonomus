from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class AuditLog(Base):
    """Immutable audit log for all compliance activities."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    control_result_id = Column(Integer, ForeignKey("control_results.id"), nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # detection, remediation, approval, scan, etc.
    action = Column(String(255), nullable=False)
    actor = Column(String(255))  # user email or system
    
    # Context
    cloud_account_id = Column(Integer)
    organization_id = Column(Integer)
    control_id = Column(String(100), index=True)
    resource_id = Column(String(500))
    
    # Data (immutable snapshot)
    event_data = Column(JSON, nullable=False)
    before_state = Column(JSON)
    after_state = Column(JSON)
    
    # Metadata
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    success = Column(String(50), default="success")  # success, failure, partial
    error_message = Column(Text)
    
    # Relationships
    control_result = relationship("ControlResult", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_actor', 'actor'),
    )
