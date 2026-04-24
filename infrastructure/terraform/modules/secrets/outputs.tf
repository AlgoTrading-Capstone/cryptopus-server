output "db_credentials_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "django_secret_arn" {
  description = "ARN of the Django secrets"
  value       = aws_secretsmanager_secret.django.arn
}

output "kraken_keys_path" {
  description = "Base path for Kraken API keys in Secrets Manager"
  value       = "${var.project}/${var.environment}/kraken-keys"
}