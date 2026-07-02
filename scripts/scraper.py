# Jobs24X7 Job Scraper Framework
# Uses Scrapy to scrape company career pages for job listings
# Add new companies to SPIDER_REGISTRY below

SPIDER_REGISTRY = {
    'stripe': {
        'url': 'https://stripe.com/jobs',
        'type': 'direct',
    },
    'vercel': {
        'url': 'https://vercel.com/careers',
        'type': 'direct',
    },
    'linear': {
        'url': 'https://linear.app/careers',
        'type': 'direct',
    },
    'retool': {
        'url': 'https://retool.com/careers',
        'type': 'direct',
    },
    'airtable': {
        'url': 'https://airtable.com/careers',
        'type': 'direct',
    },
}

from scrapy.spiders import CrawlSpider
from scrapy.http import Request
from urllib.parse import urljoin
import re


class CompanyJobSpider(CrawlSpider):
    name = 'company_jobs'

    def __init__(self, company=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_config = SPIDER_REGISTRY.get(company, {})
        self.company_name = company
        if self.company_config:
            self.start_urls = [self.company_config['url']]

    def parse(self, response):
        potential_links = response.css('a[href*="job"], a[href*="career"], a[href*="position"], a[href*="opening"]::attr(href)').getall()
        for link in potential_links[:20]:
            yield Request(
                url=urljoin(response.url, link),
                callback=self.parse_job,
                meta={'source_company': self.company_name}
            )

    def parse_job(self, response):
        title = response.css('h1::text, title::text').get('')
        title = re.sub(r'\s*\|.*$', '', title).strip()

        if not title or len(title) < 5:
            return

        description = ' '.join(response.css('p::text, li::text, div.description *::text').getall()).strip()[:5000]

        yield {
            'title': title,
            'company': self.company_name.title() if self.company_name else '',
            'description': description,
            'apply_url': response.url,
            'source_url': response.url,
            'source_company': self.company_name or '',
        }
