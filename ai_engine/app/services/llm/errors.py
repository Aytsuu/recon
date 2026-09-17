class LLMCompletionError(Exception):
    def __init__(self, message: str = "LLM completion failed.") -> None:
        self.message = message
        super().__init__(message)
