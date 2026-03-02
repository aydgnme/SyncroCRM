from django.contrib import admin
from .models import Category, Product, Warehouse, Stock, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


class StockInline(admin.TabularInline):
    model = Stock
    extra = 0
    readonly_fields = ('updated_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'base_price', 'unit', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('sku', 'name', 'barcode')
    inlines = [StockInline]


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'location')


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('created_at', 'created_by')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity', 'min_level', 'is_critical', 'updated_at')
    list_filter = ('warehouse',)
    search_fields = ('product__sku', 'product__name', 'warehouse__name')
    inlines = [StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('stock', 'type', 'change', 'reason', 'reference', 'created_by', 'created_at')
    list_filter = ('type',)
    search_fields = ('stock__product__sku', 'reference', 'reason')
    readonly_fields = ('created_at',)
