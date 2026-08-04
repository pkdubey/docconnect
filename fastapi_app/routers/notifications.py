from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/")
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.notifications.models import Notification
    qs = Notification.objects.filter(user=current_user)
    if is_read is not None:
        qs = qs.filter(is_read=is_read)
    total = qs.count()
    results = qs[(page - 1) * page_size: page * page_size]
    return {
        "total": total, "page": page,
        "results": [{
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "deep_link": n.deep_link,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        } for n in results],
    }


@router.patch("/{notification_id}/read/")
async def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone
    updated = Notification.objects.filter(id=notification_id, user=current_user).update(
        is_read=True, read_at=timezone.now()
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/read-all/")
async def mark_all_read(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    from django.utils import timezone
    count = Notification.objects.filter(user=current_user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return {"success": True, "marked_read": count}


@router.get("/unread-count/")
async def unread_count(current_user=Depends(get_current_user)):
    from apps.notifications.models import Notification
    count = Notification.objects.filter(user=current_user, is_read=False).count()
    return {"unread_count": count}
