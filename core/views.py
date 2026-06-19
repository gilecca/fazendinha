from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json
import stripe
from .models import (User, ProducerProfile, Category, Product, Order, OrderItem,
                     Review, Message, Cart, CartItem)
from .forms import (LoginForm, RegisterForm, ProductForm, ReviewForm,
                    ProducerProfileForm, ConsumerProfileForm)
from .emails import (notify_producer_new_order, notify_consumer_payment_confirmed,
                     notify_consumer_status_change, send_email_verification)
from django.db import transaction
from django.db.models import F


def service_worker(request):
    return render(request, 'pwa/sw.js', content_type='application/javascript; charset=utf-8')


def offline_view(request):
    return render(request, 'pwa/offline.html')


def decrement_stock_for_order(order):
    """Decrementa estoque atomicamente e desativa produtos sem estoque."""
    with transaction.atomic():
        for item in order.items.select_related('product').all():
            updated = Product.objects.filter(
                pk=item.product.pk, stock__gte=item.quantity
            ).update(stock=F('stock') - item.quantity)
            if updated:
                product = Product.objects.get(pk=item.product.pk)
                if product.stock <= 0:
                    product.is_available = False
                    product.save(update_fields=['is_available'])


def home(request):
    categories = Category.objects.all()
    promotions = Product.objects.filter(is_promotion=True, is_available=True).select_related('category', 'producer')[:8]
    # Produtos em destaque aparecem primeiro; os demais completam até 16
    featured = Product.objects.filter(is_featured=True, is_available=True).select_related('category', 'producer')[:8]
    all_products = Product.objects.filter(is_available=True).select_related('category', 'producer').order_by('-created_at')[:16]
    producers = ProducerProfile.objects.filter(user__is_active=True).select_related('user').order_by('-is_premium', '-pk')[:8]
    return render(request, 'home.html', {
        'featured': featured,
        'promotions': promotions,
        'categories': categories,
        'producers': producers,
        'all_products': all_products,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            Cart.objects.get_or_create(user=user)
            return redirect(request.GET.get('next', 'home'))
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            if user.user_type == 'producer':
                farm_name = form.cleaned_data.get('farm_name') or f'Fazenda {user.get_full_name() or user.username}'
                ProducerProfile.objects.create(
                    user=user,
                    farm_name=farm_name,
                    city=user.city,
                )
            Cart.objects.create(user=user)
            login(request, user)
            if user.email:
                try:
                    send_email_verification(user, request)
                    messages.success(request, f'Bem-vindo(a), {user.get_full_name() or user.username}! Confirme seu e-mail para garantir acesso completo. 🌾')
                except Exception:
                    messages.success(request, f'Bem-vindo(a), {user.get_full_name() or user.username}! 🌾')
            else:
                messages.success(request, f'Bem-vindo(a), {user.get_full_name() or user.username}! 🌾')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def producer_profile(request, pk):
    producer = get_object_or_404(ProducerProfile, pk=pk)
    products = producer.products.filter(is_available=True).select_related('category')
    reviews = producer.reviews.all().select_related('reviewer').order_by('-created_at')
    review_form = ReviewForm()
    already_reviewed = False
    can_review = False
    if request.user.is_authenticated:
        already_reviewed = reviews.filter(reviewer=request.user).exists()
        can_review = Order.objects.filter(
            consumer=request.user, producer=producer, status='delivered'
        ).exists()
    return render(request, 'producer/profile.html', {
        'producer': producer,
        'products': products,
        'reviews': reviews,
        'review_form': review_form,
        'already_reviewed': already_reviewed,
        'can_review': can_review,
    })


@login_required
def add_review(request, producer_id):
    producer = get_object_or_404(ProducerProfile, pk=producer_id)
    if request.method == 'POST':
        has_purchase = Order.objects.filter(
            consumer=request.user, producer=producer, status='delivered'
        ).exists()
        if not has_purchase:
            messages.error(request, 'Você precisa ter recebido um pedido deste produtor para avaliar. 🛒')
            return redirect('producer_profile', pk=producer_id)
        form = ReviewForm(request.POST)
        if form.is_valid():
            if not producer.reviews.filter(reviewer=request.user).exists():
                review = form.save(commit=False)
                review.reviewer = request.user
                review.producer = producer
                review.save()
                messages.success(request, 'Avaliação enviada! Obrigado 🌟')
    return redirect('producer_profile', pk=producer_id)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(pk=pk).select_related('producer')[:4]
    return render(request, 'products/detail.html', {
        'product': product,
        'related': related,
    })


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products_qs = category.products.filter(is_available=True).select_related('producer')
    categories = Category.objects.all()

    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    in_stock = request.GET.get('in_stock', '')
    sort = request.GET.get('sort', 'newest')

    if min_price:
        try:
            products_qs = products_qs.filter(price__gte=float(min_price))
        except ValueError:
            min_price = ''
    if max_price:
        try:
            products_qs = products_qs.filter(price__lte=float(max_price))
        except ValueError:
            max_price = ''
    if in_stock:
        products_qs = products_qs.filter(stock__gt=0)

    sort_map = {'price_asc': 'price', 'price_desc': '-price'}
    products_qs = products_qs.order_by(sort_map.get(sort, '-created_at'))

    filter_params = request.GET.copy()
    filter_params.pop('page', None)
    filter_query = filter_params.urlencode()

    paginator = Paginator(products_qs, 12)
    products = paginator.get_page(request.GET.get('page'))
    return render(request, 'products/category.html', {
        'category': category,
        'products': products,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort': sort,
        'filter_query': filter_query,
    })


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)

    if product.stock <= 0:
        messages.error(request, f'"{product.name}" está sem estoque no momento. 😕')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Sem estoque'})
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity >= product.stock:
            messages.warning(request, f'Você já tem o máximo disponível de "{product.name}" no carrinho.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': 'Estoque insuficiente'})
            return redirect(request.META.get('HTTP_REFERER', 'cart'))
        item.quantity += 1
        item.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'count': cart.item_count(), 'ok': True})
    messages.success(request, f'"{product.name}" adicionado ao carrinho! 🛒')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart')


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        return redirect('cart')
    if request.method == 'POST':
        address = request.POST.get('address', '')
        notes = request.POST.get('notes', '')

        # Revalida estoque com leitura fresca do banco
        stock_errors = []
        for item in cart.items.select_related('product').all():
            fresh = Product.objects.get(pk=item.product.pk)
            if fresh.stock <= 0:
                stock_errors.append(f'"{fresh.name}" ficou sem estoque')
            elif item.quantity > fresh.stock:
                stock_errors.append(f'"{fresh.name}" — disponível: {fresh.stock}')
        if stock_errors:
            messages.error(request, 'Estoque insuficiente: ' + '; '.join(stock_errors) + '. Ajuste seu carrinho.')
            return redirect('cart')

        # Cria os pedidos agrupados por produtor com status pending_payment
        order_ids = []
        items_by_producer = {}
        for item in cart.items.select_related('product__producer').all():
            prod = item.product.producer
            items_by_producer.setdefault(prod, []).append(item)

        for producer, items in items_by_producer.items():
            order = Order.objects.create(
                consumer=request.user,
                producer=producer,
                address=address,
                notes=notes,
                status='pending_payment',
            )
            total = 0
            for item in items:
                price = item.product.current_price()
                OrderItem.objects.create(order=order, product=item.product,
                                         quantity=item.quantity, price=price)
                total += price * item.quantity
            order.total = total
            order.save()
            order_ids.append(order.pk)

        # Stripe Checkout
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if not settings.STRIPE_SECRET_KEY.startswith('sk_'):
                raise ValueError('Stripe não configurado')

            line_items = []
            for item in cart.items.select_related('product').all():
                line_items.append({
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': item.product.name,
                            **(({'images': [request.build_absolute_uri(item.product.photo.url)]}
                                if item.product.photo else {})),
                        },
                        'unit_amount': int(item.product.current_price() * 100),
                    },
                    'quantity': item.quantity,
                })

            order_ids_str = ','.join(str(i) for i in order_ids)
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                customer_email=request.user.email or None,
                success_url=(
                    request.build_absolute_uri('/pagamento/sucesso/')
                    + '?session_id={CHECKOUT_SESSION_ID}'
                ),
                cancel_url=(
                    request.build_absolute_uri('/pagamento/falhou/')
                    + f'?order_ids={order_ids_str}'
                ),
                metadata={'order_ids': order_ids_str},
            )

            Order.objects.filter(pk__in=order_ids).update(mp_preference_id=session.id)
            cart.items.all().delete()
            return redirect(session.url)

        except Exception as e:
            if not settings.STRIPE_SECRET_KEY.startswith('sk_'):
                # Modo simulado — Stripe não configurado
                cart.items.all().delete()
                orders = Order.objects.filter(pk__in=order_ids)
                orders.update(status='received', payment_status='approved')
                for order in orders:
                    decrement_stock_for_order(order)
                    notify_producer_new_order(order)
                    notify_consumer_payment_confirmed(order)
                messages.warning(request, '⚠️ Pagamento simulado — configure as chaves do Stripe no .env.')
                return redirect('orders')
            messages.error(request, f'Erro ao conectar com Stripe: {str(e)}')
            Order.objects.filter(pk__in=order_ids).delete()
            return redirect('cart')

    return render(request, 'cart/checkout.html', {'cart': cart})


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id', '')
    orders = Order.objects.none()

    if session_id:
        # Busca pedidos pelo session_id armazenado no campo mp_preference_id
        orders = Order.objects.filter(mp_preference_id=session_id, consumer=request.user)
        order_ids = list(orders.values_list('pk', flat=True))

        # Tenta verificar com a API do Stripe para obter order_ids do metadata
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            meta_ids_str = session.metadata.get('order_ids', '')
            meta_ids = [int(i) for i in meta_ids_str.split(',') if i.strip().isdigit()]
            if meta_ids:
                order_ids = meta_ids
                orders = Order.objects.filter(pk__in=order_ids, consumer=request.user)
        except Exception:
            pass

        # Atualiza pedidos pendentes para recebido (usa order_ids já conhecidos)
        if order_ids:
            updated = Order.objects.filter(
                pk__in=order_ids, consumer=request.user, payment_status='pending'
            ).update(payment_id=session_id, payment_status='approved', status='received')
            if updated:
                for order in Order.objects.filter(pk__in=order_ids):
                    try:
                        decrement_stock_for_order(order)
                        notify_producer_new_order(order)
                        notify_consumer_payment_confirmed(order)
                    except Exception:
                        pass
                messages.success(request, '🎉 Pagamento aprovado! Seu pedido foi confirmado.')
                orders = Order.objects.filter(pk__in=order_ids, consumer=request.user)

    return render(request, 'payments/success.html', {'orders': orders, 'session_id': session_id})


