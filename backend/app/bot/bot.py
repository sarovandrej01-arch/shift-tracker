from aiogram import Bot

from app.core.config import settings
from app.services.storage import S3Storage


def create_bot() -> Bot:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    return Bot(token=settings.bot_token)


def create_storage() -> S3Storage:
    return S3Storage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        region=settings.s3_region,
        presigned_url_expire_seconds=settings.s3_presigned_url_expire_seconds,
    )
