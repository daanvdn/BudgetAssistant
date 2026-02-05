"""FastAPI main application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth.router import router as auth_router
from common.logging_utils import LoggerFactory
from db import init_db
from routers import (
    analysis_router,
    bank_accounts_router,
    budget_router,
    categories_router,
    rules_router,
    transactions_router,
)

# Configure logging
logger = LoggerFactory.for_caller()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="BudgetAssistant API",
    description="FastAPI backend for BudgetAssistant",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")  # auth router already has /api/auth prefix
app.include_router(bank_accounts_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(budget_router, prefix="/api")
app.include_router(rules_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for validation errors (422 Unprocessable Entity).

    Logs detailed information about:
    1. The request method and URL
    2. Query parameters
    3. Request body (if available)
    4. Request headers
    5. Detailed validation errors with field locations and messages
    """
    # Get request body if available
    body = None
    try:
        body = await request.body()
        body = body.decode("utf-8") if body else None
    except Exception:
        body = "<unable to read body>"

    # Format validation errors for logging
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(loc_part) for loc_part in error.get("loc", []))
        error_details.append(
            f"  - Field: {loc}\n"
            f"    Type: {error.get('type', 'unknown')}\n"
            f"    Message: {error.get('msg', 'No message')}\n"
            f"    Input: {error.get('input', 'N/A')}"
        )

    logger.error(
        f"Validation error on {request.method} {request.url}\n"
        f"Query params: {dict(request.query_params)}\n"
        f"Request body: {body}\n"
        f"Headers: {dict(request.headers)}\n"
        f"Validation errors:\n" + "\n".join(error_details),
        exc_info=True,
        stack_info=True,
    )

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.

    This ensures that:
    1. All exceptions are logged with full stack traces
    2. A proper JSON response is returned (allowing CORS headers to be applied)
    """
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True, stack_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to BudgetAssistant API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
