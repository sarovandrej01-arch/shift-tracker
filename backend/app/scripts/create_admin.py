import asyncio
import getpass
import sys

from pydantic import ValidationError

from app.core.enums import UserRole
from app.core.exceptions.user import UserAlreadyExistsError
from app.db.session import async_session_maker
from app.repositories.user.repository import UserRepository
from app.schemas.user import UserCreate
from app.services.user.service import UserService


def build_admin_create(
    *,
    email: str,
    full_name: str,
    password: str,
    password_repeat: str,
) -> UserCreate:
    if not full_name.strip():
        raise ValueError("Full name is required")
    if password != password_repeat:
        raise ValueError("Passwords do not match")
    return UserCreate(
        email=email.strip(),
        full_name=full_name.strip(),
        password=password,
        role=UserRole.ADMIN,
        is_active=True,
    )


def _read_admin_create() -> UserCreate:
    email = input("Email: ")
    full_name = input("Full name: ")
    password = getpass.getpass("Password: ")
    password_repeat = getpass.getpass("Repeat password: ")
    try:
        return build_admin_create(
            email=email,
            full_name=full_name,
            password=password,
            password_repeat=password_repeat,
        )
    except ValidationError as exc:
        messages = [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()]
        raise SystemExit("\n".join(messages)) from None
    except ValueError as exc:
        raise SystemExit(str(exc)) from None


async def create_admin() -> None:
    data = _read_admin_create()
    async with async_session_maker() as session:
        repository = UserRepository(session)
        if await repository.count_admins() > 0:
            answer = input("An active or inactive administrator already exists. Create another? [y/N]: ")
            if answer.strip().lower() != "y":
                raise SystemExit("Cancelled")
        service = UserService(repository=repository, session=session)
        try:
            user = await service.create_user(data)
        except UserAlreadyExistsError:
            raise SystemExit("A user with this email already exists") from None
    print(f"Administrator created: {user.email}")


def main() -> None:
    try:
        asyncio.run(create_admin())
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
