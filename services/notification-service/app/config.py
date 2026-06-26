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
    environment:     str = "development"
    log_level:       str = "info"
    port:            int = 8004
    aws_region:      str = "ap-south-1"
    allowed_origins: str = "*"

    # Production email (AWS SES)
    ses_from_email:  str = "noreply@helia.health"

    # Development email (Mailhog)
    mail_host: str = "mailhog"
    mail_port: int = 1025

    redis_host:     str = "redis"
    redis_port:     int = 6379
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/2"

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
            "redis_password": s.get("redis_password", ""),
        })
    return base


settings = get_settings()
