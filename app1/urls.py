from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('upload/', views.upload_document, name='upload_document'),
    path('summary/', views.summarization, name='summary'),
    path('export/<str:format>/', views.export_summary, name='export_summary'),
]
