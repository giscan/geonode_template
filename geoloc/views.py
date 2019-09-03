# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.http import (
                         HttpResponseForbidden,
                         HttpResponsePermanentRedirect,
                         )
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, TemplateView
from .forms import (
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    AnonymousMapPermissionsForm,
    )

from .models import DataLayer, Licence, Map, TileLayer
from .utils import get_uri_template

# Create your views here.


def _urls_for_js(urls=None):
    """
    Return templated URLs prepared for javascript.
    """
    if urls is None:
        # prevent circular import
        from .urls import urlpatterns
        urls = [url.name for url in urlpatterns
                if getattr(url, 'name', None)]
    urls = dict(zip(urls, [get_uri_template(url) for url in urls]))
    urls.update(getattr(settings, 'UMAP_EXTRA_URLS', {}))
    return urls


class MapDetailMixin(object):

    model = Map

    def get_context_data(self, **kwargs):
        context = super(MapDetailMixin, self).get_context_data(**kwargs)
        properties = {
            'urls': _urls_for_js(),
            'tilelayers': TileLayer.get_list(),
            'allowEdit': self.is_edit_allowed(),
            'default_iconUrl': "%sumap/img/marker.png" % settings.STATIC_URL,  # noqa
            'umap_id': self.get_umap_id(),
            'licences': dict((l.name, l.json) for l in Licence.objects.all()),
            'edit_statuses': [(i, str(label)) for i, label in Map.EDIT_STATUS],
            'share_statuses': [(i, str(label))
                               for i, label in Map.SHARE_STATUS if i != Map.BLOCKED],
            'anonymous_edit_statuses': [(i, str(label)) for i, label
                                        in AnonymousMapPermissionsForm.STATUS],
        }
        if self.get_short_url():
            properties['shortUrl'] = self.get_short_url()

        if settings.USE_I18N:
            locale = settings.LANGUAGE_CODE
            # Check attr in case the middleware is not active
            if hasattr(self.request, "LANGUAGE_CODE"):
                locale = self.request.LANGUAGE_CODE
            properties['locale'] = locale
            context['locale'] = locale
        user = self.request.user
        if not user.is_anonymous:
            properties['user'] = {
                'id': user.pk,
                'name': user.get_username(),
                'url': reverse(settings.USER_MAPS_URL,
                               args=(user.get_username(), ))
            }
        map_settings = self.get_geojson()
        if "properties" not in map_settings:
            map_settings['properties'] = {}
        map_settings['properties'].update(properties)
        map_settings['properties']['datalayers'] = self.get_datalayers()
        context['map_settings'] = json.dumps(map_settings,
                                             indent=settings.DEBUG)
        return context

    def get_datalayers(self):
        return []

    def is_edit_allowed(self):
        return True

    def get_umap_id(self):
        return None

    def get_geojson(self):
        return {
            "geometry": {
                "coordinates": [DEFAULT_LONGITUDE, DEFAULT_LATITUDE],
                "type": "Point"
            },
            "properties": {
                "zoom": getattr(settings, 'LEAFLET_ZOOM', 6),
                "datalayers": [],
            }
        }

    def get_short_url(self):
        return None


class MapView(MapDetailMixin, DetailView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        canonical = self.get_canonical_url()
        if not request.path == canonical:
            if request.META.get('QUERY_STRING'):
                canonical = "?".join([canonical, request.META['QUERY_STRING']])
            return HttpResponsePermanentRedirect(canonical)
        if not self.object.can_view(request):
            return HttpResponseForbidden()
        return super(MapView, self).get(request, *args, **kwargs)

    def get_canonical_url(self):
        return self.object.get_absolute_url()

    def get_datalayers(self):
        datalayers = DataLayer.objects.filter(map=self.object)
        return [l.metadata for l in datalayers]

    def is_edit_allowed(self):
        return self.object.can_edit(self.request.user, self.request)

    def get_umap_id(self):
        return self.object.pk

    def get_short_url(self):
        shortUrl = None
        if hasattr(settings, 'SHORT_SITE_URL'):
            short_path = reverse_lazy('map_short_url',
                                      kwargs={'pk': self.object.pk})
            shortUrl = "%s%s" % (settings.SHORT_SITE_URL, short_path)
        return shortUrl

    def get_geojson(self):
        map_settings = self.object.settings
        if "properties" not in map_settings:
            map_settings['properties'] = {}
        map_settings['properties']['name'] = self.object.name
        map_settings['properties']['permissions'] = self.get_permissions()
        return map_settings


class MapNew(MapDetailMixin, TemplateView):
    template_name = "geoloc/map_detail.html"
