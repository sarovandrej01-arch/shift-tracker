class ReviewConfirmationIncompleteError(Exception):
    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = missing_fields
        super().__init__("Missing confirmation data: " + ", ".join(missing_fields))
