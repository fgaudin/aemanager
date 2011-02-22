from django.conf.urls.defaults import *

from django.contrib import admin
from django.conf import settings
from core.views import resend_activation_email, contact_us
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(regex=r'^$',
        view='core.views.index',
        name='index'),
    url(regex=r'^contact_us/$',
        view=contact_us,
        name='contact_us'),
    url(regex=r'^contact/sent/$',
        view='django.views.generic.simple.direct_to_template',
        name='message_sent',
        kwargs={'template': 'core/message_sent.html'}),
    url(regex=r'^logout/$',
        view='django.contrib.auth.views.logout',
        name='logout',
        kwargs={'next_page': '/'}),
    url(regex=r'^resend_activation_email/$',
        view=resend_activation_email,
        name='resend_activation_email'),
    url(regex=r'^tos/$',
        view='django.views.generic.simple.direct_to_template',
        name='tos',
        kwargs={'template': 'tos.html'}),
    url(r'^home/', include('core.urls')),
    url(r'^contact/', include('contact.urls')),
    url(r'^project/', include('project.urls')),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^issues/', include('bugtracker.urls')),
    url(r'^user/', include('registration_urls')),

)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
