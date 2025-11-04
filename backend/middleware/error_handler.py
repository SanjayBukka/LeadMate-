"""
Error Handler Middleware
Centralized error handling for the API
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pymongo.errors import PyMongoError
from bson.errors import InvalidId

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware
    Catches and formats all exceptions
    """
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        logger.warning(f"Validation error: {e.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": e.errors()
            }
        )
    except InvalidId as e:
        logger.warning(f"Invalid ID format: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Invalid ID format",
                "error": str(e)
            }
        )
    except PyMongoError as e:
        logger.error(f"Database error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database operation failed",
                "error": "Internal server error"
            }
        )
    except StarletteHTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(e) if logger.level <= logging.DEBUG else "An unexpected error occurred"
            }
        )

