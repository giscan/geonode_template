import json
from copy import copy

from django import template
from django.conf import settings

from models import DataLayer, TileLayer
from ..views import _urls_for_js

register = template.Library()


@register.inclusion_tag('umap/css.html')
def umap_css():
    return {
        "STATIC_URL": settings.STATIC_URL
    }


@register.inclusion_tag('umap/js.html')
def umap_js(locale=None):
    return {
        "STATIC_URL": settings.STATIC_URL,
        "locale": locale
    }


@register.filter
def notag(s):
    return s.replace('<', '&lt;')




@register.filter
def ipdb(what):
    import ipdb
    ipdb.set_trace()
    return ''
