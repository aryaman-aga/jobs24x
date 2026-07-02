from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Hackathon, HackathonApplication, MODE_CHOICES, HACKATHON_CATEGORIES
from django.utils import timezone
from datetime import timedelta

MAX_FREE_APPLICATIONS = 10


def hackathon_list(request):
    mode = request.GET.get('mode', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    hackathons = Hackathon.objects.filter(is_active=True)

    if mode:
        hackathons = hackathons.filter(mode=mode)
    if category:
        hackathons = hackathons.filter(category=category)
    if status == 'upcoming':
        hackathons = hackathons.filter(start_date__gte=timezone.now().date())
    elif status == 'closing':
        hackathons = hackathons.filter(
            end_date__lte=timezone.now().date() + timedelta(days=7),
            end_date__gte=timezone.now().date()
        )

    applied_ids = []
    if request.user.is_authenticated:
        applied_ids = list(HackathonApplication.objects.filter(
            user=request.user
        ).values_list('hackathon_id', flat=True))

        remaining = MAX_FREE_APPLICATIONS - HackathonApplication.objects.filter(user=request.user).count()
    else:
        remaining = MAX_FREE_APPLICATIONS

    context = {
        'hackathons': hackathons,
        'modes': MODE_CHOICES,
        'categories': HACKATHON_CATEGORIES,
        'current_mode': mode,
        'current_category': category,
        'current_status': status,
        'applied_ids': applied_ids,
        'remaining_apps': remaining,
        'max_free_apps': MAX_FREE_APPLICATIONS,
    }
    return render(request, 'hackathons/hackathon_list.html', context)


@login_required
def apply_hackathon(request, pk):
    hackathon = get_object_or_404(Hackathon, pk=pk, is_active=True)

    app_count = HackathonApplication.objects.filter(user=request.user).count()
    is_subscribed = request.user.profile.is_subscribed
    already_applied = HackathonApplication.objects.filter(user=request.user, hackathon=hackathon).exists()

    if already_applied:
        messages.info(request, 'You already applied to this hackathon.')
        return redirect('hackathon_list')

    if not is_subscribed and app_count >= MAX_FREE_APPLICATIONS:
        messages.error(request, f'Free users can apply to at most {MAX_FREE_APPLICATIONS} hackathons. Subscribe for unlimited access.')
        return redirect('pricing')

    HackathonApplication.objects.create(user=request.user, hackathon=hackathon)
    messages.success(request, f'Applied to {hackathon.title}!')
    return redirect('hackathon_list')
