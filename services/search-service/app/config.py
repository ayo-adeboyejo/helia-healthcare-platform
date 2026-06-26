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
    environment:         str = "development"
    log_level:           str = "info"
    port:                int = 8007
    aws_region:          str = "ap-south-1"
    allowed_origins:     str = "*"
    elasticsearch_host:  str = "elasticsearch"
    elasticsearch_port:  int = 9200
    elastic_username:    str = "elastic"
    elastic_password:    str = ""
    auth_service_url:    str = "http://auth-service:8001"

    @property
    def elasticsearch_url(self) -> str:
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"

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
            "elastic_username": s.get("elastic_username", "elastic"),
            "elastic_password": s.get("elastic_password", ""),
        })
    return base


settings = get_settings()
