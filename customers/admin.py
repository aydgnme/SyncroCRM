from django.contrib import admin
from .models import Customer, SalesChannel


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'company_name', 'tax_number')
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('type', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active'),
        }),
        ('Kurumsal Bilgiler (B2B)', {
            'fields': ('company_name', 'tax_number', 'tax_office'),
            'classes': ('collapse',),
        }),
    )


@admin.register(SalesChannel)
class SalesChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('name',)
    fieldsets = (
        ('Kanal Bilgileri', {
            'fields': ('name', 'platform', 'is_active'),
        }),
        ('API Entegrasyonu', {
            'fields': ('api_key', 'shop_id'),
            'classes': ('collapse',),
        }),
    )
