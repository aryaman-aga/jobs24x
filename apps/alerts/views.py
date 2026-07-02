from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import JobAlert
from apps.jobs.models import CATEGORY_CHOICES, EXPERIENCE_CHOICES


@login_required
def alert_list(request):
    alerts = JobAlert.objects.filter(user=request.user)
    return render(request, 'alerts/alert_list.html', {'alerts': alerts})


@login_required
def create_alert(request):
    if request.method == 'POST':
        alert = JobAlert.objects.create(
            user=request.user,
            role_keywords=request.POST.get('role_keywords', ''),
            experience_levels=request.POST.getlist('experience_levels'),
            categories=request.POST.getlist('categories'),
            locations=request.POST.getlist('locations', []),
            remote_only=request.POST.get('remote_only') == 'on',
            min_salary=request.POST.get('min_salary') or None,
        )
        messages.success(request, 'Job alert created successfully!')
        return redirect('alert_list')
    context = {
        'categories': CATEGORY_CHOICES,
        'experiences': EXPERIENCE_CHOICES,
    }
    return render(request, 'alerts/create_alert.html', context)


@login_required
def delete_alert(request, pk):
    alert = get_object_or_404(JobAlert, pk=pk, user=request.user)
    alert.delete()
    messages.success(request, 'Alert deleted.')
    return redirect('alert_list')


def unsubscribe_alert(request, token):
    try:
        alert = JobAlert.objects.get(id=int(token))
        alert.is_active = False
        alert.save()
        return HttpResponse('You have been unsubscribed from job alerts.')
    except (JobAlert.DoesNotExist, ValueError):
        return HttpResponse('Invalid unsubscribe link.')
