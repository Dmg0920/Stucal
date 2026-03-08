from django.urls import path
from . import views

urlpatterns = [
    # Landing / Auth
    path('', views.landing, name='landing'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('teacher/pending/', views.teacher_pending, name='teacher_pending'),

    # Teacher - student management
    path('teacher/students/', views.student_list, name='student_list'),
    path('teacher/students/new/', views.student_add, name='student_add'),
    path('teacher/students/<int:pk>/select/', views.student_select, name='student_select'),

    # Student auth
    path('student/join/', views.student_join, name='student_join'),
    path('student/setname/', views.student_setname, name='student_setname'),
    path('student/logout/', views.student_logout, name='student_logout'),

    # Main app (teacher + student)
    path('home/', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('session/new/', views.session_new, name='session_new'),
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/new/', views.material_new, name='material_new'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('history/', views.history, name='history'),

    # 舊路由相容
    path('login/', views.login_view, name='login'),
]
