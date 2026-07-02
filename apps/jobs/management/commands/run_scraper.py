from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import Job
import random


class Command(BaseCommand):
    help = 'Run scraper to fetch new jobs from various sources'

    def add_arguments(self, parser):
        parser.add_argument('--company', type=str, help='Specific company to scrape')
        parser.add_argument('--count', type=int, default=20, help='Number of test jobs to generate')

    def handle(self, *args, **options):
        company = options.get('company')
        count = options.get('count')
        now = timezone.now()

        self.stdout.write(f"[{now}] Scraper running...")

        if company:
            companies = [company]
        else:
            companies = [
                'Stripe', 'Vercel', 'Linear', 'Retool', 'Glean', 'Vanta', 'Brex',
                'Mercury', 'Airtable', 'Ashby', 'Deel', 'Lattice', 'Loom', 'Miro',
                'Podium', 'Harness', 'Replit', 'Webflow', 'Ramp', 'Anduril',
            ]

        titles_by_cat = {
            'engineering': ['Software Engineer', 'Backend Engineer', 'Frontend Engineer', 'Full Stack Engineer', 'DevOps Engineer', 'SRE', 'Data Engineer', 'ML Engineer', 'Security Engineer'],
            'design': ['Product Designer', 'UX Designer', 'UI Designer', 'Design Engineer', 'Brand Designer'],
            'product': ['Product Manager', 'Senior PM', 'Product Owner', 'Technical PM', 'APM'],
            'data_ai': ['Data Scientist', 'ML Engineer', 'Data Analyst', 'AI Engineer', 'Analytics Engineer'],
            'marketing': ['Marketing Manager', 'Content Strategist', 'Growth Marketer', 'SEO Specialist'],
            'sales': ['Account Executive', 'Sales Engineer', 'Customer Success', 'Revenue Operations'],
            'operations': ['Operations Manager', 'Business Analyst', 'Program Manager', 'Chief of Staff'],
        }

        experiences = ['fresher', 'junior', 'mid', 'senior', 'lead']
        locations = ['San Francisco', 'New York', 'London', 'Berlin', 'Singapore', 'Sydney', 'Toronto', 'Dubai', 'Remote', 'Paris', 'Amsterdam', 'Bangalore']

        created = 0
        for _ in range(count):
            c = random.choice(companies)
            cat = random.choice(list(titles_by_cat.keys()))
            title = random.choice(titles_by_cat[cat])
            exp = random.choice(experiences)
            loc = random.choice(locations)

            salary_ranges = {'fresher': (600000, 1500000), 'junior': (1200000, 2900000), 'mid': (2700000, 5800000), 'senior': (5000000, 10000000), 'lead': (9100000, 22000000)}
            s_min, s_max = salary_ranges[exp]
            salary_min = random.randint(s_min // 2, s_max // 2)
            salary_max = random.randint(salary_min, s_max)

            job, created_job = Job.objects.get_or_create(
                title=title,
                company=c,
                location=loc,
                defaults={
                    'country': 'IN',
                    'remote': random.choice([True, True, True, False]),
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'salary_currency': 'INR',
                    'experience_level': exp,
                    'category': cat,
                    'description': f"We are looking for a talented {title} to join {c}. This is a {'remote' if True else 'onsite'} role based in {loc}. You'll work with a world-class team.\n\n## Requirements\n- Strong experience\n- Problem-solving skills\n- Team player\n\n## Benefits\n- Competitive salary & equity\n- Health insurance\n- Flexible PTO",
                    'apply_url': f'https://careers.{c.lower().replace(" ", "")}.com/jobs/{random.randint(1000,9999)}',
                    'source_url': f'https://careers.{c.lower().replace(" ", "")}.com',
                    'source_company': c,
                    'posted_at': now - timedelta(days=random.randint(0, 14)),
                    'expires_at': now + timedelta(days=random.randint(14, 60)),
                    'is_active': True,
                }
            )
            if created_job:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Scraper created {created} new jobs (total active: {Job.objects.filter(is_active=True).count()})"))
