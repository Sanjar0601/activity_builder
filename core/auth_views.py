from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Teacher, Group, Assignment, Subject, TeacherGroup


def teacher_login(request):
    """Login view for teachers."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.email}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
    
    return render(request, 'core/login.html')


def teacher_register(request):
    """Registration view for teachers."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not email:
            messages.error(request, 'Email is required.')
        elif not password:
            messages.error(request, 'Password is required.')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match.')
        elif Teacher.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
        else:
            user = Teacher.objects.create_user(email=email, password=password)
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.email}!')
            return redirect('dashboard')
    
    return render(request, 'core/register.html')


@login_required
def dashboard(request):
    """Dashboard view showing teacher's groups and assignments."""
    teacher = request.user
    
    # Get teacher's subscribed groups via TeacherGroup model with prefetch
    my_groups = Group.objects.filter(
        teacher_groups__teacher=teacher
    ).prefetch_related('teacher_groups').distinct().order_by('name')
    
    # Get ALL available groups in the system
    all_groups = Group.objects.prefetch_related('teacher_groups').all().order_by('name')
    
    # Get IDs of groups the teacher is already subscribed to
    my_group_ids = set(my_groups.values_list('id', flat=True))
    
    # Get teacher's assignments (created by them or selected by them)
    my_assignments = Assignment.objects.filter(
        Q(created_by=teacher) | Q(selected_by=teacher)
    ).distinct().order_by('-created_at')
    
    context = {
        'teacher': teacher,
        'my_groups': my_groups,
        'all_groups': all_groups,
        'my_group_ids': my_group_ids,
        'my_assignments': my_assignments,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def public_library(request):
    """Public library view showing all assignments with subject filtering."""
    teacher = request.user
    assignments = Assignment.objects.all().order_by('-created_at')
    
    # Filter by subject if provided
    subject_id = request.GET.get('subject')
    if subject_id:
        assignments = assignments.filter(subject_id=subject_id)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query) | 
            Q(created_by__email__icontains=search_query)
        )
    
    # Get all subjects for filter dropdown
    subjects = Subject.objects.all().order_by('name')
    
    # Check which assignments are already selected by the teacher
    selected_assignment_ids = teacher.selected_assignments.values_list('id', flat=True)
    
    context = {
        'assignments': assignments,
        'subjects': subjects,
        'selected_subject_id': int(subject_id) if subject_id else None,
        'search_query': search_query or '',
        'selected_assignment_ids': set(selected_assignment_ids),
    }
    
    return render(request, 'core/library.html', context)


@login_required
def add_assignment_to_list(request, assignment_id):
    """Add an assignment to teacher's selected list."""
    try:
        assignment = Assignment.objects.get(id=assignment_id)
        teacher = request.user
        
        if teacher not in assignment.selected_by.all():
            assignment.selected_by.add(teacher)
            messages.success(request, f'"{assignment.title}" added to your list!')
        else:
            messages.info(request, f'"{assignment.title}" is already in your list.')
    except Assignment.DoesNotExist:
        messages.error(request, 'Assignment not found.')
    
    return redirect('library')


@login_required
def add_group_to_list(request, group_id):
    """Add a group to teacher's subscribed list via TeacherGroup."""
    try:
        group = Group.objects.get(id=group_id)
        teacher = request.user
        
        # Check if TeacherGroup relationship already exists
        teacher_group, created = TeacherGroup.objects.get_or_create(
            teacher=teacher,
            group=group
        )
        
        if created:
            messages.success(request, f'"{group.name}" added to your groups!')
        else:
            messages.info(request, f'"{group.name}" is already in your groups.')
    except Group.DoesNotExist:
        messages.error(request, 'Group not found.')
    
    return redirect('dashboard')
