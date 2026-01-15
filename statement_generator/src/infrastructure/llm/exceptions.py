"""
Provider-specific exceptions for error handling and fallback logic.
"""


class ProviderLimitError(Exception):
    """Raised when provider hits rate limit or usage cap"""

    def __init__(self, provider: str, message: str, retryable: bool = True):
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"{provider}: {message}")


class ProviderAuthError(Exception):
    """Raised when provider authentication fails"""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class ProviderError(Exception):
    """General provider error"""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}")
