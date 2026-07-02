import re
import json
import time
import random
import logging
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.jobs.models import Job

logger = logging.getLogger(__name__)

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

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

# Shine.com search config: (URL keyword, our category)
SHINE_CONFIGS = [
    ("software-engineer", "engineering"),
    ("frontend-developer", "engineering"),
    ("backend-developer", "engineering"),
    ("full-stack-developer", "engineering"),
    ("devops-engineer", "engineering"),
    ("data-scientist", "data_ai"),
    ("data-analyst", "data_ai"),
    ("machine-learning-engineer", "data_ai"),
    ("product-manager", "product"),
    ("ux-designer", "design"),
    ("graphic-designer", "design"),
    ("marketing-manager", "marketing"),
    ("digital-marketing", "marketing"),
    ("sales-manager", "sales"),
    ("business-development", "sales"),
    ("operations-manager", "operations"),
    ("hr-manager", "operations"),
]

SHINE_CITIES = [
    "bangalore", "mumbai", "delhi", "pune", "hyderabad", "chennai",
    "kolkata", "gurgaon", "noida", "ahmedabad", "jaipur",
]

FALLBACK_COMPANIES = [
    ('Stripe', 'US'), ('Vercel', 'US'), ('Linear', 'US'), ('Glean', 'US'),
    ('Vanta', 'US'), ('Brex', 'US'), ('Mercury', 'US'), ('Airtable', 'US'),
    ('Deel', 'AE'), ('Lattice', 'US'), ('Loom', 'US'), ('Miro', 'NL'),
    ('Replit', 'US'), ('Webflow', 'US'), ('Ramp', 'US'), ('Anduril', 'US'),
    ('Flipkart', 'IN'), ('Zomato', 'IN'), ('Swiggy', 'IN'), ('Razorpay', 'IN'),
    ('CRED', 'IN'), ('Groww', 'IN'), ('Zerodha', 'IN'), ('PhonePe', 'IN'),
    ('OYO', 'IN'), ('MakeMyTrip', 'IN'), ('Nykaa', 'IN'), ('Meesho', 'IN'),
    ('ShareChat', 'IN'), ('Jio Platforms', 'IN'), ('Ather Energy', 'IN'),
    ('Zepto', 'IN'), ('Blinkit', 'IN'), ('Porter', 'IN'),
    ('Google', 'US'), ('Microsoft', 'US'), ('Amazon', 'US'), ('Meta', 'US'),
    ('Netflix', 'US'), ('Apple', 'US'), ('Uber', 'US'),
    ('Airbnb', 'US'), ('Spotify', 'SE'), ('Notion', 'US'), ('Figma', 'US'),
    ('Canva', 'AU'), ('Atlassian', 'AU'), ('GitLab', 'US'), ('Supabase', 'US'),
]

FALLBACK_TITLE_TEMPLATES = {
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


def make_session():
    if HAS_CLOUDSCRAPER:
        try:
            return cloudscraper.create_scraper(delay=3)
        except Exception:
            pass
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    return session


def parse_shine_salary(sal_text):
    if not sal_text or 'hidden' in sal_text.lower() or sal_text == '[Salary Hidden]':
        return None, None
    sal_text = sal_text.replace(',', '').replace('Rs', '').replace('₹', '').strip()
    lakh_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|L)', sal_text)
    if lakh_match:
        nums = [int(float(n) * 100000) for n in lakh_match]
        if len(nums) >= 2:
            return min(nums), max(nums)
        elif len(nums) == 1:
            return int(nums[0] * 0.7), nums[0]
    thousand_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:k|K)', sal_text)
    if thousand_match:
        nums = [int(float(n) * 1000) for n in thousand_match]
        if len(nums) >= 2:
            return min(nums), max(nums)
        elif len(nums) == 1:
            return int(nums[0] * 0.7), nums[0]
    return None, None


def parse_shine_experience(exp_text):
    if not exp_text:
        return None
    exp_text = exp_text.lower().strip()
    for level, keywords in EXPERIENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in exp_text:
                return level
    match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)', exp_text)
    if match:
        max_exp = int(match.group(2))
        if max_exp <= 1:
            return 'fresher'
        elif max_exp <= 3:
            return 'junior'
        elif max_exp <= 6:
            return 'mid'
        elif max_exp <= 10:
            return 'senior'
        else:
            return 'lead'
    return 'mid'


