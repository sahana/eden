# -*- coding: utf-8 -*-

""" Sahana Eden Request Model

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

__all__ = ("RequestNeedsModel",
           "RequestNeedsContactModel",
           "RequestNeedsItemsModel",
           "RequestNeedsSkillsModel",
           "RequestNeedsOrganisationModel",
           "RequestNeedsPersonModel",
           "RequestNeedsSiteModel",
           "RequestNeedsTagModel",
           "req_rheader",
           )

from gluon import *
from gluon.sqlhtml import StringWidget
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

REQ_STATUS_NONE     = 0
REQ_STATUS_PARTIAL  = 1
REQ_STATUS_COMPLETE = 2
REQ_STATUS_CANCEL   = 3

# =============================================================================
def req_priority_opts():
    T = current.T
    return {3: T("High"),
            2: T("Medium"),
            1: T("Low")
            }

#def req_priority_represent(priority):
#    """
#        Represent request priority by a (color-coded) GIF image
#        @ToDo: make CSS-only
#    """

#    src = URL(c = "static",
#              f = "img",
#              args = ["priority", "priority_%d.gif" % (priority or 4)],
#              )
#    return DIV(IMG(_src= src))

def req_priority():
    priority_opts = req_priority_opts()
    return S3ReusableField("priority", "integer",
                           default = 2,
                           label = current.T("Priority"),
                           #@ToDo: Colour code the priority text - red, orange, green
                           #represent = req_priority_represent,
                           represent = s3_options_represent(priority_opts),
                           requires = IS_EMPTY_OR(
                                           IS_IN_SET(priority_opts)
                                           ),
                           )

# =============================================================================
def req_status_opts():
    T = current.T
    return {REQ_STATUS_NONE:     SPAN(T("None"),
                                      _class = "req_status_none",
                                      ),
            REQ_STATUS_PARTIAL:  SPAN(T("Partial"),
                                      _class = "req_status_partial",
                                      ),
            REQ_STATUS_COMPLETE: SPAN(T("Complete"),
                                      _class = "req_status_complete",
                                      ),
            }

def req_status():
    status_opts = req_status_opts()
    return S3ReusableField("req_status", "integer",
                           label = current.T("Request Status"),
                           represent = s3_options_represent(status_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(status_opts,
                                                  zero = None,
                                                  )
                                        ),
                           )

# =============================================================================
def req_timeframe():
    """
        Used only by req_need_item, and hence nothing currently
    """
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
                           represent = s3_options_represent(timeframe_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(timeframe_opts,
                                                  zero = None,
                                                  ),
                                        ),
                           )

