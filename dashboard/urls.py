from django.contrib import admin
from django.urls import path
from . import views

app_name = 'dashboard'

# All views are wrapped with admin.site.admin_view() so they:
# - Require the user to be authenticated AND have is_staff=True
# - Redirect to the admin login page if not authenticated
_v = admin.site.admin_view

urlpatterns = [
    path('', _v(views.index), name='index'),
    path('partials/kpi/', _v(views.kpi_partial), name='kpi_partial'),
    path('orders/', _v(views.orders), name='orders'),
    path('orders/new/', _v(views.order_create), name='order_create'),
    path('orders/<int:pk>/<str:action>/', _v(views.order_action), name='order_action'),
    path('stock/', _v(views.stock), name='stock'),
    path('stock/<int:pk>/adjust/', _v(views.stock_adjust), name='stock_adjust'),
]
