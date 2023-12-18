from django.contrib import admin
from .models import Guest, SignIn

# Register your models here.

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'guest_ID']

@admin.register(SignIn)
class SignInAdmin(admin.ModelAdmin):
    search_fields = ['date']





