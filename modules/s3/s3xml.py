# -*- coding: utf-8 -*-

"""
    S3XML Toolkit

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3XML"]

import os
import sys
import csv
import datetime
import urllib2

from gluon import *
from gluon.storage import Storage
import gluon.contrib.simplejson as json

from s3codec import S3Codec
from s3track import S3Trackable

try:
    from lxml import etree
except ImportError:
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

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
            "owned_by_organisation",
            "owned_by_entity"]

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
            DELETED]

    ATTRIBUTES_TO_FIELDS = [
            "admin",
            CUSER,
            MUSER,
            OGROUP,
            OUSER,
            CTIME,
            MTIME,
            MCI,
            DELETED]

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
        col="col")

    ATTRIBUTE = Storage(
        id="id",
        name="name",
        table="table",
        field="field",
        value="value",
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
        shape="shape",  # for GIS Feature Queries
        size="size",    # for GIS Feature Queries
        colour="colour",# for GIS Feature Queries
        popup="popup",  # for GIS Feature Layers/Queries
        sym="sym",      # For GPS
        type="type",
        readable="readable",
        writable="writable",
        wkt="wkt",
        has_options="has_options",
        tuid="tuid",
        label="label",
        comment="comment")

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete")

    PREFIX = Storage(
        resource="$",
        options="$o",
        reference="$k",
        attribute="@",
        text="$")

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        manager = current.manager

        self.domain = manager.domain
        self.error = None

        self.filter_mci = False # Set to true to suppress export at MCI<0

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
            _args = [(k, "'%s'" % args[k]) for k in args]
            _args = dict(_args)
        else:
            _args = None
        stylesheet = self.parse(stylesheet_path)

        if stylesheet:
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
                desc.text = self.xml_encode(contentDescription)
            from copy import deepcopy
            obj.append(deepcopy(contentObject))
        return self.transform(root, stylesheet_path, **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def tostring(tree, xml_declaration=True, pretty_print=False):
        """
            Convert an element tree into XML as string

            @param tree: the element tree
            @param xml_declaration: add an XML declaration to the output
            @param pretty_print: provide pretty formatted output
        """

        return etree.tostring(tree,
                              xml_declaration=xml_declaration,
                              encoding="utf-8",
                              pretty_print=True)

    # -------------------------------------------------------------------------
    def tree(self, elements,
             root=None,
             domain=None,
             url=None,
             start=None,
             limit=None,
             results=None):
        """
            Builds a S3XML tree from a list of elements

            @param elements: list of <resource> elements
            @param root: the root element to link the tree to
            @param domain: name of the current domain
            @param url: url of the request
            @param start: the start record (in server-side pagination)
            @param limit: the page size (in server-side pagination)
            @param results: number of total available results
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
        set = root.set
        set(ATTRIBUTE.success, json.dumps(success))
        if start is not None:
            set(ATTRIBUTE.start, str(start))
        if limit is not None:
            set(ATTRIBUTE.limit, str(limit))
        if results is not None:
            set(ATTRIBUTE.results, str(results))
        if elements is not None:
            root.extend(elements)
        if domain:
            set(ATTRIBUTE.domain, self.domain)
        if url:
            set(ATTRIBUTE.url, current.response.s3.base_url)
        # @ToDo: This should be done based on the features, not just the config
        bounds = current.gis.get_bounds()
        set(ATTRIBUTE.latmin,
            str(bounds["min_lat"]))
        set(ATTRIBUTE.latmax,
            str(bounds["max_lat"]))
        set(ATTRIBUTE.lonmin,
            str(bounds["min_lon"]))
        set(ATTRIBUTE.lonmax,
            str(bounds["max_lon"]))
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
            represent = current.manager.represent(table[f],
                                                  value=v,
                                                  strip_markup=True,
                                                  xml_escape=True)
        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_user(user_id):
        db = current.db
        cache = current.cache
        auth = current.auth
        utable = auth.settings.table_user
        user = None
        if "email" in utable:
            user = db(utable.id == user_id).select(utable.email,
                                                   limitby=(0, 1)).first()
        if user:
            return user.email
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def represent_role(role_id):
        db = current.db
        cache = current.cache
        auth = current.auth
        gtable = auth.settings.table_group
        role = None
        if "role" in gtable:
            role = db(gtable.id == role_id).select(
                        gtable.role,
                        limitby=(0, 1),
                        cache=(cache.ram, S3XML.CACHE_TTL)).first()
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

        db = current.db
        reference_map = []

        UID = self.UID
        MCI = self.MCI
        DELETED = self.DELETED

        export_uid = self.export_uid
        xml_encode = self.xml_encode
        represent = self.represent
        filter_mci = self.filter_mci
        tablename = table._tablename
        gtablename = current.auth.settings.table_group_name

        for f in fields:
            if f not in record:
                continue
            val = ids = record[f]
            if type(ids) is not list:
                ids = [ids]
            multiple = False
            fieldtype = str(table[f].type)
            if fieldtype[:9] == "reference":
                ktablename = fieldtype[10:]
            elif fieldtype[:14] == "list:reference":
                ktablename = fieldtype[15:]
                multiple = True
            else:
                continue
            ktable = db[ktablename]
            ktable_fields = ktable.fields
            k_id = ktable._id
            pkey = k_id.name

            if multiple:
                query = k_id.belongs(ids)
                limitby = None
            else:
                query = k_id == ids[0]
                limitby = (0, 1)

            uid = None
            uids = None
            supertable = None
            if pkey != "id" and "instance_type" in ktable_fields:
                if multiple:
                    continue
                krecord = db(query).select(ktable[UID],
                                           ktable.instance_type,
                                           limitby=(0, 1)).first()
                if not krecord:
                    continue
                ktablename = krecord.instance_type
                uid = krecord[UID]
                if ktablename == tablename and \
                   UID in record and record[UID] == uid:
                    continue
                uids = [uid]
            else:
                if DELETED in ktable_fields:
                    query = (ktable.deleted != True) & query
                if filter_mci and MCI in ktable_fields:
                    query = (ktable.mci >= 0) & query
                if UID in ktable_fields:
                    krecords = db(query).select(ktable[UID], limitby=limitby)
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
            value = str(table[f].formatter(val)).decode("utf-8")
            if table[f].represent:
                text = represent(table, f, val)
            else:
                text = xml_encode(value)
            entry = {"field":f,
                     "table":ktablename,
                     "multiple":multiple,
                     "id":ids,
                     "uid":uids,
                     "text":text,
                     "value":value}
            reference_map.append(Storage(entry))
        return reference_map

    # -------------------------------------------------------------------------
    def add_references(self, element, rmap, show_ids=False):
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
        UID = self.UID
        ID = ATTRIBUTE.id
        VALUE = ATTRIBUTE.value

        as_json = json.dumps
        SubElement = etree.SubElement

        for i in xrange(0, len(rmap)):
            r = rmap[i]
            reference = SubElement(element, REFERENCE)
            attr = reference.attrib
            attr[FIELD] = r.field
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
                reference.text = r.text
            else:
                attr[VALUE] = r.value
            r.element = reference

    # -------------------------------------------------------------------------
    def gis_encode(self,
                   resource,
                   record,
                   element,
                   rmap,
                   download_url="",
                   marker=None,
                   ):
        """
            GIS-encodes location references

            @param resource: the referencing resource
            @param record: the particular record
            @param element: the XML element
            @param rmap: list of references to encode
            @param download_url: download URL of this instance
            @param marker: marker dict or filename
            @param shape: shape as alternative to marker
            @param size: size of shape
            @param colour: colour of shape
            @param popup_url:  URL used for onClick Popup contents
        """

        gis = current.gis

        if not gis:
            return

        db = current.db
        s3db = current.s3db

        LATFIELD = self.Lat
        LONFIELD = self.Lon
        WKTFIELD = self.WKT

        ATTRIBUTE = self.ATTRIBUTE

        # Quicker to download Icons from Static
        # also doesn't require authentication so KML files can work in
        # Google Earth
        # @ToDo: Remove the Public URL to keep filesize small when
        # loading off same server? (GeoJSON &layer=xx)
        download_url = download_url.replace("default/download",
                                            "static/img/markers")

        _marker = None
        marker_url = None
        symbol = gis.DEFAULT_SYMBOL
        popup_label = None
        popup_fields = None
        popup_url = None
        if marker:
            try:
                # Dict
                _marker = marker["marker"]
                if _marker:
                    marker_url = "%s/%s" % (download_url, _marker)
                symbol = marker["gps_marker"] or symbol
                popup_label = marker["popup_label"]
                popup_fields = marker["popup_fields"]
            except:
                # String
                marker_url = "%s/gis_marker.image.%s.png" % (download_url, marker)

        table = resource.table
        tablename = resource.tablename

        references = []
        for r in rmap:
            if r.element is None:
                continue
            ktable = s3db.table(r.table)
            if ktable is None:
                continue
            fields = ktable.fields
            if LATFIELD not in fields or \
               LONFIELD not in fields:
                continue
            relement = r.element
            attr = relement.attrib
            if len(r.id) == 1:
                r_id = r.id[0]
            else:
                continue # Multi-reference

            LatLon = None
            WKT = None
            if "track" in current.request.get_vars:
                # Use S3Track
                try:
                    tracker = S3Trackable(table, record_id=record.id)
                except SyntaxError:
                    pass
                else:
                    gtable = s3db.gis_location
                    LatLon = tracker.get_location(as_rows=True,
                                                  _fields=[gtable.lat,
                                                           gtable.lon])

            elif "polygons" in current.request.get_vars:
                # Display Polygons not Points
                if WKTFIELD in fields:
                    query = (ktable.id == r_id)
                    if current.deployment_settings.get_gis_spatialdb():
                        if current.auth.permission.format == "geojson":
                            # Do the Simplify & GeoJSON direct from the DB
                            geojson = db(query).select(ktable.the_geom.st_simplify(0.001).st_asgeojson(precision=4).with_alias('geojson'),
                                                       limitby=(0, 1)).first().geojson
                            if geojson:
                                # Output the GeoJSON directly into the XML, so that XSLT can simply drop in
                                geometry = etree.SubElement(element, "geometry")
                                geometry.set("value", geojson)
                                WKT = True
                        else:
                            # Do the Simplify direct from the DB
                            wkt = db(query).select(ktable.the_geom.st_simplify(0.001).st_astext().with_alias('wkt'),
                                                   limitby=(0, 1)).first().wkt
                            if wkt:
                                # Convert the WKT in XSLT
                                attr[ATTRIBUTE.wkt] = wkt
                                WKT = True
                    else:
                        WKT = db(query).select(ktable[WKTFIELD],
                                               limitby=(0, 1))
                        if WKT:
                            WKT = WKT.first()
                            wkt = WKT[WKTFIELD]
                            if wkt is None:
                                continue
                            if current.auth.permission.format == "geojson":
                                # Simplify the polygon to reduce download size
                                geojson = gis.simplify(wkt, output="geojson")
                                # Output the GeoJSON directly into the XML, so that XSLT can simply drop in
                                geometry = etree.SubElement(element, "geometry")
                                geometry.set("value", geojson)
                            else:
                                # Simplify the polygon to reduce download size
                                # & also to work around the recursion limit in libxslt
                                # http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
                                wkt = gis.simplify(wkt)
                                # Convert the WKT in XSLT
                                attr[ATTRIBUTE.wkt] = wkt

            if not LatLon and not WKT:
                # Normal Location lookup
                LatLon = db(ktable.id == r_id).select(ktable[LATFIELD],
                                                      ktable[LONFIELD],
                                                      limitby=(0, 1))
            if LatLon:
                LatLon = LatLon.first()
                lat = LatLon[LATFIELD]
                lon = LatLon[LONFIELD]
                if lat is None or lon is None:
                    continue
                attr[ATTRIBUTE.lat] = "%.6f" % lat
                attr[ATTRIBUTE.lon] = "%.6f" % lon
                if not marker_url:
                    marker = gis.get_marker()
                    marker_url = "%s/%s" % (download_url, marker.image)
                attr[ATTRIBUTE.marker] = marker_url
                attr[ATTRIBUTE.sym] = symbol

            if LatLon or WKT:
                if popup_fields:
                    # Feature Layer
                    # Build the HTML for the onHover Tooltip
                    tooltip = gis.get_popup_tooltip(table,
                                                    record,
                                                    popup_label,
                                                    popup_fields)
                    try:
                        # encode suitable for use as XML attribute
                        tooltip = self.xml_encode(tooltip).decode("utf-8")
                    except:
                        pass
                    else:
                        attr[ATTRIBUTE.popup] = tooltip

                    # Build the URL for the onClick Popup contents
                    url = URL(resource.prefix,
                              resource.name).split(".", 1)[0]
                    popup_url = "%s/%i.plain" % (url,
                                                 record.id)
                elif popup_label:
                    # Feature Queries
                    # This is the pre-generated HTML for the onHover Tooltip
                    attr[ATTRIBUTE.popup] = popup_label

                if popup_url:
                    # @ToDo: add the Public URL so that layers can
                    # be loaded off remote Sahana instances
                    # (make this optional to keep filesize small
                    # when not needed?)
                    attr[ATTRIBUTE.url] = popup_url

    # -------------------------------------------------------------------------
    def resource(self, parent, table, record,
                 fields=[],
                 postprocess=None,
                 url=None):
        """
            Creates a <resource> element from a record

            @param parent: the parent element in the document tree
            @param table: the database table
            @param record: the record
            @param fields: list of field names to include
            @param postprocess: post-process hook (function to process
                <resource> elements after compilation)
            @param url: URL of the record
        """

        SubElement = etree.SubElement

        UID = self.UID
        MCI = self.MCI
        DELETED = self.DELETED

        TAG = self.TAG
        RESOURCE = TAG.resource
        DATA = TAG.data

        ATTRIBUTE = self.ATTRIBUTE
        NAME = ATTRIBUTE.name
        FIELD = ATTRIBUTE.field
        VALUE = ATTRIBUTE.value
        URL = ATTRIBUTE.url

        tablename = table._tablename
        deleted = False

        download_url = current.response.s3.download_url or ""
        auth_group = current.auth.settings.table_group_name

        if parent is not None:
            elem = SubElement(parent, RESOURCE)
        else:
            elem = etree.Element(RESOURCE)
        attrib = elem.attrib
        attrib[NAME] = tablename

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

        # GIS marker
        if table._tablename == "gis_location" and current.gis:
            marker = current.gis.get_marker() # Default Marker
            # Quicker to download Icons from Static
            # also doesn't require authentication so KML files can work in
            # Google Earth
            marker_download_url = download_url.replace("default/download",
                                                       "static/img/markers")
            marker_url = "%s/%s" % (marker_download_url, marker.image)
            attrib[ATTRIBUTE.marker] = marker_url
            symbol = "White Dot"
            attrib[ATTRIBUTE.sym] = symbol

        # Fields
        FIELDS_TO_ATTRIBUTES = self.FIELDS_TO_ATTRIBUTES

        xml_encode = self.xml_encode
        encode_iso_datetime = self.encode_iso_datetime

        table_fields = table.fields

        _repr = self.represent
        for f in fields:
            if f == DELETED:
                continue
            if f in record:
                v = record[f]
            else:
                v = None
            if f == MCI:
                if v is None:
                    v = 0
                attrib[MCI] = str(int(v) + 1)
                continue
            if v is None or f not in table_fields:
                continue
            dbfield = table[f]
            fieldtype = str(table[f].type)
            formatter = dbfield.formatter
            represent = dbfield.represent
            is_attr = f in FIELDS_TO_ATTRIBUTES
            value = None
            if fieldtype == "datetime":
                value = encode_iso_datetime(v).decode("utf-8")
            elif fieldtype in ("date", "time"):
                value = str(formatter(v)).decode("utf-8")
            if represent is not None and fieldtype != "id":
                text = _repr(table, f, v)
            elif value is not None:
                text = xml_encode(value)
            else:
                text = xml_encode(str(formatter(v)).decode("utf-8"))
            if is_attr:
                if text is not None:
                    attrib[f] = str(text)
            elif fieldtype == "upload":
                fileurl = "%s/%s" % (download_url, v)
                filename = v
                if filename:
                    data = SubElement(elem, DATA)
                    attr = data.attrib
                    attr[FIELD] = f
                    attr[URL] = fileurl
                    attr[ATTRIBUTE.filename] = filename
            elif fieldtype == "password":
                # Do not export password fields
                data = SubElement(elem, DATA)
                data.attrib[FIELD] = f
                data.text = v
            elif fieldtype == "blob":
                # Not implemented
                continue
            else:
                data = SubElement(elem, DATA)
                attr = data.attrib
                attr[FIELD] = f
                if represent or fieldtype not in ("string", "text"):
                    if value is None:
                        value = json.dumps(v).decode("utf-8")
                    attr[VALUE] = value
                data.text = text
        if url and not deleted:
            attrib[URL] = url

        postp = None
        if postprocess is not None:
            if isinstance(postprocess, dict):
                postp = postprocess.get(str(table), None)
            else:
                postp = postprocess
        if postp and callable(postp):
            result = postp(table, record, elem)
            if isinstance(result, etree._Element):
                elem = result

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
    def record(self, table, element,
               original=None,
               files=[],
               preprocess=None,
               validate=None,
               skip=[]):
        """
            Creates a record (Storage) from a <resource> element and validates
            it

            @param table: the database table
            @param element: the element
            @param original: the original record
            @param files: list of attached upload files
            @param preprocess: pre-process hook (function to process elements
                before they get parsed and validated)
            @param validate: validate hook (function to validate fields)
            @param skip: fields to skip
        """

        valid = True
        record = Storage()

        db = current.db
        auth = current.auth
        utable = auth.settings.table_user
        gtable = auth.settings.table_group

        # Preprocess the element
        prepare = None
        if preprocess is not None:
            try:
                prepare = preprocess.get(str(table), None)
            except:
                prepare = preprocess
        if prepare and callable(prepare):
            element = prepare(table, element)

        # Extract the UUID
        if self.UID in table.fields and self.UID not in skip:
            uid = self.import_uid(element.get(self.UID, None))
            if uid:
                record[self.UID] = uid

        # Attributes
        deleted = False
        for f in self.ATTRIBUTES_TO_FIELDS:
            if f == self.DELETED:
                v = element.get(f, None)
                if v == "True":
                    record[f] = deleted = True
                    break
                else:
                    continue
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            elif f in (self.CUSER, self.MUSER, self.OUSER):
                v = element.get(f, None)
                if v and utable and "email" in utable:
                    query = utable.email == v
                    user = db(query).select(utable.id, limitby=(0, 1)).first()
                    if user:
                        record[f] = user.id
                continue
            elif f == self.OGROUP:
                v = element.get(f, None)
                if v and gtable and "role" in gtable:
                    query = gtable.role == v
                    role = db(query).select(gtable.id, limitby=(0, 1)).first()
                    if role:
                        record[f] = role.id
                continue
            if f in table.fields:
                v = value = element.get(f, None)
                if value is not None:
                    field_type = str(table[f].type)
                    if field_type in ("datetime", "date", "time"):
                        (value, error) = self._dtparse(v,
                                                       field_type=field_type)
                    elif validate is not None:
                        try:
                            (value, error) = validate(table, original, f, v)
                        except AttributeError:
                            # No such field
                            continue
                    if error:
                        element.set(self.ATTRIBUTE.error,
                                    "%s: %s" % (f, error))
                        valid = False
                        continue
                    record[f] = value

        if deleted:
            return record

        # Fields
        for child in element.findall("data"):
            f = child.get(self.ATTRIBUTE.field, None)
            if not f or f not in table.fields:
                continue
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            field_type = str(table[f].type)
            if field_type in ("id", "blob"):
                continue
            elif field_type == "upload":
                download_url = child.get(self.ATTRIBUTE.url, None)
                filename = child.get(self.ATTRIBUTE.filename, None)
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
                value = child.get(self.ATTRIBUTE.value, None)

            error = None
            skip_validation = False

            if value is None:
                if field_type == "password":
                    value = child.text
                    # Do not encrypt the password if it already
                    # comes encrypted:
                    skip_validation = True
                else:
                    value = self.xml_decode(child.text)

            if value is None and field_type in ("string", "text"):
                value = ""
            elif value == "" and not field_type in ("string", "text"):
                value = None

            if value is not None:
                if field_type in ("datetime", "date", "time"):
                    (value, error) = self._dtparse(value,
                                                   field_type=field_type)
                    skip_validation = True
                    v = value
                elif isinstance(value, basestring) and len(value):
                    try:
                        _value = json.loads(value)
                        if _value != float("inf"):
                            # e.g. an HTML_COLOUR of 98E600
                            value = _value
                    except:
                        pass

                if validate is not None and not skip_validation:
                    if not isinstance(value, (basestring, list, tuple)):
                        v = str(value)
                    elif isinstance(value, basestring):
                        v = value.encode("utf-8")
                    else:
                        v = value
                    try:
                        if field_type == "upload" and download_url != "local":
                            fn, ff = field.retrieve(value)
                            v = Storage({"filename": fn, "file": ff})
                            (v, error) = validate(table, original, f, v)
                        elif field_type == "password":
                            v = value
                            (value, error) = validate(table, None, f, v)
                        else:
                            (value, error) = validate(table, original, f, v)
                    except AttributeError:
                        # No such field
                        continue
                    except:
                        error = sys.exc_info()[1]

                child.set(self.ATTRIBUTE.value, str(v).decode("utf-8"))
                if error:
                    child.set(self.ATTRIBUTE.error, "%s: %s" % (f, error))
                    valid = False
                    continue

                record[f] = value

        if valid:
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

        if options:
            if parent is not None:
                select = etree.SubElement(parent, cls.TAG.select)
            else:
                select = etree.Element(cls.TAG.select)
            select.set(cls.ATTRIBUTE.name, fieldname)
            select.set(cls.ATTRIBUTE.id,
                       "%s_%s" % (table._tablename, fieldname))

            uids = Storage()
            if show_uids:
                ftype = str(field.type)
                if ftype[:9] == "reference":
                    ktablename = ftype[10:]
                    current.manager.load(ktablename)
                    try:
                        ktable = current.db[ktablename]
                    except:
                        pass
                    else:
                        ids = [o[0] for o in options]
                        if ids and cls.UID in ktable.fields:
                            query = ktable._id.belongs(ids)
                            rows = current.db(query).select(ktable._id, ktable[cls.UID])
                            uids = Storage((str(r[ktable._id.name]), r[cls.UID])
                                        for r in rows)

            for (value, text) in options:
                if show_uids and str(value) in uids:
                    uid = uids[str(value)]
                else:
                    uid = None
                value = cls.xml_encode(str(value).decode("utf-8"))
                try:
                    markup = etree.XML(str(text))
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                except:
                    pass
                text = cls.xml_encode(str(text).decode("utf-8"))
                option = etree.SubElement(select, cls.TAG.option)
                option.set(cls.ATTRIBUTE.value, value)
                if uid:
                    option.set(cls.UID, uid)
                option.text = text
        elif parent is not None:
            return None
        else:
            return etree.Element(cls.TAG.select)

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
            for f in table.fields:
                if fields and f not in fields:
                    continue
                select = self.get_field_options(table, f,
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
            if parent is None:
                fields.set(self.ATTRIBUTE.resource, tablename)
            for f in table.fields:
                ftype = str(table[f].type)
                # Skip super entity references without ID
                if ftype[:9] == "reference" and \
                   not "id" in current.db[ftype[10:]].fields:
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
                field.set(self.ATTRIBUTE.name, f)
                field.set(self.ATTRIBUTE.type, ftype)
                field.set(self.ATTRIBUTE.readable, str(readable))
                field.set(self.ATTRIBUTE.writable, str(writable))
                has_options = str(opts is not None and
                                  len(opts) and True or False)
                field.set(self.ATTRIBUTE.has_options, has_options)
                if labels:
                    label = str(table[f].label).decode("utf-8")
                    field.set(self.ATTRIBUTE.label, label)
                    comment = table[f].comment
                    if comment:
                        comment = str(comment).decode("utf-8")
                    if comment and "<" in comment:
                        try:
                            markup = etree.XML(comment)
                            comment = markup.xpath(".//text()")
                            if comment:
                                comment = " ".join(comment)
                            else:
                                comment = ""
                        except etree.XMLSyntaxError:
                            comment = comment.replace(
                                        "<", "<!-- <").replace(">", "> -->")
                    if comment:
                        field.set(self.ATTRIBUTE.comment, comment)
        return fields

    # -------------------------------------------------------------------------
    def get_struct(self, prefix, name,
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
            element.text = cls.xml_encode(value)
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

        prefix = name = resource = field = None

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
                    element.text = cls.xml_encode(m)
                elif k.startswith(cls.PREFIX.attribute):
                    a = k[len(cls.PREFIX.attribute):]
                    element.set(a, cls.xml_encode(m))
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
            format=cls.TAG.root
            native=True

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
            findall = element.findall
            xpath = element.xpath
            for child in element:
                tag = child.tag
                if not isinstance(tag, basestring):
                    continue # skip comment nodes
                if tag[0] == "{":
                    tag = tag.rsplit("}", 1)[1]
                collapse = True
                single = False
                if native:
                    is_single = lambda t, a, v: len(xpath("%s[@%s='%s']" % (t, a, v))) == 1
                    if tag == TAG.resource:
                        resource = child.get(ATTRIBUTE.name)
                        tag = "%s_%s" % (PREFIX.resource, resource)
                        collapse = False
                    elif tag == TAG.options:
                        r = child.get(ATTRIBUTE.resource)
                        tag = "%s_%s" % (PREFIX.options, r)
                        single = is_single(TAG.options, ATTRIBUTE.resource, r)
                    elif tag == TAG.reference:
                        f = child.get(ATTRIBUTE.field)
                        tag = "%s_%s" % (PREFIX.reference, f)
                        single = is_single(TAG.reference, ATTRIBUTE.field, f)
                    elif tag == TAG.data:
                        tag = child.get(ATTRIBUTE.field)
                        single = is_single(TAG.data, ATTRIBUTE.field, tag)
                else:
                    single = len(findall(tag)) == 1
                child_obj = element2json(child, native=native)
                if child_obj:
                    if tag not in obj:
                        if single and collapse:
                            obj[tag] = child_obj
                        else:
                            obj[tag] = [child_obj]
                    else:
                        if not isinstance(obj[tag], list):
                            obj[tag] = [obj[tag]]
                        obj[tag].append(child_obj)

            attributes = element.attrib
            skip_text = False
            tag = element.tag
            for a in attributes:
                v = element.get(a)
                if native:
                    if a == ATTRIBUTE.name and tag == TAG.resource:
                        continue
                    if a == ATTRIBUTE.resource and tag == TAG.options:
                        continue
                    if a == ATTRIBUTE.field and tag in (TAG.data, TAG.reference):
                        continue
                else:
                    if a == ATTRIBUTE.value:
                        try:
                            obj[TAG.item] = json.loads(v)
                        except:
                            pass
                        else:
                            skip_text = True
                        continue
                obj[PREFIX.attribute + a] = v

            if element.text and not skip_text:
                obj[PREFIX.text] = cls.xml_decode(element.text)

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
            return json.dumps(root_dict)

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
            if element.tag in ("data", "reference"):
                resource = element.getparent()
                value = element.get("value")
                if not value:
                    value = element.text
                error = "%s, %s: '%s' (value='%s')" % (
                            resource.get("name", None),
                            element.get("field", None),
                            element.get("error", None),
                            value)
            elif element.tag == "resource":
                error = "%s: %s" % (element.get("name", None),
                                    element.get("error", None))
            else:
                error = "%s" % element.get("error", None)
            errors.append(error)
        return errors

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

        # Increase field sixe to ne able to import WKTs
        csv.field_size_limit(2**20 * 100)  # 100 megs

        root = etree.Element(cls.TAG.table)
        if resourcename is not None:
            root.set(cls.ATTRIBUTE.name, resourcename)

        def add_col(row, key, value):
            col = etree.SubElement(row, cls.TAG.col)
            col.set(cls.ATTRIBUTE.field, str(key))
            if value:
                text = str(value)
                if text.lower() not in ("null", "<null>"):
                    text = cls.xml_encode(unicode(text.decode("utf-8")))
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
            encodings = ["utf-8", "iso-8859-1"]
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
            reader = csv.DictReader(utf_8_encode(source),
                                    delimiter=delimiter,
                                    quotechar=quotechar)
            for r in reader:
                row = etree.SubElement(root, cls.TAG.row)
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

# End =========================================================================
