from django import forms
from jsignature.forms import JSignatureField
from django.core.exceptions import ValidationError

class GuestInput(forms.Form):
    guest_ID = forms.IntegerField(required = False)
    first_name = forms.CharField(required = True, strip = True, max_length = 256)
    last_name = forms.CharField(required = True, strip = True, max_length = 256)
    address = forms.CharField(required = True, strip = True, max_length = 256)
    city = forms.CharField(required = True, strip = True, max_length = 256)
    county = forms.CharField(required = True, strip = True, max_length = 256)
    phone = forms.CharField(required = False, strip = True, max_length = 256)
    email = forms.CharField(required = False, strip = True, max_length = 256)
    number_in_household = forms.IntegerField(required = True, min_value = 1, max_value = 99)
    authorized_representative_1 = forms.CharField(required = False, strip = True, max_length = 256)
    authorized_representative_2 = forms.CharField(required = False, strip = True, max_length = 256)
    tefap_signature = JSignatureField(required = True)

class SignInInput(forms.Form):
    who_performed_pickup = forms.ChoiceField(choices = [])
    signature = JSignatureField(required = True)
    fns = forms.ChoiceField(required = True, choices = [('No', 'No'), ('Yes', 'Yes/Sí')])
    number_in_household = forms.IntegerField(required = False, min_value = 1)
    yearly_income = forms.IntegerField(required = False)
    monthly_income = forms.IntegerField(required = False)
    weekly_income = forms.IntegerField(required = False)
    agency_representative_signature = JSignatureField(required = True)
    
    def clean(self):
        cleaned_data = super().clean()
        fns = cleaned_data['fns']
        y = cleaned_data['yearly_income']
        m = cleaned_data['monthly_income']
        w = cleaned_data['weekly_income']
    
        if (fns == 'No') and (y == None) and (m == None) and (w == None):
            raise ValidationError("Please input at least one of the following: Weekly, Monthly, or Yearly Income.")      

        return cleaned_data
        
class SearchBar(forms.Form):
    name_search = forms.CharField(required = False, strip = True, max_length = 256)




