from django.contrib import admin
from django.db.models import Sum
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from .models import Category, Product, Warehouse, Stock, StockMovement


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'show_product_count', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)

    @display(description='Ürün Sayısı', ordering='products__count')
    def show_product_count(self, obj):
        return obj.products.count()


class StockInline(TabularInline):
    model = Stock
    extra = 0
    readonly_fields = ('show_available', 'show_critical', 'updated_at')
    fields = ('warehouse', 'quantity', 'reserved_quantity', 'min_level', 'show_available', 'show_critical', 'updated_at')

    @display(description='Kullanılabilir')
    def show_available(self, obj):
        return obj.available_quantity

    @display(description='Kritik?', boolean=True)
    def show_critical(self, obj):
        return obj.is_critical


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('sku', 'name', 'show_category', 'base_price', 'unit', 'show_active', 'created_at')
    list_filter = ('is_active', 'category', 'unit')
    search_fields = ('sku', 'name', 'barcode', 'category__name')
    ordering = ('sku',)
    inlines = [StockInline]
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('sku', 'name', 'description', 'category', 'is_active'),
        }),
        ('Fiyat & Birim', {
            'fields': ('base_price', 'unit'),
        }),
        ('Barkod', {
            'fields': ('barcode',),
            'classes': ('collapse',),
        }),
    )

    @display(description='Kategori', label=True, ordering='category__name')
    def show_category(self, obj):
        return obj.category.name if obj.category else '—'

    @display(description='Aktif', boolean=True)
    def show_active(self, obj):
        return obj.is_active


@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ('name', 'location', 'show_type', 'show_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'location')
    ordering = ('name',)
    fieldsets = (
        ('Depo Bilgileri', {
            'fields': ('name', 'location', 'type', 'is_active'),
        }),
    )

    @display(description='Tip', label={
        'WAREHOUSE': 'success',
        'STORE': 'info',
    })
    def show_type(self, obj):
        return obj.get_type_display()

    @display(description='Aktif', boolean=True)
    def show_active(self, obj):
        return obj.is_active


class StockMovementInline(TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('type', 'change', 'reason', 'reference', 'created_by', 'created_at')
    fields = ('type', 'change', 'reason', 'reference', 'created_by', 'created_at')
    ordering = ('-created_at',)
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = ('show_product', 'show_warehouse', 'quantity', 'reserved_quantity', 'show_available', 'min_level', 'show_critical')
    list_filter = ('warehouse',)
    search_fields = ('product__sku', 'product__name', 'warehouse__name')
    ordering = ('product__sku',)
    readonly_fields = ('show_available', 'show_critical', 'updated_at')
    inlines = [StockMovementInline]
    fieldsets = (
        ('Stok Bilgisi', {
            'fields': ('product', 'warehouse', 'quantity', 'reserved_quantity', 'min_level'),
        }),
        ('Hesaplanan', {
            'fields': ('show_available', 'show_critical', 'updated_at'),
        }),
    )

    @display(description='Ürün', ordering='product__sku')
    def show_product(self, obj):
        return f'{obj.product.sku} — {obj.product.name}'

    @display(description='Depo', ordering='warehouse__name')
    def show_warehouse(self, obj):
        return obj.warehouse.name

    @display(description='Kullanılabilir')
    def show_available(self, obj):
        return obj.available_quantity

    @display(description='Kritik', boolean=True)
    def show_critical(self, obj):
        return obj.is_critical


@admin.register(StockMovement)
class StockMovementAdmin(ModelAdmin):
    list_display = ('show_product', 'show_type', 'show_change', 'reason', 'reference', 'created_by', 'created_at')
    list_filter = ('type',)
    search_fields = ('stock__product__sku', 'reference', 'reason')
    readonly_fields = ('stock', 'change', 'type', 'reason', 'reference', 'created_by', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description='Ürün')
    def show_product(self, obj):
        return obj.stock.product.sku

    @display(description='Tip', label={
        'IN':         'success',
        'OUT':        'danger',
        'TRANSFER':   'info',
        'ADJUSTMENT': 'warning',
    })
    def show_type(self, obj):
        return obj.get_type_display()

    @display(description='Miktar')
    def show_change(self, obj):
        sign = '+' if obj.change > 0 else ''
        return f'{sign}{obj.change}'
