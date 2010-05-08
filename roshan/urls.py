from django.conf.urls.defaults import *
from roshan.roshanapp import views as rv
import roshan.settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^roshan/', include('roshan.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    
    (r'^$', rv.index),
    (r'^islogin/$', rv.islogin),
    (r'^getlogin/$', rv.getlogin),
    (r'^login/$', rv.login),
    (r'^logout/$', rv.logout),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': roshan.settings.MEDIA_ROOT}),
    (r'^server/list', rv.serverlist),
    (r'^server/stat/([\w\d\-\.]+).*', rv.serverstat),
    (r'^node/list/(.*)', rv.children),
    (r'^node/get/(.*)', rv.get),
    (r'^node/add/(.*)', rv.add),
    (r'^node/update/(.*)', rv.update),
    (r'^node/delete/(.*)', rv.delete),
)
