variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "use_localstack" {
  description = "Set to true to use LocalStack instead of real AWS"
  type        = bool
  default     = true
}

variable "aws_access_key" {
  description = "AWS access key (not needed for LocalStack)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key (not needed for LocalStack)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "cryptopus"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
  default     = "cryptopus123"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "cryptopus"
}