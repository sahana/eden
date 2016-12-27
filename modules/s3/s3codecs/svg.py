# -*- coding: utf-8 -*-

"""
    S3 SVG codec

    @copyright: 2013-2016 (c) Sahana Software Foundation
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

__all__ = ("S3SVG",)

import os

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from gluon import *
from gluon.contenttype import contenttype
from gluon.storage import Storage
from gluon.streamer import DEFAULT_CHUNK_SIZE

from ..s3codec import S3Codec
from ..s3utils import s3_unicode, s3_strip_markup

# =============================================================================
class S3SVG(S3Codec):
    """
        Simple SVG format codec
    """

    # -------------------------------------------------------------------------
    def __init__(self):
        """
            Constructor
        """

        pass

    # -------------------------------------------------------------------------
    def extractResource(self, resource, list_fields):
        """
            Extract the items from the resource

            @param resource: the resource
            @param list_fields: fields to include in list views
        """

        title = self.crud_string(resource.tablename, "title_list")

        get_vars = Storage(current.request.get_vars)
        get_vars["iColumns"] = len(list_fields)
        query, orderby, left = resource.datatable_filter(list_fields, get_vars)
        resource.add_filter(query)

        data = resource.select(list_fields,
                               left=left,
                               limit=None,
                               orderby=orderby,
                               represent=True,
                               show_links=False)

        rfields = data["rfields"]
        types = []
        colnames = []
        heading = {}
        for rfield in rfields:
            if rfield.show:
                colnames.append(rfield.colname)
                heading[rfield.colname] = rfield.label
                if rfield.virtual:
                    types.append("string")
                else:
                    types.append(rfield.ftype)

        items = data["rows"]

        return (title, types, colnames, heading, items)

    # -------------------------------------------------------------------------
    def encode(self, resource, **attr):
        """
            Export data as a Scalable Vector Graphic

            @param resource: the source of the data that is to be encoded
                                as an SVG. This may be:
                                resource: the resource
                                item:     a list of pre-fetched values
                                          the headings are in the first row
                                          the data types are in the second row
            @param attr: dictionary of parameters:
                 * title:          The export filename
                 * list_fields:    Fields to include in list views
        """

        # Get the attributes
        #list_fields = attr.get("list_fields")
        #if not list_fields:
        #    list_fields = resource.list_fields()

        # @ToDo: PostGIS can extract SVG from DB (like GeoJSON)
        # http://postgis.refractions.net/documentation/manual-1.4/ST_AsSVG.html
        if resource.prefix == "gis" and resource.name == "location":
            #list_fields.append("wkt")
            list_fields = ["wkt"]
        #elif "location_id$wkt" not in list_fields:
        else:
            #list_fields.append("location_id$wkt")
            list_fields = ["location_id$wkt"]

        # Clear the WKT represent
        current.s3db.gis_location.wkt.represent = None

        # Extract the data from the resource
        (_title, types, lfields, headers, items) = self.extractResource(resource,
                                                                        list_fields)

        # @ToDo: Support multiple records
        wkt = items[0]["gis_location.wkt"]
        if not wkt:
            current.log.error("No Geometry!")

        # Convert to SVG
        title = attr.get("title", resource._ids[0])
        filename = "%s.svg" % title
        filepath = self.write_file(filename, wkt, **attr)

        # Response headers
        disposition = "attachment; filename=\"%s\"" % filename
        response = current.response
        response.headers["Content-Type"] = contenttype(".svg")
        response.headers["Content-disposition"] = disposition

        stream = open(filepath)
        return response.stream(stream, chunk_size=DEFAULT_CHUNK_SIZE,
                               request=current.request)

    # -------------------------------------------------------------------------
    @staticmethod
    def write_file(filename, wkt, **attr):

        from xml.etree import ElementTree as et

        # Create an SVG XML element
        # @ToDo: Allow customisation of height/width
        iheight = 74
        height = str(iheight)
        iwidth = 74
        width = str(iwidth)
        doc = et.Element("svg", width=width, height=height, version="1.1", xmlns="http://www.w3.org/2000/svg")

        # Convert WKT
        from shapely.wkt import loads as wkt_loads
        try:
            # Enable C-based speedups available from 1.2.10+
            from shapely import speedups
            speedups.enable()
        except:
            current.log.info("S3GIS",
                             "Upgrade Shapely for Performance enhancements")

        shape = wkt_loads(wkt)

        geom_type = shape.geom_type
        if geom_type not in ("MultiPolygon", "Polygon"):
            current.log.error("Unsupported Geometry", geom_type)
            return

        # Scale Points & invert Y axis
        from shapely import affinity
        bounds = shape.bounds # (minx, miny, maxx, maxy)
        swidth = abs(bounds[2] - bounds[0])
        sheight = abs(bounds[3] - bounds[1])
        width_multiplier = iwidth / swidth
        height_multiplier = iheight / sheight
        multiplier = min(width_multiplier, height_multiplier) * 0.9 # Padding
        shape = affinity.scale(shape, xfact=multiplier, yfact=-multiplier, origin="centroid")

        # Center Shape
        centroid = shape.centroid
        xoff = (iwidth / 2) - centroid.x
        yoff = (iheight / 2) - centroid.y
        shape = affinity.translate(shape, xoff=xoff, yoff=yoff)

        if geom_type == "MultiPolygon":
            polygons = shape.geoms
        elif geom_type == "Polygon":
            polygons = [shape]
        # @ToDo:
        #elif geom_type == "LineString":
        #    _points = shape
        #elif geom_type == "Point":
        #    _points = [shape]

        points = []
        pappend = points.append
        for polygon in polygons:
            _points = polygon.exterior.coords
            for point in _points:
                pappend("%s,%s" % (point[0], point[1]))

        points = " ".join(points)

        # Wrap in Square for Icon
        # @ToDo: Anti-Aliased Rounded Corners
        # @ToDo: Make optional
        fill = "rgb(167, 192, 210)"
        stroke = "rgb(114, 129, 145)"
        et.SubElement(doc, "rect", width=width, height=height, fill=fill, stroke=stroke)

        # @ToDo: Allow customisation of options
        fill = "rgb(225, 225, 225)"
        stroke = "rgb(165, 165, 165)"
        et.SubElement(doc, "polygon", points=points, fill=fill, stroke=stroke)

        # @ToDo: Add Attributes from list_fields

        # Write out File
        path = os.path.join(current.request.folder, "static", "cache", "svg")
        if not os.path.exists(path):
            os.makedirs(path)
        filepath = os.path.join(path, filename)
        with open(filepath, "w") as f:
            # ElementTree 1.2 doesn't write the SVG file header errata, so do that manually
            f.write("<?xml version=\"1.0\" standalone=\"no\"?>\n")
            f.write("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n")
            f.write("\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n")
            f.write(et.tostring(doc))

        return filepath

    # -------------------------------------------------------------------------
    def decode(self, resource, source, **attr):
        """
            Import data from a Scalable Vector Graphic

            @param resource: the S3Resource
            @param source: the source

            @return: an S3XML ElementTree

            @ToDo: Handle encodings within SVG other than UTF-8
        """

        # @ToDo: Complete this!
        raise NotImplementedError

        return root

# End =========================================================================
