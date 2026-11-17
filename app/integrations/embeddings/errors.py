from app.core.errors import AppError


class EmbeddingUnavailableError(AppError):
    status_code = 503
    message = "Knowledge search is temporarily unavailable"
