from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from inventory.models import Product, Stock
from orders.models import Order

from .serializers import (
    ProductListSerializer,
    StockSerializer,
    OrderReadSerializer,
    OrderCreateSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductListSerializer
    filterset_fields = ['category']
    search_fields = ['name', 'sku', 'barcode']

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Ürünün tüm depolardaki stok durumu."""
        product = self.get_object()
        stocks = Stock.objects.filter(product=product).select_related('warehouse')
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related('product', 'warehouse')
    serializer_class = StockSerializer
    filterset_fields = ['warehouse', 'product']
    search_fields = ['product__sku', 'product__name']

    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Kritik stok eşiğinin altındaki tüm kayıtlar."""
        critical = [s for s in self.get_queryset() if s.is_critical]
        serializer = self.get_serializer(critical, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related(
        'customer', 'sales_channel'
    ).prefetch_related('items__product', 'items__warehouse')
    filterset_fields = ['status', 'sales_channel']
    search_fields = ['order_number', 'customer__first_name', 'customer__last_name', 'customer__company_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderReadSerializer

    def _transition(self, pk, allowed_from, next_status, error_msg):
        order = self.get_object()
        if order.status not in allowed_from:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        order.status = next_status
        order.save()
        return Response(OrderReadSerializer(order).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """PENDING → CONFIRMED: Stoktan gerçek düşüş başlar."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.PENDING],
            next_status=Order.Status.CONFIRMED,
            error_msg='Sadece PENDING siparişler onaylanabilir.',
        )

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """CONFIRMED → SHIPPED."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.CONFIRMED],
            next_status=Order.Status.SHIPPED,
            error_msg='Sadece CONFIRMED siparişler kargoya verilebilir.',
        )

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """SHIPPED → DELIVERED."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.SHIPPED],
            next_status=Order.Status.DELIVERED,
            error_msg='Sadece SHIPPED siparişler teslim edilebilir.',
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """* → CANCELLED: DELIVERED siparişler iptal edilemez."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.SHIPPED],
            next_status=Order.Status.CANCELLED,
            error_msg='Teslim edilmiş sipariş iptal edilemez.',
        )
