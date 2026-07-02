import re

MOBILE_UA = re.compile(r'android|iphone|ipad|ipod|blackberry|iemobile|opera mini', re.I)
SAFARI_UA = re.compile(r'safari', re.I)
SAFARI_EXCLUDE = re.compile(r'chrome|chromium|crios', re.I)

def mobile_context(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    is_mobile = bool(MOBILE_UA.search(ua))
    is_safari = bool(SAFARI_UA.search(ua)) and not bool(SAFARI_EXCLUDE.search(ua))
    return {
        'is_mobile': is_mobile,
        'is_safari': is_safari,
    }
