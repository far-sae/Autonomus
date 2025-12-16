"""Evidence Engine - Immutable audit trail and compliance evidence generation."""
import boto3
import json
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit_log import AuditLog
from app.models.control_result import ControlResult
from app.models.cloud_account import CloudAccount
from app.models.organization import Organization
from app.core.config import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class EvidenceEngine:
    """Manages compliance evidence and audit export."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = boto3.client('s3')
    
    async def export_audit_report(
        self,
        organization_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Export comprehensive audit report.
        
        Args:
            organization_id: Organization ID
            start_date: Report start date
            end_date: Report end date
            format: Report format (pdf, json)
        
        Returns:
            Report details and download URL
        """
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = org_result.scalar_one_or_none()
        
        if not organization:
            raise ValueError(f"Organization {organization_id} not found")
        
        # Get audit logs
        query = select(AuditLog).where(AuditLog.organization_id == organization_id)
        
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc())
        
        result = await self.db.execute(query)
        audit_logs = result.scalars().all()
        
        # Get control results
        results_query = select(ControlResult).join(CloudAccount).where(
            CloudAccount.organization_id == organization_id
        )
        results_result = await self.db.execute(results_query)
        control_results = results_result.scalars().all()
        
        # Generate report
        if format == "pdf":
            report_data = await self._generate_pdf_report(
                organization, audit_logs, control_results, start_date, end_date
            )
            content_type = "application/pdf"
            file_ext = "pdf"
        else:
            report_data = await self._generate_json_report(
                organization, audit_logs, control_results
            )
            content_type = "application/json"
            file_ext = "json"
        
        # Upload to S3
        report_key = f"audit-reports/{organization_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        
        try:
            self.s3_client.put_object(
                Bucket=settings.EVIDENCE_BUCKET_NAME,
                Key=report_key,
                Body=report_data,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                Metadata={
                    'organization_id': str(organization_id),
                    'generated_at': datetime.utcnow().isoformat()
                }
            )
            
            # Generate presigned URL (valid for 1 hour)
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.EVIDENCE_BUCKET_NAME, 'Key': report_key},
                ExpiresIn=3600
            )
            
            return {
                "report_key": report_key,
                "download_url": download_url,
                "format": format,
                "generated_at": datetime.utcnow().isoformat(),
                "total_audit_logs": len(audit_logs),
                "total_findings": len(control_results)
            }
            
        except Exception as e:
            logger.warning(f"Failed to upload audit report to S3: {str(e)}")
            # Return report data without S3 upload (demo/local mode)
            return {
                "report_key": report_key,
                "download_url": None,  # No S3, so no download URL
                "format": format,
                "generated_at": datetime.utcnow().isoformat(),
                "total_audit_logs": len(audit_logs),
                "total_findings": len(control_results),
                "message": "Report generated successfully (S3 upload unavailable in demo mode)"
            }
    
    async def _generate_pdf_report(
        self,
        organization: Organization,
        audit_logs: List[AuditLog],
        control_results: List[ControlResult],
        start_date: datetime,
        end_date: datetime
    ) -> bytes:
        """Generate PDF audit report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"<b>Compliance Audit Report</b><br/>{organization.name}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Report metadata
        metadata_text = f"""
        <b>Report Period:</b> {start_date.strftime('%Y-%m-%d') if start_date else 'All time'} to {end_date.strftime('%Y-%m-%d') if end_date else 'Present'}<br/>
        <b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>Frameworks:</b> {', '.join(organization.compliance_frameworks)}<br/>
        """
        story.append(Paragraph(metadata_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("<b>Executive Summary</b>", styles['Heading2']))
        
        pass_count = sum(1 for r in control_results if r.status == "PASS")
        fail_count = sum(1 for r in control_results if r.status == "FAIL")
        fixed_count = sum(1 for r in control_results if r.status == "FIXED")
        total = len(control_results)
        score = ((pass_count + fixed_count) / total * 100) if total > 0 else 0
        
        summary_data = [
            ["Metric", "Count"],
            ["Total Controls Evaluated", str(total)],
            ["Passed", str(pass_count)],
            ["Failed", str(fail_count)],
            ["Fixed", str(fixed_count)],
            ["Compliance Score", f"{score:.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Failed Controls Detail
        if fail_count > 0:
            story.append(Paragraph("<b>Failed Controls (Requiring Attention)</b>", styles['Heading2']))
            
            failed_results = [r for r in control_results if r.status == "FAIL"]
            for result in failed_results[:20]:  # Limit to first 20
                story.append(Paragraph(
                    f"<b>{result.control_id}</b> - {result.result_metadata.get('control_title', 'N/A') if result.result_metadata else 'N/A'}<br/>"
                    f"Resource: {result.resource_id}<br/>"
                    f"Severity: {result.risk_level}<br/>"
                    f"Detected: {result.detected_at.strftime('%Y-%m-%d %H:%M:%S') if result.detected_at else 'N/A'}",
                    styles['Normal']
                ))
                story.append(Spacer(1, 10))
        
        # Audit Activity Summary
        story.append(Paragraph("<b>Audit Activity</b>", styles['Heading2']))
        story.append(Paragraph(f"Total audit events: {len(audit_logs)}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    async def _generate_json_report(
        self,
        organization: Organization,
        audit_logs: List[AuditLog],
        control_results: List[ControlResult]
    ) -> bytes:
        """Generate JSON audit report."""
        report = {
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "frameworks": organization.compliance_frameworks
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_controls": len(control_results),
                "pass": sum(1 for r in control_results if r.status == "PASS"),
                "fail": sum(1 for r in control_results if r.status == "FAIL"),
                "fixed": sum(1 for r in control_results if r.status == "FIXED")
            },
            "control_results": [
                {
                    "control_id": r.control_id,
                    "status": r.status,
                    "severity": r.risk_level,
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                    "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None
                }
                for r in control_results
            ],
            "audit_logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "action": log.action,
                    "actor": log.actor,
                    "success": log.success
                }
                for log in audit_logs[:1000]  # Limit to 1000 recent logs
            ]
        }
        
        return json.dumps(report, indent=2).encode('utf-8')
    
    async def store_evidence(
        self,
        control_result_id: int,
        evidence_data: Dict[str, Any]
    ) -> str:
        """Store evidence snapshot in S3."""
        evidence_key = f"evidence/{control_result_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            self.s3_client.put_object(
                Bucket=settings.EVIDENCE_BUCKET_NAME,
                Key=evidence_key,
                Body=json.dumps(evidence_data).encode('utf-8'),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            return evidence_key
            
        except Exception as e:
            logger.error(f"Failed to store evidence: {str(e)}")
            raise
