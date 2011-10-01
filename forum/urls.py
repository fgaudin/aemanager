from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('forum.views',

    url(regex=r'^$',
        view='topic_list',
        name='topic_list'),
    url(regex=r'^topic/add/$',
        view='topic_create',
        name='topic_create'),
    url(regex=r'^topic/detail/(?P<id>\d+)/$',
        view='topic_detail',
        name='topic_detail'),
)
