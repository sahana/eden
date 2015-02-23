# -*- coding: utf-8 -*-

"""
    S3 Shapefile codec

    @copyright: 2013-14 (c) Sahana Software Foundation
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

__all__ = ("S3SHP",)

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
class S3SHP(S3Codec):
    """
        Simple Shapefile format codec
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
    def encode(self, data_source, **attr):
        """
            Export data as a Shapefile

            @param data_source: the source of the data that is to be encoded
                                as a shapefile. This may be:
                                resource: the resource
                                item:     a list of pre-fetched values
                                          the headings are in the first row
                                          the data types are in the second row
            @param attr: dictionary of parameters:
                 * title:          The export filename
                 * list_fields:    Fields to include in list views
        """

        # Get the attributes
        title = attr.get("title")

        # Extract the data from the data_source
        if isinstance(data_source, (list, tuple)):
            headers = data_source[0]
            #types = data_source[1]
            items = data_source[2:]
        else:
            current.s3db.gis_location.wkt.represent = None
            list_fields = attr.get("list_fields")
            if not list_fields:
                list_fields = data_source.list_fields()
            if data_source.tablename == "gis_location":
                wkt_field = "wkt"
            else:
                wkt_field = "location_id$wkt"
            if wkt_field not in list_fields:
                list_fields.append(wkt_field)

            (_title, types, lfields, headers, items) = self.extractResource(data_source,
                                                                            list_fields)
            if not title:
                title = _title

        # Create the data structure
        output = []
        oappend = output.append

        # Header row
        headers["gis_location.wkt"] = "WKT"
        fields = []
        fappend = fields.append
        header = []
        happend = header.append
        for selector in lfields:
            h = s3_unicode(headers[selector].replace(" ", "_"))
            happend(h)
            if selector != "gis_location.wkt":
                # Don't include the WKT field as an Attribute in the Shapefile
                fappend(h)
        oappend('"%s"' % '","'.join(header))
        fields = ",".join(fields)

        for item in items:
            row = []
            rappend = row.append
            for selector in lfields:
                represent = s3_strip_markup(s3_unicode(item[selector]))
                rappend(represent)
            oappend('"%s"' % '","'.join(row))

        # Write out as CSV
        import tempfile
        web2py_path = os.getcwd()
        if os.path.exists(os.path.join(web2py_path, "temp")): # use web2py/temp
            TEMP = os.path.join(web2py_path, "temp")
        else:
            TEMP = tempfile.gettempdir()
        os_handle_temp, temp_filepath = tempfile.mkstemp(dir=TEMP, suffix=".csv")
        with open(temp_filepath, "w") as f:
            for line in output:
                f.write("%s\n" % line.encode("utf-8"))

        # Convert to Shapefile
        # @ToDo: migrate to GDAL Python bindings
        # Write out VRT file
        temp_filename = temp_filepath.rsplit(os.path.sep, 1)[1]
        vrt = \
