# System Architecture - Autonomous Compliance Platform

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER ACCESS LAYER                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  Admin Portal  │  │  User Dashboard│  │  Auditor View  │         │
│  │   (React SPA)  │  │   (React SPA)  │  │   (Read-Only)  │         │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘         │
└───────────┼──────────────────┼──────────────────┼────────────────────┘
            │                  │                  │
            └──────────────────┴──────────────────┘
                               │ HTTPS (TLS 1.2+)
┌──────────────────────────────┴────────────────────────────────────────┐
│                      APPLICATION LAYER (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                   API Gateway & Auth                          │    │
│  │  - JWT Authentication  - RBAC  - Rate Limiting               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Detection   │  │ Remediation  │  │   Evidence   │               │
│  │   Engine     │  │   Engine     │  │   Engine     │               │
│  │              │  │              │  │              │               │
│  │ • Scan cloud │  │ • Dry-run    │  │ • Snapshots  │               │
│  │ • Evaluate   │  │ • Approve    │  │ • Audit logs │               │
│  │ • Generate   │  │ • Execute    │  │ • PDF export │               │
│  │   findings   │  │ • Rollback   │  │ • S3 storage │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                  Control Library (20+ controls)               │    │
│  │  AWS-IAM • AWS-S3 • AWS-EC2 • AWS-RDS • AWS-KMS • ...       │    │
│  └──────────────────────────────────────────────────────────────┘    │
└───────────────┬────────────────────────┬──────────────────────────────┘
                │                        │
┌───────────────┴────────────┐  ┌────────┴───────────────┐
│     CLOUD INTEGRATIONS     │  │    DATA PERSISTENCE    │
│  ┌───────────────────────┐ │  │  ┌──────────────────┐  │
│  │   AWS SDK (Boto3)     │ │  │  │  PostgreSQL RDS  │  │
│  │ • IAM • S3 • EC2      │ │  │  │                  │  │
│  │ • RDS • CloudTrail    │ │  │  │ • Multi-AZ       │  │
│  │ • KMS • GuardDuty     │ │  │  │ • Encrypted      │  │
│  └───────────────────────┘ │  │  │ • Auto-backup    │  │
│  ┌───────────────────────┐ │  │  └──────────────────┘  │
│  │   Azure SDK           │ │  │  ┌──────────────────┐  │
│  │ • Entra ID • Storage  │ │  │  │  S3 Evidence     │  │
│  │ • Resource Manager    │ │  │  │                  │  │
│  └───────────────────────┘ │  │  │ • Versioned      │  │
│  ┌───────────────────────┐ │  │  │ • Encrypted      │  │
│  │   Microsoft Graph     │ │  │  │ • Lifecycle      │  │
│  │ • M365 • Users        │ │  │  └──────────────────┘  │
│  └───────────────────────┘ │  └────────────────────────┘
└────────────────────────────┘
```

## Data Flow

### 1. Scan Workflow
```
User → API → Detection Engine → Cloud SDK → Cloud Resources
                    ↓
            Control Evaluation
                    ↓
         Generate Findings → DB
                    ↓
         Store Evidence → S3
                    ↓
         Audit Log → DB (immutable)
```

### 2. Remediation Workflow
```
User Request → Approval Check → Remediation Engine
                                       ↓
                        ┌──────────────┴──────────────┐
                        │                             │
                   [Dry-Run]                     [Execute]
                        │                             │
                Simulate Fix                   Apply Changes
                        │                             │
                 Return Plan                  Update Resource
                                                      ↓
                                              Store Before/After
                                                      ↓
                                              Audit Log (immutable)
                                                      ↓
                                          Mark Finding as FIXED
```

### 3. Evidence Generation
```
Request → Evidence Engine → Query DB (Findings + Audit Logs)
                ↓
        Generate PDF/JSON
                ↓
        Upload to S3 (encrypted)
                ↓
        Generate Pre-signed URL
                ↓
        Return to User
```

## Database Schema (Detailed)

```sql
-- Organizations: Multi-tenant support
organizations
  - id (PK)
  - name
  - compliance_frameworks (JSON: ["ISO27001", "SOC2", "GDPR"])
  - settings (JSON)
  - created_at, updated_at

-- Cloud Accounts: AWS, Azure, M365
cloud_accounts
  - id (PK)
  - organization_id (FK)
  - name
  - provider (aws, azure, m365)
  - account_id
  - region
  - credentials (JSON, encrypted)
  - last_scan_at, last_scan_status
  - created_at, updated_at

-- Controls: Control library
controls
  - id (PK)
  - control_id (UNIQUE: AWS-S3-001)
  - title
  - description
  - category
  - severity
  - frameworks (JSON: {"ISO27001": ["A.13.1.3"]})
  - provider
  - can_auto_remediate
  - remediation_risk

-- Control Results: Scan findings
control_results
  - id (PK)
  - cloud_account_id (FK)
  - control_id
  - status (PASS, FAIL, FIXED, ERROR)
  - risk_level
  - resource_id
  - resource_type
  - finding_details (JSON)
  - evidence_before (JSON)
  - evidence_after (JSON)
  - evidence_s3_key
  - remediation_status
  - remediation_approved_by
  - remediation_executed_at
  - rollback_data (JSON)
  - scan_id
  - detected_at, resolved_at
  - metadata (JSON)

-- Audit Logs: Immutable audit trail
audit_logs
  - id (PK)
  - control_result_id (FK, nullable)
  - event_type (detection, remediation, approval, scan, rollback)
  - action
  - actor (user email or system)
  - cloud_account_id
  - organization_id
  - control_id
  - resource_id
  - event_data (JSON)
  - before_state (JSON)
  - after_state (JSON)
  - ip_address
  - user_agent
  - timestamp (IMMUTABLE)
  - success (success, failure, partial)
  - error_message

-- Users: Authentication & RBAC
users
  - id (PK)
  - email (UNIQUE)
  - hashed_password
  - full_name
  - role (admin, user, auditor)
  - is_active
  - created_at, updated_at
```

## Security Architecture

### Network Security
```
Internet
    ↓
[WAF] → [CloudFront] → [ALB (Public Subnet)]
                            ↓
              [ECS Tasks (Private Subnet)]
                            ↓
              [RDS (Private Subnet)]
                            
All egress via NAT Gateway
```

### Authentication Flow
```
1. User submits credentials
2. FastAPI validates against DB (bcrypt)
3. Generate JWT token (HS256, 30min expiry)
4. Return token to client
5. Client includes token in Authorization header
6. FastAPI validates token on each request
7. Check user role for RBAC
```

### Encryption Layers
- **In Transit**: TLS 1.2+ for all connections
- **At Rest**: 
  - RDS: Encrypted with KMS
  - S3: AES-256 server-side encryption
  - Credentials: Encrypted before storage
- **Application**: JWT tokens, bcrypt password hashing

## Scalability Design

### Horizontal Scaling
- ECS Fargate auto-scaling based on CPU/Memory
- ALB distributes traffic across tasks
- Stateless API design
- Database connection pooling

### Performance Optimization
- Async I/O throughout (FastAPI + SQLAlchemy async)
- Parallel cloud API calls
- Database query optimization with indexes
- Caching for control definitions (in-memory)

### High Availability
- Multi-AZ RDS deployment
- ECS tasks across multiple AZs
- S3 for durable evidence storage
- Health checks and auto-recovery

## Compliance Mappings

```
ISO 27001:
├── A.9.2.1: MFA, password policy
├── A.9.2.6: Credential management
├── A.10.1.1: Encryption at rest
├── A.10.1.2: Key rotation
├── A.12.3.1: Backup retention
├── A.12.4.1: Audit logging
├── A.12.6.1: Threat detection
└── A.13.1.1-3: Network security

SOC 2:
├── CC6.1: Logical access, encryption
├── CC6.2: Authentication
├── CC6.6: Network security
├── CC6.7: Data protection
├── CC7.2: Monitoring, logging
└── A1.2: Backup and recovery

GDPR:
├── Art.32: Security measures
├── Art.25: Privacy by design
└── Art.30: Records of processing
```

## Deployment Architecture (AWS)

```
AWS Region (us-east-1)
│
├── VPC (10.0.0.0/16)
│   ├── Public Subnets (10.0.101.0/24, 10.0.102.0/24)
│   │   ├── ALB
│   │   └── NAT Gateway
│   │
│   └── Private Subnets (10.0.1.0/24, 10.0.2.0/24)
│       ├── ECS Fargate Tasks (Backend)
│       └── RDS PostgreSQL (Multi-AZ)
│
├── S3 Buckets
│   ├── compliance-evidence (versioned, encrypted)
│   └── compliance-frontend (CloudFront)
│
├── IAM
│   ├── ECS Task Execution Role
│   ├── ECS Task Role (S3, STS)
│   └── Scanner Roles (cross-account assume)
│
├── CloudWatch
│   ├── Logs (/ecs/compliance-backend)
│   ├── Metrics (Container Insights)
│   └── Alarms
│
└── Secrets Manager
    ├── DB Password
    ├── JWT Secret
    └── AWS Credentials
```

## Monitoring & Alerting

### Key Metrics
- **Compliance Score**: Track over time
- **Scan Metrics**: Duration, success rate, findings count
- **Remediation Metrics**: Success rate, rollback count
- **API Metrics**: Response time, error rate, throughput
- **Infrastructure**: CPU, memory, disk, network

### Alerts
- Critical findings > threshold
- Scan failures
- Remediation failures
- API error rate > 1%
- Database connection errors
- RDS storage > 80%

### Logging
- **Application Logs**: Structured JSON logs
- **Audit Logs**: Immutable, retained 7 years
- **Infrastructure Logs**: VPC Flow Logs, ALB access logs
- **CloudTrail**: AWS API calls

## Disaster Recovery

### Backup Strategy
- **Database**: Automated daily backups, 7-day retention
- **Evidence**: S3 versioning, cross-region replication
- **Configuration**: Terraform state in S3 backend

### Recovery Procedures
1. **Database Failure**: Restore from latest RDS snapshot
2. **Application Failure**: ECS auto-restart, ALB health checks
3. **Region Failure**: Failover to DR region (manual)

### RTO/RPO Targets
- **RTO**: 4 hours
- **RPO**: 1 hour

---

**Built for enterprise-grade compliance automation with production-ready architecture.**
