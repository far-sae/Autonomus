import boto3
from typing import Any, Dict, Optional
from botocore.exceptions import ClientError
import json


class AWSClient:
    """AWS client wrapper for compliance scanning."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize AWS client.
        
        Args:
            credentials: Dict with 'role_arn' or 'access_key_id' and 'secret_access_key'
        """
        self.credentials = credentials
        self.session = self._create_session()
    
    def _create_session(self):
        """Create boto3 session using provided credentials."""
        try:
            if 'role_arn' in self.credentials:
                # Try to assume role if base credentials are available
                try:
                    sts = boto3.client('sts')
                    assumed_role = sts.assume_role(
                        RoleArn=self.credentials['role_arn'],
                        RoleSessionName='ComplianceScanner'
                    )
                    return boto3.Session(
                        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
                        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
                        aws_session_token=assumed_role['Credentials']['SessionToken']
                    )
                except Exception as e:
                    # If assume role fails, return a session for dry-run mode
                    # This allows testing without actual AWS credentials
                    print(f"Warning: Could not assume role {self.credentials['role_arn']}: {e}")
                    print("Creating session without credentials for dry-run/demo mode")
                    return boto3.Session()
            elif 'access_key_id' in self.credentials:
                return boto3.Session(
                    aws_access_key_id=self.credentials['access_key_id'],
                    aws_secret_access_key=self.credentials['secret_access_key'],
                    region_name=self.credentials.get('region', 'us-east-1')
                )
            else:
                # Use default credentials (environment variables, EC2 role, etc.)
                return boto3.Session()
        except Exception as e:
            print(f"Warning: Error creating AWS session: {e}")
            return boto3.Session()
    
    def get_client(self, service_name: str, region: Optional[str] = None):
        """Get boto3 client for a specific service."""
        return self.session.client(service_name, region_name=region)
    
    def get_resource(self, service_name: str, region: Optional[str] = None):
        """Get boto3 resource for a specific service."""
        return self.session.resource(service_name, region_name=region)
    
    # IAM Methods
    def list_users(self):
        """List all IAM users."""
        iam = self.get_client('iam')
        paginator = iam.get_paginator('list_users')
        users = []
        for page in paginator.paginate():
            users.extend(page['Users'])
        return users
    
    def get_user_mfa_devices(self, username: str):
        """Get MFA devices for a user."""
        iam = self.get_client('iam')
        try:
            response = iam.list_mfa_devices(UserName=username)
            return response.get('MFADevices', [])
        except ClientError:
            return []
    
    def list_access_keys(self, username: str):
        """List access keys for a user."""
        iam = self.get_client('iam')
        try:
            response = iam.list_access_keys(UserName=username)
            return response.get('AccessKeyMetadata', [])
        except ClientError:
            return []
    
    def get_credential_report(self):
        """Get IAM credential report."""
        iam = self.get_client('iam')
        try:
            # Generate report
            iam.generate_credential_report()
            # Get report (may need retries in production)
            response = iam.get_credential_report()
            return response['Content'].decode('utf-8')
        except ClientError:
            return None
    
    def list_user_policies(self, username: str):
        """List inline policies for a user."""
        iam = self.get_client('iam')
        try:
            response = iam.list_user_policies(UserName=username)
            return response.get('PolicyNames', [])
        except ClientError:
            return []
    
    def list_attached_user_policies(self, username: str):
        """List attached policies for a user."""
        iam = self.get_client('iam')
        try:
            response = iam.list_attached_user_policies(UserName=username)
            return response.get('AttachedPolicies', [])
        except ClientError:
            return []
    
    # S3 Methods
    def list_buckets(self):
        """List all S3 buckets."""
        s3 = self.get_client('s3')
        response = s3.list_buckets()
        return response.get('Buckets', [])
    
    def get_bucket_acl(self, bucket_name: str):
        """Get bucket ACL."""
        s3 = self.get_client('s3')
        try:
            return s3.get_bucket_acl(Bucket=bucket_name)
        except ClientError:
            return None
    
    def get_bucket_policy(self, bucket_name: str):
        """Get bucket policy."""
        s3 = self.get_client('s3')
        try:
            response = s3.get_bucket_policy(Bucket=bucket_name)
            return json.loads(response['Policy'])
        except ClientError:
            return None
    
    def get_bucket_encryption(self, bucket_name: str):
        """Get bucket encryption configuration."""
        s3 = self.get_client('s3')
        try:
            return s3.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return None
            raise
    
    def get_bucket_versioning(self, bucket_name: str):
        """Get bucket versioning status."""
        s3 = self.get_client('s3')
        try:
            return s3.get_bucket_versioning(Bucket=bucket_name)
        except ClientError:
            return None
    
    def get_bucket_logging(self, bucket_name: str):
        """Get bucket logging configuration."""
        s3 = self.get_client('s3')
        try:
            return s3.get_bucket_logging(Bucket=bucket_name)
        except ClientError:
            return None
    
    def get_public_access_block(self, bucket_name: str):
        """Get public access block configuration."""
        s3 = self.get_client('s3')
        try:
            return s3.get_public_access_block(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                return None
            raise
    
    # EC2 Methods
    def describe_security_groups(self, region: Optional[str] = None):
        """Describe security groups."""
        ec2 = self.get_client('ec2', region)
        paginator = ec2.get_paginator('describe_security_groups')
        groups = []
        for page in paginator.paginate():
            groups.extend(page['SecurityGroups'])
        return groups
    
    def describe_instances(self, region: Optional[str] = None):
        """Describe EC2 instances."""
        ec2 = self.get_client('ec2', region)
        paginator = ec2.get_paginator('describe_instances')
        instances = []
        for page in paginator.paginate():
            for reservation in page['Reservations']:
                instances.extend(reservation['Instances'])
        return instances
    
    def describe_volumes(self, region: Optional[str] = None):
        """Describe EBS volumes."""
        ec2 = self.get_client('ec2', region)
        paginator = ec2.get_paginator('describe_volumes')
        volumes = []
        for page in paginator.paginate():
            volumes.extend(page['Volumes'])
        return volumes
    
    def describe_snapshots(self, owner_id: str, region: Optional[str] = None):
        """Describe EBS snapshots."""
        ec2 = self.get_client('ec2', region)
        try:
            response = ec2.describe_snapshots(OwnerIds=[owner_id])
            return response.get('Snapshots', [])
        except ClientError:
            return []
    
    # CloudTrail Methods
    def describe_trails(self, region: Optional[str] = None):
        """Describe CloudTrail trails."""
        cloudtrail = self.get_client('cloudtrail', region)
        try:
            response = cloudtrail.describe_trails()
            return response.get('trailList', [])
        except ClientError:
            return []
    
    def get_trail_status(self, trail_name: str, region: Optional[str] = None):
        """Get CloudTrail status."""
        cloudtrail = self.get_client('cloudtrail', region)
        try:
            return cloudtrail.get_trail_status(Name=trail_name)
        except ClientError:
            return None
    
    def get_event_selectors(self, trail_name: str, region: Optional[str] = None):
        """Get CloudTrail event selectors."""
        cloudtrail = self.get_client('cloudtrail', region)
        try:
            return cloudtrail.get_event_selectors(TrailName=trail_name)
        except ClientError:
            return None
    
    # KMS Methods
    def list_keys(self, region: Optional[str] = None):
        """List KMS keys."""
        kms = self.get_client('kms', region)
        paginator = kms.get_paginator('list_keys')
        keys = []
        for page in paginator.paginate():
            keys.extend(page['Keys'])
        return keys
    
    def describe_key(self, key_id: str, region: Optional[str] = None):
        """Describe a KMS key."""
        kms = self.get_client('kms', region)
        try:
            response = kms.describe_key(KeyId=key_id)
            return response.get('KeyMetadata')
        except ClientError:
            return None
    
    def get_key_rotation_status(self, key_id: str, region: Optional[str] = None):
        """Get KMS key rotation status."""
        kms = self.get_client('kms', region)
        try:
            response = kms.get_key_rotation_status(KeyId=key_id)
            return response.get('KeyRotationEnabled', False)
        except ClientError:
            return False
