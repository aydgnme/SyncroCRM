from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Customer, SalesChannel


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ('show_name', 'show_type', 'email', 'phone', 'show_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'company_name', 'tax_number')
    ordering = ('-created_at',)
    fieldsets = (
        ('Kişisel Bilgiler', {
            'fields': ('type', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active'),
        }),
        ('Kurumsal Bilgiler (B2B)', {
            'fields': ('company_name', 'tax_number', 'tax_office'),
            'classes': ('collapse',),
            'description': 'Sadece kurumsal müşteriler için doldurunuz.',
        }),
    )

    @display(description='Ad Soyad / Şirket', ordering='last_name')
    def show_name(self, obj):
        return str(obj)

    @display(description='Tip', label={
        'B2C': 'info',
        'B2B': 'warning',
    })
    def show_type(self, obj):
        return obj.get_type_display()

    @display(description='Aktif', boolean=True)
    def show_active(self, obj):
        return obj.is_active


@admin.register(SalesChannel)
class SalesChannelAdmin(ModelAdmin):
    list_display = ('name', 'show_platform', 'show_order_count', 'show_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('name',)
    ordering = ('name',)
    fieldsets = (
        ('Kanal Bilgileri', {
            'fields': ('name', 'platform', 'is_active'),
        }),
        ('API Entegrasyonu', {
            'fields': ('api_key', 'shop_id'),
            'classes': ('collapse',),
            'description': 'Pazaryeri entegrasyon bilgileri. Boş bırakılabilir.',
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(order_count=Count('orders'))

    @display(description='Platform', label={
        'TRENDYOL':   'success',
        'AMAZON':     'warning',
        'HEPSIBURADA':'info',
        'N11':        'info',
        'WEBSITE':    'primary',
        'STORE':      'success',
        'OTHER':      'default',
    })
    def show_platform(self, obj):
        return obj.get_platform_display()

    @display(description='Sipariş', ordering='order_count')
    def show_order_count(self, obj):
        return obj.order_count

    @display(description='Aktif', boolean=True)
    def show_active(self, obj):
        return obj.is_active
