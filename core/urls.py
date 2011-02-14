from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('core.views',
    url(
        regex=r'^$',
        view='settings_edit',
        name='settings_edit'),
    url(
        regex=r'^change_password/$',
        view='change_password',
        name='change_password'),
    url(
        regex=r'^subscribe/$',
        view='subscribe',
        name='subscribe'),
    url(
        regex=r'^subscription_paid/$',
        view='subscription_paid',
        name='subscription_paid'),
    url(
        regex=r'^paypal_ipn/$',
        view='paypal_ipn',
        name='paypal_ipn'),
)
