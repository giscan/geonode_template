from .models import TileLayer, DataLayer, Map


class GeolocRouter(object):

    def db_for_read(self, model, **hints):

        """ reading models from datastore """
        if model in [TileLayer, DataLayer, Map]:
            return 'datastore'
        return None

    def db_for_write(self, model, **hints):

        """ writing models to datastore """
        if model in [TileLayer, DataLayer, Map]:
            return 'datastore'
        return None

