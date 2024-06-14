from django.contrib             import admin
from django.urls                import path, include
from django.conf.urls.static    import static   # static file config
from django.conf                import settings # static file config
from .views                     import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('profile', IndexView.as_view(), name='profile'),
]


urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT) # static file config
