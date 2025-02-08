from django                 import forms
from django.conf            import settings
from django.core.exceptions import ValidationError
from web.models             import Contact  # Import the model here to avoid circular imports


# custom form widget
class CustomCheckBoxWidget(forms.CheckboxSelectMultiple):
    allow_multiple_selected     = True
    input_type                  = "checkbox"
    # template_name = "django/forms/widgets/checkbox_select.html"
    # option_template_name = "django/forms/widgets/checkbox_option.html"

    template_name               =   "web/widget/checkbox_select.html"
    option_template_name        =   "web/widget/checkbox_option.html"

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False

    def value_omitted_from_data(self, data, files, name):
        # HTML checkboxes don't appear in POST data if not checked, so it's
        # never known if the value is actually omitted.
        return False


class GeneralEnquiryForm(forms.Form):
   
    # Form fields with updated help texts
    name = forms.CharField(
        max_length      =   100, 
        help_text       =   'Please enter your full name.',
        label_suffix    =   '*',
    )
    email = forms.EmailField(
        help_text       =   'Provide a valid email address where we can contact you.',
        label_suffix    =   '*',
    )
    phone_number = forms.CharField(
        max_length      =   15, 
        help_text       =   'Enter your phone number including the area code.',
        label_suffix    =   '*',
    )
    company_name = forms.CharField(
        max_length      =   100, 
        help_text       =   'Enter your company or organization name.',
        label_suffix    =   '*',
    )
    message = forms.CharField(
        widget          =   forms.Textarea, 
        required        =   False,
        help_text       =   'Provide any additional information or project details here.',
        label_suffix    =   '',
    )
    
    # Hidden fields
    journey = forms.CharField(
        required        =   False, 
        widget          =   forms.HiddenInput, 
        label_suffix    =   '',
    )
    extra_params = forms.CharField(
        required        =   False, 
        widget          =   forms.HiddenInput, 
        label_suffix    =   '',
    )


    def save(self):
        """
        Save the form data into the Contact model.
        """

        # Create a new Contact instance
        contact = Contact(
            full_name       =   self.cleaned_data['name'],
            email_id        =   self.cleaned_data['email'],
            phone_number    =   self.cleaned_data['phone_number'],
            company_name    =   self.cleaned_data['company_name'],  # Map company_name
            requirement     =   self.cleaned_data['message'],  # Map message to requirement
            journey_path    =   self.cleaned_data.get('journey', ''),  # Optional field
            extra_params    =   self.cleaned_data.get('extra_params', ''),  # Optional field
        )

        # Save the instance
        contact.save()

        # Optionally send email notifications
        contact.send_mail_notification()
        contact.send_mail_greeting()

        return contact
