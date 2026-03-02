from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='adet')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Warehouse(models.Model):
    class WarehouseType(models.TextChoices):
        WAREHOUSE = 'WAREHOUSE', 'Depo'
        STORE = 'STORE', 'Mağaza'

    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=WarehouseType.choices,
        default=WarehouseType.WAREHOUSE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    min_level = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'
        unique_together = ('product', 'warehouse')

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.name}: {self.quantity}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    @property
    def is_critical(self):
        return self.available_quantity <= self.min_level


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = 'IN', 'Giriş'
        OUT = 'OUT', 'Çıkış'
        TRANSFER = 'TRANSFER', 'Transfer'
        ADJUSTMENT = 'ADJUSTMENT', 'Düzeltme'

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    change = models.IntegerField()
    type = models.CharField(max_length=20, choices=MovementType.choices)
    reason = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
    )

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} | {self.stock.product.sku} | {self.change}"
