from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, Http404
from datetime import date, timedelta
from .models import Assignment, Submission, Question, Choice


def student_entry_view(request, assignment_uuid):
    """
    View to render the student entry page.
    Fetches assignment by UUID and checks availability.
    """
    try:
        assignment = get_object_or_404(Assignment, uuid=assignment_uuid)
    except Exception:
        return render(request, 'core/error.html', {
            'error_message': 'Assignment not found'
        }, status=404)
    
    # Check if available_date is today
    today = date.today()
    is_available = assignment.available_on == today
    
    # Get groups linked to this assignment
    groups = assignment.groups.all().order_by('name')
    
    context = {
        'assignment': assignment,
        'groups': groups,
        'is_available': is_available,
        'assignment_uuid': assignment_uuid,
    }
    
    return render(request, 'core/student_entry.html', context)


def quiz_entry_view(request, assignment_uuid):
    """
    View to render the quiz entry page.
    Fetches assignment by UUID and checks availability.
    """
    assignment = get_object_or_404(Assignment, uuid=assignment_uuid)
    
    # Check if assignment is available today using the property
    is_available = assignment.is_available_today
    
    # Get ALLOWED groups linked to this assignment
    groups = assignment.groups.all().order_by('name')
    
    context = {
        'assignment': assignment,
        'groups': groups,
        'is_available': is_available,
        'assignment_uuid': str(assignment_uuid),
    }
    
    return render(request, 'core/quiz_entry.html', context)


def quiz_questions(request, assignment_uuid):
    """
    View to render the quiz questions page.
    Checks session for submission_id and displays questions.
    """
    assignment = get_object_or_404(Assignment, uuid=assignment_uuid)
    
    # Check if student has a valid session (submission_id)
    submission_id = request.session.get('submission_id')
    if not submission_id:
        return render(request, 'core/error.html', {
            'error_message': 'No active quiz session found. Please start the quiz from the entry page.'
        }, status=403)
    
    try:
        submission = Submission.objects.get(id=submission_id, assignment=assignment)
    except Submission.DoesNotExist:
        return render(request, 'core/error.html', {
            'error_message': 'Invalid quiz session. Please start the quiz again.'
        }, status=403)
    
    # Check if quiz is already completed
    if submission.is_completed:
        return render(request, 'core/error.html', {
            'error_message': 'This quiz has already been completed.'
        }, status=403)
    
    # Fetch questions and choices for this assignment
    questions = Question.objects.filter(assignment=assignment).order_by('order', 'id').prefetch_related('choices')
    
    # Calculate time remaining
    duration_minutes = assignment.duration
    elapsed_time = timezone.now() - submission.start_time
    elapsed_minutes = elapsed_time.total_seconds() / 60
    remaining_minutes = max(0, duration_minutes - elapsed_minutes)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'questions': questions,
        'duration_minutes': duration_minutes,
        'remaining_minutes': int(remaining_minutes),
    }
    
    return render(request, 'core/quiz_questions.html', context)
