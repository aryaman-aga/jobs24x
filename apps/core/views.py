from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from io import StringIO
from django.core.management import call_command
from apps.jobs.models import CATEGORY_CHOICES, EXPERIENCE_CHOICES


def health(request):
    return JsonResponse({'status': 'ok', 'app': 'jobs24X7'})


def locations_api(request):
    from apps.jobs.models import Job
    locs = Job.objects.filter(is_active=True).values_list('location', flat=True).distinct()
    locations = sorted(set(l for l in locs if l))
    defaults = ['Remote', 'Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad',
                'Chennai', 'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur']
    merged = list(dict.fromkeys(defaults + locations))
    return JsonResponse({'locations': merged})


@csrf_exempt
def scrape_now(request):
    if request.method == 'POST':
        token = request.POST.get('token', '')
    else:
        token = request.GET.get('token', '')

    if token != settings.SCRAPER_SECRET_TOKEN:
        return JsonResponse({'error': 'invalid token'}, status=403)

    out = StringIO()
    jobs_created = 0
    hackathons_created = 0
    errors = []

    try:
        call_command('run_scraper', stdout=out, stderr=out)
    except Exception as e:
        errors.append(f'run_scraper: {e}')

    try:
        call_command('scrape_hackathons', stdout=out, stderr=out)
    except Exception as e:
        errors.append(f'scrape_hackathons: {e}')

    try:
        call_command('daily_refresh', stdout=out, stderr=out)
    except Exception as e:
        errors.append(f'daily_refresh: {e}')

    import re
    output = out.getvalue()
    m = re.search(r'created (\d+) new jobs', output)
    if m:
        jobs_created = int(m.group(1))
    m = re.search(r'created (\d+) new hackathons', output)
    if m:
        hackathons_created = int(m.group(1))

    return JsonResponse({
        'status': 'ok' if not errors else 'partial',
        'jobs_created': jobs_created,
        'hackathons_created': hackathons_created,
        'errors': errors,
        'output': output[-2000:] if output else '',
    })


def logout_view(request):
    logout(request)
    return redirect('signed_out')


def signed_out(request):
    return render(request, 'core/logout.html')


def signup(request):
    ctx = {'categories': CATEGORY_CHOICES, 'experiences': EXPERIENCE_CHOICES}

    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not request.POST.get('accept_terms'):
            messages.error(request, 'You must accept the Terms & Conditions to create an account.')
            return render(request, 'core/signup.html', ctx)

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/signup.html', ctx)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'core/signup.html', ctx)

        user = User.objects.create_user(username=email, email=email, password=password1)

        preferred_categories = request.POST.getlist('categories')
        preferred_experience = request.POST.get('experience_level', '')
        preferred_location = request.POST.get('preferred_location', '')
        profile = user.profile
        profile.preferred_categories = preferred_categories
        profile.preferred_experience = preferred_experience
        profile.preferred_location = preferred_location
        profile.save()

        login(request, user)
        return redirect('/')

    return render(request, 'core/signup.html', ctx)