# =============================================================================
class RequestNeedsModel(S3Model):
    """
        Simple Requests Management System
        - Starts as Simple free text Needs
        - Extensible via Key-Value Tags
        - Extensible with Items
        - Extensible with Skills
        Use cases:
        - SHARE: local governments express needs to be met by NGOs (/Private Sector/Public in future)
        - Organisations can request Money or Time from remote volunteers
        - Sites can request Time from local volunteers or accept drop-off for Goods
        - Projects can request x (tbc: MapPH usecase)

        - Used by CCC
    """

    names = ("req_need",
             "req_need_id",
             )

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Needs
        #
        tablename = "req_need"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          self.gis_location_id(), # Can be hidden, e.g. if using Sites (can then sync this onaccept)
                          s3_datetime(default = "now",
                                      widget = "date",
                                      ),
                          s3_datetime("end_date",
                                      label = T("End Date"),
                                      # Enable in Templates if-required
                                      readable = False,
                                      writable = False,
                                      ),
                          req_priority()(),
                          Field("name", notnull = True,
                                length = 64,
                                label = T("Summary of Needs"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          s3_comments("description",
                                      label = T("Description"),
                                      comment = None,
                                      ),
                          req_status()("status",
                                       label = T("Fulfilment Status"),
                                       ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Needs"),
            title_list = T("Needs"),
            title_display = T("Needs"),
            title_update = T("Edit Needs"),
            title_upload = T("Import Needs"),
            label_list_button = T("List Needs"),
            label_delete_button = T("Delete Needs"),
            msg_record_created = T("Needs added"),
            msg_record_modified = T("Needs updated"),
            msg_record_deleted = T("Needs deleted"),
            msg_list_empty = T("No Needs currently registered"),
            )

        self.configure(tablename,
                       super_entity = "doc_entity",
                       )

        # Components
        self.add_components(tablename,
                            org_organisation = {"link": "req_need_organisation",
                                                "joinby": "need_id",
                                                "key": "organisation_id",
                                                "multiple": False,
                                                },
                            req_need_organisation = {"joinby": "need_id",
                                                     "multiple": False,
                                                     },
                            org_site = {"link": "req_need_site",
                                        "joinby": "need_id",
                                        "key": "site_id",
                                        "multiple": False,
                                        },
                            req_need_contact = {"joinby": "need_id",
                                                # Can redefine as multiple=True in template if-required
                                                "multiple": False,
                                                },
                            req_need_item = "need_id",
                            req_need_person = "need_id",
                            req_need_skill = "need_id",
                            req_need_tag = {"name": "tag",
                                            "joinby": "need_id",
                                            },
                            )

        # Custom Methods
        self.set_method("req", "need",
                        method = "assign",
                        action = self.pr_AssignMethod(component = "need_person"),
                        )

        # NB Only instance of this being used (SHARE) over-rides this to show the req_number
        represent = S3Represent(lookup = tablename,
                                show_link = True,
                                )
        need_id = S3ReusableField("need_id", "reference %s" % tablename,
                                  label = T("Need"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "req_need.id",
                                                          represent,
                                                          orderby = "req_need.date",
                                                          sort = True,
                                                          )),
                                  sortby = "date",
                                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"req_need_id": need_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        return {"req_need_id": S3ReusableField.dummy("need_id"),
                }

# =============================================================================
class RequestNeedsContactModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Contacts (People)

        - Used by CCC
    """

    names = ("req_need_contact",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Needs <=> Persons
        #

        tablename = "req_need_contact"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.pr_person_id(empty = False,
                                            label = T("Contact"),
                                            ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "person_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsItemsModel(S3Model):
    """
        Simple Requests Management System
        - optional extension to support Items, but still not using Inventory-linked Requests

        - Unused currently (SHARE now uses it's own need_item)
    """

    names = ("req_need_item",
             )

    def model(self):

        T = current.T

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        # ---------------------------------------------------------------------
        # Needs <=> Supply Items
        #

        tablename = "req_need_item"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.supply_item_category_id(),
                          self.supply_item_id(empty = False,
                                              # Default:
                                              #ondelete = "RESTRICT",
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
                          self.supply_item_pack_id(),
                          req_timeframe()(),
                          Field("quantity", "double",
                                label = T("Quantity"),
                                #label = T("Quantity Requested"),
                                represent = float_represent,
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
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
                          req_priority()(),
                          s3_comments(),
                          req_status()("status",
                                       label = T("Fulfilment Status"),
                                       ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "item_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsSkillsModel(S3Model):
    """
        Simple Requests Management System
        - optional extension to support Skills, but still not using normal Requests

        - Used by CCC
    """

    names = ("req_need_skill",
             )

    def model(self):

        T = current.T
        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Needs <=> Skills
        #
        skill_id = self.hrm_skill_id # Load normal model
        CREATE_SKILL = crud_strings["hrm_skill"].label_create

        tablename = "req_need_skill"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          skill_id(comment = S3PopupLink(c = "hrm",
                                                         f = "skill",
                                                         label = CREATE_SKILL,
                                                         tooltip = None,
                                                         vars = {"prefix": "req"},
                                                         ),
                                   empty = False,
                                   ),
                          Field("quantity", "double",
                                label = T("Quantity"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                requires = IS_EMPTY_OR(
                                            IS_FLOAT_AMOUNT(minimum = 1.0)
                                            ),
                                ),
                          req_priority()(),
                          s3_comments(),
                          req_status()("status",
                                       label = T("Fulfilment Status"),
                                       ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "skill_id",
                                                            ),
                                                 ),
                       )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Skill"),
            title_list = T("Skills"),
            title_display = T("Skill"),
            title_update = T("Edit Skill"),
            #title_upload = T("Import Skills"),
            label_list_button = T("List Skills"),
            label_delete_button = T("Delete Skill"),
            msg_record_created = T("Skill added"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill deleted"),
            msg_list_empty = T("No Skills currently registered for this Request"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsOrganisationModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Organisations
        - link exposed in Templates as-required

        - Used by CCC
    """

    names = ("req_need_organisation",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Needs <=> Organisations
        #
        organisation_id = self.org_organisation_id # Load normal model
        CREATE = current.response.s3.crud_strings["org_organisation"].label_create

        tablename = "req_need_organisation"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          organisation_id(comment = S3PopupLink(c = "org",
                                                                f = "organisation",
                                                                label = CREATE,
                                                                tooltip = None,
                                                                vars = {"prefix": "req"},
                                                                ),
                                          empty = False,
                                          ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsPersonModel(S3Model):
    """
        Simple Requests Management System
        - optional link to People (used for assignments to Skills)
        - currently assumes that Need just has a single Skill, so no need to say which skill the person is for

        - used by CCC
    """

    names = ("req_need_person",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Needs <=> Persons
        #
        # @ToDo: configuration setting once-required
        status_opts = {1: T("Applied"),
                       2: T("Approved"),
                       3: T("Rejected"),
                       4: T("Invited"),
                       5: T("Accepted"),
                       6: T("Declined"),
                       }

        tablename = "req_need_person"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          self.pr_person_id(empty = False),
                          Field("status", "integer",
                                default = 4, # Invited
                                label = T("Status"),
                                represent = s3_options_represent(status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(status_opts)
                                            ),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "person_id",
                                                            ),
                                                 ),
                       )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Person"),
            title_display = T("Person Details"),
            title_list = T("People"),
            title_update = T("Edit Person"),
            #title_upload = T("Import People"),
            label_list_button = T("List People"),
            label_delete_button = T("Remove Person"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person updated"),
            msg_record_deleted = T("Person removed"),
            msg_list_empty = T("No People currently linked to this Need")
        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsSiteModel(S3Model):
    """
        Simple Requests Management System
        - optional link to Sites
        - link exposed in Templates as-required

        - currently unused
    """

    names = ("req_need_site",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Needs <=> Sites
        #
        SITE = current.deployment_settings.get_org_site_label()

        tablename = "req_need_site"
        self.define_table(tablename,
                          self.req_need_id(empty = False),
                          # Component not instance
                          self.super_link("site_id", "org_site",
                                          label = SITE,
                                          readable = True,
                                          writable = True,
                                          represent = self.org_site_represent,
                                          ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "site_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class RequestNeedsTagModel(S3Model):
    """
        Needs Tags

        - used by CCC
    """

    names = ("req_need_tag",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Need Tags
        # - Key-Value extensions
        # - can be used to add structured extensions, such as:
        #   * Reference
        #   * Cash Donations accepted (/ Details)
        #   * Goods drop-off point (/ Details)
        #   * Transport required (/ Details)
        #   * Security needed (/ Details)
        #   * Volunteering Opportunities (/ Details)
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "req_need_tag"
        self.define_table(tablename,
                          self.req_need_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("need_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def req_rheader(r):
    """
        Resource Header for Needs
    """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    record = r.record
    if not record:
        # RHeaders only used in single-record views
        return None

    if r.name == "need":
        T = current.T
        tabs = [(T("Basic Details"), None),
                # Only available in SHARE:
                #(T("Demographics"), "demographic"),
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
        rheader = None

    return rheader

# END =========================================================================
