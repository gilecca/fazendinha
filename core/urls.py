from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import FarmSetPasswordForm

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.register_view, name='register'),

    path('produtor/<int:pk>/', views.producer_profile, name='producer_profile'),
    path('produtor/<int:producer_id>/avaliar/', views.add_review, name='add_review'),

    path('produto/<int:pk>/', views.product_detail, name='product_detail'),
    path('categoria/<slug:slug>/', views.category_view, name='category'),

    path('carrinho/', views.cart_view, name='cart'),
    path('carrinho/adicionar/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('carrinho/remover/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrinho/atualizar/<int:item_id>/', views.update_cart, name='update_cart'),
    path('finalizar/', views.checkout, name='checkout'),
    path('pagamento/sucesso/', views.payment_success, name='payment_success'),
    path('pagamento/falhou/', views.payment_failure, name='payment_failure'),
    path('pagamento/pendente/', views.payment_pending, name='payment_pending'),
    path('pagamento/webhook/', views.payment_webhook, name='payment_webhook'),

    path('pedidos/', views.orders_view, name='orders'),

    path('chat/', views.chat_list, name='chat'),
    path('chat/<int:user_id>/', views.chat_view, name='chat_with'),

    path('busca/', views.search_view, name='search'),
    path('mapa/', views.map_view, name='map'),

    path('painel/', views.producer_dashboard, name='producer_dashboard'),
    path('painel/produto/novo/', views.add_product, name='add_product'),
    path('painel/produto/<int:pk>/editar/', views.edit_product, name='edit_product'),
    path('painel/produto/<int:pk>/deletar/', views.delete_product, name='delete_product'),
    path('painel/pedido/<int:pk>/status/', views.update_order_status, name='update_order_status'),
    path('painel/perfil/', views.edit_producer_profile, name='edit_producer_profile'),

    path('perfil/', views.edit_consumer_profile, name='edit_consumer_profile'),
    path('pedido/<int:pk>/cancelar/', views.cancel_order, name='cancel_order'),

    path('verificar-email/reenviar/', views.resend_verification, name='resend_verification'),
    path('verificar-email/<str:token>/', views.verify_email, name='verify_email'),

    # Redefinição de senha
    path('senha/resetar/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt',
        success_url='/senha/resetar/enviado/',
    ), name='password_reset'),
    path('senha/resetar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html',
    ), name='password_reset_done'),
    path('senha/resetar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        form_class=FarmSetPasswordForm,
        success_url='/senha/resetar/concluido/',
    ), name='password_reset_confirm'),
    path('senha/resetar/concluido/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html',
    ), name='password_reset_complete'),
]
