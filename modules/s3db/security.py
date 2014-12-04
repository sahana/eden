# -*- coding: utf-8 -*-

""" Sahana Eden Security Model

    @copyright: 2012-14 (c) Sahana Software Foundation
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

__all__ = ("S3SecurityModel",)

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3SecurityModel(S3Model):
    """
    """

    names = ("security_level",
             "security_zone_type",
             "security_zone",
             "security_staff_type",
             "security_staff",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        location_id = self.gis_location_id

        # -----------------------------------------------------------
        # Security Levels
        # - according to the UN Security Level System (SLS)
        # http://ictemergency.wfp.org/c/document_library/get_file?uuid=c025cb98-2297-4208-bcc6-76ba02719c02&groupId=10844
        # http://geonode.wfp.org/layers/geonode:wld_bnd_securitylevel_wfp
        #

        level_opts = {1: T("Minimal"),
                      2: T("Low"),
                      3: T("Moderate"),
                      4: T("Substantial"),
                      5: T("High"),
                      6: T("Extreme"),
                      }

        tablename = "security_level"
        define_table(tablename,
                     location_id(
                        #label = T("Security Level Area"),
                        widget = S3LocationSelector(show_map = False),
                        ),
                     # Overall Level
                     Field("level", "integer",
                           label = T("Security Level"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     # Categories
                     Field("armed_conflict", "integer",
                           label = T("Armed Conflict"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("terrorism", "integer",
                           label = T("Terrorism"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("crime", "integer",
                           label = T("Crime"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("civil_unrest", "integer",
                           label = T("Civil Unrest"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("hazards", "integer",
                           label = T("Hazards"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           comment = T("e.g. earthquakes or floods"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Classify Area"),
            title_display = T("Security Level Details"),
            title_list = T("Security Levels"),
            title_update = T("Edit Security Level"),
            title_upload = T("Import Security Levels"),
            label_list_button = T("List Security Levels"),
            label_delete_button = T("Delete Security Level"),
            msg_record_created = T("Security Area classified"),
            msg_record_modified = T("Security Level updated"),
            msg_record_deleted = T("Security Level deleted"),
            msg_list_empty = T("No Security Areas currently classified"))

        # -----------------------------------------------------------
        # Security Zone Types
        #
        tablename = "security_zone_type"
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
                       deduplicate = self.security_zone_type_duplicate,
                       )

        # -----------------------------------------------------------
        # Security Zones
        #
        tablename = "security_zone"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("zone_type_id", db.security_zone_type,
                           label = T("Type"),
                           represent = zone_type_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_zone_type.id",
                                                  zone_type_represent,
                                                  sort=True)),
                           comment = S3AddResourceLink(c="security",
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
        ADD_ZONE = T("Create Zone")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE,
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

        # -----------------------------------------------------------
        # Security Staff Types
        #
        tablename = "security_staff_type"
        define_table(tablename,
                     Field("name",
                           label=T("Name")),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_STAFF = T("Add Staff Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_STAFF,
            title_display = T("Staff Type Details"),
            title_list = T("Staff Types"),
            title_update = T("Edit Staff Type"),
            title_upload = T("Import Staff Types"),
            label_list_button = T("List Staff Types"),
            label_delete_button = T("Delete Staff Type"),
            msg_record_created = T("Staff Type added"),
            msg_record_modified = T("Staff Type updated"),
            msg_record_deleted = T("Staff Type deleted"),
            msg_list_empty = T("No Staff Types currently registered"))

        staff_type_represent = S3Represent(lookup=tablename)

        # -----------------------------------------------------------
        # Security Staff
        #
        tablename = "security_staff"
        define_table(tablename,
                     self.hrm_human_resource_id(),
                     Field("staff_type_id", "list:reference security_staff_type",
                           label = T("Type"),
                           represent = self.security_staff_type_multirepresent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_staff_type.id",
                                                  staff_type_represent,
                                                  sort=True,
                                                  multiple=True)),
                           comment = S3AddResourceLink(c="security",
                                                       f="staff_type",
                                                       label=ADD_STAFF,
                                                       tooltip=T("Select a Staff Type from the list or click 'Add Staff Type'")),
                           ),
                     Field("zone_id", db.security_zone,
                           label = T("Zone"),
                           represent = zone_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_zone.id",
                                                  zone_represent,
                                                  sort=True)),
                           comment = S3AddResourceLink(c="security",
                                                       f="zone",
                                                       label=ADD_ZONE,
                                                       tooltip=T("For wardens, select a Zone from the list or click 'Add Zone'")),
                           ),
                     self.super_link("site_id", "org_site",
                                     label = T("Facility"),
                                     represent = self.org_site_represent,
                                     readable = True,
                                     writable = True,
                                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Security-Related Staff"),
            title_display = T("Security-Related Staff Details"),
            title_list = T("Security-Related Staff"),
            title_update = T("Edit Security-Related Staff"),
            title_upload = T("Import Security-Related Staff"),
            label_list_button = T("List Security-Related Staff"),
            label_delete_button = T("Delete Security-Related Staff"),
            msg_record_created = T("Security-Related Staff added"),
            msg_record_modified = T("Security-Related Staff updated"),
            msg_record_deleted = T("Security-Related Staff deleted"),
            msg_list_empty = T("No Security-Related Staff currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def security_zone_type_duplicate(item):
        """
            Zone Type record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        table = item.table
        query = (table.name == item.data.name)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -----------------------------------------------------------------------------
    @staticmethod
    def security_staff_type_multirepresent(opt):
        """ Represent a staff type in list views """

        db = current.db
        table = db.security_staff_type
        set = db(table.id > 0).select(table.id,
                                      table.name).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o)["name"]) for o in opts]
            multiple = True
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt)["name"])
            multiple = False
        else:
            try:
                opt = int(opt)
            except:
                return current.messages["NONE"]
            else:
                opts = [opt]
                vals = str(set.get(opt)["name"])
                multiple = False

        if multiple:
            if len(opts) > 1:
                vals = ", ".join(vals)
            else:
                vals = len(vals) and vals[0] or ""
        return vals

# END =========================================================================
