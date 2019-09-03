# -*- coding: utf-8 -*-

from django.views.generic import TemplateView


class MapNew(TemplateView):
    template_name = "geoloc/geoloc.html"
