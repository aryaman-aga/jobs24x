from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import Job
from apps.payments.models import SubscriptionPlan
from apps.hackathons.models import Hackathon
from apps.blog.models import BlogPost
from django.contrib.auth.models import User
import random


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        if SubscriptionPlan.objects.exists():
            self.stdout.write(self.style.WARNING("Data already exists, skipping seed"))
            return

        self.stdout.write("Seeding database...")

        Job.objects.all().delete()
        SubscriptionPlan.objects.all().delete()
        Hackathon.objects.all().delete()
        BlogPost.objects.all().delete()

        plans_data = [
            {'name': 'weekly', 'display_name': 'Weekly', 'price': 149, 'duration_days': 7, 'sort_order': 1, 'features': ["Access to hidden jobs not on LinkedIn", "Advanced filters", "Unlimited saved jobs", "Know real salaries before applying"]},
            {'name': 'monthly', 'display_name': 'Monthly', 'price': 499, 'duration_days': 30, 'sort_order': 2, 'features': ["Access to hidden jobs not on LinkedIn", "Advanced filters", "Unlimited saved jobs", "Unlimited alerts", "Know real salaries before applying"]},
            {'name': 'six_month', 'display_name': '6 Months', 'price': 399, 'duration_days': 180, 'sort_order': 3, 'features': ["Access to hidden jobs not on LinkedIn", "Advanced filters", "Unlimited saved jobs", "Unlimited alerts", "Know real salaries before applying", "Early access to new jobs"]},
            {'name': 'yearly', 'display_name': 'Yearly', 'price': 199, 'duration_days': 365, 'sort_order': 4, 'features': ["Access to hidden jobs not on LinkedIn", "Advanced filters", "Unlimited saved jobs", "Unlimited alerts", "Know real salaries before applying", "Early access to new jobs", "Priority support"]},
        ]

        for plan_data in plans_data:
            SubscriptionPlan.objects.create(**plan_data)
        self.stdout.write("✓ Created subscription plans")

        companies = [
            ('Stripe', 'US'), ('Vercel', 'US'), ('Linear', 'US'), ('Retool', 'US'),
            ('Glean', 'US'), ('Vanta', 'US'), ('Brex', 'US'), ('Mercury', 'US'),
            ('Airtable', 'US'), ('Ashby', 'US'), ('Deel', 'AE'), ('Lattice', 'US'),
            ('Loom', 'US'), ('Miro', 'US'), ('Podium', 'US'), ('Harness', 'US'),
            ('Replit', 'US'), ('Webflow', 'US'), ('Ramp', 'US'), ('Anduril', 'US'),
        ]

        job_titles = {
            'engineering': ['Software Engineer', 'Backend Engineer', 'Frontend Engineer', 'Full Stack Engineer', 'DevOps Engineer', 'SRE', 'iOS Engineer', 'Android Engineer', 'Data Engineer', 'ML Engineer'],
            'design': ['Product Designer', 'UX Designer', 'UI Designer', 'Design Engineer', 'Brand Designer'],
            'product': ['Product Manager', 'Senior PM', 'Product Owner', 'Technical PM'],
            'data_ai': ['Data Scientist', 'ML Engineer', 'Data Analyst', 'AI Engineer', 'Research Scientist'],
            'marketing': ['Marketing Manager', 'Content Strategist', 'Growth Marketer', 'SEO Specialist'],
            'sales': ['Account Executive', 'Sales Engineer', 'Customer Success', 'Revenue Operations'],
            'operations': ['Operations Manager', 'Business Analyst', 'Program Manager', 'Chief of Staff'],
        }

        experiences = ['fresher', 'junior', 'mid', 'senior', 'lead']
        categories = list(job_titles.keys())

        now = timezone.now()
        for i in range(100):
            company, country = random.choice(companies)
            category = random.choice(categories)
            title = random.choice(job_titles[category])
            exp = random.choice(experiences)

            salary_ranges = {
                'fresher': (600000, 1500000),
                'junior': (1200000, 2900000),
                'mid': (2700000, 5800000),
                'senior': (5000000, 10000000),
                'lead': (9100000, 22000000),
            }
            s_min, s_max = salary_ranges[exp]
            salary_min = random.randint(s_min // 2, s_max // 2)
            salary_max = random.randint(salary_min, s_max)

            location = random.choice(['San Francisco', 'New York', 'London', 'Berlin', 'Singapore', 'Sydney', 'Toronto', 'Dubai', 'Remote', 'Paris', 'Amsterdam', 'Bangalore'])

            Job.objects.create(
                title=title,
                company=company,
                location=location,
                country=country,
                remote=random.choice([True, True, True, False]),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency='INR',
                experience_level=exp,
                category=category,
                description=f"We are looking for a talented {title} to join our team at {company}. This is a {'remote' if True else 'onsite'} position based in {location}. You will work with a world-class team to build products used by millions.\n\n## Requirements\n- Strong experience in your domain\n- Excellent problem-solving skills\n- Ability to work in a fast-paced environment\n\n## Benefits\n- Competitive salary and equity\n- Health insurance\n- Flexible PTO\n- Home office budget",
                apply_url=f'https://careers.{company.lower()}.com/jobs/{i}',
                source_url=f'https://careers.{company.lower()}.com',
                source_company=company,
                posted_at=now - timedelta(days=random.randint(0, 30)),
                expires_at=now + timedelta(days=random.randint(7, 60)),
                is_active=True,
                is_featured=i < 6,
            )
        self.stdout.write("✓ Created 100 sample jobs")

        hackathon_names = [
            ('AI Innovation Challenge', 'Devpost', 'ai', '₹40L'),
            ('Web3 Buildathon', 'Devfolio', 'web3', '₹20L'),
            ('Climate Tech Hack', 'MLH', 'climate', '₹8L'),
            ('Health Hackathon', 'Devpost', 'health', '₹12L'),
            ('Fintech Summit', 'Unstop', 'fintech', '₹25L'),
            ('Student Developer Week', 'MLH', 'student', '₹4L'),
            ('IoT Innovation Lab', 'Hackster', 'iot', '₹6.5L'),
            ('EdTech Hackathon', 'Devfolio', 'edtech', '₹10L'),
        ]

        for title, organizer, cat, prize in hackathon_names:
            start = now.date() + timedelta(days=random.randint(1, 60))
            Hackathon.objects.create(
                title=title,
                organizer=organizer,
                mode=random.choice(['online', 'in_person', 'hybrid']),
                category=cat,
                prize_pool=prize,
                start_date=start,
                end_date=start + timedelta(days=random.randint(1, 3)),
                apply_url=f'https://{organizer.lower()}.com/hackathons/{title.lower().replace(" ", "-")}',
                is_active=True,
            )
        self.stdout.write("✓ Created hackathons")

        blog_posts = [
            {
                'title': 'Why applying to fewer jobs gets you more interviews',
                'excerpt': 'The math behind targeting low-competition roles instead of mass-applying to FAANG postings.',
                'content': 'Most job seekers make the same mistake: they apply to hundreds of positions and hear back from almost none. The problem isn\'t that there aren\'t enough jobs — it\'s that everyone is applying to the same ones. When a role at a FAANG company opens up, it gets thousands of applications within hours. Your resume becomes a needle in a haystack. The smarter approach is to find roles at companies that most candidates haven\'t heard of yet. These "hidden gem" companies offer great compensation, interesting work, and most importantly — your application actually gets read.\n\nAt Jobs24X7, we track career pages of 2,400+ companies and surface roles before they hit mainstream boards. Our users consistently report 3-5x higher callback rates compared to traditional job boards.',
                'read_time_min': 5,
                'is_published': True,
                'published_at': now - timedelta(days=10),
            },
            {
                'title': 'How to spot a hidden-gem company in 60 seconds',
                'excerpt': 'Five signals that tell you a company is hiring fast but flying under the recruiter radar.',
                'content': 'Not every great company has a recognizable brand. Here are five signals that a company is worth your attention:\n\n1. Recent funding from top VCs (Sequoia, a16z, Benchmark)\n2. Engineering team growing 2x+ year over year\n3. Low Glassdoor recognition (means less competition)\n4. Modern tech stack (Rust, Go, TypeScript, React)\n5. Remote-first culture\n\nWhen you find a company hitting 3+ of these signals, it\'s a hidden gem. Apply immediately.',
                'read_time_min': 4,
                'is_published': True,
                'published_at': now - timedelta(days=5),
            },
        ]

        for post_data in blog_posts:
            BlogPost.objects.create(**post_data)
        self.stdout.write("✓ Created blog posts")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
