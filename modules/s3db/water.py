# -*- coding: utf-8 -*-

""" Sahana Eden Water Model

    @copyright: 2011-13 (c) Sahana Software Foundation
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

__all__ = ["S3WaterModel",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3WaterModel(S3Model):
    """
        Water Sources
    """

    names = ["water_zone_type",
             "water_zone",
             "water_river",
             "water_gauge",
             ]

    def model(self):

        T = current.T
        db = current.db

        # Shortcuts
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # -----------------------------------------------------------
        # Water Zone Types
        #
        tablename = "water_zone_type"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ZONE_TYPE = T("Add Zone Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_ZONE_TYPE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_upload = T("Import Zone Types"),
            subtitle_create = T("Add New Zone Type"),
            label_list_button = T("List Zone Types"),
            label_create_button = ADD_ZONE_TYPE,
            label_delete_button = T("Delete Zone Type"),
            msg_record_created = T("Zone Type added"),
            msg_record_modified = T("Zone Type updated"),
            msg_record_deleted = T("Zone Type deleted"),
            msg_list_empty = T("No Zone Types currently registered"))

        zone_type_represent = S3Represent(lookup=tablename)

        self.configure(tablename,
                       deduplicate = self.water_zone_type_duplicate,
                       )

        # -----------------------------------------------------------
        # Water Zones
        # - e.g. Floods
        #
        tablename = "water_zone"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             Field("zone_type_id", db.water_zone_type,
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "water_zone_type.id",
                                                          zone_type_represent,
                                                          sort=True)),
                                   represent = zone_type_represent,
                                   comment = S3AddResourceLink(c="water",
                                                               f="zone_type",
                                                               label=ADD_ZONE_TYPE,
                                                               tooltip=T("Select a Zone Type from the list or click 'Add Zone Type'")),
                                   label=T("Type")),
                             self.gis_location_id(
                                widget = S3LocationSelectorWidget2(
                                    catalog_layers=True,
                                    polygons=True
                                    )
                                ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ZONE = T("Add Zone")
        crud_strings[tablename] = Storage(
            title_create = ADD_ZONE,
            title_display = T("Zone Details"),
            title_list = T("Zones"),
            title_update = T("Edit Zone"),
            title_upload = T("Import Zones"),
            subtitle_create = T("Add New Zone"),
            label_list_button = T("List Zones"),
            label_create_button = ADD_ZONE,
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        zone_represent = S3Represent(lookup=tablename)

        # -----------------------------------------------------------------------------
        # Rivers
        tablename = "water_river"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name"),
                                   requires = IS_NOT_EMPTY()),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_RIVER = T("Add River")
        crud_strings[tablename] = Storage(
            title_create = ADD_RIVER,
            title_display = T("River Details"),
            title_list = T("Rivers"),
            title_update = T("Edit River"),
            subtitle_create = T("Add New River"),
            label_list_button = T("List Rivers"),
            label_create_button = ADD_RIVER,
            msg_record_created = T("River added"),
            msg_record_modified = T("River updated"),
            msg_record_deleted = T("River deleted"),
            msg_list_empty = T("No Rivers currently registered"))

        #represent = S3Represent(lookup = tablename)
        #river_id = S3ReusableField("river_id", table,
        #                           requires = IS_NULL_OR(IS_ONE_OF(db, "water_river.id", represent)),
        #                           represent = represent,
        #                           label = T("River"),
        #                           comment = S3AddResourceLink(c="water",
        #                                                       f="river",
        #                                                       title=ADD_RIVER),
        #                           ondelete = "RESTRICT")

        # -----------------------------------------------------------------------------
        # Gauges
        #
        # @ToDo: Link together ones on same river with upstream/downstream relationships
        #
        flowstatus_opts = {
            1:T("Normal"),
            2:T("High"),
            3:T("Very High"),
            4:T("Low")
        }
        tablename = "water_gauge"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             Field("code",
                                   label=T("Code")),
                             #super_link("source_id", "doc_source_entity"),
                             self.gis_location_id(),
                             Field("url",
                                   label = T("URL"),
                                   requires = IS_NULL_OR(IS_URL()),
                                   represent = lambda url: \
                                    A(url, _href=url, _target="blank")
                                   ),
                             Field("image_url",
                                   label=T("Image URL")),
                             Field("discharge", "integer",
                                   label = T("Discharge (cusecs)")),
                             Field("status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(flowstatus_opts)),
                                   represent = lambda opt: \
                                    flowstatus_opts.get(opt, opt),
                                   label = T("Flow Status")),
                             s3_comments(),
                             *s3_meta_fields())

        ADD_GAUGE = T("Add Gauge")
        crud_strings[tablename] = Storage(
            title_create = ADD_GAUGE,
            title_display = T("Gauge Details"),
            title_list = T("Gauges"),
            title_update = T("Edit Gauge"),
            title_map = T("Map of Gauges"),
            subtitle_create = T("Add New Gauge"),
            label_list_button = T("List Gauges"),
            label_create_button = ADD_GAUGE,
            msg_record_created = T("Gauge added"),
            msg_record_modified = T("Gauge updated"),
            msg_record_deleted = T("Gauge deleted"),
            msg_list_empty = T("No Gauges currently registered"),
            name_nice = T("Gauge"),
            name_nice_plural = T("Gauges"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def water_zone_type_duplicate(item):
        """
            Zone Type record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "water_zone_type":
            table = item.table
            query = (table.name == item.data.name)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

# END =========================================================================
