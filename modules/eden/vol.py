# -*- coding: utf-8 -*-
"""
    Sahana Eden Volunteers Management 
    (Extends modules/eden/hrm.py)

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

__all__ = ["S3VolClusterDataModel",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3VolClusterDataModel(S3Model):

    names = ["vol_cluster_type",
             "vol_cluster",
             "vol_cluster_position",
             "vol_volunteer_cluster"
             ]

    def model(self):

        db = current.db
        T = current.T

        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster_type"
        table = self.define_table(tablename,
                                  Field("name", unique=True,
                                        label = T("Name")),
                                  *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Volunteer Cluster Type Type"),
            title_display = T("Volunteer Cluster Type"),
            title_list = T("Volunteer Cluster Type"),
            title_update = T("Edit Volunteer Cluster Type"),
            title_search = T("Search Volunteer Cluster Types"),
            title_upload = T("Import Volunteer Cluster Types"),
            subtitle_create = T("Add New Volunteer Cluster Type"),
            label_list_button = T("List Volunteer Cluster Types"),
            label_create_button = T("Add Volunteer Cluster Type"),
            label_delete_button = T("Delete Volunteer Cluster Type"),
            msg_record_created = T("Volunteer Cluster Type added"),
            msg_record_modified = T("Volunteer Cluster Type updated"),
            msg_record_deleted = T("Volunteer Cluster Type deleted"),
            msg_list_empty = T("No Volunteer Cluster Types"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster_type",
                                    vars = dict(child = "vol_cluster_type_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create_button,
                                    title = T("Volunteer Cluster Type"),
                                    )

        vol_cluster_type_id = S3ReusableField("vol_cluster_type_id", table,
                                              label = T("Volunteer Cluster Type"),
                                              requires = IS_NULL_OR(
                                                                    IS_ONE_OF(db,
                                                                              "vol_cluster_type.id",
                                                                              s3_represent_name(table))),
                                              represent = s3_represent_name(table), 
                                              comment = comment
                                              )

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster"
        table = self.define_table(tablename,
                                  vol_cluster_type_id(),
                                  Field("name", unique=True,
                                        label = T("Name")),
                                  *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Volunteer Cluster"),
            title_display = T("Volunteer Cluster"),
            title_list = T("Volunteer Cluster"),
            title_update = T("Edit Volunteer Cluster"),
            title_search = T("Search Volunteer Clusters"),
            title_upload = T("Import Volunteer Clusters"),
            subtitle_create = T("Add New Volunteer Cluster"),
            label_list_button = T("List Volunteer Clusters"),
            label_create_button = T("Add Volunteer Cluster"),
            label_delete_button = T("Delete Volunteer Cluster"),
            msg_record_created = T("Volunteer Cluster added"),
            msg_record_modified = T("Volunteer Cluster updated"),
            msg_record_deleted = T("Volunteer Cluster deleted"),
            msg_list_empty = T("No Volunteer Clusters"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster",
                                    vars = dict(child = "vol_cluster_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create_button,
                                    title = T("Volunteer Cluster"),
                                    )

        vol_cluster_id = S3ReusableField("vol_cluster_id", table,
                                         label = T("Volunteer Cluster"),
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db,
                                                                  "vol_cluster.id",
                                                                  s3_represent_name(table))),
                                         represent = s3_represent_name(table),
                                         comment = comment
                                         )

        # ---------------------------------------------------------------------
        # Volunteer Group Position
        #
        tablename = "vol_cluster_position"
        table = self.define_table(tablename,
                                  Field("name", unique=True,
                                        label = T("Name")),
                                  *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Volunteer Cluster Position"),
            title_display = T("Volunteer Cluster Position"),
            title_list = T("Volunteer Cluster Position"),
            title_update = T("Edit Volunteer Cluster Position"),
            title_search = T("Search Volunteer Cluster Positions"),
            title_upload = T("Import Volunteer Cluster Positions"),
            subtitle_create = T("Add New Volunteer Cluster Position"),
            label_list_button = T("List Volunteer Cluster Positions"),
            label_create_button = T("Add Volunteer Cluster Position"),
            label_delete_button = T("Delete Volunteer Cluster Position"),
            msg_record_created = T("Volunteer Cluster Position added"),
            msg_record_modified = T("Volunteer Cluster Position updated"),
            msg_record_deleted = T("Volunteer Cluster Position deleted"),
            msg_list_empty = T("No Volunteer Cluster Positions"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster_position",
                                    vars = dict(child = "vol_cluster_position_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create_button,
                                    title = T("Volunteer Cluster Position"),
                                    )

        vol_cluster_position_id = S3ReusableField("vol_cluster_position_id", table,
                                                label = T("Volunteer Cluster Postion"),
                                                requires = IS_NULL_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_position.id",
                                                                      s3_represent_name(table))),
                                                represent = s3_represent_name(table),
                                                comment = comment
                                                )

        # ---------------------------------------------------------------------
        # Volunteer Cluster Link Table
        cluster_type_filter = SCRIPT(
'''$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'sub_volunteer_cluster_vol_cluster_type_id',
  'Field':'sub_volunteer_cluster_vol_cluster_id',
  'FieldKey':'vol_cluster_type_id',
  'FieldPrefix':'vol',
  'FieldResource':'cluster',
 })
})''')

        tablename = "vol_volunteer_cluster"
        table = self.define_table(tablename,
                                  self.hrm_human_resource_id(),
                                  vol_cluster_type_id(script = cluster_type_filter), # This field is ONLY here to provide a filter
                                  vol_cluster_id(readable=False,
                                                 writable=False),
                                  vol_cluster_position_id(readable=False,
                                                          writable=False),
                                  *s3_meta_fields())

        # Return names to response.s3
        return Storage(
                vol_cluster_type_id = vol_cluster_type_id,
                vol_cluster_id = vol_cluster_id,
            )

    # =====================================================================
    @staticmethod
    def defaults():
        """
            Return safe defaults for model globals, this will be called instead
            of model() in case the model has been deactivated in
            deployment_settings.
        """

        return Storage(
            vol_cluster_id = S3ReusableField("vol_cluster_id", "integer",
                                             readable=False,
                                             writable=False),
            )
# END =========================================================================
