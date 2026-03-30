import json
import uuid

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST

from customers.models import Customer, SalesChannel
from inventory.models import Stock, StockMovement, Warehouse, Product
from orders.models import Order, OrderItem

PAGE_SIZE = 25


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _render_dashboard(request, template_name, context=None):
    merged_context = {**admin.site.each_context(request), **(context or {})}
    return render(request, template_name, merged_context)


def _kpi_context():
    today = timezone.now().date()

    # Use DB-level filter instead of loading all stocks into memory
    critical_qs = Stock.objects.filter(
        quantity__lte=F('min_level') + F('reserved_quantity')
    ).select_related('product', 'warehouse')
    critical = list(critical_qs)

    revenue = Order.objects.filter(
        status=Order.Status.DELIVERED
    ).aggregate(
        total=Sum(
            ExpressionWrapper(F('items__unit_price') * F('items__quantity'), output_field=DecimalField()),
            default=0,
        )
    )['total'] or 0

    return {
        'total_orders': Order.objects.count(),
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'revenue': revenue,
        'critical_count': len(critical),
        'critical_stocks': critical[:5],
    }


# ─── Dashboard home ───────────────────────────────────────────────────────────

@login_required
def index(request):
    week_ago = timezone.now() - timedelta(days=6)
    today = timezone.now().date()

    channel_data = Order.objects.values('sales_channel__name').annotate(count=Count('id')).order_by('-count')
    status_data = Order.objects.values('status').annotate(count=Count('id'))
    status_labels_map = dict(Order.Status.choices)

    day_map = {
        e['day']: e['count']
        for e in Order.objects.filter(created_at__gte=week_ago)
        .annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('id'))
    }

    context = {
        **_kpi_context(),
        'channel_labels': json.dumps([d['sales_channel__name'] for d in channel_data]),
        'channel_counts': json.dumps([d['count'] for d in channel_data]),
        'status_labels': json.dumps([status_labels_map.get(d['status'], d['status']) for d in status_data]),
        'status_counts': json.dumps([d['count'] for d in status_data]),
        'trend_labels': json.dumps([(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]),
        'trend_counts': json.dumps([day_map.get(today - timedelta(days=i), 0) for i in range(6, -1, -1)]),
        'recent_movements': StockMovement.objects.select_related('stock__product', 'stock__warehouse').order_by('-created_at')[:10],
        'recent_orders': Order.objects.select_related('customer', 'sales_channel').prefetch_related('items').order_by('-created_at')[:8],
    }
    return _render_dashboard(request, 'dashboard/index.html', context)


@login_required
def kpi_partial(request):
    return render(request, 'dashboard/partials/kpi.html', _kpi_context())


# ─── Orders ───────────────────────────────────────────────────────────────────

@login_required
def orders(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    all_orders = Order.objects.all()

    qs = (
        Order.objects
        .select_related('customer', 'sales_channel')
        .prefetch_related('items')
        .order_by('-created_at')
    )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(
            Q(order_number__icontains=q) |
            Q(customer__first_name__icontains=q) |
            Q(customer__last_name__icontains=q) |
            Q(customer__company_name__icontains=q)
        )

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    page_range = list(paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1))
    status_summary = {
        row['status']: row['count']
        for row in all_orders.values('status').annotate(count=Count('id'))
    }

    ctx = {
        'page_obj': page_obj,
        'page_range': page_range,
        'status_choices': Order.Status.choices,
        'current_status': status_filter,
        'search': q,
        'status_summary': status_summary,
        'today_orders_total': all_orders.filter(created_at__date=timezone.localdate()).count(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/partials/orders_content.html', ctx)
    return _render_dashboard(request, 'dashboard/orders.html', ctx)


@login_required
@require_POST
def order_action(request, pk, action):
    order = get_object_or_404(
        Order.objects.select_related('customer', 'sales_channel').prefetch_related('items'),
        pk=pk,
    )

    transitions = {
        'confirm': ([Order.Status.PENDING], Order.Status.CONFIRMED),
        'ship':    ([Order.Status.CONFIRMED], Order.Status.SHIPPED),
        'deliver': ([Order.Status.SHIPPED], Order.Status.DELIVERED),
        'cancel':  ([Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.SHIPPED], Order.Status.CANCELLED),
    }
    labels = {
        'confirm': 'onaylandı',
        'ship': 'kargoya verildi',
        'deliver': 'teslim edildi',
        'cancel': 'iptal edildi',
    }

    if action not in transitions:
        return HttpResponse(status=400)

    allowed, next_status = transitions[action]
    if order.status not in allowed:
        return HttpResponse(status=400)

    order.status = next_status
    order.save()

    response = render(request, 'dashboard/partials/order_row.html', {'order': order})
    response['HX-Trigger'] = json.dumps({
        'showToast': {'msg': f'#{order.order_number} siparişi {labels[action]}.', 'type': 'success'}
    })
    return response


@login_required
def order_create(request):
    """Render and process the new order form."""
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        channel_id = request.POST.get('sales_channel')
        order_number = request.POST.get('order_number', '').strip()
        note = request.POST.get('note', '').strip()
        items_raw = request.POST.get('items_json', '[]')
        initial_items = items_raw

        errors = []
        items = []
        try:
            items = json.loads(items_raw)
            initial_items = json.dumps(items)
        except (json.JSONDecodeError, ValueError):
            errors.append('Sipariş satırları okunamadı.')
            initial_items = '[]'

        if not customer_id:
            errors.append('Müşteri seçilmelidir.')
        if not channel_id:
            errors.append('Satış kanalı seçilmelidir.')
        if not items:
            errors.append('En az bir ürün eklenmelidir.')
        if not order_number:
            order_number = 'ORD-' + str(uuid.uuid4())[:8].upper()

        if not errors:
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        order_number=order_number,
                        customer_id=customer_id,
                        sales_channel_id=channel_id,
                        note=note,
                    )
                    for item_data in items:
                        product_id = item_data.get('product')
                        warehouse_id = item_data.get('warehouse')
                        qty = int(item_data.get('quantity', 0))
                        price = item_data.get('unit_price')

                        if not product_id or not warehouse_id or qty <= 0:
                            raise ValueError('Her satır için ürün, depo ve pozitif miktar girilmelidir.')

                        stock = Stock.objects.select_for_update().get(
                            product_id=product_id, warehouse_id=warehouse_id
                        )
                        if stock.available_quantity < qty:
                            product = Product.objects.get(pk=product_id)
                            raise ValueError(
                                f"{product.sku} için stok yetersiz: "
                                f"mevcut {stock.available_quantity}, istenen {qty}."
                            )
                        OrderItem.objects.create(
                            order=order,
                            product_id=product_id,
                            warehouse_id=warehouse_id,
                            quantity=qty,
                            unit_price=price,
                        )
                return redirect('dashboard:orders')
            except Exception as e:
                errors.append(str(e))

        ctx = _order_create_context(initial_items)
        ctx['errors'] = errors
        ctx['prev'] = request.POST
        return _render_dashboard(request, 'dashboard/order_create.html', ctx)

    return _render_dashboard(request, 'dashboard/order_create.html', _order_create_context())


def _order_create_context(initial_items='[]'):
    customers = list(Customer.objects.filter(is_active=True).order_by('first_name', 'last_name'))
    channels = list(SalesChannel.objects.filter(is_active=True).order_by('name'))
    product_rows = list(Product.objects.filter(is_active=True).order_by('sku').values('id', 'sku', 'name', 'base_price'))
    warehouse_rows = list(Warehouse.objects.filter(is_active=True).order_by('name').values('id', 'name'))
    stocks_qs = list(Stock.objects.values('product_id', 'warehouse_id', 'quantity', 'reserved_quantity'))
    return {
        'customers': customers,
        'channels': channels,
        'products_json': json.dumps(product_rows),
        'warehouses_json': json.dumps(warehouse_rows),
        'stocks_json': json.dumps(stocks_qs),
        'items_json_initial': initial_items,
        'prev': {},
        'customer_count': len(customers),
        'channel_count': len(channels),
        'product_count': len(product_rows),
        'warehouse_count': len(warehouse_rows),
    }


# ─── Stock ────────────────────────────────────────────────────────────────────

@login_required
def stock(request):
    q = request.GET.get('q', '').strip()
    warehouse_filter = request.GET.get('warehouse', '')
    warehouses = Warehouse.objects.filter(is_active=True).order_by('name')

    qs = Stock.objects.select_related('product__category', 'warehouse').order_by('product__sku')
    if q:
        qs = qs.filter(Q(product__sku__icontains=q) | Q(product__name__icontains=q))
    if warehouse_filter:
        qs = qs.filter(warehouse_id=warehouse_filter)

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    page_range = list(paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1))
    critical_count = qs.filter(quantity__lte=F('min_level') + F('reserved_quantity')).count()
    available_total = qs.aggregate(total=Sum(F('quantity') - F('reserved_quantity')))['total'] or 0

    ctx = {
        'page_obj': page_obj,
        'stocks': page_obj,
        'page_range': page_range,
        'warehouses': warehouses,
        'current_warehouse': warehouse_filter,
        'search': q,
        'critical_count': critical_count,
        'available_total': available_total,
        'warehouse_count': warehouses.count(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/partials/stock_content.html', ctx)
    return _render_dashboard(request, 'dashboard/stock.html', ctx)


@login_required
def stock_adjust(request, pk):
    """GET: load adjustment modal. POST: apply adjustment and return updated row."""
    stock_obj = get_object_or_404(Stock.objects.select_related('product', 'warehouse'), pk=pk)

    if request.method == 'POST':
        try:
            movement_type = request.POST.get('type', '').strip()
            change = int(request.POST.get('change', 0))
            new_min_raw = request.POST.get('min_level', '').strip()
            reason = request.POST.get('reason', '').strip()

            allowed_types = [StockMovement.MovementType.IN, StockMovement.MovementType.ADJUSTMENT]

            with transaction.atomic():
                s = Stock.objects.select_for_update().get(pk=pk)

                update_fields = ['updated_at']

                if new_min_raw != '':
                    s.min_level = int(new_min_raw)
                    update_fields.append('min_level')

                if change != 0 and movement_type in allowed_types:
                    s.quantity += change
                    update_fields.append('quantity')
                    StockMovement.objects.create(
                        stock=s,
                        change=change,
                        type=movement_type,
                        reason=reason or (
                            'Stok girişi' if movement_type == StockMovement.MovementType.IN
                            else 'Manuel düzeltme'
                        ),
                        created_by=request.user,
                    )

                s.save(update_fields=update_fields)

            stock_obj.refresh_from_db()
            response = render(request, 'dashboard/partials/stock_row.html', {'s': stock_obj})
            response['HX-Trigger'] = json.dumps({
                'showToast': {'msg': f'{stock_obj.product.sku} stoğu güncellendi.', 'type': 'success'},
                'closeModal': True,
            })
            return response

        except (ValueError, TypeError, Stock.DoesNotExist) as e:
            return HttpResponse(str(e), status=400)

    # GET — return modal form HTML
    return render(request, 'dashboard/partials/stock_adjust_modal.html', {
        's': stock_obj,
        'movement_types': [
            (StockMovement.MovementType.IN, 'Stok girişi'),
            (StockMovement.MovementType.ADJUSTMENT, 'Düzeltme'),
        ],
    })
