from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('create_new_guest/<language>', views.create_new_guest, name = 'create_new_guest'),
    path('lookup_guest/<internal_ID>', views.lookup_guest, name = 'lookup_guest'),
    path('linked_proxy_form/<language>/<internal_ID>', views.linked_proxy_form, name = 'linked_proxy_form'),
    path('new_guest_created/<internal_ID>', views.new_guest_created, name = 'new_guest_created'),
    path('sign_in', views.sign_in, name = 'sign_in'),
    path('weekly_signatures/<language>/<internal_ID>', views.weekly_signatures, name = 'weekly_signatures'),
    path('submission_complete/<tefap_flag>/<internal_ID>', views.submission_complete, name = 'submission_complete'),
    path('sign_out', views.sign_out, name = 'sign_out'),
    path('unlinked_proxy_form', views.unlinked_proxy_form, name = 'unlinked_proxy'),
    path('unlinked_proxy_successful', views.unlinked_proxy_successful, name = 'unlinked_proxy_successful'),
    path('generate_report', views.generate_report, name = 'generate_report'),
    path('generate_report/database', views.generate_report_database, name = 'generate_report_database'),
    path('generate_report/pdf', views.generate_report_pdf, name = 'generate_report_pdf'),
    path('generate_report/alpha_list', views.generate_alpha_list, name = 'generate_alpha_list'),
    path('generate_report/attendance_report', views.generate_attendance_report, name = 'generate_attendance_report'),
]

if settings.DEBUG == True:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

