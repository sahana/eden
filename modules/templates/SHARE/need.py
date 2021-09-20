# -*- coding: utf-8 -*-

""" Sahana Eden Needs Model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("NeedsActivityModel",
           "NeedsDemographicsModel",
           "NeedsLineModel",
           "NeedsResponseModel",
           "NeedsResponseEventModel",
           "NeedsResponseLineModel",
           "NeedsResponseOrganisationModel",
           "NeedsSectorModel",
           #"need_rheader",
           )

from gluon import *
from gluon.storage import Storage
from s3 import *
from s3layouts import S3PopupLink

# =============================================================================
def need_timeframe():
    T = current.T
    timeframe_opts = {1: T("0-12 hours"),
                      2: T("12-24 hours"),
                      3: T("1-2 days"),
                      4: T("2-4 days"),
                      5: T("5-7 days"),
                      6: T(">1 week"),
                      }
    return S3ReusableField("timeframe", "integer",
                           default = 3,
                           label = T("Timeframe"),
                           represent = S3Represent(options = timeframe_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(timeframe_opts,
                                                  zero = None,
                                                  ),
                                        ),
                           )

# =============================================================================
class NeedsActivityModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Activities (Activity created to respond to Need)
    """

    names = ("need_activity",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Needs <=> Activities
        #

        tablename = "need_activity"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.project_activity_id(empty = False),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "activity_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class NeedsDemographicsModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Demographics

        @ToDo: Auto-populate defaults for Items based on Demographics
    """

    names = ("need_demographic",
             )

    def model(self):

        T = current.T

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        # ---------------------------------------------------------------------
        # Needs <=> Demographics
        #
        if current.s3db.table("stats_demographic"):
            title = current.response.s3.crud_strings["stats_demographic"].label_create
            parameter_id_comment = S3PopupLink(c = "stats",
                                               f = "demographic",
                                               vars = {"child": "parameter_id"},
                                               title = title,
                                               )
        else:
            parameter_id_comment = None

        tablename = "need_demographic"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.super_link("parameter_id", "stats_parameter",
                                          instance_types = ("stats_demographic",),
                                          label = T("Demographic"),
                                          represent = self.stats_parameter_represent,
                                          readable = True,
                                          writable = True,
                                          empty = False,
                                          comment = parameter_id_comment,
                                          ),
                          need_timeframe()(),
                          Field("value", "double",
                                label = T("Number"),
                                #label = T("Number in Need"),
                                represent = float_represent,
                                requires = IS_NOT_EMPTY(),
                                ),
                          Field("value_committed", "double",
                                label = T("Number Committed"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("value_uncommitted", "double",
                                label = T("Number Uncommitted"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("value_reached", "double",
                                label = T("Number Reached"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "parameter_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class NeedsLineModel(S3Model):
    """
        Simple Requests Management System
        - optional extension to support Demographics & Items within a single Line
    """

    names = ("need_line",
             "need_line_id",
             )

    def model(self):

        T = current.T
        db = current.db

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        if self.table("stats_demographic"):
            title = current.response.s3.crud_strings["stats_demographic"].label_create
            parameter_id_comment = S3PopupLink(c = "stats",
                                               f = "demographic",
                                               vars = {"child": "parameter_id"},
                                               title = title,
                                               )
        else:
            parameter_id_comment = None

        # ---------------------------------------------------------------------
        # Lines
        #

        tablename = "need_line"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          # A less precise location for this line
                          # Here to more easily allow multiple dropdowns within an Inline form
                          self.gis_location_id("coarse_location_id"),
                          # A more precise location for this line
                          self.gis_location_id(),
                          self.org_sector_id(),
                          self.super_link("parameter_id", "stats_parameter",
                                          instance_types = ("stats_demographic",),
                                          #label = T("Demographic"),
                                          label = T("People affected"),
                                          represent = self.stats_parameter_represent,
                                          readable = True,
                                          writable = True,
                                          #empty = False,
                                          comment = parameter_id_comment,
                                          ),
                          Field("value", "double",
                                label = T("Number"),
                                #label = T("Number in Need"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
                          Field("value_committed", "double",
                                label = T("Number Committed"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("value_uncommitted", "double",
                                label = T("Number Uncommitted"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("value_reached", "double",
                                label = T("Number Reached"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          self.supply_item_category_id(),
                          self.supply_item_id(# Default:
                                              #ondelete = "RESTRICT",
                                              requires = IS_EMPTY_OR(self.supply_item_id().requires),
                                              # Filter Item dropdown based on Category
                                              script = '''
$.filterOptionsS3({
 'trigger':'item_category_id',
 'target':'item_id',
 'lookupPrefix':'supply',
 'lookupResource':'item',
})''',
                                              # Don't use Auto-complete
                                              widget = None,
                                              ),
                          self.supply_item_pack_id(requires = IS_EMPTY_OR(self.supply_item_pack_id().requires),
                                                   ),
                          Field("quantity", "double",
                                label = T("Quantity"),
                                #label = T("Quantity Requested"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
                          need_timeframe()(),
                          Field("quantity_committed", "double",
                                label = T("Quantity Committed"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("quantity_uncommitted", "double",
                                label = T("Quantity Uncommitted"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          Field("quantity_delivered", "double",
                                label = T("Quantity Delivered"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                # Enable in templates as-required
                                readable = False,
                                # Normally set automatically
                                writable = False,
                                ),
                          #s3_comments(),
                          req_status()("status",
                                       label = T("Fulfilment Status"),
                                       ),
                          *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            need_response_line = "need_line_id",
                            )

        #represent = S3Represent(lookup = tablename)
        need_line_id = S3ReusableField("need_line_id", "reference %s" % tablename,
                                       label = T("Need"),
                                       ondelete = "SET NULL",
                                       #represent = represent,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "need_line.id",
                                                              #represent,
                                                              #orderby = "need_line.date",
                                                              #sort = True,
                                                              )),
                                       sortby = "date",
                                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"need_line_id": need_line_id,
                }

# =============================================================================
class NeedsSectorModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Sectors
    """

    names = ("need_sector",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Needs <=> Sectors
        #
        tablename = "need_sector"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.org_sector_id(empty = False),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "sector_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class NeedsResponseModel(S3Model):
    """
        A Response to a Need
        - a group of Activities
    """

    names = ("need_response",
             "need_response_id",
             )

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Response
        #
        tablename = "need_response"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          self.req_need_id(),
                          self.gis_location_id(),
                          s3_date(default = "now"),
                          s3_comments("name",
                                      label = T("Summary of Needs/Activities"),
                                      comment = None,
                                      ),
                          s3_comments("contact",
                                      label = T("Contact Details"),
                                      comment = None,
                                      ),
                          s3_comments("address",
                                      label = T("Delivery Address"),
                                      comment = None,
                                      ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        # Called Activities in SHARE/LK, which is the only usecase
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Activity Group"),
        #    title_list = T("Activity Groups"),
        #    title_display = T("Activity Group"),
        #    title_update = T("Edit Activity Group"),
        #    title_upload = T("Import Activity Groups"),
        #    label_list_button = T("List Activity Groups"),
        #    label_delete_button = T("Delete Activity Group"),
        #    msg_record_created = T("Activity Group added"),
        #    msg_record_modified = T("Activity Group updated"),
        #    msg_record_deleted = T("Activity Group deleted"),
        #    msg_list_empty = T("No Activity Groups currently registered"),
        #    )

        self.configure(tablename,
                       super_entity = "doc_entity",
                       )

        # Components
        self.add_components(tablename,
                            event_event = {"link": "need_response_event",
                                            "joinby": "need_response_id",
                                            "key": "event_id",
                                            "multiple": False,
                                            },
                            org_organisation = {"link": "need_response_organisation",
                                                "joinby": "need_response_id",
                                                "key": "organisation_id",
                                                "multiple": False,
                                                },
                            req_need_response_line = "need_response_id",
                            )


        # NB Only instance of this being used (SHARE) over-rides this to show the req_number
        represent = S3Represent(lookup = tablename,
                                show_link = True,
                                )
        need_response_id = S3ReusableField("need_response_id", "reference %s" % tablename,
                                           label = T("Activity Group"),
                                           ondelete = "CASCADE",
                                           represent = represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "need_response.id",
                                                                  represent,
                                                                  orderby = "need_response.date",
                                                                  sort = True,
                                                                  )),
                                           sortby = "date",
                                           )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"need_response_id": need_response_id,
                }

