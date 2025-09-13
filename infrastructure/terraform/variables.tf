variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "economic-indicators-monitor"
}

variable "bucket_name" {
  description = "S3 bucket name for data lake"
  type        = string
  default     = "dl-economic-indicators-prod"
}