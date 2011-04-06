from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('backup.views',
    url(regex=r'^$',
        view='backup',
        name='backup'),
    url(regex=r'^download/$',
        view='backup_download',
        name='backup_download'),
)
