import logging
from unittest.mock import patch

import pytest

from app.bot.bot import create_bot, create_telegram_session, normalize_telegram_proxy_url


def test_missing_proxy_url_is_none() -> None:
    assert normalize_telegram_proxy_url(None) is None
    assert normalize_telegram_proxy_url("") is None
    assert normalize_telegram_proxy_url("   ") is None
    assert create_telegram_session(None) is None
    assert create_telegram_session("") is None


def test_http_proxy_is_attached_to_session() -> None:
    proxy_url = "http://user:s3cret-proxy-pass@proxy.example.com:3128"

    session = create_telegram_session(proxy_url)

    assert session is not None
    assert session.proxy == proxy_url


def test_socks5_proxy_is_attached_to_session() -> None:
    proxy_url = "socks5://user:s3cret-proxy-pass@proxy.example.com:1080"

    session = create_telegram_session(proxy_url)

    assert session is not None
    assert session.proxy == proxy_url


@pytest.mark.parametrize(
    "proxy_url",
    [
        "https://proxy.example.com:443",
        "socks5h://proxy.example.com:1080",
        "ftp://proxy.example.com:21",
        "proxy.example.com:1080",
        "http://proxy.example.com",
        "socks5://",
    ],
)
def test_unsupported_proxy_url_is_rejected(proxy_url: str) -> None:
    with pytest.raises(ValueError, match="TELEGRAM_PROXY_URL"):
        create_telegram_session(proxy_url)


def test_bot_without_proxy_uses_direct_session() -> None:
    with patch("app.bot.bot.settings") as settings:
        settings.bot_token = "000000000:TEST_TOKEN"
        settings.telegram_proxy_url = ""
        bot = create_bot()

    assert bot.session.proxy is None


def test_proxy_secret_is_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    proxy_url = "socks5://user:s3cret-proxy-pass@proxy.example.com:1080"

    with patch("app.bot.bot.settings") as settings:
        settings.bot_token = "000000000:TEST_TOKEN"
        settings.telegram_proxy_url = proxy_url
        with caplog.at_level(logging.INFO):
            bot = create_bot()

    assert bot.session.proxy == proxy_url
    assert "Telegram proxy configured" in caplog.text
    assert proxy_url not in caplog.text
    assert "s3cret-proxy-pass" not in caplog.text
    assert "proxy.example.com" not in caplog.text
