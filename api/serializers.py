from rest_framework import serializers
from inventory.models import Category, Product, Warehouse, Stock, StockMovement
from orders.models import Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'barcode', 'base_price', 'unit', 'category', 'is_active']


class StockSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    is_critical = serializers.BooleanField(read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id', 'product_sku', 'product_name', 'warehouse_name',
            'quantity', 'reserved_quantity', 'available_quantity',
            'min_level', 'is_critical', 'updated_at',
        ]
        read_only_fields = ['reserved_quantity', 'updated_at']


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_sku', 'product_name',
            'warehouse', 'warehouse_name', 'quantity', 'unit_price', 'total_price',
        ]


class OrderItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'warehouse', 'quantity', 'unit_price']

    def validate(self, data):
        try:
            stock = Stock.objects.get(product=data['product'], warehouse=data['warehouse'])
        except Stock.DoesNotExist:
            raise serializers.ValidationError(
                f"{data['product'].sku} ürünü için seçilen depoda stok kaydı bulunamadı."
            )
        if stock.available_quantity < data['quantity']:
            raise serializers.ValidationError(
                f"Yetersiz stok. Kullanılabilir: {stock.available_quantity}, İstenen: {data['quantity']}"
            )
        return data


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    sales_channel_name = serializers.CharField(source='sales_channel.name', read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name',
            'sales_channel', 'sales_channel_name', 'status',
            'total_amount', 'note', 'items', 'created_at', 'updated_at',
        ]

    def get_customer_name(self, obj):
        return str(obj.customer)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ['order_number', 'customer', 'sales_channel', 'note', 'items']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Sipariş en az bir kalem içermelidir.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order
