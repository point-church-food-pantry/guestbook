from django.db import models

# Create your models here.

class Guest(models.Model):
    '''
    Information for new guests, corresponding to front page of TEFAP form.
    '''
    internal_ID = models.BigAutoField(primary_key = True) # For internal database use only
    guest_ID = models.BigIntegerField(blank = True, null = True) # Number the guests use
    active = models.CharField(max_length = 256, blank = True, null = True)
    first_name = models.CharField(max_length = 256, blank = True, null = True)
    last_name = models.CharField(max_length = 256, blank = True, null = True)
    address = models.CharField(max_length = 256, blank = True, null = True)
    city = models.CharField(max_length = 256, blank = True, null = True)
    county = models.CharField(max_length = 256, blank = True, null = True)
    phone = models.CharField(max_length = 256, blank = True, null = True)
    email = models.CharField(max_length = 256, blank = True, null = True)
    number_in_household = models.BigIntegerField(blank = True, null = True)
    authorized_representative_1 = models.CharField(max_length = 256, blank = True, null = True)
    authorized_representative_2 = models.CharField(max_length = 256, blank = True, null = True)
    authorized_representative_3 = models.CharField(max_length = 256, blank = True, null = True)
    authorized_representative_4 = models.CharField(max_length = 256, blank = True, null = True)
    authorized_representative_5 = models.CharField(max_length = 256, blank = True, null = True)
    tefap_signature_date = models.CharField(max_length = 256, blank = True, null = True)
    tefap_signature = models.TextField(blank = True, null = True)
    language_preference = models.CharField(max_length = 256, blank = True, null = True)

    def __str__(self):
        return f"{self.guest_ID} - {self.first_name} {self.last_name} ({self.internal_ID})"

class SignIn(models.Model):
    '''
    Records of each sign-in for each guest, corresponding to back page of TEFAP form.
    '''
    internal_ID = models.ForeignKey(Guest, on_delete = models.PROTECT)
    date = models.CharField(max_length = 256, blank = True, null = True)
    who_performed_pickup = models.CharField(max_length = 256, blank = True, null = True)
    signature = models.TextField(blank = True, null = True)
    fns = models.CharField(max_length = 256, blank = True, null = True)
    number_in_household = models.BigIntegerField(blank = True, null = True)
    yearly_income = models.CharField(max_length = 256, blank = True, null = True)
    monthly_income = models.CharField(max_length = 256, blank = True, null = True)
    weekly_income = models.CharField(max_length = 256, blank = True, null = True)
    tefap_eligible = models.CharField(max_length = 256, blank = True, null = True)
    agency_representative_signature = models.TextField(blank = True, null = True)
    
    def __str__(self):
        return f"{str(self.internal_ID).split("(")[0]} {self.date} ({self.id})"










