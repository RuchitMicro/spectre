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





class CommonModel(models.Model):
    extra_params    =   models.JSONField        (blank=True, null=True)
    created_at      =   models.DateTimeField    (auto_now_add=True, blank=True, null = True)
    updated_at      =   models.DateTimeField    (auto_now=True, blank=True, null=True)
    created_by      =   models.CharField        (max_length=300, blank=True, null=True)
    updated_by      =   models.CharField        (max_length=300, blank=True, null=True)

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
    iframe                  =   models.URLField     (blank=True, null=True, max_length=999)
    contact_number          =   models.CharField    (blank=True,null=True,max_length=13)
    email                   =   models.EmailField   (blank=True,null=True)
    admin_email             =   models.EmailField   (blank=True, null=True, max_length=300,help_text='Email of the admin. All the Enquiries will be sent to this email.', default='team@example.com')
    gst                     =   models.CharField    (blank=True,null=True,max_length=15, help_text="GST Number")
    extra_contact_details   =   models.TextField     (blank=True,null=True)

    facebook                =   models.URLField     (blank=True,null=True,max_length=100)
    instagram               =   models.URLField     (blank=True,null=True,max_length=100)
    twitter                 =   models.URLField     (blank=True,null=True,max_length=100)
    linkedin                =   models.URLField     (blank=True,null=True,max_length=100)
    youtube                 =   models.URLField     (blank=True,null=True,max_length=100)

    vision                  =   models.TextField    (blank=True,null=True)
    mission                 =   models.TextField    (blank=True,null=True)
    values                  =   models.TextField    (blank=True,null=True)
    brochure                =   models.FileField    (blank=True,null=True,upload_to='settings/')

    about_us                =   models.TextField       (blank=True,null=True)
    terms_and_conditions    =   models.TextField       (blank=True,null=True)
    privacy_policy          =   models.TextField       (blank=True,null=True)
    return_policy           =   models.TextField       (blank=True,null=True)
    disclaimer              =   models.TextField       (blank=True,null=True)

    robots                  =   models.FileField    (blank=True,null=True,upload_to='settings/')

        
    admin_meta = {
        'fieldsets' : [
            ('General', {
                'classes': ['tab'],
                'fields' : ['logo', 'favicon',]},
            ),
            ('Social Media', {
                'classes': ['tab'],
                'fields' : ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube'],
                }),
            ('Contact Information',{
                'classes': ['tab'],
                'fields' : ['address','iframe', 'contact_number', 'email', 'gst', 'extra_contact_details'],
            }),
            ('Vision & Mission',{
                'classes': ['tab'],
                'fields' : ['vision', 'mission', 'values', 'brochure'],
            }),
            ('Security & Compliance',{
                'classes': ['tab'],
                'fields' : ['about_us','terms_and_conditions', 'privacy_policy', 'return_policy', 'disclaimer'],
            }),
            ('Mail',{
                'classes': ['tab'],
                'fields' : ['admin_email',],
            }),
            ('SEO',{
                'classes': ['tab'],
                'fields' : ['global_head', 'robots',],
            }),
        ],
        'single_entry' : True,
        'rtf_exclude' : ['global_head', 'address', 'extra_contact_details'],
    }
    
    def __str__(self):
        return 'Edit Site Settings'

    class Meta:
        verbose_name_plural = "Site Setting"


# Image Master
class ImageMaster(CommonModel):
    name                =   models.CharField        (max_length=300)
    image               =   models.ImageField       (upload_to="image_master/")
    
    admin_meta = {
        'list_display': ['name', 'image', 'created_at', 'updated_at', 'created_by', 'updated_by',],   
    }

    def __str__(self):
        return str()


# File Master
class FileMaster(CommonModel):
    name                =   models.CharField    (max_length=300)
    file                =   models.FileField    (upload_to='file_master/')

    admin_meta = {
        'list_display': ['name', 'file', 'get_file_type', 'created_at', 'updated_at', 'created_by', 'updated_by'],   
    }

    # give me the file type
    def get_file_type(self):
        return self.file.name.split('.')[-1]
    
    def __str__(self):
        return str(self.name)
    
# Banner Image
class BannerImage(CommonModel):
    title           =   models.CharField    (max_length=300, blank=True, null=True, help_text='Title of the Banner Image. This name is shown in the Home page.')
    desktop_image   =   models.ImageField   (upload_to="desktop_banner_image/", blank=True, null=True, help_text='Banner image for desktop. This Image is shown in the Home page.')
    mobile_image    =   models.ImageField   (upload_to="mobile_banner_image/", blank=True, null=True, help_text='Banner image for mobile. This Image is shown in the Home page.')
    description     =   models.TextField    (null=True,blank=True, help_text='Banner description')
    order_by        =   models.IntegerField (default=0, blank=True, null=True)

    def image_display(self):
        if self.desktop_image:
            return mark_safe(
                        '<div style="height:200px;width:200px;"><img src='+self.desktop_image.url+' style="object-fit:contain;height:100%;width:100%" alt=""></div>'
                    )        
        return "No image available"
    
    admin_meta = {
        'list_display': ['title', 'image_display', 'description', 'order_by'],
        'list_editable' : ['order_by'],
        'ordering': ['order_by'],
        'search_fields': ['title', 'desktop_image','mobile_image']
    }
    
    def __str__(self):
        return (self.title)
    
    class Meta:
        verbose_name_plural = "Banner Image"
        ordering            = ['order_by']