def infer_category(title, description=''):
    text = (title + ' ' + description).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return cat
    return random.choice(list(CATEGORY_KEYWORDS.keys()))


def infer_experience(title, description=''):
    text = (title + ' ' + description).lower()
    for exp, keywords in EXPERIENCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return exp
    weights = {'fresher': 15, 'junior': 25, 'mid': 30, 'senior': 20, 'lead': 10}
    return random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def fetch_shine_page(keyword, city, page=1):
    url = f"https://www.shine.com/job-search/{keyword}-jobs-in-{city}"
    if page > 1:
        url += f"?page={page}"

    session = make_session()
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"Shine {url}: HTTP {resp.status_code}")
            return []
        if '__NEXT_DATA__' not in resp.text:
            logger.warning(f"Shine {url}: No __NEXT_DATA__ in response")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        if not script:
            return []

        data = json.loads(script.string)
        search_data = data['props']['pageProps']['initialState']['jsrp']['searchresult']['data']
        raw_jobs = search_data.get('results', [])
        has_next = search_data.get('next', False)

        if not raw_jobs:
            return []

        now = timezone.now()
        jobs = []
        for j in raw_jobs:
            title = j.get('jJT', '').strip()
            company = j.get('jCName', '').strip()
            if not title or not company:
                continue

            locations = j.get('jLoc', [])
            location = locations[0] if locations else city.title()

            salary_text = j.get('jSal', '')
            salary_min, salary_max = parse_shine_salary(salary_text)
            if not salary_min or not salary_max:
                exp_guess = parse_shine_experience(j.get('jExp', ''))
                if exp_guess and exp_guess in SALARY_RANGES:
                    s_min, s_max = SALARY_RANGES[exp_guess]
                    salary_min = random.randint(s_min // 2, s_max // 2)
                    salary_max = random.randint(salary_min, s_max)
                else:
                    salary_min, salary_max = None, None

            description_text = j.get('jJD', '')[:3000] if j.get('jJD') else ''
            description = re.sub(r'<[^>]+>', '', description_text).strip()

            apply_slug = j.get('jSlug', '')
            apply_url = f"https://www.shine.com/job-search/{apply_slug}" if apply_slug else ''

            posted_str = j.get('jPDate', '')
            posted_at = now
            if posted_str:
                try:
                    posted_at = datetime.strptime(posted_str.split('T')[0], '%Y-%m-%d')
                    posted_at = timezone.make_aware(posted_at) if timezone.is_naive(posted_at) else posted_at
                except (ValueError, IndexError):
                    posted_at = now - timedelta(days=random.randint(0, 14))

            experience_level = parse_shine_experience(j.get('jExp', '')) or infer_experience(title, description)
            category = infer_category(title, description)

            is_remote = any(w in (title + ' ' + description + ' ' + location).lower()
                           for w in ['remote', 'work from home', 'wfh', '100% remote'])

            country = 'IN' if any(city_name.lower() in location.lower() for city_name in
                                   ['bangalore', 'mumbai', 'delhi', 'pune', 'hyderabad',
                                    'chennai', 'kolkata', 'gurgaon', 'noida', 'ahmedabad',
                                    'jaipur', 'india', 'indian']) else ''

            jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'country': country,
                'category': category,
                'experience_level': experience_level,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': 'INR',
                'remote': is_remote,
                'description': description[:3000],
                'apply_url': apply_url,
                'source_url': url,
                'source_company': company,
                'posted_at': posted_at,
                'expires_at': None,
                'is_active': True,
                'is_featured': False,
            })

        return jobs

    except Exception as e:
        logger.error(f"Shine fetch error for {url}: {e}")
        return []


