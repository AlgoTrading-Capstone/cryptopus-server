terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS provider - points to LocalStack for local development
provider "aws" {
  region = var.aws_region

  # LocalStack configuration
  # When running locally, all API calls go to LocalStack instead of real AWS
  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      ec2            = "http://localhost:4566"
      eks            = "http://localhost:4566"
      rds            = "http://localhost:4566"
      elasticache    = "http://localhost:4566"
      s3             = "http://localhost:4566"
      ecr            = "http://localhost:4566"
      secretsmanager = "http://localhost:4566"
      iam            = "http://localhost:4566"
      route53        = "http://localhost:4566"
      wafv2          = "http://localhost:4566"
      elbv2          = "http://localhost:4566"
    }
  }

  # LocalStack does not require real credentials
  # These are dummy values used only for local development
  access_key = var.use_localstack ? "test" : var.aws_access_key
  secret_key = var.use_localstack ? "test" : var.aws_secret_key

  # Skip validations that fail against LocalStack
  skip_credentials_validation = var.use_localstack
  skip_requesting_account_id  = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  s3_use_path_style           = var.use_localstack
}