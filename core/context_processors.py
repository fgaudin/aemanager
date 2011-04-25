from django.conf import settings

def parent_site(request):
    return {'logo_url': settings.LOGO_URL,
            'parent_site_url': settings.PARENT_SITE_URL}

def version(request=None):
    return {'version': '1.1.1'}

def google_api_key(request):
    return {'GOOGLE_API_KEY': settings.GOOGLE_API_KEY}
