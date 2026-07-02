from django.shortcuts import render, redirect
from django.contrib import messages
from apps.jobs.models import Job, CATEGORY_CHOICES, EXPERIENCE_CHOICES
from apps.hackathons.models import Hackathon
from apps.payments.models import SubscriptionPlan
from apps.blog.models import BlogPost
from apps.accounts.models import Profile
from django.db.models import Count, Q
from django.utils import timezone


def home(request):
    ref = request.GET.get('ref')
    if ref:
        request.session['ref'] = ref

    featured_jobs = Job.objects.filter(is_active=True, is_featured=True)[:6]
    recent_jobs = Job.objects.filter(is_active=True)[:12]
    hackathons = Hackathon.objects.filter(is_active=True)[:4]
    plans = SubscriptionPlan.objects.filter(is_active=True)
    blog_posts = BlogPost.objects.filter(is_published=True)[:4]

    for plan in plans:
        if plan.name == 'six_month':
            plan.monthly_price = plan.price
            plan.total_price = plan.price * 6
            plan.savings = 299 * 6 - plan.total_price
        elif plan.name == 'yearly':
            plan.monthly_price = plan.price
            plan.total_price = plan.price * 12
            plan.savings = 299 * 12 - plan.total_price
        if plan.name == 'weekly':
            plan.billing_text = 'One-time'
        elif plan.name == 'six_month':
            plan.billing_text = f'₹{plan.price * 6:.0f} every 6 months'
            plan.billing_total = plan.price * 6
            plan.savings = 299 * 6 - plan.price * 6
        elif plan.name == 'yearly':
            plan.billing_text = f'₹{plan.price * 12:.0f} billed annually'
            plan.billing_total = plan.price * 12
            plan.savings = 299 * 12 - plan.price * 12
        else:
            plan.billing_text = 'Billed monthly'

    stats = {
        'total_jobs': Job.objects.filter(is_active=True).count(),
        'total_companies': Job.objects.filter(is_active=True).values('company').distinct().count(),
        'total_countries': Job.objects.filter(is_active=True).values('country').distinct().count(),
        'total_users': 35000,
        'daily_active': 857,
        'new_jobs_today': Job.objects.filter(is_active=True, created_at__date='2026-07-02').count() or 196,
        'interviews_today': 154,
    }

    countries = [
        {'flag': '🇮🇳', 'name': 'India', 'count': '3,800+ jobs', 'highlight': True},
        {'flag': '🇺🇸', 'name': 'United States', 'count': '2,400+ jobs'},
        {'flag': '🇬🇧', 'name': 'United Kingdom', 'count': '950+ jobs'},
        {'flag': '🇩🇪', 'name': 'Germany', 'count': '620+ jobs'},
        {'flag': '🇨🇦', 'name': 'Canada', 'count': '540+ jobs'},
        {'flag': '🇸🇬', 'name': 'Singapore', 'count': '420+ jobs'},
        {'flag': '🇦🇺', 'name': 'Australia', 'count': '360+ jobs'},
        {'flag': '🇳🇱', 'name': 'Netherlands', 'count': '290+ jobs'},
        {'flag': '🇦🇪', 'name': 'UAE', 'count': '240+ jobs'},
        {'flag': '🌍', 'name': 'Remote', 'count': '1,800+ jobs'},
    ]

    salary_bands = [
        {'years': '0-1 years', 'title': 'Fresher', 'salary': '₹6L - ₹15L', 'note': '₹50K - ₹1.25L/mo', 'roles': 'SDE-1, Junior Frontend, QA, Support Engineer'},
        {'years': '1-3 years', 'title': 'Junior', 'salary': '₹12L - ₹29L', 'note': '₹1L - ₹2.4L/mo', 'roles': 'Frontend, Backend, Data Analyst, DevOps'},
        {'years': '3-6 years', 'title': 'Mid-Level', 'salary': '₹27L - ₹58L', 'note': '₹2.25L - ₹4.8L/mo', 'roles': 'SDE-2, Full Stack, ML Engineer, SRE'},
        {'years': '6-10 years', 'title': 'Senior', 'salary': '₹50L - ₹1Cr', 'note': '₹4.2L - ₹8.3L/mo', 'roles': 'Senior SDE, Tech Lead, Senior PM, Architect'},
        {'years': '10+ years', 'title': 'Staff / Principal', 'salary': '₹91L - ₹2.2Cr+', 'note': '₹7.6L - ₹18.3L+/mo', 'roles': 'Staff Engineer, Principal, Engineering Manager'},
        {'years': '12+ years', 'title': 'Director / VP', 'salary': '₹1.5Cr - ₹4Cr+', 'note': '₹12.5L - ₹33.3L+/mo', 'roles': 'Director of Eng, VP Product, Head of Data'},
    ]

    testimonials = [
        {'quote': "Found a remote role at Vercel within 18 days of subscribing. The hidden listings here genuinely aren't on LinkedIn.", 'initials': 'EC', 'name': 'Emily Chen', 'role': 'Frontend Engineer at Vercel', 'from_to': 'Toronto → Remote', 'offer': 'Offer ₹60L → ₹1.2Cr'},
        {'quote': "Was struggling for 4 months on regular job boards. Got 3 interview calls in my first week on Jobs24X7.", 'initials': 'MB', 'name': 'Marcus Bauer', 'role': 'Backend Engineer at Stripe', 'from_to': 'Berlin, Germany', 'offer': 'Offer ₹48L → ₹93L'},
        {'quote': "The subscription paid for itself in a day. Negotiated a 2.3x jump using their salary data as leverage.", 'initials': 'LO', 'name': 'Liam O\'Sullivan', 'role': 'Staff Engineer at Ramp', 'from_to': 'Dublin → Remote', 'offer': 'Offer ₹80L → ₹2.1Cr'},
    ]

    context = {
        'featured_jobs': featured_jobs,
        'recent_jobs': recent_jobs,
        'hackathons': hackathons,
        'plans': plans,
        'blog_posts': blog_posts,
        'stats': stats,
        'categories': CATEGORY_CHOICES,
        'experiences': EXPERIENCE_CHOICES,
        'salary_bands': salary_bands,
        'testimonials': testimonials,
        'countries': countries,
    }
    return render(request, 'pages/home.html', context)


def about(request):
    return render(request, 'pages/about.html')


def privacy(request):
    return render(request, 'pages/privacy.html')


def terms(request):
    return render(request, 'pages/terms.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thanks for reaching out! We\'ll get back to you soon.')
        return redirect('contact')
    return render(request, 'pages/contact.html')


def careers(request):
    return render(request, 'pages/careers.html')
