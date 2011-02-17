from django.conf import settings

def parent_site(request):
    return {'logo_url': settings.LOGO_URL,
            'parent_site_url': settings.PARENT_SITE_URL}
