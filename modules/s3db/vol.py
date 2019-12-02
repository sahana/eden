# -*- coding: utf-8 -*-
"""
    Sahana Eden Volunteers Management
    (Extends modules/eden/hrm.py)

    @copyright: 2012-2019 (c) Sahana Software Foundation
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

__all__ = ("S3VolunteerModel",
           "S3VolunteerActivityModel",
           "S3VolunteerAwardModel",
           "S3VolunteerClusterModel",
           "vol_service_record",
           "vol_person_controller",
           "vol_volunteer_controller",
           )

import json

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3VolunteerModel(S3Model):

    names = ("vol_details",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Volunteer Details
        # - extra details for volunteers
        #
        tablename = "vol_details"
        self.define_table(tablename,
                          self.hrm_human_resource_id(ondelete = "CASCADE"),
                          Field("volunteer_type",
                                readable = False,
                                writable = False,
                                ),
                          Field("active", "boolean",
                                default = False,
                                label = T("Active"),
                                represent = self.vol_active_represent,
                                ),
                          Field("card", "boolean",
                                default = False,
                                label = T("Card holder"),
                                represent = self.vol_active_represent,
                                # Enable in-template when-required
                                readable = False,
                                writable = False,
                                ),
                          *s3_meta_fields())

    # -------------------------------------------------------------------------
    @staticmethod
    def vol_active_represent(opt):
        """ Represent the Active status of a Volunteer """

        if "report" in current.request.args:
            # We can't use a represent
            return opt

        # List view, so HTML represent is fine
        if opt:
            output = DIV(current.T("Yes"), _style="color:green")
        else:
            output = DIV(current.T("No"), _style="color:red")
        return output

# =============================================================================
class S3VolunteerActivityModel(S3Model):
    """
        Currently used by CRMADA
    """

    names = ("vol_activity_type",
             "vol_activity_type_sector",
             "vol_activity",
             "vol_activity_activity_type",
             "vol_activity_hours",
             "vol_activity_hours_activity_type",
             )

    def model(self):

        T = current.T
        db = current.db
        #auth = current.auth

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        #ADMIN = current.session.s3.system_roles.ADMIN
        #is_admin = auth.s3_has_role(ADMIN)

        #root_org = auth.root_org()
        #if is_admin:
        #    filter_opts = ()
        #elif root_org:
        #    filter_opts = (root_org, None)
        #else:
        #    filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Volunteer Activity Type
        #
        tablename = "vol_activity_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     #self.org_organisation_id(default = root_org,
                     #                         readable = is_admin,
                     #                         writable = is_admin,
                     #                         ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Activity Type"),
            title_display = T("Activity Type"),
            title_list = T("Activity Types"),
            title_update = T("Edit Activity Type"),
            title_upload = T("Import Activity Types"),
            label_list_button = T("List Activity Types"),
            label_delete_button = T("Delete Activity Type"),
            msg_record_created = T("Activity Type added"),
            msg_record_modified = T("Activity Type updated"),
            msg_record_deleted = T("Activity Type deleted"),
            msg_list_empty = T("No Activity Types found"))

        comment = S3PopupLink(c = "vol",
                              f = "activity_type",
                              label = crud_strings[tablename].label_create,
                              title = T("Activity Type"),
                              )

        represent = S3Represent(lookup=tablename, translate=True)
        activity_type_id = S3ReusableField("activity_type_id", "reference %s" % tablename,
                                           label = T("Activity Type"),
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db,
                                                                  "vol_activity_type.id",
                                                                  represent,
                                                                  #filterby="organisation_id",
                                                                  #filter_opts=filter_opts,
                                                                  )),
                                           ondelete = "CASCADE",
                                           represent = represent,
                                           comment = comment
                                           )

        # Components
        add_components(tablename,
                       # Sectors
                       org_sector = {"link": "vol_activity_type_sector",
                                     "joinby": "activity_type_id",
                                     "key": "sector_id",
                                     "actuate": "link",
                                     },
                       )

        crud_form = S3SQLCustomForm("name",
                                    S3SQLInlineLink("sector",
                                                    label = T("Sectors"),
                                                    field = "sector_id",
                                                    help_field = "comments",
                                                    cols = 4,
                                                    ),
                                    "comments",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  )

        # ---------------------------------------------------------------------
        # Volunteer Activity Types <> Sectors
        # Choice of Sector filters the list of Activity Types
        #
        tablename = "vol_activity_type_sector"
        define_table(tablename,
                     activity_type_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                     self.org_sector_id(empty = False,
                                        ondelete = "CASCADE",
                                        ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Volunteer Activities
        #
        tablename = "vol_activity"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     self.org_organisation_id(),
                     self.org_sector_id(empty = False,
                                        ),
                     self.gis_location_id(),
                     s3_date(future=0),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Activity"),
            title_display = T("Activity"),
            title_list = T("Activities"),
            title_update = T("Edit Activity"),
            title_upload = T("Import Activities"),
            label_list_button = T("List Activities"),
            label_delete_button = T("Delete Activity"),
            msg_record_created = T("Activity added"),
            msg_record_modified = T("Activity updated"),
            msg_record_deleted = T("Activity deleted"),
            msg_list_empty = T("No Activities found"))

        represent = S3Represent(lookup=tablename, show_link=True)
        activity_id = S3ReusableField("activity_id", "reference %s" % tablename,
                                      label = T("Activity"),
                                      requires = IS_ONE_OF(db,
                                                           "vol_activity.id",
                                                           represent,
                                                           #filterby="organisation_id",
                                                           #filter_opts=filter_opts,
                                                           ),
                                      represent = represent,
                                      #comment = comment
                                      )

        # Components
        add_components(tablename,
                       # Activity Types
                       vol_activity_type = {"link": "vol_activity_activity_type",
                                            "joinby": "activity_id",
                                            "key": "activity_type_id",
                                            "actuate": "link",
                                            },
                       # Hours
                       vol_activity_hours = {"name": "hours",
                                             "joinby": "activity_id",
                                             },
                       )

        crud_form = S3SQLCustomForm("organisation_id",
                                    "sector_id",
                                    S3SQLInlineLink("activity_type",
                                                    label = T("Activity Types"),
                                                    field = "activity_type_id",
                                                    #help_field = s3db.project_theme_help_fields,
                                                    cols = 4,
                                                    translate = True,
                                                    # Filter Activity Type by Sector
                                                    filterby = "activity_type_id:vol_activity_type_sector.sector_id",
                                                    match = "sector_id",
                                                    script = '''
$.filterOptionsS3({
 'trigger':'sector_id',
 'target':{'alias':'activity_type','name':'activity_type_id','inlineType':'link'},
 'lookupPrefix':'vol',
 'lookupResource':'activity_type',
 'lookupKey':'activity_type_id:vol_activity_type_sector.sector_id',
 'showEmptyField':false,
 //'tooltip':'project_theme_help_fields(id,name)'
})'''
                                                    ),
                                    (T("Activity Name"), "name"),
                                    "location_id",
                                    "date",
                                    "comments",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  list_fields = ["name",
                                 "organisation_id",
                                 "sector_id",
                                 "activity_activity_type.activity_type_id",
                                 "location_id",
                                 "date",
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Volunteer Activities <> Activity Types link Table
        #
        tablename = "vol_activity_activity_type"
        define_table(tablename,
                     activity_id(ondelete = "CASCADE",
                                 ),
                     activity_type_id(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Volunteer Activities <> People link table
        #
        #vol_roles = current.deployment_settings.get_hrm_vol_roles()

        tablename = "vol_activity_hours"
        define_table(tablename,
                     activity_id(ondelete = "RESTRICT",
                                 ),
                     self.pr_person_id(empty = False,
                                       # Don't create here
                                       comment = None,
                                       ),
                     self.hrm_job_title_id(#readable = vol_roles,
                                           #writable = vol_roles,
                                           ),
                     s3_date(future=0),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     Field("hours", "double",
                           label = T("Hours"),
                           ),
                     # Training records are auto-populated
                     #Field("training", "boolean",
                     #      default = False,
                     #      label = T("Type"),
                     #      represent = lambda opt: \
                     #                  T("Training") if opt else T("Work"),
                     #      writable = False,
                     #      ),
                     #Field("training_id", self.hrm_training,
                     #      label = T("Course"),
                     #      represent = self.hrm_TrainingRepresent(),
                     #      writable = False,
                     #      ),
                     Field.Method("month", vol_activity_hours_month),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Hours"),
            title_display = T("Hours Details"),
            title_list = T("Hours"),
            title_update = T("Edit Hours"),
            title_upload = T("Import Hours"),
            label_list_button = T("List Hours"),
            label_delete_button = T("Delete Hours"),
            msg_record_created = T("Hours added"),
            msg_record_modified = T("Hours updated"),
            msg_record_deleted = T("Hours deleted"),
            msg_list_empty = T("Currently no hours recorded for this volunteer"))

        filter_widgets = [
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            # Doesn't support translations
                            #represent="%(name)s",
                            ),
            S3OptionsFilter("activity_hours_activity_type.activity_type_id",
                            # Doesn't support translation
                            #represent = "%(name)s",
                            ),
            S3OptionsFilter("job_title_id",
                            #label = T("Volunteer Role"),
                            # Doesn't support translation
                            #represent = "%(name)s",
                            ),
            S3DateFilter("date",
                         hide_time = True,
                         ),
            ]

        report_fields = [#"training",
                         #"activity_id",
                         "activity_hours_activity_type.activity_type_id",
                         "job_title_id",
                         #"training_id",
                         (T("Month"), "month"),
                         "hours",
                         "person_id$gender",
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 defaults = Storage(rows = "activity_hours_activity_type.activity_type_id",
                                                    cols = "month",
                                                    fact = "sum(hours)",
                                                    totals = True,
                                                    )
                                 )

        # Components
        add_components(tablename,
                       vol_activity_type = {"link": "vol_activity_hours_activity_type",
                                            "joinby": "activity_hours_id",
                                            "key": "activity_type_id",
                                            "actuate": "link",
                                            },
                       )

        # CRUD form
        crud_form = S3SQLCustomForm("activity_id",
                                    "person_id",
                                    "date",
                                    #"end_date",
                                    "job_title_id",
                                    "hours",
                                    S3SQLInlineLink(
                                        "activity_type",
                                        field = "activity_type_id",
                                        label = T("Activity Types"),
                                        help_field = "comments",
                                        cols = "4",
                                        ),
                                    "comments",
                                    )

        configure(tablename,
                  context = {"person": "person_id",
                             },
                  crud_form = crud_form,
                  extra_fields = ["date"],
                  filter_widgets = filter_widgets,
                  list_fields = ["activity_id",
                                 "person_id",
                                 "activity_hours_activity_type.activity_type_id",
                                 "date",
                                 "job_title_id",
                                 "hours",
                                 ],
                  onaccept = vol_activity_hours_onaccept,
                  ondelete = vol_activity_hours_onaccept,
                  orderby = "vol_activity_hours.date desc",
                  report_options = report_options,
                  )

        # ---------------------------------------------------------------------
        # Volunteer Activity Hours <> Activity Type link table
        #

        # Filter Activity Type List to just those for the Activity
        # We will only add hours on Tab of Activity
        #options = {"trigger": "activity_id",
        #           "target": {"alias": "activity_hours_activity_type",
        #                      "name": "activity_type_id",
        #                      },
        #           "scope": "form",
        #           "lookupPrefix": "vol",
        #           "lookupResource": "activity_type",
        #           "optional": True,
        #           }
        #script = '''$.filterOptionsS3(%s)''' % \
        #                    json.dumps(options, separators=SEPARATORS)

        tablename = "vol_activity_hours_activity_type"
        define_table(tablename,
                     Field("activity_hours_id", "reference vol_activity_hours"),
                     activity_type_id(#script = script,
                                      ),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def vol_activity_hours_month(row):
    """
        Virtual field for vol_activity_hours - returns the date of the first
        day of the month of this entry, used for activity hours report.

        Requires "date" to be in the additional report_fields

        @param row: the Row
    """

    try:
        thisdate = row["vol_activity_hours.date"]
    except AttributeError:
        return current.messages["NONE"]
    if not thisdate:
        return current.messages["NONE"]

    #thisdate = thisdate.date()
    month = thisdate.month
    year = thisdate.year
    first = datetime.date(year, month, 1)

    return first.strftime("%y-%m")

# =============================================================================
def vol_activity_hours_onaccept(form):
    """
        Update the Active Status for the volunteer
        - called both onaccept & ondelete
    """

    vol_active = current.deployment_settings.get_hrm_vol_active()
    if not callable(vol_active):
        # Nothing to do (either field is disabled or else set manually)
        return

    # Deletion and update have a different format
    delete = False
    try:
        record_id = form.vars.id
    except AttributeError:
        record_id = form.id
        delete = True

    # Get the full record
    db = current.db
    table = db.vol_activity_hours
    record = db(table.id == record_id).select(table.person_id,
                                              table.deleted_fk,
                                              limitby=(0, 1),
                                              ).first()

    if delete:
        deleted_fks = json.loads(record.deleted_fk)
        person_id = deleted_fks["person_id"]
    else:
        person_id = record.person_id

    # Recalculate the Active Status for this Volunteer
    active = vol_active(person_id)

    # Read the current value
    s3db = current.s3db
    dtable = s3db.vol_details
    htable = s3db.hrm_human_resource
    query = (htable.person_id == person_id) & \
            (dtable.human_resource_id == htable.id)
    row = db(query).select(dtable.id,
                           dtable.active,
                           limitby=(0, 1)).first()
    if row:
        if row.active != active:
            # Update
            db(dtable.id == row.id).update(active=active)
    else:
        # Create record
        row = db(htable.person_id == person_id).select(htable.id,
                                                       limitby=(0, 1)
                                                       ).first()
        if row:
            dtable.insert(human_resource_id = row.id,
                          active = active)

# =============================================================================
class S3VolunteerAwardModel(S3Model):

    names = ("vol_award",
             "vol_volunteer_award",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Volunteer Award
        #
        tablename = "vol_award"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     self.org_organisation_id(default = root_org,
                                              readable = is_admin,
                                              writable = is_admin,
                                              ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Award"),
            title_display = T("Award"),
            title_list = T("Awards"),
            title_update = T("Edit Award"),
            title_upload = T("Import Awards"),
            label_list_button = T("List Awards"),
            label_delete_button = T("Delete Award"),
            msg_record_created = T("Award added"),
            msg_record_modified = T("Award updated"),
            msg_record_deleted = T("Award deleted"),
            msg_list_empty = T("No Awards found"))

        comment = S3PopupLink(c = "vol",
                              f = "award",
                              label = crud_strings[tablename].label_create,
                              title = T("Award"),
                              )

        represent = S3Represent(lookup=tablename)
        award_id = S3ReusableField("award_id", "reference %s" % tablename,
                                   label = T("Award"),
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db,
                                                          "vol_award.id",
                                                          represent,
                                                          filterby="organisation_id",
                                                          filter_opts=filter_opts)),
                                   represent = represent,
                                   comment = comment
                                   )

        # ---------------------------------------------------------------------
        # Volunteers <> Awards link table
        #
        tablename = "vol_volunteer_award"
        define_table(tablename,
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     award_id(),
                     s3_date(future = 0,
                             ),
                     Field("number",
                           label = T("Number"),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("file", "upload",
                           autodelete = True,
                           label = T("Attachment"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.vol_award_file_represent,
                           requires = IS_LENGTH(current.MAX_FILENAME_LENGTH),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Award"),
            title_display = T("Award"),
            title_list = T("Awards"),
            title_update = T("Edit Award"),
            title_upload = T("Import Awards"),
            label_list_button = T("List Awards"),
            label_delete_button = T("Delete Award"),
            msg_record_created = T("Award added"),
            msg_record_modified = T("Award updated"),
            msg_record_deleted = T("Award deleted"),
            msg_list_empty = T("No Awards found"))

        self.configure(tablename,
                       context = {"person": "person_id"},
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def vol_award_file_represent(filename):
        """
            File representation

            @param filename: the stored file name (field value)

            @return: a link to download the file
        """

        if filename:
            try:
                # Check whether file exists and extract the original
                # file name from the stored file name
                origname = current.db.vol_volunteer_award.file.retrieve(filename)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(origname,
                         _href=URL(c="default", f="download", args=[filename]))
        else:
            return current.messages["NONE"]

# =============================================================================
class S3VolunteerClusterModel(S3Model):
    """
        Fucntionality to support the Philippines Red Cross
    """

    names = ("vol_cluster_type",
             "vol_cluster",
             "vol_cluster_position",
             "vol_volunteer_cluster",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster_type"
        define_table(tablename,
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(255),
                                       ],
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster Type"),
            title_display = T("Volunteer Cluster Type"),
            title_list = T("Volunteer Cluster Type"),
            title_update = T("Edit Volunteer Cluster Type"),
            title_upload = T("Import Volunteer Cluster Types"),
            label_list_button = T("List Volunteer Cluster Types"),
            label_delete_button = T("Delete Volunteer Cluster Type"),
            msg_record_created = T("Volunteer Cluster Type added"),
            msg_record_modified = T("Volunteer Cluster Type updated"),
            msg_record_deleted = T("Volunteer Cluster Type deleted"),
            msg_list_empty = T("No Volunteer Cluster Types"))

        comment = S3PopupLink(c = "vol",
                              f = "cluster_type",
                              vars = {"child": "vol_cluster_type_id",
                                      "parent": "volunteer_cluster",
                                      },
                              label = crud_strings[tablename].label_create,
                              title = T("Volunteer Cluster Type"),
                              )

        represent = S3Represent(lookup=tablename)
        vol_cluster_type_id = S3ReusableField("vol_cluster_type_id", "reference %s" % tablename,
                                              label = T("Volunteer Cluster Type"),
                                              requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_type.id",
                                                                      represent)),
                                              represent = represent,
                                              comment = comment
                                              )

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster"
        define_table(tablename,
                     vol_cluster_type_id(),
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(255),
                                       ],
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster"),
            title_display = T("Volunteer Cluster"),
            title_list = T("Volunteer Cluster"),
            title_update = T("Edit Volunteer Cluster"),
            title_upload = T("Import Volunteer Clusters"),
            label_list_button = T("List Volunteer Clusters"),
            label_delete_button = T("Delete Volunteer Cluster"),
            msg_record_created = T("Volunteer Cluster added"),
            msg_record_modified = T("Volunteer Cluster updated"),
            msg_record_deleted = T("Volunteer Cluster deleted"),
            msg_list_empty = T("No Volunteer Clusters"))

        comment = S3PopupLink(c = "vol",
                              f = "cluster",
                              vars = {"child": "vol_cluster_id",
                                      "parent": "volunteer_cluster",
                                      },
                              label = crud_strings[tablename].label_create,
                              title = T("Volunteer Cluster"),
                              )

        represent = S3Represent(lookup=tablename)
        vol_cluster_id = S3ReusableField("vol_cluster_id", "reference %s" % tablename,
                                         label = T("Volunteer Cluster"),
                                         requires = IS_EMPTY_OR(
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
        define_table(tablename,
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(255),
                                       ],
                           ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster Position"),
            title_display = T("Volunteer Cluster Position"),
            title_list = T("Volunteer Cluster Position"),
            title_update = T("Edit Volunteer Cluster Position"),
            title_upload = T("Import Volunteer Cluster Positions"),
            label_list_button = T("List Volunteer Cluster Positions"),
            label_delete_button = T("Delete Volunteer Cluster Position"),
            msg_record_created = T("Volunteer Cluster Position added"),
            msg_record_modified = T("Volunteer Cluster Position updated"),
            msg_record_deleted = T("Volunteer Cluster Position deleted"),
            msg_list_empty = T("No Volunteer Cluster Positions"))

        comment = S3PopupLink(c = "vol",
                              f = "cluster_position",
                              vars = {"child": "vol_cluster_position_id",
                                      "parent": "volunteer_cluster",
                                      },
                              label = crud_strings[tablename].label_create,
                              title = T("Volunteer Cluster Position"),
                              )

        represent = S3Represent(lookup=tablename)
        vol_cluster_position_id = S3ReusableField("vol_cluster_position_id", "reference %s" % tablename,
                                                label = T("Volunteer Cluster Position"),
                                                requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_position.id",
                                                                      represent)),
                                                represent = represent,
                                                comment = comment
                                                )

        # ---------------------------------------------------------------------
        # Volunteer Cluster Link Table
        cluster_type_filter = '''
$.filterOptionsS3({
 'trigger':'vol_cluster_type_id',
 'target':'vol_cluster_id',
 'lookupKey':'vol_cluster_type_id',
 'lookupPrefix':'vol',
 'lookupResource':'cluster',
})'''

        tablename = "vol_volunteer_cluster"
        define_table(tablename,
                     self.hrm_human_resource_id(ondelete = "CASCADE"),
                     vol_cluster_type_id(script = cluster_type_filter), # This field is ONLY here to provide a filter
                     vol_cluster_id(readable=False,
                                    writable=False),
                     vol_cluster_position_id(readable=False,
                                             writable=False),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {"vol_cluster_type_id": vol_cluster_type_id,
                "vol_cluster_id": vol_cluster_id,
                }

    # =====================================================================
    @staticmethod
    def defaults():
        """
            Return safe defaults for model globals, this will be called instead
            of model() in case the model has been deactivated in
            deployment_settings.
        """

        return {"vol_cluster_id": S3ReusableField("vol_cluster_id",
                                                  "integer",
                                                  readable = False,
                                                  writable = False,
                                                  ),
                }

# =============================================================================
def vol_service_record(r, **attr):
    """
        Generate a Volunteer Service Record
    """

    record = r.record
    if record.type != 2:
        # Only relevant to volunteers
        return None

    T = current.T
    db = current.db
    settings = current.deployment_settings

    ptable = db.pr_person
    person_id = record.person_id
    person = db(ptable.id == person_id).select(ptable.pe_id,
                                               ptable.first_name,
                                               ptable.middle_name,
                                               ptable.last_name,
                                               ptable.comments,
                                               limitby=(0, 1),
                                               ).first()
    vol_name = s3_fullname(person)

    def callback(r):

        # Header
        s3db = current.s3db
        otable = db.org_organisation
        org_id = record.organisation_id
        org = db(otable.id == org_id).select(otable.name,
                                             otable.acronym, # Present for consistent cache key
                                             otable.logo,
                                             limitby=(0, 1),
                                             ).first()
        if settings.get_L10n_translate_org_organisation():
            org_name = s3db.org_OrganisationRepresent(parent=False,
                                                      acronym=False)(org_id)
        else:
            org_name = org.name

        logo = org.logo
        if logo:
            logo = s3db.org_organisation_logo(org)
        elif settings.get_org_branches():
            root_org = current.cache.ram(
                # Common key with auth.root_org
                "root_org_%s" % org_id,
                lambda: s3db.org_root_organisation(org_id),
                time_expire=120
                )
            logo = s3db.org_organisation_logo(root_org)

        innerTable = TABLE(TR(TH(vol_name)),
                           TR(TD(org_name)))
        if current.response.s3.rtl:
            # Right-to-Left
            person_details = TABLE(TR(TD(innerTable),
                                      TD(logo),
                                      ))
        else:
            person_details = TABLE(TR(TD(logo),
                                      TD(innerTable),
                                      ))

        pe_id = person.pe_id

        # Photo
        itable = s3db.pr_image
        query = (itable.pe_id == pe_id) & \
                (itable.profile == True)
        image = db(query).select(itable.image,
                                 limitby=(0, 1)).first()
        if image:
            image = image.image
            size = (160, None)
            image = s3db.pr_image_library_represent(image, size=size)
            size = s3db.pr_image_size(image, size)
            url = URL(c="default",
                      f="download",
                      args=image)
            avatar = IMG(_src=url,
                         _width=size[0],
                         _height=size[1],
                         )
            person_details[0].append(TD(avatar))

        # Addresses
        addrtable = s3db.pr_address
        ltable = db.gis_location
        query = (addrtable.pe_id == pe_id) & \
                (addrtable.location_id == ltable.id)
        addresses = db(query).select(addrtable.type,
                                     ltable.addr_street,
                                     ltable.L3,
                                     ltable.L2,
                                     ltable.L1,
                                     orderby = addrtable.type,
                                     limitby=(0, 2))
        address_list = []
        for address in addresses:
            _location = address["gis_location"]
            address = TABLE(TR(TH(addrtable.type.represent(address["pr_address"].type))),
                            TR(_location.addr_street),
                            TR(_location.L3),
                            TR(_location.L2),
                            TR(_location.L1),
                            )
            address_list.append(address)

        # Contacts
        ctable = s3db.pr_contact
        contacts = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                    ctable.value,
                                                    orderby = ctable.priority,
                                                    limitby=(0, 3))
        contact_list = TABLE()
        contact_represent = ctable.contact_method.represent
        for contact in contacts:
            contact_list.append(TH(contact_represent(contact.contact_method)))
            contact_list.append(contact.value)

        # Emergency Contact
        #ectable = s3db.pr_contact_emergency
        #emergency = db(ectable.pe_id == pe_id).select(ectable.name,
        #                                              ectable.relationship,
        #                                              ectable.phone,
        #                                              limitby=(0, 1)).first()
        #if emergency:
        #    econtact = TABLE(TR(TH(T("Emergency Contact"))),
        #                     TR(emergency.name),
        #                     TR(emergency.relationship),
        #                     TR(emergency.phone),
        #                     )
        #else:
        #    econtact = TABLE()
        contact_row = TR()
        if len(address_list) > 0:
            contact_row.append(TD(address_list[0]))
        if len(address_list) > 1:
            contact_row.append(TD(address_list[1]))
        contact_row.append(contact_list)
        #contact_row.append(econtact)

        # Identity
        idtable = s3db.pr_identity
        query = (idtable.person_id == person_id) & \
                (idtable.deleted == False)
        rows = db(query).select(idtable.type,
                                idtable.value,
                                idtable.valid_until)
        id_row = TR()
        for identity in rows:
            id_row.append(TABLE(TR(TH(idtable.type.represent(identity.type))),
                                TR(identity.value),
                                TR(identity.valid_until),
                                ))

        # Comments:
        comments = person.comments or ""
        if comments:
            comments = TABLE(TR(TH(T("Comments"))),
                             TR(comments))

        # Training Courses
        hours = {}
        ttable = s3db.hrm_training
        ctable = s3db.hrm_course
        query = (ttable.deleted == False) & \
                (ttable.person_id == person_id) & \
                (ttable.course_id == ctable.id)
        rows = db(query).select(ctable.name,
                                ttable.date,
                                ttable.hours,
                                orderby = ~ttable.date)
        date_represent = ttable.date.represent
        for row in rows:
            _row = row["hrm_training"]
            _date = _row.date
            hours[_date.date()] = {"course": row["hrm_course"].name,
                                   "date": date_represent(_date),
                                   "hours": _row.hours or "",
                                   }
        courses = TABLE(TR(TH(T("Date")),
                           TH(T("Training")),
                           TH(T("Hours"))))
        _hours = {}
        for key in sorted(hours.keys()):
            _hours[key] = hours[key]
        total = 0
        for hour in hours:
            _hour = hours[hour]
            __hours = _hour["hours"] or 0
            courses.append(TR(_hour["date"],
                              _hour["course"],
                              str(__hours)
                              ))
            total += __hours
        if total > 0:
            courses.append(TR(TD(""), TD("Total"), TD("%d" % total)))

        vol_experience = settings.get_hrm_vol_experience()
        if vol_experience == "activity":
            # Activity Hours
            # - grouped by Activity Type/Role
            activity_types = OrderedDict()
            hrstable = s3db.vol_activity_hours
            attable = db.vol_activity_type
            ltable = db.vol_activity_hours_activity_type
            jtable = db.hrm_job_title
            query = (hrstable.deleted == False) & \
                    (hrstable.person_id == person_id)
            left = [jtable.on(hrstable.job_title_id == jtable.id),
                    attable.on((hrstable.id == ltable.activity_hours_id) & \
                               (ltable.activity_type_id == attable.id)),
                    ]
            rows = db(query).select(hrstable.date,
                                    hrstable.hours,
                                    jtable.name,
                                    attable.name,
                                    left=left,
                                    orderby = ~hrstable.date)
            NONE = current.messages["NONE"]
            for row in rows:
                _row = row["vol_activity_hours"]
                _date = _row.date
                hours = _row.hours or 0
                role = row["hrm_job_title"]["name"] or NONE
                atrow = row["vol_activity_type"]
                atype = atrow.name
                if atype not in activity_types:
                    activity_types[atype] = OrderedDict()
                a = activity_types[atype]
                if role in a:
                    a[role]["end_date"] = _date
                    a[role]["hours"] += hours
                else:
                    a[role] = {"start_date": _date,
                               "end_date": _date,
                               "hours": hours,
                               }
            date_represent = hrstable.date.represent
            programme = TABLE(TR(TH(T("Start Date")),
                                 TH(T("End Date")),
                                 TH(T("Activity Type")),
                                 TH(T("Role")),
                                 TH(T("Hours"))))
            total = 0
            for a in activity_types:
                _a = activity_types[a]
                for r in _a:
                    role = _a[r]
                    hours = role["hours"]
                    total += hours
                    programme.append(TR(date_represent(role["start_date"]),
                                        date_represent(role["end_date"]),
                                        a,
                                        r,
                                        str(hours)
                                        ))

            if total > 0:
                programme.append(TR("", "", "", TD("Total"), TD("%d" % total)))

        elif vol_experience in ("programme", "both"):
            # Programme Hours
            # - grouped by Programme/Role
            programmes = OrderedDict()
            hrstable = s3db.hrm_programme_hours
            ptable = db.hrm_programme
            jtable = db.hrm_job_title
            query = (hrstable.deleted == False) & \
                    (hrstable.training == False) & \
                    (hrstable.person_id == person_id) & \
                    (hrstable.programme_id == ptable.id)
            left = jtable.on(hrstable.job_title_id == jtable.id)
            rows = db(query).select(hrstable.date,
                                    hrstable.hours,
                                    jtable.name,
                                    ptable.name,
                                    ptable.name_long,
                                    left=left,
                                    orderby = ~hrstable.date)
            NONE = current.messages["NONE"]
            for row in rows:
                _row = row["hrm_programme_hours"]
                _date = _row.date
                hours = _row.hours or 0
                role = row["hrm_job_title"]["name"] or NONE
                prow = row["hrm_programme"]
                if prow.name_long:
                    programme = prow.name_long
                else:
                    programme = prow.name
                if programme not in programmes:
                    programmes[programme] = OrderedDict()
                p = programmes[programme]
                if role in p:
                    p[role]["end_date"] = _date
                    p[role]["hours"] += hours
                else:
                    p[role] = {"start_date": _date,
                               "end_date": _date,
                               "hours": hours,
                               }
            date_represent = hrstable.date.represent
            programme = TABLE(TR(TH(T("Start Date")),
                                 TH(T("End Date")),
                                 TH(T("Work on Program")),
                                 TH(T("Role")),
                                 TH(T("Hours"))))
            total = 0
            for p in programmes:
                _p = programmes[p]
                for r in _p:
                    role = _p[r]
                    hours = role["hours"]
                    total += hours
                    programme.append(TR(date_represent(role["start_date"]),
                                        date_represent(role["end_date"]),
                                        p,
                                        r,
                                        str(hours)
                                        ))

            if total > 0:
                programme.append(TR("", "", "", TD("Total"), TD("%d" % total)))
        else:
            programme = ""

        # Space for the printed document to be signed
        datestamp = S3DateTime.date_represent(current.request.now)
        datestamp = "%s: %s" % (T("Date Printed"), datestamp)
        manager = settings.get_hrm_vol_service_record_manager()
        signature = TABLE(TR(TH(T("Signature"))),
                          TR(TD()),
                          TR(TD(manager)),
                          TR(TD(datestamp)))

        output = DIV(TABLE(TR(TH(T("Volunteer Service Record")))),
                     person_details,
                     TABLE(contact_row),
                     TABLE(id_row),
                     TABLE(comments),
                     TABLE(courses),
                     TABLE(programme),
                     TABLE(signature),
                     )

        return output

    from s3.s3export import S3Exporter
    exporter = S3Exporter().pdf
    pdf_title = "%s - %s" % (s3_str(vol_name),
                             s3_str(T("Volunteer Service Record")),
                             )
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = pdf_title,
                    pdf_table_autogrow = "B",
                    pdf_callback = callback,
                    **attr
                    )

# =============================================================================
def vol_volunteer_controller():
    """ Volunteers Controller """

    s3 = current.response.s3
    s3db = current.s3db
    settings = current.deployment_settings
    T = current.T

    # Volunteers only
    s3.filter = FS("type") == 2

    vol_experience = settings.get_hrm_vol_experience()

    def prep(r):
        resource = r.resource

        # CRUD String
        s3.crud_strings[resource.tablename] = s3.crud_strings["hrm_volunteer"]

        # Default to volunteers
        table = r.table
        table.type.default = 2

        if settings.get_hrm_unavailability():
            # Apply availability filter
            s3db.pr_availability_filter(r)

        # Configure list_fields
        if r.representation == "xls":
            s3db.hrm_xls_list_fields(r, staff=False)
        else:
            list_fields = ["person_id",
                           "person_id$gender",
                           ]
            if settings.get_hrm_use_code() is True:
                list_fields.append("code")
            if settings.get_hrm_vol_roles():
                list_fields.append("job_title_id")
            if settings.get_hrm_vol_departments():
                list_fields.append("department_id")
            if settings.get_hrm_multiple_orgs():
                list_fields.append("organisation_id")
            list_fields.extend(((settings.get_ui_label_mobile_phone(), "phone.value"),
                                (T("Email"), "email.value"),
                                ))
            # Volunteers use home address
            location_id = table.location_id
            location_id.label = T("Home Address")
            list_fields.append("location_id")
            if settings.get_hrm_use_trainings():
                list_fields.append((T("Trainings"), "person_id$training.course_id"))
            if settings.get_hrm_use_certificates():
                list_fields.append((T("Certificates"), "person_id$certification.certificate_id"))

            # Volunteer Programme and Active-status
            report_options = resource.get_config("report_options")
            if vol_experience in ("programme", "both"):
                # Don't use status field
                table.status.readable = table.status.writable = False
                # Use active field?
                vol_active = settings.get_hrm_vol_active()
                if vol_active:
                    list_fields.insert(3, (T("Active?"), "details.active"))
                # Add Programme to List Fields
                list_fields.insert(6, "person_id$hours.programme_id")

                # Add active and programme to Report Options
                report_fields = report_options.rows
                report_fields.append("person_id$hours.programme_id")
                if vol_active:
                    report_fields.append((T("Active?"), "details.active"))
                report_options.rows = report_fields
                report_options.cols = report_fields
                report_options.fact = report_fields
            else:
                # Use status field
                list_fields.append("status")

            # Update filter widgets
            filter_widgets = \
                s3db.hrm_human_resource_filters(resource_type = "volunteer",
                                                hrm_type_opts = s3db.hrm_type_opts)

            # Reconfigure
            resource.configure(list_fields = list_fields,
                               filter_widgets = filter_widgets,
                               )

        if r.interactive:
            if s3.rtl:
                # Ensure that + appears at the beginning of the number
                # - using table alias to only apply to filtered component
                f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                f.represent = s3_phone_represent
                f.widget = S3PhoneWidget()

            if r.id:
                if r.method not in ("profile", "delete"):
                    # Redirect to person controller
                    req_vars = {"human_resource.id": r.id,
                                "group": "volunteer"
                                }
                    if r.representation == "iframe":
                        req_vars["format"] = "iframe"
                        args = [r.method]
                    else:
                        args = []
                    redirect(URL(f="person", vars=req_vars, args=args))
            else:
                if r.method == "import":
                    # Redirect to person controller
                    redirect(URL(f="person",
                                 args="import",
                                 vars={"group": "volunteer"}))

                elif not r.component and r.method != "delete":
                    # Use vol controller for person_id widget
                    table.person_id.widget = S3AddPersonWidget(controller="vol")
                    # Show location ID
                    location_id.writable = location_id.readable = True
                    # Hide unwanted fields
                    for fn in ("site_id",
                               "department_id",
                               "essential",
                               "site_contact",
                               "status",
                               ):
                        table[fn].writable = table[fn].readable = False
                    # Hide volunteer ID as per setting
                    if settings.get_hrm_use_code() is not True:
                        table.code.readable = table.code.writable = False
                    # Organisation Dependent Fields
                    # @ToDo: Move these to the IFRC Template & make Lazy settings
                    set_org_dependent_field = settings.set_org_dependent_field
                    set_org_dependent_field("pr_person_details", "father_name")
                    set_org_dependent_field("pr_person_details", "mother_name")
                    set_org_dependent_field("pr_person_details", "affiliations")
                    set_org_dependent_field("pr_person_details", "company")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")
                    # Label for "occupation"
                    s3db.pr_person_details.occupation.label = T("Normal Job")
                    # Assume staff only between 12-81
                    dob = s3db.pr_person.date_of_birth
                    dob.widget = S3CalendarWidget(past_months = 972,
                                                  future_months = -144,
                                                  )
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and not r.component:
            # Configure action buttons
            S3CRUD.action_buttons(r, deletable=settings.get_hrm_deletable())
            if settings.has_module("msg") and \
               settings.get_hrm_compose_button() and \
               current.auth.permission.has_permission("update", c="hrm", f="compose"):
                # @ToDo: Remove this now that we have it in Events?
                s3.actions.append({
                        "url": URL(f="compose",
                                    vars = {"human_resource.id": "[id]"}),
                        "_class": "action-btn send",
                        "label": str(T("Send Message"))
                    })

        elif r.representation == "plain":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp

    return current.rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def vol_person_controller():
    """
        Person Controller
        - used to see PR component tabs, for Personal Profile & Imports
        - includes components relevant to HRM
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    get_vars = current.request.get_vars
    response = current.response
    s3 = response.s3
    session = current.session
    settings = current.deployment_settings
    resourcename = "person"

    configure = s3db.configure
    set_method = s3db.set_method

    # Custom Method for Contacts
    set_method("pr", resourcename,
               method = "contacts",
               action = s3db.pr_Contacts)

    # Custom Method for CV
    set_method("pr", resourcename,
               method = "cv",
               action = s3db.hrm_CV)

    # Custom Method for HR Record
    set_method("pr", resourcename,
               method = "record",
               action = s3db.hrm_Record)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_components("pr_person", asset_asset="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        configure("asset_asset",
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

    group = get_vars.get("group", "volunteer")
    hr_id = get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    table = s3db.hrm_human_resource
    table.type.default = 2
    get_vars["xsltmode"] = "volunteer"
    if hr_id:
        hr = db(table.id == hr_id).select(table.type,
                                          limitby=(0, 1)).first()
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            get_vars["group"] = group

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    configure(tablename,
              deletable = False,
              )

    #mode = session.s3.hrm.mode
    #if mode is not None:
    #    # Configure for personal mode
    #    s3db.hrm_human_resource.organisation_id.readable = True
    #    s3.crud_strings[tablename].update(
    #        title_display = T("Personal Profile"),
    #        title_update = T("Personal Profile"))
    #    # People can view their own HR data, but not edit it
    #    configure("hrm_human_resource",
    #              insertable = False,
    #              editable = False,
    #              deletable = False)
    #    configure("hrm_certification",
    #              insertable = True,
    #              editable = True,
    #              deletable = True)
    #    configure("hrm_credential",
    #              insertable = False,
    #              editable = False,
    #              deletable = False)
    #    configure("hrm_competency",
    #              insertable = True,  # Can add unconfirmed
    #              editable = False,
    #              deletable = False)
    #    configure("hrm_training",    # Can add but not provide grade
    #              insertable = True,
    #              editable = False,
    #              deletable = False)
    #    configure("hrm_experience",
    #              insertable = False,
    #              editable = False,
    #              deletable = False)
    #    configure("pr_group_membership",
    #              insertable = False,
    #              editable = False,
    #              deletable = False)
    #else:
    # Configure for HR manager mode
    s3.crud_strings[tablename].update(
            title_display = T("Volunteer Details"),
            title_update = T("Volunteer Details"),
            title_upload = T("Import Volunteers"),
            )

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: {"ReplaceOption": T("Remove existing data before import")}

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the organisation
            before processing a new data import, used for the import_prep
            hook in response.s3
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                else:
                    return # don't delete if no group specified

                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3db.resource("hrm_human_resource", filter=query)
                        resource.delete(format="xml", cascade=True)
    s3.import_prep = import_prep

    # CRUD pre-process
    def prep(r):

        # Plug-in role matrix for Admins/OrgAdmins
        S3PersonRoleManager.set_method(r, entity="pr_person")

        method = r.method
        if r.representation == "s3json":
            current.xml.show_ids = True
        elif r.interactive and method != "import":
            if s3.rtl:
                # Ensure that + appears at the beginning of the number
                # - using table alias to only apply to filtered component
                f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                f.represent = s3_phone_represent
                f.widget = S3PhoneWidget()

            if not r.component:
                table = r.table
                # Assume volunteers only between 12-81
                dob = table.date_of_birth
                dob.widget = S3CalendarWidget(past_months = 972,
                                              future_months = -144,
                                              )
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False
                table.age_group.readable = table.age_group.writable = False

                s3db.pr_person_details.occupation.label = T("Normal Job")

                # Organisation Dependent Fields
                # @ToDo: Move these to the IFRC Template & make Lazy settings
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person", "middle_name")
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "grandfather_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "year_of_birth")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")

            else:
                component_name = r.component_name
                if component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False,
                              )

                elif component_name == "group_membership":
                    s3db.hrm_configure_pr_group_membership()

                elif component_name == "hours":
                    # Exclude records which are just to link to Programme
                    component_table = r.component.table
                    query = (r.component.table.hours != None)
                    r.resource.add_component_filter("hours", query)
                    component_table.training.readable = False
                    component_table.training_id.readable = False

                elif component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = table.ethnicity.readable = True
                    table.blood_type.writable = table.blood_type.readable = True
                    table.medical_conditions.writable = table.medical_conditions.readable = True
                    table.other_details.writable = table.other_details.readable = True

                elif component_name == "training":
                    external = get_vars.get("~.course_id$external")
                    if external is not None:
                        table = s3db.hrm_course
                        query = (table.deleted == False)
                        ADMIN = session.s3.system_roles.ADMIN
                        auth = current.auth
                        if not auth.s3_has_role(ADMIN):
                            query &= ((table.organisation_id == auth.root_org()) | \
                                      (table.organisation_id == None))
                        if external == "True":
                            query &= (table.external == True)
                        else:
                            query &= (table.external == False)
                        rows = db(query).select(table.id)
                        filter_opts = [row.id for row in rows]
                        field = s3db.hrm_training.course_id
                        field.requires = IS_ONE_OF(db, "hrm_course.id",
                                                   field.represent,
                                                   filterby="id",
                                                   filter_opts=filter_opts,
                                                   )

            if method == "record" or r.component_name == "human_resource":
                table = s3db.hrm_human_resource
                table.code.writable = table.code.readable = False
                table.department_id.writable = table.department_id.readable = False
                table.essential.writable = table.essential.readable = False
                #table.location_id.readable = table.location_id.writable = True
                table.person_id.writable = table.person_id.readable = False
                table.site_id.writable = table.site_id.readable = False
                table.site_contact.writable = table.site_contact.readable = False
                #org = session.s3.hrm.org
                #field = table.organisation_id
                #if org is None:
                #    field.widget = None
                #else:
                #    field.default = org
                #    field.readable = field.writable = False

                # Organisation Dependent Fields
                # @ToDo: Move these to the IFRC Template & make Lazy settings
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")

            elif method == "cv" or r.component_name == "training":
                list_fields = ["course_id",
                               "grade",
                               ]
                if settings.get_hrm_course_pass_marks:
                    list_fields.append("grade_details")
                list_fields.append("date")
                s3db.configure("hrm_training",
                               list_fields = list_fields,
                               )

            resource = r.resource
            #if mode is not None:
            #    r.resource.build_query(id=current.auth.s3_logged_in_person())
            if method not in ("deduplicate", "search_ac"):
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="volunteer"))
                if resource.count() == 1:
                    resource.load()
                    r.record = resource.records().first()
                    if r.record:
                        r.id = r.record.id
                if not r.record:
                    session.error = T("Record not found")
                    redirect(URL(f="volunteer"))
                if hr_id and r.component_name == "human_resource":
                    r.component_id = hr_id
                configure("hrm_human_resource",
                          insertable = False)

        elif r.representation == "aadata":
            if r.component_name == "group_membership":
                s3db.hrm_configure_pr_group_membership()
            elif method == "cv" or r.component_name == "training":
                list_fields = ["course_id",
                               "grade",
                               ]
                if settings.get_hrm_course_pass_marks:
                    list_fields.append("grade_details")
                list_fields.append("date")
                s3db.configure("hrm_training",
                               list_fields = list_fields,
                               )

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both") and \
                   r.method not in ("report", "import") and \
                   "form" in output:
                    # Insert field to set the Programme
                    # @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
                    sep = ": "
                    table = s3db.hrm_programme_hours
                    field = table.programme_id
                    if r.id:
                        query = (table.person_id == r.id)
                        default = db(query).select(table.programme_id,
                                                   orderby=table.date).last()
                        if default:
                            default = default.programme_id
                    else:
                        default = field.default
                    widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                    field_id = "%s_%s" % (table._tablename, field.name)
                    label = field.label
                    label = LABEL(label, label and sep, _for=field_id,
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                    s3_formstyle = settings.get_ui_formstyle()
                    programme = s3_formstyle(row_id, label, widget,
                                             field.comment)
                    try:
                        output["form"][0].insert(2, programme[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(2, programme[0])
                    except:
                        pass

            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    #orgname = session.s3.hrm.orgname

    return current.rest_controller("pr", resourcename,
                                   csv_template = ("hrm", "volunteer"),
                                   csv_stylesheet = ("hrm", "person.xsl"),
                                   csv_extra_fields = [
                                        {"label": "Type",
                                         "field": s3db.hrm_human_resource.type,
                                         }
                                        ],
                                   #orgname = orgname,
                                   replace_option = T("Remove existing data before import"),
                                   rheader = s3db.hrm_rheader,
                                   )

# END =========================================================================
