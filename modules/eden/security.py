# -*- coding: utf-8 -*-

""" Sahana Eden Security Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3SecurityModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3SecurityModel(S3Model):
    """
    """

    names = ["security_zone_type",
             "security_zone",
             "security_staff_type",
             "security_staff",
             ]

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # -----------------------------------------------------------
        # Security Zone Types
        tablename = "security_zone_type"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ZONE = T("Add Zone Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_ZONE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_search = T("Search Zone Types"),
            title_upload = T("Import Zone Types"),
            subtitle_create = T("Add New Zone Type"),
            label_list_button = T("List Zone Types"),
            label_create_button = T("Add New Zone Type"),
            label_delete_button = T("Delete Zone Type"),
            msg_record_created = T("Zone Type added"),
            msg_record_modified = T("Zone Type updated"),
            msg_record_deleted = T("Zone Type deleted"),
            msg_list_empty = T("No Zone Types currently registered"))

        # -----------------------------------------------------------
        # Security Zones
        tablename = "security_zone"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             Field("zone_type_id", db.security_zone_type,
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "security_zone_type.id",
                                                          self.security_zone_type_represent,
                                                          sort=True)),
                                   represent = self.security_zone_type_represent,
                                   comment = S3AddResourceLink(c="security",
                                                               f="zone_type",
                                                               label=ADD_ZONE,
                                                               tooltip=T("Select a Zone Type from the list or click 'Add Zone Type'")),
                                   label=T("Type")),
                             self.gis_location_id(
                                widget = S3LocationSelectorWidget(polygon=True)
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
            title_search = T("Search Zones"),
            title_upload = T("Import Zones"),
            subtitle_create = T("Add New Zone"),
            label_list_button = T("List Zones"),
            label_create_button = T("Add New Zone"),
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        # -----------------------------------------------------------
        # Security Staff Types
        tablename = "security_staff_type"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_STAFF = T("Add Staff Type")
        crud_strings[tablename] = Storage(
            title_create = ADD_STAFF,
            title_display = T("Staff Type Details"),
            title_list = T("Staff Types"),
            title_update = T("Edit Staff Type"),
            title_search = T("Search Staff Types"),
            title_upload = T("Import Staff Types"),
            subtitle_create = T("Add New Staff Type"),
            label_list_button = T("List Staff Types"),
            label_create_button = T("Add New Staff Type"),
            label_delete_button = T("Delete Staff Type"),
            msg_record_created = T("Staff Type added"),
            msg_record_modified = T("Staff Type updated"),
            msg_record_deleted = T("Staff Type deleted"),
            msg_list_empty = T("No Staff Types currently registered"))

        # -----------------------------------------------------------
        # Security Staff
        tablename = "security_staff"
        table = define_table(tablename,
                             self.hrm_human_resource_id(),
                             Field("staff_type_id", "list:reference security_staff_type",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "security_staff_type.id",
                                                          self.security_staff_type_represent,
                                                          sort=True,
                                                          multiple=True)),
                                   represent = self.security_staff_type_multirepresent,
                                   comment = S3AddResourceLink(c="security",
                                                               f="staff_type",
                                                               label=ADD_STAFF,
                                                               tooltip=T("Select a Staff Type from the list or click 'Add Staff Type'")),
                                   label=T("Type")),
                              Field("zone_id", db.security_zone,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "security_zone.id",
                                                          self.security_zone_represent,
                                                          sort=True)),
                                    represent = self.security_zone_represent,
                                    comment = S3AddResourceLink(c="security",
                                                                f="zone",
                                                                label=ADD_ZONE,
                                                                tooltip=T("For wardens, select a Zone from the list or click 'Add Zone'")),
                                    label=T("Zone")),
                                  self.super_link("site_id", "org_site",
                                                  label = T("Facility"),
                                                  represent=self.org_site_represent,
                                                  readable=True,
                                                  writable=True),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD strings
        ADD_STAFF = T("Add Security-Related Staff")
        crud_strings[tablename] = Storage(
            title_create = ADD_STAFF,
            title_display = T("Security-Related Staff Details"),
            title_list = T("Security-Related Staff"),
            title_update = T("Edit Security-Related Staff"),
            title_search = T("Search Security-Related Staff"),
            title_upload = T("Import Security-Related Staff"),
            subtitle_create = T("Add New Security-Related Staff"),
            label_list_button = T("List Security-Related Staff"),
            label_create_button = T("Add New Security-Related Staff"),
            label_delete_button = T("Delete Security-Related Staff"),
            msg_record_created = T("Security-Related Staff added"),
            msg_record_modified = T("Security-Related Staff updated"),
            msg_record_deleted = T("Security-Related Staff deleted"),
            msg_list_empty = T("No Security-Related Staff currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

    # -----------------------------------------------------------------------------
    @staticmethod
    def security_zone_type_represent(id, row=None):
        """ Represent a security zone type in option fields or list views """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.security_zone_type
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def security_zone_represent(id, row=None):
        """ Represent a security zone in option fields or list views """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.security_zone
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

    # -----------------------------------------------------------------------------
    @staticmethod
    def security_staff_type_represent(id, row=None):
        """ Represent a staff type zone in option fields """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.security_staff_type
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

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
