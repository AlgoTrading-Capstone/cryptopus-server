variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "alb_arn" {
  description = "ARN of the ALB to associate WAF with"
  type        = string
}