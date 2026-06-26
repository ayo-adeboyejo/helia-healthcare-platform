"""
shared/secrets.py
Fetches all secrets from AWS Secrets Manager at startup.
Every service imports this module to get credentials.
The EC2 IAM role provides authentication automatically —
no access keys needed anywhere in the code.
"""
import boto3
import json
import os
import logging

logger = logging.getLogger(__name__)


def get_secrets(secret_name: str = "helia/production", region: str = "ap-south-1") -> dict:
    """
    Fetch secrets from AWS Secrets Manager.
    Falls back to environment variables for local development.
    """
    # In local development, skip Secrets Manager and use env vars
    if os.getenv("ENVIRONMENT", "development") == "development":
        logger.info("Development mode — using environment variables instead of Secrets Manager")
        return {}

    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response["SecretString"])
        logger.info(f"Successfully loaded secrets from {secret_name}")
        return secrets
    except Exception as e:
        logger.error(f"Failed to load secrets from Secrets Manager: {e}")
        raise RuntimeError(f"Cannot start service — failed to load secrets: {e}")
