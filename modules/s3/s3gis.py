# -*- coding: utf-8 -*-

"""
    GIS Module

    @version: 0.9.0

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @copyright: (c) 2010-2012 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
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

__all__ = ["GIS", "GoogleGeocoder", "YahooGeocoder"]

import os
import re
import sys
import copy
#import logging
import math             # Needed for greatCircleDistance
#import random          # Needed when feature_queries are passed in without a name
import urllib           # Needed for urlencoding
import urllib2          # Needed for quoting & error handling on fetch
import Cookie           # Needed for Sessions on Internal KML feeds
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
from datetime import timedelta  # Needed for Feed Refresh checks
import zipfile          # Needed to unzip KMZ files

try:
    from lxml import etree # Needed to follow NetworkLinks
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

KML_NAMESPACE = "http://earth.google.com/kml/2.2"

from gluon import *
from gluon.dal import Rows
from gluon.storage import Storage, Messages
from gluon.tools import fetch
import gluon.contrib.simplejson as json
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3method import S3Method
from s3utils import s3_debug, s3_fullname

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    s3_debug("WARNING: %s: Shapely GIS library not installed" % __name__)

# Map WKT types to db types
GEOM_TYPES = {
    "point": 1,
    "linestring": 2,
    "polygon": 3,
    "multipoint": 4,
    "multilinestring": 5,
    "multipolygon": 6,
    "geometrycollection": 7,
}

# km
RADIUS_EARTH = 6371.01

# Garmin GPS Symbols
GPS_SYMBOLS = [
    "Airport",
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
        GIS functions
    """

    def __init__(self):
        settings = current.deployment_settings
        if not current.db is not None:
            raise RuntimeError, "Database must not be None"
        if not current.auth is not None:
            raise RuntimeError, "Undefined authentication controller"
        messages = current.messages
        #messages.centroid_error = str(A("Shapely", _href="http://pypi.python.org/pypi/Shapely/", _target="_blank")) + " library not found, so can't find centroid!"
        messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        messages.unknown_type = "Unknown Type!"
        messages.invalid_wkt_point = "Invalid WKT: must be like POINT(3 4)"
        messages.invalid_wkt = "Invalid WKT: see http://en.wikipedia.org/wiki/Well-known_text"
        messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.gps_symbols = GPS_SYMBOLS
        self.DEFAULT_SYMBOL = "White Dot"
        self.hierarchy_level_keys = ["L0", "L1", "L2", "L3", "L4"]
        self.hierarchy_levels = {}
        self.max_allowed_level_num = 4
        self.region_level_keys = ["L0", "L1", "L2", "L3", "L4", "GR"]
        # Info for countries. These will be filled in once the gis_location
        # table is available and populated with L0 countries.
        # countries and site countries are lists (or Rows) of Storage, ordered
        # by country name. Each element contains L0 location id (key "id"),
        # country code (key "code"), and name (key "name").
        self.countries = None  # id, code, and name for all countries
        self.site_countries = None  # same for this site's countries
        # These will be OrderedDicts of id or code vs. country name.
        self.countries_by_id = None
        self.countries_by_code = None
        self.site_countries_by_id = None
        self.site_countries_by_code = None

    # -------------------------------------------------------------------------
    @staticmethod
    def abbreviate_wkt(wkt, max_length=30):
        if not wkt:
            # Blank WKT field
            return None
        elif len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index("(")]
        else:
            return wkt

    # -------------------------------------------------------------------------
    def download_kml(self, record_id, filename):
        """
            Download a KML file:
                - unzip it if-required
                - follow NetworkLinks recursively if-required

            Save the file to the /uploads folder

            Designed to be called asynchronously using:
                current.s3task.async("download_kml", [record_id, filename])

            @ToDo: Pass error messages to Result & have JavaScript listen for these
        """

        db = current.db

        layer = KMLLayer()

        query = (layer.table.id == record_id)
        record = db(query).select(limitby=(0, 1)).first()
        url = record.url

        cachepath = layer.cachepath
        filepath = os.path.join(cachepath, filename)

        warning = self.fetch_kml(url, filepath)

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
                pass

    # -------------------------------------------------------------------------
    def fetch_kml(self, url, filepath):
        """
            Fetch a KML file:
                - unzip it if-required
                - follow NetworkLinks recursively if-required

            Returns a file object

            Designed as a helper function for download_kml()
        """

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
            cookie = Cookie.SimpleCookie()
            cookie[response.session_id_name] = response.session_id
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

        if file[:2] == "PK":
            # Unzip
            fp = StringIO(file)
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
            filenames = []
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
    def get_bearing(lat_start, lon_start, lat_end, lon_end):
        """
            Given a Start & End set of Coordinates, return a Bearing
            Formula from: http://www.movable-type.co.uk/scripts/latlong.html
        """

        import math

        delta_lon = lon_start - lon_end
        bearing = math.atan2( math.sin(delta_lon) * math.cos(lat_end),
                             (math.cos(lat_start) * math.sin(lat_end)) - \
                             (math.sin(lat_start) * math.cos(lat_end) * math.cos(delta_lon)) )
        # Convert to a compass bearing
        bearing = (bearing + 360) % 360

        return bearing

    # -------------------------------------------------------------------------
    def get_bounds(self, features=[]):
        """
            Calculate the Bounds of a list of Features
            e.g. When a map is displayed that focuses on a collection of points,
                 the map is zoomed to show just the region bounding the points.
            e.g. To use in GPX export for correct zooming
`
            Ensure a minimum size of bounding box, and that the points
            are inset from the border.
            @ToDo: Optimised Geospatial routines rather than this crude hack
        """

        # 
        # Minimum Bounding Box
        # - gives a minimum width and height in degrees for the region shown.
        # Without this, a map showing a single point would not show any extent around that point.
        bbox_min_size = 0.05
        # Bounding Box Insets
        # - adds a small amount of distance outside the points.
        # Without this, the outermost points would be on the bounding box, and might not be visible.
        bbox_inset = 0.007

        if len(features) > 0:

            min_lon = 180
            min_lat = 90
            max_lon = -180
            max_lat = -90

            # Is this a simple feature set or the result of a join?
            try:
                lon = features[0].lon
                simple = True
            except (AttributeError, KeyError):
                simple = False

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

                min_lon = min(lon, min_lon)
                min_lat = min(lat, min_lat)
                max_lon = max(lon, max_lon)
                max_lat = max(lat, max_lat)

            # Assure a reasonable-sized box.
            delta_lon = (bbox_min_size - (max_lon - min_lon)) / 2.0
            if delta_lon > 0:
                min_lon -= delta_lon
                max_lon += delta_lon
            delta_lat = (bbox_min_size - (max_lat - min_lat)) / 2.0
            if delta_lat > 0:
                min_lat -= delta_lat
                max_lat += delta_lat
            
            # Move bounds outward by specified inset.
            min_lon -= bbox_inset
            max_lon += bbox_inset
            min_lat -= bbox_inset
            max_lat += bbox_inset

            # Check that we're still within overall bounds
            # - seems unnecessary?
            #min_lon = max(config.min_lon, min_lon)
            #min_lat = max(config.min_lat, min_lat)
            #max_lon = min(config.max_lon, max_lon)
            #max_lat = min(config.max_lat, max_lat)

        else:
            # no features
            config = self.get_config()
            min_lon = config.min_lon or -180
            max_lon = config.max_lon or 180
            min_lat = config.min_lat or -90
            max_lat = config.max_lat or 90

        return dict(min_lon=min_lon, min_lat=min_lat,
                    max_lon=max_lon, max_lat=max_lat)

    # -------------------------------------------------------------------------
    @staticmethod
    def _lookup_parent_path(feature_id):
        """
            Helper that gets parent and path for a location.
        """

        db = current.db
        table = db.gis_location

        query = (table.id == feature_id)
        feature = db(query).select(table.path,
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
        """

        db = current.db
        table = db.gis_location

        query = (table.deleted == False)
        if level:
            query = query & (table.level == level)
        term = str(id)
        query = query & ((table.path.like(term + "/%")) | \
                         (table.path.like("%/" + term + "/%")))
        children = db(query).select(table.id,
                                    table.name)
        return children

    # -------------------------------------------------------------------------
    def get_parents(self, feature_id, feature=None, ids_only=False):
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

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location

        if not feature or "path" not in feature or "parent" not in feature:
            feature = self._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = self.update_location_tree(feature_id, feature.parent)

            path_list = map(int, path.split("/"))
            if len(path_list) == 1:
                # No parents -- path contains only this feature.
                return None

            # Get path in the desired order, without current feature.
            reverse_path = path_list[:-1]
            reverse_path.reverse()

            # If only ids are wanted, stop here.
            if ids_only:
                return reverse_path

            # Retrieve parents - order in which they're returned is arbitrary.
            query = (table.id.belongs(reverse_path))
            fields = [table.id, table.name, table.code, table.level, table.lat, table.lon]
            unordered_parents = db(query).select(cache=cache, *fields)

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

        if not feature or "path" not in feature or "parent" not in feature:
            feature = self._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = self.update_location_tree(feature_id, feature.parent)

            # Get ids of ancestors at each level.
            if feature.parent:
                strict = self.get_strict_hierarchy(feature.parent)
            else:
                strict = self.get_strict_hierarchy(feature_id)
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
                ancestors = self.get_parents(feature_id, feature=feature)
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

            if names:
                # We need to have entries for all levels
                # (both for address onvalidation & new LocationSelector)
                hierarchy_level_keys = self.hierarchy_level_keys
                for key in hierarchy_level_keys:
                    if not results.has_key(key):
                        results[key] = None

        return results

    # -------------------------------------------------------------------------
    def get_parents_of_level(self, locations, level):
        """
            Given a list of gis_location.ids, return a list of the Parents of
            the given Level (Lx)

            - used by S3Report
        """

        output = []

        if not locations or not level:
            return output

        while locations:
            # Recursively pull out good records & try parents agaian
            (newoutput, locations) = self._get_parents_of_level(locations, level)
            for id in newoutput:
                output.append(id)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_parents_of_level(locations, level):
        """
            Given a list of gis_location.ids, return a list of the Parents of
            the given Level (Lx)

            - helper functions used by get_parents_of_level() to handle recursion
        """

        output = []

        if not locations or not level:
            return output

        # Read the records from the database
        db = current.db
        s3db = current.s3db
        table = s3db.gis_location
        query = (table.id.belongs(locations))
        rows = db(query).select(table.id,
                                table.level,
                                table.parent,
                                table.path)

        tryagain = []

        for row in rows:
            _level = row.level
            if _level == level:
                # We're already at the right level, pass it back
                output.append(row.id)
            elif _level[1:] > level[1:]:
                # We're already too high, skip
                continue
            else:
                # Try the Path
                path = row.path
                if path:
                    ids = path.split("/")
                    # Ignore this one!
                    ids.remove(str(row.id))
                    for id in ids:
                        if id not in tryagain:
                            tryagain.append(int(id))
                else:
                    # Try the Parent
                    parent = row.parent
                    if parent and parent not in tryagain:
                        tryagain.append(parent)

        return (output, tryagain)

    # -------------------------------------------------------------------------
    def update_table_hierarchy_labels(self, tablename=None):
        """
            Re-set table options that depend on location_hierarchy

            Only update tables which are already defined
        """

        T = current.T
        db = current.db

        levels = ["L1", "L2", "L3", "L4"]
        labels = self.get_location_hierarchy()

        if tablename and tablename in db:
            # Update the specific table which has just been defined
            table = db[tablename]
            if tablename == "gis_location":
                labels["L0"] = T("Country")
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
    def set_config(self, config_id=None, force_update_cache=False):
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

        session = current.session
        s3 = current.response.s3

        # If an id has been supplied, try it first. If it matches what's in
        # response, there's no work to do.
        if config_id and not force_update_cache and \
           s3.gis.config and \
           s3.gis.config.id == config_id:
            return

        db = current.db
        s3db = current.s3db

        ctable = s3db.gis_config
        mtable = s3db.gis_marker
        ptable = s3db.gis_projection
        stable = s3db.gis_symbology
        ltable = s3db.gis_layer_config

        cache = Storage()
        row = None
        if config_id:
            query = (ctable.id == config_id) & \
                    (mtable.id == stable.marker_id) & \
                    (stable.id == ctable.symbology_id) & \
                    (ptable.id == ctable.projection_id)
            row = db(query).select(limitby=(0, 1)).first()

        elif config_id is 0:
            # Use site default.
            config = db(ctable.uuid == "SITE_DEFAULT").select(limitby=(0, 1)).first()
            if not config:
                # No configs found at all
                s3.gis.config = cache
                return cache
            query = (ctable.id == config.id) & \
                    (mtable.id == stable.marker_id) & \
                    (stable.id == ctable.symbology_id) & \
                    (ptable.id == ctable.projection_id)
            row = db(query).select(limitby=(0, 1)).first()


        # If no id supplied, or the requested config does not exist,
        # fall back to personal or site config.
        if not row:
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
                append = pes.append
                for role in roles:
                    if role in role_paths:
                        # @ToDo: Read the person's gis_config to disambiguate which Path to use, if there are issues
                        pes = role_paths[role].nodes()
                        # Staff don't check Volunteer's OUs
                        break
                # Add Personal
                pes.insert(0, pe_id)
                query = (ctable.pe_id.belongs(pes)) | \
                        (ctable.uuid == "SITE_DEFAULT")
                # Personal may well not be complete, so Left Join
                left = [
                        ptable.on(ptable.id == ctable.projection_id),
                        stable.on(stable.id == ctable.symbology_id),
                        mtable.on(mtable.id == stable.marker_id),
                        ]
                # Order by pe_type (defined in gis_config)
                # @ToDo: Do this purely from the hierarchy
                rows = db(query).select(ctable.ALL,
                                        mtable.ALL,
                                        ptable.ALL,
                                        left=left,
                                        orderby=ctable.pe_type)
                cache["ids"] = []
                exclude = list(s3.all_meta_field_names)
                append = exclude.append
                for fieldname in ["delete_record", "update_record",
                                  "pe_path",
                                  "gis_layer_config", "gis_menu"]:
                    append(fieldname)
                for row in rows:
                    config = row["gis_config"]
                    if not config_id:
                        config_id = config.id
                    cache["ids"].append(config.id)
                    fields = filter(lambda key: key not in exclude,
                                    config)
                    for key in fields:
                        if key not in cache or cache[key] is None:
                            cache[key] = config[key]
                    if "epsg" not in cache or cache["epsg"] is None:
                        projection = row["gis_projection"]
                        for key in ["epsg", "units", "maxResolution", "maxExtent"]:
                            cache[key] = projection[key] if key in projection else None
                    if "image" not in cache or cache["image"] is None:
                        marker = row["gis_marker"]
                        for key in ["image", "height", "width"]:
                            cache["marker_%s" % key] = marker[key] if key in marker else None
                    if "base" not in cache:
                        # Default Base Layer?
                        query = (ltable.config_id == config.id) & \
                                (ltable.base == True) & \
                                (ltable.enabled == True)
                        base = db(query).select(ltable.layer_id,
                                                limitby=(0, 1)).first()
                        if base:
                            cache["base"] = base.layer_id
                # Add NULL values for any that aren't defined, to avoid KeyErrors
                for key in ["epsg", "units", "maxResolution", "maxExtent",
                            "marker_image", "marker_height", "marker_width",
                            "base"]:
                    if key not in cache:
                        cache[key] = None

        if not row:
            # No personal config or not logged in. Use site default.
            config = db(ctable.uuid == "SITE_DEFAULT").select(limitby=(0, 1)).first()
            if not config:
                # No configs found at all
                s3.gis.config = cache
                return cache
            query = (ctable.id == config.id) & \
                    (mtable.id == stable.marker_id) & \
                    (stable.id == ctable.symbology_id) & \
                    (ptable.id == ctable.projection_id)
            row = db(query).select(limitby=(0, 1)).first()

        if row and not cache:
            # We had a single row
            config = row["gis_config"]
            config_id = config.id
            cache["ids"] = [config_id]
            projection = row["gis_projection"]
            marker = row["gis_marker"]
            fields = filter(lambda key: key not in s3.all_meta_field_names,
                            config)
            for key in fields:
                cache[key] = config[key]
            for key in ["epsg", "units", "maxResolution", "maxExtent"]:
                cache[key] = projection[key] if key in projection else None
            for key in ["image", "height", "width"]:
                cache["marker_%s" % key] = marker[key] if key in marker else None
            # Default Base Layer?
            query = (ltable.config_id == config_id) & \
                    (ltable.base == True) & \
                    (ltable.enabled == True)
            base = db(query).select(ltable.layer_id,
                                    limitby=(0, 1)).first()
            if base:
                cache["base"] = base.layer_id
            else:
                cache["base"] = None

        # Store the values
        s3.gis.config = cache

        # Let caller know if their id was valid.
        return config_id if row else cache

    # -------------------------------------------------------------------------
    def get_config(self):
        """
            Returns the current GIS config structure.

            @ToDo: Config() class
        """

        gis = current.response.s3.gis

        if not gis.config:
            # Ask set_config to put the appropriate config in response.
            self.set_config()

        return gis.config

    # -------------------------------------------------------------------------
    @staticmethod
    def set_default_location(location, level=None):
        """
            Set the default location

            @param: location - either name or ID
            @param: level - useful to distinguish Names (ignored for IDs)
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

        try:
            # ID?
            id = int(location)
        except:
            # name
            query = (table.name == location)
            if level:
                query = query & (table.level == level)
            _location = db(query).select(table.id,
                                         limitby=(0, 1)).first()
            if _location:
                id = _location.id
            else:
                s3_debug("S3GIS: Location cannot be set as defaut", location)
                return

        table = s3db.gis_config
        query = (table.uuid == "SITE_DEFAULT")
        db(query).update(default_location_id=id)

    # -------------------------------------------------------------------------
    def get_location_hierarchy(self, level=None, location=None):
        """
            Returns the location hierarchy and it's labels

            @param: level - a specific level for which to lookup the label
                            (this use is to be discouraged, especially for the early runs as the result won't be cached)
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
                return _levels[level]
            else:
                return _levels

        T = current.T
        COUNTRY = str(T("Country"))

        if level == "L0":
            return COUNTRY

        db = current.db
        s3db = current.s3db

        table = s3db.gis_hierarchy

        if level:
            fields = [table.uuid,
                      table[level]]
        else:
            fields = [table.uuid,
                      table.L1,
                      table.L2,
                      table.L3,
                      table.L4,
                      table.L5]

        query = (table.uuid == "SITE_DEFAULT")
        if not location:
            config = self.get_config()
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
            return levels

    # -------------------------------------------------------------------------
    def get_strict_hierarchy(self, location=None):
        """
            Returns the strict hierarchy value from the current config.

            @param: location - the location_id of the record to check
        """

        db = current.db
        s3db = current.s3db

        table = s3db.gis_hierarchy

        # Read the system default
        # @ToDo: Check for an active gis_config region?
        query = (table.uuid == "SITE_DEFAULT")
        if location:
            # Try the Location's Country, but ensure we have the fallback available in a single query
            query = query | (table.location_id == self.get_parent_country(location))
        rows = db(query).select(table.uuid,
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

        T = current.T
        all_levels = OrderedDict()
        all_levels.update(self.get_location_hierarchy())
        all_levels["GR"] = T("Location Group")
        #all_levels["XX"] = T("Imported")

        if level:
            try:
                return all_levels[level]
            except Exception, exception:

                return level
        else:
            return all_levels

    # -------------------------------------------------------------------------
    # @ToDo: There is nothing stopping someone from making extra configs that
    # have country locations as their region location. Need to select here
    # only those configs that belong to the hierarchy. If the L0 configs are
    # created during initial db creation, then we can tell which they are
    # either by recording the max id for an L0 config, or by taking the config
    # with lowest id if there are more than one per country. This same issue
    # applies to any other use of country configs that relies on getting the
    # official set (e.g. looking up hierarchy labels).
    def get_edit_level(self, level, id):
        """
            Returns the edit_<level> value from the parent country hierarchy.

            Used by gis_location_onvalidation()

            @param id: the id of the location or an ancestor - used to find
                       the ancestor country location.
        """

        country = self.get_parent_country(id)

        db = current.db
        s3db = current.s3db

        table = s3db.gis_hierarchy

        fieldname = "edit_%s" % level

        # Read the system default
        query = (table.uuid == "SITE_DEFAULT")
        if country:
            # Try the Location's Country, but ensure we have the fallback available in a single query
            query = query | (table.location_id == country)
        rows = db(query).select(table[fieldname],
                                cache=s3db.cache)
        if len(rows) > 1:
            # Remove the Site Default
            filter = lambda row: row.uuid == "SITE_DEFAULT"
            rows.exclude(filter)
        row = rows.first()
        edit = row[fieldname]

        return edit

    # -------------------------------------------------------------------------
    def get_countries(self, key_type="id"):
        """
            Returns country code or L0 location id versus name for all countries.

            If key_type is "code", these are returned as an OrderedDict with
            country code as the key.  If key_type is "id", then the location id
            is the key.  In all cases, the value is the name.
        """

        settings = current.deployment_settings

        cached = False
        if settings.countries:
            # This may have been changed since the initial config
            cached = False
        elif self.countries:
            cached = True

        if not cached:
            db = current.db
            _location = "gis_location" in db and db.gis_location
            if not _location:
                # Called before gis_location is in db
                return None

            query = (_location.level == "L0")
            _countries = settings.get_gis_countries()
            if _countries:
                query = query & (_location.code.belongs(_countries))
            countries = db(query).select(_location.id,
                                         _location.code,
                                         _location.name,
                                         orderby=_location.name)
            if not countries:
                return []

            countries_by_id = OrderedDict()
            countries_by_code = OrderedDict()
            for row in countries:
                countries_by_id[row.id] = row.name
                countries_by_code[row.code] = row.name

            # Don't expose these while they're being built. Set countries last
            # so it can be used to tell when all exist.
            self.countries_by_id = countries_by_id
            self.countries_by_code = countries_by_code
            self.countries = countries

        if key_type == "id":
            return self.countries_by_id
        else:
            return self.countries_by_code

    # -------------------------------------------------------------------------
    def get_country(self, key, key_type="id"):
        """
            Returns country name for given code or id from L0 locations.

            The key can be either location id or country code, as specified
            by key_type.
        """

        if key:
            if self.countries or self.get_countries(key_type):
                if key_type == "id":
                    return self.countries_by_id[key]
                else:
                    return self.countries_by_code[key]

        return None

    # -------------------------------------------------------------------------
    def get_parent_country(self, location, key_type="id"):
        """
            Returns the parent country for a given record

            @param: location: the location or id to search for
            @param: key_type: whether to return an id or code
        """

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location

        try:
            # location is passed as integer (location_id)
            query = (table.id == location)
            location = db(query).select(table.id,
                                        table.path,
                                        table.code,
                                        table.level,
                                        limitby=(0, 1),
                                        cache=cache).first()
        except:
            # location is passed as record
            pass

        if location.level == "L0":
            if key_type == "id":
                return location.id
            elif key_type == "code":
                return location.code
        else:
            parents = self.get_parents(location.id, feature=location)
            if parents:
                for row in parents:
                    if row.level == "L0":
                        if key_type == "id":
                            return row.id
                        elif key_type == "code":
                            return row.code

        return None


    # -------------------------------------------------------------------------
    def get_default_country(self, key_type="id"):
        """
            Returns the default country for the active gis_config

            @param: key_type: whether to return an id or code
        """

        config = self.get_config()

        if config.default_location_id:
            return self.get_parent_country(config.default_location_id)

        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def get_representation(field,
                           value):
        """
            Return a quick representation for a Field based on it's value
            - faster than field.represent(value)
            Used by get_popup_tooltip()

            @ToDo: Move out of S3GIS
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        cache = current.cache
        fieldname = field.name
        tablename = field.tablename

        # Fallback representation is the value itself
        represent = value

        # If the field is an integer lookup then returning that isn't much help
        if fieldname == "type":
            if tablename == "hrm_human_resource":
                represent = cache.ram("hrm_type_%s" % value,
                                      lambda: s3db.hrm_type_opts.get(value, ""),
                                      time_expire=60)
            elif tablename == "org_office":
                represent = cache.ram("office_type_%s" % value,
                                      lambda: s3db.org_office_type_opts.get(value, ""),
                                      time_expire=60)
        elif field.type[:9] == "reference":
                tablename = field.type[10:]
                if tablename == "pr_person":
                    # Unlikely to be the same person in multiple popups so no value to caching
                    represent = s3_fullname(value)
                else:
                    table = s3db[tablename]
                    if "name" in table.fields:
                        # Simple Name lookup faster than full represent
                        represent = cache.ram("%s_%s_%s" % (tablename, fieldname, value),
                                              lambda: db(table.id == value).select(table.name,
                                                                                   limitby=(0, 1)).first().name,
                                              time_expire=60)
                    else:
                        # Do the normal represent
                        represent = cache.ram("%s_%s_%s" % (tablename, fieldname, value),
                                              lambda: field.represent(value),
                                              time_expire=60)
        elif field.type.startswith("list"):
            # Do the normal represent
            represent = cache.ram("%s_%s_%s" % (tablename, fieldname, value),
                                  lambda: field.represent(value),
                                  time_expire=60)

        return represent

    # -------------------------------------------------------------------------
    def get_features_in_polygon(self, location, tablename=None, category=None):
        """
            Returns a gluon.sql.Rows of Features within a Polygon.
            The Polygon can be either a WKT string or the ID of a record in the
            gis_location table
        """

        db = current.db
        s3db = current.s3db
        session = current.session
        T = current.T
        locations = db.gis_location

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
            query = query & (table.deleted == False)
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
                wkt = row.gis_location.wkt
                if wkt is None:
                    lat = row.gis_location.lat
                    lon = row.gis_location.lon
                    if lat is not None and lon is not None:
                        wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        continue
                try:
                    shape = wkt_loads(wkt)
                    if shape.intersects(polygon):
                        # Save Record
                        output.records.append(row)
                except shapely.geos.ReadingError:
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
                wkt = row.gis_location.wkt
                if wkt is None:
                    lat = row.gis_location.lat
                    lon = row.gis_location.lon
                    if lat is not None and lon is not None:
                        wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        continue
                try:
                    shape = wkt_loads(wkt)
                    if shape.intersects(polygon):
                        # Save Record
                        output.records.append(row)
                except shapely.geos.ReadingError:
                    s3_debug(
                        "Error reading wkt of location with id",
                        value = row.id,
                    )

        return output

    # -------------------------------------------------------------------------
    def get_features_in_radius(self, lat, lon, radius, tablename=None, category=None):
        """
            Returns Features within a Radius (in km) of a LatLon Location
        """

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
                query = query & (table.location_id == locations.id)
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

            @param feature_id: the feature ID (int) or UUID (str)
            @param filter: Filter out results based on deployment_settings
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

        if isinstance(feature_id, int):
            query = (table.id == feature_id)
        elif isinstance(feature_id, str):
            query = (table.uuid == feature_id)
        else:
            # Bail out
            return None

        feature = db(query).select(table.id,
                                   table.lat,
                                   table.lon,
                                   limitby=(0, 1)).first()

        #query = (table.deleted == False)
        #settings = current.deployment_settings
        #if filter and not settings.get_gis_display_l0():
            # @ToDo: This query looks wrong. Does it intend to exclude both
            # L0 and no level? Because it's actually a no-op. If location is
            # L0 then first term is false, but there is a level so the 2nd
            # term is also false, so the combination is false, same as the
            # 1st term alone. If the level isn't L0, the first term is true,
            # so the 2nd is irrelevant and probably isn't even evaluated, so
            # the combination is same as the 1st term alone.
            # @ToDo And besides, it the L0 lon, lat is all we have, isn't it
            # better to use that than nothing?
            #query = query & ((table.level != "L0") | (table.level == None))

        # Zero is an allowed value, hence explicit test for None.
        if "lon" in feature and "lat" in feature and \
           (feature.lat is not None) and (feature.lon is not None):
            return dict(lon=feature.lon, lat=feature.lat)

        else:
            # Step through ancestors to first with lon, lat.
            parents = self.get_parents(feature.id)
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
    def get_marker():
        """
            Returns the default Marker
            - called by S3XML.gis_encode()
        """

        return Marker().as_dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def get_marker_and_popup(layer_id=None, # Used by S3REST: S3Resource.export_tree()
                             marker=None,   # Used by S3REST: S3Resource.export_tree()
                             tablename=None,  # Used by S3Search: search_interactive()
                             record=None      # Used by S3Search: search_interactive()
                            ):
        """
            Returns the marker, popup_fields and popup_label for a Map Layer

            Used by S3REST: S3Resource.export_tree():
            @param: layer_id - db.gis_layer_feature.id
            @param: marker - a default marker image (what would provide this?)

            Used by S3Search: search_interactive():
            @param: tablename - the tablename for a resource
            @param: record - the record for a resource
        """

        db = current.db
        s3db = current.s3db

        table = s3db.gis_layer_feature
        ltable = s3db.gis_layer_symbology
        mtable = s3db.gis_marker

        try:
            symbology_id = current.response.s3.gis.config.symbology_id
        except:
            # Config not initialised yet
            config = current.gis.get_config()
            symbology_id = config.symbology_id

        if layer_id:
            # Feature Layer called by S3REST: S3Resource.export_tree()
            query = (table.id == layer_id) & \
                    (table.layer_id == ltable.layer_id) & \
                    (ltable.marker_id == mtable.id) & \
                    (ltable.symbology_id == symbology_id)
            layer = db(query).select(mtable.image,
                                     ltable.gps_marker,
                                     table.popup_label,
                                     table.popup_fields,
                                     limitby=(0, 1)).first()

            if layer:
                marker = layer.gis_marker.image
                gps_marker = layer.gis_layer_symbology.gps_marker
                frow = layer.gis_layer_feature
                popup_label = frow.popup_label
                popup_fields = frow.popup_fields
            else:
                gps_marker = None
                popup_label = ""
                popup_fields = "name"

            return dict(marker = marker,
                        gps_marker = gps_marker,
                        popup_label = popup_label,
                        popup_fields = popup_fields,
                        )

        elif tablename:
            # Search results called by S3Search: search_interactive()
            def get_layers(tablename):
                (module, resourcename) = tablename.split("_", 1)
                query = (table.module == module) & \
                        (table.resource == resourcename) & \
                        (table.layer_id == ltable.layer_id)

                left = [
                        mtable.on((ltable.marker_id == mtable.id) & \
                                  (ltable.symbology_id == symbology_id))
                        ]

                layers = db(query).select(mtable.image,
                                          mtable.height,
                                          mtable.width,
                                          #ltable.gps_marker,
                                          table.filter_field,
                                          table.filter_value,
                                          table.popup_label,
                                          table.popup_fields,
                                          left=left)
                return layers

            layers = current.cache.ram("%s_marker" % tablename,
                                       lambda: get_layers(tablename),
                                       time_expire=60)
            if not record and len(layers) > 1:
                # We can't provide details for the whole table, but need to do a per-record check
                return None
            for row in layers:
                frow = row.gis_layer_feature
                if not record or not frow.filter_field:
                    # We only have 1 row
                    marker = row.gis_marker
                    if not marker.image:
                        # Use Default Marker
                        marker = Marker().as_dict()
                    return dict(marker = marker,
                                #gps_marker = row.gis_layer_symbology.gps_marker,
                                popup_label = frow.popup_label,
                                popup_fields = frow.popup_fields,
                                )
                # Check if the record matches the filter
                if str(record[frow.filter_field]) == frow.filter_value:
                    marker = row.gis_marker
                    if not marker.image:
                        # Use Default Marker
                        marker = Marker().as_dict()
                    return dict(marker = marker,
                                #gps_marker = row.gis_layer_symbology.gps_marker,
                                popup_label = frow.popup_label,
                                popup_fields = frow.popup_fields,
                                )
            # No Feature Layer defined or
            # Row doesn't match any of the filters
            # Default Marker
            marker = Marker().as_dict()
            return dict(marker = marker,
                        #gps_marker = row.gis_layer_symbology.gps_marker,
                        popup_label = tablename or "",
                        popup_fields = None,
                        )

        else:
            s3_debug("gis.get_marker_and_popup", "Invalid arguments")
            return None

    # -------------------------------------------------------------------------
    def get_popup_tooltip(self, table, record, popup_label, popup_fields):
        """
            Returns the HTML popup_tooltip for a Map feature

            Used by S3XML.gis_encode()
            Used by S3Search: search_interactive()

            @param: table
            @param: record
            @param: popup_label
            @param: popup_fields
        """

        if popup_label:
            tooltip = "(%s)" % current.T(popup_label)
        else:
            tooltip = ""

        if popup_fields:
            popup_fields = popup_fields.split("/")
            fieldname = popup_fields[0]
            try:
                value = record[fieldname]
                if value:
                    field = table[fieldname]
                    represent = self.get_representation(field, value)
                    tooltip = "%s %s" % (represent, tooltip)
            except:
                # This field isn't in the table
                pass
        else:
            popup_fields = []

        for fieldname in popup_fields:
            try:
                if fieldname != popup_fields[0]:
                    value = record[fieldname]
                    if value:
                        field = table[fieldname]
                        represent = self.get_representation(field, value)
                        tooltip = "%s<br />%s" % (tooltip, represent)
            except:
                # This field isn't in the table
                pass

        return tooltip

    # -------------------------------------------------------------------------
    @staticmethod
    def greatCircleDistance(lat1, lon1, lat2, lon2, quick=True):
        """
            Calculate the shortest distance (in km) over the earth's sphere between 2 points
            Formulae from: http://www.movable-type.co.uk/scripts/latlong.html
            (NB We should normally use PostGIS functions, where possible, instead of this query)
        """

        # shortcuts
        cos = math.cos
        sin = math.sin
        radians = math.radians

        if quick:
            # Spherical Law of Cosines (accurate down to around 1m & computationally quick)
            acos = math.acos
            lat1 = radians(lat1)
            lat2 = radians(lat2)
            lon1 = radians(lon1)
            lon2 = radians(lon2)
            distance = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2-lon1)) * RADIUS_EARTH
            return distance

        else:
            # Haversine
            #asin = math.asin
            atan2 = math.atan2
            sqrt = math.sqrt
            pow = math.pow
            dLat = radians(lat2-lat1)
            dLon = radians(lon2-lon1)
            a = pow(sin(dLat / 2), 2) + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(dLon / 2), 2)
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            #c = 2 * asin(sqrt(a))              # Alternate version
            # Convert radians to kilometers
            distance = RADIUS_EARTH * c
            return distance

    # -------------------------------------------------------------------------
    def import_admin_areas(self,
                           source="gadm",
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

        if source != "gadm":
            s3_debug("Only GADM is currently supported")
            return

        try:
            from osgeo import ogr
        except:
            s3_debug("Unable to import ogr. Please install python-gdal bindings: GDAL-1.8.1+")
            return

        if "L0" in levels:
            self.import_gadm_L0(ogr, countries=countries)
        if "L1" in levels:
            self.import_gadm(ogr, "L1", countries=countries)
        if "L2" in levels:
            self.import_gadm(ogr, "L2", countries=countries)

        s3_debug("All done!")

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def import_gadm_L0(ogr, countries=[]):
        """
           Import L0 Admin Boundaries into the Locations table from GADM
           - designed to be called from import_admin_areas()
           - assumes that basic prepop has been done, so that no new records need to be created

           @param ogr - The OGR Python module
           @param countries - List of ISO2 countrycodes to download data for
                              defaults to all countries
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

        layer = {
            "url" : "http://gadm.org/data/gadm_v1_lev0_shp.zip",
            "zipfile" : "gadm_v1_lev0_shp.zip",
            "shapefile" : "gadm1_lev0",
            "codefield" : "ISO2", # This field is used to uniquely identify the L0 for updates
            "code2field" : "ISO"  # This field is used to uniquely identify the L0 for parenting the L1s
        }

        # Copy the current working directory to revert back to later
        old_working_directory = os.getcwd()

        # Create the working directory
        if os.path.exists(os.path.join(os.getcwd(), "temp")): # use web2py/temp/GADMv1 as a cache
            TEMP = os.path.join(os.getcwd(), "temp")
        else:
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os.path.join(TEMP, "GADMv1")
        try:
            os.mkdir(tempPath)
        except OSError:
            # Folder already exists - reuse
            pass

        # Set the current working directory
        os.chdir(tempPath)

        layerName = layer["shapefile"]

        # Check if file has already been downloaded
        fileName = layer["zipfile"]
        if not os.path.isfile(fileName):
            # Download the file
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
        ds = ogr.Open( "%s.shp" % layerName )
        if ds is None:
            s3_debug("Open failed.\n")
            return

        lyr = ds.GetLayerByName( layerName )

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
                    query = (table.code == code)
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
                        db(query).update(gis_feature_type=gis_feature_type,
                                         wkt=wkt,
                                         code2=code2,
                                         area=area)
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
    def import_gadm(self, ogr, level="L1", countries=[]):
        """
            Import L1 Admin Boundaries into the Locations table from GADM
            - designed to be called from import_admin_areas()
            - assumes a fresh database with just Countries imported

            @param ogr - The OGR Python module
            @param level - "L1" or "L2"
            @param countries - List of ISO2 countrycodes to download data for
                               defaults to all countries
        """

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location

        if level == "L1":
            layer = {
                "url" : "http://gadm.org/data/gadm_v1_lev1_shp.zip",
                "zipfile" : "gadm_v1_lev1_shp.zip",
                "shapefile" : "gadm1_lev1",
                "namefield" : "NAME_1",
                "codefield" : "ID_1",   # This field is used to uniquely identify the L1 for updates
                "code2field" : "ISO",   # This field is used to uniquely identify the L0 for parenting the L1s
                "parent" : "L0",
                "parentCode" : "code2"
            }
        elif level == "L2":
            layer = {
                "url" : "http://biogeo.ucdavis.edu/data/gadm/gadm_v1_lev2_shp.zip",
                "zipfile" : "gadm_v1_lev2_shp.zip",
                "shapefile" : "gadm_v1_lev2",
                "namefield" : "NAME_2",
                "codefield" : "ID_2",    # This field is used to uniquely identify the L2 for updates
                "code2field" : "ID_1",   # This field is used to uniquely identify the L1 for parenting the L2s
                "parent" : "L1",
                "parentCode" : "code"
            }
        else:
            s3_debug("Level %s not supported!" % level)
            return


        import shutil
        import csv
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
        old_working_directory = os.getcwd()

        # Create the working directory
        if os.path.exists(os.path.join(os.getcwd(), "temp")): # use web2py/temp/GADMv1 as a cache
            TEMP = os.path.join(os.getcwd(), "temp")
        else:
            import tempfile
            TEMP = tempfile.gettempdir()
        tempPath = os.path.join(TEMP, "GADMv1")
        try:
            os.mkdir(tempPath)
        except OSError:
            # Folder already exists - reuse
            pass

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
            url = layer["url"]
            s3_debug("Downloading %s" % url)
            try:
                file = fetch(url)
            except urllib2.URLError, exception:
                s3_debug(exception)
                # Revert back to the working directory as before.
                os.chdir(old_working_directory)
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
        inputDS = ogr.Open( inputFileName, False )
        outputFileName = "CSV"
        outputDriver = ogr.GetDriverByName("CSV")
        outputDS = outputDriver.CreateDataSource( outputFileName, options = [] )
        # GADM only has 1 layer/source
        inputLayer = inputDS.GetLayer(0)
        inputFDefn = inputLayer.GetLayerDefn()
        # Create the output Layer
        outputLayer = outputDS.CreateLayer( layerName )
        # Copy all Fields
        papszFieldTypesToString = []
        inputFieldCount = inputFDefn.GetFieldCount()
        panMap = [ -1 for i in range(inputFieldCount) ]
        outputFDefn = outputLayer.GetLayerDefn()
        nDstFieldCount = 0
        if outputFDefn is not None:
            nDstFieldCount = outputFDefn.GetFieldCount()
        for iField in range(inputFieldCount):
            inputFieldDefn = inputFDefn.GetFieldDefn(iField)
            oFieldDefn = ogr.FieldDefn( inputFieldDefn.GetNameRef(),
                                        inputFieldDefn.GetType() )
            oFieldDefn.SetWidth( inputFieldDefn.GetWidth() )
            oFieldDefn.SetPrecision( inputFieldDefn.GetPrecision() )

            # The field may have been already created at layer creation
            iDstField = -1;
            if outputFDefn is not None:
                 iDstField = outputFDefn.GetFieldIndex(oFieldDefn.GetNameRef())
            if iDstField >= 0:
                panMap[iField] = iDstField
            elif outputLayer.CreateField( oFieldDefn ) == 0:
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

                poDstFeature = ogr.Feature( outputLayer.GetLayerDefn() )

                if poDstFeature.SetFromWithMap( poFeature, 1, panMap ) != 0:

                    if nGroupTransactions > 0:
                        outputLayer.CommitTransaction()

                    s3_debug("Unable to translate feature %d from layer %s" % (poFeature.GetFID() , inputFDefn.GetName() ))
                    # Revert back to the working directory as before.
                    os.chdir(old_working_directory)
                    return

                poDstGeometry = poDstFeature.GetGeometryRef()
                if poDstGeometry is not None:

                    if nParts > 0:
                        # For -explodecollections, extract the iPart(th) of the geometry
                        poPart = poDstGeometry.GetGeometryRef(iPart).Clone()
                        poDstFeature.SetGeometryDirectly(poPart)
                        poDstGeometry = poPart

                if outputLayer.CreateFeature( poDstFeature ) != 0 and not bSkipFailures:
                    if nGroupTransactions > 0:
                        outputLayer.RollbackTransaction()
                    # Revert back to the working directory as before.
                    os.chdir(old_working_directory)
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
        ds = ogr.Open( "%s.shp" % layerName )
        if ds is None:
            s3_debug("Open failed.\n")
            # Revert back to the working directory as before.
            os.chdir(old_working_directory)
            return

        lyr = ds.GetLayerByName( layerName )

        lyr.ResetReading()

        # Use CSV for Name
        s3_debug("Opening %s.csv" % layerName)
        rows = latin_dict_reader(open("%s.csv" % layerName))

        nameField = layer["namefield"]
        codeField = layer["codefield"]
        code2Field = layer["code2field"]
        parentLevel = layer["parent"]
        parentCodeField = table[layer["parentCode"]]
        count = 0
        for row in rows:
            # Read Attributes
            feat = lyr[count]

            code2 = feat.GetField(code2Field)
            query = (table.level == parentLevel) & \
                    (parentCodeField == code2)
            parent = db(query).select(table.id,
                                      table.code,
                                      limitby=(0, 1),
                                      cache=cache).first()
            if not parent:
                # Skip locations for which we don't have a valid parent
                #s3_debug("Skipping - cannot find parent with code2: %s" % code2)
                count += 1
                continue

            if countries:
                # Skip the countries which we're not interested in
                if level == "L1":
                    if parent.code not in countries:
                        #s3_debug("Skipping %s as not in countries list" % parent.code)
                        count += 1
                        continue
                else:
                    # Check grandparent
                    country = self.get_parent_country(parent.id, key_type="code")
                    if country not in countries:
                        count += 1
                        continue

            # This is got from CSV in order to be able to handle the encoding
            name = row.pop(nameField)
            name.encode("utf8")

            code = feat.GetField(codeField)
            area = feat.GetField("Shape_Area")

            geom = feat.GetGeometryRef()
            if geom is not None:
                if geom.GetGeometryType() == ogr.wkbPoint:
                    lat = geom.GetX()
                    lon = geom.GetY()
                    table.insert(name=name,
                                 level=level,
                                 gis_feature_type=1,
                                 lat=lat,
                                 lon=lon,
                                 parent=parent.id,
                                 code=code,
                                 area=area)
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
                    table.insert(name=name,
                                 level=level,
                                 gis_feature_type=gis_feature_type,
                                 wkt=wkt,
                                 parent=parent.id,
                                 code=code,
                                 area=area)
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
            # If doing all L2s, it can break memory limits - how can we avoid this?
            s3_debug("Memory error when trying to update_location_tree()!")

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

        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        request = current.request
        settings = current.deployment_settings
        table = s3db.gis_location

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
                # @ToDo: Agree on a global repository for UUIDs:
                # http://eden.sahanafoundation.org/wiki/UserGuidelinesGISData#UUIDs
                import uuid
                uuid = "geo.sahanafoundation.org/" + uuid.uuid4()

                # Add WKT
                lat = float(lat)
                lon = float(lon)
                wkt = self.latlon_to_wkt(lat, lon)

                shape = shapely.geometry.point.Point(lon, lat)

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
                    except shapely.geos.ReadingError:
                        s3_debug("Error reading wkt of location with id", row.id)

                # Add entry to database
                table.insert(uuid=uuid,
                             geonames_id=geonames_id,
                             source="geonames",
                             name=name,
                             level=level,
                             parent=parent,
                             lat=lat,
                             lon=lon,
                             wkt=wkt,
                             lon_min=lon_min,
                             lon_max=lon_max,
                             lat_min=lat_min,
                             lat_max=lat_max)

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
    def layer_subtypes(layer="google"):
        """ Return a lit of the subtypes available for a Layer """

        if layer == "google":
            return ["Satellite", "Maps", "Hybrid", "Terrain", "MapMaker",
                    "MapMakerHybrid"]
        elif layer == "yahoo":
            return ["Satellite", "Maps", "Hybrid"]
        elif layer == "bing":
            return ["Satellite", "Maps", "Hybrid"]
        else:
            return None


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
            if SHAPELY:
                shape = shapely.wkt.loads(wkt)
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
    def update_location_tree(self, location_id=None, parent_id=None):
        """
            Update the Tree for GIS Locations:
            @author: Aravind Venkatesan and Ajay Kumar Sreenivasan from NCSU
            @summary: Using Materialized path for each node in the tree
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
            Do a lazy update of a database that does not have location paths.
            For convenience of get_parents, return the path.
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

        if location_id:
            if parent_id:
                query = (table.id == parent_id)
                parent = db(query).select(table.parent,
                                          table.path).first()
            # It is Somebody Else's Problem (see Douglas Adams) to assure that
            # parent_id points to an actual location.  We just protect ourselves
            # in case they didn't.
            if parent_id and parent:
                if parent.path:
                    # Parent has a path.
                    path = "%s/%s" % (str(parent.path), str(location_id))
                elif parent.parent:
                    parent_path = self.update_location_tree(parent_id,
                                                            parent.parent)
                    # Ok, *now* the parent has a path.
                    path = "%s/%s" % (str(parent_path), str(location_id))
                else:
                    # Parent has no parent.
                    path = "%s/%s" % (str(parent_id), str(location_id))
            else:
                path = str(location_id)

            db(table.id == location_id).update(path=path)

            return path

        else:
            # Do the whole database
            query = (table.id > 0)
            features = db(query).select(table.id,
                                        table.gis_feature_type,
                                        table.lat,
                                        table.lon,
                                        table.wkt,
                                        table.parent)
            for feature in features:
                self.update_location_tree(feature.id, feature.parent)
                # Also do the Bounds/Centroids/WKT
                form = Storage()
                form.vars = feature
                form.errors = Storage()
                self.wkt_centroid(form)
                _vars = form.vars
                if "lat_max" in _vars:
                    db(table.id == feature.id).update(gis_feature_type = _vars.gis_feature_type,
                                                      lat = _vars.lat,
                                                      lon = _vars.lon,
                                                      wkt = _vars.wkt,
                                                      lat_max = _vars.lat_max,
                                                      lat_min = _vars.lat_min,
                                                      lon_min = _vars.lon_min,
                                                      lon_max = _vars.lon_max)

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

        if vars.wkt:
            # Parse WKT for LineString, Polygon, etc
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
                vars.lon_min = vars.lon_max = vars.lon
                vars.lat_min = vars.lat_max = vars.lat

        if vars.wkt and current.deployment_settings.get_gis_spatialdb():
            # Also populate the spatial field
            vars.the_geom = vars.wkt

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def query_features_by_bbox(lon_min, lat_min, lon_max, lat_max):
        """
            Returns a query of all Locations inside the given bounding box
        """
        s3db = current.s3db
        table = s3db.gis_location
        query = (table.lat_min <= lat_max) & \
                (table.lat_max >= lat_min) & \
                (table.lon_min <= lon_max) & \
                (table.lon_max >= lon_min)
        return query

    # -------------------------------------------------------------------------
    def get_features_by_bbox(self, lon_min, lat_min, lon_max, lat_max):
        """
            Returns Rows of Locations whose shape intersects the given bbox.
        """
        db = current.db
        return db(self.query_features_by_bbox(lon_min,
                                              lat_min,
                                              lon_max,
                                              lat_max)).select()

    # -------------------------------------------------------------------------
    def _get_features_by_shape(self, shape):
        """
            Returns Rows of locations which intersect the given shape.

            Relies on Shapely for wkt parsing and intersection.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        db = current.db
        s3db = current.s3db
        table = s3db.gis_location
        in_bbox = self.query_features_by_bbox(*shape.bounds)
        has_wkt = (table.wkt != None) & (table.wkt != "")

        for loc in db(in_bbox & has_wkt).select():
            try:
                location_shape = wkt_loads(loc.wkt)
                if location_shape.intersects(shape):
                    yield loc
            except shapely.geos.ReadingError:
                s3_debug("Error reading wkt of location with id", loc.id)

    # -------------------------------------------------------------------------
    def _get_features_by_latlon(self, lat, lon):
        """
            Returns a generator of locations whose shape intersects the given LatLon.

            Relies on Shapely.
            @todo: provide an option to use PostGIS/Spatialite
        """

        point = shapely.geometry.point.Point(lon, lat)
        return self._get_features_by_shape(point)

    # -------------------------------------------------------------------------
    def _get_features_by_feature(self, feature):
        """
            Returns all Locations whose geometry intersects the given feature.

            Relies on Shapely.
            @ToDo: provide an option to use PostGIS/Spatialite
        """
        shape = wkt_loads(feature.wkt)
        return self.get_features_by_shape(shape)

    # -------------------------------------------------------------------------
    if SHAPELY:
        get_features_by_shape = _get_features_by_shape
        get_features_by_latlon = _get_features_by_latlon
        get_features_by_feature = _get_features_by_feature

    # -------------------------------------------------------------------------
    @staticmethod
    def set_all_bounds():
        """
            Sets bounds for all locations without them.

            If shapely is present, and a location has wkt, bounds of the geometry
            are used.  Otherwise, the (lat, lon) are used as bounds.
        """
        db = current.db
        s3db = current.s3db
        table = s3db.gis_location

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
                table[location.id] = dict(
                                        lon_min = bounds[0],
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
    def simplify(wkt, tolerance=0.001, preserve_topology=True, output="wkt"):
        """
            Simplify a complex Polygon
            - NB This uses Python, better performance will be gaiend by doing
                 this direct from the database if you are using PostGIS:
            ST_Simplify() is available as
            db(query).select(table.the_geom.st_simplify(tolerance).st_astext().with_alias('wkt')).first().wkt
            db(query).select(table.the_geom.st_simplify(tolerance).st_asgeojson().with_alias('geojson')).first().geojson

            @ToDo: Reduce the number of decimal points to 4
                   - requires patching modules/geojson?
        """

        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            s3_debug("S3GIS", "Upgrade Shapely for Performance enhancements")

        shape = wkt_loads(wkt)
        simplified = shape.simplify(tolerance, preserve_topology)
        if output == "wkt":
            output = simplified.to_wkt()
        elif output == "geojson":
            from ..geojson import dumps
            # Compact Encoding
            output = dumps(simplified, separators=(",", ":"))

        return output

    # -------------------------------------------------------------------------
    def show_map( self,
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
                  features = [],
                  feature_queries = [],
                  wms_browser = {},
                  catalogue_layers = False,
                  legend = False,
                  toolbar = False,
                  search = False,
                  googleEarth = False,
                  googleStreetview = False,
                  mouse_position = "normal",
                  print_tool = {},
                  mgrs = {},
                  window = False,
                  window_hide = False,
                  closable = True,
                  maximizable = True,
                  collapsed = False,
                  location_selector = False,
                  plugins = None,
                ):
        """
            Returns the HTML to display a map

            Normally called in the controller as: map = gis.show_map()
            In the view, put: {{=XML(map)}}

            @param height: Height of viewport (if not provided then the default deployment setting is used)
            @param width: Width of viewport (if not provided then the default deployment setting is used)
            @param bbox: default Bounding Box of viewport (if not provided then the Lat/Lon/Zoom are used) (Dict):
                {
                "max_lat" : float,
                "max_lon" : float,
                "min_lat" : float,
                "min_lon" : float
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
                [{
                    lat: lat,
                    lon: lon
                }]
            @param feature_queries: Feature Queries to overlay onto the map & their options (List of Dicts):
                [{
                 name   : "MyLabel",    # A string: the label for the layer
                 query  : query,        # A gluon.sql.Rows of gis_locations, which can be from a simple query or a Join.
                                        # Extra fields can be added for 'popup_url', 'popup_label' & either
                                        # 'marker' (url/height/width) or 'shape' (with optional 'colour' & 'size')
                 active : True,         # Is the feed displayed upon load or needs ticking to load afterwards?
                 marker : None          # Optional: A per-Layer marker query or marker_id for the icon used to display the feature
                 opacity : 1            # Optional
                 cluster_distance       # Optional
                 cluster_threshold      # Optional
                }]
            @param wms_browser: WMS Server's GetCapabilities & options (dict)
                {
                name: string,           # Name for the Folder in LayerTree
                url: string             # URL of GetCapabilities
                }
            @param catalogue_layers: Show all the enabled Layers from the GIS Catalogue
                                     Defaults to False: Just show the default Base layer
            @param legend: Show the Legend panel
            @param toolbar: Show the Icon Toolbar of Controls
            @param search: Show the Geonames search box
            @param googleEarth: Include a Google Earth Panel
            @param googleStreetview: Include the ability to click to open up StreetView in a popup at that location
            @param mouse_position: Show the current coordinates in the bottom-right of the map. 3 Options: 'normal' (default), 'mgrs' (MGRS), False (off)
            @param print_tool: Show a print utility (NB This requires server-side support: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting)
                {
                url: string,            # URL of print service (e.g. http://localhost:8080/geoserver/pdf/)
                mapTitle: string        # Title for the Printed Map (optional)
                subTitle: string        # subTitle for the Printed Map (optional)
                }
            @param mgrs: Use the MGRS Control to select PDFs
                {
                name: string,           # Name for the Control
                url: string             # URL of PDF server
                }
                @ToDo: Also add MGRS Search support: http://gxp.opengeo.org/master/examples/mgrs.html
            @param window: Have viewport pop out of page into a resizable window
            @param window_hide: Have the window hidden by default, ready to appear (e.g. on clicking a button)
            @param closable: In Window mode, whether the window is closable or not
            @param collapsed: Start the Tools panel (West region) collapsed
            @param location_selector: This Map is being instantiated within the LocationSelectorWidget
            @param plugins: an iterable of objects which support the following methods:
                            .addToMapWindow(items)
                            .setup(map)

        """

        request = current.request
        response = current.response
        if not response.warning:
            response.warning = ""
        session = current.session
        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth
        cache = s3db.cache
        settings = current.deployment_settings
        public_url = settings.get_base_public_url()

        cachetable = s3db.gis_cache
        MAP_ADMIN = auth.s3_has_role(session.s3.system_roles.MAP_ADMIN)

        # Defaults
        # Also in static/S3/s3.gis.js
        # http://dev.openlayers.org/docs/files/OpenLayers/Strategy/Cluster-js.html
        self.cluster_distance = 2    # pixels
        self.cluster_threshold = 2   # minimum # of features to form a cluster

        # Support bookmarks (such as from the control)
        # - these over-ride the arguments
        vars = request.vars

        # Read configuration
        config = self.get_config()
        if height:
            map_height = height
        else:
            map_height = settings.get_gis_map_height()
        if width:
            map_width = width
        else:
            map_width = settings.get_gis_map_width()
        if (bbox
            and (-90 < bbox["max_lat"] < 90)
            and (-90 < bbox["min_lat"] < 90)
            and (-180 < bbox["max_lon"] < 180)
            and (-180 < bbox["min_lon"] < 180)
        ):
            # We have sane Bounds provided, so we should use them
            pass
        else:
            # No bounds or we've been passed bounds which aren't sane
            bbox = None
            # Use Lat/Lon to center instead
            if "lat" in vars and vars.lat:
                lat = float(vars.lat)
            if lat is None or lat == "":
                lat = config.lat
            if "lon" in vars and vars.lon:
                lon = float(vars.lon)
            if lon is None or lon == "":
                lon = config.lon

        if "zoom" in request.vars:
            zoom = int(vars.zoom)
        if not zoom:
            zoom = config.zoom

        if not projection:
            projection = config.epsg
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
                    response.warning =  \
                        T("Map not available: Projection %(projection)s not supported - please add definition to %(path)s") % \
                            dict(projection = "'%s'" % projection,
                                 path= "/static/scripts/gis/proj4js/lib/defs")
                else:
                    response.warning =  \
                        T("Map not available: No Projection configured")
                return None

        units = config.units
        maxResolution = config.maxResolution
        maxExtent = config.maxExtent
        numZoomLevels = config.zoom_levels
        marker_default = Storage(image = config.marker_image,
                                 height = config.marker_height,
                                 width = config.marker_width,
                                 url = URL(c="static", f="img",
                                           args=["markers", config.marker_image]))
        markers = {}

        #####
        # CSS
        #####
        # All Loaded as-standard to avoid delays in page loading

        ######
        # HTML
        ######
        html = DIV(_id="map_wrapper")

        # Map (Embedded not Window)
        html.append(DIV(_id="map_panel"))

        # Status Reports
        html.append(TABLE(TR(
            #TD(
            #    # Somewhere to report details of OSM File Features via on_feature_hover()
            #    DIV(_id="status_osm"),
            #    _style="border: 0px none ;", _valign="top",
            #),
            TD(
                # Somewhere to report whether KML feed is using cached copy or completely inaccessible
                DIV(_id="status_kml"),
                # Somewhere to report if Files are not found
                DIV(_id="status_files"),
                _style="border: 0px none ;", _valign="top",
            )
        )))

        #########
        # Scripts
        #########

        def add_javascript(script):
            if type(script) == SCRIPT:
                html.append(script)
            elif script.startswith("http"):
                html.append(SCRIPT(_type="text/javascript",
                                   _src=script))
            else:
                html.append(SCRIPT(_type="text/javascript",
                                   _src=URL(c="static", f=script)))

        debug = session.s3.debug
        if debug:
            if projection not in (900913, 4326):
                add_javascript("scripts/gis/proj4js/lib/proj4js-combined.js")
                add_javascript("scripts/gis/proj4js/lib/defs/EPSG%s.js" % projection)

            add_javascript("scripts/gis/openlayers/lib/OpenLayers.js")
            add_javascript("scripts/gis/cdauth.js")
            add_javascript("scripts/gis/osm_styles.js")
            add_javascript("scripts/gis/GeoExt/lib/GeoExt.js")
            add_javascript("scripts/gis/GeoExt/ux/GeoNamesSearchCombo.js")
            add_javascript("scripts/gis/gxp/RowExpander.js")
            add_javascript("scripts/gis/gxp/widgets/NewSourceWindow.js")
            add_javascript("scripts/gis/gxp/plugins/LayerSource.js")
            add_javascript("scripts/gis/gxp/plugins/WMSSource.js")
            add_javascript("scripts/gis/gxp/plugins/Tool.js")
            add_javascript("scripts/gis/gxp/plugins/AddLayers.js")
            add_javascript("scripts/gis/gxp/plugins/RemoveLayer.js")
            if mouse_position == "mgrs":
                add_javascript("scripts/gis/usng2.js")
                add_javascript("scripts/gis/MP.js")
        else:
            if projection not in (900913, 4326):
                add_javascript("scripts/gis/proj4js/lib/proj4js-compressed.js")
                add_javascript("scripts/gis/proj4js/lib/defs/EPSG%s.js" % projection)
            add_javascript("scripts/gis/OpenLayers.js")
            add_javascript("scripts/gis/GeoExt.js")
            if mouse_position == "mgrs":
                add_javascript("scripts/gis/MGRS.min.js")

        if print_tool:
            url = "%sinfo.json?var=printCapabilities" % print_tool["url"]
            add_javascript(url)

        #######
        # Tools
        #######

        # Toolbar
        if toolbar:
            toolbar = "S3.gis.toolbar = true;\n"
        else:
            toolbar = ""
        
        # @ToDo: Could we get this automatically?
        if location_selector:
            loc_select = "S3.gis.loc_select = true;\n"
        else:
            loc_select = ""

        # MGRS PDF Browser
        if mgrs:
            mgrs_name = "S3.gis.mgrs_name = '%s';\n" % mgrs["name"]
            mgrs_url = "S3.gis.mgrs_url = '%s';\n" % mgrs["url"]
        else:
            mgrs_name = ""
            mgrs_url = ""

        # Legend panel
        if legend:
            legend = "S3.i18n.gis_legend = '%s';\n" % T("Legend")
        else:
            legend = ""

        # Draw Feature Controls
        if add_feature:
            if add_feature_active:
                draw_feature = "S3.gis.draw_feature = 'active';\n"
            else:
                draw_feature = "S3.gis.draw_feature = 'inactive';\n"
        else:
            draw_feature = ""

        if add_polygon:
            if add_polygon_active:
                draw_polygon = "S3.gis.draw_polygon = 'active';\n"
            else:
                draw_polygon = "S3.gis.draw_polygon = 'inactive';\n"
        else:
            draw_polygon = ""

        authenticated = ""
        config_id = ""
        if auth.is_logged_in():
            authenticated = "S3.auth = true;\n"
            if MAP_ADMIN or \
               (config.pe_id == auth.user.pe_id):
                # Personal config or MapAdmin, so enable Save Button for Updates
                config_id = "S3.gis.config_id = %i;\n" % config.id

        # Upload Layer
        if settings.get_gis_geoserver_password():
            upload_layer = "S3.i18n.gis_uploadlayer = 'Upload Shapefile';\n"
            add_javascript("scripts/gis/gxp/FileUploadField.js")
            add_javascript("scripts/gis/gxp/widgets/LayerUploadPanel.js")
        else:
            upload_layer = ""

        # Search
        if search:
            search = "S3.i18n.gis_search = '%s';\n" % T("Search location in Geonames")
            #"S3.i18n.gis_search_no_internet = '%s';" % T("Geonames.org search requires Internet connectivity!")
        else:
            search = ""

        # WMS Browser
        if wms_browser:
            wms_browser_name = "S3.gis.wms_browser_name = '%s';\n" % wms_browser["name"]
            # urlencode the URL
            wms_browser_url = "S3.gis.wms_browser_url = '%s';\n" % urllib.quote(wms_browser["url"])
        else:
            wms_browser_name = ""
            wms_browser_url = ""

        # Mouse Position
        if not mouse_position:
            mouse_position = ""
        elif mouse_position == "mgrs":
            mouse_position = "S3.gis.mouse_position = 'mgrs';\n"
        else:
            mouse_position = "S3.gis.mouse_position = true;\n"

        # OSM Authoring
        if config.osm_oauth_consumer_key and \
           config.osm_oauth_consumer_secret:
            osm_auth = "S3.gis.osm_oauth = '%s';\n" % T("Zoom in closer to Edit OpenStreetMap layer")
        else:
            osm_auth = ""

        # Print
        # NB This isn't too-flexible a method. We're now focussing on print.css
        # If we do come back to it, then it should be moved to static
        if print_tool:
            url = print_tool["url"]
            url + "" # check url can be concatenated with strings
            if "title" in print_tool:
                mapTitle = unicode(print_tool["mapTitle"])
            else:
                mapTitle = unicode(T("Map from Sahana Eden"))
            if "subtitle" in print_tool:
                subTitle = unicode(print_tool["subTitle"])
            else:
                subTitle = unicode(T("Printed from Sahana Eden"))
            if auth.is_logged_in():
                creator = unicode(auth.user.email)
            else:
                creator = ""
            print_tool1 = u"".join(("""
        if (typeof(printCapabilities) != 'undefined') {
            // info.json from script headers OK
            printProvider = new GeoExt.data.PrintProvider({
                //method: 'POST',
                //url: '""", url, """',
                method: 'GET', // 'POST' recommended for production use
                capabilities: printCapabilities, // from the info.json returned from the script headers
                customParams: {
                    mapTitle: '""", mapTitle, """',
                    subTitle: '""", subTitle, """',
                    creator: '""", creator, """'
                }
            });
            // Our print page. Stores scale, center and rotation and gives us a page
            // extent feature that we can add to a layer.
            printPage = new GeoExt.data.PrintPage({
                printProvider: printProvider
            });

            //var printExtent = new GeoExt.plugins.PrintExtent({
            //    printProvider: printProvider
            //});
            // A layer to display the print page extent
            //var pageLayer = new OpenLayers.Layer.Vector('""", unicode(T("Print Extent")), """');
            //pageLayer.addFeatures(printPage.feature);
            //pageLayer.setVisibility(false);
            //map.addLayer(pageLayer);
            //var pageControl = new OpenLayers.Control.TransformFeature();
            //map.addControl(pageControl);
            //map.setOptions({
            //    eventListeners: {
                    // recenter/resize page extent after pan/zoom
            //        'moveend': function() {
            //            printPage.fit(mapPanel, true);
            //        }
            //    }
            //});
            // The form with fields controlling the print output
            S3.gis.printFormPanel = new Ext.form.FormPanel({
                title: '""", unicode(T("Print Map")), """',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%%'},
                listeners: {
                    'expand': function() {
                        //if (null == mapPanel.map.getLayersByName('""", unicode(T("Print Extent")), """')[0]) {
                        //    mapPanel.map.addLayer(pageLayer);
                        //}
                        if (null == mapPanel.plugins[0]) {
                            //map.addLayer(pageLayer);
                            //pageControl.activate();
                            //mapPanel.plugins = [ new GeoExt.plugins.PrintExtent({
                            //    printProvider: printProvider,
                            //    map: map,
                            //    layer: pageLayer,
                            //    control: pageControl
                            //}) ];
                            //mapPanel.plugins[0].addPage();
                        }
                    },
                    'collapse':  function() {
                        //mapPanel.map.removeLayer(pageLayer);
                        //if (null != mapPanel.plugins[0]) {
                        //    map.removeLayer(pageLayer);
                        //    mapPanel.plugins[0].removePage(mapPanel.plugins[0].pages[0]);
                        //    mapPanel.plugins = [];
                        //}
                    }
                },
                items: [{
                    xtype: 'textarea',
                    name: 'comment',
                    value: '',
                    fieldLabel: '""", unicode(T("Comment")), """',
                    plugins: new GeoExt.plugins.PrintPageField({
                        printPage: printPage
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.layouts,
                    displayField: 'name',
                    fieldLabel: '""", T("Layout").decode("utf-8"), """',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.dpis,
                    displayField: 'name',
                    fieldLabel: '""", unicode(T("Resolution")), """',
                    tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    }),
                    // the plugin will work even if we modify a combo value
                    setValue: function(v) {
                        v = parseInt(v) + ' dpi';
                        Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
                    }
                //}, {
                //    xtype: 'combo',
                //    store: printProvider.scales,
                //    displayField: 'name',
                //    fieldLabel: '""", unicode(T("Scale")), """',
                //    typeAhead: true,
                //    mode: 'local',
                //    triggerAction: 'all',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                //}, {
                //    xtype: 'textfield',
                //    name: 'rotation',
                //    fieldLabel: '""", unicode(T("Rotation")), """',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                }],
                buttons: [{
                    text: '""", unicode(T("Create PDF")), """',
                    handler: function() {
                        // the PrintExtent plugin is the mapPanel's 1st plugin
                        //mapPanel.plugins[0].print();
                        // convenient way to fit the print page to the visible map area
                        printPage.fit(mapPanel, true);
                        // print the page, including the legend, where available
                        if (null == legendPanel) {
                            printProvider.print(mapPanel, printPage);
                        } else {
                            printProvider.print(mapPanel, printPage, {legend: legendPanel});
                        }
                    }
                }]
            });
        } else {
            // Display error diagnostic
            S3.gis.printFormPanel = new Ext.Panel ({
                title: '""", unicode(T("Print Map")), """',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                html: '""", unicode(T("Printing disabled since server not accessible")), """: <BR />""", unicode(url), """'
            });
        }
        """))
        else:
            print_tool1 = ""

        ##########
        # Settings
        ##########

        # Layout
        s3_gis_window = ""
        s3_gis_windowHide = ""
        if not closable:
            s3_gis_windowNotClosable = "S3.gis.windowNotClosable = true;\n"
        else:
            s3_gis_windowNotClosable = ""
        if window:
            s3_gis_window = "S3.gis.window = true;\n"
            if window_hide:
                s3_gis_windowHide = "S3.gis.windowHide = true;\n"

        if maximizable:
            maximizable = "S3.gis.maximizable = true;\n"
        else:
            maximizable = "S3.gis.maximizable = false;\n"

        # Collapsed
        if collapsed:
            collapsed = "S3.gis.west_collapsed = true;\n"
        else:
            collapsed = ""

        # Bounding Box
        if bbox:
            # Calculate from Bounds
            center = """S3.gis.lat, S3.gis.lon;
S3.gis.bottom_left = new OpenLayers.LonLat(%f, %f);
S3.gis.top_right = new OpenLayers.LonLat(%f, %f);
""" % (bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])
        else:
            center = """S3.gis.lat = %s;
S3.gis.lon = %s;
""" % (lat, lon)

        # Still being used by legacy Feature Layers
        # // Needs to be uniquely instantiated
        # // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
        cluster_style = """
        var style_cluster = new OpenLayers.Style(s3_gis_cluster_style(1), S3.gis.cluster_options);
        var featureClusterStyleMap = new OpenLayers.StyleMap({
                                          'default': style_cluster,
                                          'select': {
                                              fillColor: '#ffdc33',
                                              strokeColor: '#ff9933'
                                          }
        });
        """

        ########
        # Layers
        ########

        # =====================================================================
        # Overlays
        #

        # Duplicate Features to go across the dateline?
        # @ToDo: Action this again (e.g. for DRRPP)
        if settings.get_gis_duplicate_features():
            duplicate_features = "S3.gis.duplicate_features = true;"
        else:
            duplicate_features = ""

        # ---------------------------------------------------------------------
        # Features
        #
        # Simple Features added to the Draft layer
        # - used by the Location Selector
        #
        _features = ""
        if features:
            _features = "S3.gis.features = new Array();\n"
            counter = -1
            for feature in features:
                counter = counter + 1
                if feature["lat"] and feature["lon"]:
                    # Generate JS snippet to pass to static
                    _features += """S3.gis.features[%i] = {
    lat: %f,
    lon: %f
}\n""" % (counter,
          feature["lat"],
          feature["lon"])

        # ---------------------------------------------------------------------
        # Feature Queries
        #
        #   These can be Rows or Storage()
        # NB These considerations need to be taken care of before arriving here:
        #   Security of data
        #   Localisation of name/popup_label
        #
        if feature_queries:
            layers_feature_queries = """
S3.gis.layers_feature_queries = new Array();"""
            counter = -1
            mtable = s3db.gis_marker
        else:
            layers_feature_queries = ""
        for layer in feature_queries:
            counter = counter + 1
            name = str(layer["name"])
            name_safe = re.sub("\W", "_", name) # ???

            # Lat/Lon via Join or direct?
            try:
                layer["query"][0].gis_location.lat
                join = True
            except:
                join = False

            # Push the Features into a temporary table in order to have them accessible via GeoJSON
            # @ToDo: Maintenance Script to clean out old entries (> 24 hours?)
            fqtable = s3db.gis_feature_query
            cname = "%s_%s_%s" % (name_safe,
                                  request.controller,
                                  request.function)
            # Clear old records
            query = (fqtable.name == cname)
            if auth.user:
                created_by = auth.user.id
            else:
                # Anonymous
                # @ToDo: A deployment with many Anonymous Feature Queries being
                #        accessed will need to change this design - e.g. use session ID instead
                created_by = None
            query = query & (fqtable.created_by == created_by)
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
                record_id = fqtable.insert(**rowdict)
                if not created_by:
                    auth.s3_make_session_owner(fqtable, record_id)

            # URL to retrieve the data
            url = "%s.geojson?feature_query.name=%s&feature_query.created_by=%s" % \
                    (URL(c="gis", f="feature_query"),
                     cname,
                     created_by)

            if "active" in layer and not layer["active"]:
                visibility = """,
    "visibility": false"""
            else:
                visibility = ""

            markerLayer = ""
            if "marker" in layer:
                # per-Layer Marker
                marker = layer["marker"]
                try:
                    # row
                    marker_url = URL(c="static", f="img",
                                     args=["markers", marker.image])
                    marker_height = marker.height
                    marker_width = marker.width
                except:
                    # integer (marker_id)
                    query = (mtable.id == marker)
                    marker = db(query).select(mtable.image,
                                              mtable.height,
                                              mtable.width,
                                              limitby=(0, 1),
                                              cache=cache).first()
                    if marker:
                        marker_url = URL(c="static", f="img",
                                         args=["markers", marker.image])
                        marker_height = marker.height
                        marker_width = marker.width
                    else:
                        marker_url = ""
                if marker_url:
                    markerLayer = """,
    "marker_url": "%s",
    "marker_height": %i,
    "marker_width": %i""" % (marker_url, marker_height, marker_width)

            if "opacity" in layer and layer["opacity"] != 1:
                opacity = """,
    "opacity": %.1f""" % layer["opacity"]
            else:
                opacity = ""
            if "cluster_distance" in layer and layer["cluster_distance"] != self.cluster_distance:
                cluster_distance = """,
    "cluster_distance": %i""" % layer["cluster_distance"]
            else:
                cluster_distance = ""
            if "cluster_threshold" in layer and layer["cluster_threshold"] != self.cluster_threshold:
                cluster_threshold = """,
    "cluster_threshold": %i""" % layer["cluster_threshold"]
            else:
                cluster_threshold = ""

            # Generate JS snippet to pass to static
            layers_feature_queries += """
S3.gis.layers_feature_queries[%i] = {
    "name": "%s",
    "url": "%s"%s%s%s%s%s
}
""" % (counter,
        name,
        url,
        visibility,
        markerLayer,
        opacity,
        cluster_distance,
        cluster_threshold)

        if catalogue_layers:
            # Add all Layers from the Catalogue
            layer_types = [
                BingLayer,
                EmptyLayer,
                GoogleLayer,
                OSMLayer,
                TMSLayer,
                WMSLayer,
                JSLayer,
                ThemeLayer,
                GeoJSONLayer,
                GPXLayer,
                CoordinateLayer,
                GeoRSSLayer,
                KMLLayer,
                WFSLayer,
                FeatureLayer,
            ]
        else:
            # Add just the default Base Layer
            response.s3.gis.base = True
            layer_types = []
            base = config["base"]
            if base:
                ltable = s3db.gis_layer_entity
                query = (ltable.id == base)
                layer = db(query).select(ltable.instance_type,
                                         limitby=(0, 1)).first()
                if layer:
                    layer_type = layer.instance_type
                    if layer_type == "gis_layer_openstreetmap":
                        layer_types = [OSMLayer]
                    elif layer_type == "gis_layer_google":
                        # NB v3 doesn't work when initially hidden
                        layer_types = [GoogleLayer]
                    elif layer_type == "gis_layer_bing":
                        layer_types = [BingLayer]
                    elif layer_type == "gis_layer_tms":
                        layer_types = [TMSLayer]
                    elif layer_type == "gis_layer_wms":
                        layer_types = [WMSLayer]
                    elif layer_type == "gis_layer_empty":
                        layer_types = [EmptyLayer]
            if not layer_types:
                layer_types = [EmptyLayer]

        layers_config = ""
        for LayerType in layer_types:
            try:
                # Instantiate the Class
                layer = LayerType()
                layer_type_js = layer.as_javascript()
                if layer_type_js:
                    # Add to the output JS
                    layers_config = "".join((layers_config,
                                             layer_type_js))
                    if layer.scripts:
                        for script in layer.scripts:
                            add_javascript(script)
            except Exception, exception:
                error = "%s not shown: %s" % (LayerType.__name__,
                                                           exception)
                if debug:
                    raise HTTP(500, error)
                else:
                    response.warning += error

        # WMS getFeatureInfo
        # (loads conditionally based on whether queryable WMS Layers have been added)
        if response.s3.gis.get_feature_info:
            getfeatureinfo = """S3.i18n.gis_get_feature_info = '%s';
S3.i18n.gis_feature_info = '%s';
""" % (T("Get Feature Info"),
       T("Feature Info"))
        else:
            getfeatureinfo = ""

        #############
        # Main script
        #############

        # Configure settings to pass through to Static script
        # @ToDo: Consider passing this as JSON Objects to allow it to be done dynamically
        html.append(SCRIPT("".join((
            authenticated,
            "S3.public_url = '%s';\n" % public_url,  # Needed just for GoogleEarthPanel
            config_id,
            s3_gis_window,
            s3_gis_windowHide,
            s3_gis_windowNotClosable,
            maximizable,
            collapsed,
            toolbar,
            loc_select,
            "S3.gis.map_height = %i;\n" % map_height,
            "S3.gis.map_width = %i;\n" % map_width,
            "S3.gis.zoom = %i;\n" % (zoom or 1),
            center,
            "S3.gis.projection = '%i';\n" % projection,
            "S3.gis.units = '%s';\n" % units,
            "S3.gis.maxResolution = %f;\n" % maxResolution,
            "S3.gis.maxExtent = new OpenLayers.Bounds(%s);\n" % maxExtent,
            "S3.gis.numZoomLevels = %i;\n" % numZoomLevels,
            "S3.gis.max_w = %i;\n" % settings.get_gis_marker_max_width(),
            "S3.gis.max_h = %i;\n" % settings.get_gis_marker_max_height(),
            mouse_position,
            duplicate_features,
            wms_browser_name,
            wms_browser_url,
            mgrs_name,
            mgrs_url,
            draw_feature,
            draw_polygon,
            "S3.gis.marker_default = '%s';\n" % marker_default.image,
            "S3.gis.marker_default_height = %i;\n" % marker_default.height,
            "S3.gis.marker_default_width = %i;\n" % marker_default.width,
            osm_auth,
            layers_feature_queries,
            _features,
            layers_config,
            # i18n Labels
            legend,                     # Presence of label turns feature on
            search,                     # Presence of label turns feature on
            getfeatureinfo,             # Presence of labels turns feature on
            upload_layer,               # Presence of labels turns feature on
            "S3.i18n.gis_requires_login = '%s';\n" % T("Requires Login"),
            "S3.i18n.gis_base_layers = '%s';\n" % T("Base Layers"),
            "S3.i18n.gis_overlays = '%s';\n" % T("Overlays"),
            "S3.i18n.gis_layers = '%s';\n" % T("Layers"),
            "S3.i18n.gis_draft_layer = '%s';\n" % T("Draft Features"),
            "S3.i18n.gis_cluster_multiple = '%s';\n" % T("There are multiple records at this location"),
            "S3.i18n.gis_loading = '%s';\n" % T("Loading"),
            "S3.i18n.gis_length_message = '%s';\n" % T("The length is"),
            "S3.i18n.gis_area_message = '%s';\n" % T("The area is"),
            "S3.i18n.gis_length_tooltip = '%s';\n" % T("Measure Length: Click the points along the path & end with a double-click"),
            "S3.i18n.gis_area_tooltip = '%s';\n" % T("Measure Area: Click the points around the polygon & end with a double-click"),
            "S3.i18n.gis_zoomfull = '%s';\n" % T("Zoom to maximum map extent"),
            "S3.i18n.gis_zoomout = '%s';\n" % T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle"),
            "S3.i18n.gis_zoomin = '%s';\n" % T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle"),
            "S3.i18n.gis_pan = '%s';\n" % T("Pan Map: keep the left mouse button pressed and drag the map"),
            "S3.i18n.gis_navPrevious = '%s';\n" % T("Previous View"),
            "S3.i18n.gis_navNext = '%s';\n" % T("Next View"),
            "S3.i18n.gis_geoLocate = '%s';\n" % T("Zoom to Current Location"),
            "S3.i18n.gis_draw_feature = '%s';\n" % T("Add Point"),
            "S3.i18n.gis_draw_polygon = '%s';\n" % T("Add Polygon"),
            "S3.i18n.gis_save = '%s';\n" % T("Save: Default Lat, Lon & Zoom for the Viewport"),
            "S3.i18n.gis_potlatch = '%s';\n" % T("Edit the OpenStreetMap data for this area"),
            # For S3LocationSelectorWidget
            "S3.i18n.gis_current_location = '%s';\n" % T("Current Location"),
        ))))

        # Static Script
        if debug:
            add_javascript("scripts/S3/s3.gis.js")
            add_javascript("scripts/S3/s3.gis.layers.js")
            add_javascript("scripts/S3/s3.gis.controls.js")
        else:
            add_javascript("scripts/S3/s3.gis.min.js")

        # Dynamic Script (stuff which should, as far as possible, be moved to static)
        html.append(SCRIPT(print_tool1))

        # Set up map plugins
        # This, and any code it generates is done last
        # However, map plugin should not assume this.
        if plugins is not None:
            for plugin in plugins:
                plugin.extend_gis_map(
                    add_javascript,
                    html.append # for adding in dynamic configuration, etc.
                )

        return html

# =============================================================================
class Marker(object):
    """
        Represents a Map Marker
    """

    def __init__(self, id=None, layer_id=None):

        db = current.db
        s3db = current.s3db
        mtable = s3db.gis_marker
        marker = None
        config = None
        if id:
            # Lookup the Marker details from it's ID
            query = (mtable.id == id)
            marker = db(query).select(mtable.image,
                                      mtable.height,
                                      mtable.width,
                                      limitby=(0, 1),
                                      cache=s3db.cache).first()
        elif layer_id:
            # Check if we have a Marker for this Layer
            config = current.gis.get_config()
            ltable = s3db.gis_layer_symbology
            query = (ltable.layer_id == layer_id) & \
                    (ltable.symbology_id == config.symbology_id) & \
                    (ltable.marker_id == mtable.id)
            marker = db(query).select(mtable.image,
                                      mtable.height,
                                      mtable.width,
                                      limitby=(0, 1)).first()
        if not marker:
            # Default Marker
            if not config:
                config = current.gis.get_config()
            self.image = config.marker_image
            self.height = config.marker_height
            self.width = config.marker_width
        else:
            self.image = marker.image
            self.height = marker.height
            self.width = marker.width

        # Always lookup URL client-side
        #self.url = URL(c="static", f="img",
        #               args=["markers", marker.image])

    def add_attributes_to_output(self, output):
        """
            Called by Layer.as_dict()
        """
        output["marker_image"] = self.image
        output["marker_height"] = self.height
        output["marker_width"] = self.width

    def as_dict(self):
        """
            Called by gis.get_marker()
        """
        output = Storage(
                        image = self.image,
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
            config = current.gis.get_config()
            projection = Storage(epsg = config.epsg)

        self.epsg = projection.epsg

# =============================================================================
class Layer(object):
    """
        Abstract base class for Layers from Catalogue
    """

    def __init__(self):

        self.sublayers = []
        append = self.sublayers.append
        self.scripts = []

        s3 = current.response.s3
        s3db = current.s3db
        s3_has_role = current.auth.s3_has_role

        # Read the Layers enabled in the Active Configs
        tablename = self.tablename
        table = s3db[tablename]
        ctable = s3db.gis_config
        ltable = s3db.gis_layer_config

        fields = table.fields
        metafields = s3.all_meta_field_names
        fields = [table[f] for f in fields if f not in metafields]
        fields.append(ltable.enabled)
        fields.append(ltable.visible)
        fields.append(ltable.base)
        fields.append(ctable.pe_type)
        query = (table.layer_id == ltable.layer_id) & \
                (ltable.config_id == ctable.id) & \
                (ltable.config_id.belongs(s3.gis.config.ids))
        if s3.gis.base == True:
            # Only show the default base layer
            if self.tablename == "gis_layer_empty":
                # Show even if disabled (as fallback)
                query = (table.id > 0)
            else:
                query = query & (ltable.base == True)

        rows = current.db(query).select(orderby=ctable.pe_type,
                                        *fields)
        layer_ids = []
        # Flag to show whether we've set the default baselayer
        # (otherwise a config higher in the hierarchy can overrule one lower down)
        base = True
        for _record in rows:
            record = _record[tablename]
            # Check if we've already seen this layer
            layer_id = record.layer_id
            if layer_id in layer_ids:
                continue
            # Add layer to list of checked
            layer_ids.append(layer_id)
            # Check if layer is enabled
            _config = _record["gis_layer_config"]
            if not _config.enabled:
                continue
            # Check user is allowed to access the layer
            role_required = record.role_required
            if role_required and not s3_has_role(role_required):
                continue
            # All OK - add SubLayer
            record["visible"] = _config.visible
            if base and _config.base:
                # name can't conflict with OSM layers
                record["_base"] = True
                base = False
            else:
                record["_base"] = False
            if tablename in ["gis_layer_bing", "gis_layer_google"]:
                append(record)
            else:
                append(self.SubLayer(record))

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layers as Javascript
            - suitable for inclusion in the HTML page
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
            # Output the Layer Type as JSON
            layer_type_json = json.dumps(sublayer_dicts,
                                         sort_keys=True,
                                         indent=4)
            return "%s = %s\n" % (self.js_array, layer_type_json)
        else:
            return None

    # -------------------------------------------------------------------------
    def as_json(self):
        """
            Output the Layers as JSON

            @ToDo: Support layers with SubLayer.as_dict() to pass config
                   dynamically between server & client
        """

        if self.record:
            return json.dumps(self.as_dict(), indent=4, sort_keys=True)
        else:
            return

    # -------------------------------------------------------------------------
    class SubLayer(object):
        def __init__(self, record):
            # Ensure all attributes available (even if Null)
            self.__dict__.update(record)
            del record
            self.safe_name = re.sub('[\\"]', "", self.name)

            self.marker = Marker(layer_id=self.layer_id)
            if hasattr(self, "projection_id"):
                self.projection = Projection(self.projection_id)

        def setup_clustering(self, output):
            gis = current.gis
            cluster_distance = gis.cluster_distance
            cluster_threshold = gis.cluster_threshold
            if self.cluster_distance != cluster_distance:
                output["cluster_distance"] = self.cluster_distance
            if self.cluster_threshold != cluster_threshold:
                output["cluster_threshold"] = self.cluster_threshold

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

        @staticmethod
        def add_attributes_if_not_default(output, **values_and_defaults):
            # could also write values in debug mode, to check if defaults ignored.
            # could also check values are not being overwritten.
            for key, (value, defaults) in values_and_defaults.iteritems():
                if value not in defaults:
                    output[key] = value

# -----------------------------------------------------------------------------
class BingLayer(Layer):
    """
        Bing Layers from Catalogue
    """

    tablename = "gis_layer_bing"
    js_array = "S3.gis.Bing"

    # -------------------------------------------------------------------------
    def as_dict(self):
        sublayers = self.sublayers
        if sublayers:
            if Projection().epsg != 900913:
                raise Exception("Cannot display Bing layers unless we're using the Spherical Mercator Projection\n")
            # Mandatory attributes
            output = {
                "ApiKey": current.deployment_settings.get_gis_api_bing()
                }

            for sublayer in sublayers:
                # Attributes which are defaulted client-side if not set
                if sublayer._base:
                    # Set default Base layer
                    output["Base"] = sublayer.type
                if sublayer.type == "aerial":
                    output["Aerial"] = {"name": sublayer.name or "Bing Satellite",
                                        "id": sublayer.layer_id}
                elif sublayer.type == "road":
                    output["Road"] = {"name": sublayer.name or "Bing Roads",
                                      "id": sublayer.layer_id}
                elif sublayer.type == "hybrid":
                    output["Hybrid"] = {"name": sublayer.name or "Bing Hybrid",
                                        "id": sublayer.layer_id}
            return output
        else:
            return None

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layer as Javascript
            - suitable for inclusion in the HTML page
        """

        output = self.as_dict()
        if output:
            result = json.dumps(output, indent=4, sort_keys=True)
            if result:
                return "%s = %s\n" % (
                    self.js_array,
                    result
                )

        return None

# -----------------------------------------------------------------------------
class CoordinateLayer(Layer):
    """
        Coordinate Layer from Catalogue
        - there should only be one of these
    """

    tablename = "gis_layer_coordinate"

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layer as Javascript
            - suitable for inclusion in the HTML page
        """

        sublayers = self.sublayers
        if sublayers:
            sublayer = sublayers[0]
            name_safe = re.sub("'", "", sublayer.name)
            if "visible" in sublayer and sublayer["visible"]:
                visibility = "true"
            else:
                visibility = "false"
            output = "S3.gis.CoordinateGrid={name:'%s',visibility:%s,id:%s};" % \
                (name_safe, visibility, sublayer.layer_id)
            return output
        else:
            return None

# -----------------------------------------------------------------------------
class EmptyLayer(Layer):
    """
        Empty Layer from Catalogue
        - there should only be one of these
    """

    tablename = "gis_layer_empty"

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layer as Javascript
            - suitable for inclusion in the HTML page
        """

        sublayers = self.sublayers
        if sublayers:
            sublayer = sublayers[0]
            name = str(current.T(sublayer.name))
            name_safe = re.sub("'", "", name)
            if sublayer._base:
                base = ",base:true"
            else:
                base = ""
            output = "S3.gis.EmptyLayer={name:'%s',id:%s%s};\n" % \
                (name_safe, sublayer.layer_id, base)
            return output
        else:
            return None

# -----------------------------------------------------------------------------
class FeatureLayer(Layer):
    """
        Feature Layers from Catalogue
    """

    tablename = "gis_layer_feature"
    js_array = "S3.gis.layers_features"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def __init__(self, record):
            record_module = record.module
            self.skip = False
            if record_module is not None:
                if record_module not in current.deployment_settings.modules:
                    # Module is disabled
                    self.skip = True
                if not current.auth.permission(c=record.module,
                                               f=record.resource):
                    # User has no permission to this resource (in ACL)
                    self.skip = True
            else:
                raise Exception("FeatureLayer Record '%s' has no module" % record.name)
            super(FeatureLayer.SubLayer, self).__init__(record)

        def as_dict(self):
            if self.skip:
                # Skip layer
                return
            url = "%s.geojson?layer=%i&components=None" % \
                (URL(self.module, self.resource),
                 self.id)
            if self.filter:
                url = "%s&%s" % (url, self.filter)
            if self.trackable:
                url = "%s&track=1" % url

            # Mandatory attributes
            output = {
                "id": self.layer_id,
                "name": self.safe_name,
                "url": url,
            }
            #
            self.marker.add_attributes_to_output(output)
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)

            return output

# -----------------------------------------------------------------------------
class GeoJSONLayer(Layer):
    """
        GeoJSON Layers from Catalogue
    """

    tablename = "gis_layer_geojson"
    js_array = "S3.gis.layers_geojson"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            # Mandatory attributes
            output = {
                "id": self.layer_id,
                "name": self.safe_name,
                "url": self.url,
            }
            self.marker.add_attributes_to_output(output)

            # Attributes which are defaulted client-side if not set
            projection = self.projection
            if projection.epsg != 4326:
                output["projection"] = projection.epsg
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)

            return output

# -----------------------------------------------------------------------------
class GeoRSSLayer(Layer):
    """
        GeoRSS Layers from Catalogue
    """

    tablename = "gis_layer_georss"
    js_array = "S3.gis.layers_georss"

    def __init__(self):
        super(GeoRSSLayer, self).__init__()
        GeoRSSLayer.SubLayer.cachetable = current.s3db.gis_cache

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            db = current.db
            request = current.request
            response = current.response
            session = current.session
            public_url = current.deployment_settings.get_base_public_url()
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
                # @ToDo: Call directly without going via HTTP
                # @ToDo: Make this async by using S3Task (also use this for the refresh time)
                fields = ""
                if self.data:
                    fields = "&data_field=%s" % self.data
                if self.image:
                    fields = "%s&image_field=%s" % (fields, self.image)
                _url = "%s%s/update.georss?fetchurl=%s%s" % (public_url,
                                                             URL(c="gis", f="cache_feed"),
                                                             url,
                                                             fields)
                # Keep Session for local URLs
                cookie = Cookie.SimpleCookie()
                cookie[response.session_id_name] = response.session_id
                session._unlock(response)
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
            output = {
                    "id": self.layer_id,
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
class GoogleLayer(Layer):
    """
        Google Layers/Tools from Catalogue
    """

    tablename = "gis_layer_google"
    js_array = "S3.gis.Google"

    # -------------------------------------------------------------------------
    def as_dict(self):
        sublayers = self.sublayers
        if sublayers:
            T = current.T
            epsg = (Projection().epsg == 900913)
            apikey = current.deployment_settings.get_gis_api_google()
            debug = current.session.s3.debug
            add_script = self.scripts.append

            output = {}

            for sublayer in sublayers:
                # Attributes which are defaulted client-side if not set
                if sublayer.type == "earth":
                    output["Earth"] = str(T("Switch to 3D"))
                    add_script("http://www.google.com/jsapi?key=%s" % apikey)
                    add_script(SCRIPT("try{google && google.load('earth','1');}catch(e){};", _type="text/javascript"))
                    if debug:
                        # Non-debug has this included within GeoExt.js
                        add_script("scripts/gis/gxp/widgets/GoogleEarthPanel.js")
                elif epsg:
                    # Earth is the only layer which can run in non-Spherical Mercator
                    # @ToDo: Warning?
                    if sublayer._base:
                        # Set default Base layer
                        output["Base"] = sublayer.type
                    if sublayer.type == "satellite":
                        output["Satellite"] = {"name": sublayer.name or "Google Satellite",
                                               "id": sublayer.layer_id}
                    elif sublayer.type == "maps":
                        output["Maps"] = {"name": sublayer.name or "Google Maps",
                                          "id": sublayer.layer_id}
                    elif sublayer.type == "hybrid":
                        output["Hybrid"] = {"name": sublayer.name or "Google Hybrid",
                                            "id": sublayer.layer_id}
                    elif sublayer.type == "streetview":
                        output["StreetviewButton"] = "Click where you want to open Streetview"
                    elif sublayer.type == "terrain":
                        output["Terrain"] = {"name": sublayer.name or "Google Terrain",
                                             "id": sublayer.layer_id}
                    elif sublayer.type == "mapmaker":
                        output["MapMaker"] = {"name": sublayer.name or "Google MapMaker",
                                              "id": sublayer.layer_id}
                    elif sublayer.type == "mapmakerhybrid":
                        output["MapMakerHybrid"] = {"name": sublayer.name or "Google MapMaker Hybrid",
                                                    "id": sublayer.layer_id}

            if "MapMaker" in output or "MapMakerHybrid" in output:
                # Need to use v2 API
                # http://code.google.com/p/gmaps-api-issues/issues/detail?id=2349
                add_script("http://maps.google.com/maps?file=api&v=2&key=%s" % apikey)
            else:
                # v3 API
                add_script("http://maps.google.com/maps/api/js?v=3.6&sensor=false")
                if "StreetviewButton" in output:
                    # Streetview doesn't work with v2 API
                    output["StreetviewButton"] = str(T("Click where you want to open Streetview"))
                    output["StreetviewTitle"] = str(T("Street View"))
                    if debug:
                        # Non-debug has this included within GeoExt.js
                        add_script("scripts/gis/gxp/widgets/GoogleStreetViewPanel.js")

            return output
        else:
            return None

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layer as Javascript
            - suitable for inclusion in the HTML page
        """

        output = self.as_dict()
        if output:
            result = json.dumps(output, indent=4, sort_keys=True)
            if result:
                return "%s = %s\n" % (
                    self.js_array,
                    result
                )

        return None

# -----------------------------------------------------------------------------
class GPXLayer(Layer):
    """
        GPX Layers from Catalogue
    """

    tablename = "gis_layer_gpx"
    js_array = "S3.gis.layers_gpx"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            url = URL(c="default", f="download",
                      args=self.track)

            # Mandatory attributes
            output = {
                    "id": self.layer_id,
                    "name": self.safe_name,
                    "url": url,
                }
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
class JSLayer(Layer):
    """
        JS Layers from Catalogue
        - these are raw Javascript layers for use by expert OpenLayers people
          to quickly add/configure new data sources without needing support
          from back-end Sahana programmers
    """

    tablename = "gis_layer_js"

    # -------------------------------------------------------------------------
    def as_javascript(self):
        """
            Output the Layer as Javascript
            - suitable for inclusion in the HTML page
        """

        sublayers = self.sublayers
        if sublayers:
            output = "function addJSLayers() {"
            for sublayer in sublayers:
                output = "%s\n%s" % (output,
                                     sublayer.code)
            output = "%s\n}" % output
            return output
        else:
            return None


# -----------------------------------------------------------------------------
class KMLLayer(Layer):
    """
        KML Layers from Catalogue
    """

    tablename = "gis_layer_kml"
    js_array = "S3.gis.layers_kml"

    # -------------------------------------------------------------------------
    def __init__(self):
        "Set up the KML cache, should be done once per request"
        super(KMLLayer, self).__init__()

        # Needed for gis.download_kml()
        self.table = current.s3db[self.tablename]

        # Can we cache downloaded KML feeds?
        # Needed for unzipping & filtering as well
        # @ToDo: Should we move this folder to static to speed up access to cached content?
        #           Do we need to secure it?
        cachepath = os.path.join(current.request.folder,
                                 "uploads",
                                 "gis_cache")

        if os.path.exists(cachepath):
            cacheable = os.access(cachepath, os.W_OK)
        else:
            try:
                os.mkdir(cachepath)
            except OSError, os_error:
                s3_debug(
                    "GIS: KML layers cannot be cached: %s %s" % (
                        cachepath,
                        os_error
                    )
                )
                cacheable = False
            else:
                cacheable = True
        # @ToDo: Migrate to gis_cache
        KMLLayer.cachetable = current.s3db.gis_cache2
        KMLLayer.cacheable = cacheable
        KMLLayer.cachepath = cachepath


    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            db = current.db
            request = current.request

            cachetable = KMLLayer.cachetable
            cacheable = KMLLayer.cacheable
            cachepath = KMLLayer.cachepath

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
                    current.s3task.async("download_kml",
                                         args=[self.id, filename])
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

            output = dict(
                id = self.layer_id,
                name = self.safe_name,
                url = url,
            )
            self.add_attributes_if_not_default(
                output,
                title = (self.title, ("name", None, "")),
                body = (self.body, ("description", None)),
                refresh = (self.refresh, (900,)),
            )
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            self.marker.add_attributes_to_output(output)
            return output

# -----------------------------------------------------------------------------
class OSMLayer(Layer):
    """
        OpenStreetMap Layers from Catalogue

        @ToDo: Provide a catalogue of standard layers which are fully-defined
               in static & can just have name over-ridden, as well as
               fully-custom layers.
    """

    tablename = "gis_layer_openstreetmap"
    js_array = "S3.gis.layers_osm"

    # def __init__(self):
        # if Projection().epsg != 900913:
            # raise Exception("Cannot display OpenStreetMap layers unless we're using the Spherical Mercator Projection\n")
        # super(OSMLayer, self).__init__()

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            output = {
                    "id": self.layer_id,
                    "name": self.safe_name,
                    "url1": self.url1,
                }
            self.add_attributes_if_not_default(
                output,
                base = (self.base, (False,)),
                _base = (self._base, (False,)),
                url2 = (self.url2, (None,)),
                url3 = (self.url3, (None,)),
                zoomLevels = (self.zoom_levels, (9,)),
                attribution = (self.attribution, (None,)),
            )
            self.setup_folder_and_visibility(output)
            return output

# -----------------------------------------------------------------------------
class ThemeLayer(Layer):
    """
        Theme Layers from Catalogue
    """

    tablename = "gis_layer_theme"
    js_array = "S3.gis.layers_theme"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            url = "%s.geojson?theme_data.layer_theme_id=%i&polygons=1" % \
                (URL(c="gis", f="theme_data"),
                 self.id)

            # Mandatory attributes
            output = {
                "id": self.layer_id,
                "name": self.safe_name,
                "url": url,
            }
            #
            self.setup_folder_and_visibility(output)

            return output

# -----------------------------------------------------------------------------
class TMSLayer(Layer):
    """
        TMS Layers from Catalogue
    """

    tablename = "gis_layer_tms"
    js_array = "S3.gis.layers_tms"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            output = {
                    "id": self.layer_id,
                    "name": self.safe_name,
                    "url": self.url,
                    "layername": self.layername
                }
            self.add_attributes_if_not_default(
                output,
                _base = (self._base, (False,)),
                url2 = (self.url2, (None,)),
                url3 = (self.url3, (None,)),
                format = (self.img_format, ("png", None)),
                zoomLevels = (self.zoom_levels, (9,)),
                attribution = (self.attribution, (None,)),
            )
            self.setup_folder(output)
            return output

# -----------------------------------------------------------------------------
class WFSLayer(Layer):
    """
        WFS Layers from Catalogue
    """

    tablename = "gis_layer_wfs"
    js_array = "S3.gis.layers_wfs"

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            output = dict(
                id = self.layer_id,
                name = self.safe_name,
                url = self.url,
                title = self.title,
                featureType = self.featureType,
                featureNS = self.featureNS,
                schema = self.wfs_schema,
            )
            self.add_attributes_if_not_default(
                output,
                version = (self.version, ("1.1.0",)),
                geometryName = (self.geometryName, ("the_geom",)),
                styleField = (self.style_field, (None,)),
                styleValues = (self.style_values, ("{}", None)),
                projection = (self.projection.epsg, (4326,)),
                #editable
            )
            self.setup_folder_visibility_and_opacity(output)
            self.setup_clustering(output)
            return output


# -----------------------------------------------------------------------------
class WMSLayer(Layer):
    """
        WMS Layers from Catalogue
    """

    js_array = "S3.gis.layers_wms"
    tablename = "gis_layer_wms"

    # -------------------------------------------------------------------------
    def __init__(self):
        super(WMSLayer, self).__init__()
        if self.sublayers:
            debug = current.session.s3.debug
            add_script = self.scripts.append
            if debug:
                # Non-debug has this included within GeoExt.js
                add_script("scripts/gis/gxp/plugins/WMSGetFeatureInfo.js")

    # -------------------------------------------------------------------------
    class SubLayer(Layer.SubLayer):
        def as_dict(self):
            if self.queryable:
                current.response.s3.gis.get_feature_info = True
            output = dict(
                id = self.layer_id,
                name = self.safe_name,
                url = self.url,
                layers = self.layers
            )
            legend_url = self.legend_url
            if legend_url and not legend_url.startswith("http"):
                legend_url = "%s/%s%s" % \
                    (current.deployment_settings.get_base_public_url(),
                     current.request.application,
                     legend_url)
            self.add_attributes_if_not_default(
                output,
                transparent = (self.transparent, (True,)),
                version = (self.version, ("1.1.1",)),
                format = (self.img_format, ("image/png",)),
                map = (self.map, (None,)),
                buffer = (self.buffer, (0,)),
                base = (self.base, (False,)),
                _base = (self._base, (False,)),
                style = (self.style, (None,)),
                bgcolor = (self.bgcolor, (None,)),
                tiled = (self.tiled, (False, )),
                legendURL = (legend_url, (None,)),
                queryable = (self.queryable, (False, )),
            )
            self.setup_folder_visibility_and_opacity(output)
            return output


# =============================================================================
class S3MAP(S3Method):
    """
        Class to generate a Map

        Currently unused

        A typical implementation would be as follows:
            exporter = s3base.S3MAP()
            return exporter(xrequest, **attr)

        This class supports a set of Features, typically called from the icon
        shown in a search
                For example inv/warehouse

        For specialist calls a S3MAP() object will need to be created.
        See the apply_method() for ideas on how to create a map,
        but as a minimum the following structure is required:

            _map = S3MAP()
            #_map.newDocument(_map.defaultTitle(resource))
    """

    def apply_method(self, r, **attr):
        """
            Apply CRUD methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler
                         The attributes that it knows about are:
                         * componentname
                         * formname
                         * list_fields

            @returns: output object to send to the view
        """

        gis = current.gis

        # @ToDo: Deprecate gis controller's display_feature() & display_features()
        # @ToDo: Build feature query
        # @ToDo: Move to GeoJSON?
        feature_queries = []

        # Can this also be an Ext popup for consistency?
        #  request.vars to control map options
        output = gis.show_map(feature_queries=feature_queries)

        return output

# =============================================================================
class Geocoder(object):
    """
        Base class for all Geocoders
    """

    def __init__(self):
        " Initializes the page content object "
        pass

    # -------------------------------------------------------------------------
    @staticmethod
    def get_api_key(type):
        " Acquire API key from the database "
        pass

# -----------------------------------------------------------------------------
class GoogleGeocoder(Geocoder):
    """
        Google Geocoder module
        http://code.google.com/apis/maps/documentation/javascript/v2/reference.html#GGeoStatusCode
        Should convert this to be a thin wrapper for modules.geopy.geocoders.google
    """

    def __init__(self, location):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self)
        api_key = current.deployment_settings.get_gis_api_google()
        params = {"q": location, "key": api_key}
        self.url = "http://maps.google.com/maps/geo?%s" % urllib.urlencode(params)

    # -------------------------------------------------------------------------
    def get_json(self):
        " Returns the output in JSON format "
        url = self.url
        page = fetch(url)
        return page

# -----------------------------------------------------------------------------
class YahooGeocoder(Geocoder):
    """
        Yahoo Geocoder module
        Should convert this to be a thin wrapper for modules.geopy.geocoders.`
    """

    def __init__(self, location):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self)
        api_key = current.deployment_settings.get_gis_api_yahoo()
        params = {"location": location, "appid": api_key}
        self.url = "http://local.yahooapis.com/MapsService/V1/geocode?%s" % urllib.urlencode(params)

    # -------------------------------------------------------------------------
    def get_xml(self):
        " Return the output in XML format "
        url = self.url
        page = fetch(url)
        return page

# END =========================================================================
