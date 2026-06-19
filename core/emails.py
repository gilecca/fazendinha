import logging
import secrets
import threading
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def _send(subject, text_body, to_email, html_body=None):
    if not to_email:
        return
    def _do():
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            if html_body:
                msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception as exc:
            logger.error('Falha ao enviar email para %s: %s', to_email, exc)
    threading.Thread(target=_do, daemon=False).start()


def _html(title, greeting, body_lines, cta_url=None, cta_label=None):
    cta_block = ''
    if cta_url and cta_label:
        cta_block = f'''
        <div style="text-align:center;margin:32px 0">
          <a href="{cta_url}"
             style="background:linear-gradient(135deg,#66BB6A,#43A047);color:#fff;
                    text-decoration:none;padding:14px 36px;border-radius:25px;
                    font-weight:800;font-size:1rem;display:inline-block">
            {cta_label}
          </a>
        </div>'''
    lines_html = ''.join(f'<p style="margin:8px 0;color:#5D4037">{l}</p>' for l in body_lines)
    return f'''<!DOCTYPE html>
<html lang="pt-br">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#FFF8F0;font-family:Arial,sans-serif">
  <div style="max-width:560px;margin:32px auto;background:#fff;border-radius:16px;
              border:2px solid #C8E6C9;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)">
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#81C784,#43A047);padding:28px 32px;text-align:center">
      <div style="font-size:2.5rem;margin-bottom:6px">🌾</div>
      <h1 style="margin:0;color:#fff;font-size:1.4rem;font-weight:900;letter-spacing:-0.5px">Fazendinha</h1>
      <p style="margin:4px 0 0;color:rgba(255,255,255,.85);font-size:0.85rem">Direto do campo para você</p>
    </div>
    <!-- Body -->
    <div style="padding:32px">
      <h2 style="margin:0 0 16px;color:#2E7D32;font-size:1.2rem">{title}</h2>
      <p style="margin:0 0 8px;color:#3E2723;font-weight:600">Olá, {greeting}!</p>
      {lines_html}
      {cta_block}
      <p style="margin:24px 0 0;font-size:0.82rem;color:#A1887F">
        Se não foi você quem fez essa ação, ignore este email.
      </p>
    </div>
    <!-- Footer -->
    <div style="background:#F1F8E9;padding:16px 32px;text-align:center;
                border-top:2px solid #C8E6C9">
      <p style="margin:0;font-size:0.78rem;color:#8D6E63">
        © Fazendinha · Produtos fresquinhos do campo 🌱
      </p>
    </div>
  </div>
</body>
</html>'''


def send_email_verification(user, request):
    try:
        token = secrets.token_urlsafe(32)
        user.email_token = token
        user.save(update_fields=['email_token'])
        base = settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')
        verify_url = f'{base}/verificar-email/{token}/'
        name = user.first_name or user.username

        text = (
            f'Olá {name},\n\n'
            f'Confirme seu e-mail clicando no link abaixo:\n{verify_url}\n\n'
            'O link não expira. Se não foi você, ignore este email.\n\nFazendinha 🌾'
        )
        html = _html(
            title='Confirme seu e-mail',
            greeting=name,
            body_lines=[
                'Clique no botão abaixo para confirmar seu endereço de e-mail e ativar sua conta.',
                f'<span style="font-size:0.82rem;color:#A1887F">Ou copie o link: <a href="{verify_url}" style="color:#43A047">{verify_url}</a></span>',
            ],
            cta_url=verify_url,
            cta_label='✅ Confirmar e-mail',
        )
        _send('Fazendinha: confirme seu e-mail', text, user.email, html)
    except Exception:
        pass


def notify_new_message(sender, receiver):
    name = receiver.first_name or receiver.username
    sender_name = sender.get_full_name() or sender.username
    text = (
        f'Olá {name},\n\n'
        f'Você recebeu uma nova mensagem de {sender_name} na Fazendinha.\n'
        'Acesse o chat para responder.\n\nFazendinha 🌾'
    )
    html = _html(
        title='Nova mensagem recebida',
        greeting=name,
        body_lines=[f'Você recebeu uma mensagem de <strong>{sender_name}</strong>.',
                    'Acesse o chat para ver e responder.'],
        cta_url=f'{settings.SITE_URL}/chat/',
        cta_label='💬 Ver mensagem',
    )
    _send(
        f'Fazendinha: nova mensagem de {sender_name}',
        text,
        receiver.email,
        html,
    )


