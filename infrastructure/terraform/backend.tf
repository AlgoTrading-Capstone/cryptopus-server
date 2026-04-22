# Terraform state backend configuration
#
# The state file tracks all resources Terraform has created.
# It's stored remotely so multiple developers can share it.
#
# For LocalStack: state is stored in a local S3 bucket (fake)
# For production: state is stored in a real S3 bucket with DynamoDB locking

terraform {
  backend "s3" {
    bucket = "cryptopus-terraform-state"
    key    = "cryptopus/terraform.tfstate"
    region = "us-east-1"

    # LocalStack endpoint — remove this block for real AWS
    endpoint                    = "http://localhost:4566"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    force_path_style            = true

    # Fake credentials for LocalStack
    access_key = "test"
    secret_key = "test"
  }
}