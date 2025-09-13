# Data Lake S3 Bucket
module "data_lake_bucket" {
  source = "./modules/s3"
  
  bucket_name = var.bucket_name
  environment = var.environment
  
  enable_versioning      = false
  enable_intelligent_tiering = true
}

# DynamoDB table for Lambda state management
resource "aws_dynamodb_table" "sgs_indicators_state" {
  name           = "sgs-indicators-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "indicator"

  attribute {
    name = "indicator"
    type = "S"
  }

  tags = {
    Name = "SGS Indicators State"
  }
}