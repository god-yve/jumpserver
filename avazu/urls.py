from django.conf.urls import patterns, include, url


urlpatterns = patterns('avazu.views',
    # Examples:
    url(r'^register/$', 'add_registered_user', name='user_register'),
    url(r'^register/list/$', 'list_registered_user', name='list_registered_user'),
    url(r'^register/add/$', 'add_register', name='add_register'),
    url(r'^register/del/$', 'del_register', name='del_register'),
    url(r'^host/add/$', 'add_applyhost', name='add_applyhost'),
    url(r'^host/del/$', 'del_applyhost', name='del_applyhost'),
    url(r'^assets/apply$', 'asset_apply', name='asset_apply'),

)
