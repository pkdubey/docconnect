from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


# ── Response Schemas ──────────────────────────────────────────

class NotificationOut(BaseModel):
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


# ── Helper ────────────────────────────────────────────────────

def _notif_dict(n) -> NotificationOut:
    return NotificationOut(
        id=str(n.id),
        type=n.type,
        title=n.title,
        body=n.body,
        data=n.data_json,
        deep_link=n.deep_link,
        is_read=n.is_read,
        created_at=n.created_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.get(
    "/unread-count/",
    response_model=UnreadCountResponse,
    summary="Get unread notification count",
)
async def unread_count(current_user=Depends(get_current_user)):
    """Returns the number of unread notifications for the authenticated user."""
    from apps.notifications.models import Notification

    def _count():
        return Notification.objects.filter(user=current_user, is_read=False).count()

    count = await sync_to_async(_count, thread_sensitive=True)()
    return UnreadCountResponse(unread_count=count)


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications",
)
async def list_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user=Depends(get_current_user),
):
    """
    Returns paginated notifications for the authenticated user.

    - **is_read**: optional filter — `true` for read, `false` for unread
    - **page** / **page_size**: pagination controls
    """
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
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread,
        results=[_notif_dict(n) for n in results],
    )


@router.patch(
    "/{notification_id}/read/",
    response_model=MarkReadResponse,
    summary="Mark a notification as read",
)
async def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    """Marks a single notification as read. Returns 404 if not found or not owned by user."""
    from apps.notifications.models import Notification
    from django.utils import timezone

    def _mark():
        updated = Notification.objects.filter(
            id=notification_id, user=current_user
        ).update(is_read=True, read_at=timezone.now())
        return updated

    updated = await sync_to_async(_mark, thread_sensitive=True)()
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return MarkReadResponse(success=True, notification_id=notification_id, is_read=True)


@router.post(
    "/read-all/",
    response_model=MarkAllReadResponse,
    summary="Mark all notifications as read",
)
async def mark_all_read(current_user=Depends(get_current_user)):
    """Marks all unread notifications as read. Returns count of notifications marked."""
    from apps.notifications.models import Notification
    from django.utils import timezone

    def _mark_all():
        return Notification.objects.filter(user=current_user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    count = await sync_to_async(_mark_all, thread_sensitive=True)()
    return MarkAllReadResponse(success=True, marked_read=count)
