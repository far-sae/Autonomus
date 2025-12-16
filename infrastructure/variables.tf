variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "complianceadmin"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "evidence_bucket_name" {
  description = "S3 bucket name for evidence storage"
  type        = string
  default     = "compliance-evidence-prod"
}
