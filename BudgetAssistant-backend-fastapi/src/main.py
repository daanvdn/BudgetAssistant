"""FastAPI main application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routers import (
    analysis_router,
    auth_router,
    bank_accounts_router,
    budget_router,
    categories_router,
    rules_router,
    transactions_router,
)


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
app.include_router(auth_router, prefix="/api")
app.include_router(bank_accounts_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(budget_router, prefix="/api")
app.include_router(rules_router, prefix="/api")


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
        port=8000,
        reload=True,
    )
