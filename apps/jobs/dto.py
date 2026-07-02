from dataclasses import dataclass, asdict
from typing import Optional, List
from django.db import models
from django.db.models import Case, When, Value, IntegerField, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Job, SavedJob, CATEGORY_CHOICES, EXPERIENCE_CHOICES


@dataclass
class JobCardDTO:
    pk: int
    title: str
    company: str
    location: str
    remote: bool
    salary_min: Optional[float]
    salary_max: Optional[float]
    experience_level: str
    experience_display: str
    category: str
    is_free: bool
    is_saved: bool
    is_locked: bool


@dataclass
class JobDetailDTO:
    pk: int
    title: str
    company: str
    company_logo: str
    company_url: str
    location: str
    country: str
    remote: bool
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: str
    experience_level: str
    experience_display: str
    category: str
    category_display: str
    description: str
    apply_url: str
    source_company: str
    posted_at: Optional[str]
    can_view_details: bool
    is_free_preview: bool
    is_saved: bool
    is_subscriber_only: bool


@dataclass
class PaginatedResult:
    items: List[dict]
    page: int
    total_pages: int
    total_count: int
    has_next: bool
    has_previous: bool


class JobTranslator:
    """Translates Job model instances to lightweight DTOs for API responses."""

    FREE_PREVIEW_COUNT = 3

    @staticmethod
    def get_free_preview_ids(jobs_queryset):
        return set(jobs_queryset.values_list('pk', flat=True)[:JobTranslator.FREE_PREVIEW_COUNT])

    @staticmethod
    def get_saved_ids(user, job_ids=None):
        if not user.is_authenticated:
            return set()
        qs = SavedJob.objects.filter(user=user)
        if job_ids:
            qs = qs.filter(job_id__in=job_ids)
        return set(qs.values_list('job_id', flat=True))

    @staticmethod
    def get_subscribed(user):
        if not user.is_authenticated:
            return False
        profile = user.profile
        return profile.is_subscribed and (
            not profile.subscription_end or profile.subscription_end > timezone.now()
        )

    @classmethod
    def to_card_dto(cls, job, free_preview_ids, saved_ids, is_subscribed):
        is_free = job.pk in free_preview_ids
        is_locked = not is_free and not is_subscribed
        return JobCardDTO(
            pk=job.pk,
            title=job.title,
            company=job.company,
            location=job.location or '',
            remote=job.remote,
            salary_min=float(job.salary_min) if job.salary_min else None,
            salary_max=float(job.salary_max) if job.salary_max else None,
            experience_level=job.experience_level,
            experience_display=job.get_experience_level_display() if job.experience_level else '',
            category=job.category,
            is_free=is_free,
            is_saved=job.pk in saved_ids,
            is_locked=is_locked,
        )

    @classmethod
    def card_list(cls, jobs, free_preview_ids, saved_ids, is_subscribed):
        return [cls.to_card_dto(j, free_preview_ids, saved_ids, is_subscribed) for j in jobs]

    @classmethod
    def to_detail_dto(cls, job, is_free_preview, is_saved, can_view_details):
        return JobDetailDTO(
            pk=job.pk,
            title=job.title,
            company=job.company,
            company_logo=job.company_logo or '',
            company_url=job.company_url or '',
            location=job.location or '',
            country=job.country or '',
            remote=job.remote,
            salary_min=float(job.salary_min) if job.salary_min else None,
            salary_max=float(job.salary_max) if job.salary_max else None,
            salary_currency=job.salary_currency or 'INR',
            experience_level=job.experience_level,
            experience_display=job.get_experience_level_display() if job.experience_level else '',
            category=job.category,
            category_display=job.get_category_display() if job.category else '',
            description=job.description or '',
            apply_url=job.apply_url,
            source_company=job.source_company or job.company,
            posted_at=job.posted_at.isoformat() if job.posted_at else None,
            can_view_details=can_view_details,
            is_free_preview=is_free_preview,
            is_saved=is_saved,
            is_subscriber_only=not is_free_preview,
        )

    @classmethod
    def paginate(cls, serializer_func, page_obj):
        return PaginatedResult(
            items=[asdict(serializer_func(item)) for item in page_obj.object_list],
            page=page_obj.number,
            total_pages=page_obj.paginator.num_pages,
            total_count=page_obj.paginator.count,
            has_next=page_obj.has_next(),
            has_previous=page_obj.has_previous(),
        )


class JobQueryHelper:
    """Optimized query builder with India-first ordering and eager-loading."""

    INDIAN_LOCATIONS = [
        'India', 'Bangalore', 'Mumbai', 'Delhi', 'Pune',
        'Hyderabad', 'Chennai', 'Kolkata', 'Gurgaon', 'Noida',
    ]

    @classmethod
    def base_query(cls):
        return Job.objects.filter(is_active=True).select_related().defer(
            'description', 'company_logo', 'company_url', 'source_url'
        )

    @classmethod
    def apply_filters(cls, qs, category='', experience='', search='', remote='', location=''):
        if category:
            qs = qs.filter(category=category)
        if experience:
            qs = qs.filter(experience_level=experience)
        if remote == 'true':
            qs = qs.filter(remote=True)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(company__icontains=search)
            )
        if location:
            qs = qs.filter(
                Q(location__icontains=location) |
                Q(country__icontains=location)
            )
        else:
            india_cases = []
            for i, loc in enumerate(cls.INDIAN_LOCATIONS):
                india_cases.append(
                    When(location__icontains=loc, then=Value(i))
                )
            india_cases.append(When(country='IN', then=Value(0)))
            qs = qs.annotate(
                india_boost=Case(
                    *india_cases,
                    default=Value(len(cls.INDIAN_LOCATIONS)),
                    output_field=IntegerField(),
                )
            ).order_by('india_boost', '-is_featured', '-posted_at', '-created_at')
        return qs
