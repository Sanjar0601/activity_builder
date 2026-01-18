from ninja import Router
from ninja import Schema
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date
from django.http import Http404

from .models import Assignment, Group, Submission

router = Router()


class GroupSchema(Schema):
    """Schema for Group response."""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class AssignmentGroupsResponse(Schema):
    """Response schema for assignment groups."""
    assignment_title: str
    groups: List[GroupSchema]
    is_available: bool
    message: Optional[str] = None


@router.get('/assignment/{assignment_uuid}', response=AssignmentGroupsResponse)
def get_assignment_groups(request, assignment_uuid: str):
    """
    Fetch assignment by UUID and return linked groups.
    Checks if assignment is available today.
    """
    assignment = get_object_or_404(Assignment, uuid=assignment_uuid)
    
    # Check if available_date is today
    today = date.today()
    is_available = assignment.available_on == today
    
    # Get groups linked to this assignment
    groups = assignment.groups.all()
    groups_data = [GroupSchema(id=g.id, name=g.name) for g in groups]
    
    message = None
    if not is_available:
        message = f"Assignment is available on {assignment.available_on}, not today."
    
    return AssignmentGroupsResponse(
        assignment_title=assignment.title,
        groups=groups_data,
        is_available=is_available,
        message=message
    )


class QuizEntryResponse(Schema):
    """Response schema for quiz entry."""
    assignment_title: str
    duration: int
    groups: List[GroupSchema]
    is_available: bool
    message: Optional[str] = None


class QuizStartRequest(Schema):
    """Request schema for starting quiz."""
    student_name: str
    group_id: int


class QuizStartResponse(Schema):
    """Response schema for quiz start."""
    submission_id: int
    message: str


@router.get('/quiz/entry/{assignment_uuid}', response=QuizEntryResponse)
def get_quiz_entry(request, assignment_uuid: str):
    """
    GET endpoint for quiz entry.
    Returns Assignment title, duration, and list of allowed Groups.
    """
    try:
        assignment = Assignment.objects.get(uuid=assignment_uuid)
    except Assignment.DoesNotExist:
        raise Http404("Assignment not found")
    
    # Get groups linked to this assignment
    groups = assignment.groups.all().order_by('name')
    groups_data = [GroupSchema(id=g.id, name=g.name) for g in groups]
    
    message = None
    if not assignment.is_available_today:
        message = f"Assignment is available on {assignment.available_on}, not today."
    
    return QuizEntryResponse(
        assignment_title=assignment.title,
        duration=assignment.duration,
        groups=groups_data,
        is_available=assignment.is_available_today,
        message=message
    )


@router.post('/quiz/start/{assignment_uuid}', response=QuizStartResponse)
def start_quiz(request, assignment_uuid: str, data: QuizStartRequest):
    """
    POST endpoint to start quiz.
    Creates a Submission record and stores submission_id in session.
    """
    try:
        assignment = Assignment.objects.get(uuid=assignment_uuid)
    except Assignment.DoesNotExist:
        raise Http404("Assignment not found")
    
    # Check if assignment is available today
    if not assignment.is_available_today:
        return QuizStartResponse(
            submission_id=0,
            message=f"Assignment is not available today. It will be available on {assignment.available_on}."
        )
    
    # Verify group is allowed for this assignment
    try:
        group = Group.objects.get(id=data.group_id)
    except Group.DoesNotExist:
        return QuizStartResponse(
            submission_id=0,
            message="Invalid group selected."
        )
    
    if group not in assignment.groups.all():
        return QuizStartResponse(
            submission_id=0,
            message="Selected group is not allowed for this assignment."
        )
    
    # Create Submission record
    submission = Submission.objects.create(
        student_name=data.student_name,
        group=group,
        assignment=assignment,
        start_time=timezone.now()
    )
    
    # Store submission_id in session
    request.session['submission_id'] = submission.id
    request.session['assignment_uuid'] = str(assignment.uuid)
    request.session.save()
    
    return QuizStartResponse(
        submission_id=submission.id,
        message="Quiz started successfully."
    )


class ViolationResponse(Schema):
    """Response schema for violation logging."""
    success: bool
    message: str
    violations: int


@router.post('/quiz/violation/{submission_id}', response=ViolationResponse)
def log_violation(request, submission_id: int):
    """
    POST endpoint to log tab switch/fullscreen exit violations.
    Increments tab_lock_violations in Submission model.
    """
    session_submission_id = request.session.get('submission_id')
    if session_submission_id:
        submission_id = session_submission_id

    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return ViolationResponse(
            success=False,
            message="Submission not found.",
            violations=0
        )
    
    # Increment violation count
    submission.tab_lock_violations += 1
    submission.save(update_fields=['tab_lock_violations'])
    
    # Also log to security_logs JSON field
    if not submission.security_logs:
        submission.security_logs = []
    
    submission.security_logs.append({
        'timestamp': timezone.now().isoformat(),
        'type': 'tab_switch_or_blur',
        'violation_count': submission.tab_lock_violations
    })
    submission.save(update_fields=['security_logs', 'tab_lock_violations'])
    
    return ViolationResponse(
        success=True,
        message="Violation logged.",
        violations=submission.tab_lock_violations
    )
