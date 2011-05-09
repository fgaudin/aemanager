from django.conf import settings

def common(request=None):
    return {'logo_url': settings.LOGO_URL,
            'parent_site_url': settings.PARENT_SITE_URL,
            'version': '1.2',
            'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,
            'demo_mode': settings.DEMO}
