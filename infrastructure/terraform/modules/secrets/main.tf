# Database credentials secret
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project}/${var.environment}/db-credentials"
  description = "PostgreSQL credentials for Cryptopus"

  tags = {
    Name        = "${var.project}-db-credentials-${var.environment}"
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    endpoint = var.db_endpoint
    dbname   = "cryptopus"
    port     = 5432
  })
}

# Django application secrets
resource "aws_secretsmanager_secret" "django" {
  name        = "${var.project}/${var.environment}/django"
  description = "Django application secrets"

  tags = {
    Name        = "${var.project}-django-${var.environment}"
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "django" {
  secret_id = aws_secretsmanager_secret.django.id

  secret_string = jsonencode({
    secret_key     = var.django_secret_key
    jwt_secret     = var.jwt_secret
    redis_endpoint = var.redis_endpoint
  })
}

# Placeholder for Kraken API keys per user
# Individual user keys are stored here by the API service at runtime
resource "aws_secretsmanager_secret" "kraken_keys_template" {
  name        = "${var.project}/${var.environment}/kraken-keys/template"
  description = "Template path for per-user Kraken API keys. Actual keys stored as kraken-keys/{user_id}"

  tags = {
    Name        = "${var.project}-kraken-keys-${var.environment}"
    Project     = var.project
    Environment = var.environment
  }
}