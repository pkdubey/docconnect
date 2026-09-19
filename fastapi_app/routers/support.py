from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(tags=["Support"])


class TicketCreate(BaseModel):
    subject: str
    description: str
    category: str = "GENERAL"


class TicketMessageCreate(BaseModel):
    message: str
    is_internal: bool = False  # admin-only internal note


class TicketStatusUpdate(BaseModel):
    status: str


# ── User-facing support ───────────────────────────────────────

@router.post("/api/v1/support/tickets/", status_code=201)
async def create_ticket(body: TicketCreate, current_user=Depends(get_current_user)):
    def _create():
        from apps.core.models import SupportTicket
        t = SupportTicket.objects.create(
            user=current_user,
            subject=body.subject,
            description=body.description,
            category=body.category,
        )
        return t

    t = await sync_to_async(_create, thread_sensitive=True)()
    return {"success": True, "ticket_id": str(t.id), "status": t.status}


@router.get("/api/v1/support/tickets/")
async def list_my_tickets(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    def _list():
        from apps.core.models import SupportTicket
        qs = SupportTicket.objects.filter(user=current_user)
        if status:
            qs = qs.filter(status=status)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "tickets": [{
            "id": str(t.id), "subject": t.subject, "category": t.category,
            "status": t.status, "created_at": t.created_at.isoformat(),
        } for t in results]
    }


@router.get("/api/v1/support/tickets/{ticket_id}/")
async def get_ticket(ticket_id: str, current_user=Depends(get_current_user)):
    def _get():
        from apps.core.models import SupportTicket
        try:
            t = SupportTicket.objects.prefetch_related('messages__sender').get(
                id=ticket_id, user=current_user
            )
        except SupportTicket.DoesNotExist:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return t

    try:
        t = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "id": str(t.id), "subject": t.subject, "description": t.description,
        "category": t.category, "status": t.status,
        "created_at": t.created_at.isoformat(),
        "messages": [{
            "id": str(m.id), "message": m.message,
            "sender_id": str(m.sender_id),
            "is_internal": m.is_internal,
            "created_at": m.created_at.isoformat(),
        } for m in t.messages.filter(is_internal=False)],
    }


@router.post("/api/v1/support/tickets/{ticket_id}/messages/", status_code=201)
async def add_ticket_message(
    ticket_id: str, body: TicketMessageCreate, current_user=Depends(get_current_user)
):
    def _add():
        from apps.core.models import SupportTicket, SupportMessage
        try:
            t = SupportTicket.objects.get(id=ticket_id, user=current_user)
        except SupportTicket.DoesNotExist:
            raise HTTPException(status_code=404, detail="Ticket not found")
        m = SupportMessage.objects.create(
            ticket=t, sender=current_user, message=body.message, is_internal=False
        )
        return m

    try:
        m = await sync_to_async(_add, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "message_id": str(m.id)}


# ── Admin support management ──────────────────────────────────

@router.get("/api/v1/admin/support/tickets/")
async def admin_list_tickets(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    def _list():
        from apps.core.models import SupportTicket
        qs = SupportTicket.objects.select_related('user', 'assigned_to')
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "tickets": [{
            "id": str(t.id), "subject": t.subject, "category": t.category,
            "status": t.status, "user_id": str(t.user_id),
            "user_phone": t.user.phone, "created_at": t.created_at.isoformat(),
        } for t in results]
    }


@router.get("/api/v1/admin/support/tickets/{ticket_id}/")
async def admin_get_ticket(ticket_id: str, current_user=Depends(get_current_user)):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    def _get():
        from apps.core.models import SupportTicket
        try:
            t = SupportTicket.objects.select_related('user', 'assigned_to').prefetch_related('messages__sender').get(id=ticket_id)
        except SupportTicket.DoesNotExist:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return t

    try:
        t = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "id": str(t.id), "subject": t.subject, "description": t.description,
        "category": t.category, "status": t.status,
        "user_id": str(t.user_id), "user_phone": t.user.phone,
        "assigned_to": str(t.assigned_to_id) if t.assigned_to_id else None,
        "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
        "created_at": t.created_at.isoformat(),
        "messages": [{
            "id": str(m.id), "message": m.message,
            "sender_id": str(m.sender_id), "is_internal": m.is_internal,
            "created_at": m.created_at.isoformat(),
        } for m in t.messages.all()],
    }


@router.patch("/api/v1/admin/support/tickets/{ticket_id}/")
async def admin_update_ticket(
    ticket_id: str, body: TicketStatusUpdate, current_user=Depends(get_current_user)
):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    def _update():
        from apps.core.models import SupportTicket
        updated = SupportTicket.objects.filter(id=ticket_id).update(status=body.status)
        if not updated:
            raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "ticket_id": ticket_id, "status": body.status}


class TicketAssign(BaseModel):
    admin_user_id: str


@router.post("/api/v1/admin/support/tickets/{ticket_id}/assign/")
async def admin_assign_ticket(ticket_id: str, body: TicketAssign, current_user=Depends(get_current_user)):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    def _assign():
        from django.contrib.auth import get_user_model
        from apps.core.models import SupportTicket
        User = get_user_model()
        try:
            assignee = User.objects.get(id=body.admin_user_id, user_type='ADMIN')
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="Admin user not found")
        updated = SupportTicket.objects.filter(id=ticket_id).update(
            assigned_to=assignee, status='IN_PROGRESS'
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        await sync_to_async(_assign, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "ticket_id": ticket_id, "assigned_to": body.admin_user_id}


@router.post("/api/v1/admin/support/tickets/{ticket_id}/resolve/")
async def admin_resolve_ticket(ticket_id: str, current_user=Depends(get_current_user)):
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    from django.utils import timezone

    def _resolve():
        from apps.core.models import SupportTicket
        updated = SupportTicket.objects.filter(id=ticket_id).update(
            status='RESOLVED', resolved_at=timezone.now()
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        await sync_to_async(_resolve, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "ticket_id": ticket_id, "status": "RESOLVED"}


@router.post("/api/v1/admin/support/tickets/{ticket_id}/messages/", status_code=201)
async def admin_add_ticket_message(
    ticket_id: str, body: TicketMessageCreate, current_user=Depends(get_current_user)
):
    """Admin can add public replies or internal notes to any ticket."""
    if current_user.user_type != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    def _add():
        from apps.core.models import SupportTicket, SupportMessage
        try:
            t = SupportTicket.objects.get(id=ticket_id)
        except SupportTicket.DoesNotExist:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if t.status == 'CLOSED':
            raise HTTPException(status_code=409, detail="Ticket is closed")
        m = SupportMessage.objects.create(
            ticket=t, sender=current_user,
            message=body.message, is_internal=body.is_internal
        )
        return m

    try:
        m = await sync_to_async(_add, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "message_id": str(m.id)}
