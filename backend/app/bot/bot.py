import logging
from urllib.parse import urlparse

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from app.core.config import settings
from app.services.storage import S3Storage

logger = logging.getLogger(__name__)

# aiohttp-socks 0.12, used by aiogram 3 AiohttpSession, accepts these schemes.
# socks5 is created with remote DNS resolution. https and socks5h are rejected.
SUPPORTED_TELEGRAM_PROXY_SCHEMES = frozenset({"http", "socks4", "socks5"})


def normalize_telegram_proxy_url(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    parsed = urlparse(stripped)
    if parsed.scheme not in SUPPORTED_TELEGRAM_PROXY_SCHEMES:
        supported = ", ".join(sorted(SUPPORTED_TELEGRAM_PROXY_SCHEMES))
        raise ValueError(f"TELEGRAM_PROXY_URL scheme must be one of: {supported}")
    if not parsed.hostname or parsed.port is None:
        raise ValueError("TELEGRAM_PROXY_URL must include a host and port")
    return stripped


def create_telegram_session(proxy_url: str | None) -> AiohttpSession | None:
    normalized = normalize_telegram_proxy_url(proxy_url)
    if normalized is None:
        return None
    return AiohttpSession(proxy=normalized)


def create_bot() -> Bot:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")
    session = create_telegram_session(settings.telegram_proxy_url)
    if session is None:
        return Bot(token=settings.bot_token)
    logger.info("Telegram proxy configured")
    return Bot(token=settings.bot_token, session=session)


def create_storage() -> S3Storage:
    return S3Storage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket,
        region=settings.s3_region,
        presigned_url_expire_seconds=settings.s3_presigned_url_expire_seconds,
        public_endpoint_url=settings.s3_public_endpoint_url,
    )
