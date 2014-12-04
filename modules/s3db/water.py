# -*- coding: utf-8 -*-

""" Sahana Eden Water Model

    @copyright: 2011-14 (c) Sahana Software Foundation
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

__all__ = ("S3WaterModel",)

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3WaterModel(S3Model):
    """
        Water Sources
    """

    names = ("water_zone_type",
             "water_zone",
             "water_river",
             "water_gauge",
             #"water_debris_basin",
             #"water_reservoir",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        location_id = self.gis_location_id

        # -----------------------------------------------------------
        # Water Zone Types
        #
        tablename = "water_zone_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_ZONE_TYPE = T("Create Zone Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE_TYPE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_upload = T("Import Zone Types"),
            label_list_button = T("List Zone Types"),
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
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("zone_type_id", db.water_zone_type,
                           label = T("Type"),
                           represent = zone_type_represent,
                           requires = IS_EMPTY_OR(
                                       IS_ONE_OF(db, "water_zone_type.id",
                                                 zone_type_represent,
                                                 sort=True)),
                           comment = S3AddResourceLink(c="water",
                                                       f="zone_type",
                                                       label=ADD_ZONE_TYPE,
                                                       tooltip=T("Select a Zone Type from the list or click 'Add Zone Type'")),
                           ),
                     location_id(
                        widget = S3LocationSelector(catalog_layers = True,
                                                    points = False,
                                                    polygons = True,
                                                    ),
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Zone"),
            title_display = T("Zone Details"),
            title_list = T("Zones"),
            title_update = T("Edit Zone"),
            title_upload = T("Import Zones"),
            label_list_button = T("List Zones"),
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        zone_represent = S3Represent(lookup=tablename)

        # -----------------------------------------------------------------------------
        # Rivers
        tablename = "water_river"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     location_id(
                        widget = S3LocationSelector(catalog_layers = True,
                                                    points = False,
                                                    polygons = True,
                                                    )
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_RIVER = T("Create River")
        crud_strings[tablename] = Storage(
            label_create = ADD_RIVER,
            title_display = T("River Details"),
            title_list = T("Rivers"),
            title_update = T("Edit River"),
            label_list_button = T("List Rivers"),
            msg_record_created = T("River added"),
            msg_record_modified = T("River updated"),
            msg_record_deleted = T("River deleted"),
            msg_list_empty = T("No Rivers currently registered"))

        #represent = S3Represent(lookup = tablename)
        #river_id = S3ReusableField("river_id", "reference %s" % tablename,
        #                           label = T("River"),
        #                           ondelete = "RESTRICT",
        #                           represent = represent,
        #                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "water_river.id", represent)),
        #                           comment = S3AddResourceLink(c="water",
        #                                                       f="river",
        #                                                       title=ADD_RIVER),
        #                           )

        # -----------------------------------------------------------------------------
        # Gauges
        #
        # @ToDo: Link together ones on same river with upstream/downstream relationships
        #
        flowstatus_opts = {1: T("Normal"),
                           2: T("High"),
                           3: T("Very High"),
                           4: T("Low")
                           }

        tablename = "water_gauge"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("code",
                           label = T("Code"),
                           ),
                     #super_link("source_id", "doc_source_entity"),
                     location_id(),
                     Field("url",
                           label = T("URL"),
                           represent = lambda url: \
                                       A(url, _href=url, _target="blank"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("image_url",
                           label = T("Image URL"),
                           ),
                     Field("discharge", "integer",
                           label = T("Discharge (cusecs)"),
                           ),
                     Field("status", "integer",
                           label = T("Flow Status"),
                           represent = lambda opt: \
                            flowstatus_opts.get(opt, opt),
                           requires = IS_EMPTY_OR(IS_IN_SET(flowstatus_opts)),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Gauge"),
            title_display = T("Gauge Details"),
            title_list = T("Gauges"),
            title_update = T("Edit Gauge"),
            title_map = T("Map of Gauges"),
            label_list_button = T("List Gauges"),
            msg_record_created = T("Gauge added"),
            msg_record_modified = T("Gauge updated"),
            msg_record_deleted = T("Gauge deleted"),
            msg_list_empty = T("No Gauges currently registered"))

        # -----------------------------------------------------------------------------
        # Debris Basins
        # http://dpw.lacounty.gov/wrd/sediment/why_move_dirt.cfm
        #
        #tablename = "water_debris_basin"
        #define_table(tablename,
        #             Field("name",
        #                   label = T("Name"),
        #                   ),
        #             location_id(),
        #             s3_comments(),
        #             *s3_meta_fields())

        #crud_strings[tablename] = Storage(
        #    label_create = T("Create Debris Basin"),
        #    title_display = T("Debris Basin Details"),
        #    title_list = T("Debris Basins"),
        #    title_update = T("Edit Debris Basin"),
        #    title_map = T("Map of Debris Basins"),
        #    label_list_button = T("List Debris Basins"),
        #    msg_record_created = T("Debris Basin added"),
        #    msg_record_modified = T("Debris Basin updated"),
        #    msg_record_deleted = T("Debris Basin deleted"),
        #    msg_list_empty = T("No Debris Basins currently registered"))

        # -----------------------------------------------------------------------------
        # Reservoirs
        # Water Storage areas
        #
        #tablename = "water_reservoir"
        #define_table(tablename,
        #             Field("name",
        #                   label = T("Name"),
        #                   ),
        #             location_id(),
        #             s3_comments(),
        #             *s3_meta_fields())

        #crud_strings[tablename] = Storage(
        #    label_create = T("Create Reservoir"),
        #    title_display = T("Reservoir Details"),
        #    title_list = T("Reservoirs"),
        #    title_update = T("Edit Reservoir"),
        #    title_map = T("Map of Reservoirs"),
        #    label_list_button = T("List Reservoirs"),
        #    msg_record_created = T("Reservoir added"),
        #    msg_record_modified = T("Reservoir updated"),
        #    msg_record_deleted = T("Reservoir deleted"),
        #    msg_list_empty = T("No Reservoirs currently registered"))

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
