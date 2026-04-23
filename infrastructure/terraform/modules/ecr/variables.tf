variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "services" {
  description = "List of services to create ECR repositories for"
  type        = list(string)
  default     = ["api", "trading-engine", "rl-inference"]
}