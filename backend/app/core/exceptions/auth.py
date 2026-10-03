class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class MissingTokenError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass
