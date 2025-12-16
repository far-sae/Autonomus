"""Remediation Engine - Automated compliance remediation with safety controls."""
import uuid
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.control_result import ControlResult
from app.models.cloud_account import CloudAccount
from app.models.audit_log import AuditLog
from app.services.aws_client import AWSClient
from app.controls.aws_controls import AWS_CONTROLS
import logging

logger = logging.getLogger(__name__)


class RemediationEngine:
    """Handles automated remediation with approval workflows and rollback."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def remediate_finding(
        self,
        finding_id: int,
        dry_run: bool = True,
        approved_by: str = None
    ) -> Dict[str, Any]:
        """
        Remediate a specific finding.
        
        Args:
            finding_id: ControlResult ID
            dry_run: If True, simulate remediation without applying changes
            approved_by: Email of approver (required for non-dry-run)
        
        Returns:
            Remediation result
        """
        # Get finding
        result = await self.db.execute(
            select(ControlResult).where(ControlResult.id == finding_id)
        )
        finding_record = result.scalar_one_or_none()
        
        if not finding_record:
            raise ValueError(f"Finding {finding_id} not found")
        
        if finding_record.status not in ["FAIL", "ERROR"]:
            raise ValueError(f"Finding {finding_id} is not in remediable state")
        
        # Get cloud account
        account_result = await self.db.execute(
            select(CloudAccount).where(CloudAccount.id == finding_record.cloud_account_id)
        )
        account = account_result.scalar_one_or_none()
        
        # Get control and client
        client = AWSClient(account.credentials) if account.provider == "aws" else None
        control_class = next((c for c in AWS_CONTROLS if c.control_id == finding_record.control_id), None)
        
        if not control_class:
            raise ValueError(f"Control {finding_record.control_id} not found")
        
        control = control_class(client)
        
        # Check if control supports remediation
        finding_obj = type('Finding', (), {
            'resource_id': finding_record.resource_id,
            'resource_type': finding_record.resource_type,
            'evidence': finding_record.evidence_before,
            'finding_details': finding_record.finding_details
        })()
        
        try:
            # Execute remediation
            remediation_result = await control.remediate(finding_obj, dry_run=dry_run)
            
            if remediation_result.success:
                if not dry_run:
                    # Update finding record
                    finding_record.status = "FIXED"
                    finding_record.remediation_status = "executed"
                    finding_record.remediation_approved_by = approved_by
                    finding_record.remediation_executed_at = datetime.utcnow()
                    finding_record.evidence_after = remediation_result.after_state
                    finding_record.rollback_data = remediation_result.rollback_data
                    finding_record.resolved_at = datetime.utcnow()
                    await self.db.commit()
                
                # Log remediation
                await self._log_audit(
                    event_type="remediation",
                    action=f"{'Dry-run' if dry_run else 'Executed'} remediation for {finding_record.control_id}",
                    actor=approved_by or "system",
                    cloud_account_id=account.id,
                    organization_id=account.organization_id,
                    control_id=finding_record.control_id,
                    resource_id=finding_record.resource_id,
                    control_result_id=finding_id,
                    before_state=remediation_result.before_state,
                    after_state=remediation_result.after_state,
                    event_data={
                        "dry_run": dry_run,
                        "success": True,
                        "finding_id": finding_id
                    }
                )
                
                return {
                    "success": True,
                    "finding_id": finding_id,
                    "control_id": finding_record.control_id,
                    "dry_run": dry_run,
                    "resource_id": finding_record.resource_id,
                    "before_state": remediation_result.before_state,
                    "after_state": remediation_result.after_state,
                    "message": f"Remediation {'simulated' if dry_run else 'executed'} successfully"
                }
            else:
                # Remediation failed
                if not dry_run:
                    finding_record.remediation_status = "failed"
                    finding_record.remediation_details = {"error": remediation_result.error_message}
                    await self.db.commit()
                
                await self._log_audit(
                    event_type="remediation",
                    action=f"Failed remediation for {finding_record.control_id}",
                    actor=approved_by or "system",
                    cloud_account_id=account.id,
                    control_id=finding_record.control_id,
                    resource_id=finding_record.resource_id,
                    control_result_id=finding_id,
                    event_data={
                        "dry_run": dry_run,
                        "success": False,
                        "error": remediation_result.error_message
                    },
                    success="failure",
                    error_message=remediation_result.error_message
                )
                
                return {
                    "success": False,
                    "finding_id": finding_id,
                    "error": remediation_result.error_message
                }
                
        except Exception as e:
            logger.error(f"Remediation error for finding {finding_id}: {str(e)}")
            raise
    
    async def rollback_remediation(self, finding_id: int, rolled_back_by: str) -> Dict[str, Any]:
        """
        Rollback a previously executed remediation.
        
        Args:
            finding_id: ControlResult ID
            rolled_back_by: Email of person initiating rollback
        
        Returns:
            Rollback result
        """
        # Get finding
        result = await self.db.execute(
            select(ControlResult).where(ControlResult.id == finding_id)
        )
        finding_record = result.scalar_one_or_none()
        
        if not finding_record or finding_record.status != "FIXED":
            raise ValueError(f"Finding {finding_id} not in rollback-able state")
        
        if not finding_record.rollback_data:
            raise ValueError(f"No rollback data available for finding {finding_id}")
        
        # Get account and control
        account_result = await self.db.execute(
            select(CloudAccount).where(CloudAccount.id == finding_record.cloud_account_id)
        )
        account = account_result.scalar_one_or_none()
        
        client = AWSClient(account.credentials) if account.provider == "aws" else None
        control_class = next((c for c in AWS_CONTROLS if c.control_id == finding_record.control_id), None)
        
        if not control_class:
            raise ValueError(f"Control {finding_record.control_id} not found")
        
        control = control_class(client)
        
        try:
            # Execute rollback
            rollback_result = await control.rollback(finding_record.rollback_data)
            
            if rollback_result.success:
                # Update status
                finding_record.status = "FAIL"
                finding_record.remediation_status = "rolled_back"
                finding_record.remediation_details = {
                    **finding_record.remediation_details,
                    "rolled_back_at": datetime.utcnow().isoformat(),
                    "rolled_back_by": rolled_back_by
                }
                await self.db.commit()
                
                # Log rollback
                await self._log_audit(
                    event_type="rollback",
                    action=f"Rolled back remediation for {finding_record.control_id}",
                    actor=rolled_back_by,
                    cloud_account_id=account.id,
                    control_id=finding_record.control_id,
                    resource_id=finding_record.resource_id,
                    control_result_id=finding_id,
                    event_data={"finding_id": finding_id, "success": True}
                )
                
                return {
                    "success": True,
                    "finding_id": finding_id,
                    "message": "Remediation rolled back successfully"
                }
            else:
                return {
                    "success": False,
                    "finding_id": finding_id,
                    "error": rollback_result.error_message
                }
                
        except Exception as e:
            logger.error(f"Rollback error for finding {finding_id}: {str(e)}")
            raise
    
    async def _log_audit(self, event_type: str, action: str, actor: str, **kwargs):
        """Log audit event."""
        log = AuditLog(
            event_type=event_type,
            action=action,
            actor=actor,
            event_data=kwargs.get('event_data', {}),
            cloud_account_id=kwargs.get('cloud_account_id'),
            organization_id=kwargs.get('organization_id'),
            control_id=kwargs.get('control_id'),
            resource_id=kwargs.get('resource_id'),
            control_result_id=kwargs.get('control_result_id'),
            before_state=kwargs.get('before_state'),
            after_state=kwargs.get('after_state'),
            success=kwargs.get('success', "success"),
            error_message=kwargs.get('error_message')
        )
        self.db.add(log)
        await self.db.commit()
