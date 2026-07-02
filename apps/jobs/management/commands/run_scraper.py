import time
import random
import re
import logging
from datetime import timedelta

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.jobs.models import Job

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
]

INDIAN_CITIES = [
    'Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai',
    'Kolkata', 'Gurgaon', 'Noida', 'Ahmedabad', 'Jaipur',
]

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


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def scrape_indeed(location, role_keywords, max_pages=3):
    jobs_found = []
    base_url = 'https://in.indeed.com/jobs'

    for keyword in role_keywords:
        for page in range(max_pages):
            try:
                params = {
                    'q': keyword,
                    'l': location,
                    'start': page * 10,
                }
                resp = requests.get(
                    base_url,
                    params=params,
                    headers=get_headers(),
                    timeout=15,
                )
                if resp.status_code != 200:
                    logger.warning(f"Indeed returned {resp.status_code} for {keyword} in {location}")
                    continue

                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.select('[class*="job_seen_beacon"], [class*="result"], .job-card, .tapItem')

                if not cards:
                    cards = soup.select('table.results tbody tr, .jobCard, .job-row')

                for card in cards:
                    try:
                        title_el = card.select_one('h2 a, h2 span, [class*="jobTitle"] a, [class*="title"] a')
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)

                        company_el = card.select_one('[class*="companyName"], [class*="company"] a, [class*="company"] span')
                        company = company_el.get_text(strip=True) if company_el else 'Unknown Company'

                        loc_el = card.select_one('[class*="location"], [class*="loc"]')
                        job_location = loc_el.get_text(strip=True) if loc_el else location

                        salary_el = card.select_one('[class*="salary"], [class*="pay"]')
                        salary_text = salary_el.get_text(strip=True) if salary_el else ''

                        link_el = card.select_one('h2 a, [class*="jobTitle"] a')
                        relative_link = link_el.get('href') if link_el else ''
                        if relative_link and not relative_link.startswith('http'):
                            relative_link = 'https://in.indeed.com' + relative_link
                        apply_url = relative_link or f'https://in.indeed.com/viewjob?jk={random.randint(10000,99999)}'

                        desc_el = card.select_one('[class*="summary"], [class*="description"], [class*="snippet"]')
                        description = desc_el.get_text(strip=True) if desc_el else ''

                        salary_min, salary_max = parse_indeed_salary(salary_text + ' ' + description)

                        remote = any(w in (title + ' ' + description).lower()
                                     for w in ['remote', 'work from home', 'wfh', 'fully remote', '100% remote'])

                        jobs_found.append({
                            'title': title,
                            'company': company,
                            'location': job_location,
                            'salary_min': salary_min,
                            'salary_max': salary_max,
                            'description': description[:2000],
                            'apply_url': apply_url,
                            'remote': remote,
                            'source': 'Indeed',
                        })
                    except Exception:
                        continue

                delay = random.uniform(2.0, 4.0)
                time.sleep(delay)

            except requests.RequestException as e:
                logger.warning(f"Request failed for {keyword} in {location}: {e}")
                time.sleep(5)
                continue

    return jobs_found


def parse_indeed_salary(text):
    if not text:
        return None, None
    text = text.replace(',', '').replace('\u20b9', '').replace('₹', '').strip()
    numbers = re.findall(r'(\d{3,})', text)
    if numbers:
        nums = [int(n) for n in numbers if int(n) > 1000]
        if len(nums) >= 2:
            return min(nums), max(nums)
        elif len(nums) == 1:
            return int(nums[0] * 0.7), nums[0]
    return None, None


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
        ('Netflix', 'US'), ('Apple', 'US'), ('Twitter/X', 'US'), ('Uber', 'US'),
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
            'twitter/x': 'x.com',
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
    help = 'Advanced scraper: scrapes Indeed India + generates fallback jobs with real-looking data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Number of fallback jobs if scraping fails')
        parser.add_argument('--no-scrape', action='store_true', help='Skip Indeed scraping, only use fallback')

    def handle(self, *args, **options):
        count = options['count']
        no_scrape = options['no_scrape']
        start_time = time.time()
        now = timezone.now()

        self.stdout.write(f"[{now}] Advanced scraper starting...")
        self.stdout.write(f"Scrape Indeed: {'No' if no_scrape else 'Yes'}")
        self.stdout.write(f"Fallback count: {count}")

        all_jobs = []

        if not no_scrape:
            cities_to_scrape = ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Remote']
            role_groups = [
                ['software engineer', 'backend engineer', 'frontend developer'],
                ['data scientist', 'data analyst', 'machine learning'],
                ['product manager', 'ux designer', 'devops engineer'],
                ['full stack', 'android developer', 'ios developer'],
                ['marketing', 'sales', 'customer success'],
            ]

            self.stdout.write("Scraping Indeed India...")
            for city in cities_to_scrape:
                self.stdout.write(f"  Searching {city}...", ending='')
                for roles in role_groups:
                    jobs = scrape_indeed(city, roles, max_pages=2)
                    all_jobs.extend(jobs)
                    if jobs:
                        self.stdout.write(f" {len(jobs)} jobs from {roles[0]}", ending='')
                    time.sleep(random.uniform(1.0, 2.0))
                self.stdout.write(f"  → {len([j for j in all_jobs if city in j.get('location', '')])} total from {city}")

        else:
            self.stdout.write("Indeed scraping skipped.")

        self.stdout.write(f"\nIndeed scraping produced {len(all_jobs)} raw results")

        processed_indeed = []
        for job in all_jobs:
            text = (job['title'] + ' ' + job.get('description', '')).lower()
            job['category'] = infer_category(job['title'], job.get('description', ''))
            job['experience_level'] = infer_experience(job['title'], job.get('description', ''))
            job['source_company'] = job['company']
            job['source_url'] = job.get('apply_url', '')
            job['country'] = 'IN' if any(city.lower() in job.get('location', '').lower() for city in
                                          ['bangalore', 'mumbai', 'delhi', 'pune', 'hyderabad', 'chennai',
                                           'kolkata', 'gurgaon', 'noida', 'ahmedabad', 'jaipur', 'india']) else ''
            job['salary_currency'] = 'INR'
            job['posted_at'] = now - timedelta(days=random.randint(0, 7))
            job['expires_at'] = now + timedelta(days=random.randint(14, 45))
            job['is_featured'] = False
            processed_indeed.append(job)

        indeed_created, indeed_skipped = save_jobs(processed_indeed, self.stdout)
        self.stdout.write(f"Indeed: {indeed_created} new, {indeed_skipped} duplicates skipped")

        fallback_needed = max(0, count - indeed_created)
        if fallback_needed > 0:
            self.stdout.write(f"Generating {fallback_needed} fallback jobs...")
            fallback_jobs = generate_fallback_jobs(fallback_needed)
            fb_created, fb_skipped = save_jobs(fallback_jobs, self.stdout)
            self.stdout.write(f"Fallback: {fb_created} new, {fb_skipped} duplicates skipped")
        else:
            self.stdout.write("Fallback not needed (enough Indeed jobs)")

        elapsed = time.time() - start_time
        total_active = Job.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"✓ Scraper complete in {elapsed:.1f}s. {total_active} total active jobs in database."
        ))