# Contact
class Contact(CommonModel):
    full_name       =   models.CharField    (max_length=300)
    email           =   models.EmailField   (max_length=300)
    phone_number    =   models.CharField    (max_length=20)
    requirement     =   models.TextField    ()

    journey_path    =   models.TextField    (blank=True, null=True, help_text='A complete url trace of user journey that lead them to fill the form.')

    admin_meta = {
        'list_display': ['full_name', 'email', 'phone_number', 'created_at', 'updated_at',],
        'search_fields': ['full_name', 'email', 'phone_number',],
        'rtf_exclude' : ['requirement', 'journey_path'],
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

    admin_meta = {
        'list_display' : ['category', 'slug', 'created_at', 'updated_at',],
        'search_fields' : ['category', 'slug',],
    }

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

    admin_meta =    {
        'list_display'      :   ("__str__","category","created_at","updated_at"),
        'list_editable'     :   ("category",),
        'list_per_page'     :   50,
        'list_filter'       :   ("category",),
        'search_fields'     :   ("title","sub_title","category__category"),
        'autocomplete_fields':   ("category",),
        'rtf_exclude'       :   ['head',]
    }

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name_plural = "Blog"
        ordering = ['order_by'] #Sort in desc order

class FAQCategory(CommonModel):
    name                =   models.CharField    (max_length=300, blank=True, null=True)
    description         =   models.TextField    (blank=True, null=True)
    order_by            =   models.IntegerField (default=0, blank=True, null=True)
    
    admin_meta = {
        'list_display': ['name', 'description', 'order_by'],
        'list_editable': ['description', 'order_by',],
        'search_fields' : ['name', ],
        'list_per_page': 50,
        'ordering': ['order_by'],
    }
    
    def __str__(self):
        return str(self.name)
    
    class Meta:
        verbose_name_plural = 'FAQ Categories'
        ordering = ['order_by']
    
class FAQ(CommonModel):
    category            =   models.ForeignKey   (FAQCategory, on_delete=models.CASCADE, blank=True, null=True)
    question            =   models.CharField    (max_length=300, blank=True, null=True)
    answer              =   models.TextField    (blank=True, null=True)
    order_by            =   models.IntegerField (default=0, blank=True, null=True)

    admin_meta = {
        'list_display': ['question', 'answer','order_by'],
        'list_editable': ['answer', 'order_by',],
        'list_per_page': 50,
        'autocomplete_fields' : ['category'],
    }

    def __str__(self):
        return str(self.question)
    
    class Meta:
        verbose_name_plural = 'FAQ'
        ordering = ['order_by'] #Sort in Asc order
        

# Testimonial Models
class Testimonial(CommonModel):
    name            =   models.CharField    (max_length=300, null=True)
    designation     =   models.CharField    (max_length=300, null=True)
    image           =   models.ImageField   (blank=True, null=True, upload_to='testimonial/')
    description     =   models.TextField    (null=True)
    logo            =   models.ImageField   (blank=True, null=True, upload_to='testimonial/company_logo/')
    order_by        =   models.IntegerField (default=0, blank=True, null=True)

    admin_meta = {
        'list_display': ['name', 'designation', 'image', 'logo'],
        'list_per_page': 50,
        'search_fields': ['name', 'designation'],
        'ordering' : ['order_by']
    }

    def __str__(self):
        return str(self.name) if self.name else str(self.id)
    
    class Meta:
        verbose_name_plural = 'Testimonials'
        ordering = ['order_by'] #Sort in Asc order


# Dynamic Head
# Injects data inside <head> of a specific target url
# Used for SEO
class Head(CommonModel):
    target_url  =   models.URLField     (unique=True, help_text="Enter absolute URL of the target.  <br> Ex: https://wolfx.io/blog <br> https://wolfx.io/blog/ <br> https://wolfx.io/blog?category=UI-UX ")
    head        =   models.TextField    (help_text="Head Data")

    admin_meta = {
        'list_display'      :   ("target_url","head","created_at", "updated_at"),
        'list_per_page'     :   50,
        'rtf_exclude'       :   ("head")

    }

    def __str__(self):
        return str(self.target_url)
