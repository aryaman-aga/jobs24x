from django.shortcuts import render
from django.db.models import Q
from .models import Hackathon, MODE_CHOICES, HACKATHON_CATEGORIES


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
        hackathons = hackathons.filter(start_date__gte=__import__('django.utils.timezone').utils.timezone.now().date())
    elif status == 'closing':
        hackathons = hackathons.filter(end_date__lte=__import__('django.utils.timezone').utils.timezone.now().date() + __import__('datetime').timedelta(days=7), end_date__gte=__import__('django.utils.timezone').utils.timezone.now().date())

    context = {
        'hackathons': hackathons,
        'modes': MODE_CHOICES,
        'categories': HACKATHON_CATEGORIES,
        'current_mode': mode,
        'current_category': category,
        'current_status': status,
    }
    return render(request, 'hackathons/hackathon_list.html', context)
