from app.core.errors import AppError


class LLMNotConfiguredError(AppError):
    status_code = 503
    message = "AI assistant is not configured"


class LLMUnavailableError(AppError):
    status_code = 503
    message = "AI assistant is temporarily unavailable"


class LLMTimeoutError(AppError):
    status_code = 504
    message = "AI assistant took too long to respond"
