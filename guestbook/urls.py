"""
URL configuration for guestbook project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
import allauth.account.views as allauthbase
import allauth.mfa.base.views as mfa
import allauth.mfa.totp.views as totp
import allauth.mfa.recovery_codes.views as codes

urlpatterns = [
    path("admin/", admin.site.urls),
    path("guestbook_sign_in/", include("guestbook_sign_in.urls")),
    path('', RedirectView.as_view(url='guestbook_sign_in/', permanent=True)), # Redirect root URL to sign-in app
    
    # Allauth
   
    # Do not enable this in production - it may allow password resets by email.
    # path('accounts/', include('allauth.urls')),
    
    path('accounts/login/', allauthbase.LoginView.as_view(), name = 'account_login'), 
    path('accounts/logout/', allauthbase.LogoutView.as_view(), name = 'account_logout'),

    # LEAVE SIGNUPS DISABLED! They allow an arbitrary user to register for an account and access the database.
    # path('accounts/signup/', allauthbase.SignupView.as_view(), name = 'account_signup'), 
    
    # Duplicating the login page is an extremely hacky workaround so that AllAuth doesn't throw a fit about accout_signup not existing.
    path('accounts/login/', allauthbase.LoginView.as_view(), name = 'account_signup'),

    path('accounts/reauthenticate/', allauthbase.ReauthenticateView.as_view(), name="account_reauthenticate"),
    path('accounts/2fa/', mfa.IndexView.as_view(), name = 'mfa_index'),
    path('accounts/2fa/authenticate/', mfa.AuthenticateView.as_view(), name='mfa_authenticate'),
    path('accounts/2fa/reauthenticate/', mfa.ReauthenticateView.as_view(), name="mfa_reauthenticate"),
    path('accounts/2fa/totp/activate/', totp.ActivateTOTPView.as_view(), name = 'mfa_activate_totp'),
    path('accounts/2fa/totp/deactivate/', totp.DeactivateTOTPView.as_view(), name = 'mfa_deactivate_totp'),
    path('accounts/2fa/recovery-codes/', codes.ViewRecoveryCodesView.as_view(), name="mfa_view_recovery_codes"),
    path('accounts/2fa/recovery-codes/download/', codes.DownloadRecoveryCodesView.as_view(), name="mfa_download_recovery_codes"),
    path('accounts/2fa/recovery-codes/generate/', codes.GenerateRecoveryCodesView.as_view(), name="mfa_generate_recovery_codes"),
    
    # No longer needed because Allauth is handling logins
    # path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name = 'login'),
]


### DELETE BEFORE DEPLOYMENT! NOT SAFE FOR PRODUCTION!!! ###
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
### END DELETE ###

