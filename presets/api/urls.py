from django.contrib import admin
from django.urls    import path

from api.views      import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
