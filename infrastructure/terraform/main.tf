# VPC - networking foundation everything else depends on
module "vpc" {
  source = "./modules/vpc"

  project            = var.project
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# S3 - models bucket and terraform state bucket
module "s3" {
  source = "./modules/s3"

  project     = var.project
  environment = var.environment
}

# ECR - Docker image repositories per service
module "ecr" {
  source = "./modules/ecr"

  project     = var.project
  environment = var.environment
  services    = ["api", "trading-engine", "rl-inference"]
}

# RDS - PostgreSQL + TimescaleDB
module "rds" {
  source = "./modules/rds"

  project            = var.project
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.vpc.rds_security_group_id
  db_username        = var.db_username
  db_password        = var.db_password
}

# ElastiCache - Redis
module "elasticache" {
  source = "./modules/elasticache"

  project            = var.project
  environment        = var.environment
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.vpc.redis_security_group_id
}

# Secrets Manager - credentials and API keys
module "secrets" {
  source = "./modules/secrets"

  project           = var.project
  environment       = var.environment
  db_username       = var.db_username
  db_password       = var.db_password
  db_endpoint       = module.rds.db_endpoint
  redis_endpoint    = module.elasticache.redis_endpoint
  django_secret_key = var.django_secret_key
  jwt_secret        = var.jwt_secret
}

# EKS - Kubernetes cluster
module "eks" {
  source = "./modules/eks"

  project                     = var.project
  environment                 = var.environment
  vpc_id                      = module.vpc.vpc_id
  private_subnet_ids          = module.vpc.private_subnet_ids
  eks_nodes_security_group_id = module.vpc.eks_nodes_security_group_id
  db_credentials_arn          = module.secrets.db_credentials_arn
  django_secret_arn           = module.secrets.django_secret_arn
  models_bucket_arn           = module.s3.models_bucket_arn
}

# WAF - web application firewall attached to ALB
# Note: ALB is created by the Kubernetes Ingress controller
# WAF association happens after ALB ARN is known
module "waf" {
  source = "./modules/waf"

  project     = var.project
  environment = var.environment
  alb_arn     = var.alb_arn
}