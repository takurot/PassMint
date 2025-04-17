from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .api import api_router
from .schemas.auth import ErrorResponse

# Create FastAPI app
app = FastAPI(
    title="PassMint API",
    description="API for PassMint, a service to issue and manage mobile wallet passes",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error={
                "code": "VALIDATION_ERROR",
                "message": str(exc),
            }
        ).dict(),
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "PassMint API",
        "version": "0.1.0",
        "status": "online",
    }


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"} 