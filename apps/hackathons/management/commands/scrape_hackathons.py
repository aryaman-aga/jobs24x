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
    'IIIT Hyderabad', 'IIIT Delhi', 'Jadavpur University', 'DTU Delhi', 'NSUT Delhi',
    'MIT-WPU', 'COEP Pune', 'Thapar University', 'LNMIIT Jaipur', 'DAIICT Gandhinagar',
]

HACKATHON_TEMPLATES = [
    # Major Indian Hackathons
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
    {'title': 'Deloitte Techathon', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'TCS CodeVita', 'category': 'ai', 'prize': '₹5,00,000'},
    {'title': 'Wipro TalentNext Hackathon', 'category': 'other', 'prize': '₹2,00,000'},
    {'title': 'Cisco Global Problem Solver', 'category': 'iot', 'prize': '$5,000'},
    {'title': 'IBM Call for Code', 'category': 'climate', 'prize': '$10,000'},
    {'title': 'EY Techathon', 'category': 'fintech', 'prize': '₹3,00,000'},
    {'title': 'Accenture Innovation Challenge', 'category': 'ai', 'prize': '₹2,00,000'},
    {'title': 'Infosys Hackathon', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'Paytm Build for India', 'category': 'fintech', 'prize': '₹5,00,000'},
    {'title': 'Google Summer of Code', 'category': 'student', 'prize': '$3,000'},
    {'title': 'MLH Fellowship', 'category': 'student', 'prize': '$5,000'},
    {'title': 'Outplayed by Google', 'category': 'gaming', 'prize': '$10,000'},
    {'title': 'ESL India Premiership', 'category': 'gaming', 'prize': '₹5,00,000'},
    # University hackathons
    {'title': 'IIT Bombay E-Summit Hackathon', 'category': 'ai', 'prize': '₹1,00,000'},
    {'title': 'IIT Delhi Tryst Hackathon', 'category': 'other', 'prize': '₹80,000'},
    {'title': 'IIT Madras Shaastra Hackathon', 'category': 'ai', 'prize': '₹1,50,000'},
    {'title': 'IIT Kharagpur Kshitij Hackathon', 'category': 'other', 'prize': '₹1,00,000'},
    {'title': 'IIT Kanpur Techkriti Hackathon', 'category': 'iot', 'prize': '₹75,000'},
    {'title': 'IIT Roorkee Cognizance Hackathon', 'category': 'ai', 'prize': '₹1,00,000'},
    {'title': 'IIT Guwahati Techniche Hackathon', 'category': 'climate', 'prize': '₹60,000'},
    {'title': 'IIT Hyderabad Hackathon', 'category': 'health', 'prize': '₹50,000'},
    {'title': 'BITS Pilani APOGEE Hackathon', 'category': 'ai', 'prize': '₹1,00,000'},
    {'title': 'IIIT Hyderabad Felicity Hackathon', 'category': 'fintech', 'prize': '₹75,000'},
    {'title': 'NIT Trichy Festember Hackathon', 'category': 'other', 'prize': '₹50,000'},
    {'title': 'NIT Surathkal Engineer Hackathon', 'category': 'ai', 'prize': '₹60,000'},
    {'title': 'VIT Vellore Gravitas Hackathon', 'category': 'edtech', 'prize': '₹80,000'},
    {'title': 'DTU Delhi Hackathon', 'category': 'iot', 'prize': '₹40,000'},
    {'title': 'NSUT Delhi Hackathon', 'category': 'ai', 'prize': '₹35,000'},
    {'title': 'DAIICT Gandhinagar Hackathon', 'category': 'fintech', 'prize': '₹30,000'},
    {'title': 'LNMIIT Jaipur Hackathon', 'category': 'web3', 'prize': '₹25,000'},
    {'title': 'Thapar University Hackathon', 'category': 'ai', 'prize': '₹50,000'},
    {'title': 'COEP Pune Hackathon', 'category': 'iot', 'prize': '₹40,000'},
    {'title': 'MIT-WPU Hackathon', 'category': 'health', 'prize': '₹35,000'},
    {'title': 'PES University Hackathon', 'category': 'ai', 'prize': '₹45,000'},
    {'title': 'RV College of Engineering Hackathon', 'category': 'other', 'prize': '₹30,000'},
    {'title': 'BMS College of Engineering Hackathon', 'category': 'climate', 'prize': '₹25,000'},
    {'title': 'Manipal Institute of Technology Hackathon', 'category': 'edtech', 'prize': '₹50,000'},
    {'title': 'SRM University Hackathon', 'category': 'ai', 'prize': '₹40,000'},
    {'title': 'Christ University Hackathon', 'category': 'fintech', 'prize': '₹35,000'},
    {'title': 'Amrita University Hackathon', 'category': 'health', 'prize': '₹30,000'},
    {'title': 'SASTRA University Hackathon', 'category': 'other', 'prize': '₹25,000'},
    {'title': 'KIIT University Hackathon', 'category': 'edtech', 'prize': '₹40,000'},
    {'title': 'Sathyabama University Hackathon', 'category': 'iot', 'prize': '₹30,000'},
    # Thematic hackathons
    {'title': 'AI for Agriculture Hackathon', 'category': 'climate', 'prize': '₹2,00,000'},
    {'title': 'Women in Tech Hackathon', 'category': 'other', 'prize': '₹1,00,000'},
    {'title': 'Climate Tech Challenge', 'category': 'climate', 'prize': '₹5,00,000'},
    {'title': 'HealthTech Innovation Lab', 'category': 'health', 'prize': '₹3,00,000'},
    {'title': 'Fintech for All Hackathon', 'category': 'fintech', 'prize': '₹2,50,000'},
    {'title': 'Web3 Builders Hackathon', 'category': 'web3', 'prize': '₹4,00,000'},
    {'title': 'EdTech for Rural India', 'category': 'edtech', 'prize': '₹1,50,000'},
    {'title': 'Smart Cities Hackathon', 'category': 'iot', 'prize': '₹3,00,000'},
    {'title': 'Cyber Security Challenge', 'category': 'ai', 'prize': '₹2,00,000'},
    {'title': 'Space Tech Hackathon', 'category': 'iot', 'prize': '₹5,00,000'},
    {'title': 'Ocean Conservation Hack', 'category': 'climate', 'prize': '₹1,00,000'},
    {'title': 'Mental Health Hackathon', 'category': 'health', 'prize': '₹2,00,000'},
    {'title': 'Blockchain for Supply Chain', 'category': 'web3', 'prize': '₹3,00,000'},
    {'title': 'AR/VR Experience Hack', 'category': 'ar_vr', 'prize': '₹1,50,000'},
    {'title': 'Robotics Challenge India', 'category': 'iot', 'prize': '₹4,00,000'},
    {'title': 'Drone Technology Hackathon', 'category': 'iot', 'prize': '₹3,00,000'},
    {'title': '5G Innovation Lab', 'category': 'iot', 'prize': '₹5,00,000'},
    {'title': 'Quantum Computing Challenge', 'category': 'ai', 'prize': '₹2,00,000'},
    {'title': 'Open Source Contribution Fest', 'category': 'student', 'prize': '₹1,00,000'},
    {'title': 'Hack for Accessibility', 'category': 'health', 'prize': '₹1,50,000'},
    {'title': 'Data for Good Challenge', 'category': 'ai', 'prize': '₹2,00,000'},
    {'title': 'Green Energy Hackathon', 'category': 'climate', 'prize': '₹3,00,000'},
    {'title': 'E-Waste Management Hack', 'category': 'climate', 'prize': '₹1,00,000'},
    {'title': 'Water Conservation Hackathon', 'category': 'climate', 'prize': '₹2,00,000'},
    {'title': 'Smart Farming Hackathon', 'category': 'climate', 'prize': '₹1,50,000'},
    {'title': 'Digital Health Summit', 'category': 'health', 'prize': '₹3,00,000'},
    {'title': 'Payment Innovation Challenge', 'category': 'fintech', 'prize': '₹4,00,000'},
    {'title': 'InsurTech Hackathon', 'category': 'fintech', 'prize': '₹2,00,000'},
    {'title': 'Real Estate Tech Hack', 'category': 'other', 'prize': '₹1,00,000'},
    {'title': 'Travel Tech Hackathon', 'category': 'other', 'prize': '₹1,50,000'},
    # Ongoing / recurring hackathons
    {'title': 'AngelHack India {year}', 'category': 'other', 'prize': '₹2,00,000'},
    {'title': 'HackMIT', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'PennApps', 'category': 'ai', 'prize': '$6,000'},
    {'title': 'CalHacks', 'category': 'ai', 'prize': '$10,000'},
    {'title': 'TreeHacks (Stanford)', 'category': 'ai', 'prize': '$8,000'},
    {'title': 'HackHarvard', 'category': 'other', 'prize': '$5,000'},
    {'title': 'Yale Hackathon', 'category': 'other', 'prize': '$4,000'},
    {'title': 'HackPrinceton', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'HackNY', 'category': 'fintech', 'prize': '$3,000'},
    {'title': 'HackDartmouth', 'category': 'other', 'prize': '$3,000'},
    {'title': 'HackGT (Georgia Tech)', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'HackIllinois', 'category': 'ai', 'prize': '$4,000'},
    {'title': 'HackBeanpot', 'category': 'other', 'prize': '$2,000'},
    {'title': 'HackRice', 'category': 'ai', 'prize': '$4,000'},
    {'title': 'HackUMass', 'category': 'other', 'prize': '$3,000'},
    {'title': 'Boilermake (Purdue)', 'category': 'iot', 'prize': '$4,000'},
    {'title': 'HackTheNorth (Waterloo)', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'nwHacks (UBC)', 'category': 'fintech', 'prize': '$3,000'},
    {'title': 'UofTHacks (Toronto)', 'category': 'ai', 'prize': '$4,000'},
    {'title': 'McHacks (McGill)', 'category': 'other', 'prize': '$3,000'},
    {'title': 'Dubai Blockchain Hackathon', 'category': 'web3', 'prize': 'AED 50,000'},
    {'title': 'Singapore Fintech Hackathon', 'category': 'fintech', 'prize': 'SGD 10,000'},
    {'title': 'London Tech Week Hack', 'category': 'ai', 'prize': '£5,000'},
    {'title': 'Berlin Tech Summit Hack', 'category': 'other', 'prize': '€4,000'},
    {'title': 'Paris AI for Good Hack', 'category': 'ai', 'prize': '€3,000'},
    {'title': 'Amsterdam Web3 Hack', 'category': 'web3', 'prize': '€5,000'},
    {'title': 'Sydney Innovation Hack', 'category': 'climate', 'prize': 'AUD 10,000'},
    {'title': 'Tokyo Tech Challenge', 'category': 'iot', 'prize': '¥500,000'},
    # Platform-specific
    {'title': 'Devfolio Season of Hackathons', 'category': 'other', 'prize': '₹1,00,000'},
    {'title': 'Devpost Global Hackathon', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'HackerEarth Challenges', 'category': 'ai', 'prize': '₹50,000'},
    {'title': 'CodeChef Coding Challenge', 'category': 'ai', 'prize': '₹1,00,000'},
    {'title': 'HackerRank Hackathons', 'category': 'ai', 'prize': '₹75,000'},
    {'title': 'Unstop Mega Hackathon', 'category': 'other', 'prize': '₹10,00,000'},
    {'title': 'Dare2Compete National Hackathon', 'category': 'other', 'prize': '₹5,00,000'},
    {'title': 'TechGig Code Gladiators', 'category': 'ai', 'prize': '₹3,00,000'},
    {'title': 'Coding Ninjas Hackathon', 'category': 'student', 'prize': '₹1,00,000'},
    {'title': 'InterviewBit Hackathon', 'category': 'ai', 'prize': '₹50,000'},
    {'title': 'Scaler Hackathon', 'category': 'edtech', 'prize': '₹2,00,000'},
    {'title': 'UpGrad Campus Hackathon', 'category': 'edtech', 'prize': '₹1,50,000'},
    {'title': 'Great Learning Hackathon', 'category': 'edtech', 'prize': '₹1,00,000'},
    {'title': 'Simplilearn Hackathon', 'category': 'edtech', 'prize': '₹75,000'},
    # Domain-specific competitions
    {'title': 'ISRO Space Apps Challenge', 'category': 'iot', 'prize': '₹2,00,000'},
    {'title': 'DRDO Innovation Challenge', 'category': 'other', 'prize': '₹3,00,000'},
    {'title': 'NITI Aayog hackathon', 'category': 'other', 'prize': '₹5,00,000'},
    {'title': 'Startup India Innovation Week', 'category': 'other', 'prize': '₹2,00,000'},
    {'title': 'Make in India Hackathon', 'category': 'other', 'prize': '₹10,00,000'},
    {'title': 'Digital India Hackathon', 'category': 'other', 'prize': '₹5,00,000'},
    {'title': 'Skill India Hackathon', 'category': 'edtech', 'prize': '₹3,00,000'},
    {'title': 'Swachh Bharat Hackathon', 'category': 'climate', 'prize': '₹2,00,000'},
    {'title': 'Ayushman Bharat Hackathon', 'category': 'health', 'prize': '₹1,00,000'},
    {'title': 'POSHAN Abhiyaan Hackathon', 'category': 'health', 'prize': '₹50,000'},
    # Beginner-friendly
    {'title': 'First Timers Only Hackathon', 'category': 'beginner', 'prize': '₹25,000'},
    {'title': 'College Freshman Hackathon', 'category': 'beginner', 'prize': '₹30,000'},
    {'title': 'Women Who Code Hackathon', 'category': 'beginner', 'prize': '₹50,000'},
    {'title': 'GirlScript Summer of Code', 'category': 'student', 'prize': '₹40,000'},
    {'title': 'Codecademy Hackathon', 'category': 'beginner', 'prize': '$1,000'},
    {'title': 'freeCodeCamp Hackathon', 'category': 'beginner', 'prize': '$2,000'},
    {'title': 'Khan Academy Hackathon', 'category': 'edtech', 'prize': '$1,000'},
    {'title': 'LeetCode Weekly Contest', 'category': 'ai', 'prize': '₹15,000'},
    {'title': 'Codeforces Round', 'category': 'ai', 'prize': '₹10,000'},
    {'title': 'AtCoder Beginner Contest', 'category': 'beginner', 'prize': '¥10,000'},
    {'title': 'MLH Local Hack Day', 'category': 'beginner', 'prize': '₹20,000'},
    {'title': 'Hack Club Hackathon', 'category': 'student', 'prize': '₹15,000'},
    {'title': 'Replit Bounty Hunt', 'category': 'beginner', 'prize': '$500'},
    {'title': 'GitHub Game Off', 'category': 'gaming', 'prize': '$2,000'},
    {'title': 'Hacktoberfest', 'category': 'beginner', 'prize': 'T-shirt'},
    {'title': 'Advent of Code', 'category': 'ai', 'prize': 'Bragging rights'},
    {'title': 'ETH Global Hackathon', 'category': 'web3', 'prize': '$5,000'},
    {'title': 'Solana Hackathon', 'category': 'web3', 'prize': '$10,000'},
    {'title': 'Polygon BUIDL IT', 'category': 'web3', 'prize': '$5,000'},
    {'title': 'Avalanche Hackathon', 'category': 'web3', 'prize': '$5,000'},
    {'title': 'Near Horizon Hackathon', 'category': 'web3', 'prize': '$3,000'},
    {'title': 'Filecoin Hackathon', 'category': 'web3', 'prize': '$5,000'},
    {'title': 'Chainlink Hackathon', 'category': 'web3', 'prize': '$5,000'},
    # AI/ML specific
    {'title': 'Kaggle Competition - Tabular Playground', 'category': 'ai', 'prize': '$10,000'},
    {'title': 'Kaggle - NLP Challenge', 'category': 'ai', 'prize': '$15,000'},
    {'title': 'Kaggle - Computer Vision', 'category': 'ai', 'prize': '$12,000'},
    {'title': 'Hugging Face Community Challenge', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'OpenAI Research Hackathon', 'category': 'ai', 'prize': '$10,000'},
    {'title': 'Anthropic Safety Hackathon', 'category': 'ai', 'prize': '$8,000'},
    {'title': 'DeepMind Scholarship Hack', 'category': 'ai', 'prize': '£5,000'},
    {'title': 'Meta AI Hackathon', 'category': 'ai', 'prize': '$10,000'},
    {'title': 'Apple ML Challenge', 'category': 'ai', 'prize': '$5,000'},
    {'title': 'Netflix Recommendation Hack', 'category': 'ai', 'prize': '$4,000'},
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
        parser.add_argument('--count', type=int, default=30, help='Number of hackathons to generate as fallback')

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
                    'apply_url': f'https://unstop.com/hackathons/{title.lower().replace(" ", "-").replace("/", "-")}',
                    'description': f'{title} is a premier hackathon organized by {organizer}.\n\n'
                                   f'## Prizes\n- Grand Prize: {tmpl["prize"]}\n- Runner up prizes\n- Swag and goodies\n\n'
                                   f'## Why participate?\n- Work on real-world problems\n- Get noticed by top recruiters\n'
                                   f'- Network with industry experts\n- Build your portfolio',
                    'is_active': True,
                    'is_featured': random.random() > 0.7,
                }
            )
            if created_hack:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'✓ Hackathon scraper created {created} new hackathons (total: {Hackathon.objects.filter(is_active=True).count()})'
        ))
