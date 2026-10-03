class InvalidDateRangeError(Exception):
    def __init__(self, detail: str = "date_from must be less than or equal to date_to") -> None:
        self.detail = detail
        super().__init__(detail)
