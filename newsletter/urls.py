from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('newsletter.views',
    # admin stuff
    url(
        regex=r'^email_users/$',
        view='email_users',
        name='email_users'),
    url(
        regex=r'^email_users/(?P<message_id>\d+)/$',
        view='email_users',
        name='email_users'),
    url(
        regex=r'^email_delete/(?P<id>\d+)/$',
        view='email_delete',
        name='email_delete'),
)
