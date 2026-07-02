from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Job, SavedJob, CATEGORY_CHOICES, EXPERIENCE_CHOICES
from .dto import JobTranslator, JobQueryHelper


def job_list(request):
    category = request.GET.get('category', '')
    experience = request.GET.get('experience', '')
    search = request.GET.get('q', '')
    remote = request.GET.get('remote', '')
    location = request.GET.get('location', '')

    qs = JobQueryHelper.base_query()
    qs = JobQueryHelper.apply_filters(qs, category, experience, search, remote, location)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    user = request.user
    subscribed = JobTranslator.get_subscribed(user)
    free_preview_ids = JobTranslator.get_free_preview_ids(
        page_obj.object_list if page_obj.object_list else Job.objects.filter(is_active=True)
    )
    saved_ids = JobTranslator.get_saved_ids(user, [j.pk for j in page_obj.object_list])

    context = {
        'jobs': page_obj,
        'page_obj': page_obj,
        'categories': CATEGORY_CHOICES,
        'experiences': EXPERIENCE_CHOICES,
        'current_category': category,
        'current_experience': experience,
        'current_search': search,
        'current_remote': remote,
        'current_location': location,
        'saved_job_ids': list(saved_ids),
        'free_preview_ids': list(free_preview_ids),
        'is_subscribed': subscribed,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    user = request.user
    subscribed = JobTranslator.get_subscribed(user)

    free_preview_ids = JobTranslator.get_free_preview_ids(
        Job.objects.filter(is_active=True)
    )
    is_free_preview = job.pk in free_preview_ids
    can_view_details = is_free_preview or subscribed

    is_saved = False
    if user.is_authenticated:
        is_saved = job.pk in JobTranslator.get_saved_ids(user, [job.pk])

    context = {
        'job': job,
        'is_saved': is_saved,
        'is_free_preview': is_free_preview,
        'can_view_details': can_view_details,
        'is_subscribed': subscribed,
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
