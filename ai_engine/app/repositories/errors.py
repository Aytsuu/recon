class RepositoryError(Exception):
    def __init__(self, message: str = "Repository operation failed.") -> None:
        self.message = message
        super().__init__(message)
