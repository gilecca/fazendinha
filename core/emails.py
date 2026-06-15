import secrets
from django.core.mail import send_mail
from django.conf import settings


def _send(subject, body, to_email):
    if not to_email:
        return
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=True,
    )


def send_email_verification(user, request):
    token = secrets.token_urlsafe(32)
    user.email_token = token
    user.save(update_fields=['email_token'])
    verify_url = request.build_absolute_uri(f'/verificar-email/{token}/')
    body = f"""Olá {user.first_name or user.username},

Confirme seu e-mail clicando no link abaixo:
{verify_url}

O link não expira, mas você pode solicitar um novo a qualquer momento.
Se não foi você, ignore este e-mail.

Fazendinha 🌾
"""
    _send('[Fazendinha] Confirme seu e-mail', body, user.email)


def notify_new_message(sender, receiver):
    body = f"""Olá {receiver.first_name or receiver.username},

Você recebeu uma nova mensagem de {sender.get_full_name() or sender.username} na Fazendinha.

Acesse o chat para ver e responder.

Fazendinha 🌾
"""
    _send(
        f'💬 Nova mensagem de {sender.get_full_name() or sender.username} — Fazendinha',
        body,
        receiver.email,
    )


def notify_producer_new_order(order):
    from django.conf import settings as django_settings
    fee_pct = getattr(django_settings, 'SERVICE_FEE_PERCENT', 10)
    total = float(order.total)
    fee_value = round(total * fee_pct / 100, 2)
    net_value = round(total - fee_value, 2)

    items_text = '\n'.join(
        f'  - {item.product.name} x{item.quantity}  (R$ {item.subtotal})'
        for item in order.items.select_related('product').all()
    )
    body = f"""Olá, {order.producer.farm_name}!

Você tem um NOVO pedido confirmado na Fazendinha. 🎉

━━━━━━━━━━━━━━━━━━━━━━━━
Pedido #{order.pk}
Cliente: {order.consumer.get_full_name() or order.consumer.username}
Telefone: {order.consumer.phone or 'não informado'}
Endereço: {order.address or 'não informado'}
Observações: {order.notes or 'nenhuma'}

Itens:
{items_text}

Valor bruto:       R$ {total:.2f}
Taxa da plataforma ({fee_pct}%): - R$ {fee_value:.2f}
💰 Você recebe:    R$ {net_value:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━

Acesse seu painel para atualizar o status do pedido.

Fazendinha 🌾
"""
    _send(f'🌾 Novo pedido #{order.pk} — Fazendinha', body, order.producer.user.email)


def notify_consumer_payment_confirmed(order):
    body = f"""Olá, {order.consumer.get_full_name() or order.consumer.username}!

Seu pagamento foi confirmado. ✅ Seu pedido está ativo!

━━━━━━━━━━━━━━━━━━━━━━━━
Pedido #{order.pk}
Fazenda: {order.producer.farm_name}
Total: R$ {order.total}
━━━━━━━━━━━━━━━━━━━━━━━━

Acompanhe o status do seu pedido pelo site.

Fazendinha 🌾
"""
    _send(f'✅ Pagamento confirmado — Pedido #{order.pk}', body, order.consumer.email)


def notify_consumer_status_change(order):
    msgs = {
        'preparing': ('👨‍🍳 Pedido em preparo', 'Seu pedido está sendo preparado com muito carinho!'),
        'delivery':  ('🚚 Pedido saiu para entrega', 'Seu pedido saiu para entrega. Fique de olho!'),
        'delivered': ('✅ Pedido entregue', 'Seu pedido foi entregue. Aproveite os produtos fresquinhos!'),
        'cancelled': ('❌ Pedido cancelado', 'Infelizmente seu pedido foi cancelado. Entre em contato conosco.'),
    }
    if order.status not in msgs:
        return
    subject_suffix, line = msgs[order.status]
    body = f"""Olá, {order.consumer.get_full_name() or order.consumer.username}!

{line}

━━━━━━━━━━━━━━━━━━━━━━━━
Pedido #{order.pk} — {order.producer.farm_name}
Status: {order.get_status_display()}
Total: R$ {order.total}
━━━━━━━━━━━━━━━━━━━━━━━━

Fazendinha 🌾
"""
    _send(f'📦 Pedido #{order.pk}: {subject_suffix}', body, order.consumer.email)
