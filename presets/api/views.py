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

from api.models                 import *



class IndexView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'message': 'INDEX GET'})
    
    def post(self, request, *args, **kwargs):
        return JsonResponse({'message': 'INDEX POST'})
    


# Django Unfold Admin
def dashboard_callback(request, context):

    # if(closing.object.get(date=yesterday_date).exists()):
    # do nothing
    # else
    # incoming_money_total = get all incoming money of yesterday
    # outgoing_money_total = get all outgoing money of yesterday
    # yesterday_closing_balance = incoming_money_total - outgoing_money_total
    # total_balance = 
    # closing.object.create(date=yesterday_date, closing_balance=yesterday_closing_balance)


    context.update({
        "custom_variable": "value",
        "cards": [
            {"title": "Card 1", "metric": "Metric 1"},
            {"title": "Card 2", "metric": "Metric 2"},
            {"title": "Card 3", "metric": "Metric 3"},
        ],
        "navigation": [
            {"title": "Dashboard", "link": "/", "icon": "dashboard"},
            {"title": "Users", "link": "/admin/users", "icon": "people"},
        ],
        "filters": [
            {"title": "Filter 1", "link": "/filter1"},
            {"title": "Filter 2", "link": "/filter2"},
        ],
    })
    return context