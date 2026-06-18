import uuid
import json
import calendar
import re
import tablib
import datetime
from django.shortcuts               import get_object_or_404, redirect, render
from django.urls                    import get_resolver, reverse
from django.http                    import HttpResponse, JsonResponse, HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseServerError
from django.db                      import transaction
from django.db.models               import Sum, Aggregate, Count, Avg
from django.db.models.functions     import TruncMonth
from django.contrib.auth            import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins     import LoginRequiredMixin
from django.contrib.auth.models     import Group, Permission


# Settings
from django.conf                    import settings

# Django Views
from django.views               import View     # Importing django class based view
from django.views.generic       import CreateView, TemplateView, ListView, UpdateView, DetailView # Importing django generic class based view

# DRF 
from rest_framework.views           import APIView
from rest_framework.response        import Response
from rest_framework                 import status
from rest_framework.generics        import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions     import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework.pagination      import PageNumberPagination
from rest_framework.filters         import SearchFilter, OrderingFilter

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework                 import generics

# Send mail Django's Inbuilt function
from django.core.mail           import send_mail
from django.template.loader     import render_to_string

# Django API Helper
from django_api_helper.views        import  GenericCRUDView, GenericObjectPermissionView, GenericBulkUploadView
from django_api_helper.serializers  import  create_model_serializer
from django_api_helper.resources    import  create_dynamic_resource
from django_api_helper.filters      import  DynamicFilterSetCreator
from django_api_helper.decorators   import  error_handling, check_table_permissions

# Import Export
from import_export.formats.base_formats import CSV, XLS, XLSX

from .models                import *
from .serializers           import *



class IndexView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'message': 'Healthy and alive!'}, status=status.HTTP_200_OK)
    
class ReadOnlyView(GenericCRUDView):
    http_method_names       = ["get", "head", "options"]
    bypass_table_permission = True
    permission_classes      = [AllowAny]

    def get_serializer_class(self):
        if not self.model:
            raise AssertionError("ReadOnlyView requires a 'model' attribute.")
        return create_model_serializer(self.model)

    def post(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})

    def patch(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})

    def delete(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})


class CreateOnlyView(GenericCRUDView):
    http_method_names       = ["post", "head", "options"]
    bypass_table_permission = True
    permission_classes      = [AllowAny]

    def get_serializer_class(self):
        if not self.model:
            raise AssertionError("CreateOnlyView requires a 'model' attribute.")
        return create_model_serializer(self.model)
    
    # Fully generic schema generator
    def get(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})

    def patch(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})

    def delete(self, request, *args, **kwargs):
        return Response({"error": "Method not allowed", "status": status.HTTP_405_METHOD_NOT_ALLOWED})

# ---------------------------------------------------------------------------
# Site / SEO
# ---------------------------------------------------------------------------

class SiteSettingAPIView(ReadOnlyView):
    model = SiteSetting

class HeadAPIView(ReadOnlyView):
    model = Head

class BannerAPIView(ReadOnlyView):
    model = BannerImage

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class ProfileAPIView(GenericCRUDView):
    model = Profile
    permission_classes = [IsAuthenticated]
    serializer_class = create_model_serializer(Profile)
    bypass_table_permission = True

    def get_object(self):
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return Response({"error": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProfileUpdateSerializer(
            profile, data=request.data, partial=True, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        return Response({"error": "Permission Denied"}, status=status.HTTP_403_FORBIDDEN)

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

class ContactAPIView(CreateOnlyView):
    model = Contact

class BlogCategoryAPIView(ReadOnlyView):
    model = BlogCategory

class BlogAPIView(ReadOnlyView):
    model = Blog

class FAQCategoryAPIView(ReadOnlyView):
    model = FAQCategory

class FAQAPIView(ReadOnlyView):
    model = FAQ

class TestimonialAPIView(ReadOnlyView):
    model = Testimonial



# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserRegistrationAPIView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(generics.CreateAPIView):
    serializer_class = PasswordResetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.UpdateAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password has been reset.'}, status=status.HTTP_200_OK)
