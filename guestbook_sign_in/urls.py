from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('create_new_guest/<language>', views.create_new_guest, name = 'create_new_guest'),
    path('weekly_signatures/<language>/<guest_ID>', views.weekly_signatures, name = 'weekly_signatures'),
    path('submission_complete/<tefap_flag>/<guest_ID>', views.submission_complete, name = 'submission_complete'),
    path('sign_in', views.sign_in, name = 'sign_in'),
    path('sign_out', views.sign_out, name = 'sign_out'),
    path('generate_report', views.generate_report, name = 'generate_report'),
    path('generate_report/<file_type>', views.generate_report_file, name = 'generate_report_file'),
    path('generate_proxy_form/<guest_ID>', views.generate_proxy_form, name = 'generate_proxy_form'),
]

if settings.DEBUG == True:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

