import time
import random
import re
import logging
from datetime import timedelta

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.jobs.models import Job

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    'engineering': ['software engineer', 'backend', 'frontend', 'full stack', 'devops', 'sre',
                    'android', 'ios', 'data engineer', 'platform engineer', 'infrastructure',
                    'security engineer', 'site reliability', 'systems engineer', 'cloud engineer'],
    'data_ai': ['data scientist', 'machine learning', 'ml engineer', 'data analyst', 'ai engineer',
                'analytics engineer', 'research scientist', 'nlp engineer', 'computer vision'],
    'design': ['product designer', 'ux designer', 'ui designer', 'design engineer', 'brand designer',
               'graphic designer', 'visual designer', 'interaction designer'],
    'product': ['product manager', 'product owner', 'technical pm', 'product analyst',
                'associate product manager', 'product lead'],
    'marketing': ['marketing manager', 'content strategist', 'growth marketer', 'seo specialist',
                  'brand manager', 'digital marketing', 'social media manager'],
    'sales': ['account executive', 'sales engineer', 'customer success', 'revenue operations',
              'business development', 'sales manager', 'account manager'],
    'operations': ['operations manager', 'business analyst', 'program manager', 'chief of staff',
                   'supply chain', 'project manager', 'scrum master'],
}

EXPERIENCE_KEYWORDS = {
    'fresher': ['fresher', 'entry level', '0-1 years', 'intern', 'trainee', 'junior engineer', 'graduate'],
    'junior': ['1-3 years', 'junior', 'associate', '1+ year', '2+ years'],
    'mid': ['3-6 years', 'mid', 'mid-level', '3+ years', '4+ years', '5+ years'],
    'senior': ['senior', 'lead', 'staff', '6+ years', '7+ years', '8+ years', '9+ years'],
    'lead': ['principal', 'director', 'head of', 'vp', 'manager', '10+ years', 'architect', 'fellow'],
}

SALARY_RANGES = {
    'fresher': (300000, 1200000),
    'junior': (800000, 2500000),
    'mid': (2000000, 5000000),
    'senior': (4000000, 10000000),
    'lead': (8000000, 25000000),
}

ADZUNA_CATEGORIES = [
    ('it-jobs', 'engineering'),
    ('engineering-jobs', 'engineering'),
    ('technology-jobs', 'engineering'),
    ('data-analyst-jobs', 'data_ai'),
    ('creative-design-jobs', 'design'),
    ('sales-jobs', 'sales'),
    ('marketing-jobs', 'marketing'),
    ('accounting-finance-jobs', 'operations'),
    ('admin-jobs', 'operations'),
    ('consultancy-jobs', 'product'),
    ('customer-service-jobs', 'sales'),
    ('graduate-jobs', None),
    ('hr-jobs', 'operations'),
]

INDIAN_CITIES = [
    'Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai',
    'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur',
]


def infer_category(title, description):
    text = (title + ' ' + description).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return cat
    return random.choice(list(CATEGORY_KEYWORDS.keys()))


