from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework.routers import DefaultRouter
from . import views


route = DefaultRouter()
###############################################################
# ROUTES
route.register('', views.UserViewSet)

# PATHS
urlpatterns = [
    # path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token-blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path("", include(route.urls)),

]