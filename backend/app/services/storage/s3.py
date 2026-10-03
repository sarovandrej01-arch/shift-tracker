import aioboto3

from app.core.exceptions.storage import StorageConfigurationError
from app.services.storage.base import ObjectStorage


def _normalize_key(key: str) -> str:
    normalized = key.strip().lstrip("/")
    if not normalized:
        raise ValueError("storage key must not be empty")
    return normalized


def _require_setting(value: str | None, name: str) -> str:
    if value is None or not value.strip():
        raise StorageConfigurationError(f"{name} is not configured")
    return value.strip()


class S3Storage(ObjectStorage):
    def __init__(
        self,
        *,
        endpoint_url: str | None,
        access_key: str | None,
        secret_key: str | None,
        bucket: str | None,
        region: str | None = None,
        presigned_url_expire_seconds: int = 3600,
        public_endpoint_url: str | None = None,
    ) -> None:
        self.endpoint_url = _require_setting(endpoint_url, "S3_ENDPOINT_URL")
        public_endpoint = public_endpoint_url.strip() if public_endpoint_url and public_endpoint_url.strip() else ""
        self.public_endpoint_url = public_endpoint or self.endpoint_url
        self.bucket = _require_setting(bucket, "S3_BUCKET")
        access_key = _require_setting(access_key, "S3_ACCESS_KEY")
        secret_key = _require_setting(secret_key, "S3_SECRET_KEY")
        if presigned_url_expire_seconds <= 0:
            raise ValueError("presigned_url_expire_seconds must be greater than 0")
        self.presigned_url_expire_seconds = presigned_url_expire_seconds
        self.session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region.strip() if region and region.strip() else None,
        )

    def _client(self, *, endpoint_url: str | None = None):
        return self.session.client("s3", endpoint_url=endpoint_url or self.endpoint_url)

    async def upload(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> None:
        normalized_key = _normalize_key(key)
        if not isinstance(data, bytes):
            raise ValueError("storage data must be bytes")

        payload: dict[str, object] = {
            "Bucket": self.bucket,
            "Key": normalized_key,
            "Body": data,
        }
        if content_type is not None:
            payload["ContentType"] = content_type

        async with self._client() as client:
            await client.put_object(**payload)

    async def delete(self, *, key: str) -> None:
        normalized_key = _normalize_key(key)
        async with self._client() as client:
            await client.delete_object(Bucket=self.bucket, Key=normalized_key)

    async def get_presigned_url(
        self,
        *,
        key: str,
        expires_seconds: int | None = None,
    ) -> str:
        expires = expires_seconds if expires_seconds is not None else self.presigned_url_expire_seconds
        if expires <= 0:
            raise ValueError("expires_seconds must be greater than 0")
        normalized_key = _normalize_key(key)
        async with self._client(endpoint_url=self.public_endpoint_url) as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": normalized_key},
                ExpiresIn=expires,
            )
