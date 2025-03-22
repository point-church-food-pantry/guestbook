from django import forms
from jsignature.forms import JSignatureField
from jsignature.widgets import JSignatureWidget
from django.core.exceptions import ValidationError

class GuestInput(forms.Form):
    first_name = forms.CharField(required = True, strip = True, max_length = 256)
    last_name = forms.CharField(required = True, strip = True, max_length = 256)
    guest_ID = forms.IntegerField(required = False)
    city = forms.CharField(required = False, strip = True, max_length = 256)
    county = forms.CharField(required = True, strip = True, max_length = 256)
    state = forms.CharField(required = True, strip = True, max_length = 256)
    phone = forms.CharField(required = False, strip = True, max_length = 256)
    email = forms.CharField(required = False, strip = True, max_length = 256)
    number_in_household = forms.IntegerField(required = True, min_value = 1, max_value = 20)
    authorized_representative_1 = forms.CharField(required = False, strip = True, max_length = 256)
    authorized_representative_2 = forms.CharField(required = False, strip = True, max_length = 256)
    tefap_signature = JSignatureField(required = True, widget=JSignatureWidget(jsignature_attrs = {'background-color' : '#d9ecea'}))

class SignInInput(forms.Form):
    who_performed_pickup = forms.ChoiceField(choices = [])
    signature = JSignatureField(required = True, widget=JSignatureWidget(jsignature_attrs = {'background-color' : '#d9ecea'}))
    fns = forms.ChoiceField(required = True, choices = [('No', 'No'), ('Yes', 'Yes/Sí')])
    number_in_household = forms.IntegerField(required = False, min_value = 1, max_value = 20)
    previously_reported_number_in_household = forms.IntegerField(required = False)
    yearly_income = forms.IntegerField(required = False)
    monthly_income = forms.IntegerField(required = False)
    weekly_income = forms.IntegerField(required = False)
    agency_representative_signature = JSignatureField(required = True, widget=JSignatureWidget(jsignature_attrs = {'background-color' : '#d9ecea'}))

    def clean(self):

        cleaned_data = super().clean()

        # Assumed maximum incomes per year, month, or week; incomes above this throw an error
        yearly_assumed_max = 1000000
        monthly_assumed_max = 100000
        weekly_assumed_max = 25000

        # If client recieves food stamps, we don't need to check income.
        # If client does not recieve food stamps, we need either yearly, monthly, or weekly income.
        fns = cleaned_data['fns']
        y = cleaned_data['yearly_income']
        m = cleaned_data['monthly_income']
        w = cleaned_data['weekly_income']
    
        if (fns == 'No') and (y == None) and (m == None) and (w == None):
            raise ValidationError("Please input at least one of the following: Weekly, Monthly, or Yearly Income.")
        elif y != None:
            if y > yearly_assumed_max:
                raise ValidationError(rf"Incomes over ${yearly_assumed_max} yearly must be entered in the Admin Portal directly.")
        elif m != None:
            if m > monthly_assumed_max:
                raise ValidationError(rf"Incomes over ${monthly_assumed_max} monthly must be entered in the Admin Portal directly.")
        elif w != None:
            if w > weekly_assumed_max:
                raise ValidationError(rf"Incomes over ${weekly_assumed_max} weekly must be entered in the Admin Portal directly.")

        # If number in household and previously reported number in household (i.e. last time the client was present) 
        # differ by more than 9 individuals, throw an error.

        if cleaned_data['number_in_household'] != None:
            if abs(cleaned_data['number_in_household'] - cleaned_data['previously_reported_number_in_household']) > 9:
                raise ValidationError(rf"Error: The number of individuals in your household has changed by more than 9 since your last visit. This is almost always due to a data input error. If your data is accurate, please enter it in the Admin Portal directly.")

        return cleaned_data
        
class SearchBar(forms.Form):
    name_search = forms.CharField(required = False, strip = True, max_length = 256)

class LinkedProxyInput(forms.Form):
    fns = forms.ChoiceField(choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.Select, required=True)
    monthly_income = forms.IntegerField(required = True, min_value = 0, max_value = 9999999)
    proxy_signature = JSignatureField(required = True, widget=JSignatureWidget(jsignature_attrs = {'background-color' : '#d9ecea'}))

class UnlinkedProxyInput(LinkedProxyInput):
    first_name = forms.CharField(required = True, strip = True, max_length = 256)
    last_name = forms.CharField(required = True, strip = True, max_length = 256)
    address = forms.CharField(required = False, strip = True, max_length = 256)
    city = forms.CharField(required = False, strip = True, max_length = 256)
    county = forms.CharField(required = True, strip = True, max_length = 256)
    state = forms.CharField(required = True, strip = True, max_length = 256)
    number_in_household = forms.IntegerField(required = True, min_value = 1, max_value = 9999999)
    authorized_representative_1 = forms.CharField(required = True, strip = True, max_length = 256)
    authorized_representative_2 = forms.CharField(required = False, strip = True, max_length = 256)
    guest_bestguess = forms.CharField(required = False, strip = True, max_length = 256) # Client can input guest ID if they remember it




