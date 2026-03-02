from django.db import models
from customers.models import Customer, SalesChannel
from inventory.models import Product, Warehouse


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Beklemede'
        CONFIRMED = 'CONFIRMED', 'Onaylandı'
        SHIPPED = 'SHIPPED', 'Kargoda'
        DELIVERED = 'DELIVERED', 'Teslim Edildi'
        CANCELLED = 'CANCELLED', 'İptal Edildi'

    order_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.order_number} — {self.customer}"

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # sipariş anındaki fiyat

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.product.sku} x{self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.unit_price
