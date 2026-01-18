from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Teacher, Group, TeacherGroup, Assignment, Submission, Question, Choice, Subject


@admin.register(Teacher)
class TeacherAdmin(BaseUserAdmin):
    """Admin interface for Teacher model."""
    list_display = ['email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email']
    ordering = ['email']
    filter_horizontal = []  # Remove default groups and user_permissions fields
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for Subject model."""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin interface for Group model."""
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(TeacherGroup)
class TeacherGroupAdmin(admin.ModelAdmin):
    """Admin interface for TeacherGroup model."""
    list_display = ['teacher', 'group', 'subscribed_at']
    list_filter = ['subscribed_at', 'group']
    search_fields = ['teacher__email', 'group__name']
    ordering = ['-subscribed_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin interface for Assignment model."""
    list_display = ['title', 'uuid', 'created_by', 'subject', 'available_on', 'duration', 'created_at']
    list_filter = ['available_on', 'created_at', 'created_by', 'subject']
    search_fields = ['title', 'uuid']
    filter_horizontal = ['groups', 'selected_by']
    ordering = ['-created_at']
    readonly_fields = ['uuid', 'created_at', 'updated_at']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Submission model."""
    list_display = ['student_name', 'group', 'assignment', 'start_time', 'end_time', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'start_time', 'created_at', 'group', 'assignment']
    search_fields = ['student_name', 'assignment__title', 'group__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


class ChoiceInline(admin.TabularInline):
    """Inline admin for Choice model."""
    model = Choice
    extra = 2
    fields = ['text', 'is_correct', 'order']
    ordering = ['order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model."""
    list_display = ['assignment', 'order', 'text_preview', 'created_at']
    list_filter = ['assignment', 'created_at']
    search_fields = ['text', 'assignment__title']
    ordering = ['assignment', 'order']
    inlines = [ChoiceInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def text_preview(self, obj):
        """Return a preview of the question text."""
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Question Preview'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    """Admin interface for Choice model."""
    list_display = ['question', 'text_preview', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__assignment']
    search_fields = ['text', 'question__text']
    ordering = ['question', 'order']
    
    def text_preview(self, obj):
        """Return a preview of the choice text."""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Choice Preview'
