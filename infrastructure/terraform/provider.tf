terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "economic-indicators-terraform-state"
    key            = "economic-indicators-monitor/terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    dynamodb_table = "economic-indicators-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "economic-indicators-monitor"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}