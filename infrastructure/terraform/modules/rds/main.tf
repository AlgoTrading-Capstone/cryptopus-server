# Subnet group - tells RDS which subnets it can use
# RDS requires at least 2 subnets in different AZs for high availability
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-rds-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project}-rds-subnet-group-${var.environment}"
    Project     = var.project
    Environment = var.environment
  }
}

# RDS PostgreSQL instance
resource "aws_db_instance" "main" {
  identifier = "${var.project}-postgres-${var.environment}"

  # Engine
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class

  # Storage
  allocated_storage     = var.allocated_storage
  storage_type          = "gp2"
  storage_encrypted     = true

  # Credentials
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  publicly_accessible    = false

  # Backup
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Prevent accidental deletion
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment == "prod" ? false : true

  tags = {
    Name        = "${var.project}-postgres-${var.environment}"
    Project     = var.project
    Environment = var.environment
  }
}