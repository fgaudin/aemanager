from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('core.views',
    url(
        regex=r'^$',
        view='settings_edit',
        name='settings_edit'),
)
