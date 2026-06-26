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
    environment:     str = "production"
    log_level:       str = "info"
    port:            int = 8006
    aws_region:      str = "ap-south-1"
    allowed_origins: str = "*"
    s3_bucket:       str = "helia-files"

    # MongoDB — values come from Secrets Manager
    mongo_host:     str = "mongodb"
    mongo_port:     int = 27017
    mongo_user:     str = ""
    mongo_password: str = ""
    mongo_db:       str = ""

    auth_service_url: str = "http://auth-service:8001"

    @property
    def mongo_url(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}?authSource=admin"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    base = Settings()
    s = load_aws_secrets()
    return Settings(**{
        **base.model_dump(),
        "mongo_user":     s.get("mongo_user", ""),
        "mongo_password": s.get("mongo_password", ""),
        "mongo_db":       s.get("mongo_db", ""),
    })


settings = get_settings()
