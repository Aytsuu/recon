class TokenIssuanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class TokenIssuanceFailedError(TokenIssuanceError):
    def __init__(self, message: str = "Streaming token could not be issued.") -> None:
        super().__init__("token_issuance_failed", message)


class TokenServiceUnavailableError(TokenIssuanceError):
    def __init__(self, message: str = "Streaming token service is unavailable.") -> None:
        super().__init__("token_service_unavailable", message)
