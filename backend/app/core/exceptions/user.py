class UserNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class InvalidUserPasswordError(Exception):
    pass


class CannotModifyOwnAdminAccessError(Exception):
    pass


class LastActiveAdminError(Exception):
    pass