# =============================================================================
class NeedsResponseEventModel(S3Model):
    """
        Link Events &/or Incidents with Need Responses (Activity Groups)
    """

    names = ("need_response_event",
             )

    def model(self):

        #T = current.T

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Events <> Impacts
        #

        tablename = "need_response_event"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.need_response_id(empty = False,
                                                ondelete = "CASCADE",
                                                ),
                          *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "incident_id",
                                                            "need_response_id",
                                                            ),
                                                 ),
                       onaccept = lambda form: \
                        self.event_set_event_from_incident(form, "need_response_event"),
                       )

        # Not accessed directly
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Activity Group"),
        #    title_display = T("Activity Group Details"),
        #    title_list = T("Activity Groups"),
        #    title_update = T("Edit Activity Group"),
        #    label_list_button = T("List Activity Groups"),
        #    label_delete_button = T("Delete Activity Group"),
        #    msg_record_created = T("Activity Group added"),
        #    msg_record_modified = T("Activity Group updated"),
        #    msg_record_deleted = T("Activity Group removed"),
        #    msg_list_empty = T("No Activity Groups currently registered in this Event"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class NeedsResponseLineModel(S3Model):
    """
        A Line within a Response to a Need
        - an Activity
        Not using the normal Activity model to avoid components of components
    """

    names = ("need_response_line",
             )

    def model(self):

        T = current.T
        #db = current.db

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        modality_opts = {1: T("Cash"),
                         2: T("In-kind"),
                         }

        if current.s3db.table("stats_demographic"):
            title = current.response.s3.crud_strings["stats_demographic"].label_create
            parameter_id_comment = S3PopupLink(c = "stats",
                                               f = "demographic",
                                               vars = {"child": "parameter_id"},
                                               title = title,
                                               )
        else:
            parameter_id_comment = None

        # ---------------------------------------------------------------------
        # Response Line
        #
        tablename = "need_response_line"
        self.define_table(tablename,
                          self.need_response_id(),
                          self.need_line_id(),
                          # A less precise location for this line
                          # Here to more easily allow multiple dropdowns within an Inline form
                          self.gis_location_id("coarse_location_id"),
                          # A more precise location for this line
                          self.gis_location_id(),
                          self.org_sector_id(),
                          Field("modality", "integer",
                                label = T("Modality"),
                                represent = S3Represent(options = modality_opts),
                                requires = IS_IN_SET(modality_opts),
                                ),
                          s3_date(label = T("Date Planned")),
                          s3_date("end_date",
                                  label = T("Date Completed"),
                                  ),
                          self.super_link("parameter_id", "stats_parameter",
                                          instance_types = ("stats_demographic",),
                                          label = T("Beneficiaries"),
                                          represent = self.stats_parameter_represent,
                                          readable = True,
                                          writable = True,
                                          #empty = False,
                                          comment = parameter_id_comment,
                                          ),
                          Field("value", "integer",
                                label = T("Number Planned"),
                                #label = T("Number in Need"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_INT_IN_RANGE(0, None),
                                ),
                          Field("value_reached", "integer",
                                label = T("Number Reached"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_INT_IN_RANGE(0, None),
                                ),
                          self.supply_item_category_id(),
                          self.supply_item_id(# Default:
                                              #ondelete = "RESTRICT",
                                              requires = IS_EMPTY_OR(self.supply_item_id().requires),
                                              # Filter Item dropdown based on Category
                                              script = '''
$.filterOptionsS3({
 'trigger':'item_category_id',
 'target':'item_id',
 'lookupPrefix':'supply',
 'lookupResource':'item',
})''',
                                              # Don't use Auto-complete
                                              widget = None,
                                              ),
                          self.supply_item_pack_id(requires = IS_EMPTY_OR(self.supply_item_pack_id().requires),
                                                   ),
                          Field("quantity", "double",
                                label = T("Quantity Planned"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
                          Field("quantity_delivered", "double",
                                label = T("Quantity Delivered"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
                          self.project_status_id(),
                          s3_comments(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class NeedsResponseOrganisationModel(S3Model):
    """
        Organisations involved in Activity Groups
    """

    names = ("need_response_organisation",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Activity Groups <=> Organisations
        #
        organisation_id = self.org_organisation_id # Load normal model
        CREATE = current.response.s3.crud_strings["org_organisation"].label_create

        project_organisation_roles = current.deployment_settings.get_project_organisation_roles()

        tablename = "need_response_organisation"
        self.define_table(tablename,
                          self.need_response_id(empty = False),
                          organisation_id(comment = S3PopupLink(c = "org",
                                                                f = "organisation",
                                                                label = CREATE,
                                                                tooltip = None,
                                                                vars = {"prefix": "req"},
                                                                ),
                                          empty = False,
                                          ),
                          Field("role", "integer",
                                default = 1, # Lead
                                label = T("Role"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(project_organisation_roles)
                                            ),
                                represent = S3Represent(options = project_organisation_roles),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_response_id",
                                                            "organisation_id",
                                                            "role",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def need_rheader(r, check_page=False):
    """
        Resource Header for Needs
        - unused
    """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    record = r.record
    if not record:
        # RHeaders only used in single-record views
        return None

    resourcename = r.name
    if resourcename == "need":
        T = current.T
        tabs = [(T("Basic Details"), None),
                (T("Demographics"), "demographic"),
                (T("Items"), "need_item"),
                (T("Skills"), "need_skill"),
                (T("Tags"), "tag"),
                ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        location_id = r.table.location_id
        rheader = DIV(TABLE(TR(TH("%s: " % location_id.label),
                               location_id.represent(record.location_id),
                               )),
                      rheader_tabs)

    else:
        # Not defined, probably using wrong rheader
        rheader = None

    return rheader

# END =========================================================================
