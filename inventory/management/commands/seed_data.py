"""
Tüm katmanlar için test verisi oluşturur.
Kullanım: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Katman 1-2-3 için örnek test verisi oluşturur'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self._create_categories()
            self._create_warehouses()
            self._create_products()
            self._create_stocks()
            self._create_customers()
            self._create_sales_channels()
            self._create_orders()
        self.stdout.write(self.style.SUCCESS('Test verisi başarıyla oluşturuldu.'))

    # ------------------------------------------------------------------
    # Katman 1
    # ------------------------------------------------------------------

    def _create_categories(self):
        from inventory.models import Category
        data = [
            ('Elektronik', 'Telefon, tablet, bilgisayar ve aksesuarlar'),
            ('Giyim', 'Erkek, kadın ve çocuk giyim ürünleri'),
            ('Ev & Yaşam', 'Mutfak, banyo ve dekorasyon ürünleri'),
        ]
        for name, desc in data:
            Category.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write('  ✓ Kategoriler')

    def _create_warehouses(self):
        from inventory.models import Warehouse
        data = [
            ('İstanbul Merkez Depo', 'Esenyurt, İstanbul', 'WAREHOUSE'),
            ('Ankara Depo', 'Ostim, Ankara', 'WAREHOUSE'),
            ('Kadıköy Mağaza', 'Kadıköy, İstanbul', 'STORE'),
        ]
        for name, location, wtype in data:
            Warehouse.objects.get_or_create(name=name, defaults={'location': location, 'type': wtype})
        self.stdout.write('  ✓ Depolar / Mağazalar')

    def _create_products(self):
        from inventory.models import Product, Category
        elektronik = Category.objects.get(name='Elektronik')
        giyim = Category.objects.get(name='Giyim')
        ev = Category.objects.get(name='Ev & Yaşam')

        data = [
            ('SKU-001', 'iPhone 15 Kılıf', '8690001000010', 149.90, 'adet', elektronik),
            ('SKU-002', 'USB-C Şarj Kablosu', '8690001000027', 89.90, 'adet', elektronik),
            ('SKU-003', 'Bluetooth Kulaklık', '8690001000034', 599.90, 'adet', elektronik),
            ('SKU-004', 'Erkek Pamuklu T-Shirt', '8690001000041', 199.90, 'adet', giyim),
            ('SKU-005', 'Kadın Jogger Eşofman', '8690001000058', 349.90, 'adet', giyim),
            ('SKU-006', 'Cam Kapaklı Saklama Kabı', '8690001000065', 124.90, 'adet', ev),
        ]
        for sku, name, barcode, price, unit, cat in data:
            Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'barcode': barcode,
                    'base_price': price,
                    'unit': unit,
                    'category': cat,
                },
            )
        self.stdout.write('  ✓ Ürünler')

    def _create_stocks(self):
        from inventory.models import Product, Warehouse, Stock, StockMovement
        warehouses = {w.name: w for w in Warehouse.objects.all()}
        products = {p.sku: p for p in Product.objects.all()}

        # (sku, depo_adı, miktar, min_level)
        data = [
            ('SKU-001', 'İstanbul Merkez Depo', 150, 20),
            ('SKU-001', 'Ankara Depo', 80, 10),
            ('SKU-001', 'Kadıköy Mağaza', 25, 5),
            ('SKU-002', 'İstanbul Merkez Depo', 300, 50),
            ('SKU-002', 'Ankara Depo', 120, 20),
            ('SKU-003', 'İstanbul Merkez Depo', 45, 10),
            ('SKU-003', 'Kadıköy Mağaza', 8, 5),
            ('SKU-004', 'İstanbul Merkez Depo', 200, 30),
            ('SKU-004', 'Ankara Depo', 90, 15),
            ('SKU-004', 'Kadıköy Mağaza', 3, 5),   # Kritik stok — uyarı tetiklemeli
            ('SKU-005', 'İstanbul Merkez Depo', 110, 20),
            ('SKU-006', 'İstanbul Merkez Depo', 75, 10),
            ('SKU-006', 'Kadıköy Mağaza', 12, 5),
        ]
        for sku, wname, qty, min_lvl in data:
            stock, created = Stock.objects.get_or_create(
                product=products[sku],
                warehouse=warehouses[wname],
                defaults={'quantity': qty, 'min_level': min_lvl},
            )
            if created:
                StockMovement.objects.create(
                    stock=stock,
                    change=qty,
                    type=StockMovement.MovementType.IN,
                    reason='Açılış stok girişi',
                    reference='SEED-INIT',
                )
        self.stdout.write('  ✓ Stoklar + Açılış hareketleri')

    # ------------------------------------------------------------------
    # Katman 2
    # ------------------------------------------------------------------

    def _create_customers(self):
        from customers.models import Customer
        data = [
            {
                'type': 'B2C', 'first_name': 'Ahmet', 'last_name': 'Yılmaz',
                'email': 'ahmet.yilmaz@email.com', 'phone': '05301234567',
                'address': 'Kadıköy, İstanbul',
            },
            {
                'type': 'B2C', 'first_name': 'Zeynep', 'last_name': 'Kaya',
                'email': 'zeynep.kaya@email.com', 'phone': '05421234567',
                'address': 'Çankaya, Ankara',
            },
            {
                'type': 'B2B', 'first_name': 'Mehmet', 'last_name': 'Demir',
                'email': 'satin.alma@teknohub.com', 'phone': '02121234567',
                'address': 'Maslak, İstanbul',
                'company_name': 'TeknoHub Bilişim A.Ş.',
                'tax_number': '1234567890',
                'tax_office': 'Sarıyer VD',
            },
        ]
        for item in data:
            Customer.objects.get_or_create(email=item['email'], defaults=item)
        self.stdout.write('  ✓ Müşteriler (2 B2C, 1 B2B)')

    def _create_sales_channels(self):
        from customers.models import SalesChannel
        data = [
            ('Trendyol TR', 'TRENDYOL'),
            ('Amazon TR', 'AMAZON'),
            ('Kadıköy Mağaza', 'STORE'),
            ('syncrocrm.com', 'WEBSITE'),
        ]
        for name, platform in data:
            SalesChannel.objects.get_or_create(name=name, defaults={'platform': platform})
        self.stdout.write('  ✓ Satış Kanalları')

    # ------------------------------------------------------------------
    # Katman 3
    # ------------------------------------------------------------------

    def _create_orders(self):
        from customers.models import Customer, SalesChannel
        from inventory.models import Product, Warehouse
        from orders.models import Order, OrderItem

        customers = {c.email: c for c in Customer.objects.all()}
        channels = {c.name: c for c in SalesChannel.objects.all()}
        products = {p.sku: p for p in Product.objects.all()}
        warehouses = {w.name: w for w in Warehouse.objects.all()}
        istanbul = warehouses['İstanbul Merkez Depo']
        ankara = warehouses['Ankara Depo']
        magaza = warehouses['Kadıköy Mağaza']

        orders_data = [
            # Teslim edilmiş sipariş — tam akış
            {
                'order_number': 'ORD-0001',
                'customer': customers['ahmet.yilmaz@email.com'],
                'sales_channel': channels['Trendyol TR'],
                'status': Order.Status.DELIVERED,
                'items': [
                    (products['SKU-001'], istanbul, 2, 149.90),
                    (products['SKU-002'], istanbul, 1, 89.90),
                ],
            },
            # Kargoda olan sipariş
            {
                'order_number': 'ORD-0002',
                'customer': customers['zeynep.kaya@email.com'],
                'sales_channel': channels['Amazon TR'],
                'status': Order.Status.SHIPPED,
                'items': [
                    (products['SKU-003'], istanbul, 1, 599.90),
                ],
            },
            # Onaylanmış kurumsal sipariş
            {
                'order_number': 'ORD-0003',
                'customer': customers['satin.alma@teknohub.com'],
                'sales_channel': channels['syncrocrm.com'],
                'status': Order.Status.CONFIRMED,
                'items': [
                    (products['SKU-004'], istanbul, 10, 179.90),
                    (products['SKU-005'], istanbul, 5, 299.90),
                ],
            },
            # Beklemedeki mağaza siparişi
            {
                'order_number': 'ORD-0004',
                'customer': customers['ahmet.yilmaz@email.com'],
                'sales_channel': channels['Kadıköy Mağaza'],
                'status': Order.Status.PENDING,
                'items': [
                    (products['SKU-006'], magaza, 3, 124.90),
                ],
            },
            # İptal edilmiş sipariş — stok iade testi
            {
                'order_number': 'ORD-0005',
                'customer': customers['zeynep.kaya@email.com'],
                'sales_channel': channels['Trendyol TR'],
                'status': Order.Status.CANCELLED,
                'items': [
                    (products['SKU-001'], ankara, 1, 149.90),
                ],
            },
        ]

        for o in orders_data:
            if Order.objects.filter(order_number=o['order_number']).exists():
                continue

            # Önce PENDING olarak oluştur — signal'lar doğru çalışsın
            order = Order.objects.create(
                order_number=o['order_number'],
                customer=o['customer'],
                sales_channel=o['sales_channel'],
                status=Order.Status.PENDING,
                note='Seed verisi',
            )
            for product, warehouse, qty, price in o['items']:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    warehouse=warehouse,
                    quantity=qty,
                    unit_price=price,
                )

            # Hedef statüse ilerlet — her adımda signal tetiklensin
            target = o['status']
            flow = [
                Order.Status.CONFIRMED,
                Order.Status.SHIPPED,
                Order.Status.DELIVERED,
            ]
            if target == Order.Status.CANCELLED:
                order.status = Order.Status.CANCELLED
                order.save()
            else:
                for step in flow:
                    order.status = step
                    order.save()
                    if step == target:
                        break

        self.stdout.write('  ✓ Siparişler (5 adet — DELIVERED, SHIPPED, CONFIRMED, PENDING, CANCELLED)')
