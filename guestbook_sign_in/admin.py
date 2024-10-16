from django.contrib import admin
from .models import Guest, SignIn, LinkedProxy, UnlinkedProxy

# Register your models here.

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'guest_ID']

@admin.register(SignIn)
class SignInAdmin(admin.ModelAdmin):
    search_fields = ['date']

@admin.register(LinkedProxy)
class BoundProxyAdmin(admin.ModelAdmin):
    search_fields = ['internal_id']

@admin.register(UnlinkedProxy)
class UnboundProxyAdmin(admin.ModelAdmin):
    search_fields = ['internal_id', 'first_name', 'last_name']




