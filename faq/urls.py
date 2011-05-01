from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('faq.views',

    url(regex=r'^$',
        view='faq_list',
        name='faq_list'),
)