@login_required
def payment_failure(request):
    order_ids_str = request.GET.get('order_ids', '')
    order_ids = [int(i) for i in order_ids_str.split(',') if i.strip().isdigit()]
    orders = Order.objects.filter(pk__in=order_ids, consumer=request.user)
    orders.update(payment_status='rejected', status='cancelled')
    return render(request, 'payments/failure.html', {'orders': orders})


@login_required
def payment_pending(request):
    session_id = request.GET.get('session_id', '')
    orders = Order.objects.none()
    if session_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            order_ids_str = session.metadata.get('order_ids', '')
            order_ids = [int(i) for i in order_ids_str.split(',') if i.strip().isdigit()]
            orders = Order.objects.filter(pk__in=order_ids, consumer=request.user)
            orders.update(payment_id=session_id, payment_status='in_process')
        except Exception:
            pass
    return render(request, 'payments/pending.html', {'orders': orders})


@csrf_exempt
def payment_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        if webhook_secret and not webhook_secret.startswith('whsec_COLOQUE'):
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # Secret não configurado: processa sem validar assinatura (apenas em dev/test)
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.get('payment_status') == 'paid':
            order_ids_str = session.get('metadata', {}).get('order_ids', '')
            order_ids = [int(i) for i in order_ids_str.split(',') if i.strip().isdigit()]
            if order_ids:
                updated_count = Order.objects.filter(
                    pk__in=order_ids, payment_status='pending'
                ).update(
                    payment_id=session['id'],
                    payment_status='approved',
                    status='received',
                )
                if updated_count > 0:
                    for order in Order.objects.filter(pk__in=order_ids):
                        decrement_stock_for_order(order)
                        notify_producer_new_order(order)
                        notify_consumer_payment_confirmed(order)

    return HttpResponse(status=200)


