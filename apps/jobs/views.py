from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Job, SavedJob, CATEGORY_CHOICES, EXPERIENCE_CHOICES


def job_list(request):
    category = request.GET.get('category', '')
    experience = request.GET.get('experience', '')
    search = request.GET.get('q', '')
    remote = request.GET.get('remote', '')

    jobs = Job.objects.filter(is_active=True)

    if category:
        jobs = jobs.filter(category=category)
    if experience:
        jobs = jobs.filter(experience_level=experience)
    if remote == 'true':
        jobs = jobs.filter(remote=True)
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(company__icontains=search) |
            Q(description__icontains=search)
        )

    saved_job_ids = []
    if request.user.is_authenticated:
        saved_job_ids = list(SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True))

    context = {
        'jobs': jobs,
        'categories': CATEGORY_CHOICES,
        'experiences': EXPERIENCE_CHOICES,
        'current_category': category,
        'current_experience': experience,
        'current_search': search,
        'current_remote': remote,
        'saved_job_ids': saved_job_ids,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    can_view_details = False
    if request.user.is_authenticated:
        profile = request.user.profile
        can_view_details = profile.is_subscribed and (
            not profile.subscription_end or profile.subscription_end > timezone.now()
        )

    context = {
        'job': job,
        'is_saved': is_saved,
        'can_view_details': can_view_details,
    }

    if request.GET.get('modal'):
        return render(request, 'jobs/_job_modal_content.html', context)
    return render(request, 'jobs/job_detail.html', context)


@login_required
def save_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    SavedJob.objects.get_or_create(user=request.user, job=job)
    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': True})
    return redirect(request.META.get('HTTP_REFERER', 'job_list'))


@login_required
def unsave_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    SavedJob.objects.filter(user=request.user, job=job).delete()
    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': False})
    return redirect(request.META.get('HTTP_REFERER', 'job_list'))
