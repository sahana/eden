# -*- coding: utf-8 -*-

""" S3XML Toolkit

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

import datetime
import os
import re
import sys
import urllib2

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import *
from gluon.storage import Storage

from s3codec import S3Codec
from s3fields import S3RepresentLazy
from s3utils import s3_get_foreign_key, s3_unicode, S3MarkupStripper, s3_validate, s3_represent_value

ogetattr = object.__getattribute__

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3XML(S3Codec):
    """
        XML toolkit for S3XRC
    """

    namespace = "sahana"

    CACHE_TTL = 20 # time-to-live of RAM cache for field representations

    UID = "uuid"
    MCI = "mci"
    DELETED = "deleted"
    REPLACEDBY = "deleted_rb"
    APPROVED = "approved"
    CTIME = "created_on"
    CUSER = "created_by"
    MTIME = "modified_on"
    MUSER = "modified_by"
    OGROUP = "owned_by_group"
    OUSER = "owned_by_user"

    # GIS field names
    Lat = "lat"
    Lon = "lon"
    WKT = "wkt"

    IGNORE_FIELDS = [
        "id",
        "deleted_fk",
        "approved_by",
        # @todo: export the realm entity
        "realm_entity",
        ]

    FIELDS_TO_ATTRIBUTES = [
        "id",
        "admin",
        CUSER,
        MUSER,
        OGROUP,
        OUSER,
        CTIME,
        MTIME,
        UID,
        MCI,
        DELETED,
        ]

    ATTRIBUTES_TO_FIELDS = [
        "admin",
        CUSER,
        MUSER,
        OGROUP,
        OUSER,
        CTIME,
        MTIME,
        MCI,
        DELETED,
        APPROVED,
        ]

    TAG = Storage(
        root="s3xml",
        resource="resource",
        reference="reference",
        description="description",
        contents="contents",
        meta="meta",
        data="data",
        list="list",
        item="item",
        object="object",
        select="select",
        field="field",
        option="option",
        options="options",
        fields="fields",
        table="table",
        row="row",
        col="col",
        )

    ATTRIBUTE = Storage(
        id="id",
        name="name",
        table="table",
        field="field",
        value="value",
        alias="alias",
        resource="resource",
        ref="ref",
        domain="domain",
        url="url",
        filename="filename",
        error="error",
        start="start",
        limit="limit",
        success="success",
        results="results",
        lat="lat",
        latmin="latmin",
        latmax="latmax",
        lon="lon",
        lonmin="lonmin",
        lonmax="lonmax",
        marker="marker",
        marker_url="marker_url",
        marker_height="marker_height",
        marker_width="marker_width",
        popup="popup",          # for GIS Feature Layers/Queries
        popup_url="popup_url",  # for map popups
        sym="sym",              # for GPS
        attributes="attributes",# For GeoJSON exports
        type="type",
        readable="readable",
        writable="writable",
        wkt="wkt",
        has_options="has_options",
        tuid="tuid",
        label="label",
        comment="comment",
        replaced_by="replaced_by"
        )

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete",
        )

    PREFIX = Storage(
        resource="$",
        options="$o",
        reference="$k",
        attribute="@",
        text="$",
        )

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        self.domain = current.request.env.server_name
        self.error = None
        self.filter_mci = False # Set to true to suppress export at MCI<0
        
        self.show_ids = False
        self.show_urls = True

    # XML+XSLT tools ==========================================================
    #
    def parse(self, source):
        """
            Parse an XML source into an element tree

            @param source: the XML source -
                can be a file-like object, a filename or a HTTP/HTTPS/FTP URL
        """

        self.error = None
        if isinstance(source, basestring) and source[:5] == "https":
            try:
                source = urllib2.urlopen(source)
            except:
                pass
        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            e = sys.exc_info()[1]
            self.error = e
            return None

    # -------------------------------------------------------------------------
    def transform(self, tree, stylesheet_path, **args):
        """
            Transform an element tree with XSLT

            @param tree: the element tree
            @param stylesheet_path: pathname of the XSLT stylesheet
            @param args: dict of arguments to pass to the stylesheet
        """

        self.error = None

        if args:
            _args = dict((k, "'%s'" % args[k]) for k in args)
        else:
            _args = None
            
        if isinstance(stylesheet_path, (etree._ElementTree, etree._Element)):
            # Pre-parsed stylesheet
            stylesheet = stylesheet_path
        else:
            stylesheet = self.parse(stylesheet_path)

        if stylesheet is not None:
            try:
                ac = etree.XSLTAccessControl(read_file=True, read_network=True)
                transformer = etree.XSLT(stylesheet, access_control=ac)
                if _args:
                    result = transformer(tree, **_args)
                else:
                    result = transformer(tree)
                return result
            except:
                e = sys.exc_info()[1]
                self.error = e
                current.log.error(e)
                return None
        else:
            # Error parsing the XSL stylesheet
            return None

    # -------------------------------------------------------------------------
    def envelope(self, tree, stylesheet_path, **args):
        """
            Wraps XML contents into an XML envelope like:

            <contents>
                <object>
                    <description>Description Text</description>
                    <-- tree gets copied in here -->
                </object>
                <!-- can be multiple <object> elements -->
            </contents>

            @param tree: the element tree or list of trees to wrap, can also
                         be a list of tuples (tree, description) in order to
                         provide a description for each XML content object
            @param stylesheet_path: the path to the XSLT transformation stylesheet
                                    to transform the envelope (e.g. into EDXL-DE)
            @param args: stylesheet parameters
        """

        if not isinstance(tree, (list, tuple)):
            tree = [tree]
        root = etree.Element(self.TAG.contents)
        for subtree in tree:
            contentDescription = None
            if isinstance(subtree, (list, tuple)):
                contentObject = subtree[0]
                if len(subtree) > 1:
                    contentDescription = subtree[1]

            if isinstance(subtree, etree._ElementTree):
                contentObject = subtree.getroot()
            else:
                contentObject = subtree
            obj = etree.SubElement(root, self.TAG.object)
            if contentDescription:
                desc = etree.SubElement(obj, self.TAG.description)
                desc.text = contentDescription
            from copy import deepcopy
            obj.append(deepcopy(contentObject))
        return self.transform(root, stylesheet_path, **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def tostring(tree, xml_declaration=True, pretty_print=True):
        """
            Convert an element tree into XML as string

            @param tree: the element tree
            @param xml_declaration: add an XML declaration to the output
            @param pretty_print: provide pretty formatted output
        """

        return etree.tostring(tree,
                              xml_declaration=xml_declaration,
                              encoding="utf-8",
                              pretty_print=pretty_print)

    # -------------------------------------------------------------------------
    def tree(self, elements,
             root=None,
             domain=None,
             url=None,
             start=None,
             limit=None,
             results=None,
             maxbounds=False):
        """
            Builds a S3XML tree from a list of elements

            @param elements: list of <resource> elements
            @param root: the root element to link the tree to
            @param domain: name of the current domain
            @param url: url of the request
            @param start: the start record (in server-side pagination)
            @param limit: the page size (in server-side pagination)
            @param results: number of total available results
            @param maxbounds: include maximum Geo-boundaries (lat/lon min/max)
        """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT stylesheets (need explicit prefix) and thus this
        # would require a rework of all existing stylesheets (which is
        # however useful)

        ATTRIBUTE = self.ATTRIBUTE

        success = False

        if root is None:
            root = etree.Element(self.TAG.root)
        if elements is not None or len(root):
            success = True
        set_attribute = root.set
        set_attribute(ATTRIBUTE.success, json.dumps(success))
        if start is not None:
            set_attribute(ATTRIBUTE.start, str(start))
        if limit is not None:
            set_attribute(ATTRIBUTE.limit, str(limit))
        if results is not None:
            set_attribute(ATTRIBUTE.results, str(results))
        if elements is not None:
            root.extend(elements)
        if domain:
            set_attribute(ATTRIBUTE.domain, self.domain)
        if url:
            set_attribute(ATTRIBUTE.url, current.response.s3.base_url)
        if maxbounds:
            # @ToDo: This should be done based on the features, not just the config
            bounds = current.gis.get_bounds()
            set_attribute(ATTRIBUTE.latmin,
                          str(bounds["lat_min"]))
            set_attribute(ATTRIBUTE.latmax,
                          str(bounds["lat_max"]))
            set_attribute(ATTRIBUTE.lonmin,
                          str(bounds["lon_min"]))
            set_attribute(ATTRIBUTE.lonmax,
                          str(bounds["lon_max"]))
        return etree.ElementTree(root)

    # -------------------------------------------------------------------------
    def export_uid(self, uid):
        """
            Exports UIDs with domain prefix

            @param uid: the UID
        """

        if not uid:
            return uid
        if uid[:4] == "urn:":
            return uid
        else:
            domain = self.domain
            if domain and "/" not in uid[1:-1]:
                return "%s/%s" % (domain, uid.strip("/"))
            else:
                return uid

    # -------------------------------------------------------------------------
    def import_uid(self, uid):
        """
            Imports UIDs with domain prefixes

            @param uid: the UID
        """

        domain = self.domain
        if not uid or uid.startswith("urn:") or not domain:
            return uid
        else:
            if "/" in uid[1:-1]:
                (_domain, _uid) = uid.strip("/").split("/", 1)
                if _domain == domain:
                    return _uid
                else:
                    return uid
            else:
                return uid

    # Data export =============================================================
    #
    def represent(self, table, f, v):
        """
            Get the representation of a field value

            @param table: the database table
            @param f: the field name
            @param v: the value
        """

        if f in (self.CUSER, self.MUSER, self.OUSER):
            represent = current.cache.ram("auth_user_%s" % v,
                                          lambda: self.represent_user(v),
                                          time_expire=60)
        elif f in (self.OGROUP):
            represent = current.cache.ram("auth_group_%s" % v,
                                          lambda: self.represent_role(v),
                                          time_expire=60)
        else:
            represent = s3_represent_value(table[f],
                                           value=v,
                                           strip_markup=True)
        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_user(user_id):
        utable = current.auth.settings.table_user
        #user = None
        #if "email" in utable:
        user = current.db(utable.id == user_id).select(utable.email,
                                                       limitby=(0, 1)
                                                       ).first()
        if user:
            return user.email
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_role(role_id):
        gtable = current.auth.settings.table_group
        #role = None
        #if "role" in gtable:
        role = current.db(gtable.id == role_id).select(gtable.role,
                                                       limitby=(0, 1),
                                                       cache=(current.cache.ram,
                                                              S3XML.CACHE_TTL)
                                                       ).first()
        if role:
            return role.role
        return None

    # -------------------------------------------------------------------------
    def rmap(self, table, record, fields):
        """
            Generates a reference map for a record

            @param table: the database table
            @param record: the record
            @param fields: list of reference field names in this table
        """

        reference_map = []

        DELETED = self.DELETED
        REPLACEDBY = self.REPLACEDBY

        if DELETED in record and record[DELETED] and \
           REPLACEDBY in record and record[REPLACEDBY]:
            fields = [REPLACEDBY]
            #replace = True
        else:
            fields = [f for f in fields if f in record and record[f]]
            #replace = False
            
        if not fields:
            return reference_map

        db = current.db

        UID = self.UID
        MCI = self.MCI

        export_uid = self.export_uid
        represent = self.represent
        filter_mci = self.filter_mci
        tablename = table._tablename
        gtablename = current.auth.settings.table_group_name
        load_table = current.s3db.table

        for f in fields:

            if f == REPLACEDBY:
                val = ogetattr(record, f)
                if not val:
                    continue
                row = db(table._id == val).select(table[UID],
                                                  limitby=(0, 1)).first()
                if not row:
                    continue
                else:
                    uids = [export_uid(row[UID])]
                entry = {"field": f,
                         "table": tablename,
                         "multiple": False,
                         "id": [val],
                         "uid": uids,
                         "text": None,
                         "lazy": False,
                         "value": None}
                reference_map.append(Storage(entry))
                continue

            try:
                dbfield = ogetattr(table, f)
            except:
                continue

            ktablename, pkey, multiple = s3_get_foreign_key(dbfield)
            if not ktablename:
                # Not a foreign key
                continue
            
            val = ids = ogetattr(record, f)

            ktable = load_table(ktablename)
            if not ktable:
                # Referenced table doesn't exist
                continue

            ktable_fields = ktable.fields
            k_id = ktable._id

            uid = None
            uids = None

            if pkey is None:
                pkey = k_id.name
            if pkey != "id" and "instance_type" in ktable_fields:

                # Super-link
                if multiple:
                    # @todo: Can't currently resolve multi-references to
                    # super-entities
                    continue
                else:
                    query = (k_id == ids)

                # Get the super-record
                srecord = db(query).select(ogetattr(ktable, UID),
                                           ktable.instance_type,
                                           limitby=(0, 1)).first()
                if not srecord:
                    continue
                    
                ktablename = srecord.instance_type
                uid = ogetattr(srecord, UID)
                
                if ktablename == tablename and \
                   UID in record and ogetattr(record, UID) == uid and \
                   not self.show_ids:
                    # Super key in the main instance record, never export
                    continue
                
                ktable = load_table(ktablename)
                if not ktable:
                    continue
                    
                # Make sure the referenced record is accessible:
                query = current.auth.s3_accessible_query("read", ktable) & \
                        (ktable[UID] == uid)
                krecord = db(query).select(ktable._id, limitby=(0, 1)).first()
                
                if not krecord:
                    continue
                    
                ids = [krecord[ktable._id]]
                uids = [export_uid(uid)]

            else:

                # Make sure the referenced records are accessible:
                query = current.auth.s3_accessible_query("read", ktable)
                if multiple:
                    query &= (k_id.belongs(ids))
                    limitby = None
                else:
                    query &= (k_id == ids)
                    limitby = (0, 1)
                    
                if DELETED in ktable_fields:
                    query = (ktable.deleted != True) & query
                if filter_mci and MCI in ktable_fields:
                    query = (ktable.mci >= 0) & query

                if UID in ktable_fields:
                    
                    krecords = db(query).select(ogetattr(ktable, UID),
                                                limitby=limitby)
                    if krecords:
                        uids = [r[UID] for r in krecords if r[UID]]
                        if ktablename != gtablename:
                            uids = map(export_uid, uids)
                    else:
                        continue
                else:
                    
                    krecord = db(query).select(k_id, limitby=(0, 1)).first()
                    if not krecord:
                        continue

            value = s3_unicode(dbfield.formatter(val))

            # Get the representation
            lazy = None
            renderer = dbfield.represent
            if renderer is not None:
                if hasattr(renderer, "bulk"):
                    text = None
                    lazy = S3RepresentLazy(val, renderer)
                else:
                    text = represent(table, f, val)
            else:
                text = value

            # Add the entry to the reference map
            entry = {"field":f,
                     "table":ktablename,
                     "multiple":multiple,
                     "id":ids if type(ids) is list else [ids],
                     "uid":uids,
                     "text":text,
                     "lazy":lazy,
                     "value":value}
            reference_map.append(Storage(entry))

        return reference_map

    # -------------------------------------------------------------------------
    def add_references(self, element, rmap, show_ids=False, lazy=None):
        """
            Adds <reference> elements to a <resource>

            @param element: the <resource> element
            @param rmap: the reference map for the corresponding record
            @param show_ids: insert the record ID as attribute in references
        """

        REFERENCE = self.TAG.reference

        ATTRIBUTE = self.ATTRIBUTE
        RESOURCE = ATTRIBUTE.resource
        FIELD = ATTRIBUTE.field
        VALUE = ATTRIBUTE.value
        ID = ATTRIBUTE.id
        RB = ATTRIBUTE.replaced_by

        UID = self.UID
        REPLACEDBY = self.REPLACEDBY
        
        as_json = json.dumps
        SubElement = etree.SubElement

        for i in xrange(0, len(rmap)):

            r = rmap[i]
            
            f = r.field
            if f == REPLACEDBY:
                element.set(RB, r.uid[0])
                continue

            reference = SubElement(element, REFERENCE)
            attr = reference.attrib
            attr[FIELD] = f
            attr[RESOURCE] = r.table

            if show_ids:
                if r.multiple:
                    ids = str(as_json(r.id))
                else:
                    ids = str(r.id[0])
                attr[ID] = ids

            if r.uid:
                
                if r.multiple:
                    uids = str(as_json(r.uid))
                else:
                    uids = str(r.uid[0])
                attr[UID] = uids.decode("utf-8")

                # Render representation
                if r.lazy is not None:
                    if lazy is not None:
                        lazy.append((r.lazy, reference, None, None))
                    else:
                        r.lazy.render_node(reference, None, None)
                else:
                    reference.text = r.text

            else:
                attr[VALUE] = r.value

            r.element = reference

    # -------------------------------------------------------------------------
    def latlon(self, rmap):
        """
            Add lat/lon to location references

            @param rmap: the reference map of the tree
        """
        
        ATTRIBUTE = self.ATTRIBUTE
        
        locations = {}
        for reference in rmap:
            if reference.table == "gis_location" and len(reference.id) == 1:
                location_id = reference.id[0]
                if location_id not in locations:
                    locations[location_id] = [reference]
                else:
                    locations[location_id].append(reference)
        if locations:
            ltable = current.s3db.gis_location
            rows = current.db(ltable._id.belongs(locations.keys())) \
                             .select(ltable.id,
                                     ltable.lat,
                                     ltable.lon,
                                     ).as_dict()

            for location_id, row in rows.items():
                lat = row["lat"]
                lon = row["lon"]
                if lat is not None and lon is not None:
                    references = locations.get(location_id, ())
                    for reference in references:
                        attr = reference.element.attrib
                        attr[ATTRIBUTE.lat] = "%.4f" % lat
                        attr[ATTRIBUTE.lon] = "%.4f" % lon
        return

    # -------------------------------------------------------------------------
    def gis_encode(self,
                   resource,
                   record,
                   element,
                   location_data = {},
                   ):
        """
            GIS-encodes the master resource so that it can be transformed into
            a mappable format.

            @param resource: the referencing resource
            @param record: the particular record
            @param element: the XML element
            @param location_data: dictionary of location data from gis.get_location_data()

            @ToDo: Support multiple locations per master resource (e.g. event_event.location)
        """

        format = current.auth.permission.format
        if format not in ("geojson", "georss", "gpx", "kml"):
            return

        tablename = resource.tablename
        if tablename == "gis_feature_query":
            # Requires no special handling: XSLT uses normal fields
            return dict()

        db = current.db
        gis = current.gis
        request = current.request
        settings = current.deployment_settings

        ATTRIBUTE = self.ATTRIBUTE
        WKTFIELD = self.WKT

        # Retrieve data prepared earlier in gis.get_location_data()
        latlons = location_data.get("latlons", [])
        geojsons = location_data.get("geojsons", [])
        wkts = location_data.get("wkts", [])
        #popup_url = location_data.get("popup_url", [])
        markers = location_data.get("markers", [])
        tooltips = location_data.get("tooltips", [])
        attributes = location_data.get("attributes", [])

        map_data = element.find("map")
        if map_data:
            map_data = map_data[0]
        else:
            map_data = etree.SubElement(element, "map")

        attr = map_data.attrib
        record_id = record.id

        if tablename == "gis_location":
            if tablename in geojsons:
                # These have been looked-up in bulk
                geojson = geojsons[tablename].get(record_id, None)
                if geojson:
                    geometry = etree.SubElement(map_data, "geometry")
                    geometry.set("value", geojson)
                    #if tablename in attributes:
                    #    # Add Attributes
                    #    _attr = ""
                    #    attrs = attributes[tablename][record_id]
                    #    for a in attrs:
                    #        if _attr:
                    #            _attr = "%s,[%s]=[%s]" % (_attr, a, attrs[a])
                    #        else:
                    #            _attr = "[%s]=[%s]" % (a, attrs[a])
                    #    if _attr:
                    #        attr[ATTRIBUTE.attributes] = _attr
                if tablename in tooltips:
                    # Retrieve the HTML for the onHover Tooltip
                    tooltip = tooltips[tablename][record_id]
                    if type(tooltip) is not unicode:
                        try:
                            # encode suitable for use as XML attribute
                            tooltip = tooltip.decode("utf-8")
                        except:
                            pass
                    else:
                        attr[ATTRIBUTE.popup] = tooltip
                # Use the current controller for map popup URLs to get
                # the controller settings applied even for map popups
                url = URL(request.controller,
                          request.function).split(".", 1)[0]
                # Assume being used within the Sahana Mapping client
                # so use local URLs to keep filesize down
                url = "%s/%i.plain" % (url, record_id)
                attr[ATTRIBUTE.popup_url] = url

            elif tablename in wkts:
                # Nothing gets here currently
                # tbc: KML Polygons (or we should also do these outside XSLT)
                wkt = wkts[tablename][record_id]
                # Convert the WKT in XSLT
                attr[ATTRIBUTE.wkt] = wkt

            else:
                # Lookup record by record :/
                table = resource.table
                query = (table._id == record_id)
                if settings.get_gis_spatialdb():
                    # Do the Simplify direct from the DB
                    row = db(query).select(table.the_geom.st_simplify(0.01).st_astext().with_alias("wkt"),
                                           limitby=(0, 1)).first()
                    if row:
                        # Convert the WKT in XSLT
                        attr[ATTRIBUTE.wkt] = row.wkt
                        # Locate the attributes
                        #row = row[tablename]
                else:
                    row = db(query).select(table[WKTFIELD],
                                           limitby=(0, 1)).first()
                    if row:
                        wkt = row[WKTFIELD]
                        if wkt:
                            # Simplify the polygon to reduce download size
                            # & also to work around the recursion limit in libxslt
                            # http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
                            wkt = gis.simplify(wkt)
                            # Convert the WKT in XSLT
                            attr[ATTRIBUTE.wkt] = wkt

            if format == "kml":
                # GIS marker
                marker = current.gis.get_marker() # Default Marker
                # Quicker to download Icons from Static
                # also doesn't require authentication so KML files can work in
                # Google Earth
                marker_download_url = "%s/%s/static/img/markers" % \
                    (current.deployment_settings.get_base_public_url(),
                     request.application)
                marker_url = "%s/%s" % (marker_download_url, marker.image)
                attr[ATTRIBUTE.marker] = marker_url
            elif format =="gpx":
                symbol = "White Dot"
                attr[ATTRIBUTE.sym] = symbol

            # End: tablename == "gis_location"
            return

        elif len(tablename) > 19 and \
           tablename.startswith("gis_layer_shapefile"):
            # Shapefile data
            if tablename in geojsons:
                # These have been looked-up in bulk
                geojson = geojsons[tablename].get(record_id, None)
                if geojson:
                    geometry = etree.SubElement(map_data, "geometry")
                    geometry.set("value", geojson)
                    if tablename in attributes:
                        # Add Attributes
                        #_attr = ""
                        attrs = attributes[tablename][record_id]
                        #for a in attrs:
                        #    if _attr:
                        #        _attr = "%s,[%s]=[%s]" % (_attr, a, attrs[a])
                        #    else:
                        #        _attr = "[%s]=[%s]" % (a, attrs[a])
                        #if _attr:
                        #    attr[ATTRIBUTE.attributes] = _attr
                        if attrs:
                            _attr = json.dumps(attrs, separators=SEPARATORS)
                            attr[ATTRIBUTE.attributes] = _attr.replace('"', "|")
            elif tablename in wkts:
                # Nothing gets here currently
                # tbc: KML Polygons (or we should also do these outside XSLT)
                wkt = wkts[tablename][record_id]
                # Convert the WKT in XSLT
                attr[ATTRIBUTE.wkt] = wkt
            else:
                # Lookup record by record :/
                table = resource.table
                query = (table._id == record_id)
                #fields = []
                #fappend = fields.append
                #for f in table.fields:
                #    if f not in ("id", "layer_id", "lat", "lon", "wkt"):
                #        fappend(f)
                if settings.get_gis_spatialdb():
                    # Do the Simplify direct from the DB
                    #fields.remove("the_geom")
                    #_fields = [table[f] for f in fields]
                    row = db(query).select(table.the_geom.st_simplify(0.01).st_astext().with_alias("wkt"),
                                           #*_fields,
                                           limitby=(0, 1)).first()
                    if row:
                        # Convert the WKT in XSLT
                        attr[ATTRIBUTE.wkt] = row.wkt
                        # Locate the attributes
                        #row = row[tablename]
                else:
                    # _fields = [table[f] for f in fields]
                    row = db(query).select(table[WKTFIELD],
                                           #*_fields,
                                           limitby=(0, 1)).first()
                    if row:
                        wkt = row[WKTFIELD]
                        if wkt:
                            # Simplify the polygon to reduce download size
                            # & also to work around the recursion limit in libxslt
                            # http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
                            wkt = gis.simplify(wkt)
                            # Convert the WKT in XSLT
                            attr[ATTRIBUTE.wkt] = wkt

            # End: Shapefile data
            return

        # Normal Resources
        if format == "geojson":
            if tablename in geojsons:
                # These have been looked-up in bulk
                geojson = geojsons[tablename].get(record_id, None)
                if geojson:
                    geometry = etree.SubElement(map_data, "geometry")
                    geometry.set("value", geojson)

            elif tablename in latlons:
                # These have been looked-up in bulk
                LatLon = latlons[tablename].get(record_id, None)
                if LatLon:
                    lat = LatLon[0]
                    lon = LatLon[1]
                    if lat is not None and lon is not None:
                        attr[ATTRIBUTE.lat] = "%.4f" % lat
                        attr[ATTRIBUTE.lon] = "%.4f" % lon
            else:
                # Error
                raise

            if tablename in attributes:
                # Add Attributes
                #_attr = ""
                attrs = attributes[tablename][record_id]
                #for a in attrs:
                #    if _attr:
                #        _attr = "%s,[%s]=[%s]" % (_attr, a, attrs[a])
                #    else:
                #        _attr = "[%s]=[%s]" % (a, attrs[a])
                #if _attr:
                #    attr[ATTRIBUTE.attributes] = _attr
                if attrs:
                    _attr = json.dumps(attrs, separators=SEPARATORS)
                    attr[ATTRIBUTE.attributes] = _attr.replace('"', "|")

            if tablename in markers:
                _markers = markers[tablename]
                if _markers.get("image", None):
                    # Single Marker here
                    m = _markers
                else:
                    # We have a separate Marker per-Feature
                    m = _markers[record_id]
                if m:
                    # Assume being used within the Sahana Mapping client
                    # so use local URLs to keep filesize down
                    download_url = "/%s/static/img/markers" % \
                        request.application
                    attr[ATTRIBUTE.marker_url] = "%s/%s" % (download_url,
                                                            m["image"])
                    attr[ATTRIBUTE.marker_height] = str(m["height"])
                    attr[ATTRIBUTE.marker_width] = str(m["width"])
            if tablename in tooltips:
                # Retrieve the HTML for the onHover Tooltip
                tooltip = tooltips[tablename][record_id]
                if type(tooltip) is not unicode:
                    try:
                        # encode suitable for use as XML attribute
                        tooltip = tooltip.decode("utf-8")
                    except:
                        pass
                else:
                    attr[ATTRIBUTE.popup] = tooltip

            # Use the current controller for map popup URLs to get
            # the controller settings applied even for map popups
            url = URL(request.controller,
                      request.function).split(".", 1)[0]
            # Assume being used within the Sahana Mapping client
            # so use local URLs to keep filesize down
            url = "%s/%i.plain" % (url, record_id)
            attr[ATTRIBUTE.popup_url] = url
            # End: format == "geojson"
            return

        elif tablename in latlons:
            # These have been looked-up in bulk
            LatLon = latlons[tablename].get(record_id, None)
            if LatLon:
                lat = LatLon[0]
                lon = LatLon[1]
                if lat is not None and lon is not None:
                    attr[ATTRIBUTE.lat] = "%.4f" % lat
                    attr[ATTRIBUTE.lon] = "%.4f" % lon

        elif tablename in wkts:
            # Nothing gets here currently
            # tbc: KML Polygons (or we should also do these outside XSLT)
            wkt = wkts[tablename][record_id]
            # Convert the WKT in XSLT
            attr[ATTRIBUTE.wkt] = wkt

        else:
            # Lookup record by record :/
            # Nothing should get here
            return

        if tablename in markers:
            _markers = markers[tablename]
            if _markers.get("image", None):
                # Single Marker here
                m = _markers
            else:
                # We have a separate Marker per-Feature
                m = _markers[record_id]
            if m:
                if format == "gpx":
                    attr[ATTRIBUTE.sym] = m.get("gps_marker",
                                                gis.DEFAULT_SYMBOL)
                else:
                    # Assume being used outside the Sahana Mapping client
                    # so use public URLs
                    download_url = "%s/%s/static/img/markers" % \
                        (settings.get_base_public_url(), request.application)
                    attr[ATTRIBUTE.marker] = "%s/%s" % (download_url,
                                                        m["image"])

    # -------------------------------------------------------------------------
    def resource(self,
                 parent,
                 table,
                 record,
                 alias=None,
                 fields=[],
                 url=None,
                 lazy=None,
                 postprocess=None):
        """
            Creates a <resource> element from a record

            @param parent: the parent element in the document tree
            @param table: the database table
            @param record: the record
            @param alias: the resource alias (for disambiguation of components)
            @param fields: list of field names to include
            @param url: URL of the record
            @param lazy: lazy representation map
            @param postprocess: post-process hook (xml_post_render)
        """

        SubElement = etree.SubElement

        UID = self.UID
        MCI = self.MCI
        DELETED = self.DELETED

        TAG = self.TAG
        RESOURCE = TAG["resource"]
        DATA = TAG["data"]

        ATTRIBUTE = self.ATTRIBUTE
        NAME = ATTRIBUTE["name"]
        ALIAS = ATTRIBUTE["alias"]
        FIELD = ATTRIBUTE["field"]
        VALUE = ATTRIBUTE["value"]
        FILEURL = ATTRIBUTE["url"]

        tablename = table._tablename
        deleted = False

        download_url = current.response.s3.download_url or ""
        auth_group = current.auth.settings.table_group_name

        # Create the element
        if parent is not None:
            elem = SubElement(parent, RESOURCE)
        else:
            elem = etree.Element(RESOURCE)

        attrib = elem.attrib

        attrib[NAME] = tablename
        if alias:
            attrib[ALIAS] = alias

        # UID
        if UID in table.fields and UID in record:
            uid = record[UID]
            uid = str(table[UID].formatter(uid)).decode("utf-8")
            if tablename != auth_group:
                attrib[UID] = self.export_uid(uid)
            else:
                attrib[UID] = uid

        # DELETED
        if DELETED in record and record[DELETED]:
            deleted = True
            attrib[DELETED] = "True"
            # export only MTIME with deleted records
            fields = [self.MTIME]

        # Fields
        FIELDS_TO_ATTRIBUTES = self.FIELDS_TO_ATTRIBUTES

        encode_iso_datetime = self.encode_iso_datetime

        _repr = self.represent
        to_json = json.dumps

        for f in fields:

            if f == DELETED:
                continue

            v = record.get(f, None)

            if f == MCI:
                if v is None:
                    v = 0
                attrib[MCI] = str(int(v) + 1)
                continue
            
            if v is None or not hasattr(table, f):
                continue

            dbfield = ogetattr(table, f)
            fieldtype = str(dbfield.type)
            formatter = dbfield.formatter
            represent = dbfield.represent
            value = None

            if fieldtype == "datetime":
                value = encode_iso_datetime(v).decode("utf-8")
            elif fieldtype in ("date", "time") or \
                 fieldtype[:7] == "decimal":
                value = str(formatter(v)).decode("utf-8")

            # Get the representation
            is_lazy = False
            if fieldtype not in ("upload", "password", "blob"):
                if represent is not None and \
                   fieldtype != "id" and \
                   f not in ("created_on", "modified_on"):
                    if lazy is not None and hasattr(represent, "bulk"):
                        is_lazy = True
                        text = S3RepresentLazy(v, represent)
                    else:
                        text = _repr(table, f, v)

                elif value is not None:
                    text = value
                else:
                    text = s3_unicode(formatter(v))
            else:
                text = None

            if f in FIELDS_TO_ATTRIBUTES:
                if text is not None:
                    if is_lazy:
                        lazy.append((text, None, attrib, f))
                    else:
                        attrib[f] = s3_unicode(text)

            elif fieldtype == "upload":
                if v:
                    fileurl = None

                    # Retrieve the file properties
                    if dbfield.custom_retrieve_file_properties:
                        prop = dbfield.custom_retrieve_file_properties(v)
                    else:
                        prop = dbfield.retrieve_file_properties(v)
                    filename = prop["filename"]

                    # File in static (e.g. GIS marker image)?
                    folder = prop["path"]
                    if folder:
                        path = os.path.relpath(folder, current.request.folder) \
                                      .split(os.sep)
                        if path[0] == "static" and len(path) > 1:
                            path.append(filename)
                            fileurl = URL(c=path[0], f=path[1], args=path[2:])

                    # If not static - construct default download URL
                    if fileurl is None:
                        fileurl = "%s/%s" % (download_url, v)
                        
                    data = SubElement(elem, DATA)
                    attr = data.attrib
                    attr[FIELD] = f
                    attr[FILEURL] = fileurl
                    attr[ATTRIBUTE.filename] = filename

            elif fieldtype == "password":
                data = SubElement(elem, DATA)
                data.attrib[FIELD] = f
                data.text = v

            elif fieldtype == "blob":
                # Not implemented - skip
                continue

            else:
                # Create a <data> element
                data = SubElement(elem, DATA)
                attr = data.attrib
                attr[FIELD] = f
                if represent or fieldtype not in ("string", "text"):
                    if value is None:
                        value = to_json(v).decode("utf-8")
                    attr[VALUE] = value
                if is_lazy:
                    lazy.append((text, data, None, None))
                else:
                    data.text = text

        if url and not deleted:
            attrib[FILEURL] = url

        if postprocess:
            postprocess(elem, record)

        return elem

    # Data import =============================================================
    #
    @classmethod
    def select_resources(cls, tree, tablename):
        """
            Selects resources from an element tree

            @param tree: the element tree
            @param tablename: table name to search for
        """

        resources = []

        if isinstance(tree, etree._ElementTree):
            root = tree.getroot()
            if root is None or root.tag != cls.TAG.root:
                return resources
        else:
            root = tree

        if root is None or not len(root):
            return resources
        expr = './%s[@%s="%s"]' % \
               (cls.TAG.resource, cls.ATTRIBUTE.name, tablename)
        resources = root.xpath(expr)
        return resources

    # -------------------------------------------------------------------------
    @classmethod
    def components(cls, element, names=None):
        """ Selects component elements in a resource element """

        RESOURCE = cls.TAG.resource
        NAME = cls.ATTRIBUTE.name

        for child in element.iterchildren():
            if child.tag == RESOURCE:
                if names is None or child.get(NAME, None) in names:
                    yield child
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def _dtparse(dtstr, field_type="datetime"):
        """
            Helper function to parse a string into a date,
            time or datetime value (always returns UTC datetimes).

            @param dtstr: the string
            @param field_type: the field type
        """

        error = None
        value = None

        try:
            dt = S3Codec.decode_iso_datetime(str(dtstr))
            value = S3Codec.as_utc(dt)
        except:
            error = sys.exc_info()[1]
        if error is None:
            if field_type == "date":
                value = value.date()
            elif field_type == "time":
                value = value.time()
        return (value, error)

    # -------------------------------------------------------------------------
    @classmethod
    def record(cls, table, element,
               original=None,
               files=[],
               skip=[],
               postprocess=None):
        """
            Creates a record (Storage) from a <resource> element and validates
            it

            @param table: the database table
            
            @param element: the element
            @param original: the original record
            @param files: list of attached upload files
            @param postprocess: post-process hook (xml_post_parse)
            @param skip: fields to skip
        """

        valid = True
        record = Storage()

        db = current.db
        auth = current.auth
        utable = auth.settings.table_user
        gtable = auth.settings.table_group

        # Extract the UUID
        UID = cls.UID
        if UID in table.fields and UID not in skip:
            uid = current.xml.import_uid(element.get(UID, None))
            if uid:
                record[UID] = uid

        # Attribute names
        ATTRIBUTE = cls.ATTRIBUTE
        FIELD = ATTRIBUTE["field"]
        VALUE = ATTRIBUTE["value"]
        ERROR = ATTRIBUTE["error"]

        DELETED = cls.DELETED
        APPROVED = cls.APPROVED
        IGNORE_FIELDS = cls.IGNORE_FIELDS
        OGROUP = cls.OGROUP
        USER_FIELDS = (cls.CUSER, cls.MUSER, cls.OUSER)

        # Attributes
        deleted = False
        for f in cls.ATTRIBUTES_TO_FIELDS:
            
            if f == DELETED:
                if f in table and \
                   element.get(f, "false").lower() == "true":
                    record[f] = deleted = True
                    replaced_by = element.get(ATTRIBUTE["replaced_by"], None)
                    if replaced_by:
                        record[cls.REPLACEDBY] = replaced_by
                    break
                else:
                    continue
                
            if f == APPROVED:
                # Override default-approver:
                if "approved_by" in table:
                    if element.get(f, "true").lower() == "false":
                        record["approved_by"] = None
                    else:
                        if table["approved_by"].default == None:
                            auth.permission.set_default_approver(table)
                continue
            
            if f in IGNORE_FIELDS or f in skip:
                continue
            
            elif f in USER_FIELDS:
                v = element.get(f, None)
                if v and utable and "email" in utable:
                    query = (utable.email == v)
                    user = db(query).select(utable.id, limitby=(0, 1)).first()
                    if user:
                        record[f] = user.id
                continue
            
            elif f == OGROUP:
                v = element.get(f, None)
                if v and gtable and "role" in gtable:
                    query = (gtable.role == v)
                    role = db(query).select(gtable.id, limitby=(0, 1)).first()
                    if role:
                        record[f] = role.id
                continue
            
            if hasattr(table, f): # f in table.fields:
                v = value = element.get(f, None)
                if value is not None:
                    field_type = str(table[f].type)
                    if field_type in ("datetime", "date", "time"):
                        (value, error) = cls._dtparse(v,
                                                      field_type=field_type)
                    else:
                        try:
                            (value, error) = s3_validate(table, f, v, original)
                        except AttributeError:
                            # No such field
                            continue
                    if error:
                        element.set(ERROR, "%s: %s" % (f, error))
                        valid = False
                        continue
                    record[f] = value

        if deleted:
            return record

        # Fields
        xml_decode = cls.xml_decode
        for child in element.findall("data"):
            error = None
            f = child.get(FIELD, None)
            if not f or not hasattr(table, f): # f not in table.fields:
                continue
            if f in IGNORE_FIELDS or f in skip:
                continue
            field_type = str(table[f].type)
            if field_type in ("id", "blob"):
                continue
            elif field_type == "upload":
                download_url = child.get(ATTRIBUTE["url"], None)
                filename = child.get(ATTRIBUTE["filename"], None)
                upload = None
                if filename and filename in files:
                    # We already have the file cached
                    upload = files[filename]
                elif download_url == "local":
                    # File is already in-place
                    value = filename
                    # Read from the filesystem
                    # uploadfolder = table[f].uploadfolder
                    # if not uploadfolder:
                        # uploadfolder = os.path.join(current.request.folder,
                                                    # "uploads")
                    # filepath = os.path.join(uploadfolder, filename)
                    # try:
                        # upload = open(filepath, r)
                    # except IOError:
                        # continue
                elif download_url:
                    # Download file from Internet
                    if not filename:
                        try:
                            filename = download_url.split("?")[0]
                        except:
                            # Fake filename as fallback
                            filename = "upload.bin"
                    try:
                        upload = urllib2.urlopen(download_url)
                    except IOError:
                        continue
                if upload:
                    field = table[f]
                    value = field.store(upload, filename)
                elif download_url != "local":
                    continue
            else:
                value = child.get(VALUE, None)

            skip_validation = False
            is_text = field_type in ("string", "text")

            if value is None:
                decode_value = not is_text
                if field_type == "password":
                    value = child.text
                    # Do not re-encrypt the password if it already
                    # comes encrypted:
                    skip_validation = True
                else:
                    value = xml_decode(child.text)
            else:
                decode_value = True

            if value is None and is_text:
                value = ""
            elif value == "" and not is_text:
                value = None

            if value is not None:
                if field_type in ("datetime", "date", "time"):
                    (value, error) = cls._dtparse(value,
                                                  field_type=field_type)
                    skip_validation = True
                    v = value
                elif field_type == "upload":
                    pass
                elif isinstance(value, basestring) \
                     and len(value) \
                     and decode_value:
                    try:
                        _value = json.loads(value)
                        if _value != float("inf"):
                            # e.g. an HTML_COLOUR of 98E600
                            value = _value
                    except:
                        error = sys.exc_info()[1]

                if not skip_validation:
                    if not isinstance(value, (basestring, list, tuple)):
                        v = str(value)
                    elif isinstance(value, basestring):
                        v = value.encode("utf-8")
                    else:
                        v = value
                    filename = None
                    try:
                        if field_type == "upload" and \
                           download_url != "local" and \
                           table[f].requires:
                            filename, stream = field.retrieve(value)
                            v = filename
                            if isinstance(stream, basestring):
                                # Regular file in file system => try open
                                stream = open(stream, "rb")
                            if not error:
                                dummy = Storage({"filename": filename,
                                                 "file": stream})
                                (dummy, error) = s3_validate(table, f, dummy, original)
                        elif field_type == "password":
                            v = value
                            (value, error) = s3_validate(table, f, v)
                        else:
                            (value, error) = s3_validate(table, f, v, original)
                    except AttributeError:
                        # No such field
                        continue
                    except IOError:
                        if filename:
                            error = "Cannot read uploaded file: %s" % filename
                        else:
                            error = sys.exc_info()[1]
                    except:
                        error = sys.exc_info()[1]

                child.set(VALUE, s3_unicode(v))
                if error:
                    child.set(ERROR, "%s: %s" % (f, error))
                    valid = False
                    continue

                record[f] = value

        if valid:
            if postprocess:
                postprocess(element, record)
            return record
        else:
            return None

    # Data model helpers ======================================================
    #
    @classmethod
    def get_field_options(cls, table, fieldname, parent=None, show_uids=False):
        """
            Get options of a field as <select>

            @param table: the table
            @param fieldname: the fieldname
            @param parent: the parent element in the tree
        """

        options = []
        if fieldname in table.fields:
            field = table[fieldname]
            requires = field.requires
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            if requires:
                r = requires[0]
                if isinstance(r, IS_EMPTY_OR):
                    r = r.other
                try:
                    options = r.options()
                except:
                    pass

        TAG = cls.TAG
        if options:
            ATTRIBUTE = cls.ATTRIBUTE
            SubElement = etree.SubElement
            if parent is not None:
                select = SubElement(parent, TAG.select)
            else:
                select = etree.Element(TAG.select)
            select.set(ATTRIBUTE.name, fieldname)
            select.set(ATTRIBUTE.id,
                       "%s_%s" % (table._tablename, fieldname))

            uids = Storage()
            if show_uids:
                ftype = str(field.type)
                if ftype[:9] == "reference":
                    ktablename = ftype[10:]
                    try:
                        ktable = current.s3db[ktablename]
                    except:
                        pass
                    else:
                        ids = [o[0] for o in options]
                        if ids and cls.UID in ktable.fields:
                            query = ktable._id.belongs(ids)
                            rows = current.db(query).select(ktable._id, ktable[cls.UID])
                            uids = Storage((str(r[ktable._id.name]), r[cls.UID])
                                        for r in rows)

            _XML = etree.XML
            OPTION = TAG.option
            VALUE = ATTRIBUTE.value
            for (value, text) in options:
                if show_uids and str(value) in uids:
                    uid = uids[str(value)]
                else:
                    uid = None
                value = s3_unicode(value)
                try:
                    markup = _XML(s3_unicode(text))
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                except:
                    pass
                text = s3_unicode(text)
                option = SubElement(select, OPTION)
                option.set(VALUE, value)
                if uid:
                    option.set(cls.UID, uid)
                option.text = text
        elif parent is not None:
            return None
        else:
            return etree.Element(TAG.select)

        return select

    # -------------------------------------------------------------------------
    def get_options(self, prefix, name, fields=None, show_uids=False):
        """
            Get options of option fields in a table as <select>s

            @param prefix: the application prefix
            @param name: the resource name (without prefix)
            @param fields: optional list of fieldnames
        """

        db = current.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        options = etree.Element(self.TAG.options)

        if fields:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            if len(fields) == 1:
                return(self.get_field_options(table, fields[0],
                                              show_uids=show_uids))

        if table:
            options.set(self.ATTRIBUTE.resource, tablename)
            get_field_options = self.get_field_options
            for f in table.fields:
                if fields and f not in fields:
                    continue
                select = get_field_options(table, f,
                                           parent=options,
                                           show_uids=show_uids)

        return options

    # -------------------------------------------------------------------------
    def get_fields(self, prefix, name,
                   parent=None,
                   meta=False,
                   options=False,
                   references=False,
                   labels=False):
        """
            Get fields in a table as <fields> element

            @param prefix: the application prefix
            @param name: the resource name (without prefix)
            @param parent: the parent element to append the tree to
            @param options: include option lists in option fields
            @param references: include option lists even in reference fields
        """

        db = current.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        if parent is not None:
            fields = parent
        else:
            fields = etree.Element(self.TAG.fields)
        if table:
            ATTRIBUTE = self.ATTRIBUTE
            if parent is None:
                fields.set(ATTRIBUTE.resource, tablename)
            for f in table.fields:
                ftype = str(table[f].type)
                # Skip own super links
                if ftype[:9] == "reference":
                    ktablename = ftype[10:]
                    s = current.s3db.get_config(tablename, "super_entity")
                    if not isinstance(s, (list, tuple)):
                        s = [s]
                    if ktablename in s:
                        continue
                if f in self.IGNORE_FIELDS or ftype == "id":
                    continue
                if f in self.FIELDS_TO_ATTRIBUTES:
                    if not meta:
                        continue
                    tag = self.TAG.meta
                else:
                    tag = self.TAG.field
                readable = table[f].readable
                writable = table[f].writable
                field = etree.SubElement(fields, tag)
                if options:
                    p = field
                    if not references and \
                       ftype[:9] in ("reference", "list:refe"):
                        p = None
                else:
                    p = None
                opts = self.get_field_options(table, f, parent=p)
                set_attribute = field.set
                set_attribute(ATTRIBUTE.name, f)
                set_attribute(ATTRIBUTE.type, ftype)
                set_attribute(ATTRIBUTE.readable, str(readable))
                set_attribute(ATTRIBUTE.writable, str(writable))
                has_options = str(opts is not None and
                                  len(opts) and True or False)
                set_attribute(ATTRIBUTE.has_options, has_options)
                if labels:
                    label = s3_unicode(table[f].label)
                    set_attribute(ATTRIBUTE.label, label)
                    comment = table[f].comment
                    if comment:
                        comment = s3_unicode(comment)
                    if comment and "<" in comment:
                        try:
                            stripper = S3MarkupStripper()
                            stripper.feed(comment)
                            comment = stripper.stripped()
                        except Exception:
                            current.log.error(sys.exc_info()[1])
                    if comment:
                        set_attribute(ATTRIBUTE.comment, comment)
        return fields

    # -------------------------------------------------------------------------
    def get_struct(self, prefix, name,
                   alias=None,
                   parent=None,
                   meta=False,
                   options=True,
                   references=False):
        """
            Get the table structure as XML tree

            @param prefix: the application prefix
            @param name: the tablename (without prefix)
            @param parent: the parent element to append the tree to
            @param options: include option lists in option fields
            @param references: include option lists even in reference fields

            @raise AttributeError: in case the table doesn't exist
        """

        db = current.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        if table is not None:
            if parent is not None:
                e = etree.SubElement(parent, self.TAG.resource)
            else:
                e = etree.Element(self.TAG.resource)
            e.set(self.ATTRIBUTE.name, tablename)
            if alias and alias != name:
                e.set(self.ATTRIBUTE.alias, alias)
            self.get_fields(prefix, name,
                            parent=e,
                            meta=meta,
                            options=options,
                            references=references,
                            labels=True)
            return e
        else:
            raise AttributeError("No table like %s" % tablename)

    # JSON toolkit ============================================================
    #
    @classmethod
    def __json2element(cls, key, value, native=False):
        """
            Converts a data field from JSON into an element

            @param key: key (field name)
            @param value: value for the field
            @param native: use native mode
            @type native: bool
        """

        if isinstance(value, dict):
            return cls.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key == cls.TAG.item:
                _list = etree.Element(key)
            else:
                _list = etree.Element(cls.TAG.list)
            for obj in value:
                item = cls.__json2element(cls.TAG.item, obj,
                                           native=native)
                _list.append(item)
            return _list

        else:
            if native:
                element = etree.Element(cls.TAG.data)
                element.set(cls.ATTRIBUTE.field, key)
            else:
                element = etree.Element(key)
            if not isinstance(value, (str, unicode)):
                value = str(value)
            element.text = value
            return element

    # -------------------------------------------------------------------------
    @classmethod
    def __obj2element(cls, tag, obj, native=False):
        """
            Converts a JSON object into an element

            @param tag: tag name for the element
            @param obj: the JSON object
            @param native: use native mode for attributes
        """

        resource = field = None

        if not tag:
            tag = cls.TAG.object

        elif native:
            if tag.startswith(cls.PREFIX.reference):
                field = tag[len(cls.PREFIX.reference) + 1:]
                tag = cls.TAG.reference
            elif tag.startswith(cls.PREFIX.options):
                resource = tag[len(cls.PREFIX.options) + 1:]
                tag = cls.TAG.options
            elif tag.startswith(cls.PREFIX.resource):
                resource = tag[len(cls.PREFIX.resource) + 1:]
                tag = cls.TAG.resource
            elif not tag == cls.TAG.root:
                field = tag
                tag = cls.TAG.data

        element = etree.Element(tag)

        if native:
            if resource:
                if tag == cls.TAG.resource:
                    element.set(cls.ATTRIBUTE.name, resource)
                else:
                    element.set(cls.ATTRIBUTE.resource, resource)
            if field:
                element.set(cls.ATTRIBUTE.field, field)

        for k in obj:
            m = obj[k]
            if isinstance(m, dict):
                child = cls.__obj2element(k, m, native=native)
                element.append(child)
            elif isinstance(m, (list, tuple)):
                #l = etree.SubElement(element, k)
                for _obj in m:
                    child = cls.__json2element(k, _obj, native=native)
                    element.append(child)
            else:
                if k == cls.PREFIX.text:
                    element.text = m
                elif k.startswith(cls.PREFIX.attribute):
                    a = k[len(cls.PREFIX.attribute):]
                    element.set(a, m)
                else:
                    child = cls.__json2element(k, m, native=native)
                    element.append(child)

        return element

    # -------------------------------------------------------------------------
    @classmethod
    def json2tree(cls, source, format=None):
        """
            Converts JSON into an element tree

            @param source: the JSON source
            @param format: name of the XML root element
        """

        try:
            root_dict = json.load(source)
        except (ValueError, ):
            e = sys.exc_info()[1]
            raise HTTP(400, body=cls.json_message(False, 400, e))

        native=False

        if not format:
            format = cls.TAG.root
            native = True

        if root_dict and isinstance(root_dict, dict):
            root = cls.__obj2element(format, root_dict, native=native)
            if root is not None:
                return etree.ElementTree(root)

        return None

    # -------------------------------------------------------------------------
    @classmethod
    def __element2json(cls, element, native=False):
        """
            Converts an element into JSON

            @param element: the element
            @param native: use native mode for attributes
        """

        TAG = cls.TAG
        ATTRIBUTE = cls.ATTRIBUTE
        PREFIX = cls.PREFIX

        element2json = cls.__element2json

        if element.tag == TAG.list:
            obj = []
            append = obj.append
            for child in element:
                tag = child.tag
                if not isinstance(tag, basestring):
                    continue # skip comment nodes
                if tag[0] == "{":
                    tag = tag.rsplit("}", 1)[1]
                child_obj = element2json(child, native=native)
                if child_obj:
                    append(child_obj)
            return obj
        else:
            obj = {}
            iterchildren = element.iterchildren
            xpath = element.xpath
            is_single = lambda t, a, v: len(xpath("%s[@%s='%s']" % (t, a, v))) == 1
            for child in iterchildren(tag=etree.Element):
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}", 1)[1]
                collapse = True
                single = False
                attributes = child.attrib
                if native:
                    if tag == TAG.resource:
                        resource = attributes[ATTRIBUTE.name]
                        tag = "%s_%s" % (PREFIX.resource, resource)
                        collapse = False
                    elif tag == TAG.options:
                        r = attributes[ATTRIBUTE.resource]
                        tag = "%s_%s" % (PREFIX.options, r)
                        single = is_single(TAG.options, ATTRIBUTE.resource, r)
                    elif tag == TAG.reference:
                        f = attributes[ATTRIBUTE.field]
                        tag = "%s_%s" % (PREFIX.reference, f)
                        single = is_single(TAG.reference, ATTRIBUTE.field, f)
                    elif tag == TAG.data:
                        tag = attributes[ATTRIBUTE.field]
                        single = is_single(TAG.data, ATTRIBUTE.field, tag)
                else:
                    for s in iterchildren(tag=tag):
                        if single is True:
                            single = False
                            break
                        else:
                            single = True
                child_obj = element2json(child, native=native)
                if child_obj:
                    if tag not in obj:
                        if single and collapse:
                            obj[tag] = child_obj
                        else:
                            obj[tag] = [child_obj]
                    else:
                        if type(obj[tag]) is not list:
                            obj[tag] = [obj[tag]]
                        obj[tag].append(child_obj)

            attributes = element.attrib
            skip_text = False
            tag = element.tag
            numeric = False
            for a in attributes:
                v = attributes[a]
                if native:
                    if a == ATTRIBUTE.name and tag == TAG.resource:
                        continue
                    if a == ATTRIBUTE.resource and tag == TAG.options:
                        continue
                    if a == ATTRIBUTE.field and tag in (TAG.data, TAG.reference):
                        continue
                    if a == ATTRIBUTE.value:
                        try:
                            v = json.loads(v)
                        except:
                            pass
                else:
                    if a == ATTRIBUTE.value:
                        try:
                            obj[TAG.item] = json.loads(v)
                        except:
                            pass
                        else:
                            skip_text = True
                        continue
                    elif a == ATTRIBUTE.type and v == "numeric":
                        numeric = True
                        continue
                obj[PREFIX.attribute + a] = v

            if element.text and not skip_text:
                represent = cls.xml_decode(element.text)
                if numeric:
                    # Value should be a number not string
                    try:
                        float_represent = float(represent.replace(",", ""))
                        int_represent = int(float_represent)
                        if int_represent == float_represent:
                            represent = int_represent
                        else:
                            represent = float_represent
                    except:
                        # @ToDo: Don't assume this i18n formatting...
                        pass
                obj[PREFIX.text] = represent

            if len(obj) == 1 and obj.keys()[0] in \
               (PREFIX.text, TAG.item, TAG.list):
                obj = obj[obj.keys()[0]]

            return obj

    # -------------------------------------------------------------------------
    @classmethod
    def tree2json(cls, tree, pretty_print=False, native=False):
        """
            Converts an element tree into JSON

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output
        """

        if isinstance(tree, etree._ElementTree):
            root = tree.getroot()
        else:
            root = tree

        if native or root.tag == cls.TAG.root:
            native = True
        else:
            native = False

        root_dict = cls.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return "\n".join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    @staticmethod
    def collect_errors(job):
        """
            Collect errors from an error tree

            @param job: the import job, resource or error tree as Element
        """

        errors = []

        try:
            if isinstance(job, etree._Element):
                error_tree = job
            else:
                error_tree = job.error_tree
        except AttributeError:
            return errors
        if error_tree is None:
            return errors

        elements = error_tree.xpath(".//*[@error]")
        for element in elements:
            get = element.get
            if element.tag == "data":
                resource = element.getparent()
                value = get("value")
                if not value:
                    value = element.text
                error = "%s, %s: '%s' (value='%s')" % (
                            resource.get("name", None),
                            get("field", None),
                            get("error", None),
                            value)
            if element.tag == "reference":
                resource = element.getparent()
                error = "%s, %s: '%s'" % (
                            resource.get("name", None),
                            get("field", None),
                            get("error", None))
            elif element.tag == "resource":
                error = "%s: %s" % (get("name", None),
                                    get("error", None))
            else:
                error = "%s" % get("error", None)
            errors.append(error)
        return errors

    # -------------------------------------------------------------------------
    @classmethod
    def xls2tree(cls, source,
                 resourcename=None,
                 extra_data=None,
                 sheet=None,
                 rows=None,
                 cols=None,
                 fields=None,
                 header_row=True):
        """
            Convert a table in an XLS (MS Excel) sheet into an ElementTree,
            consisting of <table name="format">, <row> and
            <col field="fieldname"> elements (see: L{csv2tree}).

            The returned ElementTree can be imported using S3CSV
            stylesheets (through S3Resource.import_xml()).

            @param source: the XLS source (stream, or XLRD book, or
                           None if sheet is an open XLRD sheet)
            @param resourcename: the resource name
            @param extra_data: dict of extra cols to add to each row
            @param sheet: sheet name or index, or an open XLRD sheet
                          (open work sheet overrides source)
            @param rows: Rows range, integer (length from 0) or
                         tuple (start, length) - or a tuple (start,) to
                         read all available rows after start
            @param cols: Columns range, like "rows"
            @param fields: Field map, a dict {index: fieldname} where
                           index is the column index counted from the
                           first column within the specified range,
                           e.g. cols=(2,7), fields={1:"MyField"}
                           means column 3 in the sheet is "MyField",
                           the field map can be omitted to read the field
                           names from the sheet (see "header_row")
            @param header_row: the first row contains column headers
                               (if fields is None, they will be used
                               as field names in the output - otherwise
                               they will be ignored)
            @return: an etree.ElementTree representing the table
        """

        import xlrd
        
        # Shortcuts
        ATTRIBUTE = cls.ATTRIBUTE
        FIELD = ATTRIBUTE.field
        TAG = cls.TAG
        COL = TAG.col
        SubElement = etree.SubElement

        DEFAULT_SHEET_NAME = "SahanaData"

        # Root element
        root = etree.Element(TAG.table)
        if resourcename is not None:
            root.set(ATTRIBUTE.name, resourcename)

        if isinstance(sheet, xlrd.sheet.Sheet):
            # Open work sheet passed as argument => use this
            s = sheet
        else:
            if hasattr(source, "read"):
                # Source is a stream
                if hasattr(source, "seek"):
                    source.seek(0)
                wb = xlrd.open_workbook(file_contents=source.read(),
                                        # requires xlrd 0.7.x or higher
                                        on_demand=True)
            elif isinstance(source, xlrd.book.Book):
                # Source is an open work book
                wb = source
            else:
                # Unsupported source type
                raise RuntimeError("xls2tree: invalid source %s" %
                                   type(source))

            # Find the sheet
            try:
                if isinstance(sheet, (int, long)):
                    s = wb.sheet_by_index(sheet)
                elif isinstance(sheet, basestring):
                    s = wb.sheet_by_name(sheet)
                elif sheet is None:
                    if DEFAULT_SHEET_NAME in wb.sheet_names():
                        s = wb.sheet_by_name(DEFAULT_SHEET_NAME)
                    else:
                        s = wb.sheet_by_index(0)
                else:
                    raise SyntaxError("xls2tree: invalid sheet %s" % sheet)
            except IndexError, xlrd.XLRDError:
                s = None

        def cell_range(cells, max_cells):
            """
                Helper method to calculate a cell range

                @param cells: the specified range
                @param max_cells: maximum number of cells
            """
            if not cells:
                cells = (0, max_cells)
            elif not isinstance(cells, (tuple, list)):
                cells = (0, cells)
            elif len(cells) == 1:
                cells = (cells[0], max_cells)
            else:
                cells = (cells[0], cells[0] + cells[1])
            return cells

        if s:
            # Calculate cell range
            rows = cell_range(rows, s.nrows)
            cols = cell_range(cols, s.ncols)

            # Column headers
            if fields:
                headers = fields
            elif not header_row:
                headers = dict((i, "%s" % i)
                               for i in range(cols[1]- cols[0]))
            else:
                # Use header row in the work sheet
                headers = {}

            # Lambda to decode XLS dates into an ISO datetime-string
            decode_date = lambda v: datetime.datetime(
                                    *xlrd.xldate_as_tuple(v, wb.datemode))
                                    
            encode_iso_datetime = cls.encode_iso_datetime
            def decode(t, v):
                """
                    Helper method to decode the cell value by type

                    @param t: the cell type
                    @param v: the cell value
                    @return: text representation of the cell value
                """
                text = ""
                if v:
                    if t is None:
                        text = s3_unicode(v).strip()
                    elif t == xlrd.XL_CELL_TEXT:
                        text = v.strip()
                    elif t == xlrd.XL_CELL_NUMBER:
                        text = str(long(v)) if long(v) == v else str(v)
                    elif t == xlrd.XL_CELL_DATE:
                        text = encode_iso_datetime(decode_date(v))
                    elif t == xlrd.XL_CELL_BOOLEAN:
                        text = str(value).lower()
                return text

            def add_col(row, name, t, v):
                """
                    Helper method to add a column to an output row

                    @param row: the output row (etree.Element)
                    @param name: the column name
                    @param t: the cell type
                    @param v: the cell value
                """
                col = SubElement(row, COL)
                col.set(FIELD, name)
                col.text = decode(t, v)

            # Process the rows
            ROW = TAG.row
            record_idx = 0
            extra_fields = set(extra_data) if extra_data else None
            check_headers = extra_fields is not None
            for ridx in range(*rows):
                # Read types and values
                types = s.row_types(ridx, *cols)
                values = s.row_values(ridx, *cols)
                
                if header_row and record_idx == 0:
                    # Read column headers
                    if not fields:
                        for cidx, value in enumerate(values):
                            header = decode(types[cidx], value)
                            headers[cidx] = header
                            if check_headers:
                                extra_fields.discard(header)
                        check_headers = False
                else:
                    # Add output row
                    orow = SubElement(root, ROW)
                    for cidx, name in headers.items():
                        if check_headers:
                            extra_fields.discard(name)
                        try:
                            t = types[cidx]
                            v = values[cidx]
                        except IndexError:
                            pass
                        else:
                            add_col(orow, name, t, v)
                    check_headers = False
                            
                    # Add extra data
                    if extra_fields:
                        for key in extra_fields:
                            add_col(orow, key, None, extra_data[key])
                record_idx += 1

        return  etree.ElementTree(root)
        
    # -------------------------------------------------------------------------
    @classmethod
    def csv2tree(cls, source,
                 resourcename=None,
                 extra_data=None,
                 delimiter=",",
                 quotechar='"'):
        """
            Convert a table-form CSV source into an element tree, consisting of
            <table name="format">, <row> and <col field="fieldname"> elements.

            @param source: the source (file-like object)
            @param resourcename: the resource name
            @param extra_data: dict of extra cols to add to each row
            @param delimiter: delimiter for values
            @param quotechar: quotation character

            @todo: add a character encoding parameter to skip the guessing
        """

        import csv

        # Increase field sixe to be able to import WKTs
        csv.field_size_limit(2**20 * 100)  # 100 megs

        # Shortcuts
        ATTRIBUTE = cls.ATTRIBUTE
        FIELD = ATTRIBUTE.field
        TAG = cls.TAG
        COL = TAG.col
        SubElement = etree.SubElement

        root = etree.Element(TAG.table)
        if resourcename is not None:
            root.set(ATTRIBUTE.name, resourcename)

        def add_col(row, key, value):
            col = SubElement(row, COL)
            col.set(FIELD, s3_unicode(key))
            if value:
                text = s3_unicode(value).strip()
                if text.lower() not in ("null", "<null>"):
                    col.text = text
            else:
                col.text = ""

        def utf_8_encode(source):
            """
                UTF-8-recode the source line by line, guessing the character
                encoding of the source.
            """
            # Make this a list of all encodings you need to support (as long as
            # they are supported by Python codecs), always starting with the most
            # likely.
            encodings = ["utf-8-sig", "iso-8859-1"]
            e = encodings[0]
            for line in source:
                if e:
                    try:
                        yield unicode(line, e, "strict").encode("utf-8")
                    except:
                        pass
                    else:
                        continue
                for encoding in encodings:
                    try:
                        yield unicode(line, encoding, "strict").encode("utf-8")
                    except:
                        continue
                    else:
                        e = encoding
                        break
        try:
            import StringIO
            if not isinstance(source, StringIO.StringIO):
                source = utf_8_encode(source)
            reader = csv.DictReader(source,
                                    delimiter=delimiter,
                                    quotechar=quotechar)
            ROW = TAG.row
            for r in reader:
                row = SubElement(root, ROW)
                for k in r:
                    add_col(row, k, r[k])
                if extra_data:
                    for key in extra_data:
                        if key not in r:
                            add_col(row, key, extra_data[key])
        except csv.Error:
            e = sys.exc_info()[1]
            raise HTTP(400, body=cls.json_message(False, 400, e))

        # Use this to debug the source tree if needed:
        #print >>sys.stderr, cls.tostring(root, pretty_print=True)

        return  etree.ElementTree(root)

# =============================================================================
class S3XMLFormat(object):
    """ Helper class to store a pre-parsed stylesheet """

    def __init__(self, stylesheet):
        """
            Constructor

            @param stylesheet: the stylesheet (pathname or stream)
        """

        self.tree = current.xml.parse(stylesheet)
        if not self.tree:
            current.log.error("%s parse error: %s" %
                              (stylesheet, current.xml.error))
        
        self.select = None
        self.skip = None

    # -------------------------------------------------------------------------
    def get_fields(self, tablename):
        """
            Get the fields to include/exclude for the specified table.

            @param tablename: the tablename
            @return: tuple of lists (include, exclude) of fields to
                     include or exclude. None indicates "all fields",
                     whereas an empty list indicates "no fields".
        """

        ANY = "ANY"
        default = (None, None)

        tree = self.tree
        if not tree:
            return default

        if self.select is None:
            self.__inspect()

        def find_match(items, tablename, default):

            if tablename in items:
                match = items[tablename]
            else:
                match = False
                maxlen = 0
                for tn, fields in items.iteritems():
                    if "*" in tn:
                        m = re.match(tn.replace("*", ".*"), tablename)
                        if not m:
                            continue
                        l = m.span()[-1]
                        if l > maxlen:
                            match = fields
                if match is False:
                    match = items.get(ANY, default)
            return match

        select = find_match(self.select, tablename, None)
        skip = find_match(self.skip, tablename, set())
        
        if skip:
            if select:
                include = [fn for fn in select if fn not in skip]
                exclude = [fn for fn in skip if fn not in select]
            else:
                include = None
                exclude = list(skip)
        else:
            include = list(select) if select else None
            exclude = []
        return (include, exclude)

    # -------------------------------------------------------------------------
    def __inspect(self):
        """ Check the fields configuration in the stylesheet (if any) """

        ALL = "ALL"
        ANY = "ANY"

        tree = self.tree

        ns = {"s3": "http://eden.sahanafoundation.org/wiki/S3"}
        elements = tree.xpath("./s3:fields", namespaces=ns)

        select = {}
        skip = {}

        for element in elements:
            tables = element.get("tables", ANY).split(",")

            fields = element.get("select", None)
            if fields is not None and fields != ALL:
                fields = set([f.strip() for f in fields.split(",")])
                
            exclude = element.get("exclude", None)
            if exclude is not None:
                exclude = set([f.strip() for f in exclude.split(",")])

            for table in tables:
                tablename = table.strip()
                if fields:
                    select[tablename] = None if fields == ALL else fields
                if exclude:
                    skip[tablename] = exclude
                
        self.select = select
        self.skip = skip
        return

    # -------------------------------------------------------------------------
    def transform(self, tree, **args):
        """
            Transform an element tree using this format

            @param tree: the element tree
            @param args: parameters for the stylesheet
        """

        if not self.tree:
            current.log.error("XMLFormat: no stylesheet available")
            return tree

        return current.xml.transform(tree, self.tree, **args)

# End =========================================================================
