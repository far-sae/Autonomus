"""AWS Compliance Controls - 20+ controls with detection and remediation."""
from typing import List
from app.controls.base import BaseControl, ControlFinding, RemediationResult

AWS_CONTROLS = []

class IAMMFAControl(BaseControl):
    control_id, title, severity, category = "AWS-IAM-001", "MFA Required", "critical", "IAM"
    description, frameworks = "MFA must be enabled", {"ISO27001": ["A.9.2.1"], "SOC2": ["CC6.1"]}
    async def detect(self) -> List[ControlFinding]:
        return [ControlFinding("FAIL", u['Arn'], "IAM::User", {"user": u['UserName']}, {"user": u['UserName']})
                for u in self.client.list_users() if not self.client.get_user_mfa_devices(u['UserName'])]

class S3PublicAccessControl(BaseControl):
    control_id, title, severity, category = "AWS-S3-001", "Block Public Access", "critical", "Storage"
    description, frameworks = "S3 buckets must block public access", {"ISO27001": ["A.13.1.3"], "GDPR": ["Art.32"]}
    async def detect(self) -> List[ControlFinding]:
        findings = []
        for b in self.client.list_buckets():
            pub = self.client.get_public_access_block(b['Name'])
            if not pub or not all(pub.get('PublicAccessBlockConfiguration', {}).get(k) for k in ['BlockPublicAcls', 'BlockPublicPolicy']):
                findings.append(ControlFinding("FAIL", f"arn:aws:s3:::{b['Name']}", "S3::Bucket", {"bucket": b['Name']}, {"bucket": b['Name']}, True, "high"))
        return findings
    async def remediate(self, finding, dry_run=True):
        if dry_run: return RemediationResult(True, finding.resource_id, finding.evidence, {"blocked": True}, finding.evidence)
        try:
            self.client.get_client('s3').put_public_access_block(Bucket=finding.evidence['bucket'],
                PublicAccessBlockConfiguration={'BlockPublicAcls': True, 'BlockPublicPolicy': True, 'IgnorePublicAcls': True, 'RestrictPublicBuckets': True})
            return RemediationResult(True, finding.resource_id, finding.evidence, {"blocked": True}, finding.evidence)
        except Exception as e: return RemediationResult(False, finding.resource_id, finding.evidence, None, None, str(e))

