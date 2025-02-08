# Generated using Spectre 
# Strictly to be used for web templates.
# Use this file as a reference for your project's settings.py file.

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    "unfold",                           # before django.contrib.admin
    "unfold.contrib.filters",           # optional, if special filters are needed
    "unfold.contrib.forms",             # optional, if special form elements are needed
    "unfold.contrib.import_export",     # optional, if django-import-export package is used
    "unfold.contrib.simple_history",    # optional, if django-simple-history package is used
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_recaptcha',
    'django_cleanup.apps.CleanupConfig',
    'simple_history',
    'import_export',
    
    'web',
]

APPEND_SLASH = True


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'unfold-templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'web.context_processor.site_settings',  # Add this line for context processor
            ],
        },
    },
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_URL          =   '/static/'
STATICFILES_DIRS    =   [
    os.path.join(BASE_DIR, 'web/static'),
]
STATIC_ROOT =   os.path.join(BASE_DIR, 'static')
MEDIA_URL   =   '/media/'
MEDIA_ROOT  =   os.path.join(BASE_DIR, 'media')





# ReCaptcha
RECAPTCHA_PRIVATE_KEY       = '*****'
RECAPTCHA_PUBLIC_KEY        = '*****'
RECAPTCHA_DEFAULT_ACTION    = 'generic'
RECAPTCHA_SCORE_THRESHOLD   = 0.7
# RECAPTCHA_LANGUAGE          = 'en' # for auto detection language, remove this from your settings
RECAPTCHA_DISABLE           = False



# Email Setup
DEFAULT_FROM_EMAIL  =   'hello@wolfx.io'
EMAIL_HOST          =   'smtp.zoho.in'
EMAIL_HOST_USER     =   'hello@wolfx.io'
EMAIL_HOST_PASSWORD =   '*******'
EMAIL_PORT          =   587
EMAIL_USE_TLS       =   True
EMAIL_USE_SSL       =   False






# Django Unfold settings
# settings.py
from django.templatetags.static import static
from django.urls                import reverse_lazy
from django.utils.translation   import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": 'WOLFx Admin',
    "SITE_HEADER": 'WOLFx Admin',
    "SITE_URL": "/",
    "SITE_SYMBOL": "speed",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "web.views.dashboard_callback",
    "STYLES": [
        lambda request: static("web/css/style.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": ("Main"),
                "items": [
                    {
                        "title": ("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": ("Authentication and Authorization"),
                "separator": True,
                "items": [
                    {
                        "title": ("Users"),
                        "icon": "person",
                        "link": "/admin/auth/user/"
                    },
                    {
                        "title": ("Groups"),
                        "icon": "group",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": ("Site Configuration"),
                "separator": True,
                "items": [
                    {
                        "title": ("Site Setting"),
                        "icon": "settings",
                        "link": "/admin/web/sitesetting/",
                    },
                ]
            },
            {
                "title": ("Media"),
                "items": [
                    {
                        "title": ("Image Master"),
                        "icon": "image",
                        "link": "/admin/web/imagemaster/",
                    },
                    {
                        "title": ("File Master"),
                        "icon": "attach_file",
                        "link": "/admin/web/filemaster/",
                    },
                ]
            },
            {
                "title": ("Content"),
                "items": [
                    {
                        "title": ("Contact"),
                        "icon": "contact_phone",
                        "link": "/admin/web/contact/",
                    },
                    {
                        "title": ("FAQ Category"),
                        "icon": "help_outline",
                        "link": "/admin/web/faqcategory/",
                    },
                    {
                        "title": ("FAQ"),
                        "icon": "help_outline",
                        "link": "/admin/web/faq/",
                    },
                ]
            },
            {
                "title": ("Case Studies"),
                "items": [
                    {
                        "title": ("Case Study Category"),
                        "icon": "category",
                        "link": "/admin/web/casestudycategory/",
                    },
                    {
                        "title": ("Case Study"),
                        "icon": "article",
                        "link": "/admin/web/casestudy/",
                    },
                    {
                        "title": ("Case Study FAQ"),
                        "icon": "question_answer",
                        "link": "/admin/web/casestudyfaq/",
                    },
                ]
            },
            {
                "title": ("Blog"),
                "items": [
                    {
                        "title": ("Blog Category"),
                        "icon": "category",
                        "link": "/admin/web/blogcategory/",
                    },
                    {
                        "title": ("Blog"),
                        "icon": "article",
                        "link": "/admin/web/blog/",
                    },
                    {
                        "title": ("Blog Image"),
                        "icon": "image",
                        "link": "/admin/web/blogimage/",
                    },
                ]
            },
            {
                "title": ("SEO & Redirects"),
                "items": [
                    {
                        "title": ("Redirect"),
                        "icon": "redo",
                        "link": "/admin/web/redirect/",
                    },
                    {
                        "title": ("Head"),
                        "icon": "manage_search",
                        "link": "/admin/web/head/",
                    },
                ]
            },
        ],
    },
}



