#!/usr/bin/env bash
set -euo pipefail

# Terraform backend setup script
# Creates S3 bucket and DynamoDB table for remote state management

BACKEND_BUCKET="economic-indicators-terraform-state"
BACKEND_TABLE="economic-indicators-terraform-locks"
REGION="us-east-2"

echo "Setting up Terraform backend infrastructure..."

# Create S3 bucket for state
if ! aws s3api head-bucket --bucket "$BACKEND_BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BACKEND_BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint=$REGION
  echo "Created backend bucket: $BACKEND_BUCKET"
else
  echo "Backend bucket already exists: $BACKEND_BUCKET"
fi

# Configure bucket security
aws s3api put-public-access-block --bucket "$BACKEND_BUCKET" \
  --public-access-block-configuration '{"BlockPublicAcls":true,"IgnorePublicAcls":true,"BlockPublicPolicy":true,"RestrictPublicBuckets":true}'

aws s3api put-bucket-encryption --bucket "$BACKEND_BUCKET" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws s3api put-bucket-versioning --bucket "$BACKEND_BUCKET" \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locks
if ! aws dynamodb describe-table --table-name "$BACKEND_TABLE" --no-cli-pager 2>/dev/null; then
  aws dynamodb create-table \
    --table-name "$BACKEND_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --no-cli-pager
  echo "Created DynamoDB table: $BACKEND_TABLE"
  
  # Wait for table to be active
  aws dynamodb wait table-exists --table-name "$BACKEND_TABLE"
else
  echo "DynamoDB table already exists: $BACKEND_TABLE"
fi

echo "✅ Backend infrastructure ready!"
echo
echo "Backend configuration:"
echo "  Bucket: $BACKEND_BUCKET"
echo "  Table: $BACKEND_TABLE"
echo "  Region: $REGION"