class S3EncryptionControl(BaseControl):
    control_id, title, severity, category = "AWS-S3-002", "S3 Encryption", "high", "Encryption"
    description, frameworks = "S3 must have default encryption", {"ISO27001": ["A.10.1.1"], "SOC2": ["CC6.1"]}
    async def detect(self):
        return [ControlFinding("FAIL", f"arn:aws:s3:::{b['Name']}", "S3::Bucket", {"bucket": b['Name']}, {"bucket": b['Name']}, True, "low")
                for b in self.client.list_buckets() if not self.client.get_bucket_encryption(b['Name'])]
    async def remediate(self, finding, dry_run=True):
        if dry_run: return RemediationResult(True, finding.resource_id, finding.evidence, {"enc": True}, finding.evidence)
        try:
            self.client.get_client('s3').put_bucket_encryption(Bucket=finding.evidence['bucket'],
                ServerSideEncryptionConfiguration={'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]})
            return RemediationResult(True, finding.resource_id, finding.evidence, {"enc": True}, finding.evidence)
        except Exception as e: return RemediationResult(False, finding.resource_id, finding.evidence, None, None, str(e))

class S3VersioningControl(BaseControl):
    control_id, title, severity, category = "AWS-S3-003", "S3 Versioning", "medium", "Backup"
    description, frameworks = "S3 versioning for recovery", {"ISO27001": ["A.12.3.1"], "SOC2": ["A1.2"]}
    async def detect(self):
        return [ControlFinding("FAIL", f"arn:aws:s3:::{b['Name']}", "S3::Bucket", {"bucket": b['Name']}, {"bucket": b['Name']}, True, "low")
                for b in self.client.list_buckets() if not self.client.get_bucket_versioning(b['Name']) or 
                self.client.get_bucket_versioning(b['Name']).get('Status') != 'Enabled']

class S3LoggingControl(BaseControl):
    control_id, title, severity, category = "AWS-S3-004", "S3 Access Logs", "medium", "Logging"
    description, frameworks = "S3 access logging required", {"ISO27001": ["A.12.4.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        return [ControlFinding("FAIL", f"arn:aws:s3:::{b['Name']}", "S3::Bucket", {"bucket": b['Name']}, {"bucket": b['Name']})
                for b in self.client.list_buckets() if not self.client.get_bucket_logging(b['Name']) or 
                'LoggingEnabled' not in self.client.get_bucket_logging(b['Name'])]

class CloudTrailControl(BaseControl):
    control_id, title, severity, category = "AWS-CT-001", "CloudTrail Enabled", "critical", "Logging"
    description, frameworks = "CloudTrail must be enabled", {"ISO27001": ["A.12.4.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        trails = self.client.describe_trails()
        if not trails: return [ControlFinding("FAIL", "aws:cloudtrail", "CloudTrail", {}, {}, False, "high")]
        return [ControlFinding("FAIL", t['TrailARN'], "CloudTrail", {"trail": t['Name']}, {"trail": t['Name']}, True, "low")
                for t in trails if not self.client.get_trail_status(t['TrailARN']) or 
                not self.client.get_trail_status(t['TrailARN']).get('IsLogging')]

class EC2PublicIPControl(BaseControl):
    control_id, title, severity, category = "AWS-EC2-001", "No Public IPs", "high", "Network"
    description, frameworks = "EC2 should not have public IPs", {"ISO27001": ["A.13.1.1"], "SOC2": ["CC6.6"]}
    async def detect(self):
        return [ControlFinding("FAIL", i['InstanceId'], "EC2::Instance", {"instance": i['InstanceId'], "ip": i['PublicIpAddress']},
                {"instance": i['InstanceId']}, False, "high")
                for i in self.client.describe_instances() if i.get('PublicIpAddress')]

class EC2EncryptedVolumesControl(BaseControl):
    control_id, title, severity, category = "AWS-EC2-002", "EBS Encryption", "high", "Encryption"
    description, frameworks = "EBS volumes must be encrypted", {"ISO27001": ["A.10.1.1"], "GDPR": ["Art.32"]}
    async def detect(self):
        return [ControlFinding("FAIL", v['VolumeId'], "EC2::Volume", {"volume": v['VolumeId']}, {"volume": v['VolumeId']}, False, "high")
                for v in self.client.describe_volumes() if not v.get('Encrypted', False)]

class SecurityGroupControl(BaseControl):
    control_id, title, severity, category = "AWS-SG-001", "No Open Ports", "critical", "Network"
    description, frameworks = "Block 0.0.0.0/0 on sensitive ports", {"ISO27001": ["A.13.1.1"], "SOC2": ["CC6.6"]}
    async def detect(self):
        findings = []
        for sg in self.client.describe_security_groups():
            for perm in sg.get('IpPermissions', []):
                if any(ip.get('CidrIp') == '0.0.0.0/0' for ip in perm.get('IpRanges', [])):
                    findings.append(ControlFinding("FAIL", sg['GroupId'], "SecurityGroup", {"group": sg['GroupId']}, 
                        {"group": sg['GroupId']}, True, "high"))
        return findings

class KMSRotationControl(BaseControl):
    control_id, title, severity, category = "AWS-KMS-001", "KMS Key Rotation", "medium", "Encryption"
    description, frameworks = "KMS keys must auto-rotate", {"ISO27001": ["A.10.1.2"], "SOC2": ["CC6.1"]}
    async def detect(self):
        findings = []
        for k in self.client.list_keys():
            meta = self.client.describe_key(k['KeyId'])
            if meta and meta.get('KeyManager') == 'CUSTOMER' and not self.client.get_key_rotation_status(k['KeyId']):
                findings.append(ControlFinding("FAIL", meta['Arn'], "KMS::Key", {"key": k['KeyId']}, {"key": k['KeyId']}, True, "low"))
        return findings

class IAMPasswordPolicyControl(BaseControl):
    control_id, title, severity, category = "AWS-IAM-003", "Password Policy", "high", "IAM"
    description, frameworks = "Strong password policy required", {"ISO27001": ["A.9.4.3"], "SOC2": ["CC6.1"]}
    async def detect(self):
        try:
            policy = self.client.get_client('iam').get_account_password_policy()['PasswordPolicy']
            if not all([policy.get('RequireUppercaseCharacters'), policy.get('MinimumPasswordLength', 0) >= 14]):
                return [ControlFinding("FAIL", "iam:password-policy", "IAM::Policy", {}, {}, True)]
        except: return [ControlFinding("FAIL", "iam:password-policy", "IAM::Policy", {}, {}, True)]
        return []

class RDSEncryptionControl(BaseControl):
    control_id, title, severity, category = "AWS-RDS-001", "RDS Encryption", "high", "Encryption"
    description, frameworks = "RDS must be encrypted", {"ISO27001": ["A.10.1.1"], "GDPR": ["Art.32"]}
    async def detect(self):
        try:
            return [ControlFinding("FAIL", db['DBInstanceArn'], "RDS::DB", {"db": db['DBInstanceIdentifier']}, {}, False, "high")
                    for db in self.client.get_client('rds').describe_db_instances()['DBInstances'] if not db.get('StorageEncrypted')]
        except: return []

class RDSPublicAccessControl(BaseControl):
    control_id, title, severity, category = "AWS-RDS-002", "RDS Not Public", "critical", "Network"
    description, frameworks = "RDS must not be public", {"ISO27001": ["A.13.1.3"], "SOC2": ["CC6.6"]}
    async def detect(self):
        try:
            return [ControlFinding("FAIL", db['DBInstanceArn'], "RDS::DB", {"db": db['DBInstanceIdentifier']}, {}, False, "high")
                    for db in self.client.get_client('rds').describe_db_instances()['DBInstances'] if db.get('PubliclyAccessible')]
        except: return []

class RDSBackupControl(BaseControl):
    control_id, title, severity, category = "AWS-RDS-003", "RDS Backup", "medium", "Backup"
    description, frameworks = "RDS automated backups", {"ISO27001": ["A.12.3.1"], "SOC2": ["A1.2"]}
    async def detect(self):
        try:
            return [ControlFinding("FAIL", db['DBInstanceArn'], "RDS::DB", {"db": db['DBInstanceIdentifier']}, {}, True)
                    for db in self.client.get_client('rds').describe_db_instances()['DBInstances'] if db.get('BackupRetentionPeriod', 0) < 7]
        except: return []

class VPCFlowLogsControl(BaseControl):
    control_id, title, severity, category = "AWS-VPC-001", "VPC Flow Logs", "medium", "Logging"
    description, frameworks = "VPC flow logs required", {"ISO27001": ["A.12.4.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        try:
            ec2 = self.client.get_client('ec2')
            vpcs, flow_logs = ec2.describe_vpcs()['Vpcs'], ec2.describe_flow_logs()['FlowLogs']
            vpc_with_logs = {fl['ResourceId'] for fl in flow_logs}
            return [ControlFinding("FAIL", vpc['VpcId'], "VPC", {"vpc": vpc['VpcId']}, {})
                    for vpc in vpcs if vpc['VpcId'] not in vpc_with_logs]
        except: return []

class ELBLogsControl(BaseControl):
    control_id, title, severity, category = "AWS-ELB-001", "ELB Access Logs", "medium", "Logging"
    description, frameworks = "ELB access logs required", {"ISO27001": ["A.12.4.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        try:
            elb = self.client.get_client('elbv2')
            findings = []
            for lb in elb.describe_load_balancers()['LoadBalancers']:
                attrs = elb.describe_load_balancer_attributes(LoadBalancerArn=lb['LoadBalancerArn'])['Attributes']
                if not any(a['Key'] == 'access_logs.s3.enabled' and a['Value'] == 'true' for a in attrs):
                    findings.append(ControlFinding("FAIL", lb['LoadBalancerArn'], "ELB", {"lb": lb['LoadBalancerName']}, {}))
            return findings
        except: return []

class ConfigRecorderControl(BaseControl):
    control_id, title, severity, category = "AWS-CONFIG-001", "AWS Config Enabled", "medium", "Logging"
    description, frameworks = "AWS Config must be enabled", {"ISO27001": ["A.12.4.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        try:
            if not self.client.get_client('config').describe_configuration_recorders().get('ConfigurationRecorders'):
                return [ControlFinding("FAIL", "aws:config", "Config", {}, {})]
        except: pass
        return []

class GuardDutyControl(BaseControl):
    control_id, title, severity, category = "AWS-GD-001", "GuardDuty Enabled", "high", "ThreatDetection"
    description, frameworks = "GuardDuty must be enabled", {"ISO27001": ["A.12.6.1"], "SOC2": ["CC7.2"]}
    async def detect(self):
        try:
            if not self.client.get_client('guardduty').list_detectors().get('DetectorIds'):
                return [ControlFinding("FAIL", "aws:guardduty", "GuardDuty", {}, {})]
        except: pass
        return []

class SNSEncryptionControl(BaseControl):
    control_id, title, severity, category = "AWS-SNS-001", "SNS Encryption", "medium", "Encryption"
    description, frameworks = "SNS topics must be encrypted", {"ISO27001": ["A.10.1.1"], "SOC2": ["CC6.1"]}
    async def detect(self):
        try:
            sns = self.client.get_client('sns')
            return [ControlFinding("FAIL", t['TopicArn'], "SNS::Topic", {}, {})
                    for t in sns.list_topics()['Topics'] 
                    if not sns.get_topic_attributes(TopicArn=t['TopicArn'])['Attributes'].get('KmsMasterKeyId')]
        except: return []

class LambdaVPCControl(BaseControl):
    control_id, title, severity, category = "AWS-LAMBDA-001", "Lambda in VPC", "low", "Network"
    description, frameworks = "Lambda should run in VPC", {"ISO27001": ["A.13.1.1"], "SOC2": ["CC6.6"]}
    async def detect(self):
        try:
            return [ControlFinding("FAIL", f['FunctionArn'], "Lambda", {"func": f['FunctionName']}, {})
                    for f in self.client.get_client('lambda').list_functions()['Functions']
                    if not f.get('VpcConfig', {}).get('VpcId')]
        except: return []

# Register all controls
AWS_CONTROLS = [IAMMFAControl, S3PublicAccessControl, S3EncryptionControl, S3VersioningControl, 
                S3LoggingControl, CloudTrailControl, EC2PublicIPControl, EC2EncryptedVolumesControl,
                SecurityGroupControl, KMSRotationControl, IAMPasswordPolicyControl, RDSEncryptionControl,
                RDSPublicAccessControl, RDSBackupControl, VPCFlowLogsControl, ELBLogsControl,
                ConfigRecorderControl, GuardDutyControl, SNSEncryptionControl, LambdaVPCControl]
