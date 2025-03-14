from django.contrib import admin
from rest_framework.decorators import api_view
from django.urls import path, include
from rest_framework.response import Response
from django.conf.urls.static import static
from django.conf import settings

# Welcome view
@api_view(['GET'])
def welcome_view(request):
    return Response({"message": "Welcome to Django Boiler Plate"})


################################################################
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', welcome_view),
    path('api/auth/', include('authentication.urls')),
    path('api/core/', include('core.urls')),
    path('__debug__/', include("debug_toolbar.urls")),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)