"""
URL configuration for csr_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from questionnaire import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('set-language/<str:language>/', views.set_language, name='set_language'),
    path('section-a/', views.section_a, name='section_a'),
    path('download-options/<uuid:application_id>/', views.download_options, name='download_options'),
    path('section-b/<uuid:application_id>/', views.section_b, name='section_b'),
    path('download/full/<uuid:application_id>/', views.download_full_pdf, name='download_full'),
    path('download/section/<uuid:application_id>/<str:section_key>/',views.download_section_pdf, name='download_section'),
    path('final-page/<uuid:application_id>/', views.final_page, name='final_page'),
    path('download-trigger/<uuid:application_id>/<str:download_type>/', views.download_trigger, name='download_trigger'),
    path('download-trigger/<uuid:application_id>/<str:download_type>/<str:section_key>/', views.download_trigger, name='download_trigger_section'),
    path('serve-pdf/<uuid:application_id>/<str:pdf_type>/', views.serve_pdf, name='serve_pdf'),
    path('serve-pdf/<uuid:application_id>/<str:pdf_type>/<str:section_key>/', views.serve_pdf, name='serve_pdf_section'),
    path('upload/', views.upload_start, name='upload_start'),
    path('upload/<uuid:application_id>/', views.upload_pdf, name='upload_pdf'),
    path('upload/success/<uuid:application_id>/', views.upload_success, name='upload_success'),
    path('verify/<uuid:verification_code>/', views.verify_response, name='verify_response'),
    path('verify-mobile/', views.verify_mobile, name='verify_mobile'),
]
