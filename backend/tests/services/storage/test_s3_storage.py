import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import StorageConfigurationError
from app.services.storage import S3Storage


def _storage(client: AsyncMock, *, presigned_url_expire_seconds: int = 3600) -> tuple[S3Storage, MagicMock]:
    storage = S3Storage(
        endpoint_url="http://localhost:9000",
        access_key="access-key",
        secret_key="secret-key",
        bucket="shift-tracker",
        region="us-east-1",
        presigned_url_expire_seconds=presigned_url_expire_seconds,
    )
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=None)
    storage.session = MagicMock()
    storage.session.client = MagicMock(return_value=context)
    return storage, context


def test_upload_sends_content_type() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, context = _storage(client)

        await storage.upload(
            key="telegram/2026/10/03/photo.jpg",
            data=b"photo-data",
            content_type="image/jpeg",
        )

        client.put_object.assert_awaited_once_with(
            Bucket="shift-tracker",
            Key="telegram/2026/10/03/photo.jpg",
            Body=b"photo-data",
            ContentType="image/jpeg",
        )
        context.__aenter__.assert_awaited()

    asyncio.run(scenario())


def test_upload_without_content_type_omits_content_type() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, _context = _storage(client)

        await storage.upload(key="telegram/photo.jpg", data=b"photo-data")

        kwargs = client.put_object.await_args.kwargs
        assert "ContentType" not in kwargs
        assert kwargs["Body"] == b"photo-data"

    asyncio.run(scenario())


def test_upload_strips_leading_slash() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, _context = _storage(client)

        await storage.upload(key="/telegram/photo.jpg", data=b"photo-data")

        assert client.put_object.await_args.kwargs["Key"] == "telegram/photo.jpg"

    asyncio.run(scenario())


def test_empty_key_is_rejected() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, _context = _storage(client)

        with pytest.raises(ValueError, match="storage key must not be empty"):
            await storage.upload(key="   ", data=b"photo-data")

        client.put_object.assert_not_called()

    asyncio.run(scenario())


def test_delete_calls_delete_object() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, _context = _storage(client)

        await storage.delete(key="/telegram/photo.jpg")

        client.delete_object.assert_awaited_once_with(
            Bucket="shift-tracker",
            Key="telegram/photo.jpg",
        )

    asyncio.run(scenario())


def test_presigned_url_uses_get_object() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        client.generate_presigned_url.return_value = "https://example.test/photo"
        storage, _context = _storage(client)

        url = await storage.get_presigned_url(key="telegram/photo.jpg", expires_seconds=900)

        assert url == "https://example.test/photo"
        client.generate_presigned_url.assert_awaited_once_with(
            "get_object",
            Params={"Bucket": "shift-tracker", "Key": "telegram/photo.jpg"},
            ExpiresIn=900,
        )

    asyncio.run(scenario())


def test_presigned_url_uses_public_endpoint_and_upload_uses_internal() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        client.generate_presigned_url.return_value = "http://localhost:9000/shift-tracker/photo"
        storage = S3Storage(
            endpoint_url="http://minio:9000",
            public_endpoint_url="http://localhost:9000",
            access_key="access-key",
            secret_key="secret-key",
            bucket="shift-tracker",
            region="us-east-1",
        )
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=client)
        context.__aexit__ = AsyncMock(return_value=None)
        storage.session = MagicMock()
        storage.session.client = MagicMock(return_value=context)

        await storage.upload(key="telegram/photo.jpg", data=b"photo", content_type="image/jpeg")
        await storage.get_presigned_url(key="telegram/photo.jpg")

        endpoints = [call.kwargs["endpoint_url"] for call in storage.session.client.call_args_list]
        assert endpoints == ["http://minio:9000", "http://localhost:9000"]

    asyncio.run(scenario())


def test_presigned_url_falls_back_to_internal_endpoint() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        client.generate_presigned_url.return_value = "http://minio:9000/shift-tracker/photo"
        storage, _context = _storage(client)

        await storage.upload(key="telegram/photo.jpg", data=b"photo", content_type="image/jpeg")
        await storage.get_presigned_url(key="telegram/photo.jpg")

        endpoints = [call.kwargs["endpoint_url"] for call in storage.session.client.call_args_list]
        assert endpoints == ["http://localhost:9000", "http://localhost:9000"]

    asyncio.run(scenario())


@pytest.mark.parametrize("expires_seconds", [0, -1])
def test_invalid_expiration_is_rejected(expires_seconds: int) -> None:
    async def scenario() -> None:
        client = AsyncMock()
        storage, _context = _storage(client)

        with pytest.raises(ValueError, match="expires_seconds"):
            await storage.get_presigned_url(key="telegram/photo.jpg", expires_seconds=expires_seconds)

        client.generate_presigned_url.assert_not_called()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("kwargs", "setting_name"),
    [
        ({"bucket": None}, "S3_BUCKET"),
        ({"bucket": "  "}, "S3_BUCKET"),
        ({"access_key": None}, "S3_ACCESS_KEY"),
        ({"secret_key": ""}, "S3_SECRET_KEY"),
        ({"endpoint_url": None}, "S3_ENDPOINT_URL"),
    ],
)
def test_missing_config_is_rejected(kwargs: dict[str, str | None], setting_name: str) -> None:
    config = {
        "endpoint_url": "http://localhost:9000",
        "access_key": "access-key",
        "secret_key": "secret-key",
        "bucket": "shift-tracker",
    }
    config.update(kwargs)

    with pytest.raises(StorageConfigurationError, match=setting_name):
        S3Storage(**config)


def test_constructor_expiration_is_used_by_default() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        client.generate_presigned_url.return_value = "https://example.test/photo"
        storage, _context = _storage(client, presigned_url_expire_seconds=1800)

        await storage.get_presigned_url(key="telegram/photo.jpg")

        assert client.generate_presigned_url.await_args.kwargs["ExpiresIn"] == 1800

    asyncio.run(scenario())


@pytest.mark.parametrize("presigned_url_expire_seconds", [0, -1])
def test_invalid_constructor_expiration_is_rejected(presigned_url_expire_seconds: int) -> None:
    with pytest.raises(ValueError, match="presigned_url_expire_seconds"):
        S3Storage(
            endpoint_url="http://localhost:9000",
            access_key="access-key",
            secret_key="secret-key",
            bucket="shift-tracker",
            region="us-east-1",
            presigned_url_expire_seconds=presigned_url_expire_seconds,
        )


def test_s3_exception_is_not_swallowed() -> None:
    async def scenario() -> None:
        client = AsyncMock()
        client.put_object.side_effect = RuntimeError("s3 unavailable")
        storage, _context = _storage(client)

        with pytest.raises(RuntimeError, match="s3 unavailable"):
            await storage.upload(key="telegram/photo.jpg", data=b"photo-data")

    asyncio.run(scenario())
