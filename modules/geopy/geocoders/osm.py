import simplejson
from urllib import urlencode
from urllib2 import urlopen, HTTPError
from geopy import util
from geopy import Point, Location
from geopy.geocoders.base import Geocoder


class OSMGazetteer(Geocoder):
    
    BASE_URL = "http://nominatim.openstreetmap.org/?%s"

    def __init__(self, format_string='%s', viewbox=(-180,-90,180,90)):
        self.format_string = format_string
        self.viewbox = ','.join(map(str, viewbox))
        self.output_format = 'json'

    def geocode(self, string):
        params = {'q': self.format_string % string,
                  'format': self.output_format,
                  'viewbox': self.viewbox
                 }
        url = self.BASE_URL % urlencode(params)
        return self.geocode_url(url)

    def geocode_url(self, url):
        print "Fetching %s..." % url
        page = urlopen(url).read()

        parse = getattr(self, 'parse_' + self.output_format)
        return parse(page)

    def parse_json(self, page):
        attribution, sep, page = page.partition("\n")
        results = simplejson.loads(page)
        
        def parse_result(result):
            location = result.get('display_name')
            latitude = result.get('lat')
            longitude = result.get('lon')
            if latitude and longitude:
                point = Point(latitude, longitude)
            else:
                point = None
            return Location(location, point, result)

        return [parse_result(result) for result in results]
