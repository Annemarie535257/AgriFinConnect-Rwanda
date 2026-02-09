from django.urls import path
from . import views

urlpatterns = [
    # Auth (admin is backend-created; login only for admin)
    path('auth/register/', views.auth_register),
    path('auth/login/', views.auth_login),
    # ML model APIs
    path('eligibility/', views.eligibility),
    path('risk/', views.risk),
    path('recommend-amount/', views.recommend_amount),
    path('chat/', views.chat),
]