def infer_experience(title, description):
    text = (title + ' ' + description).lower()
    for exp, keywords in EXPERIENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return exp
    weights = {'fresher': 15, 'junior': 25, 'mid': 30, 'senior': 20, 'lead': 10}
    return random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def fetch_adzuna_jobs(max_total=300):
    app_id = settings.ADZUNA_APP_ID
    app_key = settings.ADZUNA_APP_KEY
    if not app_id or not app_key:
        logger.warning("Adzuna API keys not configured")
        return []

    jobs_found = []
    base_url = 'https://api.adzuna.com/v1/api/jobs/in/search/'
    per_page = 50
    max_pages = min(5, max(1, max_total // per_page))

    search_configs = []
    for adz_cat, our_cat in ADZUNA_CATEGORIES:
        search_configs.append({'category': adz_cat, 'what': ''})
    for city in INDIAN_CITIES[:5]:
        search_configs.append({'what': 'software', 'where': city})
        search_configs.append({'what': 'data', 'where': city})
        search_configs.append({'what': 'marketing', 'where': city})

    seen = set()

    for config in search_configs:
        for page in range(1, max_pages + 1):
            if len(jobs_found) >= max_total:
                break
            try:
                params = {
                    'app_id': app_id,
                    'app_key': app_key,
                    'results_per_page': per_page,
                    'page': page,
                    'content-type': 'application/json',
                    'max_days_old': 30,
                }
                if config.get('what'):
                    params['what'] = config['what']
                if config.get('where'):
                    params['where'] = config['where']
                if config.get('category'):
                    params['category'] = config['category']

                resp = requests.get(base_url + str(page), params=params, timeout=20)
                if resp.status_code != 200:
                    logger.warning(f"Adzuna returned {resp.status_code} for {config}")
                    continue

                data = resp.json()
                results = data.get('results', [])
                if not results:
                    break

                for job in results:
                    job_id = job.get('id')
                    if job_id and job_id in seen:
                        continue
                    if job_id:
                        seen.add(job_id)

                    title = job.get('title', '')
                    company = job.get('company', {}).get('display_name', '')
                    if not title or not company:
                        continue

                    location = job.get('location', {}).get('display_name', '')
                    area = job.get('location', {}).get('area', [])
                    if not location and area:
                        location = area[-1] if len(area) > 1 else area[0]

                    description = re.sub(r'<[^>]+>', '', job.get('description', ''))[:3000]
                    apply_url = job.get('redirect_url', '')

                    salary_min = job.get('salary_min')
                    salary_max = job.get('salary_max')
                    salary_currency = job.get('salary_currency', 'INR')
                    contract_type = job.get('contract_type', '')
                    contract_time = job.get('contract_time', '')

                    job_type = ''
                    if contract_type:
                        job_type = contract_type
                    if contract_time and contract_time not in job_type:
                        if job_type:
                            job_type += ' / '
                        job_type += contract_time.replace('_', ' ')

                    created_str = job.get('created')
                    posted_at = timezone.now()
                    if created_str:
                        try:
                            from datetime import datetime
                            posted_at = datetime.strptime(created_str.split('+')[0].split('T')[0], '%Y-%m-%d')
                            posted_at = timezone.make_aware(posted_at) if timezone.is_naive(posted_at) else posted_at
                        except (ValueError, IndexError):
                            posted_at = timezone.now() - timedelta(days=random.randint(0, 14))

                    category = infer_category(title, description)
                    experience = infer_experience(title, description)

                    is_remote = any(w in (title + ' ' + description).lower()
                                    for w in ['remote', 'work from home', 'wfh', '100% remote'])

                    jobs_found.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'category': category,
                        'experience_level': experience,
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency if salary_currency else 'INR',
                        'remote': is_remote,
                        'description': description,
                        'apply_url': apply_url,
                        'source_url': apply_url,
                        'source_company': company,
                        'posted_at': posted_at,
                        'expires_at': posted_at + timedelta(days=random.randint(14, 45)),
                        'is_active': True,
                        'is_featured': False,
                        'country': 'IN' if any(city.lower() in location.lower() for city in
                                                ['bangalore', 'mumbai', 'delhi', 'pune', 'hyderabad',
                                                 'chennai', 'kolkata', 'gurgaon', 'noida', 'ahmedabad',
                                                 'jaipur', 'india', 'indian']) else '',
                    })

                time.sleep(0.5)

            except requests.RequestException as e:
                logger.warning(f"Adzuna request failed: {e}")
                time.sleep(2)
                continue

        if len(jobs_found) >= max_total:
            break

    return jobs_found