'''<OGRVRTDataSource>
    <OGRVRTLayer name="%s">
        <SrcDataSource>%s</SrcDataSource>
        <GeometryType>wkbGeometryCollection</GeometryType>
        <TargetSRS>EPSG:4326</TargetSRS>
        <GeometryField encoding="WKT" field="WKT"/>
    </OGRVRTLayer>
</OGRVRTDataSource>''' % (temp_filename.rsplit(".", 1)[0], temp_filename)
        os_handle_vrt, vrt_filename = tempfile.mkstemp(dir=TEMP, suffix=".vrt")
        with open(vrt_filename, "w") as f:
            f.write(vrt)
        # @ToDo: Check that the data exists before writing out file
        # Write Points
        os.chdir(TEMP)
        # Use + not %s as % within string
        cmd = 'ogr2ogr -a_srs "EPSG:4326" -f "ESRI Shapefile" ' + title + '_point.shp ' + vrt_filename + ' -select ' + fields + ' -skipfailures -nlt POINT -where "WKT LIKE \'%POINT%\'"'
        #os.system("rm %s_point.*" % title)
        os.system(cmd)
        # Write Lines
        cmd = 'ogr2ogr -a_srs "EPSG:4326" -f "ESRI Shapefile" ' + title + '_line.shp ' + vrt_filename + ' -select ' + fields + ' -skipfailures -nlt MULTILINESTRING -where "WKT LIKE \'%LINESTRING%\'"'
        #os.system("rm %s_line.*" % title)
        os.system(cmd)
        # Write Polygons
        cmd = 'ogr2ogr -a_srs "EPSG:4326" -f "ESRI Shapefile" ' + title + '_polygon.shp ' + vrt_filename + ' -select ' + fields + ' -skipfailures -nlt MULTIPOLYGON -where "WKT LIKE \'%POLYGON%\'"'
        #os.system("rm %s_polygon.*" % title)
        os.system(cmd)
        os.close(os_handle_temp)
        os.unlink(temp_filepath)
        os.close(os_handle_vrt)
        os.unlink(vrt_filename)
        # Zip up
        import zipfile
        request = current.request
        filename = "%s_%s.zip" % (request.env.server_name, title)
        fzip = zipfile.ZipFile(filename, "w")
        for item in ("point", "line", "polygon"):
            for exten in ("shp", "shx", "prj", "dbf"):
                tfilename = "%s_%s.%s" % (title, item, exten)
                fzip.write(tfilename)
                os.unlink(tfilename)
        fzip.close()
        # Restore path
        os.chdir(web2py_path)

        # Response headers
        disposition = "attachment; filename=\"%s\"" % filename
        response = current.response
        response.headers["Content-Type"] = contenttype(".zip")
        response.headers["Content-disposition"] = disposition

        stream = open(os.path.join(TEMP, filename), "rb")
        return response.stream(stream, chunk_size=DEFAULT_CHUNK_SIZE,
                               request=request)

    # -------------------------------------------------------------------------
    def decode(self, resource, source, **attr):
        """
            Import data from a Shapefile

            @param resource: the S3Resource
            @param source: the source

            @return: an S3XML ElementTree

            @ToDo: Handle encodings within Shapefiles other than UTF-8
        """

        # @ToDo: Complete this!
        # Sample code coming from this working script:
        # http://eden.sahanafoundation.org/wiki/BluePrint/GIS/ShapefileLayers#ImportintonativeTables
        # We also have sample code to read SHP from GDAL in:
        # gis_layer_shapefile_onaccept() & import_admin_areas() [GADM]
        raise NotImplementedError

        try:
            from lxml import etree
        except ImportError:
            import sys
            print >> sys.stderr, "ERROR: lxml module needed for XML handling"
            raise

        try:
            from osgeo import ogr
        except ImportError:
            import sys
            print >> sys.stderr, "ERROR: GDAL module needed for Shapefile handling"
            raise

        # @ToDo: Check how this would happen
        shapefilename = source

        layername = os.path.splitext(os.path.basename(shapefilename))[0]

        # Create the datasource
        ds = ogr.Open(shapefilename)

        # Open the shapefile
        if ds is None:
            # @ToDo: Bail gracefully
            raise

        # Get the layer and iterate through the features
        lyr = ds.GetLayer(0)

        root = etree.Element("shapefile", name=layername)

        OFTInteger = ogr.OFTInteger
        OFTReal = ogr.OFTReal
        OFTString = ogr.OFTString
        for feat in lyr:
            featurenode = etree.SubElement(root, "feature")
            feat_defn = lyr.GetLayerDefn()
            GetFieldDefn = feat_defn.GetFieldDefn
            for i in range(feat_defn.GetFieldCount()):
                field_defn = GetFieldDefn(i)
                fieldnode = etree.SubElement(featurenode, field_defn.GetName())
                if field_defn.GetType() == OFTInteger:
                    fieldnode.text = str(feat.GetFieldAsInteger(i))
                elif field_defn.GetType() == OFTReal:
                    fieldnode.text = str(feat.GetFieldAsDouble(i))
                elif field_defn.GetType() == OFTString:
                    FieldString = str(feat.GetFieldAsString(i))
                    # @ToDo: Don't assume UTF-8
                    fieldnode.text = FieldString.decode(encoding="UTF-8",
                                                        errors="strict")

            wktnode = etree.SubElement(featurenode, "wkt")
            geom = feat.GetGeometryRef()
            wktnode.text = geom.ExportToWkt()

        # @ToDo: Convert using XSLT

        # Debug: Write out the etree
        #xmlString = etree.tostring(root, pretty_print=True)
        #f = open("test.xml","w")
        #f.write(xmlString)

        return root

# End =========================================================================
