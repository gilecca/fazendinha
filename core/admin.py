from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProducerProfile, Category, Product, Order, OrderItem, Review, Message, Cart, CartItem


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Dados extras', {'fields': ('user_type', 'phone', 'city', 'photo')}),
    )
    list_display = ['username', 'get_full_name', 'email', 'user_type', 'city']
    list_filter = ['user_type', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']


@admin.register(ProducerProfile)
class ProducerProfileAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'user', 'city', 'state', 'is_premium']
    list_filter = ['is_premium', 'state']
    search_fields = ['farm_name', 'user__username', 'city']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'producer', 'category', 'price', 'stock', 'is_available', 'is_featured', 'is_promotion']
    list_filter = ['is_available', 'is_featured', 'is_promotion', 'category']
    list_editable = ['price', 'stock', 'is_available', 'is_featured']
    search_fields = ['name', 'producer__farm_name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'consumer', 'producer', 'status', 'payment_status', 'total', 'created_at']
    list_filter = ['status', 'payment_status']
    list_editable = ['status']
    search_fields = ['consumer__username', 'producer__farm_name', 'payment_id']
    date_hierarchy = 'created_at'
    readonly_fields = ['consumer', 'producer', 'payment_id', 'mp_preference_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'producer', 'quality', 'delivery', 'service', 'average_score', 'created_at']
    list_filter = ['quality', 'delivery', 'service']
    search_fields = ['reviewer__username', 'producer__farm_name']
    readonly_fields = ['reviewer', 'producer', 'created_at']

    def average_score(self, obj):
        return round(obj.average_score(), 1)
    average_score.short_description = 'Média'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['sender__username', 'receiver__username', 'content']

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Mensagem'


admin.site.register(Cart)
admin.site.register(CartItem)

admin.site.site_header = '🌾 Fazendinha — Admin'
admin.site.site_title = 'Fazendinha'
admin.site.index_title = 'Painel de Administração'
