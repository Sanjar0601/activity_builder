"""
URL configuration for activity_builder project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from ninja import NinjaAPI

from django.shortcuts import redirect
from core.api import router as core_router
from core.views import student_entry_view, quiz_entry_view, quiz_questions, submit_quiz
from core.auth_views import teacher_login, teacher_register, dashboard, public_library, add_assignment_to_list, add_group_to_list


def home_redirect(request):
    """Redirect to dashboard if authenticated, otherwise to login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

api = NinjaAPI()

api.add_router('/core', core_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    
    # Authentication URLs (public)
    path('login/', teacher_login, name='login'),
    path('register/', teacher_register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Teacher Dashboard URLs (require login)
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/add-group/<int:group_id>/', add_group_to_list, name='add_group'),
    path('library/', public_library, name='library'),
    path('library/add/<int:assignment_id>/', add_assignment_to_list, name='add_assignment'),
    
    # Student Entry URLs (public, no login required)
    path('test/<uuid:assignment_uuid>/', student_entry_view, name='student_entry'),
    path('quiz/<uuid:assignment_uuid>/entry/', quiz_entry_view, name='quiz_entry'),
    path('quiz/<uuid:assignment_uuid>/questions/', quiz_questions, name='quiz_questions'),
    path('quiz/<uuid:assignment_uuid>/submit/', submit_quiz, name='submit_quiz'),
    
    # Root redirect
    path('', home_redirect, name='home'),
]
