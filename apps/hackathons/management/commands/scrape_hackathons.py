from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from apps.hackathons.models import Hackathon
import random
import requests
from bs4 import BeautifulSoup
import json


INDIAN_ORGANIZERS = [
    'Smart India Hackathon', 'HackerEarth', 'HackerRank', 'CodeChef', 'Coding Ninjas',
    'Unstop', 'Devfolio', 'Major League Hacking', 'TechGig', 'Dare2Compete',
    'IIT Bombay', 'IIT Delhi', 'IIT Madras', 'IIT Kharagpur', 'IIT Kanpur',
    'NIT Trichy', 'BITS Pilani', 'VIT Vellore', 'SRM University', 'PES University',
]

HACKATHON_TEMPLATES = [
    {'title': 'Smart India Hackathon {year}', 'category': 'ai', 'prize': '₹10,00,000'},
    {'title': 'Flipkart GRiD 6.0', 'category': 'fintech', 'prize': '₹5,00,000'},
    {'title': 'Amazon ML Challenge', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'Google Solution Challenge', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'JP Morgan Code for Good', 'category': 'fintech', 'prize': '₹2,00,000'},
    {'title': 'Microsoft Imagine Cup', 'category': 'ai', 'prize': '$10,000'},
    {'title': 'Goldman Sachs Engineering Summit', 'category': 'fintech', 'prize': '₹1,00,000'},
    {'title': 'Swiggy HackerCamp', 'category': 'edtech', 'prize': '₹3,00,000'},
    {'title': 'Zomato Feeding India Hackathon', 'category': 'health', 'prize': '₹2,00,000'},
    {'title': 'Razorpay RISE Hackathon', 'category': 'fintech', 'prize': '₹5,00,000'},
    {'title': 'CRED Climate Hackathon', 'category': 'climate', 'prize': '₹4,00,000'},
    {'title': 'Groww Fintech Hackathon', 'category': 'fintech', 'prize': '₹2,50,000'},
    {'title': 'Zerodha Quantathon', 'category': 'fintech', 'prize': '₹3,50,000'},
    {'title': 'Ola Mobility Hackathon', 'category': 'iot', 'prize': '₹3,00,000'},
    {'title': 'MakeMyTrip Travel Hack', 'category': 'other', 'prize': '₹1,50,000'},
    {'title': 'Nykaa Beauty Tech Hackathon', 'category': 'edtech', 'prize': '₹2,00,000'},
    {'title': 'Ather Energy EV Hackathon', 'category': 'climate', 'prize': '₹3,00,000'},
    {'title': 'Jio Platforms 5G Hackathon', 'category': 'iot', 'prize': '₹5,00,000'},
    {'title': 'PhonePe Payment Hackathon', 'category': 'fintech', 'prize': '₹4,00,000'},
    {'title': 'Unacademy EdTech Hackathon', 'category': 'edtech', 'prize': '₹2,00,000'},
    {'title': 'Meesho Social Commerce Hack', 'category': 'other', 'prize': '₹1,50,000'},
    {'title': 'ShareChat AI Hackathon', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'Byju\'s Future of Learning', 'category': 'edtech', 'prize': '₹5,00,000'},
    {'title': 'AngelHack India', 'category': 'other', 'prize': '₹2,00,000'},
    {'title': 'Deloitte Techathon', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'TCS CodeVita', 'category': 'ai', 'prize': '₹5,00,000'},
    {'title': 'Wipro TalentNext Hackathon', 'category': 'other', 'prize': '₹2,00,000'},
    {'title': 'Cisco Global Problem Solver', 'category': 'iot', 'prize': '$5,000'},
    {'title': 'IBM Call for Code', 'category': 'climate', 'prize': '$10,000'},
    {'title': 'EY Techathon', 'category': 'fintech', 'prize': '₹3,00,000'},
]


def try_unstop():
    try:
        resp = requests.get(
            'https://unstop.com/api/public/competition/list?type=hackathon&page=1&per_page=20',
            headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'},
            timeout=10
        )
        data = resp.json()
        competitions = data.get('data', {}).get('competition')
        if competitions and isinstance(competitions, list) and len(competitions) > 0:
            return competitions
    except Exception:
        pass
    return None


