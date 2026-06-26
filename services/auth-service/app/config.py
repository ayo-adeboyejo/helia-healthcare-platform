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
    # Application
    environment:     str = "development"
    log_level:       str = "info"
    port:            int = 8001
    aws_region:      str = "ap-south-1"
    allowed_origins: str = "*"

    # PostgreSQL
    postgres_host:    str = "postgres"
    postgres_port:    int = 5432
    postgres_user:    str = "helia"
    postgres_password: str = "helia_dev_password"
    db_name:          str = "authdb"

    # Redis
    redis_host:     str = "redis"
    redis_port:     int = 6379
    redis_password: str = "helia_dev_redis"

    # JWT — used directly from .env in development
    jwt_secret:                      str = "dev_jwt_secret_change_in_production"
    jwt_algorithm:                   str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days:   int = 7

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    base = Settings()

    # In production overlay with AWS Secrets Manager values
    if base.environment == "production":
        s = load_aws_secrets()
        return Settings(**{
            **base.model_dump(),
            "postgres_user":                   s.get("postgres_user", ""),
            "postgres_password":               s.get("postgres_password", ""),
            "db_name":                         s.get("postgres_auth_db", ""),
            "redis_password":                  s.get("redis_password", ""),
            "jwt_secret":                      s.get("jwt_secret", ""),
            "jwt_algorithm":                   s.get("jwt_algorithm", "HS256"),
            "jwt_access_token_expire_minutes": int(s.get("jwt_access_token_expire_minutes", 60)),
            "jwt_refresh_token_expire_days":   int(s.get("jwt_refresh_token_expire_days", 7)),
        })
    return base


settings = get_settings()
