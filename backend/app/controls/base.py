from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ControlFinding:
    """Result of a control check."""
    status: str  # PASS, FAIL, ERROR
    resource_id: str
    resource_type: str
    finding_details: Dict[str, Any]
    evidence: Dict[str, Any]
    can_auto_remediate: bool = False
    remediation_risk: str = "low"


@dataclass
class RemediationResult:
    """Result of a remediation action."""
    success: bool
    resource_id: str
    before_state: Dict[str, Any]
    after_state: Optional[Dict[str, Any]]
    rollback_data: Optional[Dict[str, Any]]
    error_message: Optional[str] = None


class BaseControl(ABC):
    """Base class for all compliance controls."""
    
    def __init__(self, client: Any):
        self.client = client
    
    @property
    @abstractmethod
    def control_id(self) -> str:
        """Unique control identifier."""
        pass
    
    @property
    @abstractmethod
    def title(self) -> str:
        """Control title."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Control description."""
        pass
    
    @property
    @abstractmethod
    def severity(self) -> str:
        """Control severity: critical, high, medium, low."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Control category."""
        pass
    
    @property
    @abstractmethod
    def frameworks(self) -> Dict[str, List[str]]:
        """Mapping to compliance frameworks."""
        pass
    
    @abstractmethod
    async def detect(self) -> List[ControlFinding]:
        """
        Detect compliance violations.
        
        Returns:
            List of findings
        """
        pass
    
    async def remediate(self, finding: ControlFinding, dry_run: bool = True) -> RemediationResult:
        """
        Remediate a finding.
        
        Args:
            finding: The finding to remediate
            dry_run: If True, only simulate remediation
        
        Returns:
            RemediationResult
        """
        return RemediationResult(
            success=False,
            resource_id=finding.resource_id,
            before_state=finding.evidence,
            after_state=None,
            rollback_data=None,
            error_message="Remediation not implemented for this control"
        )
    
    async def rollback(self, rollback_data: Dict[str, Any]) -> RemediationResult:
        """
        Rollback a remediation.
        
        Args:
            rollback_data: Data needed to rollback
        
        Returns:
            RemediationResult
        """
        return RemediationResult(
            success=False,
            resource_id=rollback_data.get('resource_id', 'unknown'),
            before_state={},
            after_state=None,
            rollback_data=None,
            error_message="Rollback not implemented for this control"
        )
