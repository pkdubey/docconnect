"""
WebSocket consumer for real-time messaging.

Connect: ws://host/ws/conversations/<conversation_id>/
Auth:    ?token=<access_token>  (query param)

Events sent to client:
  {"type": "message", "id": "...", "sender_id": "...", "content": "...",
   "message_type": "TEXT", "created_at": "..."}

Events received from client:
  {"content": "...", "message_type": "TEXT"}
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ConversationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = f"conversation_{self.conversation_id}"

        user = await self._authenticate()
        if user is None:
            await self.close(code=4001)
            return

        if not await self._is_participant(user):
            await self.close(code=4003)
            return

        self.user = user
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        content = (data.get('content') or '').strip()
        message_type = data.get('message_type', 'TEXT')
        if not content:
            return

        msg = await self._save_message(content, message_type)
        if msg is None:
            return

        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat_message',
            'id': str(msg['id']),
            'sender_id': str(self.user.id),
            'content': msg['content'],
            'message_type': msg['message_type'],
            'created_at': msg['created_at'],
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['id'],
            'sender_id': event['sender_id'],
            'content': event['content'],
            'message_type': event['message_type'],
            'created_at': event['created_at'],
        }))

    # ── Helpers ──────────────────────────────────────────────

    async def _authenticate(self):
        qs = self.scope.get('query_string', b'').decode()
        token_str = None
        for part in qs.split('&'):
            if part.startswith('token='):
                token_str = part[6:]
                break
        if not token_str:
            return None
        return await self._get_user_from_token(token_str)

    @database_sync_to_async
    def _get_user_from_token(self, token_str):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            token = AccessToken(token_str)
            User = get_user_model()
            user = User.objects.get(id=token['user_id'])
            return user if user.status == 'ACTIVE' else None
        except Exception:
            return None

    @database_sync_to_async
    def _is_participant(self, user):
        from apps.messaging.models import ConversationParticipant
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=user,
            is_active=True,
        ).exists()

    @database_sync_to_async
    def _save_message(self, content, message_type):
        from apps.messaging.models import Conversation, Message
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            msg = Message.objects.create(
                conversation=conv,
                sender=self.user,
                content=content,
                message_type=message_type if message_type in (
                    'TEXT', 'IMAGE', 'DOCUMENT', 'SHIFT_REQUEST', 'JOB_REFERRAL'
                ) else 'TEXT',
            )
            Conversation.objects.filter(id=self.conversation_id).update(updated_at=msg.created_at)
            return {
                'id': str(msg.id),
                'content': msg.content,
                'message_type': msg.message_type,
                'created_at': msg.created_at.isoformat(),
            }
        except Exception:
            return None
