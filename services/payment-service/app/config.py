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
    port:             int = 8005
    aws_region:       str = "ap-south-1"
    allowed_origins:  str = "*"
    postgres_host:    str = "postgres"
    postgres_port:    int = 5432
    postgres_user:    str = ""
    postgres_password: str = ""
    db_name:          str = ""
    auth_service_url: str = "http://auth-service:8001"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.db_name}"

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
            "postgres_user":     s.get("postgres_user", ""),
            "postgres_password": s.get("postgres_password", ""),
            "db_name":           s.get("postgres_payment_db", ""),
        })
    return base


settings = get_settings()
