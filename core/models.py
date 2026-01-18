from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from datetime import date
import uuid


class TeacherManager(BaseUserManager):
    """Manager for Teacher model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class Teacher(AbstractBaseUser):
    """Custom user model for Teachers."""
    email = models.EmailField(
        unique=True,
        verbose_name='Email Address'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Staff Status'
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name='Superuser Status'
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date Joined'
    )
    
    objects = TeacherManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
    
    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        return self.is_superuser


class Group(models.Model):
    """A shared registry of groups."""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Group Name'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject model for categorizing assignments."""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Subject Name'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TeacherGroup(models.Model):
    """Relationship model for teachers subscribing to groups."""
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teacher_groups',
        verbose_name='Teacher'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='teacher_groups',
        verbose_name='Group'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Subscribed At'
    )
    
    class Meta:
        verbose_name = 'Teacher Group Subscription'
        verbose_name_plural = 'Teacher Group Subscriptions'
        unique_together = ['teacher', 'group']
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f'{self.teacher.email} - {self.group.name}'


class Assignment(models.Model):
    """Assignment model for tests/activities."""
    title = models.CharField(
        max_length=255,
        verbose_name='Title'
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UUID'
    )
    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Created By'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        verbose_name='Subject'
    )
    available_on = models.DateField(
        verbose_name='Available On'
    )
    duration = models.PositiveIntegerField(
        help_text='Duration in minutes',
        verbose_name='Duration (Minutes)'
    )
    groups = models.ManyToManyField(
        Group,
        related_name='assignments',
        verbose_name='Groups'
    )
    selected_by = models.ManyToManyField(
        Teacher,
        related_name='selected_assignments',
        blank=True,
        verbose_name='Selected By'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-created_at']
    
    @property
    def is_available_today(self):
        """Check if assignment is available today."""
        return self.available_on == date.today()
    
    def __str__(self):
        return self.title


class Submission(models.Model):
    """Submission model to track student test submissions."""
    student_name = models.CharField(
        max_length=255,
        verbose_name='Student Name'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Group'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Assignment'
    )
    start_time = models.DateTimeField(
        verbose_name='Start Time'
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='End Time'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Is Completed'
    )
    security_logs = models.JSONField(
        default=list,
        blank=True,
        help_text='Tracks tab switches or full-screen exits',
        verbose_name='Security Logs'
    )
    tab_lock_violations = models.PositiveIntegerField(
        default=0,
        verbose_name='Tab Lock Violations'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.student_name} - {self.assignment.title}'


class Question(models.Model):
    """Question model for assignments."""
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Assignment'
    )
    text = models.TextField(
        verbose_name='Question Text'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['assignment', 'order', 'id']
    
    def __str__(self):
        return f'{self.assignment.title} - Q{self.order}: {self.text[:50]}'


class Choice(models.Model):
    """Choice model for question answers."""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='Question'
    )
    text = models.CharField(
        max_length=500,
        verbose_name='Choice Text'
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Is Correct'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Order'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    class Meta:
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'
        ordering = ['question', 'order', 'id']
    
    def __str__(self):
        return f'{self.question.assignment.title} - {self.text[:50]}'
