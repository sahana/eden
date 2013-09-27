# -*- coding: utf-8 -*-

""" GIS Module

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @copyright: (c) 2010-2013 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["GIS",
           "S3Map",
           "S3ExportPOI",
           "S3ImportPOI",
           ]

import os
import re
import sys
#import logging
import urllib           # Needed for urlencoding
import urllib2          # Needed for quoting & error handling on fetch
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
from datetime import timedelta  # Needed for Feed Refresh checks

try:
    from lxml import etree # Needed to follow NetworkLinks
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

KML_NAMESPACE = "http://earth.google.com/kml/2.2"

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import *
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.html import *
#from gluon.http import HTTP, redirect
from gluon.dal import Rows
from gluon.storage import Storage, Messages

from s3fields import s3_all_meta_field_names
from s3rest import S3Method
from s3track import S3Trackable
from s3track import S3Trackable
from s3utils import s3_debug, s3_fullname, s3_fullname_bulk, s3_has_foreign_key, s3_include_ext

DEBUG = False
if DEBUG:
    import datetime
    print >> sys.stderr, "S3GIS: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# Map WKT types to db types
GEOM_TYPES = {"point": 1,
              "linestring": 2,
              "polygon": 3,
              "multipoint": 4,
              "multilinestring": 5,
              "multipolygon": 6,
              "geometrycollection": 7,
              }

# km
RADIUS_EARTH = 6371.01

# Compact JSON encoding
SEPARATORS = (",", ":")

# Map Defaults
# Also in static/S3/s3.gis.js
# http://dev.openlayers.org/docs/files/OpenLayers/Strategy/Cluster-js.html
CLUSTER_ATTRIBUTE = "colour"
CLUSTER_DISTANCE = 20   # pixels
CLUSTER_THRESHOLD = 2   # minimum # of features to form a cluster

# Garmin GPS Symbols
GPS_SYMBOLS = ["Airport",
               "Amusement Park"
               "Ball Park",
               "Bank",
               "Bar",
               "Beach",
               "Bell",
               "Boat Ramp",
               "Bowling",
               "Bridge",
               "Building",
               "Campground",
               "Car",
               "Car Rental",
               "Car Repair",
               "Cemetery",
               "Church",
               "Circle with X",
               "City (Capitol)",
               "City (Large)",
               "City (Medium)",
               "City (Small)",
               "Civil",
               "Contact, Dreadlocks",
               "Controlled Area",
               "Convenience Store",
               "Crossing",
               "Dam",
               "Danger Area",
               "Department Store",
               "Diver Down Flag 1",
               "Diver Down Flag 2",
               "Drinking Water",
               "Exit",
               "Fast Food",
               "Fishing Area",
               "Fitness Center",
               "Flag",
               "Forest",
               "Gas Station",
               "Geocache",
               "Geocache Found",
               "Ghost Town",
               "Glider Area",
               "Golf Course",
               "Green Diamond",
               "Green Square",
               "Heliport",
               "Horn",
               "Hunting Area",
               "Information",
               "Levee",
               "Light",
               "Live Theater",
               "Lodging",
               "Man Overboard",
               "Marina",
               "Medical Facility",
               "Mile Marker",
               "Military",
               "Mine",
               "Movie Theater",
               "Museum",
               "Navaid, Amber",
               "Navaid, Black",
               "Navaid, Blue",
               "Navaid, Green",
               "Navaid, Green/Red",
               "Navaid, Green/White",
               "Navaid, Orange",
               "Navaid, Red",
               "Navaid, Red/Green",
               "Navaid, Red/White",
               "Navaid, Violet",
               "Navaid, White",
               "Navaid, White/Green",
               "Navaid, White/Red",
               "Oil Field",
               "Parachute Area",
               "Park",
               "Parking Area",
               "Pharmacy",
               "Picnic Area",
               "Pizza",
               "Post Office",
               "Private Field",
               "Radio Beacon",
               "Red Diamond",
               "Red Square",
               "Residence",
               "Restaurant",
               "Restricted Area",
               "Restroom",
               "RV Park",
               "Scales",
               "Scenic Area",
               "School",
               "Seaplane Base",
               "Shipwreck",
               "Shopping Center",
               "Short Tower",
               "Shower",
               "Skiing Area",
               "Skull and Crossbones",
               "Soft Field",
               "Stadium",
               "Summit",
               "Swimming Area",
               "Tall Tower",
               "Telephone",
               "Toll Booth",
               "TracBack Point",
               "Trail Head",
               "Truck Stop",
               "Tunnel",
               "Ultralight Area",
               "Water Hydrant",
               "Waypoint",
               "White Buoy",
               "White Dot",
               "Zoo"
               ]

# -----------------------------------------------------------------------------
class GIS(object):
    """
        GeoSpatial functions
    """

    def __init__(self):
        messages = current.messages
        #messages.centroid_error = str(A("Shapely", _href="http://pypi.python.org/pypi/Shapely/", _target="_blank")) + " library not found, so can't find centroid!"
        messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        messages.unknown_type = "Unknown Type!"
        messages.invalid_wkt_point = "Invalid WKT: must be like POINT(3 4)"
        messages.invalid_wkt = "Invalid WKT: see http://en.wikipedia.org/wiki/Well-known_text"
        messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.DEFAULT_SYMBOL = "White Dot"
        self.hierarchy_level_keys = ["L0", "L1", "L2", "L3", "L4", "L5"]
        self.hierarchy_levels = {}
        self.max_allowed_level_num = 4

    # -------------------------------------------------------------------------
    @staticmethod
    def gps_symbols():
        return GPS_SYMBOLS

    # -------------------------------------------------------------------------
    def download_kml(self, record_id, filename, session_id_name, session_id):
        """
            Download a KML file:
                - unzip it if-required
                - follow NetworkLinks recursively if-required

            Save the file to the /uploads folder

            Designed to be called asynchronously using:
                current.s3task.async("download_kml", [record_id, filename])

            @param record_id: id of the record in db.gis_layer_kml
            @param filename: name to save the file as
            @param session_id_name: name of the session
            @param session_id: id of the session

            @ToDo: Pass error messages to Result & have JavaScript listen for these
        """

        request = current.request

        table = current.s3db.gis_layer_kml
        record = current.db(table.id == record_id).select(table.url,
                                                          limitby=(0, 1)
                                                          ).first()
        url = record.url

        filepath = os.path.join(request.global_settings.applications_parent,
                                request.folder,
                                "uploads",
                                "gis_cache",
                                filename)

        warning = self.fetch_kml(url, filepath, session_id_name, session_id)

        # @ToDo: Handle errors
        #query = (cachetable.name == name)
        if "URLError" in warning or "HTTPError" in warning:
            # URL inaccessible
            if os.access(filepath, os.R_OK):
                statinfo = os.stat(filepath)
                if statinfo.st_size:
                    # Use cached version
                    #date = db(query).select(cachetable.modified_on,
                    #                        limitby=(0, 1)).first().modified_on
                    #response.warning += "%s %s %s\n" % (url,
                    #                                    T("not accessible - using cached version from"),
                    #                                    str(date))
                    #url = URL(c="default", f="download",
                    #          args=[filename])
                    pass
                else:
                    # 0k file is all that is available
                    #response.warning += "%s %s\n" % (url,
                    #                                 T("not accessible - no cached version available!"))
                    # skip layer
                    return
            else:
                # No cached version available
                #response.warning += "%s %s\n" % (url,
                #                                 T("not accessible - no cached version available!"))
                # skip layer
                return
        else:
            # Download was succesful
            #db(query).update(modified_on=request.utcnow)
            if "ParseError" in warning:
                # @ToDo Parse detail
                #response.warning += "%s: %s %s\n" % (T("Layer"),
                #                                     name,
                #                                     T("couldn't be parsed so NetworkLinks not followed."))
                pass
            if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                #response.warning += "%s: %s %s\n" % (T("Layer"),
                #                                     name,
                #                                     T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly."))
                # Code to support GroundOverlay:
                # https://github.com/openlayers/openlayers/pull/759
                pass

    # -------------------------------------------------------------------------
    def fetch_kml(self, url, filepath, session_id_name, session_id):
        """
            Fetch a KML file:
                - unzip it if-required
                - follow NetworkLinks recursively if-required

            Returns a file object

            Designed as a helper function for download_kml()
        """

        from gluon.tools import fetch

        response = current.response
        public_url = current.deployment_settings.get_base_public_url()

        warning = ""

        local = False
        if not url.startswith("http"):
            local = True
            url = "%s%s" % (public_url, url)
        elif len(url) > len(public_url) and url[:len(public_url)] == public_url:
            local = True
        if local:
            # Keep Session for local URLs
            import Cookie
            cookie = Cookie.SimpleCookie()
            cookie[session_id_name] = session_id
            # For sync connections
            current.session._unlock(response)
            try:
                file = fetch(url, cookie=cookie)
            except urllib2.URLError:
                warning = "URLError"
                return warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return warning
        else:
            try:
                file = fetch(url)
            except urllib2.URLError:
                warning = "URLError"
                return warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return warning

        filenames = []
        if file[:2] == "PK":
            # Unzip
            fp = StringIO(file)
            import zipfile
            myfile = zipfile.ZipFile(fp)
            files = myfile.infolist()
            main = None
            candidates = []
            for _file in files:
                filename = _file.filename
                if filename == "doc.kml":
                    main = filename
                elif filename[-4:] == ".kml":
                    candidates.append(filename)
            if not main:
                if candidates:
                    # Any better way than this to guess which KML file is the main one?
                    main = candidates[0]
                else:
                    response.error = "KMZ contains no KML Files!"
                    return ""
            # Write files to cache (other than the main one)
            request = current.request
            path = os.path.join(request.folder, "static", "cache", "kml")
            if not os.path.exists(path):
                os.makedirs(path)
            for _file in files:
                filename = _file.filename
                if filename != main:
                    if "/" in filename:
                        _filename = filename.split("/")
                        dir = os.path.join(path, _filename[0])
                        if not os.path.exists(dir):
                            os.mkdir(dir)
                        _filepath = os.path.join(path, *_filename)
                    else:
                        _filepath = os.path.join(path, filename)

                    try:
                        f = open(_filepath, "wb")
                    except:
                        # Trying to write the Folder
                        pass
                    else:
                        filenames.append(filename)
                        __file = myfile.read(filename)
                        f.write(__file)
                        f.close()

            # Now read the main one (to parse)
            file = myfile.read(main)
            myfile.close()

        # Check for NetworkLink
        if "<NetworkLink>" in file:
            try:
                # Remove extraneous whitespace
                parser = etree.XMLParser(recover=True, remove_blank_text=True)
                tree = etree.XML(file, parser)
                # Find contents of href tag (must be a better way?)
                url = ""
                for element in tree.iter():
                    if element.tag == "{%s}href" % KML_NAMESPACE:
                        url = element.text
                if url:
                    # Follow NetworkLink (synchronously)
                    warning2 = self.fetch_kml(url, filepath)
                    warning += warning2
            except (etree.XMLSyntaxError,):
                e = sys.exc_info()[1]
                warning += "<ParseError>%s %s</ParseError>" % (e.line, e.errormsg)

        # Check for Overlays
        if "<GroundOverlay>" in file:
            warning += "GroundOverlay"
        if "<ScreenOverlay>" in file:
            warning += "ScreenOverlay"

        for filename in filenames:
            replace = "%s/%s" % (URL(c="static", f="cache", args=["kml"]),
                                 filename)
            # Rewrite all references to point to the correct place
            # need to catch <Icon><href> (which could be done via lxml)
            # & also <description><![CDATA[<img src=" (which can't)
            file = file.replace(filename, replace)

        # Write main file to cache
        f = open(filepath, "w")
        f.write(file)
        f.close()

        return warning

    # -------------------------------------------------------------------------
    @staticmethod
    def geocode(address, postcode=None, Lx_ids=None, geocoder="google"):
        """
            Geocode an Address
            - used by S3LocationSelectorWidget2
                      settings.get_gis_geocode_imported_addresses

            @param address: street address
            @param postcode: postcode
            @param Lx_ids: list of ancestor IDs
            @param geocoder: which geocoder service to use
        """

        from geopy import geocoders

        if geocoder == "google":
            g = geocoders.GoogleV3()
        elif geocoder == "yahoo":
            apikey = current.deployment_settings.get_gis_api_yahoo()
            g = geocoders.Yahoo(apikey)
        else:
            # @ToDo
            raise NotImplementedError

        location = address
        if postcode:
            location = "%s,%s" % (location, postcode)

        L5 = L4 = L3 = L2 = L1 = L0 = None
        if Lx_ids:
            # Convert Lx IDs to Names
            table = current.s3db.gis_location
            limit = len(Lx_ids)
            if limit > 1:
                query = (table.id.belongs(Lx_ids))
            else:
                query = (table.id == Lx_ids[0])
            db = current.db
            Lx = db(query).select(table.id,
                                  table.name,
                                  table.level,
                                  table.gis_feature_type,
                                  # Better as separate query
                                  #table.lon_min,
                                  #table.lat_min,
                                  #table.lon_max,
                                  #table.lat_max,
                                  # Better as separate query
                                  #table.wkt,
                                  limitby=(0, limit),
                                  orderby=~table.level
                                  )
            if Lx:
                Lx_names = ",".join([l.name for l in Lx])
                location = "%s,%s" % (location, Lx_names)
                for l in Lx:
                    if l.level == "L0":
                        L0 = l.id
                        continue
                    elif l.level == "L1":
                        L1 = l.id
                        continue
                    elif l.level == "L2":
                        L2 = l.id
                        continue
                    elif l.level == "L3":
                        L3 = l.id
                        continue
                    elif l.level == "L4":
                        L4 = l.id
                        continue
                    elif l.level == "L5":
                        L5 = l.id
                Lx = Lx.as_dict()

        try:
            results = g.geocode(location, exactly_one=False)
            if len(results) == 1:
                place, (lat, lon) = results[0]
                if Lx:
                    # Check Results are for a specific address & not just that for the City
                    results = g.geocode(Lx_names, exactly_one=False)
                    if len(results) == 1:
                        place2, (lat2, lon2) = results[0]
                        if place == place2:
                            results = "We can only geocode to the Lx"
                        else:
                            if Lx:
                                # Check Results are within relevant bounds
                                L0_row = None
                                wkt = None
                                if L5 and Lx[L5]["gis_feature_type"] != 1:
                                    wkt = db(table.id == L5).select(table.wkt,
                                                                    limitby=(0, 1)
                                                                    ).first().wkt
                                    used_Lx = "L5"
                                elif L4 and Lx[L4]["gis_feature_type"] != 1:
                                    wkt = db(table.id == L4).select(table.wkt,
                                                                    limitby=(0, 1)
                                                                    ).first().wkt
                                    used_Lx = "L4"
                                elif L3 and Lx[L3]["gis_feature_type"] != 1:
                                    wkt = db(table.id == L3).select(table.wkt,
                                                                    limitby=(0, 1)
                                                                    ).first().wkt
                                    used_Lx = "L3"
                                elif L2 and Lx[L2]["gis_feature_type"] != 1:
                                    wkt = db(table.id == L2).select(table.wkt,
                                                                    limitby=(0, 1)
                                                                    ).first().wkt
                                    used_Lx = "L2"
                                elif L1 and Lx[L1]["gis_feature_type"] != 1:
                                    wkt = db(table.id == L1).select(table.wkt,
                                                                    limitby=(0, 1)
                                                                    ).first().wkt
                                    used_Lx = "L1"
                                elif L0:
                                    L0_row = db(table.id == L0).select(table.wkt,
                                                                       table.lon_min,
                                                                       table.lat_min,
                                                                       table.lon_max,
                                                                       table.lat_max,
                                                                       limitby=(0, 1)
                                                                       ).first()
                                    wkt = L0_row.wkt
                                    used_Lx = "L0"
                                if wkt:
                                    from shapely.geometry import point
                                    from shapely.wkt import loads as wkt_loads
                                    try:
                                        # Enable C-based speedups available from 1.2.10+
                                        from shapely import speedups
                                        speedups.enable()
                                    except:
                                        s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")
                                    test = point.Point(lon, lat)
                                    shape = wkt_loads(wkt)
                                    ok = test.intersects(shape)
                                    if not ok:
                                        results = "Returned value not within %s" % Lx[used_Lx].name
                                elif L0:
                                    # Check within country at least
                                    if not L0_row:
                                        L0_row = db(table.id == L0).select(table.lon_min,
                                                                           table.lat_min,
                                                                           table.lon_max,
                                                                           table.lat_max,
                                                                           limitby=(0, 1)
                                                                           ).first()
                                    if lat < L0_row["lat_max"] and \
                                       lat > L0_row["lat_min"] and \
                                       lon < L0_row["lon_max"] and \
                                       lon > L0_row["lon_min"]:
                                        ok = True
                                    else:
                                        ok = False
                                        results = "Returned value not within %s" % check.name
                                else:
                                    # We'll just have to trust it!
                                    ok = True
                            if ok:
                                results = dict(lat=lat, lon=lon)
                    elif not results:
                        results = "Can't check that these results are specific enough"
                    else:
                        results = "Can't check that these results are specific enough"
                else:
                    # We'll just have to trust it!
                    results = dict(lat=lat, lon=lon)
            elif len(results):
                results = "Multiple results found"
                # @ToDo: Iterate through the results to see if just 1 is within the right bounds
            else:
                results = "No results found"
        except:
            import sys
            error = sys.exc_info()[1]
            results = str(error)

        return results

    # -------------------------------------------------------------------------
    @staticmethod
    def get_bearing(lat_start, lon_start, lat_end, lon_end):
        """
            Given a Start & End set of Coordinates, return a Bearing
            Formula from: http://www.movable-type.co.uk/scripts/latlong.html
        """

        import math

        # shortcuts
        cos = math.cos
        sin = math.sin

        delta_lon = lon_start - lon_end
        bearing = math.atan2(sin(delta_lon) * cos(lat_end),
                             (cos(lat_start) * sin(lat_end)) - \
                             (sin(lat_start) * cos(lat_end) * cos(delta_lon))
                             )
        # Convert to a compass bearing
        bearing = (bearing + 360) % 360

        return bearing

    # -------------------------------------------------------------------------
    def get_bounds(self, features=None, parent=None):
        """
            Calculate the Bounds of a list of Point Features
            e.g. When a map is displayed that focuses on a collection of points,
                 the map is zoomed to show just the region bounding the points.
            e.g. To use in GPX export for correct zooming
