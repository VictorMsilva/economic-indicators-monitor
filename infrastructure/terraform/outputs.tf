output "bucket_name" {
  description = "Name of the S3 data lake bucket"
  value       = module.data_lake_bucket.bucket_name
}

output "bucket_arn" {
  description = "ARN of the S3 data lake bucket"
  value       = module.data_lake_bucket.bucket_arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB state table"
  value       = aws_dynamodb_table.sgs_indicators_state.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB state table"
  value       = aws_dynamodb_table.sgs_indicators_state.arn
}