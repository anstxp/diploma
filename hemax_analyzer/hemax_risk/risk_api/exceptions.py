from __future__ import annotations

from fastapi import HTTPException, status


class RiskAPIError(HTTPException):

    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestError(RiskAPIError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_400_BAD_REQUEST)


class ValidationError(RiskAPIError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AnalysisError(RiskAPIError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelNotLoadedError(RiskAPIError):
    def __init__(self, detail: str = "Risk model not loaded"):
        super().__init__(detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
