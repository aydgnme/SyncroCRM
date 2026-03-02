from django.db import models


class Customer(models.Model):
    class CustomerType(models.TextChoices):
        INDIVIDUAL = 'B2C', 'Bireysel'
        CORPORATE = 'B2B', 'Kurumsal'

    type = models.CharField(
        max_length=3,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL,
    )

    # Temel bilgiler
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Kurumsal alanlar — sadece B2B için doldurulur
    company_name = models.CharField(max_length=255, blank=True)
    tax_number = models.CharField(max_length=20, blank=True)
    tax_office = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        if self.type == self.CustomerType.CORPORATE:
            return f"{self.company_name} ({self.get_type_display()})"
        return f"{self.first_name} {self.last_name}"


class SalesChannel(models.Model):
    class Platform(models.TextChoices):
        TRENDYOL = 'TRENDYOL', 'Trendyol'
        AMAZON = 'AMAZON', 'Amazon'
        HEPSIBURADA = 'HEPSIBURADA', 'Hepsiburada'
        N11 = 'N11', 'N11'
        WEBSITE = 'WEBSITE', 'Web Sitesi'
        STORE = 'STORE', 'Fiziksel Mağaza'
        OTHER = 'OTHER', 'Diğer'

    name = models.CharField(max_length=255)  # "İstanbul Mağazası", "Amazon TR" gibi özel isim
    platform = models.CharField(max_length=20, choices=Platform.choices)
    is_active = models.BooleanField(default=True)

    # API entegrasyon bilgileri — ileride doldurulacak
    api_key = models.CharField(max_length=500, blank=True)
    shop_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_channels'

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"