`
            Ensure a minimum size of bounding box, and that the points
            are inset from the border.

            @param features: A list of point features
            @param parent: A location_id to provide a polygonal bounds suitable
                           for validating child locations

            @ToDo: Support Polygons (separate function?)
        """

        if parent:
            table = current.s3db.gis_location
            db = current.db
            parent = db(table.id == parent).select(table.id,
                                                   table.level,
                                                   table.name,
                                                   table.parent,
                                                   table.path,
                                                   table.lon,
                                                   table.lat,
                                                   table.lon_min,
                                                   table.lat_min,
                                                   table.lon_max,
                                                   table.lat_max).first()
            if parent.lon_min is None or \
               parent.lon_max is None or \
               parent.lat_min is None or \
               parent.lat_max is None or \
               parent.lon == parent.lon_min or \
               parent.lon == parent.lon_max or \
               parent.lat == parent.lat_min or \
               parent.lat == parent.lat_max:
                # This is unsuitable - try higher parent
                if parent.level == "L1":
                    if parent.parent:
                        # We can trust that L0 should have the data from prepop
                        L0 = db(table.id == parent.parent).select(table.name,
                                                                  table.lon_min,
                                                                  table.lat_min,
                                                                  table.lon_max,
                                                                  table.lat_max).first()
                        return L0.lat_min, L0.lon_min, L0.lat_max, L0.lon_max, L0.name
                if parent.path:
                    path = parent.path
                else:
                    path = GIS.update_location_tree(dict(id=parent.id))
                path_list = map(int, path.split("/"))
                rows = db(table.id.belongs(path_list)).select(table.level,
                                                              table.name,
                                                              table.lat,
                                                              table.lon,
                                                              table.lon_min,
                                                              table.lat_min,
                                                              table.lon_max,
                                                              table.lat_max,
                                                              orderby=table.level)
                row_list = rows.as_list()
                row_list.reverse()
                ok = False
                for row in row_list:
                    if row["lon_min"] is not None and row["lon_max"] is not None and \
                       row["lat_min"] is not None and row["lat_max"] is not None and \
                       row["lon"] != row["lon_min"] != row["lon_max"] and \
                       row["lat"] != row["lat_min"] != row["lat_max"]:
                        ok = True
                        break

                if ok:
                    # This level is suitable
                    return row["lat_min"], row["lon_min"], row["lat_max"], row["lon_max"], row["name"]
            else:
                # This level is suitable
                return parent.lat_min, parent.lon_min, parent.lat_max, parent.lon_max, parent.name

            return -90, -180, 90, 180, None

        # Minimum Bounding Box
        # - gives a minimum width and height in degrees for the region shown.
        # Without this, a map showing a single point would not show any extent around that point.
        bbox_min_size = 0.05
        # Bounding Box Insets
        # - adds a small amount of distance outside the points.
        # Without this, the outermost points would be on the bounding box, and might not be visible.
        bbox_inset = 0.007

        if features:

            lon_min = 180
            lat_min = 90
            lon_max = -180
            lat_max = -90

            # Is this a simple feature set or the result of a join?
            try:
                lon = features[0].lon
                simple = True
            except (AttributeError, KeyError):
                simple = False

            # @ToDo: Optimised Geospatial routines rather than this crude hack
            for feature in features:

                try:
                    if simple:
                        lon = feature.lon
                        lat = feature.lat
                    else:
                        # A Join
                        lon = feature.gis_location.lon
                        lat = feature.gis_location.lat
                except AttributeError:
                    # Skip any rows without the necessary lat/lon fields
                    continue

                # Also skip those set to None. Note must use explicit test,
                # as zero is a legal value.
                if lon is None or lat is None:
                    continue

                lon_min = min(lon, lon_min)
                lat_min = min(lat, lat_min)
                lon_max = max(lon, lon_max)
                lat_max = max(lat, lat_max)

            # Assure a reasonable-sized box.
            delta_lon = (bbox_min_size - (lon_max - lon_min)) / 2.0
            if delta_lon > 0:
                lon_min -= delta_lon
                lon_max += delta_lon
            delta_lat = (bbox_min_size - (lat_max - lat_min)) / 2.0
            if delta_lat > 0:
                lat_min -= delta_lat
                lat_max += delta_lat

            # Move bounds outward by specified inset.
            lon_min -= bbox_inset
            lon_max += bbox_inset
            lat_min -= bbox_inset
            lat_max += bbox_inset

        else:
            # no features
            config = GIS.get_config()
            if config.lat_min is not None:
                lat_min = config.lat_min
            else:
                lat_min = -90
            if config.lon_min is not None:
                lon_min = config.lon_min
            else:
                lon_min = -180
            if config.lat_max is not None:
                lat_max = config.lat_max
            else:
                lat_max = 90
            if config.lon_max is not None:
                lon_max = config.lon_max
            else:
                lon_max = 180

        return dict(lon_min=lon_min, lat_min=lat_min,
                    lon_max=lon_max, lat_max=lat_max)

    # -------------------------------------------------------------------------
    @staticmethod
    def _lookup_parent_path(feature_id):
        """
            Helper that gets parent and path for a location.
        """

        db = current.db
        table = db.gis_location
        feature = db(table.id == feature_id).select(table.id,
                                                    table.name,
                                                    table.level,
                                                    table.path,
                                                    table.parent,
                                                    limitby=(0, 1)).first()

        return feature

    # -------------------------------------------------------------------------
    @staticmethod
    def get_children(id, level=None):
        """
            Return a list of IDs of all GIS Features which are children of
            the requested feature, using Materialized path for retrieving
            the children

            @author: Aravind Venkatesan and Ajay Kumar Sreenivasan from NCSU

            This has been chosen over Modified Preorder Tree Traversal for
            greater efficiency:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees

            @param: level - optionally filter by level
            
            @return: Rows object containing IDs & Names
                      Note: This does NOT include the parent location itself
        """

        db = current.db
        table = db.gis_location
        query = (table.deleted == False)
        if level:
            query &= (table.level == level)
        term = str(id)
        path = table.path
        query &= ((path.like(term + "/%")) | \
                  (path.like("%/" + term + "/%")))
        children = db(query).select(table.id,
                                    table.name)
        return children

    # -------------------------------------------------------------------------
    @staticmethod
    def get_parents(feature_id, feature=None, ids_only=False):
        """
            Returns a list containing ancestors of the requested feature.

            If the caller already has the location row, including path and
            parent fields, they can supply it via feature to avoid a db lookup.

            If ids_only is false, each element in the list is a gluon.sql.Row
            containing the gis_location record of an ancestor of the specified
            location.

            If ids_only is true, just returns a list of ids of the parents.
            This avoids a db lookup for the parents if the specified feature
            has a path.

            List elements are in the opposite order as the location path and
            exclude the specified location itself, i.e. element 0 is the parent
            and the last element is the most distant ancestor.

            Assists lazy update of a database without location paths by calling
            update_location_tree to get the path.
        """

        if not feature or "path" not in feature or "parent" not in feature:
            feature = GIS._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = GIS.update_location_tree(feature)

            path_list = map(int, path.split("/"))
            if len(path_list) == 1:
                # No parents - path contains only this feature.
                return None

            # Get path in the desired order, without current feature.
            reverse_path = path_list[:-1]
            reverse_path.reverse()

            # If only ids are wanted, stop here.
            if ids_only:
                return reverse_path

            # Retrieve parents - order in which they're returned is arbitrary.
            s3db = current.s3db
            table = s3db.gis_location
            query = (table.id.belongs(reverse_path))
            fields = [table.id, table.name, table.level, table.lat, table.lon]
            unordered_parents = current.db(query).select(cache=s3db.cache,
                                                         *fields)

            # Reorder parents in order of reversed path.
            unordered_ids = [row.id for row in unordered_parents]
            parents = [unordered_parents[unordered_ids.index(path_id)]
                       for path_id in reverse_path if path_id in unordered_ids]

            return parents

        else:
            return None

    # -------------------------------------------------------------------------
    def get_parent_per_level(self, results, feature_id,
                             feature=None,
                             ids=True,
                             names=True):
        """
            Adds ancestor of requested feature for each level to supplied dict.

            If the caller already has the location row, including path and
            parent fields, they can supply it via feature to avoid a db lookup.

            If a dict is not supplied in results, one is created. The results
            dict is returned in either case.

            If ids=True and names=False (used by old S3LocationSelectorWidget):
            For each ancestor, an entry  is added to results, like
            ancestor.level : ancestor.id

            If ids=False and names=True (used by address_onvalidation):
            For each ancestor, an entry  is added to results, like
            ancestor.level : ancestor.name

            If ids=True and names=True (used by new S3LocationSelectorWidget):
            For each ancestor, an entry  is added to results, like
            ancestor.level : {name : ancestor.name, id: ancestor.id}
        """

        if not results:
            results = {}

        id = feature_id
        # if we don't have a feature or a feature id return the dict as-is
        if not feature_id and not feature:
            return results
        if not feature_id and "path" not in feature and "parent" in feature:
            # gis_location_onvalidation on a Create => no ID yet
            # Read the Parent's path instead
            feature = self._lookup_parent_path(feature.parent)
            id = feature.id
        elif not feature or "path" not in feature or "parent" not in feature:
            feature = self._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = self.update_location_tree(feature)

            # Get ids of ancestors at each level.
            if feature.parent:
                strict = self.get_strict_hierarchy(feature.parent)
            else:
                strict = self.get_strict_hierarchy(id)
            if path and strict and not names:
                # No need to do a db lookup for parents in this case -- we
                # know the levels of the parents from their position in path.
                # Note ids returned from db are ints, not strings, so be
                # consistent with that.
                path_ids = map(int, path.split("/"))
                # This skips the last path element, which is the supplied
                # location.
                for (i, id) in enumerate(path_ids[:-1]):
                    results["L%i" % i] = id
            elif path:
                ancestors = self.get_parents(id, feature=feature)
                if ancestors:
                    for ancestor in ancestors:
                        if ancestor.level and ancestor.level in self.hierarchy_level_keys:
                            if names and ids:
                                results[ancestor.level] = Storage()
                                results[ancestor.level].name = ancestor.name
                                results[ancestor.level].id = ancestor.id
                            elif names:
                                results[ancestor.level] = ancestor.name
                            else:
                                results[ancestor.level] = ancestor.id
            if not feature_id:
                # Add the Parent in (we only need the version required for gis_location onvalidation here)
                results[feature.level] = feature.name
            if names:
                # We need to have entries for all levels
                # (both for address onvalidation & new LocationSelector)
                hierarchy_level_keys = self.hierarchy_level_keys
                for key in hierarchy_level_keys:
                    if not results.has_key(key):
                        results[key] = None

        return results

    # -------------------------------------------------------------------------
    def update_table_hierarchy_labels(self, tablename=None):
        """
            Re-set table options that depend on location_hierarchy

            Only update tables which are already defined
        """

        levels = ["L1", "L2", "L3", "L4"]
        labels = self.get_location_hierarchy()

        db = current.db
        if tablename and tablename in db:
            # Update the specific table which has just been defined
            table = db[tablename]
            if tablename == "gis_location":
                labels["L0"] = current.messages["COUNTRY"]
                table.level.requires = \
                    IS_NULL_OR(IS_IN_SET(labels))
            else:
                for level in levels:
                    table[level].label = labels[level]
        else:
            # Do all Tables which are already defined

            # gis_location
            if "gis_location" in db:
                table = db.gis_location
                table.level.requires = \
                    IS_NULL_OR(IS_IN_SET(labels))

            # These tables store location hierarchy info for XSLT export.
            # Labels are used for PDF & XLS Reports
            tables = ["org_office",
                      #"pr_person",
                      "pr_address",
                      "cr_shelter",
                      "asset_asset",
                      #"hms_hospital",
                      ]

            for tablename in tables:
                if tablename in db:
                    table = db[tablename]
                    for level in levels:
                        table[level].label = labels[level]

    # -------------------------------------------------------------------------
    @staticmethod
    def set_config(config_id=None, force_update_cache=False):
        """
            Reads the specified GIS config from the DB, caches it in response.

            Passing in a false or non-existent id will cause the personal config,
            if any, to be used, else the site config (uuid SITE_DEFAULT), else
            their fallback values defined in this class.

            If force_update_cache is true, the config will be read and cached in
            response even if the specified config is the same as what's already
            cached. Used when the config was just written.

            The config itself will be available in response.s3.gis.config.
            Scalar fields from the gis_config record and its linked
            gis_projection record have the same names as the fields in their
            tables and can be accessed as response.s3.gis.<fieldname>.

            Returns the id of the config it actually used, if any.

            @param: config_id. use '0' to set the SITE_DEFAULT

            @ToDo: Merge configs for Event
        """

        _gis = current.response.s3.gis

        # If an id has been supplied, try it first. If it matches what's in
        # response, there's no work to do.
        if config_id and not force_update_cache and \
           _gis.config and \
           _gis.config.id == config_id:
            return

        db = current.db
        s3db = current.s3db
        ctable = s3db.gis_config
        mtable = s3db.gis_marker
        ptable = s3db.gis_projection
        stable = s3db.gis_symbology
        ltable = s3db.gis_layer_config
        fields = [ctable.id,
                  ctable.default_location_id,
                  ctable.geocoder,
                  ctable.lat_min,
                  ctable.lat_max,
                  ctable.lon_min,
                  ctable.lon_max,
                  ctable.zoom,
                  ctable.lat,
                  ctable.lon,
                  ctable.pe_id,
                  ctable.symbology_id,
                  ctable.wmsbrowser_url,
                  ctable.wmsbrowser_name,
                  ctable.zoom_levels,
                  mtable.image,
                  mtable.height,
                  mtable.width,
                  ptable.epsg,
                  ptable.proj4js,
                  ptable.maxExtent,
                  ptable.units,
                  ]

        cache = Storage()
        row = None
        rows = None
        if config_id:
            # Merge this one with the Site Default
            query = (ctable.id == config_id) | \
                    (ctable.uuid == "SITE_DEFAULT")
            # May well not be complete, so Left Join
            left = [ptable.on(ptable.id == ctable.projection_id),
                    stable.on(stable.id == ctable.symbology_id),
                    mtable.on(mtable.id == stable.marker_id),
                    ]
            rows = db(query).select(*fields,
                                    left=left,
                                    orderby=ctable.pe_type,
                                    limitby=(0, 2))
            if len(rows) == 1:
                # The requested config must be invalid, so just use site default
                row = rows.first()

        elif config_id is 0:
            # Use site default
            query = (ctable.uuid == "SITE_DEFAULT") & \
                    (mtable.id == stable.marker_id) & \
                    (stable.id == ctable.symbology_id) & \
                    (ptable.id == ctable.projection_id)
            row = db(query).select(*fields,
                                   limitby=(0, 1)).first()
            if not row:
                # No configs found at all
                _gis.config = cache
                return cache

        # If no id supplied, extend the site config with any personal or OU configs
        if not rows and not row:
            # Read personalised config, if available.
            auth = current.auth
            if auth.is_logged_in():
                pe_id = auth.user.pe_id
                # OU configs
                # List of roles to check (in order)
                roles = ["Staff", "Volunteer"]
                role_paths = s3db.pr_get_role_paths(pe_id, roles=roles)
                # Unordered list of PEs
                pes = []
                for role in roles:
                    if role in role_paths:
                        # @ToDo: Allow selection of which OU a person's config should inherit from for disambiguation
                        # - store in s3db.gis_config?
                        # - needs a method in gis_config_form_setup() to populate the dropdown from the OUs (in this person's Path for this person's,  would have to be a dynamic lookup for Admins)
                        pes = role_paths[role].nodes()
                        # Staff don't check Volunteer's OUs
                        break
                query = (ctable.uuid == "SITE_DEFAULT") | \
                        ((ctable.pe_id == pe_id) & \
                         (ctable.pe_default != False))
                len_pes = len(pes)
                if len_pes == 1:
                    query |= (ctable.pe_id == pes[0])
                elif len_pes:
                    query |= (ctable.pe_id.belongs(pes))
                # Personal may well not be complete, so Left Join
                left = [ptable.on(ptable.id == ctable.projection_id),
                        stable.on(stable.id == ctable.symbology_id),
                        mtable.on(mtable.id == stable.marker_id),
                        ]
                # Order by pe_type (defined in gis_config)
                # @ToDo: Do this purely from the hierarchy
                rows = db(query).select(*fields,
                                        left=left,
                                        orderby=ctable.pe_type)
                if len(rows) == 1:
                    row = rows.first()

        if rows and not row:
            # Merge Configs
            cache["ids"] = []
            for row in rows:
                config = row["gis_config"]
                if not config_id:
                    config_id = config.id
                cache["ids"].append(config.id)
                for key in config:
                    if key in ["delete_record", "gis_layer_config", "gis_menu", "update_record"]:
                        continue
                    if key not in cache or cache[key] is None:
                        cache[key] = config[key]
                if "epsg" not in cache or cache["epsg"] is None:
                    projection = row["gis_projection"]
                    for key in ["epsg", "units", "maxExtent", "proj4js"]:
                        cache[key] = projection[key] if key in projection \
                                                     else None
                if "marker_image" not in cache or \
                   cache["marker_image"] is None:
                    marker = row["gis_marker"]
                    for key in ["image", "height", "width"]:
                        cache["marker_%s" % key] = marker[key] if key in marker \
                                                               else None
            # Add NULL values for any that aren't defined, to avoid KeyErrors
            for key in ["epsg", "units", "proj4js", "maxExtent",
                        "marker_image", "marker_height", "marker_width",
                        ]:
                if key not in cache:
                    cache[key] = None

        if not row:
            # No personal config or not logged in. Use site default.
            query = (ctable.uuid == "SITE_DEFAULT") & \
                    (mtable.id == stable.marker_id) & \
                    (stable.id == ctable.symbology_id) & \
                    (ptable.id == ctable.projection_id)
            row = db(query).select(*fields,
                                   limitby=(0, 1)).first()

            if not row:
                # No configs found at all
                _gis.config = cache
                return cache

        if not cache:
            # We had a single row
            config = row["gis_config"]
            config_id = config.id
            cache["ids"] = [config_id]
            projection = row["gis_projection"]
            marker = row["gis_marker"]
            for key in config:
                cache[key] = config[key]
            for key in ["epsg", "maxExtent", "proj4js", "units"]:
                cache[key] = projection[key] if key in projection else None
            for key in ["image", "height", "width"]:
                cache["marker_%s" % key] = marker[key] if key in marker \
                                                       else None

        # Store the values
        _gis.config = cache
        return cache

    # -------------------------------------------------------------------------
    @staticmethod
    def get_config():
        """
            Returns the current GIS config structure.

            @ToDo: Config() class
        """

        gis = current.response.s3.gis

        if not gis.config:
            # Ask set_config to put the appropriate config in response.
            if current.session.s3.gis_config_id:
                GIS.set_config(current.session.s3.gis_config_id)
            else:
                GIS.set_config()

        return gis.config

    # -------------------------------------------------------------------------
    def get_location_hierarchy(self, level=None, location=None):
        """
            Returns the location hierarchy and it's labels

            @param: level - a specific level for which to lookup the label
            @param: location - the location_id to lookup the location for
                               currently only the actual location is supported
                               @ToDo: Do a search of parents to allow this
                                      lookup for any location
        """

        _levels = self.hierarchy_levels
        _location = location

        if not location and _levels:
            # Use cached value
            if level:
                if level in _levels:
                    return _levels[level]
                else:
                    return level
            else:
                return _levels

        T = current.T
        COUNTRY = current.messages["COUNTRY"]

        if level == "L0":
            return COUNTRY

        db = current.db
        s3db = current.s3db
        table = s3db.gis_hierarchy

        fields = [table.uuid,
                  table.L1,
                  table.L2,
                  table.L3,
                  table.L4,
                  table.L5,
                  ]

        query = (table.uuid == "SITE_DEFAULT")
        if not location:
            config = GIS.get_config()
            location = config.region_location_id
        if location:
            # Try the Region, but ensure we have the fallback available in a single query
            query = query | (table.location_id == location)
        rows = db(query).select(cache=s3db.cache,
                                *fields)
        if len(rows) > 1:
            # Remove the Site Default
            filter = lambda row: row.uuid == "SITE_DEFAULT"
            rows.exclude(filter)
        elif not rows:
            # prepop hasn't run yet
            if level:
                return level
            levels = OrderedDict()
            hierarchy_level_keys = self.hierarchy_level_keys
            for key in hierarchy_level_keys:
                if key == "L0":
                    levels[key] = COUNTRY
                else:
                    levels[key] = key
            return levels

        row = rows.first()
        if level:
            try:
                return T(row[level])
            except:
                return level
        else:
            levels = OrderedDict()
            hierarchy_level_keys = self.hierarchy_level_keys
            for key in hierarchy_level_keys:
                if key == "L0":
                    levels[key] = COUNTRY
                elif key in row and row[key]:
                    # Only include rows with values
                    levels[key] = str(T(row[key]))
            if not _location:
                # Cache the value
                self.hierarchy_levels = levels
            if level:
                return levels[level]
            else:
                return levels

    # -------------------------------------------------------------------------
    def get_strict_hierarchy(self, location=None):
        """
            Returns the strict hierarchy value from the current config.

            @param: location - the location_id of the record to check
        """

        s3db = current.s3db
        table = s3db.gis_hierarchy

        # Read the system default
        # @ToDo: Check for an active gis_config region?
        query = (table.uuid == "SITE_DEFAULT")
        if location:
            # Try the Location's Country, but ensure we have the fallback available in a single query
            query = query | (table.location_id == self.get_parent_country(location))
        rows = current.db(query).select(table.uuid,
                                        table.strict_hierarchy,
                                        cache=s3db.cache)
        if len(rows) > 1:
            # Remove the Site Default
            filter = lambda row: row.uuid == "SITE_DEFAULT"
            rows.exclude(filter)
        row = rows.first()
        if row:
            strict = row.strict_hierarchy
        else:
            # Pre-pop hasn't run yet
            return False

        return strict

    # -------------------------------------------------------------------------
    def get_max_hierarchy_level(self):
        """
            Returns the deepest level key (i.e. Ln) in the current hierarchy.
            - used by gis_location_onvalidation()
        """

        location_hierarchy = self.get_location_hierarchy()
        return max(location_hierarchy)

    # -------------------------------------------------------------------------
    def get_all_current_levels(self, level=None):
        """
            Get the current hierarchy levels plus non-hierarchy levels.
        """

        all_levels = OrderedDict()
        all_levels.update(self.get_location_hierarchy())
        #T = current.T
        #all_levels["GR"] = T("Location Group")
        #all_levels["XX"] = T("Imported")

        if level:
            try:
                return all_levels[level]
            except Exception, exception:

                return level
        else:
            return all_levels

    # -------------------------------------------------------------------------
    @staticmethod
    def get_countries(key_type="id"):
        """
            Returns country code or L0 location id versus name for all countries.

            The lookup is cached in the session

            If key_type is "code", these are returned as an OrderedDict with
            country code as the key.  If key_type is "id", then the location id
            is the key.  In all cases, the value is the name.
        """

        session = current.session
        if "gis" not in session:
            session.gis = Storage()
        gis = session.gis

        if gis.countries_by_id:
            cached = True
        else:
            cached = False

        if not cached:
            s3db = current.s3db
            table = s3db.gis_location
            ttable = s3db.gis_location_tag
            query = (table.level == "L0") & \
                    (ttable.tag == "ISO2") & \
                    (ttable.location_id == table.id)
            countries = current.db(query).select(table.id,
                                                 table.name,
                                                 ttable.value,
                                                 orderby=table.name)
            if not countries:
                return []

            countries_by_id = OrderedDict()
            countries_by_code = OrderedDict()
            for row in countries:
                location = row["gis_location"]
                countries_by_id[location.id] = location.name
                countries_by_code[row["gis_location_tag"].value] = location.name

            # Cache in the session
            gis.countries_by_id = countries_by_id
            gis.countries_by_code = countries_by_code

            if key_type == "id":
                return countries_by_id
            else:
                return countries_by_code

        elif key_type == "id":
            return gis.countries_by_id
        else:
            return gis.countries_by_code

    # -------------------------------------------------------------------------
    @staticmethod
    def get_country(key, key_type="id"):
        """
            Returns country name for given code or id from L0 locations.

            The key can be either location id or country code, as specified
            by key_type.
        """

        if key:
            if current.gis.get_countries(key_type):
                if key_type == "id":
                    return current.session.gis.countries_by_id[key]
                else:
                    return current.session.gis.countries_by_code[key]

        return None

    # -------------------------------------------------------------------------
    def get_parent_country(self, location, key_type="id"):
        """
            Returns the parent country for a given record

            @param: location: the location or id to search for
            @param: key_type: whether to return an id or code

            @ToDo: Optimise to not use try/except
        """

        if not location:
            return None
        db = current.db
        s3db = current.s3db

        # @ToDo: Avoid try/except here!
        # - separate parameters best as even isinstance is expensive
        try:
            # location is passed as integer (location_id)
            table = s3db.gis_location
            location = db(table.id == location).select(table.id,
                                                       table.path,
                                                       table.level,
                                                       limitby=(0, 1),
                                                       cache=s3db.cache).first()
        except:
            # location is passed as record
            pass

        if location.level == "L0":
            if key_type == "id":
                return location.id
            elif key_type == "code":
                ttable = s3db.gis_location_tag
                query = (ttable.tag == "ISO2") & \
                        (ttable.location_id == location.id)
                tag = db(query).select(ttable.value,
                                       limitby=(0, 1)).first()
                try:
                    return tag.value
                except:
                    return None
        else:
            parents = self.get_parents(location.id,
                                       feature=location)
            if parents:
                for row in parents:
                    if row.level == "L0":
                        if key_type == "id":
                            return row.id
                        elif key_type == "code":
                            ttable = s3db.gis_location_tag
                            query = (ttable.tag == "ISO2") & \
                                    (ttable.location_id == row.id)
                            tag = db(query).select(ttable.value,
                                                   limitby=(0, 1)).first()
                            try:
                                return tag.value
                            except:
                                return None
        return None

    # -------------------------------------------------------------------------
    def get_default_country(self, key_type="id"):
        """
            Returns the default country for the active gis_config

            @param: key_type: whether to return an id or code
        """

        config = GIS.get_config()

        if config.default_location_id:
            return self.get_parent_country(config.default_location_id,
                                           key_type=key_type)

        return None

    # -------------------------------------------------------------------------
    def get_features_in_polygon(self, location, tablename=None, category=None):
        """
            Returns a gluon.sql.Rows of Features within a Polygon.
            The Polygon can be either a WKT string or the ID of a record in the
            gis_location table

            Currently unused.
            @ToDo: Optimise to not use try/except
        """

        from shapely.geos import ReadingError
        from shapely.wkt import loads as wkt_loads

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        db = current.db
        s3db = current.s3db
        locations = s3db.gis_location

        try:
            location_id = int(location)
            # Check that the location is a polygon
            query = (locations.id == location_id)
            location = db(query).select(locations.wkt,
                                        locations.lon_min,
                                        locations.lon_max,
                                        locations.lat_min,
                                        locations.lat_max,
                                        limitby=(0, 1)).first()
            if location:
                wkt = location.wkt
                if wkt and (wkt.startswith("POLYGON") or \
                            wkt.startswith("MULTIPOLYGON")):
                    # ok
                    lon_min = location.lon_min
                    lon_max = location.lon_max
                    lat_min = location.lat_min
                    lat_max = location.lat_max

                else:
                    s3_debug("Location searched within isn't a Polygon!")
                    return None
        except: # @ToDo: need specific exception
            wkt = location
            if (wkt.startswith("POLYGON") or wkt.startswith("MULTIPOLYGON")):
                # ok
                lon_min = None
            else:
                s3_debug("This isn't a Polygon!")
                return None

        try:
            polygon = wkt_loads(wkt)
        except: # @ToDo: need specific exception
            s3_debug("Invalid Polygon!")
            return None

        table = s3db[tablename]

        if "location_id" not in table.fields():
            # @ToDo: Add any special cases to be able to find the linked location
            s3_debug("This table doesn't have a location_id!")
            return None

        query = (table.location_id == locations.id)
        if "deleted" in table.fields:
            query &= (table.deleted == False)
        # @ToDo: Check AAA (do this as a resource filter?)

        features = db(query).select(locations.wkt,
                                    locations.lat,
                                    locations.lon,
                                    table.ALL)
        output = Rows()
        # @ToDo: provide option to use PostGIS/Spatialite
        # settings = current.deployment_settings
        # if settings.gis.spatialdb and settings.database.db_type == "postgres":
        if lon_min is None:
            # We have no BBOX so go straight to the full geometry check
            for row in features:
                _location = row.gis_location
                wkt = _location.wkt
                if wkt is None:
                    lat = _location.lat
                    lon = _location.lon
                    if lat is not None and lon is not None:
                        wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        continue
                try:
                    shape = wkt_loads(wkt)
                    if shape.intersects(polygon):
                        # Save Record
                        output.records.append(row)
                except ReadingError:
                    s3_debug(
                        "Error reading wkt of location with id",
                        value=row.id
                    )
        else:
            # 1st check for Features included within the bbox (faster)
            def in_bbox(row):
                _location = row.gis_location
                return (_location.lon > lon_min) & \
                       (_location.lon < lon_max) & \
                       (_location.lat > lat_min) & \
                       (_location.lat < lat_max)
            for row in features.find(lambda row: in_bbox(row)):
                # Search within this subset with a full geometry check
                # Uses Shapely.
                _location = row.gis_location
                wkt = _location.wkt
                if wkt is None:
                    lat = _location.lat
                    lon = _location.lon
                    if lat is not None and lon is not None:
                        wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        continue
                try:
                    shape = wkt_loads(wkt)
                    if shape.intersects(polygon):
                        # Save Record
                        output.records.append(row)
                except ReadingError:
                    s3_debug(
                        "Error reading wkt of location with id",
                        value = row.id,
                    )

        return output

    # -------------------------------------------------------------------------
    def get_features_in_radius(self, lat, lon, radius, tablename=None, category=None):
        """
            Returns Features within a Radius (in km) of a LatLon Location

            Unused
        """

        import math

        db = current.db
        settings = current.deployment_settings

        if settings.gis.spatialdb and settings.database.db_type == "postgres":
            # Use PostGIS routine
            # The ST_DWithin function call will automatically include a bounding box comparison that will make use of any indexes that are available on the geometries.
            # @ToDo: Support optional Category (make this a generic filter?)

            import psycopg2
            import psycopg2.extras

            dbname = settings.database.database
            username = settings.database.username
            password = settings.database.password
            host = settings.database.host
            port = settings.database.port or "5432"

            # Convert km to degrees (since we're using the_geom not the_geog)
            radius = math.degrees(float(radius) / RADIUS_EARTH)

            connection = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s" % (dbname, username, password, host, port))
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            info_string = "SELECT column_name, udt_name FROM information_schema.columns WHERE table_name = 'gis_location' or table_name = '%s';" % tablename
            cursor.execute(info_string)
            # @ToDo: Look at more optimal queries for just those fields we need
            if tablename:
                # Lookup the resource
                query_string = cursor.mogrify("SELECT * FROM gis_location, %s WHERE %s.location_id = gis_location.id and ST_DWithin (ST_GeomFromText ('POINT (%s %s)', 4326), the_geom, %s);" % (tablename, tablename, lat, lon, radius))
            else:
                # Lookup the raw Locations
                query_string = cursor.mogrify("SELECT * FROM gis_location WHERE ST_DWithin (ST_GeomFromText ('POINT (%s %s)', 4326), the_geom, %s);" % (lat, lon, radius))

            cursor.execute(query_string)
            # @ToDo: Export Rows?
            features = []
            for record in cursor:
                d = dict(record.items())
                row = Storage()
                # @ToDo: Optional support for Polygons
                if tablename:
                    row.gis_location = Storage()
                    row.gis_location.id = d["id"]
                    row.gis_location.lat = d["lat"]
                    row.gis_location.lon = d["lon"]
                    row.gis_location.lat_min = d["lat_min"]
                    row.gis_location.lon_min = d["lon_min"]
                    row.gis_location.lat_max = d["lat_max"]
                    row.gis_location.lon_max = d["lon_max"]
                    row[tablename] = Storage()
                    row[tablename].id = d["id"]
                    row[tablename].name = d["name"]
                else:
                    row.name = d["name"]
                    row.id = d["id"]
                    row.lat = d["lat"]
                    row.lon = d["lon"]
                    row.lat_min = d["lat_min"]
                    row.lon_min = d["lon_min"]
                    row.lat_max = d["lat_max"]
                    row.lon_max = d["lon_max"]
                features.append(row)

            return features

        #elif settings.database.db_type == "mysql":
            # Do the calculation in MySQL to pull back only the relevant rows
            # Raw MySQL Formula from: http://blog.peoplesdns.com/archives/24
            # PI = 3.141592653589793, mysql's pi() function returns 3.141593
            #pi = math.pi
            #query = """SELECT name, lat, lon, acos(SIN( PI()* 40.7383040 /180 )*SIN( PI()*lat/180 ))+(cos(PI()* 40.7383040 /180)*COS( PI()*lat/180) *COS(PI()*lon/180-PI()* -73.99319 /180))* 3963.191
            #AS distance
            #FROM gis_location
            #WHERE 1=1
            #AND 3963.191 * ACOS( (SIN(PI()* 40.7383040 /180)*SIN(PI() * lat/180)) + (COS(PI()* 40.7383040 /180)*cos(PI()*lat/180)*COS(PI() * lon/180-PI()* -73.99319 /180))) < = 1.5
            #ORDER BY 3963.191 * ACOS((SIN(PI()* 40.7383040 /180)*SIN(PI()*lat/180)) + (COS(PI()* 40.7383040 /180)*cos(PI()*lat/180)*COS(PI() * lon/180-PI()* -73.99319 /180)))"""
            # db.executesql(query)

        else:
            # Calculate in Python
            # Pull back all the rows within a square bounding box (faster than checking all features manually)
            # Then check each feature within this subset
            # http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates

            # @ToDo: Support optional Category (make this a generic filter?)

            # shortcuts
            radians = math.radians
            degrees = math.degrees

            MIN_LAT = radians(-90)     # -PI/2
            MAX_LAT = radians(90)      # PI/2
            MIN_LON = radians(-180)    # -PI
            MAX_LON = radians(180)     #  PI

            # Convert to radians for the calculation
            r = float(radius) / RADIUS_EARTH
            radLat = radians(lat)
            radLon = radians(lon)

            # Calculate the bounding box
            minLat = radLat - r
            maxLat = radLat + r

            if (minLat > MIN_LAT) and (maxLat < MAX_LAT):
                deltaLon = math.asin(math.sin(r) / math.cos(radLat))
                minLon = radLon - deltaLon
                if (minLon < MIN_LON):
                    minLon += 2 * math.pi
                maxLon = radLon + deltaLon
                if (maxLon > MAX_LON):
                    maxLon -= 2 * math.pi
            else:
                # Special care for Poles & 180 Meridian:
                # http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates#PolesAnd180thMeridian
                minLat = max(minLat, MIN_LAT)
                maxLat = min(maxLat, MAX_LAT)
                minLon = MIN_LON
                maxLon = MAX_LON

            # Convert back to degrees
            minLat = degrees(minLat)
            minLon = degrees(minLon)
            maxLat = degrees(maxLat)
            maxLon = degrees(maxLon)

            # shortcut
            locations = db.gis_location

            query = (locations.lat > minLat) & (locations.lat < maxLat) & (locations.lon > minLon) & (locations.lon < maxLon)
            deleted = (locations.deleted == False)
            empty = (locations.lat != None) & (locations.lon != None)
            query = deleted & empty & query

            if tablename:
                # Lookup the resource
                table = current.s3db[tablename]
                query &= (table.location_id == locations.id)
                records = db(query).select(table.ALL,
                                           locations.id,
                                           locations.name,
                                           locations.level,
                                           locations.lat,
                                           locations.lon,
                                           locations.lat_min,
                                           locations.lon_min,
                                           locations.lat_max,
                                           locations.lon_max)
            else:
                # Lookup the raw Locations
                records = db(query).select(locations.id,
                                           locations.name,
                                           locations.level,
                                           locations.lat,
                                           locations.lon,
                                           locations.lat_min,
                                           locations.lon_min,
                                           locations.lat_max,
                                           locations.lon_max)
            features = Rows()
            for record in records:
                # Calculate the Great Circle distance
                if tablename:
                    distance = self.greatCircleDistance(lat,
                                                        lon,
                                                        record.gis_location.lat,
                                                        record.gis_location.lon)
                else:
                    distance = self.greatCircleDistance(lat,
                                                        lon,
                                                        record.lat,
                                                        record.lon)
                if distance < radius:
                    features.records.append(record)
                else:
                    # skip
                    continue

            return features

    # -------------------------------------------------------------------------
    def get_latlon(self, feature_id, filter=False):
        """
            Returns the Lat/Lon for a Feature

            used by display_feature() in gis controller

            @param feature_id: the feature ID
            @param filter: Filter out results based on deployment_settings
        """

        db = current.db
        table = db.gis_location
        feature = db(table.id == feature_id).select(table.id,
                                                    table.lat,
                                                    table.lon,
                                                    table.parent,
                                                    table.path,
                                                    limitby=(0, 1)).first()

        # Zero is an allowed value, hence explicit test for None.
        if "lon" in feature and "lat" in feature and \
           (feature.lat is not None) and (feature.lon is not None):
            return dict(lon=feature.lon, lat=feature.lat)

        else:
            # Step through ancestors to first with lon, lat.
            parents = self.get_parents(feature.id, feature=feature)
            if parents:
                lon = lat = None
                for row in parents:
                    if "lon" in row and "lat" in row and \
                       (row.lon is not None) and (row.lat is not None):
                        return dict(lon=row.lon, lat=row.lat)

        # Invalid feature_id
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def get_marker(controller=None,
                   function=None,
                   ):
        """
            Returns a Marker dict
            - called by S3REST: S3Resource.export_tree() for non-geojson resources
            - called by S3Search
        """

        marker = None
        if controller and function:
            # Lookup marker in the gis_feature table
            db = current.db
            s3db = current.s3db
            ftable = s3db.gis_layer_feature
            ltable = s3db.gis_layer_symbology
            mtable = s3db.gis_marker
            try:
                symbology_id = current.response.s3.gis.config.symbology_id
            except:
                # Config not initialised yet
                config = GIS.get_config()
                symbology_id = config.symbology_id
            query = (ftable.controller == controller) & \
                    (ftable.function == function) & \
                    (ftable.layer_id == ltable.layer_id) & \
                    (ltable.symbology_id == symbology_id) & \
                    (ltable.marker_id == mtable.id)
            marker = db(query).select(mtable.image,
                                      mtable.height,
                                      mtable.width,
                                      ltable.gps_marker).first()
            if marker:
                _marker = marker["gis_marker"]
                marker = dict(image=_marker.image,
                              height=_marker.height,
                              width=_marker.width,
                              gps_marker=marker["gis_layer_symbology"].gps_marker
                              )

        if not marker:
            # Default
            marker = Marker().as_dict()

        return marker

    # -------------------------------------------------------------------------
    @staticmethod
    def get_location_data(resource):
        """
            Returns the locations, markers and popup tooltips for an XML export
            e.g. Feature Layers or Search results (Feature Resources)
            e.g. Exports in KML, GeoRSS or GPX format

            Called by S3REST: S3Resource.export_tree()
            @param: resource - S3Resource instance (required)
        """

        NONE = current.messages["NONE"]
        #if DEBUG:
        #    start = datetime.datetime.now()

        db = current.db
        s3db = current.s3db
        request = current.request
        vars = request.get_vars
        format = current.auth.permission.format

        ftable = s3db.gis_layer_feature

        layer = None

        layer_id = vars.get("layer", None)
        if layer_id:
            # Feature Layer
            query = (ftable.id == layer_id)
            layer = db(query).select(ftable.trackable,
                                     ftable.polygons,
                                     ftable.popup_label,
                                     ftable.popup_fields,
                                     ftable.attr_fields,
                                     limitby=(0, 1)).first()

        else:
            # e.g. Search results loaded as a Feature Resource layer
            # e.g. Volunteer Layer in Vulnerability module
            # e.g. KML, geoRSS or GPX export
            controller = request.controller
            function = request.function
            query = (ftable.controller == controller) & \
                    (ftable.function == function)

            layers = db(query).select(ftable.trackable,
                                      ftable.polygons,
                                      ftable.popup_label,
                                      ftable.popup_fields,
                                      ftable.attr_fields,
                                      )
            if len(layers) > 1:
                # We can't provide details for the whole layer, but need to do a per-record check
                # Suggest creating separate controllers to avoid this problem
                return None
            elif layers:
                layer = layers.first()

        if layer:
            popup_label = layer.popup_label
            popup_fields = layer.popup_fields or []
            attr_fields = layer.attr_fields or []
            trackable = layer.trackable
            polygons = layer.polygons
        else:
            popup_label = ""
            popup_fields = ["name"]
            attr_fields = []
            trackable = False
            polygons = False

        table = resource.table
        tablename = resource.tablename
        pkey = table._id.name

        markers = {}
        tooltips = {}
        attributes = {}
        represents = {}
        if format == "geojson":
            if popup_fields or attr_fields:
                # Build the Attributes &/Popup Tooltips now so that representations can be
                # looked-up in bulk rather than as a separate lookup per record
                if popup_fields:
                    tips = {}
                    label_off = vars.get("label_off", None)
                    if popup_label and not label_off:
                        _tooltip = "(%s)" % current.T(popup_label)
                    else:
                        _tooltip = ""
                attr = {}

                fields = list(set(popup_fields + attr_fields))
                if pkey not in fields:
                    fields.insert(0, pkey)

                data = resource.select(fields,
                                       limit=None,
                                       represent=True)

                rfields = data["rfields"]
                popup_cols = []
                attr_cols = []
                for f in rfields:
                    fname = f.fname
                    selector = f.selector
                    if fname in popup_fields or selector in popup_fields:
                        popup_cols.append(f.colname)
                    if fname in attr_fields or selector in attr_fields:
                        attr_cols.append(f.colname)

                rows = data["rows"]
                for row in rows:
                    record_id = int(row[str(table[pkey])])
                    if attr_cols:
                        attribute = {}
                        for fieldname in attr_cols:
                            represent = row[fieldname]
                            if represent and represent != NONE:
                                # Skip empty fields
                                fname = fieldname.split(".")[1]
                                attribute[fname] = represent
                        attr[record_id] = attribute

                    if popup_cols:
                        tooltip = _tooltip
                        first = True
                        for fieldname in popup_cols:
                            represent = row[fieldname]
                            if represent and represent != NONE:
                                # Skip empty fields
                                if first:
                                    tooltip = "%s %s" % (represent, tooltip)
                                    first = False
                                else:
                                    tooltip = "%s<br />%s" % (tooltip, represent)
                        tips[record_id] = tooltip

                if attr_fields:
                    attributes[tablename] = attr
                if popup_fields:
                    tooltips[tablename] = tips

                #if DEBUG:
                #    end = datetime.datetime.now()
                #    duration = end - start
                #    duration = "{:.2f}".format(duration.total_seconds())
                #    if layer_id:
                #        query = (ftable.id == layer_id)
                #        layer_name = db(query).select(ftable.name,
                #                                      limitby=(0, 1)).first().name
                #    else:
                #        layer_name = "Unknown"
                #    _debug("Attributes/Tooltip lookup of layer %s completed in %s seconds" % \
                #            (layer_name, duration))

            _markers = vars.get("markers", None)
            if _markers:
                # Add a per-feature Marker
                marker_fn = s3db.get_config(tablename, "marker_fn")
                if marker_fn:
                    for record in resource:
                        markers[record[pkey]] = marker_fn(record)
                else:
                    # No configuration found so use default marker for all
                    c, f = tablename.split("_", 1)
                    markers = GIS.get_marker(c, f)

                markers[tablename] = markers
        else:
            # KML, GeoRSS or GPX
            marker_fn = s3db.get_config(tablename, "marker_fn")
            if marker_fn:
                # Add a per-feature Marker
                for record in resource:
                    markers[record[pkey]] = marker_fn(record)
            else:
                # No configuration found so use default marker for all
                c, f = tablename.split("_", 1)
                markers = GIS.get_marker(c, f)

            markers[tablename] = markers

        # Lookup the LatLons now so that it can be done as a single
        # query rather than per record
        #if DEBUG:
        #    start = datetime.datetime.now()
        latlons = {}
        wkts = {}
        geojsons = {}
        gtable = s3db.gis_location
        if trackable:
            # Use S3Track
            ids = resource._ids
            # Ensure IDs in ascending order
            ids.sort()
            try:
                tracker = S3Trackable(table, record_ids=ids)
            except SyntaxError:
                # This table isn't trackable
                pass
            else:
                _latlons = tracker.get_location(_fields=[gtable.lat,
                                                         gtable.lon])
                index = 0
                for id in ids:
                    _location = _latlons[index]
                    latlons[id] = (_location.lat, _location.lon)
                    index += 1

        if not latlons:
            if "location_id" in table.fields:
                query = (table.id.belongs(resource._ids)) & \
                        (table.location_id == gtable.id)
            elif "site_id" in table.fields:
                stable = s3db.org_site
                query = (table.id.belongs(resource._ids)) & \
                        (table.site_id == stable.site_id) & \
                        (stable.location_id == gtable.id)
            else:
                # Can't display this resource on the Map
                return None

            if polygons:
                settings = current.deployment_settings
                tolerance = settings.get_gis_simplify_tolerance()
                if settings.get_gis_spatialdb():
                    if format == "geojson":
                        # Do the Simplify & GeoJSON direct from the DB
                        rows = db(query).select(table.id,
                                                gtable.the_geom.st_simplify(tolerance).st_asgeojson(precision=4).with_alias("geojson"))
                        for row in rows:
                            geojsons[row[tablename].id] = row.geojson
                    else:
                        # Do the Simplify direct from the DB
                        rows = db(query).select(table.id,
                                                gtable.the_geom.st_simplify(tolerance).st_astext().with_alias("wkt"))
                        for row in rows:
                            wkts[row[tablename].id] = row.wkt
                else:
                    rows = db(query).select(table.id,
                                            gtable.wkt)
                    simplify = GIS.simplify
                    if format == "geojson":
                        for row in rows:
                            # Simplify the polygon to reduce download size
                            geojson = simplify(row["gis_location"].wkt,
                                               tolerance=tolerance,
                                               output="geojson")
                            if geojson:
                                geojsons[row[tablename].id] = geojson
                    else:
                        for row in rows:
                            # Simplify the polygon to reduce download size
                            # & also to work around the recursion limit in libxslt
                            # http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
                            wkt = simplify(row["gis_location"].wkt)
                            if wkt:
                                wkts[row[tablename].id] = wkt

            else:
                # Points
                rows = db(query).select(table.id,
                                        gtable.lat,
                                        gtable.lon)
                for row in rows:
                    _location = row["gis_location"]
                    latlons[row[tablename].id] = (_location.lat, _location.lon)

        _latlons = {}
        if latlons:
            _latlons[tablename] = latlons
        _wkts = {}
        _wkts[tablename] = wkts
        _geojsons = {}
        _geojsons[tablename] = geojsons

        #if DEBUG:
        #    end = datetime.datetime.now()
        #    duration = end - start
        #    duration = "{:.2f}".format(duration.total_seconds())
        #    _debug("latlons lookup of layer %s completed in %s seconds" % \
        #            (layer_name, duration))

        # Used by S3XML's gis_encode()
        return dict(latlons = _latlons,
                    wkts = _wkts,
                    geojsons = _geojsons,
                    markers = markers,
                    tooltips = tooltips,
                    attributes = attributes,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_shapefile_geojson(resource):
        """
            Lookup Shapefile Layer polygons once per layer and not per-record

            Called by S3REST: S3Resource.export_tree()

            @ToDo: Vary simplification level & precision by Zoom level
                   - store this in the style?
        """

        db = current.db
        id = resource._ids[0]
        tablename = "gis_layer_shapefile_%s" % id
        table = db[tablename]
        query = resource.get_query()
        fields = []
        fappend = fields.append
        for f in table.fields:
            if f not in ("layer_id", "lat", "lon"):
                fappend(f)

        attributes = {}
        geojsons = {}
        settings = current.deployment_settings
        tolerance = settings.get_gis_simplify_tolerance()
        if settings.get_gis_spatialdb():
            # Do the Simplify & GeoJSON direct from the DB
            fields.remove("the_geom")
            fields.remove("wkt")
            _fields = [table[f] for f in fields]
            rows = db(query).select(table.the_geom.st_simplify(tolerance).st_asgeojson(precision=4).with_alias("geojson"),
                                    *_fields)
            for row in rows:
                _row = row[tablename]
                id = _row.id
                geojsons[id] = row.geojson
                _attributes = {}
                for f in fields:
                    if f not in ("id"):
                        _attributes[f] = _row[f]
                attributes[id] = _attributes
        else:
            _fields = [table[f] for f in fields]
            rows = db(query).select(*_fields)
            simplify = GIS.simplify
            for row in rows:
                # Simplify the polygon to reduce download size
                geojson = simplify(row.wkt, tolerance=tolerance,
                                   output="geojson")
                id = row.id
                if geojson:
                    geojsons[id] = geojson
                _attributes = {}
                for f in fields:
                    if f not in ("id", "wkt"):
                        _attributes[f] = row[f]
                attributes[id] = _attributes

        _attributes = {}
        _attributes[tablename] = attributes
        _geojsons = {}
        _geojsons[tablename] = geojsons

        # return 'locations'
        return dict(attributes = _attributes,
                    geojsons = _geojsons)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_theme_geojson(resource):
        """
            Lookup Theme Layer polygons once per layer and not per-record

            Called by S3REST: S3Resource.export_tree()

            @ToDo: Vary precision by Lx
                   - store this (& tolerance map) in the style?
        """

        s3db = current.s3db
        tablename = "gis_theme_data"
        table = s3db.gis_theme_data
        gtable = s3db.gis_location
        query = (table.id.belongs(resource._ids)) & \
                (table.location_id == gtable.id)

        geojsons = {}
        # @ToDo: How to get the tolerance to vary by level?
        #        - add Stored Procedure?
        #if current.deployment_settings.get_gis_spatialdb():
        #    # Do the Simplify & GeoJSON direct from the DB
        #    rows = current.db(query).select(table.id,
        #                                    gtable.the_geom.st_simplify(0.01).st_asgeojson(precision=4).with_alias("geojson"))
        #    for row in rows:
        #        geojsons[row["gis_theme_data.id"]] = row.geojson
        #else:
        rows = current.db(query).select(table.id,
                                        gtable.level,
                                        gtable.wkt)
        simplify = GIS.simplify
        tolerance = {"L0": 0.01,
                     "L1": 0.005,
                     "L2": 0.00125,
                     "L3": 0.000625,
                     "L4": 0.0003125,
                     "L5": 0.00015625,
                     }
        for row in rows:
            grow = row.gis_location
            # Simplify the polygon to reduce download size
            geojson = simplify(grow.wkt,
                               tolerance=tolerance[grow.level],
                               output="geojson")
            if geojson:
                geojsons[row["gis_theme_data.id"]] = geojson

        _geojsons = {}
        _geojsons[tablename] = geojsons

        # return 'locations'
        return dict(geojsons = _geojsons)

    # -------------------------------------------------------------------------
    @staticmethod
    def greatCircleDistance(lat1, lon1, lat2, lon2, quick=True):
        """
            Calculate the shortest distance (in km) over the earth's sphere between 2 points
            Formulae from: http://www.movable-type.co.uk/scripts/latlong.html
            (NB We could also use PostGIS functions, where possible, instead of this query)
        """

        import math

        # shortcuts
        cos = math.cos
        sin = math.sin
        radians = math.radians

        if quick:
            # Spherical Law of Cosines (accurate down to around 1m & computationally quick)
            lat1 = radians(lat1)
            lat2 = radians(lat2)
            lon1 = radians(lon1)
            lon2 = radians(lon2)
            distance = math.acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1)) * RADIUS_EARTH
            return distance

        else:
            # Haversine
            #asin = math.asin
            sqrt = math.sqrt
            pow = math.pow
            dLat = radians(lat2 - lat1)
            dLon = radians(lon2 - lon1)
            a = pow(sin(dLat / 2), 2) + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(dLon / 2), 2)
            c = 2 * math.atan2(sqrt(a), sqrt(1 - a))
            #c = 2 * asin(sqrt(a))              # Alternate version
            # Convert radians to kilometers
            distance = RADIUS_EARTH * c
            return distance

    # -------------------------------------------------------------------------
    @staticmethod
    def create_poly(feature):
        """
            Create a .poly file for OpenStreetMap exports
            http://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
        """

        from shapely.wkt import loads as wkt_loads

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        name = feature.name

        if "wkt" in feature:
            wkt = feature.wkt
        else:
            # WKT not included by default in feature, so retrieve this now
            wkt = current.db(table.id == feature.id).select(table.wkt,
                                                            limitby=(0, 1)
                                                            ).first().wkt

        try:
            shape = wkt_loads(wkt)
        except:
            error = "Invalid WKT: %s" % name
            s3_debug(error)
            return error

        geom_type = shape.geom_type
        if geom_type == "MultiPolygon":
            polygons = shape.geoms
        elif geom_type == "Polygon":
            polygons = [shape]
        else:
            error = "Unsupported Geometry: %s, %s" % (name, geom_type)
            s3_debug(error)
            return error
        if os.path.exists(os.path.join(os.getcwd(), "temp")): # use web2py/temp
            TEMP = os.path.join(os.getcwd(), "temp")
        else:
            import tempfile
            TEMP = tempfile.gettempdir()
        filename = "%s.poly" % name
        filepath = os.path.join(TEMP, filename)
        File = open(filepath, "w")
        File.write("%s\n" % filename)
        count = 1
        for polygon in polygons:
            File.write("%s\n" % count)
            points = polygon.exterior.coords
            for point in points:
                File.write("\t%s\t%s\n" % (point[0], point[1]))
            File.write("END\n")
            ++count
        File.write("END\n")
        File.close()

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def export_admin_areas(countries=[],
                           levels=["L0", "L1", "L2", "L3"],
                           format="geojson",
                           simplify=0.01,
                           decimals=4,
                           ):
        """
            Export admin areas to /static/cache for use by interactive web-mapping services
            - designed for use by the Vulnerability Mapping

            @param countries: list of ISO2 country codes
            @param levels: list of which Lx levels to export
            @param format: Only GeoJSON supported for now (may add KML &/or OSM later)
            @param simplify: tolerance for the simplification algorithm. False to disable simplification
            @param decimals: number of decimal points to include in the coordinates
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location
        ifield = table.id
        if countries:
            ttable = s3db.gis_location_tag
            cquery = (table.level == "L0") & \
                     (ttable.location_id == ifield) & \
                     (ttable.tag == "ISO2") & \
                     (ttable.value.belongs(countries))
        else:
            # All countries
            cquery = (table.level == "L0")

        if current.deployment_settings.get_gis_spatialdb():
            spatial = True
            _field = table.the_geom
            if simplify:
                # Do the Simplify & GeoJSON direct from the DB
                field = _field.st_simplify(simplify).st_asgeojson(precision=decimals).with_alias("geojson")
            else:
                # Do the GeoJSON direct from the DB
                field = _field.st_asgeojson(precision=decimals).with_alias("geojson")
        else:
            spatial = False
            field = table.wkt
            if simplify:
                _simplify = GIS.simplify
            else:
                from shapely.wkt import loads as wkt_loads
                from ..geojson import dumps
                try:
                    # Enable C-based speedups available from 1.2.10+
                    from shapely import speedups
                    speedups.enable()
                except:
                    s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        folder = os.path.join(current.request.folder, "static", "cache")

        features = []
        append = features.append

        if "L0" in levels:
            # Reduce the decimals in output by 1
            _decimals = decimals -1
            if spatial:
                if simplify:
                    field = _field.st_simplify(simplify).st_asgeojson(precision=_decimals).with_alias("geojson")
                else:
                    field = _field.st_asgeojson(precision=_decimals).with_alias("geojson")

            countries = db(cquery).select(ifield,
                                          field)
            for row in countries:
                if spatial:
                    id = row["gis_location"].id
                    geojson = row.geojson
                elif simplify:
                    id = row.id
                    wkt = row.wkt
                    if wkt:
                        geojson = _simplify(wkt, tolerance=simplify,
                                            decimals=_decimals,
                                            output="geojson")
                    else:
                        name = db(table.id == id).select(table.name,
                                                         limitby=(0, 1)).first().name
                        print >> sys.stderr, "No WKT: L0 %s %s" % (name, id)
                        continue
                else:
                    id = row.id
                    shape = wkt_loads(row.wkt)
                    # Compact Encoding
                    geojson = dumps(shape, separators=SEPARATORS)
                if geojson:
                    f = dict(type = "Feature",
                             properties = {"id": id},
                             geometry = json.loads(geojson)
                             )
                    append(f)

            if features:
                data = dict(type = "FeatureCollection",
                            features = features
                            )
                # Output to file
                filename = os.path.join(folder, "countries.geojson")
                File = open(filename, "w")
                File.write(json.dumps(data, separators=SEPARATORS))
                File.close()

        q1 = (table.level == "L1") & \
             (table.deleted != True)
        q2 = (table.level == "L2") & \
             (table.deleted != True)
        q3 = (table.level == "L3") & \
             (table.deleted != True)
        q4 = (table.level == "L4") & \
             (table.deleted != True)

        if "L1" in levels:
            if "L0" not in levels:
                countries = db(cquery).select(ifield)
            if simplify:
                # We want greater precision when zoomed-in more
                simplify = simplify / 2 # 0.005 with default setting
                if spatial:
                    field = _field.st_simplify(simplify).st_asgeojson(precision=decimals).with_alias("geojson")
            for country in countries:
                if not spatial or "L0" not in levels:
                    _id = country.id
                else:
                    _id = country["gis_location"].id
                query = q1 & (table.parent == _id)
                features = []
                append = features.append
                rows = db(query).select(ifield,
                                        field)
                for row in rows:
                    if spatial:
                        id = row["gis_location"].id
                        geojson = row.geojson
                    elif simplify:
                        id = row.id
                        wkt = row.wkt
                        if wkt:
                            geojson = _simplify(wkt, tolerance=simplify,
                                                decimals=decimals,
                                                output="geojson")
                        else:
                            name = db(table.id == id).select(table.name,
                                                             limitby=(0, 1)).first().name
                            print >> sys.stderr, "No WKT: L1 %s %s" % (name, id)
                            continue
                    else:
                        id = row.id
                        shape = wkt_loads(row.wkt)
                        # Compact Encoding
                        geojson = dumps(shape, separators=SEPARATORS)
                    if geojson:
                        f = dict(type = "Feature",
                                 properties = {"id": id},
                                 geometry = json.loads(geojson)
                                 )
                        append(f)

                if features:
                    data = dict(type = "FeatureCollection",
                                features = features
                                )
                    # Output to file
                    filename = os.path.join(folder, "1_%s.geojson" % _id)
                    File = open(filename, "w")
                    File.write(json.dumps(data, separators=SEPARATORS))
                    File.close()
                else:
                    s3_debug("No L1 features in %s" % _id)

        if "L2" in levels:
            if "L0" not in levels and "L1" not in levels:
                countries = db(cquery).select(ifield)
            if simplify:
                # We want greater precision when zoomed-in more
                simplify = simplify / 4 # 0.00125 with default setting
                if spatial:
                    field = _field.st_simplify(simplify).st_asgeojson(precision=decimals).with_alias("geojson")
            for country in countries:
                if not spatial or "L0" not in levels:
                    id = country.id
                else:
                    id = country["gis_location"].id
                query = q1 & (table.parent == id)
                l1s = db(query).select(ifield)
                for l1 in l1s:
                    query = q2 & (table.parent == l1.id)
                    features = []
                    append = features.append
                    rows = db(query).select(ifield,
                                            field)
                    for row in rows:
                        if spatial:
                            id = row["gis_location"].id
                            geojson = row.geojson
                        elif simplify:
                            id = row.id
                            wkt = row.wkt
                            if wkt:
                                geojson = _simplify(wkt, tolerance=simplify,
                                                    decimals=decimals,
                                                    output="geojson")
                            else:
                                name = db(table.id == id).select(table.name,
                                                                 limitby=(0, 1)).first().name
                                print >> sys.stderr, "No WKT: L2 %s %s" % (name, id)
                                continue
                        else:
                            id = row.id
                            shape = wkt_loads(row.wkt)
                            # Compact Encoding
                            geojson = dumps(shape, separators=SEPARATORS)
                        if geojson:
                            f = dict(type = "Feature",
                                     properties = {"id": id},
                                     geometry = json.loads(geojson)
                                     )
                            append(f)

                    if features:
                        data = dict(type = "FeatureCollection",
                                    features = features
                                    )
                        # Output to file
                        filename = os.path.join(folder, "2_%s.geojson" % l1.id)
                        File = open(filename, "w")
                        File.write(json.dumps(data, separators=SEPARATORS))
                        File.close()
                    else:
                        s3_debug("No L2 features in %s" % l1.id)

        if "L3" in levels:
            if "L0" not in levels and "L1" not in levels and "L2" not in levels:
                countries = db(cquery).select(ifield)
            if simplify:
                # We want greater precision when zoomed-in more
                simplify = simplify / 2 # 0.000625 with default setting
                if spatial:
                    field = _field.st_simplify(simplify).st_asgeojson(precision=decimals).with_alias("geojson")
            for country in countries:
                if not spatial or "L0" not in levels:
                    id = country.id
                else:
                    id = country["gis_location"].id
                query = q1 & (table.parent == id)
                l1s = db(query).select(ifield)
                for l1 in l1s:
                    query = q2 & (table.parent == l1.id)
                    l2s = db(query).select(ifield)
                    for l2 in l2s:
                        query = q3 & (table.parent == l2.id)
                        features = []
                        append = features.append
                        rows = db(query).select(ifield,
                                                field)
                        for row in rows:
                            if spatial:
                                id = row["gis_location"].id
                                geojson = row.geojson
                            elif simplify:
                                id = row.id
                                wkt = row.wkt
                                if wkt:
                                    geojson = _simplify(wkt, tolerance=simplify,
                                                        decimals=decimals,
                                                        output="geojson")
                                else:
                                    name = db(table.id == id).select(table.name,
                                                                     limitby=(0, 1)).first().name
                                    print >> sys.stderr, "No WKT: L3 %s %s" % (name, id)
                                    continue
                            else:
                                id = row.id
                                shape = wkt_loads(row.wkt)
                                # Compact Encoding
                                geojson = dumps(shape, separators=SEPARATORS)
                            if geojson:
                                f = dict(type = "Feature",
                                         properties = {"id": id},
                                         geometry = json.loads(geojson)
                                         )
                                append(f)

                        if features:
                            data = dict(type = "FeatureCollection",
                                        features = features
                                        )
                            # Output to file
                            filename = os.path.join(folder, "3_%s.geojson" % l2.id)
                            File = open(filename, "w")
                            File.write(json.dumps(data, separators=SEPARATORS))
                            File.close()
                        else:
                            s3_debug("No L3 features in %s" % l2.id)

        if "L4" in levels:
            if "L0" not in levels and "L1" not in levels and "L2" not in levels and "L3" not in levels:
                countries = db(cquery).select(ifield)
            if simplify:
                # We want greater precision when zoomed-in more
                simplify = simplify / 2 # 0.0003125 with default setting
                if spatial:
                    field = _field.st_simplify(simplify).st_asgeojson(precision=decimals).with_alias("geojson")
            for country in countries:
                if not spatial or "L0" not in levels:
                    id = country.id
                else:
                    id = country["gis_location"].id
                query = q1 & (table.parent == id)
                l1s = db(query).select(ifield)
                for l1 in l1s:
                    query = q2 & (table.parent == l1.id)
                    l2s = db(query).select(ifield)
                    for l2 in l2s:
                        query = q3 & (table.parent == l2.id)
                        l3s = db(query).select(ifield)
                        for l3 in l3s:
                            query = q4 & (table.parent == l3.id)
                            features = []
                            append = features.append
                            rows = db(query).select(ifield,
                                                    field)
                            for row in rows:
                                if spatial:
                                    id = row["gis_location"].id
                                    geojson = row.geojson
                                elif simplify:
                                    id = row.id
                                    wkt = row.wkt
                                    if wkt:
                                        geojson = _simplify(wkt, tolerance=simplify,
                                                            decimals=decimals,
                                                            output="geojson")
                                    else:
                                        name = db(table.id == id).select(table.name,
                                                                         limitby=(0, 1)).first().name
                                        print >> sys.stderr, "No WKT: L4 %s %s" % (name, id)
                                        continue
                                else:
                                    id = row.id
                                    shape = wkt_loads(row.wkt)
                                    # Compact Encoding
                                    geojson = dumps(shape, separators=SEPARATORS)
                                if geojson:
                                    f = dict(type = "Feature",
                                             properties = {"id": id},
                                             geometry = json.loads(geojson)
                                             )
                                    append(f)

                            if features:
                                data = dict(type = "FeatureCollection",
                                            features = features
                                            )
                                # Output to file
                                filename = os.path.join(folder, "4_%s.geojson" % l3.id)
                                File = open(filename, "w")
                                File.write(json.dumps(data, separators=SEPARATORS))
                                File.close()
                            else:
                                s3_debug("No L4 features in %s" % l3.id)

    # -------------------------------------------------------------------------
    def import_admin_areas(self,
                           source="gadmv1",
                           countries=[],
                           levels=["L0", "L1", "L2"]
                          ):
        """
           Import Admin Boundaries into the Locations table

           @param source - Source to get the data from.
                           Currently only GADM is supported: http://gadm.org
           @param countries - List of ISO2 countrycodes to download data for
                              defaults to all countries
           @param levels - Which levels of the hierarchy to import.
                           defaults to all 3 supported levels
        """

        if source == "gadmv1":
            try:
                from osgeo import ogr
            except:
                s3_debug("Unable to import ogr. Please install python-gdal bindings: GDAL-1.8.1+")
                return

            if "L0" in levels:
                self.import_gadm1_L0(ogr, countries=countries)
            if "L1" in levels:
                self.import_gadm1(ogr, "L1", countries=countries)
            if "L2" in levels:
                self.import_gadm1(ogr, "L2", countries=countries)

            s3_debug("All done!")

        elif source == "gadmv1":
            try:
                from osgeo import ogr
            except:
                s3_debug("Unable to import ogr. Please install python-gdal bindings: GDAL-1.8.1+")
                return

            if "L0" in levels:
                self.import_gadm2(ogr, "L0", countries=countries)
            if "L1" in levels:
                self.import_gadm2(ogr, "L1", countries=countries)
            if "L2" in levels:
                self.import_gadm2(ogr, "L2", countries=countries)

            s3_debug("All done!")

        else:
            s3_debug("Only GADM is currently supported")
            return

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def import_gadm1_L0(ogr, countries=[]):
        """
           Import L0 Admin Boundaries into the Locations table from GADMv1
           - designed to be called from import_admin_areas()
           - assumes that basic prepop has been done, so that no new records need to be created

           @param ogr - The OGR Python module
           @param countries - List of ISO2 countrycodes to download data for
                              defaults to all countries
        """

        db = current.db
        s3db = current.s3db
        ttable = s3db.gis_location_tag
        table = db.gis_location

        layer = {
            "url" : "http://gadm.org/data/gadm_v1_lev0_shp.zip",
            "zipfile" : "gadm_v1_lev0_shp.zip",
            "shapefile" : "gadm1_lev0",
            "codefield" : "ISO2", # This field is used to uniquely identify the L0 for updates
            "code2field" : "ISO"  # This field is used to uniquely identify the L0 for parenting the L1s
        }

        # Copy the current working directory to revert back to later
        cwd = os.getcwd()

        # Create the working directory
        TEMP = os.path.join(cwd, "temp")
        if not os.path.exists(TEMP): # use web2py/temp/GADMv1 as a cache
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os.path.join(TEMP, "GADMv1")
        if not os.path.exists(tempPath):
            try:
                os.mkdir(tempPath)
            except OSError:
                s3_debug("Unable to create temp folder %s!" % tempPath)
                return

        # Set the current working directory
        os.chdir(tempPath)

        layerName = layer["shapefile"]

        # Check if file has already been downloaded
        fileName = layer["zipfile"]
        if not os.path.isfile(fileName):
            # Download the file
            from gluon.tools import fetch
            url = layer["url"]
            s3_debug("Downloading %s" % url)
            try:
                file = fetch(url)
            except urllib2.URLError, exception:
                s3_debug(exception)
                return
            fp = StringIO(file)
        else:
            s3_debug("Using existing file %s" % fileName)
            fp = open(fileName)

        # Unzip it
        s3_debug("Unzipping %s" % layerName)
        import zipfile
        myfile = zipfile.ZipFile(fp)
        for ext in ["dbf", "prj", "sbn", "sbx", "shp", "shx"]:
            fileName = "%s.%s" % (layerName, ext)
            file = myfile.read(fileName)
            f = open(fileName, "w")
            f.write(file)
            f.close()
        myfile.close()

        # Use OGR to read Shapefile
        s3_debug("Opening %s.shp" % layerName)
        ds = ogr.Open("%s.shp" % layerName)
        if ds is None:
            s3_debug("Open failed.\n")
            return

        lyr = ds.GetLayerByName(layerName)

        lyr.ResetReading()

        codeField = layer["codefield"]
        code2Field = layer["code2field"]
        for feat in lyr:
            code = feat.GetField(codeField)
            if not code:
                # Skip the entries which aren't countries
                continue
            if countries and code not in countries:
                # Skip the countries which we're not interested in
                continue

            geom = feat.GetGeometryRef()
            if geom is not None:
                if geom.GetGeometryType() == ogr.wkbPoint:
                    pass
                else:
                    query = (table.id == ttable.location_id) & \
                            (ttable.tag == "ISO2") & \
                            (ttable.value == code)
                    wkt = geom.ExportToWkt()
                    if wkt.startswith("LINESTRING"):
                        gis_feature_type = 2
                    elif wkt.startswith("POLYGON"):
                        gis_feature_type = 3
                    elif wkt.startswith("MULTIPOINT"):
                        gis_feature_type = 4
                    elif wkt.startswith("MULTILINESTRING"):
                        gis_feature_type = 5
                    elif wkt.startswith("MULTIPOLYGON"):
                        gis_feature_type = 6
                    elif wkt.startswith("GEOMETRYCOLLECTION"):
                        gis_feature_type = 7
                    code2 = feat.GetField(code2Field)
                    #area = feat.GetField("Shape_Area")
                    try:
                        id = db(query).select(table.id,
                                              limitby=(0, 1)).first().id
                        query = (table.id == id)
                        db(query).update(gis_feature_type=gis_feature_type,
                                         wkt=wkt)
                        ttable.insert(location_id = id,
                                      tag = "ISO3",
                                      value = code2)
                        #ttable.insert(location_id = location_id,
                        #              tag = "area",
                        #              value = area)
                    except db._adapter.driver.OperationalError, exception:
                        s3_debug(exception)

            else:
                s3_debug("No geometry\n")

        # Close the shapefile
        ds.Destroy()

        db.commit()

        # Revert back to the working directory as before.
        os.chdir(cwd)

        return

    # -------------------------------------------------------------------------
    def import_gadm1(self, ogr, level="L1", countries=[]):
        """
            Import L1 Admin Boundaries into the Locations table from GADMv1
            - designed to be called from import_admin_areas()
            - assumes a fresh database with just Countries imported

            @param ogr - The OGR Python module
            @param level - "L1" or "L2"
            @param countries - List of ISO2 countrycodes to download data for
                               defaults to all countries
        """

        if level == "L1":
            layer = {
                "url" : "http://gadm.org/data/gadm_v1_lev1_shp.zip",
                "zipfile" : "gadm_v1_lev1_shp.zip",
                "shapefile" : "gadm1_lev1",
                "namefield" : "NAME_1",
                # Uniquely identify the L1 for updates
                "sourceCodeField" : "ID_1",
                "edenCodeField" : "GADM1",
                # Uniquely identify the L0 for parenting the L1s
                "parent" : "L0",
                "parentSourceCodeField" : "ISO",
                "parentEdenCodeField" : "ISO3",
            }
        elif level == "L2":
            layer = {
                "url" : "http://biogeo.ucdavis.edu/data/gadm/gadm_v1_lev2_shp.zip",
                "zipfile" : "gadm_v1_lev2_shp.zip",
                "shapefile" : "gadm_v1_lev2",
                "namefield" : "NAME_2",
                # Uniquely identify the L2 for updates
                "sourceCodeField" : "ID_2",
                "edenCodeField" : "GADM2",
                # Uniquely identify the L0 for parenting the L1s
                "parent" : "L1",
                "parentSourceCodeField" : "ID_1",
                "parentEdenCodeField" : "GADM1",
            }
        else:
            s3_debug("Level %s not supported!" % level)
            return

        import csv
        import shutil
        import zipfile

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location
        ttable = s3db.gis_location_tag

        csv.field_size_limit(2**20 * 100)  # 100 megs

        # Not all the data is encoded like this
        # (unable to determine encoding - appears to be damaged in source):
        # Azerbaijan L1
        # Vietnam L1 & L2
        ENCODING = "cp1251"

        # from http://docs.python.org/library/csv.html#csv-examples
        def latin_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
            for row in csv.reader(unicode_csv_data):
                yield [unicode(cell, ENCODING) for cell in row]

        def latin_dict_reader(data, dialect=csv.excel, **kwargs):
            reader = latin_csv_reader(data, dialect=dialect, **kwargs)
            headers = reader.next()
            for r in reader:
                yield dict(zip(headers, r))

        # Copy the current working directory to revert back to later
        cwd = os.getcwd()

        # Create the working directory
        TEMP = os.path.join(cwd, "temp")
        if not os.path.exists(TEMP): # use web2py/temp/GADMv1 as a cache
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os.path.join(TEMP, "GADMv1")
        if not os.path.exists(tempPath):
            try:
                os.mkdir(tempPath)
            except OSError:
                s3_debug("Unable to create temp folder %s!" % tempPath)
                return

        # Set the current working directory
        os.chdir(tempPath)

        # Remove any existing CSV folder to allow the new one to be created
        try:
            shutil.rmtree("CSV")
        except OSError:
            # Folder doesn't exist, so should be creatable
            pass

        layerName = layer["shapefile"]

        # Check if file has already been downloaded
        fileName = layer["zipfile"]
        if not os.path.isfile(fileName):
            # Download the file
            from gluon.tools import fetch
            url = layer["url"]
            s3_debug("Downloading %s" % url)
            try:
                file = fetch(url)
            except urllib2.URLError, exception:
                s3_debug(exception)
                # Revert back to the working directory as before.
                os.chdir(cwd)
                return
            fp = StringIO(file)
        else:
            s3_debug("Using existing file %s" % fileName)
            fp = open(fileName)

        # Unzip it
        s3_debug("Unzipping %s" % layerName)
        myfile = zipfile.ZipFile(fp)
        for ext in ["dbf", "prj", "sbn", "sbx", "shp", "shx"]:
            fileName = "%s.%s" % (layerName, ext)
            file = myfile.read(fileName)
            f = open(fileName, "w")
            f.write(file)
            f.close()
        myfile.close()

        # Convert to CSV
        s3_debug("Converting %s.shp to CSV" % layerName)
        # Simplified version of generic Shapefile Importer:
        # http://svn.osgeo.org/gdal/trunk/gdal/swig/python/samples/ogr2ogr.py
        bSkipFailures = False
        nGroupTransactions = 200
        nFIDToFetch = ogr.NullFID
        inputFileName = "%s.shp" % layerName
        inputDS = ogr.Open(inputFileName, False)
        outputFileName = "CSV"
        outputDriver = ogr.GetDriverByName("CSV")
        outputDS = outputDriver.CreateDataSource(outputFileName, options=[])
        # GADM only has 1 layer/source
        inputLayer = inputDS.GetLayer(0)
        inputFDefn = inputLayer.GetLayerDefn()
        # Create the output Layer
        outputLayer = outputDS.CreateLayer(layerName)
        # Copy all Fields
        papszFieldTypesToString = []
        inputFieldCount = inputFDefn.GetFieldCount()
        panMap = [-1 for i in range(inputFieldCount)]
        outputFDefn = outputLayer.GetLayerDefn()
        nDstFieldCount = 0
        if outputFDefn is not None:
            nDstFieldCount = outputFDefn.GetFieldCount()
        for iField in range(inputFieldCount):
            inputFieldDefn = inputFDefn.GetFieldDefn(iField)
            oFieldDefn = ogr.FieldDefn(inputFieldDefn.GetNameRef(),
                                       inputFieldDefn.GetType())
            oFieldDefn.SetWidth(inputFieldDefn.GetWidth())
            oFieldDefn.SetPrecision(inputFieldDefn.GetPrecision())
            # The field may have been already created at layer creation
            iDstField = -1;
            if outputFDefn is not None:
                 iDstField = outputFDefn.GetFieldIndex(oFieldDefn.GetNameRef())
            if iDstField >= 0:
                panMap[iField] = iDstField
            elif outputLayer.CreateField(oFieldDefn) == 0:
                # now that we've created a field, GetLayerDefn() won't return NULL
                if outputFDefn is None:
                    outputFDefn = outputLayer.GetLayerDefn()
                panMap[iField] = nDstFieldCount
                nDstFieldCount = nDstFieldCount + 1
        # Transfer features
        nFeaturesInTransaction = 0
        iSrcZField = -1
        inputLayer.ResetReading()
        if nGroupTransactions > 0:
            outputLayer.StartTransaction()
        while True:
            poDstFeature = None
            if nFIDToFetch != ogr.NullFID:
                # Only fetch feature on first pass.
                if nFeaturesInTransaction == 0:
                    poFeature = inputLayer.GetFeature(nFIDToFetch)
                else:
                    poFeature = None
            else:
                poFeature = inputLayer.GetNextFeature()
            if poFeature is None:
                break
            nParts = 0
            nIters = 1
            for iPart in range(nIters):
                nFeaturesInTransaction = nFeaturesInTransaction + 1
                if nFeaturesInTransaction == nGroupTransactions:
                    outputLayer.CommitTransaction()
                    outputLayer.StartTransaction()
                    nFeaturesInTransaction = 0
                poDstFeature = ogr.Feature(outputLayer.GetLayerDefn())
                if poDstFeature.SetFromWithMap(poFeature, 1, panMap) != 0:
                    if nGroupTransactions > 0:
                        outputLayer.CommitTransaction()
                    s3_debug("Unable to translate feature %d from layer %s" % \
                                (poFeature.GetFID(), inputFDefn.GetName()))
                    # Revert back to the working directory as before.
                    os.chdir(cwd)
                    return
                poDstGeometry = poDstFeature.GetGeometryRef()
                if poDstGeometry is not None:
                    if nParts > 0:
                        # For -explodecollections, extract the iPart(th) of the geometry
                        poPart = poDstGeometry.GetGeometryRef(iPart).Clone()
                        poDstFeature.SetGeometryDirectly(poPart)
                        poDstGeometry = poPart
                if outputLayer.CreateFeature(poDstFeature) != 0 and \
                   not bSkipFailures:
                    if nGroupTransactions > 0:
                        outputLayer.RollbackTransaction()
                    # Revert back to the working directory as before.
                    os.chdir(cwd)
                    return
        if nGroupTransactions > 0:
            outputLayer.CommitTransaction()
        # Cleanup
        outputDS.Destroy()
        inputDS.Destroy()

        fileName = "%s.csv" % layerName
        filePath = os.path.join("CSV", fileName)
        os.rename(filePath, fileName)
        os.removedirs("CSV")

        # Use OGR to read SHP for geometry
        s3_debug("Opening %s.shp" % layerName)
        ds = ogr.Open("%s.shp" % layerName)
        if ds is None:
            s3_debug("Open failed.\n")
            # Revert back to the working directory as before.
            os.chdir(cwd)
            return

        lyr = ds.GetLayerByName(layerName)

        lyr.ResetReading()

        # Use CSV for Name
        s3_debug("Opening %s.csv" % layerName)
        rows = latin_dict_reader(open("%s.csv" % layerName))

        nameField = layer["namefield"]
        sourceCodeField = layer["sourceCodeField"]
        edenCodeField = layer["edenCodeField"]
        parentSourceCodeField = layer["parentSourceCodeField"]
        parentLevel = layer["parent"]
        parentEdenCodeField = layer["parentEdenCodeField"]
        parentCodeQuery = (ttable.tag == parentEdenCodeField)
        count = 0
        for row in rows:
            # Read Attributes
            feat = lyr[count]

            parentCode = feat.GetField(parentSourceCodeField)
            query = (table.level == parentLevel) & \
                    parentCodeQuery & \
                    (ttable.value == parentCode)
            parent = db(query).select(table.id,
                                      ttable.value,
                                      limitby=(0, 1),
                                      cache=cache).first()
            if not parent:
                # Skip locations for which we don't have a valid parent
                s3_debug("Skipping - cannot find parent with key: %s, value: %s" % \
                            (parentEdenCodeField, parentCode))
                count += 1
                continue

            if countries:
                # Skip the countries which we're not interested in
                if level == "L1":
                    if parent["gis_location_tag"].value not in countries:
                        #s3_debug("Skipping %s as not in countries list" % parent["gis_location_tag"].value)
                        count += 1
                        continue
                else:
                    # Check grandparent
                    country = self.get_parent_country(parent.id,
                                                      key_type="code")
                    if country not in countries:
                        count += 1
                        continue

            # This is got from CSV in order to be able to handle the encoding
            name = row.pop(nameField)
            name.encode("utf8")

            code = feat.GetField(sourceCodeField)
            area = feat.GetField("Shape_Area")

            geom = feat.GetGeometryRef()
            if geom is not None:
                if geom.GetGeometryType() == ogr.wkbPoint:
                    lat = geom.GetX()
                    lon = geom.GetY()
                    id = table.insert(name=name,
                                      level=level,
                                      gis_feature_type=1,
                                      lat=lat,
                                      lon=lon,
                                      parent=parent.id)
                    ttable.insert(location_id = id,
                                  tag = edenCodeField,
                                  value = code)
                    # ttable.insert(location_id = id,
                                  # tag = "area",
                                  # value = area)
                else:
                    wkt = geom.ExportToWkt()
                    if wkt.startswith("LINESTRING"):
                        gis_feature_type = 2
                    elif wkt.startswith("POLYGON"):
                        gis_feature_type = 3
                    elif wkt.startswith("MULTIPOINT"):
                        gis_feature_type = 4
                    elif wkt.startswith("MULTILINESTRING"):
                        gis_feature_type = 5
                    elif wkt.startswith("MULTIPOLYGON"):
                        gis_feature_type = 6
                    elif wkt.startswith("GEOMETRYCOLLECTION"):
                        gis_feature_type = 7
                    id = table.insert(name=name,
                                      level=level,
                                      gis_feature_type=gis_feature_type,
                                      wkt=wkt,
                                      parent=parent.id)
                    ttable.insert(location_id = id,
                                  tag = edenCodeField,
                                  value = code)
                    # ttable.insert(location_id = id,
                                  # tag = "area",
                                  # value = area)
            else:
                s3_debug("No geometry\n")

            count += 1

        # Close the shapefile
        ds.Destroy()

        db.commit()

        s3_debug("Updating Location Tree...")
        try:
            self.update_location_tree()
        except MemoryError:
            # If doing all L2s, it can break memory limits
            # @ToDo: Check now that we're doing by level
            s3_debug("Memory error when trying to update_location_tree()!")

        db.commit()

        # Revert back to the working directory as before.
        os.chdir(cwd)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def import_gadm2(ogr, level="L0", countries=[]):
        """
            Import Admin Boundaries into the Locations table from GADMv2
            - designed to be called from import_admin_areas()
            - assumes that basic prepop has been done, so that no new L0 records need to be created

            @param ogr - The OGR Python module
            @param level - The OGR Python module
            @param countries - List of ISO2 countrycodes to download data for
                               defaults to all countries

            @ToDo: Complete this
                - not currently possible to get all data from the 1 file easily
                - no ISO2
                - needs updating for gis_location_tag model
                - only the lowest available levels accessible
                - use GADMv1 for L0, L1, L2 & GADMv2 for specific lower?
        """

        if level == "L0":
            codeField = "ISO2"   # This field is used to uniquely identify the L0 for updates
            code2Field = "ISO"   # This field is used to uniquely identify the L0 for parenting the L1s
        elif level == "L1":
            nameField = "NAME_1"
            codeField = "ID_1"   # This field is used to uniquely identify the L1 for updates
            code2Field = "ISO"   # This field is used to uniquely identify the L0 for parenting the L1s
            parent = "L0"
            parentCode = "code2"
        elif level == "L2":
            nameField = "NAME_2"
            codeField = "ID_2"   # This field is used to uniquely identify the L2 for updates
            code2Field = "ID_1"  # This field is used to uniquely identify the L1 for parenting the L2s
            parent = "L1"
            parentCode = "code"
        else:
            s3_debug("Level %s not supported!" % level)
            return

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

        url = "http://gadm.org/data2/gadm_v2_shp.zip"
        zipfile = "gadm_v2_shp.zip"
        shapefile = "gadm2"

        # Copy the current working directory to revert back to later
        old_working_directory = os.getcwd()

        # Create the working directory
        if os.path.exists(os.path.join(os.getcwd(), "temp")): # use web2py/temp/GADMv2 as a cache
            TEMP = os.path.join(os.getcwd(), "temp")
        else:
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os.path.join(TEMP, "GADMv2")
        try:
            os.mkdir(tempPath)
        except OSError:
            # Folder already exists - reuse
            pass

        # Set the current working directory
        os.chdir(tempPath)

        layerName = shapefile

        # Check if file has already been downloaded
        fileName = zipfile
        if not os.path.isfile(fileName):
            # Download the file
            from gluon.tools import fetch
            s3_debug("Downloading %s" % url)
            try:
                file = fetch(url)
            except urllib2.URLError, exception:
                s3_debug(exception)
                return
            fp = StringIO(file)
        else:
            s3_debug("Using existing file %s" % fileName)
            fp = open(fileName)

        # Unzip it
        s3_debug("Unzipping %s" % layerName)
        import zipfile
        myfile = zipfile.ZipFile(fp)
        for ext in ["dbf", "prj", "sbn", "sbx", "shp", "shx"]:
            fileName = "%s.%s" % (layerName, ext)
            file = myfile.read(fileName)
            f = open(fileName, "w")
            f.write(file)
            f.close()
        myfile.close()

        # Use OGR to read Shapefile
        s3_debug("Opening %s.shp" % layerName)
        ds = ogr.Open("%s.shp" % layerName)
        if ds is None:
            s3_debug("Open failed.\n")
            return

        lyr = ds.GetLayerByName(layerName)

        lyr.ResetReading()

        for feat in lyr:
            code = feat.GetField(codeField)
            if not code:
                # Skip the entries which aren't countries
                continue
            if countries and code not in countries:
                # Skip the countries which we're not interested in
                continue

            geom = feat.GetGeometryRef()
            if geom is not None:
                if geom.GetGeometryType() == ogr.wkbPoint:
                    pass
                else:
                    ## FIXME
                    ##query = (table.code == code)
                    wkt = geom.ExportToWkt()
                    if wkt.startswith("LINESTRING"):
                        gis_feature_type = 2
                    elif wkt.startswith("POLYGON"):
                        gis_feature_type = 3
                    elif wkt.startswith("MULTIPOINT"):
                        gis_feature_type = 4
                    elif wkt.startswith("MULTILINESTRING"):
                        gis_feature_type = 5
                    elif wkt.startswith("MULTIPOLYGON"):
                        gis_feature_type = 6
                    elif wkt.startswith("GEOMETRYCOLLECTION"):
                        gis_feature_type = 7
                    code2 = feat.GetField(code2Field)
                    area = feat.GetField("Shape_Area")
                    try:
                        ## FIXME
                        db(query).update(gis_feature_type=gis_feature_type,
                                         wkt=wkt)
                                         #code2=code2,
                                         #area=area
                    except db._adapter.driver.OperationalError, exception:
                        s3_debug(exception)

            else:
                s3_debug("No geometry\n")

        # Close the shapefile
        ds.Destroy()

        db.commit()

        # Revert back to the working directory as before.
        os.chdir(old_working_directory)

        return

    # -------------------------------------------------------------------------
    def import_geonames(self, country, level=None):
        """
            Import Locations from the Geonames database

            @param country: the 2-letter country code
            @param level: the ADM level to import

            Designed to be run from the CLI
            Levels should be imported sequentially.
            It is assumed that L0 exists in the DB already
            L1-L3 may have been imported from Shapefiles with Polygon info
            Geonames can then be used to populate the lower levels of hierarchy
        """

        import codecs

        from shapely.geometry import point
        from shapely.geos import ReadingError
        from shapely.wkt import loads as wkt_loads

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        request = current.request
        settings = current.deployment_settings
        table = s3db.gis_location
        ttable = s3db.gis_location_tag

        url = "http://download.geonames.org/export/dump/" + country + ".zip"

        cachepath = os.path.join(request.folder, "cache")
        filename = country + ".txt"
        filepath = os.path.join(cachepath, filename)
        if os.access(filepath, os.R_OK):
            cached = True
        else:
            cached = False
            if not os.access(cachepath, os.W_OK):
                s3_debug("Folder not writable", cachepath)
                return

        if not cached:
            # Download File
            from gluon.tools import fetch
            try:
                f = fetch(url)
            except (urllib2.URLError,):
                e = sys.exc_info()[1]
                s3_debug("URL Error", e)
                return
            except (urllib2.HTTPError,):
                e = sys.exc_info()[1]
                s3_debug("HTTP Error", e)
                return

            # Unzip File
            if f[:2] == "PK":
                # Unzip
                fp = StringIO(f)
                import zipfile
                myfile = zipfile.ZipFile(fp)
                try:
                    # Python 2.6+ only :/
                    # For now, 2.5 users need to download/unzip manually to cache folder
                    myfile.extract(filename, cachepath)
                    myfile.close()
                except IOError:
                    s3_debug("Zipfile contents don't seem correct!")
                    myfile.close()
                    return

        f = codecs.open(filepath, encoding="utf-8")
        # Downloaded file is worth keeping
        #os.remove(filepath)

        if level == "L1":
            fc = "ADM1"
            parent_level = "L0"
        elif level == "L2":
            fc = "ADM2"
            parent_level = "L1"
        elif level == "L3":
            fc = "ADM3"
            parent_level = "L2"
        elif level == "L4":
            fc = "ADM4"
            parent_level = "L3"
        else:
            # 5 levels of hierarchy or 4?
            # @ToDo make more extensible still
            gis_location_hierarchy = self.get_location_hierarchy()
            try:
                label = gis_location_hierarchy["L5"]
                level = "L5"
                parent_level = "L4"
            except:
                # ADM4 data in Geonames isn't always good (e.g. PK bad)
                level = "L4"
                parent_level = "L3"
            finally:
                fc = "PPL"

        deleted = (table.deleted == False)
        query = deleted & (table.level == parent_level)
        # Do the DB query once (outside loop)
        all_parents = db(query).select(table.wkt,
                                       table.lon_min,
                                       table.lon_max,
                                       table.lat_min,
                                       table.lat_max,
                                       table.id)
        if not all_parents:
            # No locations in the parent level found
            # - use the one higher instead
            parent_level = "L" + str(int(parent_level[1:]) + 1)
            query = deleted & (table.level == parent_level)
            all_parents = db(query).select(table.wkt,
                                           table.lon_min,
                                           table.lon_max,
                                           table.lat_min,
                                           table.lat_max,
                                           table.id)

        # Parse File
        current_row = 0
        for line in f:
            current_row += 1
            # Format of file: http://download.geonames.org/export/dump/readme.txt
            geonameid,
            name,
            asciiname,
            alternatenames,
            lat,
            lon,
            feature_class,
            feature_code,
            country_code,
            cc2,
            admin1_code,
            admin2_code,
            admin3_code,
            admin4_code,
            population,
            elevation,
            gtopo30,
            timezone,
            modification_date = line.split("\t")

            if feature_code == fc:
                # Add WKT
                lat = float(lat)
                lon = float(lon)
                wkt = self.latlon_to_wkt(lat, lon)

                shape = point.Point(lon, lat)

                # Add Bounds
                lon_min = lon_max = lon
                lat_min = lat_max = lat

                # Locate Parent
                parent = ""
                # 1st check for Parents whose bounds include this location (faster)
                def in_bbox(row):
                    return (row.lon_min < lon_min) & \
                           (row.lon_max > lon_max) & \
                           (row.lat_min < lat_min) & \
                           (row.lat_max > lat_max)
                for row in all_parents.find(lambda row: in_bbox(row)):
                    # Search within this subset with a full geometry check
                    # Uses Shapely.
                    # @ToDo provide option to use PostGIS/Spatialite
                    try:
                        parent_shape = wkt_loads(row.wkt)
                        if parent_shape.intersects(shape):
                            parent = row.id
                            # Should be just a single parent
                            break
                    except ReadingError:
                        s3_debug("Error reading wkt of location with id", row.id)

                # Add entry to database
                new_id = table.insert(name=name,
                                      level=level,
                                      parent=parent,
                                      lat=lat,
                                      lon=lon,
                                      wkt=wkt,
                                      lon_min=lon_min,
                                      lon_max=lon_max,
                                      lat_min=lat_min,
                                      lat_max=lat_max)
                ttable.insert(location_id=new_id,
                              tag="geonames",
                              value=geonames_id)
            else:
                continue

        s3_debug("All done!")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def latlon_to_wkt(lat, lon):
        """
            Convert a LatLon to a WKT string

            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = "POINT(%f %f)" % (lon, lat)
        return WKT

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_location(wkt, lon=None, lat=None):
        """
            Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if Shapely is not available.
        """

        if not wkt:
            if not lon is not None and lat is not None:
                raise RuntimeError, "Need wkt or lon+lat to parse a location"
            wkt = "POINT(%f %f)" % (lon, lat)
            geom_type = GEOM_TYPES["point"]
            bbox = (lon, lat, lon, lat)
        else:
            try:
                from shapely.wkt import loads as wkt_loads
                SHAPELY = True
            except:
                SHAPELY = False

            if SHAPELY:
                shape = wkt_loads(wkt)
                centroid = shape.centroid
                lat = centroid.y
                lon = centroid.x
                geom_type = GEOM_TYPES[shape.type.lower()]
                bbox = shape.bounds
            else:
                lat = None
                lon = None
                geom_type = GEOM_TYPES[wkt.split("(")[0].lower()]
                bbox = None

        res = {"wkt": wkt, "lat": lat, "lon": lon, "gis_feature_type": geom_type}
        if bbox:
            res["lon_min"], res["lat_min"], res["lon_max"], res["lat_max"] = bbox

        return res

    # -------------------------------------------------------------------------
    @staticmethod
    def update_location_tree(feature=None):
        """
            Update GIS Locations' Materialized path, Lx locations, Lat/Lon & the_geom

            @param feature: a feature dict to update the tree for
            - if not provided then update the whole tree

            returns the path of the feature

            Called onaccept for locations (async, where-possible)
        """

        db = current.db
        try:
            table = db.gis_location
        except:
            table = current.s3db.gis_location
        spatial = current.deployment_settings.get_gis_spatialdb()
        wkt_centroid = GIS.wkt_centroid

        def bounds_centroid_wkt(feature):
            form = Storage()
            form.vars = feature
            form.errors = Storage()
            wkt_centroid(form)
            vars = form.vars
            if "lat_max" in vars:
                wkt = vars.wkt
                _vars = dict(gis_feature_type = vars.gis_feature_type,
                             lat = vars.lat,
                             lon = vars.lon,
                             wkt = wkt,
                             lat_max = vars.lat_max,
                             lat_min = vars.lat_min,
                             lon_min = vars.lon_min,
                             lon_max = vars.lon_max)
                if wkt:
                    if not wkt.startswith("POI"):
                        # Polygons aren't inherited
                        _vars.update(inherited = False)
                    if spatial:
                        _vars.update(the_geom = wkt)
                db(table.id == feature.id).update(**_vars)

        if not feature:
            # Do the whole database
            # Do in chunks to save memory and also do in correct order
            fields = [table.id, table.name, table.gis_feature_type,
                      table.L0, table.L1, table.L2, table.L3, table.L4,
                      table.lat, table.lon, table.wkt, table.inherited,
                      # Handle Countries which start with Bounds set, yet are Points
                      table.lat_min, table.lon_min, table.lat_max, table.lon_max,
                      table.path, table.parent]
            update_location_tree = GIS.update_location_tree
            for level in ["L0", "L1", "L2", "L3", "L4", "L5", None]:
                features = db(table.level == level).select(*fields)
                for feature in features:
                    feature["level"] = level
                    update_location_tree(feature)
                    # Also do the Bounds/Centroid/WKT
                    bounds_centroid_wkt(feature)
            return

        # Single Feature
        id = str(feature["id"]) if "id" in feature else None
        if not id:
            # Nothing we can do
            raise ValueError

        # L0
        name = feature.get("name", False)
        level = feature.get("level", False)
        path = feature.get("path", False)
        L0 = feature.get("L0", False)
        if level == "L0":
            if name:
                if path == id and L0 == name:
                    # No action required
                    return path
                else:
                    db(table.id == id).update(L0=name,
                                              path=id)
            else:
                # Look this up
                feature = db(table.id == id).select(table.name,
                                                    table.path,
                                                    table.L0,
                                                    limitby=(0, 1)).first()
                if feature:
                    name = feature["name"]
                    path = feature["path"]
                    L0 = feature["L0"]
                    if path == id and L0 == name:
                        # No action required
                        return path
                    else:
                        db(table.id == id).update(L0=name,
                                                  path=id)
            return id

        # L1
        parent = feature.get("parent", False)
        L1 = feature.get("L1", False)
        lat = feature.get("lat", False)
        lon = feature.get("lon", False)
        inherited = feature.get("inherited", None)
        if level == "L1":
            if name is False or lat is False or lon is False or inherited is None or \
               parent is False or path is False or L0 is False or L1 is False:
                # Get the whole feature
                feature = db(table.id == id).select(table.name,
                                                    table.parent,
                                                    table.path,
                                                    table.lat,
                                                    table.lon,
                                                    table.inherited,
                                                    table.L0,
                                                    table.L1,
                                                    limitby=(0, 1)).first()
                name = feature.name
                parent = feature.parent
                path = feature.path
                lat = feature.lat
                lon = feature.lon
                inherited = feature.inherited
                L0 = feature.L0
                L1 = feature.L1

            if parent:
                _path = "%s/%s" % (parent, id)
                _L0 = db(table.id == parent).select(table.name,
                                                    table.lat,
                                                    table.lon,
                                                    limitby=(0, 1)).first()
                L0_name = _L0.name
                L0_lat = _L0.lat
                L0_lon = _L0.lon
            else:
                _path = id
                L0_name = None
                L0_lat = None
                L0_lon = None

            if path == _path and L1 == name and L0 == L0_name:
                if inherited and lat == L0_lat and lon == L0_lon:
                    # No action required
                    return path
                elif inherited or lat is None or lon is None:
                    vars = dict(inherited=True,
                                lat=L0_lat,
                                lon=L0_lon,
                                )
                    db(table.id == id).update(**vars)
                    # Also do the Bounds/Centroid/WKT
                    vars.update(id=id,
                                gis_feature_type="1",
                                )
                    feature.update(**vars)
                    bounds_centroid_wkt(feature)
            elif inherited and lat == L0_lat and lon == L0_lon:
                db(table.id == id).update(path=_path,
                                          L0=L0_name,
                                          L1=name)
                return _path
            elif inherited or lat is None or lon is None:
                vars = dict(path=_path,
                            L0=L0_name,
                            L1=name,
                            inherited=True,
                            lat=L0_lat,
                            lon=L0_lon)
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
            else:
                db(table.id == id).update(path=_path,
                                          inherited=False,
                                          L0=L0_name,
                                          L1=name)
            # Ensure that any locations which inherit their latlon from this one get updated
            query = (table.parent == id) & \
                    (table.inherited == True)
            fields = [table.id, table.name, table.level, table.path, table.parent,
                      table.L0, table.L1, table.L2, table.L3, table.L4,
                      table.lat, table.lon, table.inherited]
            rows = db(query).select(*fields)
            update_location_tree = GIS.update_location_tree
            for row in rows:
                update_location_tree(row)
            return _path

        # L2
        L2 = feature.get("L2", False)
        if level == "L2":
            if name is False or lat is False or lon is False or inherited is None or \
               parent is False or path is False or L0 is False or L1 is False or \
                                                   L2 is False:
                # Get the whole feature
                feature = db(table.id == id).select(table.name,
                                                    table.parent,
                                                    table.path,
                                                    table.lat,
                                                    table.lon,
                                                    table.inherited,
                                                    table.L0,
                                                    table.L1,
                                                    table.L2,
                                                    limitby=(0, 1)).first()
                name = feature.name
                parent = feature.parent
                path = feature.path
                lat = feature.lat
                lon = feature.lon
                inherited = feature.inherited
                L0 = feature.L0
                L1 = feature.L1
                L2 = feature.L2

            if parent:
                Lx = db(table.id == parent).select(table.name,
                                                   table.level,
                                                   table.parent,
                                                   table.lat,
                                                   table.lon,
                                                   limitby=(0, 1)).first()
                if Lx.level == "L1":
                    L1_name = Lx.name
                    _parent = Lx.parent
                    if _parent:
                        _path = "%s/%s/%s" % (_parent, parent, id)
                        L0_name = db(table.id == _parent).select(table.name,
                                                                 limitby=(0, 1),
                                                                 cache=current.s3db.cache).first().name
                    else:
                        _path = "%s/%s" % (parent, id)
                        L0_name = None
                elif Lx.level == "L0":
                    _path = "%s/%s" % (parent, id)
                    L0_name = Lx.name
                    L1_name = None
                else:
                    s3_debug("Parent of L2 Location ID %s has invalid level: %s is %s" % \
                                (id, parent, Lx.level))
                    #raise ValueError
                    return "%s/%s" % (parent, id)
                Lx_lat = Lx.lat
                Lx_lon = Lx.lon
            else:
                _path = id
                L0_name = None
                L1_name = None
                Lx_lat = None
                Lx_lon = None

            if path == _path and L2 == name and L0 == L0_name and \
                                                L1 == L1_name:
                if inherited and lat == Lx_lat and lon == Lx_lon:
                    # No action required
                    return path
                elif inherited or lat is None or lon is None:
                    vars = dict(inherited=True,
                                lat=Lx_lat,
                                lon=Lx_lon,
                                )
                    db(table.id == id).update(**vars)
                    # Also do the Bounds/Centroid/WKT
                    vars.update(id=id,
                                gis_feature_type="1",
                                )
                    feature.update(**vars)
                    bounds_centroid_wkt(feature)
            elif inherited and lat == Lx_lat and lon == Lx_lon:
                db(table.id == id).update(path=_path,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=name,
                                          )
                return _path
            elif inherited or lat is None or lon is None:
                vars = dict(path=_path,
                            L0=L0_name,
                            L1=L1_name,
                            L2=name,
                            inherited=True,
                            lat=Lx_lat,
                            lon=Lx_lon)
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
            else:
                db(table.id == id).update(path=_path,
                                          inherited=False,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=name)
            # Ensure that any locations which inherit their latlon from this one get updated
            query = (table.parent == id) & \
                    (table.inherited == True)
            fields = [table.id, table.name, table.level, table.path, table.parent,
                      table.L0, table.L1, table.L2, table.L3, table.L4,
                      table.lat, table.lon, table.inherited]
            rows = db(query).select(*fields)
            update_location_tree = GIS.update_location_tree
            for row in rows:
                update_location_tree(row)
            return _path

        # L3
        L3 = feature.get("L3", False)
        if level == "L3":
            if name is False or lat is False or lon is False or inherited is None or \
               parent is False or path is False or L0 is False or L1 is False or \
                                                   L2 is False or L3 is False:
                # Get the whole feature
                feature = db(table.id == id).select(table.name,
                                                    table.parent,
                                                    table.path,
                                                    table.lat,
                                                    table.lon,
                                                    table.inherited,
                                                    table.L0,
                                                    table.L1,
                                                    table.L2,
                                                    table.L3,
                                                    limitby=(0, 1)).first()
                name = feature.name
                parent = feature.parent
                path = feature.path
                lat = feature.lat
                lon = feature.lon
                inherited = feature.inherited
                L0 = feature.L0
                L1 = feature.L1
                L2 = feature.L2
                L3 = feature.L3

            if parent:
                Lx = db(table.id == parent).select(table.id,
                                                   table.name,
                                                   table.level,
                                                   table.L0,
                                                   table.L1,
                                                   table.path,
                                                   table.lat,
                                                   table.lon,
                                                   limitby=(0, 1)).first()
                if Lx.level == "L2":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.name
                    _path = Lx.path
                    if _path and L0_name and L1_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                elif Lx.level == "L1":
                    L0_name = Lx.L0
                    L1_name = Lx.name
                    L2_name = None
                    _path = Lx.path
                    if _path and L0_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                elif Lx.level == "L0":
                    _path = "%s/%s" % (parent, id)
                    L0_name = Lx.name
                    L1_name = None
                    L2_name = None
                else:
                    s3_debug("Parent of L3 Location ID %s has invalid level: %s is %s" % \
                                (id, parent, Lx.level))
                    #raise ValueError
                    return "%s/%s" % (parent, id)
                Lx_lat = Lx.lat
                Lx_lon = Lx.lon
            else:
                _path = id
                L0_name = None
                L1_name = None
                L2_name = None
                Lx_lat = None
                Lx_lon = None

            if path == _path and L3 == name and L0 == L0_name and \
                                 L1 == L1_name and L2 == L2_name:
                if inherited and lat == Lx_lat and lon == Lx_lon:
                    # No action required
                    return path
                elif inherited or lat is None or lon is None:
                    vars = dict(inherited=True,
                                lat=Lx_lat,
                                lon=Lx_lon,
                                )
                    db(table.id == id).update(**vars)
                    # Also do the Bounds/Centroid/WKT
                    vars.update(id=id,
                                gis_feature_type="1",
                                )
                    bounds_centroid_wkt(feature)
            elif inherited and lat == Lx_lat and lon == Lx_lon:
                db(table.id == id).update(path=_path,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=name,
                                          )
                return _path
            elif inherited or lat is None or lon is None:
                vars = dict(path=_path,
                            L0=L0_name,
                            L1=L1_name,
                            L2=L2_name,
                            L3=name,
                            inherited=True,
                            lat=Lx_lat,
                            lon=Lx_lon)
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
            else:
                db(table.id == id).update(path=_path,
                                          inherited=False,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=name)
            # Ensure that any locations which inherit their latlon from this one get updated
            query = (table.parent == id) & \
                    (table.inherited == True)
            fields = [table.id, table.name, table.level, table.path, table.parent,
                      table.L0, table.L1, table.L2, table.L3, table.L4,
                      table.lat, table.lon, table.inherited]
            rows = db(query).select(*fields)
            update_location_tree = GIS.update_location_tree
            for row in rows:
                update_location_tree(row)
            return _path

        # L4
        L4 = feature.get("L4", False)
        if level == "L4":
            if name is False or lat is False or lon is False or inherited is None or \
               parent is False or path is False or L0 is False or L1 is False or \
                                                   L2 is False or L3 is False or \
                                                   L4 is False:
                # Get the whole feature
                feature = db(table.id == id).select(table.name,
                                                    table.parent,
                                                    table.path,
                                                    table.lat,
                                                    table.lon,
                                                    table.inherited,
                                                    table.L0,
                                                    table.L1,
                                                    table.L2,
                                                    table.L3,
                                                    table.L4,
                                                    limitby=(0, 1)).first()
                name = feature.name
                parent = feature.parent
                path = feature.path
                lat = feature.lat
                lon = feature.lon
                inherited = feature.inherited
                L0 = feature.L0
                L1 = feature.L1
                L2 = feature.L2
                L3 = feature.L3
                L4 = feature.L4

            if parent:
                Lx = db(table.id == parent).select(table.id,
                                                   table.name,
                                                   table.level,
                                                   table.L0,
                                                   table.L1,
                                                   table.L2,
                                                   table.path,
                                                   table.lat,
                                                   table.lon,
                                                   limitby=(0, 1)).first()
                if Lx.level == "L3":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
                    L3_name = Lx.name
                    _path = Lx.path
                    if _path and L0_name and L1_name and L2_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.L2,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                        L2_name = Lx.L2
                elif Lx.level == "L2":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.name
                    L3_name = None
                    _path = Lx.path
                    if _path and L0_name and L1_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                elif Lx.level == "L1":
                    L0_name = Lx.L0
                    L1_name = Lx.name
                    L2_name = None
                    L3_name = None
                    _path = Lx.path
                    if _path and L0_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                elif Lx.level == "L0":
                    _path = "%s/%s" % (parent, id)
                    L0_name = Lx.name
                    L1_name = None
                    L2_name = None
                    L3_name = None
                else:
                    s3_debug("Parent of L4 Location ID %s has invalid level: %s is %s" % \
                                (id, parent, Lx.level))
                    #raise ValueError
                    return "%s/%s" % (parent, id)
                Lx_lat = Lx.lat
                Lx_lon = Lx.lon
            else:
                _path = id
                L0_name = None
                L1_name = None
                L2_name = None
                L3_name = None
                Lx_lat = None
                Lx_lon = None

            if path == _path and L4 == name and L0 == L0_name and \
                                 L1 == L1_name and L2 == L2_name and \
                                 L3 == L3_name:
                if inherited and lat == Lx_lat and lon == Lx_lon:
                    # No action required
                    return path
                elif inherited or lat is None or lon is None:
                    vars = dict(inherited=True,
                                lat=Lx_lat,
                                lon=Lx_lon,
                                )
                    db(table.id == id).update(**vars)
                    # Also do the Bounds/Centroid/WKT
                    vars.update(id=id,
                                gis_feature_type="1",
                                )
                    feature.update(**vars)
                    bounds_centroid_wkt(feature)
            elif inherited and lat == Lx_lat and lon == Lx_lon:
                db(table.id == id).update(path=_path,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=L3_name,
                                          L4=name,
                                          )
                return _path
            elif inherited or lat is None or lon is None:
                vars = dict(path=_path,
                            L0=L0_name,
                            L1=L1_name,
                            L2=L2_name,
                            L3=L3_name,
                            L4=name,
                            inherited=True,
                            lat=Lx_lat,
                            lon=Lx_lon)
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
            else:
                db(table.id == id).update(path=_path,
                                          inherited=False,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=L3_name,
                                          L4=name)
            # Ensure that any locations which inherit their latlon from this one get updated
            query = (table.parent == id) & \
                    (table.inherited == True)
            fields = [table.id, table.name, table.level, table.path, table.parent,
                      table.L0, table.L1, table.L2, table.L3, table.L4,
                      table.lat, table.lon, table.inherited]
            rows = db(query).select(*fields)
            update_location_tree = GIS.update_location_tree
            for row in rows:
                update_location_tree(row)
            return _path

        # L5
        L5 = feature.get("L5", False)
        if level == "L5":
            if name is False or lat is False or lon is False or inherited is None or \
               parent is False or path is False or L0 is False or L1 is False or \
                                                   L2 is False or L3 is False or \
                                                   L4 is False or L5 is False:
                # Get the whole feature
                feature = db(table.id == id).select(table.name,
                                                    table.parent,
                                                    table.path,
                                                    table.lat,
                                                    table.lon,
                                                    table.inherited,
                                                    table.L0,
                                                    table.L1,
                                                    table.L2,
                                                    table.L3,
                                                    table.L4,
                                                    table.L5,
                                                    limitby=(0, 1)).first()
                name = feature.name
                parent = feature.parent
                path = feature.path
                lat = feature.lat
                lon = feature.lon
                inherited = feature.inherited
                L0 = feature.L0
                L1 = feature.L1
                L2 = feature.L2
                L3 = feature.L3
                L4 = feature.L4
                L5 = feature.L5

            if parent:
                Lx = db(table.id == parent).select(table.id,
                                                   table.name,
                                                   table.level,
                                                   table.L0,
                                                   table.L1,
                                                   table.L2,
                                                   table.L3,
                                                   table.path,
                                                   table.lat,
                                                   table.lon,
                                                   limitby=(0, 1)).first()
                if Lx.level == "L4":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
                    L3_name = Lx.L3
                    L4_name = Lx.name
                    _path = Lx.path
                    if _path and L0_name and L1_name and L2_name and L3_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.L2,
                                                           table.L3,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                        L2_name = Lx.L2
                        L3_name = Lx.L3
                elif Lx.level == "L3":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
                    L3_name = Lx.name
                    L4_name = None
                    _path = Lx.path
                    if _path and L0_name and L1_name and L2_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.L2,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                        L2_name = Lx.L2
                elif Lx.level == "L2":
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.name
                    L3_name = None
                    L4_name = None
                    _path = Lx.path
                    if _path and L0_name and L1_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.L1,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                        L1_name = Lx.L1
                elif Lx.level == "L1":
                    L0_name = Lx.L0
                    L1_name = Lx.name
                    L2_name = None
                    L3_name = None
                    L4_name = None
                    _path = Lx.path
                    if _path and L0_name:
                        _path = "%s/%s" % (_path, id)
                    else:
                        # This feature needs to be updated
                        _path = GIS.update_location_tree(Lx)
                        _path = "%s/%s" % (_path, id)
                        # Query again
                        Lx = db(table.id == parent).select(table.L0,
                                                           table.lat,
                                                           table.lon,
                                                           limitby=(0, 1)
                                                           ).first()
                        L0_name = Lx.L0
                elif Lx.level == "L0":
                    _path = "%s/%s" % (parent, id)
                    L0_name = Lx.name
                    L1_name = None
                    L2_name = None
                    L3_name = None
                    L4_name = None
                else:
                    s3_debug("Parent of L5 Location ID %s has invalid level: %s is %s" % \
                                (id, parent, Lx.level))
                    #raise ValueError
                    return "%s/%s" % (parent, id)
                Lx_lat = Lx.lat
                Lx_lon = Lx.lon
            else:
                _path = id
                L0_name = None
                L1_name = None
                L2_name = None
                L3_name = None
                L4_name = None
                Lx_lat = None
                Lx_lon = None

            if path == _path and L5 == name and L0 == L0_name and \
                                 L1 == L1_name and L2 == L2_name and \
                                 L3 == L3_name and L4 == L4_name:
                if inherited and lat == Lx_lat and lon == Lx_lon:
                    # No action required
                    return path
                elif inherited or lat is None or lon is None:
                    vars = dict(inherited=True,
                                lat=Lx_lat,
                                lon=Lx_lon,
                                )
                    db(table.id == id).update(**vars)
                    # Also do the Bounds/Centroid/WKT
                    vars.update(id=id,
                                gis_feature_type="1",
                                )
                    feature.update(**vars)
                    bounds_centroid_wkt(feature)
            elif inherited and lat == Lx_lat and lon == Lx_lon:
                db(table.id == id).update(path=_path,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=L3_name,
                                          L4=L4_name,
                                          L5=name,
                                          )
                return _path
            elif inherited or lat is None or lon is None:
                vars = dict(path=_path,
                            L0=L0_name,
                            L1=L1_name,
                            L2=L2_name,
                            L3=L3_name,
                            L4=L4_name,
                            L5=name,
                            inherited=True,
                            lat=Lx_lat,
                            lon=Lx_lon)
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
            else:
                db(table.id == id).update(path=_path,
                                          inherited=False,
                                          L0=L0_name,
                                          L1=L1_name,
                                          L2=L2_name,
                                          L3=L3_name,
                                          L4=L4_name,
                                          L5=name)
            # Ensure that any locations which inherit their latlon from this one get updated
            query = (table.parent == id) & \
                    (table.inherited == True)
            fields = [table.id, table.name, table.level, table.path, table.parent,
                      table.L0, table.L1, table.L2, table.L3, table.L4, table.L5,
                      table.lat, table.lon, table.inherited]
            rows = db(query).select(*fields)
            update_location_tree = GIS.update_location_tree
            for row in rows:
                update_location_tree(row)
            return _path

        # Specific Location
        # - or unspecified (which we should avoid happening)
        if name is False or lat is False or lon is False or inherited is None or \
           parent is False or path is False or L0 is False or L1 is False or \
                                               L2 is False or L3 is False or \
                                               L4 is False or L5 is False:
            # Get the whole feature
            feature = db(table.id == id).select(table.name,
                                                table.level,
                                                table.parent,
                                                table.path,
                                                table.lat,
                                                table.lon,
                                                table.inherited,
                                                table.L0,
                                                table.L1,
                                                table.L2,
                                                table.L3,
                                                table.L4,
                                                table.L5,
                                                limitby=(0, 1)).first()
            name = feature.name
            parent = feature.parent
            path = feature.path
            lat = feature.lat
            lon = feature.lon
            inherited = feature.inherited
            L0 = feature.L0
            L1 = feature.L1
            L2 = feature.L2
            L3 = feature.L3
            L4 = feature.L4
            L5 = feature.L5

        if parent:
            Lx = db(table.id == parent).select(table.id,
                                               table.name,
                                               table.level,
                                               table.L0,
                                               table.L1,
                                               table.L2,
                                               table.L3,
                                               table.L4,
                                               table.path,
                                               table.lat,
                                               table.lon,
                                               limitby=(0, 1)).first()
            if Lx.level == "L5":
                L0_name = Lx.L0
                L1_name = Lx.L1
                L2_name = Lx.L2
                L3_name = Lx.L3
                L4_name = Lx.L4
                L5_name = Lx.name
                _path = Lx.path
                if _path and L0_name and L1_name and L2_name and L3_name and L4_name:
                    _path = "%s/%s" % (_path, id)

                else:
                    # This feature needs to be updated
                    _path = GIS.update_location_tree(Lx)
                    _path = "%s/%s" % (_path, id)
                    # Query again
                    Lx = db(table.id == parent).select(table.L0,
                                                       table.L1,
                                                       table.L2,
                                                       table.L3,
                                                       table.L4,
                                                       table.lat,
                                                       table.lon,
                                                       limitby=(0, 1)).first()
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
                    L3_name = Lx.L3
                    L4_name = Lx.L4
            elif Lx.level == "L4":
                L0_name = Lx.L0
                L1_name = Lx.L1
                L2_name = Lx.L2
                L3_name = Lx.L3
                L4_name = Lx.name
                L5_name = None
                _path = Lx.path
                if _path and L0_name and L1_name and L2_name and L3_name:
                    _path = "%s/%s" % (_path, id)
                else:
                    # This feature needs to be updated
                    _path = GIS.update_location_tree(Lx)
                    _path = "%s/%s" % (_path, id)
                    # Query again
                    Lx = db(table.id == parent).select(table.L0,
                                                       table.L1,
                                                       table.L2,
                                                       table.L3,
                                                       table.lat,
                                                       table.lon,
                                                       limitby=(0, 1)).first()
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
                    L3_name = Lx.L3
            elif Lx.level == "L3":
                L0_name = Lx.L0
                L1_name = Lx.L1
                L2_name = Lx.L2
                L3_name = Lx.name
                L4_name = None
                L5_name = None
                _path = Lx.path
                if _path and L0_name and L1_name and L2_name:
                    _path = "%s/%s" % (_path, id)
                else:
                    # This feature needs to be updated
                    _path = GIS.update_location_tree(Lx)
                    _path = "%s/%s" % (_path, id)
                    # Query again
                    Lx = db(table.id == parent).select(table.L0,
                                                       table.L1,
                                                       table.L2,
                                                       table.lat,
                                                       table.lon,
                                                       limitby=(0, 1)).first()
                    L0_name = Lx.L0
                    L1_name = Lx.L1
                    L2_name = Lx.L2
            elif Lx.level == "L2":
                L0_name = Lx.L0
                L1_name = Lx.L1
                L2_name = Lx.name
                L3_name = None
                L4_name = None
                L5_name = None
                _path = Lx.path
                if _path and L0_name and L1_name:
                    _path = "%s/%s" % (_path, id)
                else:
                    # This feature needs to be updated
                    _path = GIS.update_location_tree(Lx)
                    _path = "%s/%s" % (_path, id)
                    # Query again
                    Lx = db(table.id == parent).select(table.L0,
                                                       table.L1,
                                                       table.lat,
                                                       table.lon,
                                                       limitby=(0, 1)).first()
                    L0_name = Lx.L0
                    L1_name = Lx.L1
            elif Lx.level == "L1":
                L0_name = Lx.L0
                L1_name = Lx.name
                L2_name = None
                L3_name = None
                L4_name = None
                L5_name = None
                _path = Lx.path
                if _path and L0_name:
                    _path = "%s/%s" % (_path, id)
                else:
                    # This feature needs to be updated
                    _path = GIS.update_location_tree(Lx)
                    _path = "%s/%s" % (_path, id)
                    # Query again
                    Lx = db(table.id == parent).select(table.L0,
                                                       table.lat,
                                                       table.lon,
                                                       limitby=(0, 1)).first()
                    L0_name = Lx.L0
            elif Lx.level == "L0":
                _path = "%s/%s" % (parent, id)
                L0_name = Lx.name
                L1_name = None
                L2_name = None
                L3_name = None
                L4_name = None
                L5_name = None
            else:
                #raise ValueError
                return id
            Lx_lat = Lx.lat
            Lx_lon = Lx.lon
        else:
            _path = id
            if feature.level == "L0":
                L0_name = name
            else:
                L0_name = None
            L1_name = None
            L2_name = None
            L3_name = None
            L4_name = None
            L5_name = None
            Lx_lat = None
            Lx_lon = None

        if path == _path and L0 == L0_name and \
                             L1 == L1_name and L2 == L2_name and \
                             L3 == L3_name and L4 == L4_name and \
                             L5 == L5_name:
            if inherited and lat == Lx_lat and lon == Lx_lon:
                # No action required
                return path
            elif inherited or lat is None or lon is None:
                vars = dict(inherited=True,
                            lat=Lx_lat,
                            lon=Lx_lon,
                            )
                db(table.id == id).update(**vars)
                # Also do the Bounds/Centroid/WKT
                vars.update(id=id,
                            gis_feature_type="1",
                            )
                feature.update(**vars)
                bounds_centroid_wkt(feature)
        elif inherited and lat == Lx_lat and lon == Lx_lon:
            db(table.id == id).update(path=_path,
                                      L0=L0_name,
                                      L1=L1_name,
                                      L2=L2_name,
                                      L3=L3_name,
                                      L4=L4_name,
                                      L5=L5_name,
                                      )
        elif inherited or lat is None or lon is None:
            vars = dict(path=_path,
                        L0=L0_name,
                        L1=L1_name,
                        L2=L2_name,
                        L3=L3_name,
                        L4=L4_name,
                        L5=L5_name,
                        inherited=True,
                        lat=Lx_lat,
                        lon=Lx_lon
                        )
            db(table.id == id).update(**vars)
            # Also do the Bounds/Centroid/WKT
            vars.update(id=id,
                        gis_feature_type="1",
                        )
            feature.update(**vars)
            bounds_centroid_wkt(feature)
        else:
            db(table.id == id).update(path=_path,
                                      inherited=False,
                                      L0=L0_name,
                                      L1=L1_name,
                                      L2=L2_name,
                                      L3=L3_name,
                                      L4=L4_name,
                                      L5=L5_name)
        return _path

    # -------------------------------------------------------------------------
    @staticmethod
    def wkt_centroid(form):
        """
            OnValidation callback:
            If a WKT is defined: validate the format,
                calculate the LonLat of the Centroid, and set bounds
            Else if a LonLat is defined: calculate the WKT for the Point.

            Uses Shapely.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        messages = current.messages
        vars = form.vars

        if vars.get("gis_feature_type", None) == "1":
            # Point
            if (vars.lon is None and vars.lat is None) or \
               (vars.lon == "" and vars.lat == ""):
                # No Geometry available
                # Don't clobber existing records (e.g. in Prepop)
                #vars.gis_feature_type = "0"
                # Cannot create WKT, so Skip
                return
            elif vars.lat is None or vars.lat == "":
                # Can't just have lon without lat
                form.errors["lat"] = messages.lat_empty
            elif vars.lon is None or vars.lon == "":
                form.errors["lon"] = messages.lon_empty
            else:
                vars.wkt = "POINT(%(lon)s %(lat)s)" % vars
                if "lon_min" not in vars or vars.lon_min is None:
                    vars.lon_min = vars.lon
                if "lon_max" not in vars or vars.lon_max is None:
                    vars.lon_max = vars.lon
                if "lat_min" not in vars or vars.lat_min is None:
                    vars.lat_min = vars.lat
                if "lat_max" not in vars or vars.lat_max is None:
                    vars.lat_max = vars.lat

        elif vars.get("wkt", None):
            # Parse WKT for LineString, Polygon, etc
            from shapely.wkt import loads as wkt_loads
            try:
                shape = wkt_loads(vars.wkt)
            except:
                try:
                    # Perhaps this is really a LINESTRING (e.g. OSM import of an unclosed Way)
                    linestring = "LINESTRING%s" % vars.wkt[8:-1]
                    shape = wkt_loads(linestring)
                    vars.wkt = linestring
                except:
                    form.errors["wkt"] = messages.invalid_wkt
                return
            gis_feature_type = shape.type
            if gis_feature_type == "Point":
                vars.gis_feature_type = 1
            elif gis_feature_type == "LineString":
                vars.gis_feature_type = 2
            elif gis_feature_type == "Polygon":
                vars.gis_feature_type = 3
            elif gis_feature_type == "MultiPoint":
                vars.gis_feature_type = 4
            elif gis_feature_type == "MultiLineString":
                vars.gis_feature_type = 5
            elif gis_feature_type == "MultiPolygon":
                vars.gis_feature_type = 6
            elif gis_feature_type == "GeometryCollection":
                vars.gis_feature_type = 7
            try:
                centroid_point = shape.centroid
                vars.lon = centroid_point.x
                vars.lat = centroid_point.y
                bounds = shape.bounds
                if gis_feature_type != "Point" or \
                   "lon_min" not in vars or vars.lon_min is None or \
                   vars.lon_min == vars.lon_max:
                    # Update bounds unless we have a 'Point' which has already got wider Bounds specified (such as a country)
                    vars.lon_min = bounds[0]
                    vars.lat_min = bounds[1]
                    vars.lon_max = bounds[2]
                    vars.lat_max = bounds[3]
            except:
                form.errors.gis_feature_type = messages.centroid_error

        elif (vars.lon is None and vars.lat is None) or \
             (vars.lon == "" and vars.lat == ""):
            # No Geometry available
            # Don't clobber existing records (e.g. in Prepop)
            #vars.gis_feature_type = "0"
            # Cannot create WKT, so Skip
            return
        else:
            # Point
            vars.gis_feature_type = "1"
            if vars.lat is None or vars.lat == "":
                form.errors["lat"] = messages.lat_empty
            elif vars.lon is None or vars.lon == "":
                form.errors["lon"] = messages.lon_empty
            else:
                vars.wkt = "POINT(%(lon)s %(lat)s)" % vars
                if "lon_min" not in vars or vars.lon_min is None:
                    vars.lon_min = vars.lon
                if "lon_max" not in vars or vars.lon_max is None:
                    vars.lon_max = vars.lon
                if "lat_min" not in vars or vars.lat_min is None:
                    vars.lat_min = vars.lat
                if "lat_max" not in vars or vars.lat_max is None:
                    vars.lat_max = vars.lat

        if current.deployment_settings.get_gis_spatialdb():
            # Also populate the spatial field
            vars.the_geom = vars.wkt

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def query_features_by_bbox(lon_min, lat_min, lon_max, lat_max):
        """
            Returns a query of all Locations inside the given bounding box
        """

        table = current.s3db.gis_location
        query = (table.lat_min <= lat_max) & \
                (table.lat_max >= lat_min) & \
                (table.lon_min <= lon_max) & \
                (table.lon_max >= lon_min)
        return query

    # -------------------------------------------------------------------------
    @staticmethod
    def get_features_by_bbox(lon_min, lat_min, lon_max, lat_max):
        """
            Returns Rows of Locations whose shape intersects the given bbox.
        """

        query = current.gis.query_features_by_bbox(lon_min,
                                                   lat_min,
                                                   lon_max,
                                                   lat_max)
        return current.db(query).select()

    # -------------------------------------------------------------------------
    @staticmethod
    def get_features_by_shape(shape):
        """
            Returns Rows of locations which intersect the given shape.

            Relies on Shapely for wkt parsing and intersection.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        from shapely.geos import ReadingError
        from shapely.wkt import loads as wkt_loads

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        table = current.s3db.gis_location
        in_bbox = current.gis.query_features_by_bbox(*shape.bounds)
        has_wkt = (table.wkt != None) & (table.wkt != "")

        for loc in current.db(in_bbox & has_wkt).select():
            try:
                location_shape = wkt_loads(loc.wkt)
                if location_shape.intersects(shape):
                    yield loc
            except ReadingError:
                s3_debug("Error reading wkt of location with id", loc.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def get_features_by_latlon(lat, lon):
        """
            Returns a generator of locations whose shape intersects the given LatLon.

            Relies on Shapely.
            @todo: provide an option to use PostGIS/Spatialite
        """

        from shapely.geometry import point

        return current.gis.get_features_by_shape(point.Point(lon, lat))

    # -------------------------------------------------------------------------
    @staticmethod
    def get_features_by_feature(feature):
        """
            Returns all Locations whose geometry intersects the given feature.

            Relies on Shapely.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        from shapely.wkt import loads as wkt_loads

        shape = wkt_loads(feature.wkt)
        return current.gis.get_features_by_shape(shape)

    # -------------------------------------------------------------------------
    @staticmethod
    def set_all_bounds():
        """
            Sets bounds for all locations without them.

            If shapely is present, and a location has wkt, bounds of the geometry
            are used.  Otherwise, the (lat, lon) are used as bounds.
        """

        try:
            from shapely.wkt import loads as wkt_loads
            SHAPELY = True
        except:
            SHAPELY = False

        db = current.db
        table = current.s3db.gis_location

        # Query to find all locations without bounds set
        no_bounds = (table.lon_min == None) & \
                    (table.lat_min == None) & \
                    (table.lon_max == None) & \
                    (table.lat_max == None) & \
                    (table.lat != None) & \
                    (table.lon != None)
        if SHAPELY:
            # Refine to those locations with a WKT field
            wkt_no_bounds = no_bounds & (table.wkt != None) & (table.wkt != "")
            for location in db(wkt_no_bounds).select(table.wkt):
                try :
                    shape = wkt_loads(location.wkt)
                except:
                    s3_debug("Error reading WKT", location.wkt)
                    continue
                bounds = shape.bounds
                table[location.id] = dict(lon_min = bounds[0],
                                          lat_min = bounds[1],
                                          lon_max = bounds[2],
                                          lat_max = bounds[3],
                                          )

        # Anything left, we assume is a Point, so set the bounds to be the same
        db(no_bounds).update(lon_min=table.lon,
                             lat_min=table.lat,
                             lon_max=table.lon,
                             lat_max=table.lat)

    # -------------------------------------------------------------------------
    @staticmethod
    def simplify(wkt,
                 tolerance=None,
                 preserve_topology=True,
                 output="wkt",
                 decimals=4
                 ):
        """
            Simplify a complex Polygon using the Douglas-Peucker algorithm
            - NB This uses Python, better performance will be gained by doing
                 this direct from the database if you are using PostGIS:
            ST_Simplify() is available as
            db(query).select(table.the_geom.st_simplify(tolerance).st_astext().with_alias('wkt')).first().wkt
            db(query).select(table.the_geom.st_simplify(tolerance).st_asgeojson().with_alias('geojson')).first().geojson

            @param wkt: the WKT string to be simplified (usually coming from a gis_location record)
            @param tolerance: how aggressive a simplification to perform
            @param preserve_topology: whether the simplified geometry should be maintained
            @param output: whether to output as WKT or GeoJSON format
            @param decimals: the number of decimal places to include in the output
        """

        from shapely.geometry import Point, LineString, Polygon, MultiPolygon
        from shapely.wkt import loads as wkt_loads

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        try:
            shape = wkt_loads(wkt)
        except:
            wkt = wkt[10] if wkt else wkt
            s3_debug("Invalid Shape: %s" % wkt)
            return None

        if not tolerance:
            tolerance = current.deployment_settings.get_gis_simplify_tolerance()

        if tolerance:
            shape = shape.simplify(tolerance, preserve_topology)

        # Limit the number of decimal places
        formatter = ".%sf" % decimals
        def shrink_polygon(shape):
            """ Helper Function """
            points = shape.exterior.coords
            coords = []
            cappend = coords.append
            for point in points:
                x = float(format(point[0], formatter))
                y = float(format(point[1], formatter))
                cappend((x, y))
            return Polygon(LineString(coords))

        geom_type = shape.geom_type
        if geom_type == "MultiPolygon":
            polygons = shape.geoms
            p = []
            pappend = p.append
            for polygon in polygons:
                pappend(shrink_polygon(polygon))
            shape = MultiPolygon([s for s in p])
        elif geom_type == "Polygon":
            shape = shrink_polygon(shape)
        elif geom_type == "LineString":
            points = shape.coords
            coords = []
            cappend = coords.append
            for point in points:
                x = float(format(point[0], formatter))
                y = float(format(point[1], formatter))
                cappend((x, y))
            shape = LineString(coords)
        elif geom_type == "Point":
            x = float(format(shape.x, formatter))
            y = float(format(shape.y, formatter))
            shape = Point(x, y)
        else:
            s3_debug("Cannot yet shrink Geometry: %s" % geom_type)

        # Output
        if output == "wkt":
            output = shape.to_wkt()
        elif output == "geojson":
            from ..geojson import dumps
            # Compact Encoding
            output = dumps(shape, separators=SEPARATORS)

        return output

    # -------------------------------------------------------------------------
    def show_map(self,
                 id = "default_map",
                 height = None,
                 width = None,
                 bbox = {},
                 lat = None,
                 lon = None,
                 zoom = None,
                 projection = None,
                 add_feature = False,
                 add_feature_active = False,
                 add_polygon = False,
                 add_polygon_active = False,
                 features = None,
                 feature_queries = None,
                 feature_resources = None,
                 wms_browser = {},
                 catalogue_layers = False,
                 legend = False,
                 toolbar = False,
                 nav = None,
                 area = False,
                 save = False,
                 search = False,
                 mouse_position = None,
                 overview = None,
                 permalink = None,
                 scaleline = None,
                 zoomcontrol = None,
                 print_tool = {},
                 mgrs = {},
                 window = False,
                 window_hide = False,
                 closable = True,
                 maximizable = True,
                 collapsed = False,
                 callback = "DEFAULT",
                 plugins = None,
                 ):
        """
            Returns the HTML to display a map

            Normally called in the controller as: map = gis.show_map()
            In the view, put: {{=XML(map)}}

            @param id: ID to uniquely identify this map if there are several on a page
            @param height: Height of viewport (if not provided then the default deployment setting is used)
            @param width: Width of viewport (if not provided then the default deployment setting is used)
            @param bbox: default Bounding Box of viewport (if not provided then the Lat/Lon/Zoom are used) (Dict):
                {"lon_min" : float,
                 "lat_min" : float,
                 "lon_max" : float,
                 "lat_max" : float,
                 }
            @param lat: default Latitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param lon: default Longitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param zoom: default Zoom level of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param projection: EPSG code for the Projection to use (if not provided then the default setting from the Map Service Catalogue is used)
            @param add_feature: Whether to include a DrawFeature control to allow adding a marker to the map
            @param add_feature_active: Whether the DrawFeature control should be active by default
            @param add_polygon: Whether to include a DrawFeature control to allow drawing a polygon over the map
            @param add_polygon_active: Whether the DrawFeature control should be active by default
            @param features: Simple Features to overlay on Map (no control over appearance & not interactive)
                [wkt]
            @param feature_queries: Feature Queries to overlay onto the map & their options (List of Dicts):
                [{"name"   : T("MyLabel"), # A string: the label for the layer
                  "query"  : query,        # A gluon.sql.Rows of gis_locations, which can be from a simple query or a Join.
                                           # Extra fields can be added for 'popup_url', 'popup_label' & either
                                           # 'marker' (url/height/width) or 'shape' (with optional 'colour' & 'size')
                  "active" : True,         # Is the feed displayed upon load or needs ticking to load afterwards?
                  "marker" : None,         # Optional: A per-Layer marker query or marker_id for the icon used to display the feature
                  "opacity" : 1,           # Optional
                  "cluster_attribute",     # Optional
                  "cluster_distance",      # Optional
                  "cluster_threshold"      # Optional
                }]
            @param feature_resources: REST URLs for (filtered) resources to overlay onto the map & their options (List of Dicts):
                [{"name"      : T("MyLabel"), # A string: the label for the layer
                  "id"        : "search",     # A string: the id for the layer (for manipulation by JavaScript)
                  "active"    : True,         # Is the feed displayed upon load or needs ticking to load afterwards?
                  EITHER:
                  "layer_id"  : 1,            # An integer: the layer_id to load (optional alternative to specifying URL/tablename/marker)
                  "filter"    : "filter",     # A string: an optional URL filter which *replaces* any in the layer
                  OR:
                  "tablename" : "module_resource", # A string: the tablename (used to determine whether to locate via location_id or site_id)
                  "url"       : "/eden/module/resource.geojson?filter", # A URL to load the resource

                  "marker"    : None,         # Optional: A per-Layer marker dict for the icon used to display the feature (overrides layer_id if-set)
                  "opacity"   : 1,            # Optional (overrides layer_id if-set)
                  "cluster_attribute",        # Optional (overrides layer_id if-set)
                  "cluster_distance",         # Optional (overrides layer_id if-set)
                  "cluster_threshold",        # Optional (overrides layer_id if-set)
                  "dir",                      # Optional (overrides layer_id if-set)
                  "style",                    # Optional (overrides layer_id if-set)
                }]
            @param wms_browser: WMS Server's GetCapabilities & options (dict)
                {"name": T("MyLabel"),     # Name for the Folder in LayerTree
                 "url": string             # URL of GetCapabilities
                }
            @param catalogue_layers: Show all the enabled Layers from the GIS Catalogue
                                     Defaults to False: Just show the default Base layer
            @param legend: True: Show the GeoExt Legend panel, False: No Panel, "floating": New floating Legend Panel
            @param toolbar: Show the Icon Toolbar of Controls
            @param nav: Show the Navigation controls on the Toolbar
            @param area: Show the Area tool on the Toolbar
            @param save: Show the Save tool on the Toolbar
            @param search: Show the Geonames search box
            @param mouse_position: Show the current coordinates in the bottom-right of the map. 3 Options: 'normal', 'mgrs', False (defaults to checking deployment_settings, which defaults to 'normal')
            @param overview: Show the Overview Map (defaults to checking deployment_settings, which defaults to True)
            @param permalink: Show the Permalink control (defaults to checking deployment_settings, which defaults to True)
            @param scaleline: Show the ScaleLine control (defaults to checking deployment_settings, which defaults to True)
            @param zoomcontrol: Show the Zoom control (defaults to checking deployment_settings, which defaults to True)
            @param print_tool: Show a print utility (NB This requires server-side support: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting)
                {"url": string,            # URL of print service (e.g. http://localhost:8080/geoserver/pdf/)
                 "mapTitle": string,       # Title for the Printed Map (optional)
                 "subTitle": string        # subTitle for the Printed Map (optional)
                }
            @param mgrs: Use the MGRS Control to select PDFs
                {"name": string,           # Name for the Control
                 "url": string             # URL of PDF server
                }
                @ToDo: Also add MGRS Search support: http://gxp.opengeo.org/master/examples/mgrs.html
            @param window: Have viewport pop out of page into a resizable window
            @param window_hide: Have the window hidden by default, ready to appear (e.g. on clicking a button)
            @param closable: In Window mode, whether the window is closable or not
            @param collapsed: Start the Tools panel (West region) collapsed
            @param callback: Code to run once the Map JavaScript has loaded
            @param plugins: an iterable of objects which support the following methods:
                                .extend_gis_map(map)
                            Client-side portion suppoprts the following methods:
                                .addToMapWindow(items)
                                .setup(map)

        """

        return MAP(id = id,
                   height = height,
                   width = width,
                   bbox = bbox,
                   lat = lat,
                   lon = lon,
                   zoom = zoom,
                   projection = projection,
                   add_feature = add_feature,
                   add_feature_active = add_feature_active,
                   add_polygon = add_polygon,
                   add_polygon_active = add_polygon_active,
                   features = features,
                   feature_queries = feature_queries,
                   feature_resources = feature_resources,
                   wms_browser = wms_browser,
                   catalogue_layers = catalogue_layers,
                   legend = legend,
                   toolbar = toolbar,
                   nav = nav,
                   area = area,
                   save = save,
                   search = search,
                   mouse_position = mouse_position,
                   overview = overview,
                   permalink = permalink,
                   scaleline = scaleline,
                   zoomcontrol = zoomcontrol,
                   print_tool = print_tool,
                   mgrs = mgrs,
                   window = window,
                   window_hide = window_hide,
                   closable = closable,
                   maximizable = maximizable,
                   collapsed = collapsed,
                   callback = callback,
                   plugins = plugins,
                   )

# =============================================================================
class MAP(DIV):
    """
        HTML Helper to render a Map
        - allows the Map to be generated only when being rendered
        - used by gis.show_map()
    """

    def __init__(self, **opts):
        """
            :param **opts: options to pass to the Map for server-side processing
        """

        # We haven't yet run _setup()
        self.setup = False
        self.callback = None

        # Options for server-side processing
        self.opts = opts
        self.id = opts.get("id", "default_map")

        # Options for client-side processing
        self.options = {}

        # Components
        components = []

        # Map (Embedded not Window)
        # Needs to be an ID which means we can't have multiple per page :/
        # - Alternatives are also fragile. See s3.gis.js
        components.append(DIV(DIV(_class="map_loader"),
                              _id="map_panel"))

        self.components = components
        for c in components:
            self._setnode(c)

        # Other DIV settings
        self.attributes = {"_class": "map_wrapper",
                           "_id": self.id,
                           }
        self.parent = None

    # -------------------------------------------------------------------------
    def _setup(self):
        """
            Setup the Map
            - not done during init() to hve as Lazy as possible
            - separated from xml() in order to be able to read options to put
              into scripts (callback or otherwise)
        """

        opts = self.opts

        request = current.request
        response = current.response
        if not response.warning:
            response.warning = ""
        s3 = response.s3
        T = current.T
        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings
        MAP_ADMIN = auth.s3_has_role(current.session.s3.system_roles.MAP_ADMIN)
        # Default configuration
        config = GIS.get_config()

        # Support bookmarks (such as from the control)
        # - these over-ride the arguments
        vars = request.get_vars

        # JS Globals
        globals = {}

        # Map Options for client-side processing
        options = {}

        # Strings used by all Maps
        i18n = {"gis_base_layers": T("Base Layers"),
                "gis_overlays": T(settings.get_gis_label_overlays()),
                "gis_layers": T("Layers"),
                "gis_draft_layer": T("Draft Features"),
                "gis_cluster_multiple": T("There are multiple records at this location"),
                "gis_loading": T("Loading"),
                "gis_requires_login": T("Requires Login"),
                "gis_zoomin": T("Zoom In"),
                }

        ############
        # Viewport
        ############

        height = opts.get("height", None)
        if height:
            map_height = height
        else:
            map_height = settings.get_gis_map_height()
        options["map_height"] = map_height
        width = opts.get("width", None)
        if width:
            map_width = width
        else:
            map_width = settings.get_gis_map_width()
        options["map_width"] = map_width

        # Bounding Box or Center/Zoom
        bbox = opts.get("bbox", None)
        if (bbox
            and (-90 <= bbox["lat_max"] <= 90)
            and (-90 <= bbox["lat_min"] <= 90)
            and (-180 <= bbox["lon_max"] <= 180)
            and (-180 <= bbox["lon_min"] <= 180)
            ):
            # We have sane Bounds provided, so we should use them
            pass
        else:
            # No bounds or we've been passed bounds which aren't sane
            bbox = None
            # Use Lat/Lon/Zoom to center instead
            if "lat" in vars and vars.lat:
                lat = float(vars.lat)
            else:
                lat = opts.get("lat", None)
            if lat is None or lat == "":
                lat = config.lat
            if "lon" in vars and vars.lon:
                lon = float(vars.lon)
            else:
                lon = opts.get("lon", None)
            if lon is None or lon == "":
                lon = config.lon

        if bbox:
            # Calculate from Bounds
            options["bbox"] = [bbox["lon_min"], # left
                               bbox["lat_min"], # bottom
                               bbox["lon_max"], # right
                               bbox["lat_max"], # top
                               ]
        else:
            options["lat"] = lat
            options["lon"] = lon

        if "zoom" in vars:
            zoom = int(vars.zoom)
        else:
            zoom = opts.get("zoom", None)
        if not zoom:
            zoom = config.zoom
        options["zoom"] = zoom or 1

        options["numZoomLevels"] = config.zoom_levels

        ############
        # Projection
        ############

        projection = opts.get("projection", None)
        if not projection:
            projection = config.epsg
        options["projection"] = projection
        if projection not in (900913, 4326):
            # Test for Valid Projection file in Proj4JS library
            projpath = os.path.join(
                request.folder, "static", "scripts", "gis", "proj4js", \
                "lib", "defs", "EPSG%s.js" % projection
            )
            try:
                f = open(projpath, "r")
                f.close()
            except:
                if projection:
                    proj4js = config.proj4js
                    if proj4js:
                        # Create it
                        try:
                            f = open(projpath, "w")
                        except IOError, e:
                            response.error =  \
                        T("Map not available: Cannot write projection file - %s") % e
                        else:
                            f.write('''Proj4js.defs["EPSG:4326"]="%s"''' % proj4js)
                            f.close()
                    else:
                        response.warning =  \
    T("Map not available: Projection %(projection)s not supported - please add definition to %(path)s") % \
        dict(projection = "'%s'" % projection,
             path= "/static/scripts/gis/proj4js/lib/defs")
                else:
                    response.error =  \
                        T("Map not available: No Projection configured")
                return None
            options["maxExtent"] = config.maxExtent
            options["units"] = config.units

        ########
        # Marker
        ########

        if config.marker_image:
            options["marker_default"] = dict(i = config.marker_image,
                                             h = config.marker_height,
                                             w = config.marker_width,
                                             )
        # @ToDo: show_map() opts with fallback to settings 
        # Keep these in sync with scaleImage() in s3.gis.js
        marker_max_height = settings.get_gis_marker_max_height() 
        if marker_max_height != 35:
            options["max_h"] = marker_max_height
        marker_max_width = settings.get_gis_marker_max_width() 
        if marker_max_width != 30:
            options["max_w"] = marker_max_width

        ########
        # Layout
        ########

        if not opts.get("closable", False):
            options["windowNotClosable"] = True
        if opts.get("window", False):
            options["window"] = True
            if opts.get("window_hide", False):
                options["windowHide"] = True

        if opts.get("maximizable", False):
            options["maximizable"] = True
        else:
            options["maximizable"] = False

        # Collapsed
        if opts.get("collapsed", False):
            options["west_collapsed"] = True

        # LayerTree
        if not settings.get_gis_layer_tree_base():
            options["hide_base"] = True
        if not settings.get_gis_layer_tree_overlays():
            options["hide_overlays"] = True
        if not settings.get_gis_layer_tree_expanded():
            options["folders_closed"] = True
        if settings.get_gis_layer_tree_radio():
            options["folders_radio"] = True

        #######
        # Tools
        #######

        # Toolbar
        if opts.get("toolbar", False):
            options["toolbar"] = True

            i18n["gis_length_message"] = T("The length is")
            i18n["gis_length_tooltip"] = T("Measure Length: Click the points along the path & end with a double-click")
            i18n["gis_zoomfull"] = T("Zoom to maximum map extent")
            i18n["gis_zoominbutton"] = T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle")
            i18n["gis_zoomout"] = T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle")
            i18n["gis_geoLocate"] = T("Zoom to Current Location")

            # Search
            if opts.get("search", False):
                # Presence of label adds support JS in Loader and turns feature on in s3.gis.js
                # @ToDo: Provide explicit option to support multiple maps in a page with different options
                i18n["gis_search"] = T("Search location in Geonames")
                #i18n["gis_search_no_internet"] = T("Geonames.org search requires Internet connectivity!")

            # Show NAV controls?
            # e.g. removed within S3LocationSelectorWidget[2]
            nav = opts.get("nav", None)
            if nav is None:
                nav = settings.get_gis_nav_controls()
            if nav:
                i18n["gis_pan"] = T("Pan Map: keep the left mouse button pressed and drag the map")
                i18n["gis_navPrevious"] = T("Previous View")
                i18n["gis_navNext"] = T("Next View")
            else:
                options["nav"] = False

            # Show Area control?
            if opts.get("area", False):
                options["area"] = True
                i18n["gis_area_message"] = T("The area is")
                i18n["gis_area_tooltip"] = T("Measure Area: Click the points around the polygon & end with a double-click")

            # Show Save control?
            # e.g. removed within S3LocationSelectorWidget[2]
            if opts.get("save", True) and auth.is_logged_in():
                options["save"] = True
                i18n["gis_save"] = T("Save: Default Lat, Lon & Zoom for the Viewport")
                if MAP_ADMIN or (config.pe_id == auth.user.pe_id):
                    # Personal config or MapAdmin, so Save Button does Updates
                    options["config_id"] = config.id

            # OSM Authoring
            pe_id = auth.user.pe_id if auth.s3_logged_in() else None
            if pe_id and s3db.auth_user_options_get_osm(pe_id):
                # Presence of label turns feature on in s3.gis.js
                # @ToDo: Provide explicit option to support multiple maps in a page with different options
                i18n["gis_potlatch"] = T("Edit the OpenStreetMap data for this area")
                i18n["gis_osm_zoom_closer"] = T("Zoom in closer to Edit OpenStreetMap layer")

            # MGRS PDF Browser
            mgrs = opts.get("mgrs", None)
            if mgrs:
                options["mgrs_name"] = mgrs["name"]
                options["mgrs_url"] = mgrs["url"]
        else:
            # No Toolbar
            # Show Save control?
            # e.g. removed within S3LocationSelectorWidget[2]
            if opts.get("save", True) and auth.is_logged_in():
                db = current.db
                permit = auth.s3_has_permission
                ctable = db.gis_config
                if permit("create", ctable):
                    options["save"] = True
                    i18n["gis_save_map"] = T("Save Map")
                    i18n["gis_new_map"] = T("Save as New Map?")
                    i18n["gis_name_map"] = T("Name of Map")
                    i18n["save"] = T("Save")
                    i18n["saved"] = T("Saved")
                    config_id = config.id
                    _config = db(ctable.id == config_id).select(ctable.uuid,
                                                                ctable.name,
                                                                limitby=(0, 1),
                                                                ).first()
                    if MAP_ADMIN:
                        i18n["gis_my_maps"] = T("Saved Maps")
                    else:
                        options["pe_id"] = auth.user.pe_id
                        i18n["gis_my_maps"] = T("My Maps")
                    if permit("update", ctable, record_id=config_id):
                        options["config_id"] = config_id
                        options["config_name"] = _config.name
                    elif _config.uuid != "SITE_DEFAULT":
                        options["config_name"] = _config.name

        # Legend panel
        legend = opts.get("legend", False)
        if legend:
            i18n["gis_legend"] = T("Legend")
            if legend == "float":
                options["legend"] = "float"
                if settings.get_gis_layer_metadata():
                    options["metadata"] = True
                    # MAP_ADMIN better for simpler deployments
                    #if auth.s3_has_permission("create", "cms_post_layer"):
                    if MAP_ADMIN:
                        i18n["gis_metadata_create"] = T("Create 'More Info'")
                        i18n["gis_metadata_edit"] = T("Edit 'More Info'")
                    else:
                        i18n["gis_metadata"] = T("More Info")
            else:
                options["legend"] = True

        # Draw Feature Controls
        if opts.get("add_feature", False):
            i18n["gis_draw_feature"] = T("Add Point")
            if opts.get("add_feature_active", False):
                options["draw_feature"] = "active"
            else:
                options["draw_feature"] = "inactive"

        if opts.get("add_polygon", False):
            i18n["gis_draw_polygon"] = T("Add Polygon")
            if opts.get("add_polygon_active", False):
                options["draw_polygon"] = "active"
            else:
                options["draw_polygon"] = "inactive"

        # Layer Properties
        if settings.get_gis_layer_properties():
            # Presence of label turns feature on in s3.gis.js
            i18n["gis_properties"] = T("Layer Properties")

        # Upload Layer
        if settings.get_gis_geoserver_password():
            # Presence of label adds support JS in Loader and turns feature on in s3.gis.js
            # @ToDo: Provide explicit option to support multiple maps in a page with different options
            i18n["gis_uploadlayer"] = T("Upload Shapefile")

        # WMS Browser
        wms_browser = opts.get("wms_browser", None)
        if wms_browser:
            options["wms_browser_name"] = wms_browser["name"]
            # urlencode the URL
            options["wms_browser_url"] = urllib.quote(wms_browser["url"])

        # Mouse Position
        # 'normal', 'mgrs' or 'off'
        mouse_position = opts.get("mouse_position", None)
        if mouse_position is None:
            mouse_position = settings.get_gis_mouse_position()
        if mouse_position == "mgrs":
            options["mouse_position"] = "mgrs"
            # Tell loader to load support scripts
            globals["mgrs"] = True
        elif mouse_position:
            options["mouse_position"] = True

        # Overview Map
        overview = opts.get("overview", None)
        if overview is None:
            overview = settings.get_gis_overview()
        if not overview:
            options["overview"] = False

        # Permalink
        permalink = opts.get("permalink", None)
        if permalink is None:
            permalink = settings.get_gis_permalink()
        if not permalink:
            options["permalink"] = False

        # ScaleLine
        scaleline = opts.get("scaleline", None)
        if scaleline is None:
            scaleline = settings.get_gis_scaleline()
        if not scaleline:
            options["scaleline"] = False

        # Zoom control
        zoomcontrol = opts.get("zoomcontrol", None)
        if zoomcontrol is None:
            zoomcontrol = settings.get_gis_zoomcontrol()
        if not zoomcontrol:
            options["zoomcontrol"] = False

        ########
        # Layers
        ########

        # Duplicate Features to go across the dateline?
        # @ToDo: Action this again (e.g. for DRRPP)
        if settings.get_gis_duplicate_features():
            options["duplicate_features"] = True

        # Features
        features = opts.get("features", None)
        if features:
            options["features"] = addFeatures(features)

        # Feature Queries
        feature_queries = opts.get("feature_queries", None)
        if feature_queries:
            options["feature_queries"] = addFeatureQueries(feature_queries)

        # Feature Resources
        feature_resources = opts.get("feature_resources", None)
        if feature_resources:
            options["feature_resources"] = addFeatureResources(feature_resources)

        if opts.get("catalogue_layers", False):
            # Add all Layers from the Catalogue
            layer_types = [LayerArcREST,
                           LayerBing,
                           LayerEmpty,
                           LayerGoogle,
                           LayerOSM,
                           LayerTMS,
                           LayerWMS,
                           LayerXYZ,
                           LayerJS,
                           LayerTheme,
                           LayerGeoJSON,
                           LayerGPX,
                           LayerCoordinate,
                           LayerGeoRSS,
                           LayerKML,
                           LayerOpenWeatherMap,
                           LayerShapefile,
                           LayerWFS,
                           LayerFeature,
                           ]
        else:
            # Add just the default Base Layer
            s3.gis.base = True
            layer_types = []
            db = current.db
            ltable = s3db.gis_layer_config
            etable = s3db.gis_layer_entity
            query = (etable.id == ltable.layer_id) & \
                    (ltable.config_id == config["id"]) & \
                    (ltable.base == True) & \
                    (ltable.enabled == True)
            layer = db(query).select(etable.instance_type,
                                     limitby=(0, 1)).first()
            if not layer:
                # Use Site Default
                ctable = db.gis_config
                query = (etable.id == ltable.layer_id) & \
                        (ltable.config_id == ctable.id) & \
                        (ctable.uuid == "SITE_DEFAULT") & \
                        (ltable.base == True) & \
                        (ltable.enabled == True)
                layer = db(query).select(etable.instance_type,
                                         limitby=(0, 1)).first()
            if layer:
                layer_type = layer.instance_type
                if layer_type == "gis_layer_openstreetmap":
                    layer_types = [LayerOSM]
                elif layer_type == "gis_layer_google":
                    # NB v3 doesn't work when initially hidden
                    layer_types = [LayerGoogle]
                elif layer_type == "gis_layer_arcrest":
                    layer_types = [LayerArcREST]
                elif layer_type == "gis_layer_bing":
                    layer_types = [LayerBing]
                elif layer_type == "gis_layer_tms":
                    layer_types = [LayerTMS]
                elif layer_type == "gis_layer_wms":
                    layer_types = [LayerWMS]
                elif layer_type == "gis_layer_xyz":
                    layer_types = [LayerXYZ]
                elif layer_type == "gis_layer_empty":
                    layer_types = [LayerEmpty]

            if not layer_types:
                layer_types = [LayerEmpty]

        scripts = []
        scripts_append = scripts.append
        for LayerType in layer_types:
            try:
                # Instantiate the Class
                layer = LayerType()
                layer.as_dict(options)
                for script in layer.scripts:
                    scripts_append(script)
            except Exception, exception:
                error = "%s not shown: %s" % (LayerType.__name__, exception)
                if s3.debug:
                    raise HTTP(500, error)
                else:
                    response.warning += error

        # WMS getFeatureInfo
        # (loads conditionally based on whether queryable WMS Layers have been added)
        if s3.gis.get_feature_info:
            # Presence of label turns feature on
            # @ToDo: Provide explicit option to support multiple maps in a page with different options
            i18n["gis_get_feature_info"] = T("Get Feature Info")
            i18n["gis_feature_info"] = T("Feature Info")

        # Callback can be set before _setup()
        if not self.callback:
            self.callback = opts.get("callback", "DEFAULT")
        # These can be read/modified after _setup() & before xml()
        self.options = options

        self.globals = globals
        self.i18n = i18n
        self.scripts = scripts

        # Set up map plugins
        # - currently just used by Climate
        # @ToDo: Get these working with new loader
        # This, and any code it generates, is done last
        # However, map plugin should not assume this.
        self.plugin_callbacks = []
        plugins = opts.get("plugins", None)
        if plugins:
            for plugin in plugins:
                plugin.extend_gis_map(self)

        # Flag to xml() that we've already been run
        self.setup = True

        return options

    # -------------------------------------------------------------------------
    def xml(self):
        """
            Render the Map
            - this is primarily done by inserting a lot of JavaScript
            - CSS loaded as-standard to avoid delays in page loading
            - HTML added in init() as a component
        """

        if not self.setup:
            self._setup()

        # Add ExtJS
        # @ToDo: Do this conditionally on whether Ext UI is used
        s3_include_ext()

        s3 = current.response.s3

        js_global_append = s3.js_global.append

        i18n_dict = self.i18n
        i18n = []
        i18n_append = i18n.append
        for key, val in i18n_dict.items():
            # @ToDo: Check if already inserted (optimise multiple maps)
            i18n_append('''i18n.%s="%s"''' % (key, val))
        i18n = '''\n'''.join(i18n)
        js_global_append(i18n)

        globals_dict = self.globals
        globals = []
        globals_append = globals.append
        dumps = json.dumps
        for key, val in globals_dict.items():
            # @ToDo: Check if already inserted (optimise multiple maps)
            globals_append('''S3.gis.%s=%s''' % (key, dumps(val, separators=SEPARATORS)))
        globals = '''\n'''.join(globals)
        js_global_append(globals)

        scripts = s3.scripts
        script = URL(c="static", f="scripts/S3/s3.gis.loader.js")
        if script not in scripts:
            scripts.append(script)

        callback = self.callback
        map_id = self.id
        options = self.options
        projection = options["projection"]
        options = dumps(options, separators=SEPARATORS)
        plugin_callbacks = '''\n'''.join(self.plugin_callbacks)
        if callback:
            if callback == "DEFAULT":
                if map_id == "default_map":
                    callback = '''S3.gis.show_map(null,%s)''' % options
                else:
                    callback = '''S3.gis.show_map(%s,%s)''' % (map_id, options)
            else:
                # Store options where they can be read by a later show_map()
                js_global_append('''S3.gis.options["%s"]=%s''' % (map_id, options))
            script = URL(c="static", f="scripts/yepnope.1.5.4-min.js")
            if script not in scripts:
                scripts.append(script)
            if plugin_callbacks:
                callback = '''%s\n%s''' % (callback, plugin_callbacks)
            callback = '''function(){%s}''' % callback
        else:
            # Store options where they can be read by a later show_map()
            js_global_append('''S3.gis.options["%s"]=%s''' % (map_id, options))
            if plugin_callbacks:
                callback = '''function(){%s}''' % plugin_callbacks
            else:
                callback = '''null'''
        loader = '''s3_gis_loadjs(%(debug)s,%(projection)s,%(callback)s,%(scripts)s)''' \
            % dict(debug = "true" if s3.debug else "false",
                   projection = projection,
                   callback = callback,
                   scripts = self.scripts
                   )
        s3.jquery_ready.append(loader)

        # Return the HTML
        return super(MAP, self).xml()

# =============================================================================
def addFeatures(features):
    """
        Add Simple Features to the Draft layer
        - used by S3LocationSelectorWidget
    """

    simplify = GIS.simplify
    _f = []
    append = _f.append
    for feature in features:
        geojson = simplify(feature, output="geojson")
        if geojson:
            f = dict(type = "Feature",
                     geometry = json.loads(geojson))
            append(f)
    return _f

# =============================================================================
def addFeatureQueries(feature_queries):
    """
        Add Feature Queries to the map
        -  These can be Rows or Storage()
        NB These considerations need to be taken care of before arriving here:
            Security of data
            Localisation of name/popup_label
    """

    db = current.db
    s3db = current.s3db
    cache = s3db.cache
    request = current.request
    controller = request.controller
    function = request.function
    fqtable = s3db.gis_feature_query
    mtable = s3db.gis_marker

    auth = current.auth
    auth_user = auth.user
    if auth_user:
        created_by = auth_user.id
        s3_make_session_owner = auth.s3_make_session_owner
    else:
        # Anonymous
        # @ToDo: A deployment with many Anonymous Feature Queries being
        #        accessed will need to change this design - e.g. use session ID instead
        created_by = None

    layers_feature_query = []
    append = layers_feature_query.append
    for layer in feature_queries:
        name = str(layer["name"])
        _layer = dict(name=name)
        name_safe = re.sub("\W", "_", name)

        # Lat/Lon via Join or direct?
        try:
            layer["query"][0].gis_location.lat
            join = True
        except:
            join = False

        # Push the Features into a temporary table in order to have them accessible via GeoJSON
        # @ToDo: Maintenance Script to clean out old entries (> 24 hours?)
        cname = "%s_%s_%s" % (name_safe,
                              controller,
                              function)
        # Clear old records
        query = (fqtable.name == cname) & \
                (fqtable.created_by == created_by)
        db(query).delete()
        for row in layer["query"]:
            rowdict = {"name" : cname}
            if join:
                rowdict["lat"] = row.gis_location.lat
                rowdict["lon"] = row.gis_location.lon
            else:
                rowdict["lat"] = row["lat"]
                rowdict["lon"] = row["lon"]
            if "popup_url" in row:
                rowdict["popup_url"] = row["popup_url"]
            if "popup_label" in row:
                rowdict["popup_label"] = row["popup_label"]
            if "marker" in row:
                rowdict["marker_url"] = URL(c="static", f="img",
                                            args=["markers",
                                                  row["marker"].image])
                rowdict["marker_height"] = row["marker"].height
                rowdict["marker_width"] = row["marker"].width
            else:
                if "marker_url" in row:
                    rowdict["marker_url"] = row["marker_url"]
                if "marker_height" in row:
                    rowdict["marker_height"] = row["marker_height"]
                if "marker_width" in row:
                    rowdict["marker_width"] = row["marker_width"]
            if "shape" in row:
                rowdict["shape"] = row["shape"]
            if "size" in row:
                rowdict["size"] = row["size"]
            if "colour" in row:
                rowdict["colour"] = row["colour"]
            if "opacity" in row:
                rowdict["opacity"] = row["opacity"]
            record_id = fqtable.insert(**rowdict)
            if not created_by:
                s3_make_session_owner(fqtable, record_id)

        # URL to retrieve the data
        url = "%s.geojson?feature_query.name=%s&feature_query.created_by=%s" % \
                (URL(c="gis", f="feature_query"),
                 cname,
                 created_by)
        _layer["url"] = url

        if "active" in layer and not layer["active"]:
            _layer["visibility"] = False

        markerLayer = ""
        if "marker" in layer:
            # per-Layer Marker
            marker = layer["marker"]
            if isinstance(marker, int):
                # integer (marker_id) not row
                marker = db(mtable.id == marker).select(mtable.image,
                                                        mtable.height,
                                                        mtable.width,
                                                        limitby=(0, 1),
                                                        cache=cache
                                                        ).first()
            if marker:
                # @ToDo: Single option as dict
                _layer["marker_url"] = marker["image"]
                _layer["marker_height"] = marker["height"]
                _layer["marker_width"] = marker["width"]

        if "opacity" in layer and layer["opacity"] != 1:
            _layer["opacity"] = "%.1f" % layer["opacity"]
        if "cluster_attribute" in layer and \
           layer["cluster_attribute"] != CLUSTER_ATTRIBUTE:
            _layer["cluster_attribute"] = layer["cluster_attribute"]
        if "cluster_distance" in layer and \
           layer["cluster_distance"] != CLUSTER_DISTANCE:
            _layer["cluster_distance"] = layer["cluster_distance"]
        if "cluster_threshold" in layer and \
           layer["cluster_threshold"] != CLUSTER_THRESHOLD:
            _layer["cluster_threshold"] = layer["cluster_threshold"]
        append(_layer)

    return layers_feature_query

# =============================================================================
def addFeatureResources(feature_resources):
    """
        Add Feature Resources to the map
        - REST URLs to back-end resources
    """

    db = current.db
    s3db = current.s3db
    config = GIS.get_config()
    ftable = s3db.gis_layer_feature
    ltable = s3db.gis_layer_config

    layers_feature_resource = []
    append = layers_feature_resource.append
    for layer in feature_resources:
        name = str(layer["name"])
        _layer = dict(name=name)
        id = str(layer["id"])
        id = re.sub("\W", "_", id)
        _layer["id"] = id

        # Are we loading a Catalogue Layer or a simple URL?
        layer_id = layer.get("layer_id", None)
        if layer_id:
            query = (ftable.layer_id == layer_id)
            lquery = (ltable.layer_id == layer_id) & \
                     (ltable.config_id == config.id)
            left = ltable.on(lquery)
            row = db(query).select(ftable.id,
                                   ftable.controller,
                                   ftable.function,
                                   ftable.filter,
                                   ftable.trackable,
                                   ftable.use_site,
                                   ftable.opacity,
                                   ftable.cluster_attribute,
                                   ftable.cluster_distance,
                                   ftable.cluster_threshold,
                                   ftable.dir,
                                   ltable.style,
                                   left=left,
                                   limitby=(0, 1)).first()
            style = layer.get("style", row["gis_layer_config.style"])
            row = row["gis_layer_feature"]
            if row.use_site:
                maxdepth = 1
                show_ids = "&show_ids=true"
            else:
                maxdepth = 0
                show_ids = ""
            url = "%s.geojson?layer=%i&components=None&maxdepth=%s%s" % \
                (URL(row.controller, row.function), row.id, maxdepth, show_ids)
            # Use specified filter or fallback to the one in the layer
            filter = layer.get("filter", row.filter)
            if filter:
                url = "%s&%s" % (url, filter)
            if row.trackable:
                url = "%s&track=1" % url
            opacity = layer.get("opacity", row.opacity)
            cluster_attribute = layer.get("cluster_attribute",
                                          row.cluster_attribute)
            cluster_distance = layer.get("cluster_distance",
                                         row.cluster_distance)
            cluster_threshold = layer.get("cluster_threshold",
                                          row.cluster_threshold)
            dir = layer.get("dir", row.dir)
            if style:
                try:
                    # JSON Object?
                    style = json.loads(style)
                except:
                    style = None
            if not style:
                marker = layer.get("marker",
                                   Marker(layer_id=layer_id).as_dict())
        else:
            # URL to retrieve the data
            url = layer["url"]
            tablename = layer["tablename"]
            table = s3db[tablename]
            # Optimise the query & tell back-end not to add the type to the tooltips
            if "location_id" in table.fields:
                maxdepth = 0
                show_ids = ""
            elif "site_id" in table.fields:
                maxdepth = 1
                show_ids = "&show_ids=true"
            else:
                # Not much we can do!
                continue
            options = "components=None&maxdepth=%s%s&label_off=1" % \
                        (maxdepth, show_ids)
            if "?" in url:
                url = "%s&%s" % (url, options)
            else:
                url = "%s?%s" % (url, options)
            opacity = layer.get("opacity", 1)
            cluster_attribute = layer.get("cluster_attribute",
                                          CLUSTER_ATTRIBUTE)
            cluster_distance = layer.get("cluster_distance",
                                         CLUSTER_DISTANCE)
            cluster_threshold = layer.get("cluster_threshold",
                                          CLUSTER_THRESHOLD)
            dir = layer.get("dir", None)
            style = layer.get("style", None)
            if style:
                try:
                    # JSON Object?
                    style = json.loads(style)
                except:
                    style = None
            if not style:
                marker = layer.get("marker", None)

        if "active" in layer and not layer["active"]:
            _layer["visibility"] = False
        if opacity != 1:
            _layer["opacity"] = "%.1f" % opacity
        if cluster_attribute != CLUSTER_ATTRIBUTE:
            _layer["cluster_attribute"] = cluster_attribute
        if cluster_distance != CLUSTER_DISTANCE:
            _layer["cluster_distance"] = cluster_distance
        if cluster_threshold != CLUSTER_THRESHOLD:
            _layer["cluster_threshold"] = cluster_threshold
        if dir:
            _layer["dir"] = dir

        if style:
            _layer["style"] = style
        elif marker:
            # Per-layer Marker
            _layer["marker"] = dict(i = marker["image"],
                                    h = marker["height"],
                                    w = marker["width"],
                                    )
        else:
            # Request the server to provide per-feature Markers
            url = "%s&markers=1" % url
        _layer["url"] = url
        append(_layer)

    return layers_feature_resource

# =============================================================================
class Marker(object):
    """
        Represents a Map Marker

        @ToDo: Support Markers in Themes
    """

    def __init__(self, id=None, tablename=None, layer_id=None):

        db = current.db
        s3db = current.s3db
        mtable = s3db.gis_marker
        marker = None
        config = None
        polygons = False
        if id:
            # Lookup the Marker details from it's ID
            marker = db(mtable.id == id).select(mtable.image,
                                                mtable.height,
                                                mtable.width,
                                                limitby=(0, 1),
                                                cache=s3db.cache).first()
        elif layer_id:
            # Check if we have a Marker for this Layer
            config = GIS.get_config()
            ltable = s3db.gis_layer_symbology
            query = (ltable.layer_id == layer_id) & \
                    (ltable.symbology_id == config.symbology_id) & \
                    (ltable.marker_id == mtable.id)
            marker = db(query).select(mtable.image,
                                      mtable.height,
                                      mtable.width,
                                      limitby=(0, 1)).first()
            if not marker:
                # Check to see if we're a Polygon/LineString
                # (& hence shouldn't use a default marker)
                if tablename == "gis_layer_feature":
                    table = db.gis_layer_feature
                    query = (table.layer_id == layer_id)
                    layer = db(query).select(table.polygons,
                                             limitby=(0, 1)).first()
                    if layer and layer.polygons:
                        polygons = True
                elif tablename == "gis_layer_shapefile":
                    table = db.gis_layer_shapefile
                    query = (table.layer_id == layer_id)
                    layer = db(query).select(table.gis_feature_type,
                                             limitby=(0, 1)).first()
                    if layer and layer.gis_feature_type != 1:
                        polygons = True

        if marker:
            self.image = marker.image
            self.height = marker.height
            self.width = marker.width
        elif polygons:
            self.image = None
        else:
            # Default Marker
            if not config:
                config = GIS.get_config()
            self.image = config.marker_image
            self.height = config.marker_height
            self.width = config.marker_width

    # -------------------------------------------------------------------------
    def add_attributes_to_output(self, output):
        """
            Called by Layer.as_dict()
        """

        if self.image:
            output["marker"] = dict(i = self.image,
                                    h = self.height,
                                    w = self.width,
                                    )

    # -------------------------------------------------------------------------
    def as_dict(self):
        """
            Called by gis.get_marker(), feature_resources & s3profile
        """

        output = Storage(image = self.image,
                         height = self.height,
                         width = self.width,
                         )
        return output

# =============================================================================
class Projection(object):
    """
        Represents a Map Projection
    """

    def __init__(self, id=None):

        if id:
            s3db = current.s3db
            table = s3db.gis_projection
            query = (table.id == id)
            projection = current.db(query).select(table.epsg,
                                                  limitby=(0, 1),
                                                  cache=s3db.cache).first()
        else:
            # Default projection
            config = GIS.get_config()
            projection = Storage(epsg = config.epsg)

        self.epsg = projection.epsg

# =============================================================================
class Layer(object):
    """
        Abstract base class for Layers from Catalogue
    """

    def __init__(self):

        sublayers = []
        append = sublayers.append
        # List of Scripts to load async with the Map JavaScript
        self.scripts = []

        gis = current.response.s3.gis
        s3db = current.s3db
        s3_has_role = current.auth.s3_has_role

        # Read the Layers enabled in the Active Configs
        if gis.config is None:
            GIS.set_config()
        tablename = self.tablename
        table = s3db[tablename]
        ctable = s3db.gis_config
        ltable = s3db.gis_layer_config

        fields = table.fields
        metafields = s3_all_meta_field_names()
        fields = [table[f] for f in fields if f not in metafields]
        fields += [ltable.enabled,
                   ltable.visible,
                   ltable.base,
                   ltable.style,
                   ctable.pe_type,
                   ]
        query = (table.layer_id == ltable.layer_id) & \
                (ltable.config_id == ctable.id) & \
                (ltable.config_id.belongs(gis.config.ids))
        if gis.base == True:
            # Only show the default base layer
            if self.tablename == "gis_layer_empty":
                # Show even if disabled (as fallback)
                query = (table.id > 0)
            else:
                query &= (ltable.base == True)

        if current.deployment_settings.get_gis_layer_metadata():
            mtable = s3db.cms_post_layer
            left = mtable.on(mtable.layer_id == table.layer_id)
            fields.append(mtable.post_id)
        else:
            left = None
        rows = current.db(query).select(orderby=ctable.pe_type,
                                        left=left,
                                        *fields)
        layer_ids = []
        lappend = layer_ids.append
        SubLayer = self.SubLayer
        # Flag to show whether we've set the default baselayer
        # (otherwise a config higher in the hierarchy can overrule one lower down)
        base = True
        # Layers requested to be visible via URL (e.g. embedded map)
        visible = current.request.get_vars.get("layers", None)
        if visible:
            visible = visible.split(".")
        else:
            visible = []
        for _record in rows:
            record = _record[tablename]
            # Check if we've already seen this layer
            layer_id = record.layer_id
            if layer_id in layer_ids:
                continue
            # Add layer to list of checked
            lappend(layer_id)
            # Check if layer is enabled
            _config = _record["gis_layer_config"]
            if not _config.enabled:
                continue
            # Check user is allowed to access the layer
            role_required = record.role_required
            if role_required and not s3_has_role(role_required):
                continue
            # All OK - add SubLayer
            record["visible"] = _config.visible or str(layer_id) in visible
            if base and _config.base:
                # name can't conflict with OSM/WMS/ArcREST layers
                record["_base"] = True
                base = False
            else:
                record["_base"] = False
            if "style" not in record:
                # Take from the layer_config
                record["style"] = _config.style
            if left is not None:
                record["post_id"] = _record["cms_post_layer.post_id"]
            if tablename in ["gis_layer_bing", "gis_layer_google"]:
                # SubLayers handled differently
                append(record)
            else:
                append(SubLayer(tablename, record))

        # Alphasort layers
        # - client will only sort within their type: s3.gis.layers.js
        self.sublayers = sorted(sublayers, key=lambda row: row.name)

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        """
            Output the Layers as a Python dict
        """

        sublayer_dicts = []
        append = sublayer_dicts.append
        sublayers = self.sublayers
        for sublayer in sublayers:
            # Read the output dict for this sublayer
            sublayer_dict = sublayer.as_dict()
            if sublayer_dict:
                # Add this layer to the list of layers for this layer type
                append(sublayer_dict)

        if sublayer_dicts:
            if options:
                # Used by Map._setup()
                options[self.dictname] = sublayer_dicts
            else:
                # Used by as_json() and hence as_javascript()
                return sublayer_dicts

    # -------------------------------------------------------------------------
    def as_json(self):
        """
            Output the Layers as JSON
        """

        result = self.as_dict()
        if result:
            #return json.dumps(result, indent=4, separators=(",", ": "), sort_keys=True)
            return json.dumps(result, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layers as global Javascript
            - suitable for inclusion in the HTML page
        """

        result = self.as_json()
        if result:
            return '''S3.gis.%s=%s\n''' % (self.dictname, result)

    # -------------------------------------------------------------------------
    class SubLayer(object):
        def __init__(self, tablename, record):
            # Ensure all attributes available (even if Null)
            self.__dict__.update(record)
            del record
            self.safe_name = re.sub('[\\"]', "", self.name)

            if tablename not in ("gis_layer_arcrest",
                                 "gis_layer_coordinate",
                                 "gis_layer_empty",
                                 "gis_layer_js",
                                 "gis_layer_mgrs",
                                 "gis_layer_openstreetmap",
                                 "gis_layer_openweathermap",
                                 "gis_layer_theme",
                                 "gis_layer_tms",
                                 "gis_layer_wms",
                                 "gis_layer_xyz",
                                 ):
                # Layer uses Markers
                self.marker = Marker(tablename=tablename, layer_id=self.layer_id)
            if hasattr(self, "projection_id"):
                self.projection = Projection(self.projection_id)

        def setup_clustering(self, output):
            if hasattr(self, "cluster_attribute"):
                cluster_attribute = self.cluster_attribute
            else:
                cluster_attribute = None
            cluster_distance = self.cluster_distance
            cluster_threshold = self.cluster_threshold
            if cluster_attribute and \
               cluster_attribute != CLUSTER_ATTRIBUTE:
                output["cluster_attribute"] = cluster_attribute
            if cluster_distance != CLUSTER_DISTANCE:
                output["cluster_distance"] = cluster_distance
            if cluster_threshold != CLUSTER_THRESHOLD:
                output["cluster_threshold"] = cluster_threshold

        def setup_folder(self, output):
            if self.dir:
                output["dir"] = self.dir

        def setup_folder_and_visibility(self, output):
            if not self.visible:
                output["visibility"] = False
            if self.dir:
                output["dir"] = self.dir

        def setup_folder_visibility_and_opacity(self, output):
            if not self.visible:
                output["visibility"] = False
            if self.opacity != 1:
                output["opacity"] = "%.1f" % self.opacity
            if self.dir:
                output["dir"] = self.dir

        # ---------------------------------------------------------------------
        @staticmethod
        def add_attributes_if_not_default(output, **values_and_defaults):
            # could also write values in debug mode, to check if defaults ignored.
            # could also check values are not being overwritten.
            for key, (value, defaults) in values_and_defaults.iteritems():
                if value not in defaults:
                    output[key] = value

# -----------------------------------------------------------------------------
class LayerArcREST(Layer):
    """
        ArcGIS REST Layers from Catalogue
    """

    tablename = "gis_layer_arcrest"
    dictname = "layers_arcrest"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "arcrest",
                      "name": self.safe_name,
                      "url": self.url,
                      }

            # Attributes which are defaulted client-side if not set
            self.setup_folder_and_visibility(output)
            self.add_attributes_if_not_default(
                output,
                layers = (self.layers, ([0],)),
                transparent = (self.transparent, (True,)),
                base = (self.base, (False,)),
                _base = (self._base, (False,)),
            )

            return output

# -----------------------------------------------------------------------------
class LayerBing(Layer):
    """
        Bing Layers from Catalogue
    """

    tablename = "gis_layer_bing"
    dictname = "Bing"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            if Projection().epsg != 900913:
                raise Exception("Cannot display Bing layers unless we're using the Spherical Mercator Projection\n")
            apikey = current.deployment_settings.get_gis_api_bing()
            if not apikey:
                raise Exception("Cannot display Bing layers unless we have an API key\n")
            # Mandatory attributes
            ldict = {"ApiKey": apikey
                     }

            for sublayer in sublayers:
                # Attributes which are defaulted client-side if not set
                if sublayer._base:
                    # Set default Base layer
                    ldict["Base"] = sublayer.type
                if sublayer.type == "aerial":
                    ldict["Aerial"] = {"name": sublayer.name or "Bing Satellite",
                                       "id": sublayer.layer_id}
                elif sublayer.type == "road":
                    ldict["Road"] = {"name": sublayer.name or "Bing Roads",
                                     "id": sublayer.layer_id}
                elif sublayer.type == "hybrid":
                    ldict["Hybrid"] = {"name": sublayer.name or "Bing Hybrid",
                                       "id": sublayer.layer_id}
            if options:
                # Used by Map._setup()
                options[self.dictname] = ldict
            else:
                # Used by as_json() and hence as_javascript()
                return ldict

# -----------------------------------------------------------------------------
class LayerCoordinate(Layer):
    """
        Coordinate Layer from Catalogue
        - there should only be one of these
    """

    tablename = "gis_layer_coordinate"
    dictname = "CoordinateGrid"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            if current.response.s3.debug:
                self.scripts.append("gis/cdauth.js")
            else:
                self.scripts.append("gis/cdauth.min.js")
            sublayer = sublayers[0]
            name_safe = re.sub("'", "", sublayer.name)
            ldict = dict(name = name_safe,
                         visibility = sublayer.visible,
                         id = sublayer.layer_id)
            if options:
                # Used by Map._setup()
                options[self.dictname] = ldict
            else:
                # Used by as_json() and hence as_javascript()
                return ldict

# -----------------------------------------------------------------------------
class LayerEmpty(Layer):
    """
        Empty Layer from Catalogue
        - there should only be one of these
    """

    tablename = "gis_layer_empty"
    dictname = "EmptyLayer"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            sublayer = sublayers[0]
            name = str(current.T(sublayer.name))
            name_safe = re.sub("'", "", sublayer.name)
            ldict = dict(name = name_safe,
                         id = sublayer.layer_id)
            if sublayer._base:
                ldict["base"] = True
            if options:
                # Used by Map._setup()
                options[self.dictname] = ldict
            else:
                # Used by as_json() and hence as_javascript()
                return ldict

# -----------------------------------------------------------------------------
class LayerFeature(Layer):
    """
        Feature Layers from Catalogue
    """

    tablename = "gis_layer_feature"
    dictname = "layers_feature"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def __init__(self, tablename, record):
            controller = record.controller
            self.skip = False
            if controller is not None:
                if controller not in current.deployment_settings.modules:
                    # Module is disabled
                    self.skip = True
                if not current.auth.permission.has_permission("read",
                                                              c=controller,
                                                              f=record.function):
                    # User has no permission to this resource (in ACL)
                    self.skip = True
            else:
                raise Exception("Feature Layer Record '%s' has no controller" % record.name)
            super(LayerFeature.SubLayer, self).__init__(tablename, record)

        def as_dict(self):
            if self.skip:
                # Skip layer
                return
            if self.use_site:
                maxdepth = 1
                show_ids = "&show_ids=true"
            else:
                maxdepth = 0
                show_ids = ""
            url = "%s.geojson?layer=%i&components=None&maxdepth=%s%s" % \
                (URL(self.controller, self.function), self.id, maxdepth, show_ids)
            if self.filter:
                url = "%s&%s" % (url, self.filter)
            if self.trackable:
                url = "%s&track=1" % url
            style = self.style
            if style:
                try:
                    # JSON Object?
                    style = json.loads(style)
                except:
                    # Fieldname to pass to URL for server-side lookup
                    url = "%s&style=%s" % (url, style)
                    style = None

            # Mandatory attributes
            output = {"id": self.layer_id,
                      # Defaults client-side if not-provided
                      #"type": "feature",
                      "name": self.safe_name,
                      "url": url,
                      }

            # Attributes which are defaulted client-side if not set
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style
            else:
                self.marker.add_attributes_to_output(output)

            return output

# -----------------------------------------------------------------------------
class LayerGeoJSON(Layer):
    """
        GeoJSON Layers from Catalogue
    """

    tablename = "gis_layer_geojson"
    dictname = "layers_geojson"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "geojson",
                      "name": self.safe_name,
                      "url": self.url,
                      }

            # Attributes which are defaulted client-side if not set
            projection = self.projection
            if projection.epsg != 4326:
                output["projection"] = projection.epsg
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style
            else:
                self.marker.add_attributes_to_output(output)

            return output

# -----------------------------------------------------------------------------
class LayerGeoRSS(Layer):
    """
        GeoRSS Layers from Catalogue
    """

    tablename = "gis_layer_georss"
    dictname = "layers_georss"

    def __init__(self):
        super(LayerGeoRSS, self).__init__()
        LayerGeoRSS.SubLayer.cachetable = current.s3db.gis_cache

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            db = current.db
            request = current.request
            response = current.response
            cachetable = self.cachetable

            url = self.url
            # Check to see if we should Download layer to the cache
            download = True
            query = (cachetable.source == url)
            existing_cached_copy = db(query).select(cachetable.modified_on,
                                                    limitby=(0, 1)).first()
            refresh = self.refresh or 900 # 15 minutes set if we have no data (legacy DB)
            if existing_cached_copy:
                modified_on = existing_cached_copy.modified_on
                cutoff = modified_on + timedelta(seconds=refresh)
                if request.utcnow < cutoff:
                    download = False
            if download:
                # Download layer to the Cache
                from gluon.tools import fetch
                # @ToDo: Call directly without going via HTTP
                # @ToDo: Make this async by using S3Task (also use this for the refresh time)
                fields = ""
                if self.data:
                    fields = "&data_field=%s" % self.data
                if self.image:
                    fields = "%s&image_field=%s" % (fields, self.image)
                _url = "%s%s/update.georss?fetchurl=%s%s" % (current.deployment_settings.get_base_public_url(),
                                                             URL(c="gis", f="cache_feed"),
                                                             url,
                                                             fields)
                # Keep Session for local URLs
                import Cookie
                cookie = Cookie.SimpleCookie()
                cookie[response.session_id_name] = response.session_id
                current.session._unlock(response)
                try:
                    # @ToDo: Need to commit to not have DB locked with SQLite?
                    fetch(_url, cookie=cookie)
                    if existing_cached_copy:
                        # Clear old selfs which are no longer active
                        query = (cachetable.source == url) & \
                                (cachetable.modified_on < cutoff)
                        db(query).delete()
                except Exception, exception:
                    s3_debug("GeoRSS %s download error" % url, exception)
                    # Feed down
                    if existing_cached_copy:
                        # Use cached copy
                        # Should we Update timestamp to prevent every
                        # subsequent request attempting the download?
                        #query = (cachetable.source == url)
                        #db(query).update(modified_on=request.utcnow)
                        pass
                    else:
                        response.warning += "%s down & no cached copy available" % url

            name_safe = self.safe_name

            # Pass the GeoJSON URL to the client
            # Filter to the source of this feed
            url = "%s.geojson?cache.source=%s" % (URL(c="gis", f="cache_feed"),
                                                  url)

            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "georss",
                      "name": name_safe,
                      "url": url,
                      }
            self.marker.add_attributes_to_output(output)

            # Attributes which are defaulted client-side if not set
            if self.refresh != 900:
                output["refresh"] = self.refresh
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)

            return output

# -----------------------------------------------------------------------------
class LayerGoogle(Layer):
    """
        Google Layers/Tools from Catalogue
    """

    tablename = "gis_layer_google"
    dictname = "Google"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            T = current.T
            epsg = (Projection().epsg == 900913)
            settings = current.deployment_settings
            apikey = settings.get_gis_api_google()
            s3 = current.response.s3
            debug = s3.debug
            # Google scripts use document.write so cannot be loaded async via yepnope.js
            add_script = s3.scripts.append

            ldict = {}

            for sublayer in sublayers:
                # Attributes which are defaulted client-side if not set
                if sublayer.type == "earth":
                    ldict["Earth"] = str(T("Switch to 3D"))
                    #{"modules":[{"name":"earth","version":"1"}]}
                    add_script("http://www.google.com/jsapi?key=" + apikey + "&autoload=%7B%22modules%22%3A%5B%7B%22name%22%3A%22earth%22%2C%22version%22%3A%221%22%7D%5D%7D")
                    # Dynamic Loading not supported: https://developers.google.com/loader/#Dynamic
                    #s3.jquery_ready.append('''try{google.load('earth','1')catch(e){}''')
                    if debug:
                        self.scripts.append("gis/gxp/widgets/GoogleEarthPanel.js")
                    else:
                        self.scripts.append("gis/gxp/widgets/GoogleEarthPanel.min.js")
                    s3.js_global.append('''S3.public_url="%s"''' % settings.get_base_public_url())
                elif epsg:
                    # Earth is the only layer which can run in non-Spherical Mercator
                    # @ToDo: Warning?
                    if sublayer._base:
                        # Set default Base layer
                        ldict["Base"] = sublayer.type
                    if sublayer.type == "satellite":
                        ldict["Satellite"] = {"name": sublayer.name or "Google Satellite",
                                              "id": sublayer.layer_id}
                    elif sublayer.type == "maps":
                        ldict["Maps"] = {"name": sublayer.name or "Google Maps",
                                         "id": sublayer.layer_id}
                    elif sublayer.type == "hybrid":
                        ldict["Hybrid"] = {"name": sublayer.name or "Google Hybrid",
                                           "id": sublayer.layer_id}
                    elif sublayer.type == "streetview":
                        ldict["StreetviewButton"] = "Click where you want to open Streetview"
                    elif sublayer.type == "terrain":
                        ldict["Terrain"] = {"name": sublayer.name or "Google Terrain",
                                            "id": sublayer.layer_id}
                    elif sublayer.type == "mapmaker":
                        ldict["MapMaker"] = {"name": sublayer.name or "Google MapMaker",
                                             "id": sublayer.layer_id}
                    elif sublayer.type == "mapmakerhybrid":
                        ldict["MapMakerHybrid"] = {"name": sublayer.name or "Google MapMaker Hybrid",
                                                   "id": sublayer.layer_id}

            if "MapMaker" in ldict or "MapMakerHybrid" in ldict:
                # Need to use v2 API
                # This should be able to be fixed in OpenLayers now since Google have fixed in v3 API:
                # http://code.google.com/p/gmaps-api-issues/issues/detail?id=2349#c47
                add_script("http://maps.google.com/maps?file=api&v=2&key=%s" % apikey)
            else:
                # v3 API (3.10 is frozen, 3.11 release & 3.12 is nightly)
                add_script("http://maps.google.com/maps/api/js?v=3.11&sensor=false")
                if "StreetviewButton" in ldict:
                    # Streetview doesn't work with v2 API
                    ldict["StreetviewButton"] = str(T("Click where you want to open Streetview"))
                    ldict["StreetviewTitle"] = str(T("Street View"))
                    if debug:
                        self.scripts.append("gis/gxp/widgets/GoogleStreetViewPanel.js")
                    else:
                        self.scripts.append("gis/gxp/widgets/GoogleStreetViewPanel.min.js")

            if options:
                # Used by Map._setup()
                options[self.dictname] = ldict
            else:
                # Used by as_json() and hence as_javascript()
                return ldict

# -----------------------------------------------------------------------------
class LayerGPX(Layer):
    """
        GPX Layers from Catalogue
    """

    tablename = "gis_layer_gpx"
    dictname = "layers_gpx"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            url = URL(c="default", f="download",
                      args=self.track)

            # Mandatory attributes
            output = {"id": self.layer_id,
                      "name": self.safe_name,
                      "url": url,
                      }

            # Attributes which are defaulted client-side if not set
            self.marker.add_attributes_to_output(output)
            self.add_attributes_if_not_default(
                output,
                waypoints = (self.waypoints, (True,)),
                tracks = (self.tracks, (True,)),
                routes = (self.routes, (True,)),
            )
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            return output

# -----------------------------------------------------------------------------
class LayerJS(Layer):
    """
        JS Layers from Catalogue
        - these are raw Javascript layers for use by expert OpenLayers people
          to quickly add/configure new data sources without needing support
          from back-end Sahana programmers
    """

    tablename = "gis_layer_js"
    dictname = "layers_js"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            sublayer_dicts = []
            append = sublayer_dicts.append
            for sublayer in sublayers:
                append(sublayer.code)
            if options:
                # Used by Map._setup()
                options[self.dictname] = sublayer_dicts
            else:
                # Used by as_json() and hence as_javascript()
                return sublayer_dicts

# -----------------------------------------------------------------------------
class LayerKML(Layer):
    """
        KML Layers from Catalogue
    """

    tablename = "gis_layer_kml"
    dictname = "layers_kml"

    # -------------------------------------------------------------------------
    def __init__(self, init=True):
        "Set up the KML cache, should be done once per request"

        super(LayerKML, self).__init__()

        # Can we cache downloaded KML feeds?
        # Needed for unzipping & filtering as well
        # @ToDo: Should we move this folder to static to speed up access to cached content?
        #           Do we need to secure it?
        request = current.request
        cachepath = os.path.join(request.folder,
                                 "uploads",
                                 "gis_cache")

        if os.path.exists(cachepath):
            cacheable = os.access(cachepath, os.W_OK)
        else:
            try:
                os.mkdir(cachepath)
            except OSError, os_error:
                s3_debug("GIS: KML layers cannot be cached: %s %s" % \
                            (cachepath, os_error))
                cacheable = False
            else:
                cacheable = True
        # @ToDo: Migrate to gis_cache
        LayerKML.cachetable = current.s3db.gis_cache2
        LayerKML.cacheable = cacheable
        LayerKML.cachepath = cachepath

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            db = current.db
            request = current.request

            cachetable = LayerKML.cachetable
            cacheable = LayerKML.cacheable
            cachepath = LayerKML.cachepath

            name = self.name
            if cacheable:
                _name = urllib2.quote(name)
                _name = _name.replace("%", "_")
                filename = "%s.file.%s.kml" % (cachetable._tablename,
                                               _name)


                # Should we download a fresh copy of the source file?
                download = True
                query = (cachetable.name == name)
                cached = db(query).select(cachetable.modified_on,
                                          limitby=(0, 1)).first()
                refresh = self.refresh or 900 # 15 minutes set if we have no data (legacy DB)
                if cached:
                    modified_on = cached.modified_on
                    cutoff = modified_on + timedelta(seconds=refresh)
                    if request.utcnow < cutoff:
                        download = False

                if download:
                    # Download file (async, if workers alive)
                    response = current.response
                    session_id_name = response.session_id_name
                    session_id = response.session_id
                    current.s3task.async("gis_download_kml",
                                         args=[self.id, filename, session_id_name, session_id])
                    if cached:
                        db(query).update(modified_on=request.utcnow)
                    else:
                        cachetable.insert(name=name, file=filename)

                url = URL(c="default", f="download",
                          args=[filename])
            else:
                # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                # (Requires OpenLayers.Layer.KML to be available)
                url = self.url

            # Mandatory attributes
            output = dict(id = self.layer_id,
                          name = self.safe_name,
                          url = url,
                          )

            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                title = (self.title, ("name", None, "")),
                body = (self.body, ("description", None)),
                refresh = (self.refresh, (900,)),
            )
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style
            else:
                self.marker.add_attributes_to_output(output)

            return output

# -----------------------------------------------------------------------------
class LayerOSM(Layer):
    """
        OpenStreetMap Layers from Catalogue

        @ToDo: Provide a catalogue of standard layers which are fully-defined
               in static & can just have name over-ridden, as well as
               fully-custom layers.
    """

    tablename = "gis_layer_openstreetmap"
    dictname = "layers_osm"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):

            if Projection().epsg != 900913:
                # Cannot display OpenStreetMap layers unless we're using the Spherical Mercator Projection
                return {}

            # Mandatory attributes
            output = {"id": self.layer_id,
                      "name": self.safe_name,
                      "url1": self.url1,
                      }

            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                base = (self.base, (True,)),
                _base = (self._base, (False,)),
                url2 = (self.url2, ("",)),
                url3 = (self.url3, ("",)),
                zoomLevels = (self.zoom_levels, (9,)),
                attribution = (self.attribution, (None,)),
            )
            self.setup_folder_and_visibility(output)
            return output

# -----------------------------------------------------------------------------
class LayerOpenWeatherMap(Layer):
    """
       OpenWeatherMap Layers from Catalogue
    """

    tablename = "gis_layer_openweathermap"
    dictname = "OWM"

    # -------------------------------------------------------------------------
    def as_dict(self, options=None):
        sublayers = self.sublayers
        if sublayers:
            if current.response.s3.debug:
                self.scripts.append("gis/OWM.OpenLayers.js")
            else:
                self.scripts.append("gis/OWM.OpenLayers.min.js")
            ldict = {}
            for sublayer in sublayers:
                if sublayer.type == "station":
                    ldict["station"] = {"name": sublayer.name or "Weather Stations",
                                        "id": sublayer.layer_id,
                                        "dir": sublayer.dir,
                                        "visibility": sublayer.visible
                                        }
                elif sublayer.type == "city":
                    ldict["city"] = {"name": sublayer.name or "Current Weather",
                                     "id": sublayer.layer_id,
                                     "dir": sublayer.dir,
                                     "visibility": sublayer.visible
                                     }
            if options:
                # Used by Map._setup()
                options[self.dictname] = ldict
            else:
                # Used by as_json() and hence as_javascript()
                return ldict

# -----------------------------------------------------------------------------
class LayerShapefile(Layer):
    """
        Shapefile Layers from Catalogue
    """

    tablename = "gis_layer_shapefile"
    dictname = "layers_shapefile"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            url = "%s/%s/data.geojson" % \
                (URL(c="gis", f="layer_shapefile"), self.id)
            if self.filter:
                url = "%s?layer_shapefile_%s.%s" % (url, self.id, self.filter)

            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "shapefile",
                      "name": self.safe_name,
                      "url": url,
                      # Shapefile layers don't alter their contents, so don't refresh
                      "refresh": 0,
                      }
            
            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                desc = (self.description, (None, "")),
                src = (self.source_name, (None, "")),
                src_url = (self.source_url, (None, "")),
            )
            # We convert on-upload to have BBOX handling work properly
            #projection = self.projection
            #if projection.epsg != 4326:
            #    output["projection"] = projection.epsg
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style
            else:
                self.marker.add_attributes_to_output(output)

            return output

# -----------------------------------------------------------------------------
class LayerTheme(Layer):
    """
        Theme Layers from Catalogue
    """

    tablename = "gis_layer_theme"
    dictname = "layers_theme"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            url = "%s.geojson?theme_data.layer_theme_id=%i&polygons=1&maxdepth=0" % \
                (URL(c="gis", f="theme_data"), self.id)

            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "theme",
                      "name": self.safe_name,
                      "url": url,
                      }

            # Attributes which are defaulted client-side if not set
            self.setup_folder_and_visibility(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style

            return output

# -----------------------------------------------------------------------------
class LayerTMS(Layer):
    """
        TMS Layers from Catalogue
    """

    tablename = "gis_layer_tms"
    dictname = "layers_tms"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = {"id": self.layer_id,
                      "type": "tms",
                      "name": self.safe_name,
                      "url": self.url,
                      "layername": self.layername
                      }

            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                _base = (self._base, (False,)),
                url2 = (self.url2, (None,)),
                url3 = (self.url3, (None,)),
                format = (self.img_format, ("png", None)),
                zoomLevels = (self.zoom_levels, (19,)),
                attribution = (self.attribution, (None,)),
            )
            self.setup_folder(output)
            return output

# -----------------------------------------------------------------------------
class LayerWFS(Layer):
    """
        WFS Layers from Catalogue
    """

    tablename = "gis_layer_wfs"
    dictname = "layers_wfs"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = dict(id = self.layer_id,
                          name = self.safe_name,
                          url = self.url,
                          title = self.title,
                          featureType = self.featureType,
                          )

            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                version = (self.version, ("1.1.0",)),
                featureNS = (self.featureNS, (None, "")),
                geometryName = (self.geometryName, ("the_geom",)),
                schema = (self.wfs_schema, (None, "")),
                username = (self.username, (None, "")),
                password = (self.password, (None, "")),
                projection = (self.projection.epsg, (4326,)),
                desc = (self.description, (None, "")),
                src = (self.source_name, (None, "")),
                src_url = (self.source_url, (None, "")),
                refresh = (self.refresh, (0,)),
                #editable
            )
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            style = self.style
            if style:
                style = json.loads(style)
                output["style"] = style
            else:
                self.marker.add_attributes_to_output(output)

            return output

# -----------------------------------------------------------------------------
class LayerWMS(Layer):
    """
        WMS Layers from Catalogue
    """

    tablename = "gis_layer_wms"
    dictname = "layers_wms"

    # -------------------------------------------------------------------------
    def __init__(self):
        super(LayerWMS, self).__init__()
        if self.sublayers:
            if current.response.s3.debug:
                self.scripts.append("gis/gxp/plugins/WMSGetFeatureInfo.js")
            else:
                self.scripts.append("gis/gxp/plugins/WMSGetFeatureInfo.min.js")

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            if self.queryable:
                current.response.s3.gis.get_feature_info = True
            # Mandatory attributes
            output = dict(id = self.layer_id,
                          name = self.safe_name,
                          url = self.url,
                          layers = self.layers
                          )

            # Attributes which are defaulted client-side if not set
            legend_url = self.legend_url
            if legend_url and not legend_url.startswith("http"):
                legend_url = "%s/%s%s" % \
                    (current.deployment_settings.get_base_public_url(),
                     current.request.application,
                     legend_url)
            attr = dict(transparent = (self.transparent, (True,)),
                        version = (self.version, ("1.1.1",)),
                        format = (self.img_format, ("image/png",)),
                        map = (self.map, (None, "")),
                        username = (self.username, (None, "")),
                        password = (self.password, (None, "")),
                        buffer = (self.buffer, (0,)),
                        base = (self.base, (False,)),
                        _base = (self._base, (False,)),
                        style = (self.style, (None, "")),
                        bgcolor = (self.bgcolor, (None, "")),
                        tiled = (self.tiled, (False,)),
                        legendURL = (legend_url, (None, "")),
                        queryable = (self.queryable, (False,)),
                        desc = (self.description, (None, "")),
                        )
            
            if current.deployment_settings.get_gis_layer_metadata():
                # Use CMS to add info about sources
                attr["post_id"] = (self.post_id, (None, ""))
            else:
                # Link direct to sources
                attr.update(src = (self.source_name, (None, "")),
                            src_url = (self.source_url, (None, "")),
                            )

            self.add_attributes_if_not_default(output, **attr)
            self.setup_folder_visibility_and_opacity(output)

            return output

# -----------------------------------------------------------------------------
class LayerXYZ(Layer):
    """
        XYZ Layers from Catalogue
    """

    tablename = "gis_layer_xyz"
    dictname = "layers_xyz"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = {"id": self.layer_id,
                      "name": self.safe_name,
                      "url": self.url
                      }

            # Attributes which are defaulted client-side if not set
            self.add_attributes_if_not_default(
                output,
                _base = (self._base, (False,)),
                url2 = (self.url2, (None,)),
                url3 = (self.url3, (None,)),
                format = (self.img_format, ("png", None)),
                zoomLevels = (self.zoom_levels, (19,)),
                attribution = (self.attribution, (None,)),
            )
            self.setup_folder(output)
            return output

# =============================================================================
class S3Map(S3Method):
    """
        Class to generate a Map linked to Search filters
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point to apply map method to S3Requests
            - produces a full page with S3FilterWidgets above a Map

            @param r: the S3Request isntance
            @param attr: controller attributes for the request

            @return: output object to send to the view
        """

        if r.http == "GET":
            representation = r.representation
            if representation == "html":
                return self.page(r, **attr)

        else:
            r.error(405, current.manager.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def page(self, r, **attr):
        """
            Map page

            @param r: the S3Request instance
            @param attr: controller attributes for the request
        """

        if r.representation in ("html", "iframe"):

            s3db = current.s3db
            response = current.response
            resource = self.resource
            get_config = resource.get_config
            tablename = resource.tablename

            widget_id = "default_map"

            output = {}

            title = response.s3.crud_strings[tablename].get("title_map",
                                                            current.T("Map"))
            output["title"] = title

            # Filter widgets
            filter_widgets = get_config("filter_widgets", None)
            if filter_widgets and not self.hide_filter:
                advanced = False
                for widget in filter_widgets:
                    if "hidden" in widget.opts and widget.opts.hidden:
                        advanced = resource.get_config("map_advanced", True)
                        break

                request = self.request
                from s3filter import S3FilterForm
                filter_formstyle = get_config("filter_formstyle", None)
                submit = resource.get_config("map_submit", True)
                filter_form = S3FilterForm(filter_widgets,
                                           formstyle=filter_formstyle,
                                           advanced=advanced,
                                           submit=submit,
                                           ajax=True,
                                           # URL to update the Filter Widget Status
                                           ajaxurl=r.url(method="filter",
                                                         vars={},
                                                         representation="options"),
                                           _class="filter-form",
                                           _id="%s-filter-form" % widget_id,
                                           )
                get_vars = request.get_vars
                filter_form = filter_form.html(resource, get_vars=get_vars, target=widget_id)
            else:
                # Render as empty string to avoid the exception in the view
                filter_form = ""

            output["form"] = filter_form

            # Map
            output["map"] = self.widget(r, widget_id=widget_id,
                                        callback='''S3.search.s3map()''', **attr)

            # View
            response.view = self._view(r, "map.html")

            return output

        else:
            r.error(501, r.ERROR.BAD_FORMAT)

    # -------------------------------------------------------------------------
    def widget(self,
               r,
               method="map",
               widget_id=None,
               visible=True,
               callback=None,
               **attr):
        """
            Render a Map widget suitable for use in an S3Filter-based page
            such as S3Summary
            
            @param r: the S3Request
            @param method: the widget method
            @param widget_id: the widget ID
            @param callback: None by default in case DIV is hidden
            @param visible: whether the widget is initially visible
            @param attr: controller attributes
        """

        if not widget_id:
            widget_id = "default_map"

        gis = current.gis
        tablename = self.tablename

        marker_fn = current.s3db.get_config(tablename, "marker_fn")
        if marker_fn:
            # Per-feature markers added in get_location_data()
            marker = None
        else:
            # Single Marker for the layer
            request = self.request
            marker = gis.get_marker(request.controller,
                                    request.function)

        url = URL(extension="geojson", args=None)

        # @ToDo: Support maps with multiple layers (Dashboards)
        #layer_id = "search_results_%s" % widget_id
        layer_id = "search_results"
        feature_resources = [{"name"      : current.T("Search Results"),
                              "id"        : layer_id,
                              "tablename" : tablename,
                              "url"       : url,
                              # We activate in callback after ensuring URL is updated for current filter status
                              "active"    : False,
                              "marker"    : marker
                              }]

        map = gis.show_map(id = widget_id,
                           feature_resources = feature_resources,
                           #catalogue_layers = True,
                           collapsed = True,
                           legend = True,
                           #toolbar = True,
                           #search = True,
                           save = False,
                           callback = callback,
                           )
        return map

# =============================================================================
class S3ExportPOI(S3Method):
    """ Export point-of-interest resources for a location """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        manager = current.manager
        output = dict()

        if r.http == "GET":
            output = self.export(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def export(self, r, **attr):
        """
            Export POI resources.

            URL options:

                - "resources"   list of tablenames to export records from

                - "msince"      datetime in ISO format, "auto" to use the
                                feed's last update

                - "update_feed" 0 to skip the update of the feed's last
                                update datetime, useful for trial exports

            Supported formats:

                .xml            S3XML
                .osm            OSM XML Format
                .kml            Google KML

            (other formats can be requested, but may give unexpected results)

            @param r: the S3Request
            @param attr: controller options for this request
        """

        import datetime, time
        tfmt = current.xml.ISOFORMAT

        # Determine request Lx
        current_lx = r.record
        if not current_lx: # or not current_lx.level:
            # Must have a location
            r.error(400, current.manager.error.BAD_REQUEST)
        else:
            self.lx = current_lx.id

        tables = []
        # Parse the ?resources= parameter
        if "resources" in r.get_vars:
            resources = r.get_vars["resources"]
        else:
            # Fallback to deployment_setting
            resources = current.deployment_settings.get_gis_poi_resources()
        if not isinstance(resources, list):
            resources = [resources]
        [tables.extend(t.split(",")) for t in resources]

        # Parse the ?update_feed= parameter
        update_feed = True
        if "update_feed" in r.get_vars:
            _update_feed = r.get_vars["update_feed"]
            if _update_feed == "0":
                update_feed = False

        # Parse the ?msince= parameter
        msince = None
        if "msince" in r.get_vars:
            msince = r.get_vars["msince"]
            if msince.lower() == "auto":
                msince = "auto"
            else:
                try:
                    (y, m, d, hh, mm, ss, t0, t1, t2) = \
                        time.strptime(msince, tfmt)
                    msince = datetime.datetime(y, m, d, hh, mm, ss)
                except ValueError:
                    msince = None

        # Export a combined tree
        tree = self.export_combined_tree(tables,
                                         msince=msince,
                                         update_feed=update_feed)

        xml = current.xml
        manager = current.manager

        # Set response headers
        headers = current.response.headers
        representation = r.representation
        if r.representation in manager.json_formats:
            as_json = True
            default = "application/json"
        else:
            as_json = False
            default = "text/xml"
        headers["Content-Type"] = manager.content_type.get(representation,
                                                           default)

        # Find XSLT stylesheet and transform
        stylesheet = r.stylesheet()
        if tree and stylesheet is not None:
            args = Storage(domain=manager.domain,
                           base_url=manager.s3.base_url,
                           utcnow=datetime.datetime.utcnow().strftime(tfmt))
            tree = xml.transform(tree, stylesheet, **args)
        if tree:
            if as_json:
                output = xml.tree2json(tree, pretty_print=True)
            else:
                output = xml.tostring(tree, pretty_print=True)

        return output

    # -------------------------------------------------------------------------
    def export_combined_tree(self, tables, msince=None, update_feed=True):
        """
            Export a combined tree of all records in tables, which
            are in Lx, and have been updated since msince.

            @param tables: list of table names
            @param msince: minimum modified_on datetime, "auto" for
                           automatic from feed data, None to turn it off
            @param update_feed: update the last_update datetime in the feed
        """

        db = current.db
        s3db = current.s3db
        ftable = s3db.gis_poi_feed

        lx = self.lx

        elements = []
        results = 0
        for tablename in tables:

            # Define the resource
            try:
                resource = s3db.resource(tablename, components=[])
            except AttributeError:
                # Table not defined (module deactivated?)
                continue

            # Check
            if "location_id" not in resource.fields:
                # Hardly a POI resource without location_id
                continue

            # Add Lx filter
            self._add_lx_filter(resource, lx)

            # Get the feed data
            query = (ftable.tablename == tablename) & \
                    (ftable.location_id == lx)
            feed = db(query).select(limitby=(0, 1)).first()
            if msince == "auto":
                if feed is None:
                    _msince = None
                else:
                    _msince = feed.last_update
            else:
                _msince = msince

            # Export the tree and append its element to the element list
            tree = resource.export_tree(msince=_msince,
                                        references=["location_id"])

            # Update the feed data
            if update_feed:
                muntil = resource.muntil
                if feed is None:
                    ftable.insert(location_id = lx,
                                  tablename = tablename,
                                  last_update = muntil)
                else:
                    feed.update_record(last_update = muntil)

            elements.extend([c for c in tree.getroot()])

        # Combine all elements in one tree and return it
        tree = current.xml.tree(elements, results=len(elements))
        return tree

    # -------------------------------------------------------------------------
    @staticmethod
    def _add_lx_filter(resource, lx):
        """
            Add a Lx filter for the current location to this
            resource.

            @param resource: the resource
        """

        from s3resource import S3FieldSelector as FS
        query = (FS("location_id$path").contains("/%s/" % lx)) | \
                (FS("location_id$path").like("%s/%%" % lx))
        resource.add_filter(query)

# -----------------------------------------------------------------------------
class S3ImportPOI(S3Method):
    """
        Import point-of-interest resources for a location
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_method(r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        if r.representation == "html":

            T = current.T
            s3db = current.s3db
            request = current.request
            response = current.response

            title = T("Import from OpenStreetMap")

            res_select = [TR(TD(B("%s: " % T("Select resources to import")),
                                _colspan=3))]
            for resource in current.deployment_settings.get_gis_poi_resources():
                id = "res_" + resource
                res_select.append(TR(TD(LABEL(resource, _for=id)),
                                     TD(INPUT(_type="checkbox",
                                              _name=id,
                                              _id=id,
                                              _checked=True)),
                                     TD()))

            form = FORM(
                    TABLE(
                        TR(TD(T("Can read PoIs either from an OpenStreetMap file (.osm) or mirror."),
                              _colspan=3),
                           ),
                        TR(TD(B("%s: " % T("File"))),
                           TD(INPUT(_type="file", _name="file", _size="50")),
                           TD(SPAN("*", _class="req",
                                   _style="padding-right: 5px;"))
                           ),
                        TR(TD(),
                           TD(T("or")),
                           TD(),
                           ),
                        TR(TD(B("%s: " % T("Host"))),
                           TD(INPUT(_type="text", _name="host",
                                    _id="host", _value="localhost")),
                           TD(),
                           ),
                        TR(TD(B("%s: " % T("Database"))),
                           TD(INPUT(_type="text", _name="database",
                                    _id="database", _value="osm")),
                           TD(),
                           ),
                        TR(TD(B("%s: " % T("User"))),
                           TD(INPUT(_type="text", _name="user",
                                    _id="user", _value="osm")),
                           TD(),
                           ),
                        TR(TD(B("%s: " % T("Password"))),
                           TD(INPUT(_type="text", _name="password",
                                    _id="password", _value="planet")),
                           TD(),
                           ),
                        TR(TD(B("%s: " % T("Ignore Errors?"))),
                           TD(INPUT(_type="checkbox", _name="ignore_errors",
                                    _id="ignore_errors")),
                           TD(),
                           ),
                        res_select,
                        TR(TD(),
                           TD(INPUT(_type="submit", _value=T("Import"))),
                           TD(),
                           )
                        )
                    )

            if not r.id:
                from s3validators import IS_LOCATION
                from s3widgets import S3LocationAutocompleteWidget
                # dummy field
                field = s3db.org_office.location_id
                field.requires = IS_NULL_OR(IS_LOCATION())
                widget = S3LocationAutocompleteWidget()(field, None)
                row = TR(TD(B("%s: " % T("Location"))),
                         TD(widget),
                         TD(SPAN("*", _class="req",
                                 _style="padding-right: 5px;"))
                         )
                form[0].insert(3, row)

            response.view = "create.html"
            output = dict(title=title,
                          form=form)

            if form.accepts(request.vars, current.session):

                vars = form.vars
                if vars.file != "":
                    File = vars.file.file
                else:
                    # Create .poly file
                    if r.record:
                        record = r.record
                    elif not vars.location_id:
                        form.errors["location_id"] = T("Location is Required!")
                        return output
                    else:
                        gtable = s3db.gis_location
                        record = current.db(gtable.id == vars.location_id).select(gtable.name,
                                                                                  gtable.wkt,
                                                                                  limitby=(0, 1)
                                                                                  ).first()
                        if record.wkt is None:
                            form.errors["location_id"] = T("Location needs to have WKT!")
                            return output
                    error = GIS.create_poly(record)
                    if error:
                        current.session.error = error
                        redirect(URL(args=r.id))
                    # Use Osmosis to extract an .osm file using this .poly
                    name = record.name
                    if os.path.exists(os.path.join(os.getcwd(), "temp")): # use web2py/temp
                        TEMP = os.path.join(os.getcwd(), "temp")
                    else:
                        import tempfile
                        TEMP = tempfile.gettempdir()
                    filename = os.path.join(TEMP, "%s.osm" % name)
                    cmd = ["/home/osm/osmosis/bin/osmosis", # @ToDo: deployment_setting
                           "--read-pgsql",
                           "host=%s" % vars.host,
                           "database=%s" % vars.database,
                           "user=%s" % vars.user,
                           "password=%s" % vars.password,
                           "--dataset-dump",
                           "--bounding-polygon",
                           "file=%s" % os.path.join(TEMP, "%s.poly" % name),
                           "--write-xml",
                           "file=%s" % filename,
                           ]
                    import subprocess
                    try:
                        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
                    except subprocess.CalledProcessError, e:
                        current.session.error = T("OSM file generation failed: %s") % e.output
                        redirect(URL(args=r.id))
                    except AttributeError:
                        # Python < 2.7
                        error = subprocess.call(cmd, shell=True)
                        if error:
                            s3_debug(cmd)
                            current.session.error = T("OSM file generation failed!")
                            redirect(URL(args=r.id))
                    try:
                        File = open(filename, "r")
                    except:
                        current.session.error = T("Cannot open created OSM file!")
                        redirect(URL(args=r.id))

                stylesheet = os.path.join(request.folder, "static", "formats",
                                          "osm", "import.xsl")
                ignore_errors = vars.get("ignore_errors", None)
                xml = current.xml
                tree = xml.parse(File)
                define_resource = s3db.resource
                response.error = ""
                import_count = 0

                import_res = []
                for resource in current.deployment_settings.get_gis_poi_resources():
                    if getattr(vars, "res_" + resource):
                        import_res.append(resource)

                for tablename in import_res:
                    try:
                        table = s3db[tablename]
                    except:
                        # Module disabled
                        continue
                    resource = define_resource(tablename)
                    s3xml = xml.transform(tree, stylesheet_path=stylesheet,
                                          name=resource.name)
                    try:
                        success = resource.import_xml(s3xml,
                                                      ignore_errors=ignore_errors)
                        import_count += resource.import_count
                    except:
                        import sys
                        response.error += str(sys.exc_info()[1])
                if import_count:
                    response.confirmation = "%s %s" % \
                        (import_count,
                         T("PoIs successfully imported."))
                else:
                    response.information = T("No PoIs available.")

            return output

        else:
            raise HTTP(501, BADMETHOD)

# END =========================================================================
