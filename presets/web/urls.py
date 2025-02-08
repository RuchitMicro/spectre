from django.contrib import admin
from django.urls    import path

from web.views      import *

urlpatterns = [
    path('', IndexView.as_view(), name='index'),

    # Contact Us
    path('contact-us/', ContactUsView.as_view(), name='contact-us'),

    # FAQ
    path('faq/', FAQView.as_view(), name ='faq'),

    # legal 
    path('privacy-policy/',         PrivacyPolicyView.as_view(),        name ='privacy-policy'),
    path('terms-and-conditions/',   TermsAndConditionsView.as_view(),   name ='terms-and-conditions'),
    path('cookie-policy/',          CookiePolicyView.as_view(),         name ='cookie-policy'),

    # Case Study 
    path('case-study/',                     CaseStudyListView.as_view(),    name ='case-study'),
    path('case-study/<slug:slug>/',         CaseStudyListView.as_view(),    name ='case-study'),
    path('case-study-detail/<slug:slug>/',  CaseStudyDetailView.as_view(),  name ='case-study-detail'),

    # Keep these last Blog Contents
    path('blog/',               BlogListView.as_view(), name ='blog'),
    path('blog/<slug:slug>',    BlogListView.as_view(), name ='blog'),
    path('<slug:slug>',         BlogDetailView.as_view(), name ='blog-detail'),
    
]
