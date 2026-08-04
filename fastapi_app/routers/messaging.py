from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/messages", tags=["Messaging"])


# ── Schemas ───────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    participant_user_id: str  # for DIRECT conversations


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = Field("TEXT", pattern=r'^(TEXT|IMAGE|DOCUMENT|SHIFT_REQUEST|JOB_REFERRAL)$')


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/conversations/", status_code=201)
async def start_conversation(data: ConversationCreate, current_user=Depends(get_current_user)):
    from django.contrib.auth import get_user_model
    from apps.messaging.models import Conversation, ConversationParticipant
    User = get_user_model()
    try:
        other_user = User.objects.get(id=data.participant_user_id)
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if direct conversation already exists between these two users
    existing = (
        ConversationParticipant.objects.filter(user=current_user, conversation__type='DIRECT')
        .values_list('conversation_id', flat=True)
    )
    shared = ConversationParticipant.objects.filter(
        user=other_user, conversation_id__in=existing
    ).first()
    if shared:
        return {"conversation_id": str(shared.conversation_id), "existing": True}

    conv = Conversation.objects.create(type='DIRECT')
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conv, user=current_user),
        ConversationParticipant(conversation=conv, user=other_user),
    ])
    return {"conversation_id": str(conv.id), "existing": False}


@router.get("/conversations/")
async def list_conversations(current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant, Message
    participants = (
        ConversationParticipant.objects
        .filter(user=current_user, is_active=True)
        .select_related('conversation')
        .order_by('-conversation__updated_at')
    )
    result = []
    for p in participants:
        last_msg = Message.objects.filter(conversation=p.conversation).order_by('-created_at').first()
        result.append({
            "conversation_id": str(p.conversation_id),
            "type": p.conversation.type,
            "last_message": last_msg.content if last_msg else None,
            "last_message_at": last_msg.created_at.isoformat() if last_msg else None,
            "last_read_at": p.last_read_at.isoformat() if p.last_read_at else None,
        })
    return result


@router.get("/conversations/{conversation_id}/messages/")
async def get_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.messaging.models import Conversation, ConversationParticipant, Message
    from django.utils import timezone
    if not ConversationParticipant.objects.filter(conversation_id=conversation_id, user=current_user, is_active=True).exists():
        raise HTTPException(status_code=403, detail="Not a participant")

    # Mark as read
    ConversationParticipant.objects.filter(conversation_id=conversation_id, user=current_user).update(
        last_read_at=timezone.now()
    )

    qs = Message.objects.filter(conversation_id=conversation_id).order_by('-created_at')
    total = qs.count()
    messages = qs[(page - 1) * page_size: page * page_size]
    return {
        "total": total, "page": page,
        "messages": [{
            "id": str(m.id),
            "sender_id": str(m.sender_id),
            "content": m.content,
            "message_type": m.message_type,
            "file_id": str(m.file_id) if m.file_id else None,
            "created_at": m.created_at.isoformat(),
        } for m in messages],
    }


@router.post("/conversations/{conversation_id}/messages/", status_code=201)
async def send_message(conversation_id: str, data: MessageCreate, current_user=Depends(get_current_user)):
    from apps.messaging.models import Conversation, ConversationParticipant, Message
    if not ConversationParticipant.objects.filter(conversation_id=conversation_id, user=current_user, is_active=True).exists():
        raise HTTPException(status_code=403, detail="Not a participant")
    msg = Message.objects.create(
        conversation_id=conversation_id,
        sender=current_user,
        content=data.content,
        message_type=data.message_type,
    )
    # bump conversation updated_at
    Conversation.objects.filter(id=conversation_id).update(updated_at=msg.created_at)
    return {"id": str(msg.id), "created_at": msg.created_at.isoformat()}
