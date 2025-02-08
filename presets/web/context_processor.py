from django.conf    import settings
from web.models     import *
from datetime       import datetime  # Import datetime to get the current year
from web.forms      import GeneralEnquiryForm

    
def site_settings(request):
    local_head                  =   None
    setting                     =   None
    general_enquiry_form        =   None
    current_year                =   datetime.now().year  # Get the current year

    try:
        setting                 =   SiteSetting.objects.all().first() if SiteSetting.objects.all().first() else None
        target_url              =   request.build_absolute_uri()
        local_head              =   Head.objects.get(target_url=target_url) if Head.objects.filter(target_url=target_url).exists() else None
        general_enquiry_form    =   GeneralEnquiryForm()
    except Exception as e:
        print('Warning: Exception in Context Processor.')
        print(e)

    return {
        'setting'               : setting,
        'local_head'            : local_head,
        'current_year'          : current_year,  # Add current year to the context
        'general_enquiry_form'  : general_enquiry_form,  # Add current year to the context
    }
