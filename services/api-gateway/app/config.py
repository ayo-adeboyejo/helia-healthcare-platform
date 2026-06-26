import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment:                 str = "production"
    log_level:                   str = "info"
    port:                        int = 8000
    redis_host:                  str = "redis"
    redis_port:                  int = 6379
    redis_password:              str = "helia_dev_redis"
    auth_service_url:            str = "http://auth-service:8001"
    user_service_url:            str = "http://user-service:8002"
    appointment_service_url:     str = "http://appointment-service:8003"
    notification_service_url:    str = "http://notification-service:8004"
    payment_service_url:         str = "http://payment-service:8005"
    medical_records_service_url: str = "http://medical-records-service:8006"
    search_service_url:          str = "http://search-service:8007"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
