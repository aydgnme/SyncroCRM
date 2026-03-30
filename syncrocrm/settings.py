from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
    'customers',
    'orders',
    'api',
    'dashboard',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'syncrocrm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'syncrocrm.wsgi.application'

_db_engine = config('DB_ENGINE', default='django.db.backends.postgresql')
_db_name = config('DB_NAME', default='syncrocrm')

DATABASES = {
    'default': {
        'ENGINE': _db_engine,
        # SQLite needs an absolute path; PostgreSQL uses a plain DB name
        'NAME': BASE_DIR / _db_name if _db_engine == 'django.db.backends.sqlite3' else _db_name,
        'USER': config('DB_USER', default='syncrocrm'),
        'PASSWORD': config('DB_PASSWORD', default='syncrocrm'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache — Redis db 1 (Celery db 0 kullanıyor)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
    }
}

from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "SyncroCRM",
    "SITE_HEADER": "SyncroCRM",
    "SITE_URL": "/dashboard/",
    "SITE_ICON": None,
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {
        "font": {
            "subtle-light":    "107 114 128",
            "subtle-dark":     "156 163 175",
            "default-light":   "75 85 99",
            "default-dark":    "209 213 219",
            "important-light": "17 24 39",
            "important-dark":  "243 244 246",
        },
        "primary": {
            "50":  "238 242 255",
            "100": "224 231 255",
            "200": "199 210 254",
            "300": "165 180 252",
            "400": "129 140 248",
            "500": "99 102 241",
            "600": "79 70 229",
            "700": "67 56 202",
            "800": "55 48 163",
            "900": "49 46 129",
            "950": "30 27 75",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Genel Bakış",
                "items": [
                    {"title": "Ana Panel",  "icon": "bar_chart",     "link": "/dashboard/"},
                    {"title": "Siparişler", "icon": "shopping_bag",  "link": "/dashboard/orders/"},
                    {"title": "Stok",       "icon": "archive",       "link": "/dashboard/stock/"},
                ],
            },
            {
                "title": "Envanter",
                "items": [
                    {"title": "Ürünler",          "icon": "inventory_2",  "link": reverse_lazy("admin:inventory_product_changelist")},
                    {"title": "Kategoriler",      "icon": "category",     "link": reverse_lazy("admin:inventory_category_changelist")},
                    {"title": "Depolar",          "icon": "warehouse",    "link": reverse_lazy("admin:inventory_warehouse_changelist")},
                    {"title": "Stok Kayıtları",   "icon": "layers",       "link": reverse_lazy("admin:inventory_stock_changelist")},
                    {"title": "Stok Hareketleri", "icon": "swap_horiz",   "link": reverse_lazy("admin:inventory_stockmovement_changelist")},
                ],
            },
            {
                "title": "Müşteriler",
                "items": [
                    {"title": "Müşteri Listesi", "icon": "people",     "link": reverse_lazy("admin:customers_customer_changelist")},
                    {"title": "Satış Kanalları", "icon": "storefront", "link": reverse_lazy("admin:customers_saleschannel_changelist")},
                ],
            },
            {
                "title": "Sipariş Yönetimi",
                "items": [
                    {"title": "Tüm Siparişler", "icon": "receipt_long", "link": reverse_lazy("admin:orders_order_changelist")},
                ],
            },
        ],
    },
}

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_THROTTLE_CLASSES': [
        'api.throttles.BurstRateThrottle',
        'api.throttles.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst':      '60/min',
        'sustained':  '2000/day',
        'auth_token': '5/min',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Istanbul'

# E-posta
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@syncrocrm.com')
ADMINS = [('SyncroCRM Admin', config('ADMIN_EMAIL', default='admin@syncrocrm.com'))]
