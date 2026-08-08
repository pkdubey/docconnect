from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/unread-count/")
async def unread_count(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification

    def _count():
        return Notification.objects.filter(user=current_user, is_read=False).count()

    count = await sync_to_async(_count, thread_sensitive=True)()
    return {"unread_count": count}


@router.get("/")
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
        results = list(qs.order_by('-created_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{
            "id": str(n.id), "type": n.type, "title": n.title,
            "body": n.body, "deep_link": n.deep_link,
            "is_read": n.is_read, "created_at": n.created_at.isoformat(),
        } for n in results],
    }


@router.patch("/{notification_id}/read/")
async def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone

    def _mark():
        return Notification.objects.filter(id=notification_id, user=current_user).update(
            is_read=True, read_at=timezone.now()
        )

    updated = await sync_to_async(_mark, thread_sensitive=True)()
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/read-all/")
async def mark_all_read(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone

    def _mark_all():
        return Notification.objects.filter(user=current_user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    count = await sync_to_async(_mark_all, thread_sensitive=True)()
    return {"success": True, "marked_read": count}
