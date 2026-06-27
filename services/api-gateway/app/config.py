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
    environment:                 str = "production"
    log_level:                   str = "info"
    port:                        int = 8000
    aws_region:                  str = "ap-south-1"
    redis_host:                  str = "redis"
    redis_port:                  int = 6379
    redis_password:              str = ""
    auth_service_url:            str = "http://auth-service:8001"
    user_service_url:            str = "http://user-service:8002"
    appointment_service_url:     str = "http://appointment-service:8003"
    notification_service_url:    str = "http://notification-service:8004"
    payment_service_url:         str = "http://payment-service:8005"
    medical_records_service_url: str = "http://medical-records-service:8006"
    search_service_url:          str = "http://search-service:8007"

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    base = Settings()
    s = load_aws_secrets()
    return Settings(**{
        **base.model_dump(),
        "redis_password": s.get("redis_password", ""),
    })


settings = get_settings()