def try_hackerearth():
    try:
        resp = requests.get(
            'https://www.hackerearth.com/challenges/',
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        soup = BeautifulSoup(resp.text, 'html.parser')
        import re
        scripts = soup.find_all('script')
        for s in scripts:
            if s.string and 'challenges' in s.string:
                match = re.search(r'challenges\s*:\s*(\[.*?\])', s.string, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
    except Exception:
        pass
    return None


class Command(BaseCommand):
    help = 'Scrape hackathons from various sources (Unstop, HackerEarth, seed data)'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=15, help='Number of hackathons to generate')

    def handle(self, *args, **options):
        count = options.get('count')
        now = timezone.now()
        created = 0

        self.stdout.write('Attempting to fetch from Unstop...')
        unstop_data = try_unstop()
        if unstop_data:
            self.stdout.write(self.style.SUCCESS(f'Found {len(unstop_data)} hackathons on Unstop'))
            for item in unstop_data:
                defaults = {
                    'organizer': item.get('organizer_name', 'Unstop'),
                    'mode': 'online',
                    'category': item.get('category', 'other'),
                    'prize_pool': item.get('prize', ''),
                    'start_date': item.get('start_date', now.date()),
                    'end_date': item.get('end_date', now.date() + timedelta(days=7)),
                    'apply_url': f'https://unstop.com/competition/{item.get("slug", "")}',
                    'description': item.get('description', ''),
                    'cover_image': item.get('cover_image', ''),
                    'is_active': True,
                }
                job, created_job = Hackathon.objects.get_or_create(
                    title=item.get('title', 'Unstop Hackathon'),
                    defaults=defaults,
                )
                if created_job:
                    created += 1
            self.stdout.write(self.style.SUCCESS(f'Created {created} hackathons from Unstop'))
            return

        self.stdout.write('Unstop API unavailable. Trying HackerEarth...')
        he_data = try_hackerearth()
        if he_data:
            self.stdout.write(self.style.SUCCESS('HackerEarth data found'))
            for item in he_data[:count]:
                title = item.get('title', 'HackerEarth Challenge')
                defaults = {
                    'organizer': item.get('company', 'HackerEarth'),
                    'mode': 'online',
                    'category': 'other',
                    'prize_pool': item.get('prize', ''),
                    'start_date': now.date(),
                    'end_date': now.date() + timedelta(days=14),
                    'apply_url': item.get('url', ''),
                    'description': item.get('description', ''),
                    'is_active': True,
                }
                job, created_job = Hackathon.objects.get_or_create(title=title, defaults=defaults)
                if created_job:
                    created += 1
            self.stdout.write(self.style.SUCCESS(f'Created {created} hackathons from HackerEarth'))
            return

        self.stdout.write('External APIs unavailable. Generating Indian hackathons as seed data...')
        categories = ['ai', 'web3', 'climate', 'health', 'fintech', 'gaming', 'student', 'beginner', 'iot', 'ar_vr', 'edtech', 'other']
        modes = ['online', 'in_person', 'hybrid']

        selected = random.sample(HACKATHON_TEMPLATES, min(count, len(HACKATHON_TEMPLATES)))

        for tmpl in selected:
            start_date = now.date() + timedelta(days=random.randint(0, 60))
            end_date = start_date + timedelta(days=random.randint(1, 7))
            organizer = random.choice(INDIAN_ORGANIZERS)

            title = tmpl['title'].replace('{year}', str(now.year))

            hack, created_hack = Hackathon.objects.get_or_create(
                title=title,
                defaults={
                    'organizer': organizer,
                    'mode': random.choice(modes),
                    'category': tmpl['category'],
                    'prize_pool': tmpl['prize'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'apply_url': f'https://unstop.com/hackathons/{title.lower().replace(" ", "-")}',
                    'description': f'{title} is a premier hackathon organized by {organizer}. This is a great opportunity for developers, designers, and innovators to showcase their skills and win exciting prizes.\n\n## Prizes\n- Grand Prize: {tmpl["prize"]}\n- Runner up prizes\n- Swag and goodies for all participants\n\n## Why participate?\n- Work on real-world problems\n- Get noticed by top recruiters\n- Network with industry experts',
                    'is_active': True,
                    'is_featured': random.random() > 0.7,
                }
            )
            if created_hack:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Hackathon scraper created {created} new hackathons (total: {Hackathon.objects.filter(is_active=True).count()})'))
