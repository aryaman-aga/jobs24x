from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from apps.jobs.models import SavedJob, Job
from apps.payments.models import Subscription


@login_required
def dashboard(request):
    saved_count = SavedJob.objects.filter(user=request.user).count()
    active_sub = Subscription.objects.filter(user=request.user, is_active=True).first()
    profile = request.user.profile

    cats = profile.preferred_categories or []
    exp = profile.preferred_experience or ''
    loc = profile.preferred_location or ''

    recommended_jobs = Job.objects.filter(is_active=True)
    if cats:
        recommended_jobs = recommended_jobs.filter(category__in=cats)
    if exp:
        recommended_jobs = recommended_jobs.filter(experience_level=exp)
    if loc:
        recommended_jobs = recommended_jobs.filter(
            models.Q(location__icontains=loc) | models.Q(country__icontains=loc)
        )
    recommended_jobs = recommended_jobs.distinct()[:6]

    context = {
        'saved_count': saved_count,
        'subscription': active_sub,
        'profile': profile,
        'recommended_jobs': recommended_jobs,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def update_profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.preferred_categories = request.POST.getlist('categories')
        profile.preferred_experience = request.POST.get('experience_level', '')
        profile.preferred_location = request.POST.get('preferred_location', '')
        profile.save()
        messages.success(request, 'Preferences saved!')
    return redirect('dashboard')


@login_required
def saved_jobs(request):
    saved = SavedJob.objects.filter(user=request.user).select_related('job')
    return render(request, 'accounts/saved_jobs.html', {'saved_jobs': saved})


@login_required
def subscription_status(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    return render(request, 'accounts/subscription_status.html', {'subscriptions': subscriptions})
