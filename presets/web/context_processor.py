from django.conf import settings
from web.models     import *

def site_settings(request):
    local_head  =   None
    setting     =   None
    try:
        setting     =   SiteSetting.objects.all().first() if SiteSetting.objects.all().first() else None
        target_url  =   request.build_absolute_uri()
        local_head  =   Head.objects.get(target_url=target_url) if Head.objects.filter(target_url=target_url).exists() else None
    except Exception as e:
        print('Exception in Context Processor.')
        print(e)

    return {
        'setting'       : setting,
        'local_head'    : local_head,
    }
