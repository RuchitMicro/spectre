from django.contrib import admin
from django.urls    import path

from web.views      import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),

    # Keep these last Blog Contents
    path('blog/', BlogListView.as_view(), name ='Blog'),
    path('blog/<slug:slug>', BlogListView.as_view(), name ='Blog'),
    path('<slug:slug>', BlogDetailView.as_view(), name ='Blog-Detail'),
    
    path('r/<slug:slug>', RedirectView.as_view(), name='redirect'),

]
