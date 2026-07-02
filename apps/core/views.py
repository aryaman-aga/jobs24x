from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from apps.jobs.models import CATEGORY_CHOICES, EXPERIENCE_CHOICES


def health(request):
    return JsonResponse({'status': 'ok', 'app': 'jobs24X7'})


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
