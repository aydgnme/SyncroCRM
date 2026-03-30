from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .throttles import AuthTokenThrottle
from .views import CustomerViewSet, ProductViewSet, StockViewSet, OrderViewSet

router = DefaultRouter()
router.register('customers', CustomerViewSet, basename='customer')
router.register('products', ProductViewSet, basename='product')
router.register('stocks', StockViewSet, basename='stock')
router.register('orders', OrderViewSet, basename='order')


class ThrottledTokenObtainView(TokenObtainPairView):
    throttle_classes = [AuthTokenThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthTokenThrottle]


urlpatterns = [
    path('auth/token/', ThrottledTokenObtainView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
