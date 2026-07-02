from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings


def health(request):
    return JsonResponse({'status': 'ok', 'app': 'jobs24x'})


def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'core/signup.html')

        user = User.objects.create_user(username=email, email=email, password=password1)
        login(request, user)
        return redirect('/')

    return render(request, 'core/signup.html')
