from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends
from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/masters", tags=["Master Data"])


@router.get("/specialties/")
async def list_specialties(current_user=Depends(get_current_user)):
    from apps.core.models import Specialization
    items = await sync_to_async(
        lambda: list(Specialization.objects.filter(is_active=True).values("id", "name")),
        thread_sensitive=True,
    )()
    return {"results": [{"id": str(i["id"]), "name": i["name"]} for i in items]}


@router.get("/qualifications/")
async def list_qualifications(current_user=Depends(get_current_user)):
    from apps.core.models import Qualification
    items = await sync_to_async(
        lambda: list(Qualification.objects.filter(is_active=True).values("id", "name")),
        thread_sensitive=True,
    )()
    return {"results": [{"id": str(i["id"]), "name": i["name"]} for i in items]}


@router.get("/councils/")
async def list_councils(current_user=Depends(get_current_user)):
    from apps.core.models import Council
    items = await sync_to_async(
        lambda: list(Council.objects.filter(is_active=True).values("id", "name", "short")),
        thread_sensitive=True,
    )()
    return {"results": [{"id": str(i["id"]), "name": i["name"], "short": i["short"]} for i in items]}


@router.get("/job-types/")
async def list_job_types(current_user=Depends(get_current_user)):
    return {"results": [
        {"value": "FULL_TIME", "label": "Full Time"},
        {"value": "PART_TIME", "label": "Part Time"},
        {"value": "VISITING", "label": "Visiting"},
        {"value": "LOCUM", "label": "Locum"},
        {"value": "CONTRACT", "label": "Contract"},
    ]}


@router.get("/shift-types/")
async def list_shift_types(current_user=Depends(get_current_user)):
    return {"results": [
        {"value": "DAY", "label": "Day"},
        {"value": "NIGHT", "label": "Night"},
        {"value": "ROTATIONAL", "label": "Rotational"},
        {"value": "FLEXIBLE", "label": "Flexible"},
    ]}
