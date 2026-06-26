import os, sys, json, logging, boto3
from functools import lru_cache
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


def load_aws_secrets() -> dict:
    try:
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "ap-south-1"))
        response = client.get_secret_value(SecretId="helia/production")
        return json.loads(response["SecretString"])
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        sys.exit(1)


class Settings(BaseSettings):
    environment:      str = "development"
    log_level:        str = "info"
    port:             int = 8006
    aws_region:       str = "ap-south-1"
    allowed_origins:  str = "*"
    s3_bucket:        str = "helia-files"

    # S3 / MinIO — endpoint only set in development (MinIO)
    # In production, endpoint is None and IAM role handles auth
    s3_endpoint:   str = ""   # empty = use real AWS S3
    s3_access_key: str = ""   # empty = use IAM role
    s3_secret_key: str = ""   # empty = use IAM role

    # MongoDB
    mongo_host:     str = "mongodb"
    mongo_port:     int = 27017
    mongo_user:     str = ""
    mongo_password: str = ""
    mongo_db:       str = ""

    # Mail (dev only — Mailhog)
    mail_host: str = ""
    mail_port: int = 1025

    auth_service_url: str = "http://auth-service:8001"

    @property
    def mongo_url(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}?authSource=admin"
        )

    @property
    def using_minio(self) -> bool:
        """True in development when MinIO is the storage backend."""
        return self.environment == "development" and bool(self.s3_endpoint)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    base = Settings()
    if base.environment == "production":
        s = load_aws_secrets()
        return Settings(**{
            **base.model_dump(),
            "mongo_user":     s.get("mongo_user", ""),
            "mongo_password": s.get("mongo_password", ""),
            "mongo_db":       s.get("mongo_db", ""),
        })
    return base


settings = get_settings()
