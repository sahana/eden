# -*- coding: utf-8 -*-
"""
    Sahana Eden Volunteers Management 
    (Extends modules/eden/hrm.py)

    @copyright: 2012-13 (c) Sahana Software Foundation
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
           "vol_active",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3VolClusterDataModel(S3Model):

    names = ["vol_details",
             "vol_cluster_type",
             "vol_cluster",
             "vol_cluster_position",
             "vol_volunteer_cluster"
             ]

    def model(self):

        db = current.db
        T = current.T

        crud_strings = current.response.s3.crud_strings
        hrm_human_resource_id = self.hrm_human_resource_id

        # ---------------------------------------------------------------------
        # Volunteer Details
        # - extra details for volunteers
        #
        tablename = "vol_details"
        table = self.define_table(tablename,
                                  hrm_human_resource_id(ondelete = "CASCADE"),
                                  Field("active", "boolean",
                                        represent = self.vol_active_represent,
                                        label = T("Active")),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster_type"
        table = self.define_table(tablename,
                                  Field("name", unique=True,
                                        label = T("Name")),
                                  *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Volunteer Cluster Type"),
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

        represent = S3Represent(lookup=tablename)
        vol_cluster_type_id = S3ReusableField("vol_cluster_type_id", table,
                                              label = T("Volunteer Cluster Type"),
                                              requires = IS_NULL_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_type.id",
                                                                      represent)),
                                              represent = represent, 
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

        represent = S3Represent(lookup=tablename)
        vol_cluster_id = S3ReusableField("vol_cluster_id", table,
                                         label = T("Volunteer Cluster"),
                                         requires = IS_NULL_OR(
                                                        IS_ONE_OF(db,
                                                                  "vol_cluster.id",
                                                                  represent)),
                                         represent = represent,
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

        represent = S3Represent(lookup=tablename)
        vol_cluster_position_id = S3ReusableField("vol_cluster_position_id", table,
                                                label = T("Volunteer Cluster Postion"),
                                                requires = IS_NULL_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_position.id",
                                                                      represent)),
                                                represent = represent,
                                                comment = comment
                                                )

        # ---------------------------------------------------------------------
        # Volunteer Cluster Link Table
        cluster_type_filter = '''
S3OptionsFilter({
 'triggerName':'vol_cluster_type_id',
 'targetName':'vol_cluster_id',
 'lookupKey':'vol_cluster_type_id',
 'lookupPrefix':'vol',
 'lookupResource':'cluster',
})'''

        tablename = "vol_volunteer_cluster"
        table = self.define_table(tablename,
                                  hrm_human_resource_id(ondelete = "CASCADE"),
                                  vol_cluster_type_id(script = cluster_type_filter), # This field is ONLY here to provide a filter
                                  vol_cluster_id(readable=False,
                                                 writable=False),
                                  vol_cluster_position_id(readable=False,
                                                          writable=False),
                                  *s3_meta_fields())

        # Pass names back to global scope (s3.*)
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

    # =====================================================================
    @staticmethod
    def vol_active_represent(opt):
        """
            Represent the Active status of a Volunteer
        """

        args = current.request.args
        if "search" in args:
            # We can't use an HTML represent, but can use a LazyT
            # if we match in the search options
            return current.T("Yes") if opt else current.T("No")
        elif "report" in args:
            # We can't use a represent
            return opt

        # List view, so HTML represent is fine
        if opt:
            output = DIV(current.T("Yes"),
                         _style="color:green;")
        else:
            output = DIV(current.T("No"),
                         _style="color:red;")
        return output

# =============================================================================
def vol_active(person_id):
    """
        Whether a Volunteer counts as 'Active' based on the number of hours
        they've done (both Trainings & Programmes) per month, averaged over
        the last year.
        If nothing recorded for the last 3 months, don't penalise as assume
        that data entry hasn't yet been done.

        @ToDo: Move to Template
        @ToDo: This should be based on the HRM record, not Person record
               - could be active with Org1 but not with Org2
        @ToDo: allow to be calculated differently per-Org
    """

    now = current.request.utcnow

    # Time spent on Programme work
    htable = current.s3db.hrm_programme_hours
    query = (htable.deleted == False) & \
            (htable.person_id == person_id) & \
            (htable.date != None)
    programmes = current.db(query).select(htable.hours,
                                          htable.date,
                                          orderby=htable.date)
    if programmes:
        # Ignore up to 3 months of records
        three_months_prior = (now - datetime.timedelta(days=92))
        end = max(programmes.last().date, three_months_prior.date())
        last_year = end - datetime.timedelta(days=365)
        # Is this the Volunteer's first year?
        if programmes.first().date > last_year:
            # Only start counting from their first month
            start = programmes.first().date
        else:
            # Start from a year before the latest record
            start = last_year

        # Total hours between start and end
        programme_hours = 0
        for programme in programmes:
            if programme.date >= start and programme.date <= end and programme.hours:
                programme_hours += programme.hours

        # Average hours per month
        months = max(1, (end - start).days / 30.5)
        average = programme_hours / months

        # Active?
        if average >= 8:
            return True
        else:
            return False
    else:
        return False

# END =========================================================================
