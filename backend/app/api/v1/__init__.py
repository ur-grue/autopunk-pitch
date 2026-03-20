"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.billing import router as billing_router
from app.api.v1.export import router as export_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.platform_profiles import router as profiles_router
from app.api.v1.projects import router as projects_router
from app.api.v1.subtitles import router as subtitles_router

router = APIRouter()
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(jobs_router, tags=["jobs"])
router.include_router(export_router, tags=["export"])
router.include_router(subtitles_router, tags=["subtitles"])
router.include_router(billing_router, tags=["billing"])
router.include_router(profiles_router, tags=["platform-profiles"])
