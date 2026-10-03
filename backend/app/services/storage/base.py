from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    async def upload(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    async def delete(self, *, key: str) -> None:
        ...

    @abstractmethod
    async def get_presigned_url(
        self,
        *,
        key: str,
        expires_seconds: int = 3600,
    ) -> str:
        ...
