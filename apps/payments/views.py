from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SubscriptionPlan, Subscription
from apps.accounts.models import Profile
from apps.affiliate.models import AffiliateReferral, COMMISSION_RATE
import hashlib
import hmac
import json


def pricing(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
    for plan in plans:
        if plan.name == 'six_month':
            plan.billing_total = plan.price * 6
            plan.savings = 299 * 6 - plan.price * 6
        elif plan.name == 'yearly':
            plan.billing_total = plan.price * 12
            plan.savings = 299 * 12 - plan.price * 12
        else:
            plan.billing_total = plan.price
            plan.savings = 0
    context = {'plans': plans}
    return render(request, 'payments/pricing.html', context)


@login_required
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    plan_id = request.POST.get('plan_id')
    plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)

    import razorpay
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order = client.order.create({
        'amount': int(plan.price * 100),
        'currency': 'INR',
        'payment_capture': 1,
    })

    Subscription.objects.create(
        user=request.user,
        plan=plan,
        razorpay_order_id=order['id'],
        amount_paid=plan.price,
    )

    return JsonResponse({
        'order_id': order['id'],
        'amount': int(plan.price * 100),
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'name': 'Jobs24X7',
        'description': f'{plan.display_name} Plan',
        'prefill': {
            'email': request.user.email,
            'contact': '',
        },
    })


@login_required
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f'{razorpay_order_id}|{razorpay_payment_id}'.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected_signature != razorpay_signature:
        return JsonResponse({'status': 'failed', 'message': 'Signature mismatch'})

    subscription = Subscription.objects.get(razorpay_order_id=razorpay_order_id)
    subscription.razorpay_payment_id = razorpay_payment_id
    subscription.is_active = True
    subscription.save()

    profile = request.user.profile
    profile.is_subscribed = True
    profile.subscription_end = subscription.end_date
    profile.save()

    ref_code = request.session.get('ref', '')
    if ref_code:
        try:
            referrer_profile = Profile.objects.get(referral_code=ref_code)
            commission = subscription.amount_paid * COMMISSION_RATE
            AffiliateReferral.objects.create(
                referrer=referrer_profile.user,
                referred_user=request.user,
                amount=subscription.amount_paid,
                commission_amount=commission,
            )
            referrer_profile.affiliate_balance += commission
            referrer_profile.total_earned += commission
            referrer_profile.save()
        except Profile.DoesNotExist:
            pass
        del request.session['ref']

    return JsonResponse({'status': 'success'})


@csrf_exempt
def razorpay_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=400)

    webhook_secret = settings.RAZORPAY_KEY_SECRET
    body = request.body
    signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')

    expected_sig = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        return HttpResponse(status=400)

    event = json.loads(body)
    if event.get('event') == 'subscription.charged':
        sub_id = event['payload']['subscription']['entity']['id']
        try:
            sub = Subscription.objects.get(razorpay_subscription_id=sub_id)
            sub.is_active = True
            sub.save()
            profile = sub.user.profile
            profile.is_subscribed = True
            profile.save()
        except Subscription.DoesNotExist:
            pass

    return HttpResponse(status=200)