@login_required
def orders_view(request):
    orders = Order.objects.filter(consumer=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/orders.html', {'orders': orders})


@login_required
def chat_list(request):
    sent_ids = Message.objects.filter(sender=request.user).values_list('receiver_id', flat=True).distinct()
    recv_ids = Message.objects.filter(receiver=request.user).values_list('sender_id', flat=True).distinct()
    contact_ids = set(list(sent_ids) + list(recv_ids))
    contacts = User.objects.filter(pk__in=contact_ids)
    unread_counts = {
        msg['sender_id']: msg['count']
        for msg in Message.objects.filter(receiver=request.user, is_read=False)
        .values('sender_id').annotate(count=Count('id'))
    }
    return render(request, 'chat/chat_list.html', {
        'contacts': contacts,
        'unread_counts': unread_counts,
    })


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    messages_qs = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)
        return redirect('chat_with', user_id=user_id)
    return render(request, 'chat/chat.html', {
        'other_user': other_user,
        'messages_list': messages_qs,
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'relevance')
    products_qs = Product.objects.none()
    producers = ProducerProfile.objects.none()

    if len(query) >= 2:
        products_qs = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(producer__farm_name__icontains=query) |
            Q(category__name__icontains=query),
            is_available=True,
        ).select_related('producer', 'category').distinct()

        sort_map = {'price_asc': 'price', 'price_desc': '-price'}
        if sort in sort_map:
            products_qs = products_qs.order_by(sort_map[sort])

        producers = ProducerProfile.objects.filter(
            Q(farm_name__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query)
        ).select_related('user')

    total_products = products_qs.count()
    total_producers = producers.count()
    paginator = Paginator(products_qs, 12)
    products = paginator.get_page(request.GET.get('page'))

    return render(request, 'products/search.html', {
        'query': query,
        'products': products,
        'producers': producers,
        'total': total_products + total_producers,
        'sort': sort,
    })


