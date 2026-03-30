from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('show_total',)
    fields = ('product', 'warehouse', 'quantity', 'unit_price', 'show_total')

    @display(description='Toplam')
    def show_total(self, obj):
        return f'₺{obj.total_price:,.2f}'


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_number', 'show_customer', 'show_channel', 'show_status', 'show_total', 'created_at')
    list_filter = ('status', 'sales_channel')
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name', 'customer__company_name')
    ordering = ('-created_at',)
    readonly_fields = ('show_total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Sipariş Bilgileri', {
            'fields': ('order_number', 'customer', 'sales_channel', 'status', 'note'),
        }),
        ('Özet', {
            'fields': ('show_total', 'created_at', 'updated_at'),
        }),
    )

    @display(description='Müşteri', ordering='customer__last_name')
    def show_customer(self, obj):
        return str(obj.customer)

    @display(description='Kanal', ordering='sales_channel__name')
    def show_channel(self, obj):
        return obj.sales_channel.name

    @display(description='Durum', label={
        'PENDING':   'warning',
        'CONFIRMED': 'info',
        'SHIPPED':   'primary',
        'DELIVERED': 'success',
        'CANCELLED': 'danger',
    })
    def show_status(self, obj):
        return obj.get_status_display()

    @display(description='Toplam')
    def show_total(self, obj):
        return f'₺{obj.total_amount:,.2f}'
