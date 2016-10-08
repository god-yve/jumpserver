from django.conf.urls import patterns, include, url


urlpatterns = patterns('avazu.views',
    # Examples:
    url(r'^register/', 'add_registered_user', name='user_register'),
)
