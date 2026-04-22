import os


# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

# S3
#TODO: Use a secrets manager for AWS credentials in production
S3_BUCKET = os.environ.get("S3_BUCKET", "cryptopus-models")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)

# Inference
INFERENCE_INTERVAL_SECONDS = int(os.environ.get("INFERENCE_INTERVAL_SECONDS", "60"))
INFERENCE_DEVICE = os.environ.get("INFERENCE_DEVICE", "cpu")

# ElegantRL path — required to unpickle act.pth
#TODO: make sure this is set correctly in production
ELEGANTRL_PATH = os.environ.get("ELEGANTRL_PATH", "/app/elegantrl")

# Local model override for development (skips S3 download)
LOCAL_MODEL_PATH = os.environ.get("LOCAL_MODEL_PATH", None)
LOCAL_METADATA_PATH = os.environ.get("LOCAL_METADATA_PATH", None)


# Environment
ENV = os.environ.get("ENV", "development")