from enum import Enum


class MessageStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REVIEW = "review"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    ERROR = "error"


class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"


class MessageReason(str, Enum):
    NO_PHOTO = "no_photo"
    EMPLOYEE_NOT_FOUND = "employee_not_found"
    EMPLOYEE_AMBIGUOUS = "employee_ambiguous"
    GROUP_NOT_CONFIGURED = "group_not_configured"
    OUTSIDE_SHIFT_WINDOW = "outside_shift_window"
    SHIFT_ALREADY_EXISTS = "shift_already_exists"
    MESSAGE_ALREADY_PROCESSED = "message_already_processed"
    INTERNAL_ERROR = "internal_error"
