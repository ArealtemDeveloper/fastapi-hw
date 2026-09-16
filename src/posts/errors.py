class PostNotFoundError(Exception):
    pass


class AuthorNotFoundError(Exception):
    pass


class PostPermissionError(Exception):
    pass


class PostDebounceError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Please wait before creating another post")
