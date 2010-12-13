from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('accounts.views',

    # expenses
    url(regex=r'^expenses/$',
        view='expense_list',
        name='expense_list'),
    url(regex=r'^expenses/add/$',
        view='expense_add',
        name='expense_add'),
    url(regex=r'^expenses/edit/$',
        view='expense_edit',
        name='expense_edit'),
    url(regex=r'^expenses/delete/$',
        view='expense_delete',
        name='expense_delete'),
)
