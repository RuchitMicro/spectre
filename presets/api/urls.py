from django.contrib import admin
from django.urls    import path
from api.views      import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),

    # Profile & addresses
    path('profile/', ProfileAPIView.as_view(), name='profile'),

    # Auth
    path('sign-up/', UserRegistrationAPIView.as_view(), name='sign-up'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Content
    path('contact/', ContactAPIView.as_view(), name='contact'),
    path('blog-category/', BlogCategoryAPIView.as_view(), name='blog-category'),
    path('blog/', BlogAPIView.as_view(), name='blog'),
    path('faq-category/', FAQCategoryAPIView.as_view(), name='faq-category'),
    path('faq/', FAQAPIView.as_view(), name='faq'),
    path('testimonial/', TestimonialAPIView.as_view(), name='testimonial'),
    path('site-setting/', SiteSettingAPIView.as_view(), name='site-setting'),

    path('head/', HeadAPIView.as_view(), name='head'),
]