# -*- coding: utf-8 -*-

""" Sahana Eden Flood Model

    @copyright: 2011-12 (c) Sahana Software Foundation
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

__all__ = ["S3FloodModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3FloodModel(S3Model):
    """
        Monitors Water Levels
    """

    names = ["flood_gauge",
             "flood_river",
             ]

    def model(self):

        T = current.T

        # Shortcuts
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

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
        tablename = "flood_gauge"
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
            title_search = T("Search Gauges"),
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

        # -----------------------------------------------------------------------------
        # Rivers
        tablename = "flood_river"
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
            title_search = T("Search Rivers"),
            subtitle_create = T("Add New River"),
            label_list_button = T("List Rivers"),
            label_create_button = ADD_RIVER,
            msg_record_created = T("River added"),
            msg_record_modified = T("River updated"),
            msg_record_deleted = T("River deleted"),
            msg_list_empty = T("No Rivers currently registered"))

        #river_id = S3ReusableField("river_id", table,
        #                           requires = IS_NULL_OR(IS_ONE_OF(db, "flood_river.id", "%(name)s")),
        #                           represent = lambda id: \
        #                            (id and [db(db.flood_river.id == id).select(db.flood_river.name,
        #                                                                        limitby=(0, 1)).first().name] or ["None"])[0],
        #                           label = T("River"),
        #                           comment = S3AddResourceLink(c="flood",
        #                                                       f="river",
        #                                                       title=ADD_RIVER),
        #                           ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# END =========================================================================
