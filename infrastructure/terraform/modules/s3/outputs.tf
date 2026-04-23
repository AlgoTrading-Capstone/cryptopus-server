output "models_bucket_name" {
  description = "Name of the S3 bucket for RL models"
  value       = aws_s3_bucket.models.bucket
}

output "models_bucket_arn" {
  description = "ARN of the S3 bucket for RL models"
  value       = aws_s3_bucket.models.arn
}

output "terraform_state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}