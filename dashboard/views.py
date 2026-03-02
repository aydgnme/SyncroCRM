import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from customers.models import SalesChannel
from inventory.models import Stock, StockMovement
from orders.models import Order


@login_required
def index(request):
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=6)

    # --- KPI Kartları ---
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()

    revenue = Order.objects.filter(
        status=Order.Status.DELIVERED
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('items__unit_price') * F('items__quantity'),
                output_field=DecimalField(),
            ),
            default=0,
        )
    )['total'] or 0

    all_stocks = list(Stock.objects.select_related('product', 'warehouse').all())
    critical_stocks = [s for s in all_stocks if s.is_critical]

    # --- Grafik 1: Satış Kanalı Bazlı Sipariş Dağılımı (Pie) ---
    channel_data = (
        Order.objects
        .values('sales_channel__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    channel_labels = [d['sales_channel__name'] for d in channel_data]
    channel_counts = [d['count'] for d in channel_data]

    # --- Grafik 2: Son 7 Günlük Sipariş Trendi (Bar) ---
    daily_orders = (
        Order.objects
        .filter(created_at__gte=week_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    day_map = {entry['day']: entry['count'] for entry in daily_orders}
    trend_labels = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
    trend_counts = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    trend_counts = [day_map.get(today - timedelta(days=i), 0) for i in range(6, -1, -1)]

    # --- Grafik 3: Sipariş Durumu Dağılımı (Doughnut) ---
    status_data = Order.objects.values('status').annotate(count=Count('id'))
    status_labels_map = dict(Order.Status.choices)
    status_labels = [status_labels_map.get(d['status'], d['status']) for d in status_data]
    status_counts = [d['count'] for d in status_data]

    # --- Son Stok Hareketleri ---
    recent_movements = (
        StockMovement.objects
        .select_related('stock__product', 'stock__warehouse', 'created_by')
        .order_by('-created_at')[:12]
    )

    # --- Son Siparişler ---
    recent_orders = (
        Order.objects
        .select_related('customer', 'sales_channel')
        .prefetch_related('items')
        .order_by('-created_at')[:8]
    )

    context = {
        # KPI
        'total_orders': total_orders,
        'today_orders': today_orders,
        'revenue': revenue,
        'critical_count': len(critical_stocks),
        'critical_stocks': critical_stocks[:5],
        # Grafikler — JSON
        'channel_labels': json.dumps(channel_labels),
        'channel_counts': json.dumps(channel_counts),
        'trend_labels': json.dumps(trend_labels),
        'trend_counts': json.dumps(trend_counts),
        'status_labels': json.dumps(status_labels),
        'status_counts': json.dumps(status_counts),
        # Tablolar
        'recent_movements': recent_movements,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/index.html', context)
