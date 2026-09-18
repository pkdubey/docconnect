from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])
notif_prefs_router = APIRouter(prefix="/api/v1/notification-preferences", tags=["Notifications"])


# ── Schemas ───────────────────────────────────────────────────

class NotificationOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "type": "JOB_ALERT",
        "title": "New job match", "body": "Apollo Hospital posted a Cardiologist role",
        "data": {"job_id": "550e8400-e29b-41d4-a716-446655440001"},
        "deep_link": "/jobs/550e8400-e29b-41d4-a716-446655440001",
        "is_read": False, "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    type: str
    title: str
    body: Optional[str]
    data: Optional[Dict[str, Any]]
    deep_link: Optional[str]
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    unread_count: int
    results: List[NotificationOut]


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    success: bool
    notification_id: str
    is_read: bool


class MarkAllReadResponse(BaseModel):
    success: bool
    marked_read: int


DEFAULT_PREFS = {
    "CONNECTION_REQUEST": {"in_app": True, "push": True},
    "CONNECTION_ACCEPTED": {"in_app": True, "push": True},
    "POST_INTERACTION": {"in_app": True, "push": True},
    "NEW_MESSAGE": {"in_app": True, "push": True},
    "RECOMMENDED_JOB": {"in_app": True, "push": True},
    "APPLICATION_UPDATE": {"in_app": True, "push": True},
    "INTERVIEW_UPDATE": {"in_app": True, "push": True},
    "SHIFT_REQUEST": {"in_app": True, "push": True},
    "SHIFT_ACCEPTED": {"in_app": True, "push": True},
    "SHIFT_CONFIRMED": {"in_app": True, "push": True},
    "SHIFT_CANCELLED": {"in_app": True, "push": True},
    "VERIFICATION_UPDATE": {"in_app": True, "push": True},
    "REPORT_UPDATE": {"in_app": True, "push": False},
    "SUPPORT_UPDATE": {"in_app": True, "push": True},
}


# ── Helper ────────────────────────────────────────────────────

def _notif_dict(n) -> NotificationOut:
    return NotificationOut(
        id=str(n.id), type=n.type, title=n.title, body=n.body,
        data=n.data_json, deep_link=n.deep_link,
        is_read=n.is_read, created_at=n.created_at.isoformat(),
    )


# ── Notification endpoints ────────────────────────────────────

@router.get("/unread-count/", response_model=UnreadCountResponse)
async def unread_count(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    count = await sync_to_async(
        lambda: Notification.objects.filter(user=current_user, is_read=False).count(),
        thread_sensitive=True,
    )()
    return UnreadCountResponse(unread_count=count)


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.notifications.models import Notification

    def _list():
        qs = Notification.objects.filter(user=current_user)
        if is_read is not None:
            qs = qs.filter(is_read=is_read)
        total = qs.count()
        unread = Notification.objects.filter(user=current_user, is_read=False).count()
        results = list(qs.order_by('-created_at')[(page - 1) * page_size: page * page_size])
        return total, unread, results

    total, unread, results = await sync_to_async(_list, thread_sensitive=True)()
    return NotificationListResponse(
        total=total, page=page, page_size=page_size,
        unread_count=unread, results=[_notif_dict(n) for n in results],
    )


@router.patch("/{notification_id}/read/", response_model=MarkReadResponse)
async def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone

    updated = await sync_to_async(
        lambda: Notification.objects.filter(id=notification_id, user=current_user)
        .update(is_read=True, read_at=timezone.now()),
        thread_sensitive=True,
    )()
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return MarkReadResponse(success=True, notification_id=notification_id, is_read=True)


@router.post("/read-all/", response_model=MarkAllReadResponse)
async def mark_all_read(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone

    count = await sync_to_async(
        lambda: Notification.objects.filter(user=current_user, is_read=False)
        .update(is_read=True, read_at=timezone.now()),
        thread_sensitive=True,
    )()
    return MarkAllReadResponse(success=True, marked_read=count)


# ── Notification Preferences ──────────────────────────────────

@notif_prefs_router.get("/", summary="Get per-event notification preferences")
async def get_notification_preferences(current_user=Depends(get_current_user)):
    prefs = current_user.metadata.get("notification_preferences", DEFAULT_PREFS)
    return {"preferences": prefs}


class NotifPrefsUpdate(BaseModel):
    preferences: Dict[str, Any]


@notif_prefs_router.put("/", summary="Update notification preferences")
async def update_notification_preferences(
    body: NotifPrefsUpdate,
    current_user=Depends(get_current_user),
):
    def _update():
        current_user.metadata["notification_preferences"] = body.preferences
        current_user.save(update_fields=["metadata"])

    await sync_to_async(_update, thread_sensitive=True)()
    return {"success": True, "preferences": body.preferences}
