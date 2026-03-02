from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)
    fields = ('product', 'warehouse', 'quantity', 'unit_price', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'sales_channel', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'sales_channel')
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name', 'customer__company_name')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Sipariş Bilgileri', {
            'fields': ('order_number', 'customer', 'sales_channel', 'status', 'note'),
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
