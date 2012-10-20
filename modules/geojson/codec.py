# ============================================================================
# GeoJSON. Copyright (C) 2007 Sean C. Gillies
#
# See ../LICENSE.txt
# 
# Contact: Sean Gillies, sgillies@frii.com
# ============================================================================

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

import factory
from mapping import Mapping, to_mapping


class GeoJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Mapping):
            mapping = obj
        else:
            mapping = to_mapping(obj)
        d = dict(mapping)
        type_str = d.pop("type", None)
        if type_str:
            geojson_factory = getattr(factory, type_str, factory.GeoJSON)
            d = geojson_factory(**d).__geo_interface__
        return d


# Wrap the functions from simplejson, providing encoder, decoders, and
# object creation hooks

def dump(obj, fp, cls=GeoJSONEncoder, **kwargs):
    return json.dump(to_mapping(obj), fp, cls=cls, **kwargs)


def dumps(obj, cls=GeoJSONEncoder, **kwargs):
    return json.dumps(to_mapping(obj), cls=cls, **kwargs)


def load(fp, cls=json.JSONDecoder, object_hook=None, **kwargs):
    return json.load(fp, cls=cls, object_hook=object_hook, **kwargs)


def loads(s, cls=json.JSONDecoder, object_hook=None, **kwargs):
    return json.loads(s, cls=cls, object_hook=object_hook, **kwargs)

# Backwards compatibility
PyGFPEncoder = GeoJSONEncoder
