import json
from datetime import timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.update_last_seen(self.scope['user'])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.update_last_seen(self.scope['user'])

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']
        if not user.is_authenticated:
            return

        if data.get('type') == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'typing_notification', 'sender_id': user.id}
            )
            return

        content = data.get('content', '').strip()
        receiver_id = data.get('receiver_id')
        if not content or not receiver_id:
            return

        msg = await self.save_message(user, receiver_id, content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'content': content,
                'sender_id': user.id,
                'sender_name': user.get_full_name() or user.username,
                'timestamp': msg.created_at.strftime('%d/%m %H:%M'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({**event, 'type': 'chat_message'}))

    async def typing_notification(self, event):
        await self.send(text_data=json.dumps({**event, 'type': 'typing'}))

    @database_sync_to_async
    def save_message(self, sender, receiver_id, content):
        from .models import Message, User
        from .emails import notify_new_message

        receiver = User.objects.get(pk=receiver_id)
        msg = Message.objects.create(sender=sender, receiver=receiver, content=content)

        # Envia e-mail se o receptor estiver offline (last_seen > 2 min ou nunca conectou)
        offline = (
            receiver.last_seen is None
            or receiver.last_seen < timezone.now() - timedelta(minutes=2)
        )
        if offline and receiver.email:
            notify_new_message(sender, receiver)

        return msg

    @database_sync_to_async
    def update_last_seen(self, user):
        if user.is_authenticated:
            from .models import User
            User.objects.filter(pk=user.pk).update(last_seen=timezone.now())
