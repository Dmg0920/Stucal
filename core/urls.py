from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('session/new/', views.session_new, name='session_new'),
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/new/', views.material_new, name='material_new'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('history/', views.history, name='history'),
    path('login/', views.login_view, name='login'),
]