def map_view(request):
    producers = ProducerProfile.objects.select_related('user').all()
    return render(request, 'map/map.html', {'producers': producers})


@login_required
def producer_dashboard(request):
    if not request.user.is_producer:
        messages.warning(request, 'Apenas produtores têm acesso ao painel.')
        return redirect('home')
    profile, _ = ProducerProfile.objects.get_or_create(
        user=request.user,
        defaults={'farm_name': f'Fazenda {request.user.get_full_name() or request.user.username}',
                  'city': request.user.city}
    )
    products = profile.products.all().select_related('category')
    recent_orders = profile.orders.all().prefetch_related('items__product').order_by('-created_at')[:10]
    from django.db.models import Sum
    total_sales = profile.orders.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0
    pending = profile.orders.filter(status__in=['received', 'preparing']).count()
    unread = Message.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'producer/dashboard.html', {
        'profile': profile,
        'products': products,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'pending': pending,
        'unread': unread,
    })


@login_required
def add_product(request):
    if not request.user.is_producer:
        return redirect('home')
    profile, _ = ProducerProfile.objects.get_or_create(
        user=request.user,
        defaults={'farm_name': f'Fazenda {request.user.username}', 'city': request.user.city}
    )
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = profile
            product.save()
            messages.success(request, f'Produto "{product.name}" adicionado! 🌱')
            return redirect('producer_dashboard')
    else:
        form = ProductForm()
    return render(request, 'producer/product_form.html', {'form': form, 'action': 'Adicionar'})


@login_required
def edit_product(request, pk):
    if not request.user.is_producer:
        return redirect('home')
    product = get_object_or_404(Product, pk=pk, producer=request.user.producer_profile)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado! ✅')
            return redirect('producer_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'producer/product_form.html', {'form': form, 'action': 'Editar', 'product': product})


@login_required
def delete_product(request, pk):
    if not request.user.is_producer:
        return redirect('home')
    product = get_object_or_404(Product, pk=pk, producer=request.user.producer_profile)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" removido.')
    return redirect('producer_dashboard')


@login_required
def update_order_status(request, pk):
    if not request.user.is_producer:
        return redirect('home')
    order = get_object_or_404(Order, pk=pk, producer=request.user.producer_profile)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            notify_consumer_status_change(order)
            messages.success(request, 'Status do pedido atualizado!')
    return redirect('producer_dashboard')


@login_required
def edit_consumer_profile(request):
    if request.method == 'POST':
        form = ConsumerProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado! 🌻')
            return redirect('edit_consumer_profile')
    else:
        form = ConsumerProfileForm(instance=request.user)
    return render(request, 'auth/edit_profile.html', {'form': form})


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, consumer=request.user)
    if order.status not in ['pending_payment', 'received', 'preparing']:
        messages.error(request, 'Este pedido não pode mais ser cancelado.')
        return redirect('orders')
    if order.status in ['received', 'preparing']:
        with transaction.atomic():
            for item in order.items.select_related('product').all():
                Product.objects.filter(pk=item.product.pk).update(
                    stock=F('stock') + item.quantity,
                    is_available=True,
                )
    order.status = 'cancelled'
    order.save()
    notify_consumer_status_change(order)
    messages.success(request, f'Pedido #{order.pk} cancelado.')
    return redirect('orders')


def verify_email(request, token):
    user = get_object_or_404(User, email_token=token)
    user.email_verified = True
    user.email_token = ''
    user.save(update_fields=['email_verified', 'email_token'])
    messages.success(request, 'E-mail confirmado com sucesso! 🌾')
    return redirect('home')


@login_required
def resend_verification(request):
    if request.user.email_verified:
        return redirect('home')
    if not request.user.email:
        messages.error(request, 'Adicione um e-mail ao seu perfil primeiro.')
        return redirect('edit_consumer_profile')
    send_email_verification(request.user, request)
    messages.success(request, 'E-mail de verificação reenviado! Verifique sua caixa de entrada.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


@login_required
def edit_producer_profile(request):
    if not request.user.is_producer:
        return redirect('home')
    profile, _ = ProducerProfile.objects.get_or_create(
        user=request.user,
        defaults={'farm_name': f'Fazenda {request.user.username}', 'city': request.user.city}
    )
    if request.method == 'POST':
        form = ProducerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado! 🌻')
            return redirect('producer_dashboard')
    else:
        form = ProducerProfileForm(instance=profile)
    return render(request, 'producer/edit_profile.html', {'form': form, 'profile': profile})
