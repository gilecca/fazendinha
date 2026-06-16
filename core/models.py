from io import BytesIO

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image


def _resize_image(image_field, max_w=800, max_h=800):
    """Resize image in memory before it is saved to storage.

    Works with both local FileSystemStorage and cloud backends (e.g. Supabase).
    Called BEFORE super().save() so the resized bytes reach the storage backend.
    """
    if not image_field or getattr(image_field, '_committed', True):
        return
    try:
        img = Image.open(image_field.file)
        if img.width <= max_w and img.height <= max_h:
            return
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=85, optimize=True)
        buf.seek(0)
        image_field.file = buf
    except Exception:
        pass


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('consumer', 'Consumidor'),
        ('producer', 'Produtor'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='consumer')
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='users/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_producer(self):
        return self.user_type == 'producer'

    @property
    def is_consumer(self):
        return self.user_type == 'consumer'

    def save(self, *args, **kwargs):
        _resize_image(self.photo, 400, 400)
        super().save(*args, **kwargs)


class ProducerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='producer_profile')
    farm_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, default='MG')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    cover_photo = models.ImageField(upload_to='producers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.farm_name

    def get_average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        total = sum(r.average_score() for r in reviews)
        return round(total / len(reviews), 1)

    def get_stars(self):
        avg = self.get_average_rating()
        return int(avg)

    def save(self, *args, **kwargs):
        _resize_image(self.cover_photo, 1200, 600)
        super().save(*args, **kwargs)


CATEGORY_ICONS = {
    'queijo': '🧀',
    'cafe': '☕',
    'hortalicas': '🥦',
    'doces': '🍰',
    'leite': '🥛',
    'frutas': '🍎',
    'outros': '🌾',
}


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_icon(self):
        return CATEGORY_ICONS.get(self.slug, '🌾')


class Product(models.Model):
    producer = models.ForeignKey(ProducerProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.CharField(max_length=50, blank=True, help_text='Ex: 500g, 1kg')
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_promotion = models.BooleanField(default=False)
    promotion_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def current_price(self):
        if self.is_promotion and self.promotion_price:
            return self.promotion_price
        return self.price

    def get_icon(self):
        if self.category:
            return self.category.get_icon()
        return '🌾'

    def save(self, *args, **kwargs):
        _resize_image(self.photo, 800, 800)
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Aguardando Pagamento'),
        ('received', 'Pedido Recebido'),
        ('preparing', 'Em Preparo'),
        ('delivery', 'Saiu para Entrega'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Recusado'),
        ('in_process', 'Em Processamento'),
        ('refunded', 'Estornado'),
    ]

    consumer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    producer = models.ForeignKey(ProducerProfile, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    # Campos de pagamento
    payment_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    mp_preference_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Pedido #{self.pk} — {self.consumer}'

    def status_icon(self):
        icons = {
            'pending_payment': '💳',
            'received': '📬',
            'preparing': '👨‍🍳',
            'delivery': '🚚',
            'delivered': '✅',
            'cancelled': '❌',
        }
        return icons.get(self.status, '📦')

    def payment_icon(self):
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'in_process': '🔄',
            'refunded': '↩️',
        }
        return icons.get(self.payment_status, '💳')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity


class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    producer = models.ForeignKey(ProducerProfile, on_delete=models.CASCADE, related_name='reviews')
    quality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    service = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def average_score(self):
        return (self.quality + self.delivery + self.service) / 3

    def stars(self):
        return '⭐' * int(self.average_score())

    def __str__(self):
        return f'Avaliação de {self.reviewer} para {self.producer}'


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} → {self.receiver}: {self.content[:50]}'


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        return sum(item.subtotal() for item in self.items.select_related('product').all())

    def item_count(self):
        from django.db.models import Sum
        return self.items.aggregate(n=Sum('quantity'))['n'] or 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.current_price() * self.quantity
