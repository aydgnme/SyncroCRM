from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthTokenThrottle(AnonRateThrottle):
    """
    /auth/token/ endpoint'i için sıkı limit.
    IP başına 5 istek/dakika — brute force koruması.
    """
    scope = 'auth_token'


class BurstRateThrottle(UserRateThrottle):
    """
    Kısa vadeli burst koruması: dakikada 60 istek.
    Authenticated kullanıcı başına uygulanır.
    """
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """
    Uzun vadeli günlük limit: günde 2000 istek.
    Authenticated kullanıcı başına uygulanır.
    """
    scope = 'sustained'
