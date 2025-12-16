"""Detection Engine - Scans cloud environments for compliance violations."""
import uuid
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.cloud_account import CloudAccount
from app.models.control_result import ControlResult
from app.models.audit_log import AuditLog
from app.services.aws_client import AWSClient
from app.services.azure_client import AzureClient
from app.controls.aws_controls import AWS_CONTROLS
import logging

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Core detection engine for compliance scanning."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def scan_account(self, account_id: int, control_ids: List[str] = None) -> Dict[str, Any]:
        """
        Scan a cloud account for compliance violations.
        
        Args:
            account_id: CloudAccount ID
            control_ids: Optional list of specific controls to run
        
        Returns:
            Scan results summary
        """
        # Get account
        result = await self.db.execute(select(CloudAccount).where(CloudAccount.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        scan_id = str(uuid.uuid4())
        scan_start = datetime.utcnow()
        
        logger.info(f"Starting scan {scan_id} for account {account.name}")
        
        try:
            # Update scan status
            account.last_scan_status = "in_progress"
            await self.db.commit()
            
            # Get appropriate client
            if account.provider == "aws":
                client = AWSClient(account.credentials)
                controls = [ctrl(client) for ctrl in AWS_CONTROLS]
            elif account.provider == "azure":
                client = AzureClient(account.credentials)
                controls = []  # Azure controls would go here
            else:
                raise ValueError(f"Unsupported provider: {account.provider}")
            
            # Filter controls if specified
            if control_ids:
                controls = [c for c in controls if c.control_id in control_ids]
            
            # Run detections
            total_findings = 0
            pass_count, fail_count, error_count = 0, 0, 0
            
            for control in controls:
                try:
                    findings = await control.detect()
                    
                    if not findings:
                        # Control passed
                        pass_count += 1
                        await self._save_result(account_id, control, None, "PASS", scan_id)
                    else:
                        # Control failed
                        fail_count += len(findings)
                        total_findings += len(findings)
                        
                        for finding in findings:
                            await self._save_result(account_id, control, finding, finding.status, scan_id)
                    
                except Exception as e:
                    logger.error(f"Error running control {control.control_id}: {str(e)}")
                    error_count += 1
                    await self._save_result(account_id, control, None, "ERROR", scan_id, str(e))
            
            # Update account scan status
            account.last_scan_at = datetime.utcnow()
            account.last_scan_status = "success"
            await self.db.commit()
            
            # Log scan completion
            await self._log_audit(
                event_type="scan",
                action=f"Completed scan {scan_id}",
                cloud_account_id=account_id,
                organization_id=account.organization_id,
                event_data={
                    "scan_id": scan_id,
                    "controls_run": len(controls),
                    "total_findings": total_findings,
                    "pass": pass_count,
                    "fail": fail_count,
                    "error": error_count,
                    "duration_seconds": (datetime.utcnow() - scan_start).total_seconds()
                }
            )
            
            return {
                "scan_id": scan_id,
                "account_id": account_id,
                "status": "completed",
                "summary": {
                    "total_controls": len(controls),
                    "pass": pass_count,
                    "fail": fail_count,
                    "error": error_count,
                    "total_findings": total_findings
                },
                "started_at": scan_start.isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {str(e)}")
            account.last_scan_status = "failed"
            await self.db.commit()
            raise
    
    async def _save_result(
        self,
        account_id: int,
        control: Any,
        finding: Any,
        status: str,
        scan_id: str,
        error_msg: str = None
    ):
        """Save a control result to the database."""
        result = ControlResult(
            cloud_account_id=account_id,
            control_id=control.control_id,
            status=status,
            risk_level=control.severity,
            resource_id=finding.resource_id if finding else None,
            resource_type=finding.resource_type if finding else None,
            finding_details=finding.finding_details if finding else {"error": error_msg} if error_msg else {},
            evidence_before=finding.evidence if finding else {},
            scan_id=scan_id,
            metadata={
                "control_title": control.title,
                "control_description": control.description,
                "category": control.category,
                "frameworks": control.frameworks
            }
        )
        
        self.db.add(result)
        await self.db.commit()
        
        # Log detection
        await self._log_audit(
            event_type="detection",
            action=f"Control {control.control_id}: {status}",
            cloud_account_id=account_id,
            control_id=control.control_id,
            resource_id=finding.resource_id if finding else None,
            event_data={
                "status": status,
                "severity": control.severity,
                "finding": finding.finding_details if finding else {}
            }
        )
    
    async def _log_audit(
        self,
        event_type: str,
        action: str,
        **kwargs
    ):
        """Log an audit event."""
        log = AuditLog(
            event_type=event_type,
            action=action,
            actor="system",
            event_data=kwargs.get('event_data', {}),
            cloud_account_id=kwargs.get('cloud_account_id'),
            organization_id=kwargs.get('organization_id'),
            control_id=kwargs.get('control_id'),
            resource_id=kwargs.get('resource_id'),
            success="success"
        )
        self.db.add(log)
        await self.db.commit()
    
    async def get_compliance_score(self, account_id: int = None, organization_id: int = None) -> Dict[str, Any]:
        """Calculate compliance score."""
        query = select(ControlResult)
        
        if account_id:
            query = query.where(ControlResult.cloud_account_id == account_id)
        elif organization_id:
            query = query.join(CloudAccount).where(CloudAccount.organization_id == organization_id)
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return {"score": 0, "total": 0, "pass": 0, "fail": 0, "fixed": 0}
        
        pass_count = sum(1 for r in results if r.status == "PASS")
        fail_count = sum(1 for r in results if r.status == "FAIL")
        fixed_count = sum(1 for r in results if r.status == "FIXED")
        total = len(results)
        
        score = ((pass_count + fixed_count) / total * 100) if total > 0 else 0
        
        return {
            "score": round(score, 2),
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "fixed": fixed_count,
            "by_severity": await self._get_by_severity(results)
        }
    
    async def _get_by_severity(self, results: List[ControlResult]) -> Dict[str, int]:
        """Group results by severity."""
        from collections import Counter
        severity_counts = Counter(r.risk_level for r in results if r.status == "FAIL")
        return dict(severity_counts)
