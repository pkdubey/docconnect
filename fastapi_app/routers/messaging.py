from typing import List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/messages", tags=["Messaging"])


# ── Request Schemas ───────────────────────────────────────────

class ConversationCreate(BaseModel):
    participant_user_id: str


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = Field("TEXT", pattern=r'^(TEXT|IMAGE|DOCUMENT|SHIFT_REQUEST|JOB_REFERRAL)$')


# ── Response Schemas ──────────────────────────────────────────

class ConversationCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000", "existing": False
    }})
    conversation_id: str
    existing: bool


class ConversationItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000", "type": "DIRECT",
        "last_message": "Hello doctor", "last_message_at": "2025-01-01T00:00:00Z", "last_read_at": None
    }})
    conversation_id: str
    type: str
    last_message: Optional[str]
    last_message_at: Optional[str]
    last_read_at: Optional[str]


class MessageItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "sender_id": "550e8400-e29b-41d4-a716-446655440001",
        "content": "Hello doctor", "message_type": "TEXT",
        "file_id": None, "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    sender_id: str
    content: str
    message_type: str
    file_id: Optional[str]
    created_at: str


class MessagesResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"total": 1, "page": 1, "messages": []}})
    total: int
    page: int
    messages: List[MessageItem]


class SendMessageOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/conversations/", response_model=ConversationCreateOut, status_code=201, summary="Start a conversation")
async def start_conversation(data: ConversationCreate, current_user=Depends(get_current_user)):
    from django.contrib.auth import get_user_model
    from apps.messaging.models import Conversation, ConversationParticipant

    def _create():
        User = get_user_model()
        try:
            other_user = User.objects.get(id=data.participant_user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        existing = (
            ConversationParticipant.objects.filter(user=current_user, conversation__type='DIRECT')
            .values_list('conversation_id', flat=True)
        )
        shared = ConversationParticipant.objects.filter(
            user=other_user, conversation_id__in=list(existing)
        ).first()
        if shared:
            return str(shared.conversation_id), True
        conv = Conversation.objects.create(type='DIRECT')
        ConversationParticipant.objects.bulk_create([
            ConversationParticipant(conversation=conv, user=current_user),
            ConversationParticipant(conversation=conv, user=other_user),
        ])
        return str(conv.id), False

    try:
        conv_id, existing = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return ConversationCreateOut(conversation_id=conv_id, existing=existing)


@router.get("/conversations/", response_model=List[ConversationItem], summary="List my conversations")
async def list_conversations(current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant, Message

    def _list():
        participants = (
            ConversationParticipant.objects
            .filter(user=current_user, is_active=True)
            .select_related('conversation')
            .order_by('-conversation__updated_at')
        )
        result = []
        for p in participants:
            last_msg = Message.objects.filter(conversation=p.conversation).order_by('-created_at').first()
            result.append(ConversationItem(
                conversation_id=str(p.conversation_id),
                type=p.conversation.type,
                last_message=last_msg.content if last_msg else None,
                last_message_at=last_msg.created_at.isoformat() if last_msg else None,
                last_read_at=p.last_read_at.isoformat() if p.last_read_at else None,
            ))
        return result

    return await sync_to_async(_list, thread_sensitive=True)()


@router.get("/conversations/{conversation_id}/messages/", response_model=MessagesResponse, summary="Get messages in a conversation")
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.messaging.models import ConversationParticipant, Message
    from django.utils import timezone

    def _get():
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user, is_active=True
        ).exists():
            raise HTTPException(status_code=403, detail="Not a participant")
        ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user
        ).update(last_read_at=timezone.now())
        qs = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at')
        total = qs.count()
        messages = list(qs[(page - 1) * page_size: page * page_size])
        return total, messages

    try:
        total, messages = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return MessagesResponse(
        total=total, page=page,
        messages=[MessageItem(
            id=str(m.id), sender_id=str(m.sender_id),
            content=m.content, message_type=m.message_type,
            file_id=str(m.file_id) if m.file_id else None,
            created_at=m.created_at.isoformat(),
        ) for m in messages],
    )


@router.post("/conversations/{conversation_id}/messages/", response_model=SendMessageOut, status_code=201, summary="Send a message")
async def send_message(conversation_id: str, data: MessageCreate, current_user=Depends(get_current_user)):
    from apps.messaging.models import Conversation, ConversationParticipant, Message

    def _send():
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user, is_active=True
        ).exists():
            raise HTTPException(status_code=403, detail="Not a participant")
        msg = Message.objects.create(
            conversation_id=conversation_id, sender=current_user,
            content=data.content, message_type=data.message_type,
        )
        Conversation.objects.filter(id=conversation_id).update(updated_at=msg.created_at)
        return msg

    try:
        msg = await sync_to_async(_send, thread_sensitive=True)()
    except HTTPException:
        raise
    return SendMessageOut(id=str(msg.id), created_at=msg.created_at.isoformat())


@router.post("/conversations/{conversation_id}/read/", summary="Mark conversation as read")
async def mark_conversation_read(conversation_id: str, current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant
    from django.utils import timezone

    updated = await sync_to_async(
        lambda: ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user
        ).update(last_read_at=timezone.now()),
        thread_sensitive=True,
    )()
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@router.post("/conversations/{conversation_id}/report/", status_code=201, summary="Report a conversation")
async def report_conversation(conversation_id: str, reason: str = "SPAM", current_user=Depends(get_current_user)):
    def _report():
        from apps.core.models import Report
        from apps.messaging.models import ConversationParticipant
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user, is_active=True
        ).exists():
            raise HTTPException(status_code=404, detail="Conversation not found")
        Report.objects.create(
            reporter=current_user,
            target_type='CONVERSATION',
            target_id=conversation_id,
            reason=reason if reason in [
                'SPAM', 'HARASSMENT', 'PATIENT_PRIVACY_CONCERN',
                'POTENTIAL_MEDICAL_MISINFORMATION', 'OTHER_POLICY_VIOLATION',
            ] else 'OTHER_POLICY_VIOLATION',
            severity='MEDIUM',
        )

    try:
        await sync_to_async(_report, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "message": "Conversation reported"}


@router.post("/conversations/{conversation_id}/block/", status_code=201, summary="Block a conversation")
async def block_conversation(conversation_id: str, current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant

    updated = await sync_to_async(
        lambda: ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user
        ).update(is_active=False),
        thread_sensitive=True,
    )()
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "message": "Conversation blocked"}


@router.delete("/conversations/{conversation_id}/block/", summary="Unblock a conversation")
async def unblock_conversation(conversation_id: str, current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant

    await sync_to_async(
        lambda: ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=current_user
        ).update(is_active=True),
        thread_sensitive=True,
    )()
    return {"success": True, "message": "Conversation unblocked"}
