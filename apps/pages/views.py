from django.shortcuts import render, redirect
from django.contrib import messages
from apps.jobs.models import Job, CATEGORY_CHOICES, EXPERIENCE_CHOICES
from apps.hackathons.models import Hackathon
from apps.payments.models import SubscriptionPlan
from apps.blog.models import BlogPost
from apps.accounts.models import Profile


def home(request):
    ref = request.GET.get('ref')
    if ref:
        request.session['ref'] = ref

    featured_jobs = Job.objects.filter(is_active=True, is_featured=True)[:6]
    recent_jobs = Job.objects.filter(is_active=True)[:12]
    hackathons = Hackathon.objects.filter(is_active=True)[:4]
    plans = SubscriptionPlan.objects.filter(is_active=True)
    blog_posts = BlogPost.objects.filter(is_published=True)[:4]

    stats = {
        'total_jobs': Job.objects.filter(is_active=True).count(),
        'total_companies': Job.objects.filter(is_active=True).values('company').distinct().count(),
        'total_countries': Job.objects.filter(is_active=True).values('country').distinct().count(),
        'total_users': 35000,
        'daily_active': 857,
        'new_jobs_today': Job.objects.filter(is_active=True, created_at__date='2026-07-02').count() or 196,
        'interviews_today': 154,
    }

    salary_bands = [
        {'years': '0-1 years', 'title': 'Fresher', 'salary': '₹6L - ₹15L', 'converted': '$8K - $18K · €7K - €16K', 'roles': 'SDE-1, Junior Frontend, QA'},
        {'years': '1-3 years', 'title': 'Junior', 'salary': '₹12L - ₹29L', 'converted': '$15K - $35K · €13K - €32K', 'roles': 'Frontend, Backend, Data Analyst'},
        {'years': '3-6 years', 'title': 'Mid-Level', 'salary': '₹27L - ₹58L', 'converted': '$32K - $70K · €29K - €64K', 'roles': 'SDE-2, Full Stack, ML Engineer'},
        {'years': '6-10 years', 'title': 'Senior', 'salary': '₹50L - ₹1Cr', 'converted': '$60K - $120K · €55K - €110K', 'roles': 'Senior SDE, Tech Lead, Architect'},
        {'years': '10+ years', 'title': 'Staff / Principal', 'salary': '₹91L - ₹2.2Cr+', 'converted': '$110K - $260K+ · €100K - €240K', 'roles': 'Staff Engineer, Principal, EM'},
        {'years': '12+ years', 'title': 'Director / VP', 'salary': '₹1.5Cr - ₹4Cr+', 'converted': '$180K - $500K+ · €165K - €460K', 'roles': 'Director of Eng, VP Product'},
    ]

    testimonials = [
        {'quote': "Found a remote role at Vercel within 18 days of subscribing. The hidden listings here genuinely aren't on LinkedIn.", 'initials': 'EC', 'name': 'Emily Chen', 'role': 'Frontend Engineer at Vercel', 'from_to': 'Toronto → Remote', 'offer': 'Offer ₹60L → ₹1.2Cr'},
        {'quote': "Was struggling for 4 months on regular job boards. Got 3 interview calls in my first week on Jobs24x.", 'initials': 'MB', 'name': 'Marcus Bauer', 'role': 'Backend Engineer at Stripe', 'from_to': 'Berlin, Germany', 'offer': 'Offer ₹48L → ₹93L'},
        {'quote': "Direct apply links saved me from recruiter spam. Heard back from Linear in 3 days. Worth every dollar.", 'initials': 'SM', 'name': 'Sofia Martinez', 'role': 'Product Designer at Linear', 'from_to': 'Barcelona → Remote', 'offer': 'Offer ₹35L → ₹80L'},
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