def scrape_shine(target_count, max_workers=8):
    all_jobs = []
    seen_ids = set()
    total_pages_per_combo = max(1, min(5, target_count // (len(SHINE_CONFIGS) * len(SHINE_CITIES) * 20) + 1))

    tasks = []
    for keyword, category in SHINE_CONFIGS:
        for city in SHINE_CITIES:
            for page in range(1, total_pages_per_combo + 1):
                tasks.append((keyword, city, page))

    random.shuffle(tasks)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fut_map = {}
        for keyword, city, page in tasks:
            fut = executor.submit(fetch_shine_page, keyword, city, page)
            fut_map[fut] = (keyword, city, page)

        for fut in as_completed(fut_map):
            keyword, city, page = fut_map[fut]
            try:
                jobs = fut.result()
                new_count = 0
                for j in jobs:
                    dedup_key = (j['title'], j['company'], j['location'])
                    if dedup_key not in seen_ids:
                        seen_ids.add(dedup_key)
                        all_jobs.append(j)
                        new_count += 1
                if jobs:
                    logger.info(f"Shine {keyword}/{city} p{page}: {new_count} new / {len(jobs)} total")
            except Exception as e:
                logger.error(f"Shine {keyword}/{city} p{page} failed: {e}")

            if len(all_jobs) >= target_count:
                break

        if len(all_jobs) >= target_count:
            for f in fut_map:
                f.cancel()

    return all_jobs[:target_count]


def generate_fallback_jobs(count):
    indian_cities = ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai',
                     'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur', 'Remote']
    global_cities = ['San Francisco', 'New York', 'London', 'Berlin', 'Singapore',
                     'Sydney', 'Toronto', 'Dubai', 'Amsterdam', 'Remote']
    experiences = ['fresher', 'junior', 'mid', 'senior', 'lead']
    now = timezone.now()
    jobs = []

    for i in range(count):
        company, country = random.choice(FALLBACK_COMPANIES)
        cat = random.choice(list(FALLBACK_TITLE_TEMPLATES.keys()))
        title = random.choice(FALLBACK_TITLE_TEMPLATES[cat])
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
        }
        domain = domain_map.get(company_domain, f'careers.{company_domain}.com')
        apply_url = f'https://{domain}/jobs/{random.randint(1000, 9999)}'

        desc = (
            f"We are looking for a talented {title} to join {company}. "
            f"This is a {'remote' if remote else 'onsite'} position based in {loc}.\n\n"
            f"## Requirements\n"
            f"- {random.randint(2, 6)}+ years of experience\n"
            f"- Strong problem-solving skills\n"
            f"- Experience with modern tools and technologies\n\n"
            f"## Benefits\n"
            f"- Competitive salary: ₹{salary_min:,} - ₹{salary_max:,}\n"
            f"- Health insurance\n- Flexible work hours"
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
            job, was_created = Job.objects.get_or_create(defaults=defaults, **lookup)
            if was_created:
                created += 1
            else:
                skipped += 1
        except Exception as e:
            stdout.write(f"  Error saving '{data['title']}' @ {data['company']}: {e}")

    return created, skipped


class Command(BaseCommand):
    help = 'Scraper: Shine.com (real India jobs) + fallback seed data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=300, help='Target number of jobs')
        parser.add_argument('--no-scrape', action='store_true', help='Skip Shine scraping')

    def handle(self, *args, **options):
        count = options['count']
        no_scrape = options['no_scrape']
        start_time = time.time()
        now = timezone.now()

        self.stdout.write(f"[{now}] Advanced scraper starting...")
        self.stdout.write(f"Shine.com: {'Skipped' if no_scrape else 'Enabled'}")
        self.stdout.write(f"Target: {count} jobs")

        all_jobs = []

        if not no_scrape:
            self.stdout.write("Fetching jobs from Shine.com...")
            all_jobs = scrape_shine(target_count=count)
            self.stdout.write(f"Shine returned {len(all_jobs)} unique jobs")
        else:
            self.stdout.write("Shine scraping skipped.")

        api_created, api_skipped = save_jobs(all_jobs, self.stdout)
        self.stdout.write(f"Shine: {api_created} new, {api_skipped} duplicates skipped")

        fallback_needed = max(0, count - api_created)
        if fallback_needed > 0:
            self.stdout.write(f"Generating {fallback_needed} fallback jobs...")
            fallback_jobs = generate_fallback_jobs(fallback_needed)
            fb_created, fb_skipped = save_jobs(fallback_jobs, self.stdout)
            self.stdout.write(f"Fallback: {fb_created} new, {fb_skipped} duplicates skipped")
        else:
            self.stdout.write("Fallback not needed")

        if not no_scrape and api_created == 0:
            self.stdout.write(self.style.WARNING(
                "Shine returned 0 new jobs. Check network connectivity."
            ))

        elapsed = time.time() - start_time
        total_active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"✓ Scraper complete in {elapsed:.1f}s. {total_active} total active jobs."
        ))