def notify_producer_new_order(order):
    fee_pct = getattr(settings, 'SERVICE_FEE_PERCENT', 10)
    total = float(order.total)
    fee_value = round(total * fee_pct / 100, 2)
    net_value = round(total - fee_value, 2)

    items_text = '\n'.join(
        f'  - {item.product.name} x{item.quantity}  (R$ {item.subtotal})'
        for item in order.items.select_related('product').all()
    )
    items_html = ''.join(
        f'<div style="padding:6px 0;border-bottom:1px solid #E8F5E9">'
        f'<span style="font-weight:700">{item.product.name}</span> '
        f'× {item.quantity} &nbsp;·&nbsp; R$ {item.subtotal}</div>'
        for item in order.items.select_related('product').all()
    )

    text = (
        f'Olá, {order.producer.farm_name}!\n\nNovo pedido #{order.pk} confirmado.\n\n'
        f'Cliente: {order.consumer.get_full_name() or order.consumer.username}\n'
        f'Endereço: {order.address or "não informado"}\n\nItens:\n{items_text}\n\n'
        f'Total bruto: R$ {total:.2f}\nTaxa ({fee_pct}%): -R$ {fee_value:.2f}\n'
        f'Você recebe: R$ {net_value:.2f}\n\nFazendinha 🌾'
    )
    html = _html(
        title=f'Novo pedido #{order.pk}!',
        greeting=order.producer.farm_name,
        body_lines=[
            f'<strong>Cliente:</strong> {order.consumer.get_full_name() or order.consumer.username}',
            f'<strong>Telefone:</strong> {order.consumer.phone or "não informado"}',
            f'<strong>Endereço:</strong> {order.address or "não informado"}',
            f'<div style="margin:12px 0;background:#F1F8E9;border-radius:10px;padding:12px">{items_html}'
            f'<div style="margin-top:10px;font-weight:900;color:#2E7D32;font-size:1.05rem">'
            f'Você recebe: R$ {net_value:.2f}</div></div>',
        ],
        cta_url=f'{settings.SITE_URL}/painel/',
        cta_label='📦 Ver no painel',
    )
    _send(f'Fazendinha: novo pedido #{order.pk}', text, order.producer.user.email, html)


def notify_consumer_payment_confirmed(order):
    name = order.consumer.get_full_name() or order.consumer.username
    text = (
        f'Olá, {name}!\n\nSeu pagamento foi confirmado. Pedido #{order.pk} ativo!\n'
        f'Fazenda: {order.producer.farm_name}\nTotal: R$ {order.total}\n\nFazendinha 🌾'
    )
    html = _html(
        title='Pagamento confirmado!',
        greeting=name,
        body_lines=[
            f'Seu pedido <strong>#{order.pk}</strong> foi confirmado.',
            f'<strong>Fazenda:</strong> {order.producer.farm_name}',
            f'<strong>Total:</strong> R$ {order.total}',
        ],
        cta_url=f'{settings.SITE_URL}/pedidos/',
        cta_label='📦 Acompanhar pedido',
    )
    _send(f'Fazendinha: pagamento confirmado - pedido #{order.pk}', text, order.consumer.email, html)


def notify_consumer_status_change(order):
    msgs = {
        'preparing': ('Pedido em preparo',    'Seu pedido está sendo preparado com carinho!'),
        'delivery':  ('Pedido saiu para entrega', 'Seu pedido saiu para entrega. Fique de olho!'),
        'delivered': ('Pedido entregue',       'Aproveite os produtos fresquinhos!'),
        'cancelled': ('Pedido cancelado',      'Infelizmente seu pedido foi cancelado.'),
    }
    if order.status not in msgs:
        return
    title, line = msgs[order.status]
    name = order.consumer.get_full_name() or order.consumer.username
    text = (
        f'Olá, {name}!\n\n{line}\n\n'
        f'Pedido #{order.pk} — {order.producer.farm_name}\n'
        f'Status: {order.get_status_display()}\nTotal: R$ {order.total}\n\nFazendinha 🌾'
    )
    html = _html(
        title=title,
        greeting=name,
        body_lines=[
            line,
            f'<strong>Pedido:</strong> #{order.pk} — {order.producer.farm_name}',
            f'<strong>Status:</strong> {order.get_status_display()}',
            f'<strong>Total:</strong> R$ {order.total}',
        ],
        cta_url=f'{settings.SITE_URL}/pedidos/',
        cta_label='Ver meus pedidos',
    )
    _send(f'Fazendinha: pedido #{order.pk} atualizado', text, order.consumer.email, html)
