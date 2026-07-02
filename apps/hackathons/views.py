from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Hackathon, HackathonVisit, MODE_CHOICES, HACKATHON_CATEGORIES
from django.utils import timezone
from datetime import timedelta

MAX_FREE_VISITS = 10


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

    visited_ids = []
    remaining_visits = MAX_FREE_VISITS
    is_subscribed = False

    if request.user.is_authenticated:
        is_subscribed = request.user.profile.is_subscribed
        visited_ids = list(HackathonVisit.objects.filter(
            user=request.user
        ).values_list('hackathon_id', flat=True))

        visit_count = HackathonVisit.objects.filter(user=request.user).count()
        remaining_visits = max(0, MAX_FREE_VISITS - visit_count)

    context = {
        'hackathons': hackathons,
        'modes': MODE_CHOICES,
        'categories': HACKATHON_CATEGORIES,
        'current_mode': mode,
        'current_category': category,
        'current_status': status,
        'visited_ids': visited_ids,
        'remaining_visits': remaining_visits,
        'max_free_visits': MAX_FREE_VISITS,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'hackathons/hackathon_list.html', context)


@login_required
def visit_hackathon(request, pk):
    hackathon = get_object_or_404(Hackathon, pk=pk, is_active=True)

    is_subscribed = request.user.profile.is_subscribed
    already_visited = HackathonVisit.objects.filter(user=request.user, hackathon=hackathon).exists()

    if not already_visited:
        visit_count = HackathonVisit.objects.filter(user=request.user).count()
        if not is_subscribed and visit_count >= MAX_FREE_VISITS:
            messages.error(
                request,
                f'Free users can visit up to {MAX_FREE_VISITS} hackathon pages. '
                f'Subscribe for unlimited access.'
            )
            return redirect('pricing')

        HackathonVisit.objects.create(user=request.user, hackathon=hackathon)

    return redirect(hackathon.apply_url)
