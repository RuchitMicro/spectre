# Code generated from Spectre
from django.db                          import models, IntegrityError
from django.db.models.aggregates        import Max
from django.contrib.sessions.models     import Session
from django.contrib.auth.models         import User
from django.db.models                   import Avg
from django.core.exceptions             import ValidationError
from django.core.serializers            import serialize

# Timezone
from django.utils   import timezone

# Signals
from django.db.models.signals       import post_save
from django.dispatch                import receiver

# HTML Safe String  
from django.utils.safestring        import mark_safe

# Send mail Django's Inbuilt function
from django.core.mail               import send_mail
from django.template.loader         import render_to_string

# Json
import json

# Forms
from django                 import forms       

# Regex
import re

# Django Settings
from django.conf            import settings

# UUID
import uuid

# Django Validators
from django.core.validators import MaxValueValidator, MinValueValidator

# Urllib
import urllib.parse

# Simple History Model
from simple_history.models import HistoricalRecords

# Model Utils
from model_utils        import FieldTracker
from model_utils.fields import MonitorField, StatusField

# TinyMCE
from tinymce.models                 import HTMLField





class CommonModel(models.Model):
    extra_params    =   models.JSONField        (blank=True, null=True)
    created_at      =   models.DateTimeField    (auto_now_add=True, blank=True, null = True)
    updated_at      =   models.DateTimeField    (auto_now=True, blank=True, null=True)
    created_by      =   models.CharField        (max_length=300, blank=True, null=True)
    updated_by      =   models.CharField        (max_length=300, blank=True, null=True)
    
    history         =   HistoricalRecords(inherit=True)
    tracker         =   FieldTracker()

    admin_meta      =   {}
    
    class Meta:
        abstract = True

    # Helper function to get json data of the model
    def get_json(self):
        # Serialize the model instance into JSON format
        data = serialize('json', [self], ensure_ascii=False)
        
        # Convert the serialized data into a Python object
        data = json.loads(data)
        
        # Return the first item in the list as we are serializing a single instance
        return data[0] if data else {}


# Global Settings
class SiteSetting(CommonModel):
    logo                    =   models.ImageField   (blank=True,null=True,upload_to='settings/')
    favicon                 =   models.FileField    (blank=True,null=True,upload_to='settings/')
    global_head             =   models.TextField    (blank=True,null=True, help_text='Common <head> data. It will appear in all pages.')

    address                 =   models.TextField    (blank=True,null=True,max_length=500)
    contact_number          =   models.CharField    (blank=True,null=True,max_length=13)
    email                   =   models.EmailField   (blank=True,null=True)
    gst                     =   models.CharField    (blank=True,null=True,max_length=15, help_text="GST Number")
    extra_contact_details   =   models.TextField           (blank=True,null=True)

    facebook                =   models.URLField     (blank=True,null=True,max_length=100)
    instagram               =   models.URLField     (blank=True,null=True,max_length=100)
    twitter                 =   models.URLField     (blank=True,null=True,max_length=100)
    linkedin                =   models.URLField     (blank=True,null=True,max_length=100)

    vision                  =   models.TextField    (blank=True,null=True)
    mission                 =   models.TextField    (blank=True,null=True)
    values                  =   models.TextField    (blank=True,null=True)
    brochure                =   models.FileField    (blank=True,null=True,upload_to='settings/')
    
    navigation_menu         =   models.JSONField    (blank=True, null=True)

    about_us                =   models.TextField       (blank=True,null=True)
    terms_and_conditions    =   models.TextField       (blank=True,null=True)
    privacy_policy          =   models.TextField       (blank=True,null=True)
    return_policy           =   models.TextField       (blank=True,null=True)
    disclaimer              =   models.TextField       (blank=True,null=True)

    robots                  =   models.FileField    (blank=True,null=True,upload_to='settings/')
    

    # JSON FIELD SCHEMA
    key_value_pair_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "navMenu": {
            "type": "array",
            "items": {
                "$ref": "#/definitions/menuItem"
            }
            }
        },
        "definitions": {
            "menuItem": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the menu item."
                },
                "label": {
                    "type": "string",
                    "description": "Display text for the menu item."
                },
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL link for the menu item."
                },
                "children": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/menuItem"
                },
                "description": "Nested menu items under this menu item."
                }
            },
            "required": ["id", "label"],
            "additionalProperties": False
            }
        }
    }

        
    admin_meta = {
        "json_fields": {
            "navigation_menu": {"schema":  json.dumps(key_value_pair_schema)},
        }
    }
    
    def __str__(self):
        return 'Edit Site Settings'

    class Meta:
        verbose_name_plural = "Site Setting"
    
    def save(self, *args, **kwargs):
        super(SiteSetting, self).save(*args, **kwargs)


# Image Master
class ImageMaster(CommonModel):
    name                =   models.CharField        (max_length=300)
    image               =   models.ImageField       (upload_to="image_master/")
    
    created_at          =   models.DateTimeField    (auto_now_add=True, blank=True, null = True)
    updated_at          =   models.DateTimeField    (auto_now=True, blank=True, null=True)
    
    admin_meta = {
        'list_display': ['name', 'image','__str__', 'created_at', 'updated_at', 'created_by', 'updated_by',],   
    }

    def __str__(self):
        return mark_safe(
            '<div style="height:200px;width:200px;"><img src='+self.image.url+' style="object-fit:contain;height:100%;width:100%" alt=""></div>'
        )


