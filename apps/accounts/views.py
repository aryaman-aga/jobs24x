from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.jobs.models import SavedJob
from apps.payments.models import Subscription


@login_required
def dashboard(request):
    saved_count = SavedJob.objects.filter(user=request.user).count()
    active_sub = Subscription.objects.filter(user=request.user, is_active=True).first()
    context = {
        'saved_count': saved_count,
        'subscription': active_sub,
        'profile': request.user.profile,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def saved_jobs(request):
    saved = SavedJob.objects.filter(user=request.user).select_related('job')
    return render(request, 'accounts/saved_jobs.html', {'saved_jobs': saved})


@login_required
def subscription_status(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    return render(request, 'accounts/subscription_status.html', {'subscriptions': subscriptions})
