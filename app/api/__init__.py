from fastapi import APIRouter
from .auth import router as auth_router
from .designs import router as designs_router
from .passes import router as passes_router
from .stats import router as stats_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(designs_router)
api_router.include_router(passes_router)
api_router.include_router(stats_router) 