from django.conf.urls import url

from .views import MapNew

urlpatterns = [
    url(r'^(?P<slug>[-\w]+)/$', MapNew.as_view(), name='new_point'),
]
