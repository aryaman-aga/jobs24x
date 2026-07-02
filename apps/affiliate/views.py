from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AffiliateReferral
from apps.accounts.models import Profile


def affiliate_home(request):
    return render(request, 'affiliate/affiliate_home.html')


@login_required
def affiliate_dashboard(request):
    profile = request.user.profile
    referrals = AffiliateReferral.objects.filter(referrer=request.user)
    total_referrals = referrals.count()
    total_commission = sum(r.commission_amount for r in referrals.filter(status='paid'))

    context = {
        'profile': profile,
        'referrals': referrals,
        'total_referrals': total_referrals,
        'total_commission': total_commission,
        'referral_link': request.build_absolute_uri('/') + f'?ref={profile.referral_code}',
    }
    return render(request, 'affiliate/affiliate_dashboard.html', context)