def generate_fallback_jobs(count):
    companies = [
        ('Stripe', 'US'), ('Vercel', 'US'), ('Linear', 'US'), ('Glean', 'US'),
        ('Vanta', 'US'), ('Brex', 'US'), ('Mercury', 'US'), ('Airtable', 'US'),
        ('Deel', 'AE'), ('Lattice', 'US'), ('Loom', 'US'), ('Miro', 'NL'),
        ('Replit', 'US'), ('Webflow', 'US'), ('Ramp', 'US'), ('Anduril', 'US'),
        ('Flipkart', 'IN'), ('Zomato', 'IN'), ('Swiggy', 'IN'), ('Razorpay', 'IN'),
        ('CRED', 'IN'), ('Groww', 'IN'), ('Zerodha', 'IN'), ('PhonePe', 'IN'),
        ('OYO', 'IN'), ('MakeMyTrip', 'IN'), ('Nykaa', 'IN'), ('Meesho', 'IN'),
        ('ShareChat', 'IN'), ('Jio Platforms', 'IN'), ('Ather Energy', 'IN'),
        ('Rapido', 'IN'), ('Zepto', 'IN'), ('Blinkit', 'IN'), ('Porter', 'IN'),
        ('CoinDCX', 'IN'), ('BharatPe', 'IN'), ('Upstox', 'IN'), ('Spinny', 'IN'),
        ('Google', 'US'), ('Microsoft', 'US'), ('Amazon', 'US'), ('Meta', 'US'),
        ('Netflix', 'US'), ('Apple', 'US'), ('Uber', 'US'),
        ('Airbnb', 'US'), ('Spotify', 'SE'), ('Notion', 'US'), ('Figma', 'US'),
        ('Canva', 'AU'), ('Atlassian', 'AU'), ('GitLab', 'US'), ('Supabase', 'US'),
        ('Render', 'US'), ('Railway', 'US'), ('Neon', 'US'), ('PlanetScale', 'US'),
    ]

    title_templates = {
        'engineering': [
            'Software Engineer', 'Backend Engineer', 'Frontend Engineer',
            'Full Stack Engineer', 'DevOps Engineer', 'SRE',
            'Data Engineer', 'Platform Engineer', 'Infrastructure Engineer',
            'Security Engineer', 'Android Developer', 'iOS Developer',
            'Cloud Engineer', 'Systems Engineer', 'Network Engineer',
        ],
        'data_ai': [
            'Data Scientist', 'Machine Learning Engineer', 'Data Analyst',
            'AI Engineer', 'Analytics Engineer', 'Research Scientist',
            'NLP Engineer', 'Computer Vision Engineer', 'MLOps Engineer',
            'Data Architect', 'Business Intelligence Analyst',
        ],
        'design': [
            'Product Designer', 'UX Designer', 'UI Designer',
            'Design Engineer', 'Brand Designer', 'Visual Designer',
            'Interaction Designer', 'Design Lead', 'Creative Director',
        ],
        'product': [
            'Product Manager', 'Senior Product Manager', 'Product Owner',
            'Technical Product Manager', 'Associate Product Manager',
            'Product Lead', 'Product Analyst', 'Product Operations',
        ],
        'marketing': [
            'Marketing Manager', 'Content Strategist', 'Growth Marketer',
            'SEO Specialist', 'Brand Manager', 'Digital Marketing Manager',
            'Social Media Manager', 'Performance Marketer', 'Product Marketing Manager',
        ],
        'sales': [
            'Account Executive', 'Sales Engineer', 'Customer Success Manager',
            'Revenue Operations Analyst', 'Business Development Manager',
            'Sales Manager', 'Account Manager', 'Enterprise Sales',
        ],
        'operations': [
            'Operations Manager', 'Business Analyst', 'Program Manager',
            'Chief of Staff', 'Project Manager', 'Supply Chain Manager',
            'Scrum Master', 'Technical Program Manager', 'Strategy Manager',
        ],
    }

    indian_cities = ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai',
                     'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur', 'Remote']
    global_cities = ['San Francisco', 'New York', 'London', 'Berlin', 'Singapore',
                     'Sydney', 'Toronto', 'Dubai', 'Amsterdam', 'Remote']

    experiences = ['fresher', 'junior', 'mid', 'senior', 'lead']
    now = timezone.now()
    jobs = []

    for i in range(count):
        company, country = random.choice(companies)
        cat = random.choice(list(title_templates.keys()))
        title = random.choice(title_templates[cat])
        exp = random.choice(experiences)

        is_indian_company = country == 'IN'
        loc = random.choice(indian_cities) if is_indian_company or random.random() > 0.4 else random.choice(global_cities)

        s_min, s_max = SALARY_RANGES[exp]
        salary_min = random.randint(s_min // 2, s_max // 2)
        salary_max = random.randint(salary_min, s_max)

        remote = loc == 'Remote' or (not is_indian_company and random.random() > 0.5)

        company_domain = company.lower().replace("'", "").replace(" ", "").replace(".", "")
        domain_map = {
            'meta': 'metacareers.com',
            'uber': 'uber.com/careers',
            'airbnb': 'airbnb.com/careers',
            'spotify': 'spotify.com/careers',
            'twitter/x': 'x.com',
        }
        domain = domain_map.get(company_domain, f'careers.{company_domain}.com')
        apply_url = f'https://{domain}/jobs/{random.randint(1000, 9999)}'

        desc = (
            f"We are looking for a talented {title} to join {company}. "
            f"This is a {'remote' if remote else 'onsite'} position based in {loc}.\n\n"
            f"## Requirements\n"
            f"- {random.randint(2, 6)}+ years of experience in {cat}\n"
            f"- Strong problem-solving skills\n"
            f"- Experience with modern tools and technologies\n"
            f"- Excellent communication skills\n\n"
            f"## Benefits\n"
            f"- Competitive salary: ₹{salary_min:,} - ₹{salary_max:,}\n"
            f"- Health insurance\n"
            f"- Equity / ESOPs\n"
            f"- Flexible work hours\n"
            f"- Learning & development budget"
        )

        jobs.append({
            'title': title,
            'company': company,
            'location': loc,
            'country': country,
            'category': cat,
            'experience_level': exp,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': 'INR',
            'remote': remote,
            'description': desc,
            'apply_url': apply_url,
            'source_url': f'https://{domain}',
            'source_company': company,
            'posted_at': now - timedelta(days=random.randint(0, 14)),
            'expires_at': now + timedelta(days=random.randint(14, 60)),
            'is_active': True,
            'is_featured': i < 10,
        })

    return jobs


def save_jobs(jobs_data, stdout):
    now = timezone.now()
    created = 0
    skipped = 0

    for data in jobs_data:
        if not data.get('title') or not data.get('company'):
            continue

        defaults = {
            'location': data.get('location', ''),
            'country': data.get('country', ''),
            'remote': data.get('remote', False),
            'salary_min': data.get('salary_min'),
            'salary_max': data.get('salary_max'),
            'salary_currency': data.get('salary_currency', 'INR'),
            'experience_level': data.get('experience_level', ''),
            'category': data.get('category', ''),
            'description': data.get('description', '')[:3000],
            'apply_url': data.get('apply_url', ''),
            'source_url': data.get('source_url', ''),
            'source_company': data.get('source_company', data['company']),
            'posted_at': data.get('posted_at', now),
            'expires_at': data.get('expires_at'),
            'is_active': data.get('is_active', True),
            'is_featured': data.get('is_featured', False),
        }

        lookup = {
            'title': data['title'],
            'company': data['company'],
            'apply_url': data.get('apply_url', ''),
        }

        try:
            job, was_created = Job.objects.get_or_create(
                defaults=defaults,
                **lookup,
            )
            if was_created:
                created += 1
            else:
                skipped += 1
        except Exception as e:
            stdout.write(f"  Error saving '{data['title']}' @ {data['company']}: {e}")

    return created, skipped


class Command(BaseCommand):
    help = 'Scraper: Adzuna API (real India jobs) + fallback seed data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Target number of jobs')
        parser.add_argument('--no-scrape', action='store_true', help='Skip API scraping, only use fallback')

    def handle(self, *args, **options):
        count = options['count']
        no_scrape = options['no_scrape']
        start_time = time.time()
        now = timezone.now()

        self.stdout.write(f"[{now}] Advanced scraper starting...")
        self.stdout.write(f"Adzuna API: {'Skipped' if no_scrape else 'Configured' if settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY else 'Keys not set (using fallback)'}")
        self.stdout.write(f"Target: {count} jobs")

        all_jobs = []

        if not no_scrape and settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY:
            self.stdout.write("Fetching jobs from Adzuna API...")
            all_jobs = fetch_adzuna_jobs(max_total=count)
            self.stdout.write(f"Adzuna returned {len(all_jobs)} jobs")
        else:
            self.stdout.write("API scraping skipped.")

        api_created, api_skipped = save_jobs(all_jobs, self.stdout)
        self.stdout.write(f"API: {api_created} new, {api_skipped} duplicates skipped")

        fallback_needed = max(0, count - api_created)
        if fallback_needed > 0:
            self.stdout.write(f"Generating {fallback_needed} fallback jobs...")
            fallback_jobs = generate_fallback_jobs(fallback_needed)
            fb_created, fb_skipped = save_jobs(fallback_jobs, self.stdout)
            self.stdout.write(f"Fallback: {fb_created} new, {fb_skipped} duplicates skipped")
        else:
            self.stdout.write("Fallback not needed (enough API jobs)")

        elapsed = time.time() - start_time
        total_active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"✓ Scraper complete in {elapsed:.1f}s. {total_active} total active jobs in database."
        ))
