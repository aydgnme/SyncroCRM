from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from customers.models import Customer
from inventory.models import Product, Stock
from orders.models import Order

from .serializers import (
    CustomerSerializer,
    ProductListSerializer,
    StockSerializer,
    OrderReadSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
)


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for active customers."""
    queryset = Customer.objects.filter(is_active=True)
    serializer_class = CustomerSerializer
    filterset_fields = ['type']
    search_fields = ['first_name', 'last_name', 'email', 'company_name']


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductListSerializer
    filterset_fields = ['category']
    search_fields = ['name', 'sku', 'barcode']

    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Return stock levels for a product across all warehouses."""
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
        """Return all stock records below the minimum threshold."""
        from django.db.models import F
        critical_qs = self.get_queryset().filter(
            quantity__lte=F('min_level') + F('reserved_quantity')
        )
        serializer = self.get_serializer(critical_qs, many=True)
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
        if self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
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
        """Transition order from PENDING to CONFIRMED. Triggers real stock deduction."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.PENDING],
            next_status=Order.Status.CONFIRMED,
            error_msg='Only PENDING orders can be confirmed.',
        )

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Transition order from CONFIRMED to SHIPPED."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.CONFIRMED],
            next_status=Order.Status.SHIPPED,
            error_msg='Only CONFIRMED orders can be shipped.',
        )

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Transition order from SHIPPED to DELIVERED."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.SHIPPED],
            next_status=Order.Status.DELIVERED,
            error_msg='Only SHIPPED orders can be marked as delivered.',
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order. DELIVERED orders cannot be cancelled."""
        return self._transition(
            pk,
            allowed_from=[Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.SHIPPED],
            next_status=Order.Status.CANCELLED,
            error_msg='Delivered orders cannot be cancelled.',
        )