# File Master
class FileMaster(CommonModel):
    name                =   models.CharField    (max_length=300)
    file                =   models.FileField    (upload_to='file_master/')

    created_at          =   models.DateTimeField    (auto_now_add=True, blank=True, null = True)
    updated_at          =   models.DateTimeField    (auto_now=True, blank=True, null=True)

    admin_meta = {
        'list_display': ['name', 'file', '__str__', 'created_at', 'updated_at', 'created_by', 'updated_by'],   
    }

    def __str__(self):
        return str(self.name)

# Contact
class Contact(CommonModel):
    full_name       =   models.CharField    (max_length=300)
    email_id        =   models.EmailField   (max_length=300)
    phone_number    =   models.CharField    (max_length=20)
    requirement     =   models.TextField       ()
    email_ok        =   models.BooleanField (default=False)

    journey_path    =   models.TextField    (blank=True, null=True, help_text='A complete url trace of user journey that lead them to fill the form.')
    
    created_at      =   models.DateTimeField    (auto_now_add=True, blank=True, null = True)
    updated_at      =   models.DateTimeField    (auto_now=True, blank=True, null=True)

    admin_meta = {
        'list_display': ['full_name', 'email_id', 'phone_number', 'created_at', 'updated_at',],
    }

    def __str__(self):
        return str(self.full_name)

    # Notification to Support about a new entry
    def send_mail_notification(self):
        msg_html = render_to_string('web/email/new_enquiry.html', {'Contact': self})
        send_mail(
            'New enquiry from WOLFx',
            'Hello',
            'support@wolfx.io',
            ['hello@wolfx.io'],
            fail_silently=True,
            html_message=msg_html,
        )

    # Notification to User
    def send_mail_greeting(self):
        msg_html = render_to_string('web/email/thank_you_for_contacting.html', {'Contact': self})
        send_mail(
            'WOLFx: Thank you for Contacting us',
            'Hello',
            'support@wolfx.io',
            ['hello@wolfx.io'],
            fail_silently=True,
            html_message=msg_html,
        )




# Blog Models
class BlogCategory(CommonModel):
    category    =   models.CharField(max_length=100, unique=True)
    slug        =   models.SlugField(max_length=100, unique=True)
    image       =   models.FileField(blank=True, null=True, upload_to='blog_category/')
    parent      =   models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        # Recursively build the full category path
        if self.parent:
            return f"{self.parent} -> {self.category}"
        return self.category
    
    def clean(self):
        # Ensure that no cyclic dependencies are created
        if self.parent:
            parent = self.parent
            while parent is not None:
                if parent == self:
                    raise ValidationError("A category cannot be a parent of itself or one of its descendants.")
                parent = parent.parent

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ['category']

class Blog(CommonModel):

    head_default='''<meta name="title" content=" ">
    <meta name="description" content=" ">
    <meta name="keywords" content=" ">
    <meta name="robots" content="index, follow">'''

    title               =   models.CharField        (max_length=200)
    sub_title           =   models.CharField        (max_length=200, blank=True ,null=True)
    thumbnail           =   models.ImageField       (upload_to="blog/")
    category            =   models.ForeignKey       (BlogCategory, null=True, on_delete=models.SET_NULL)
    featured_text       =   models.TextField           (null=True, blank=True)
    text                =   models.TextField           (null=True, blank=True)
    slug                =   models.SlugField        (unique=True)
    readtime            =   models.CharField        (max_length=200,null=True, blank=True)
    tags                =   models.TextField        (null=True, blank=True, default='all')
    head                =   models.TextField        (null=True, blank=True, default=head_default)
    
    order_by            =   models.IntegerField     (default=0)
    
    created_at          =   models.DateTimeField    (auto_now_add=True, blank=True, null=True)
    updated_at          =   models.DateTimeField    (auto_now=True, blank=True, null=True)
    created_by          =   models.CharField        (max_length=300)

    admin_meta =    {
        'list_display'      :   ("__str__","category","created_at","updated_at"),
        'list_editable'     :   ("category",),
        'list_per_page'     :   50,
        'list_filter'       :   ("category",),
        'inline'            :   [
            {'BlogImage': 'blog'}
        ]
    }

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name_plural = "Blog"
        ordering = ['order_by'] #Sort in desc order

class BlogImage(CommonModel):
    blog                =   models.ForeignKey       (Blog, on_delete=models.CASCADE)
    image               =   models.ImageField       (upload_to="blog_images/")
    order_by            =   models.IntegerField     (default=0)

    def __str__(self):
        return str(self.blog)

    class Meta:
        verbose_name_plural = "Blog Image"
        ordering = ['order_by'] #Sort in desc order
    


# Dynamic Head
# Injects data inside <head> of a specific target url
# Used for SEO
class Head(CommonModel):
    target_url  =   models.URLField     (unique=True, help_text="Enter absolute URL of the target.  <br> Ex: https://wolfx.io/blog <br> https://wolfx.io/blog/ <br> https://wolfx.io/blog?category=UI-UX ")
    head        =   models.TextField    (help_text="Head Data")

    def __str__(self):
        return str(self.target_url)
