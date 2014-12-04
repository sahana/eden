# -*- coding: utf-8 -*-

""" Sahana Eden Request Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3RequestModel",
           "S3RequestItemModel",
           "S3RequestSkillModel",
           "S3RequestRecurringModel",
           "S3RequestSummaryModel",
           "S3RequestTaskModel",
           "S3CommitModel",
           "S3CommitItemModel",
           "S3CommitPersonModel",
           "S3CommitSkillModel",
           "req_item_onaccept",
           "req_update_status",
           "req_rheader",
           "req_match",
           "req_add_from_template",
           "req_customise_req_fields",
           "req_req_list_layout",
           "req_customise_commit_fields",
           "req_commit_list_layout",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

REQ_STATUS_NONE     = 0
REQ_STATUS_PARTIAL  = 1
REQ_STATUS_COMPLETE = 2
REQ_STATUS_CANCEL = 3

# =============================================================================
class S3RequestModel(S3Model):
    """
    """

    names = ("req_req",
             "req_req_id",
             "req_req_ref",
             "req_hide_quantities",
             "req_inline_form",
             "req_create_form_mods",
             "req_prep",
             "req_tabs",
             "req_priority_opts",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        session = current.session
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        s3_string_represent = lambda str: str if str else NONE

        add_components = self.add_components
        crud_strings = s3.crud_strings
        set_method = self.set_method
        super_link = self.super_link

        # Multiple Item/Skill Types per Request?
        multiple_req_items = settings.get_req_multiple_req_items()

        req_status_writable = settings.get_req_status_writable()

        req_status_opts = {REQ_STATUS_NONE:     SPAN(T("None"),
                                                     _class = "req_status_none"),
                           REQ_STATUS_PARTIAL:  SPAN(T("Partial"),
                                                     _class = "req_status_partial"),
                           REQ_STATUS_COMPLETE: SPAN(T("Complete"),
                                                     _class = "req_status_complete"),
                           }

        req_status = S3ReusableField("req_status", "integer",
                                     label = T("Request Status"),
                                     requires = IS_EMPTY_OR(
                                                    IS_IN_SET(req_status_opts,
                                                              zero = None)),
                                     represent = lambda opt: \
                                        req_status_opts.get(opt, UNKNOWN_OPT),
                                     default = REQ_STATUS_NONE,
                                     writable = req_status_writable,
                                     )

        req_ref = S3ReusableField("req_ref", "string",
                                  label = T("%(REQ)s Number") % #
                                    dict(REQ=settings.get_req_shortname()),
                                  represent = self.req_ref_represent,
                                  writable = False,
                                  )

        req_priority_opts = {3: T("High"),
                             2: T("Medium"),
                             1: T("Low")
                             }

        req_types_deployed = settings.get_req_req_type()
        req_type_opts = {}
        if settings.has_module("inv") and "Stock" in req_types_deployed:
            # Number hardcoded in controller & JS
            req_type_opts[1] = settings.get_req_type_inv_label()
        #if settings.has_module("asset") and "Asset" in req_types_deployed:
        #    req_type_opts[2] = T("Assets")
        if settings.has_module("hrm") and "People" in req_types_deployed:
            req_type_opts[3] = settings.get_req_type_hrm_label()
        #if settings.has_module("cr") and "Shelter" in req_types_deployed:
        #    req_type_opts[4] = T("Shelter")
        if "Other" in req_types_deployed:
            req_type_opts[9] = T("Other")

        use_commit = settings.get_req_use_commit()
        req_ask_security = settings.get_req_ask_security()
        req_ask_transport = settings.get_req_ask_transport()
        date_writable = settings.get_req_date_writable()
        requester_label = settings.get_req_requester_label()
        requester_is_author = settings.get_req_requester_is_author()
        if requester_is_author:
            site_default = auth.user.site_id if auth.is_logged_in() else None
            requester_default = auth.s3_logged_in_person()
        else:
            site_default = None
            requester_default = None

        # Dropdown or Autocomplete?
        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = S3AddResourceLink(c="org", f="facility",
                                             vars = dict(child="site_id"),
                                             title=T("Create Facility"),
                                             tooltip=AUTOCOMPLETE_HELP)
        else:
            site_widget = None
            site_comment = S3AddResourceLink(c="org", f="facility",
                                             vars = dict(child="site_id"),
                                             title=T("Create Facility"))

        # ---------------------------------------------------------------------
        # Requests
        tablename = "req_req"
        self.define_table(tablename,
                          super_link("doc_id", "doc_entity"),
                          # @ToDo: Replace with Link Table
                          self.event_event_id(
                               default = session.s3.event,
                               ondelete = "SET NULL",
                               readable = False,
                               writable = False,
                               ),
                          Field("type", "integer",
                                label = T("Request Type"),
                                represent = lambda opt: \
                                            req_type_opts.get(opt, UNKNOWN_OPT),
                                requires = IS_IN_SET(req_type_opts, zero=None),
                                ),
                          req_ref(),
                          s3_datetime(label = T("Date Requested"),
                                      default = "now",
                                      past = 8760, # Hours, so 1 year
                                      future = 0,
                                      readable = date_writable,
                                      writable = date_writable,
                                      #represent = "date",
                                      #widget = "date",
                                      ),
                          Field("priority", "integer",
                                default = 2,
                                label = T("Priority"),
                                #@ToDo: Colour code the priority text - red, orange, green
                                represent = lambda opt: \
                                    req_priority_opts.get(opt, UNKNOWN_OPT),
                                #represent = self.req_priority_represent,
                                requires = IS_EMPTY_OR(
                                                IS_IN_SET(req_priority_opts))
                                ),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("site_id", "org_site",
                                     comment = site_comment,
                                     default = site_default,
                                     empty = False,
                                     filterby = "obsolete",
                                     filter_opts = (False,),
                                     instance_types = auth.org_site_types,
                                     label = T("Requested For Facility"),
                                     readable = True,
                                     represent = self.org_site_represent,
                                     updateable = True,
                                     widget = site_widget,
                                     writable = True,
                                     ),
                          #Field("location",
                          #      label = T("Neighborhood")),
                          # Donations: What will the Items be used for?; People: Task Details
                          s3_comments("purpose",
                                      comment = "",
                                      label = T("Purpose"),
                                      # Only-needed for summary mode (unused)
                                      #represent = self.req_purpose_represent,
                                      represent = s3_string_represent,
                                      ),
                          Field("is_template", "boolean",
                                default = False,
                                label = T("Recurring Request?"),
                                represent = s3_yes_no_represent,
                                comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Recurring Request?"),
                                                                  T("If this is a request template to be added repeatedly then the schedule can be set on the next page."))),
                                ),
                          s3_datetime("date_required",
                                      label = T("Date Needed By"),
                                      past = 1, # Allow time for people to fill out form
                                      future = 8760, # Hours, so 1 year
                                      #represent = "date",
                                      #widget = "date",
                                      ),
                          s3_datetime("date_required_until",
                                      label = T("Date Required Until"),
                                      past = 0,
                                      future = 8760, # Hours, so 1 year
                                      readable = False,
                                      writable = False
                                      ),
                          person_id("requester_id",
                                    default = requester_default,
                                    empty = settings.get_req_requester_optional(),
                                    label = requester_label,
                                    #writable = False,
                                    comment = S3AddResourceLink(c="pr", f="person",
                                                                vars = dict(child="requester_id",
                                                                            parent="req"),
                                                                title=crud_strings["pr_person"].label_create,
                                                                tooltip=AUTOCOMPLETE_HELP),
                                    ),
                          person_id("assigned_to_id", # This field should be in req_commit, but that complicates the UI
                                    label = T("Assigned To"),
                                    readable = False,
                                    writable = False,
                                    ),
                          person_id("approved_by_id",
                                    label = T("Approved By"),
                                    readable = False,
                                    writable = False,
                                    ),
                          person_id("request_for_id",
                                    #default = auth.s3_logged_in_person(),
                                    label = T("Requested For"),
                                    readable = False,
                                    writable = False,
                                    ),
                          Field("transport_req", "boolean",
                                label = T("Transportation Required"),
                                represent = s3_yes_no_represent,
                                readable = req_ask_transport,
                                writable = req_ask_transport,
                                ),
                          Field("security_req", "boolean",
                                label = T("Security Required"),
                                represent = s3_yes_no_represent,
                                readable = req_ask_security,
                                writable = req_ask_security,
                                ),
                          s3_datetime("date_recv",
                                      label = T("Date Received"), # Could be T("Date Delivered") - make deployment_setting
                                      past = 8760, # Hours, so 1 year
                                      future = 0,
                                      readable = False,
                                      writable = False,
                                      ),
                          person_id("recv_by_id",
                                    # @ToDo: Set this in Update forms? Dedicated 'Receive' button?
                                    # (Definitely not in Create forms)
                                    #default = auth.s3_logged_in_person(),
                                    label = T("Received By"),
                                    ),
                          # Simple Status
                          # - currently just enabled in customise_req_fields() workflow
                          req_status(readable = False,
                                     writable = False,
                                     ),
                          # Detailed Status
                          req_status("commit_status",
                                     label = T("Commit. Status"),
                                     represent = self.req_commit_status_represent,
                                     readable = use_commit,
                                     writable = req_status_writable and use_commit,
                                     ),
                          req_status("transit_status",
                                     label = T("Transit Status"),
                                     ),
                          req_status("fulfil_status",
                                     label = T("Fulfil. Status"),
                                     ),
                          Field("closed", "boolean",
                                default = False,
                                label = T("Closed"),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Closed"),
                                                                T("No more items may be added to this request"))),
                                ),
                          Field("cancel", "boolean",
                                default = False,
                                label = T("Cancel"),
                                ),
                          Field.Method("details", req_req_details),
                          Field.Method("drivers", req_req_drivers),
                          s3_comments(comment = ""),
                          *s3_meta_fields())

        # @todo: make lazy_table
        table = db[tablename]
        if len(req_type_opts) == 1:
            k, v = req_type_opts.items()[0]
            field = table.type
            field.default = k
            field.writable = False
            field.readable = False

        if not settings.get_req_use_req_number():
            table.req_ref.readable = False
            table.req_ref.writable = False

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Make Request"),
            title_display = T("Request Details"),
            title_list = T("Requests"),
            title_map=T("Map of Requests"),
            title_report = T("Requests Report"),
            title_update = T("Edit Request"),
            label_list_button = T("List Requests"),
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Request Added"),
            msg_record_modified = T("Request Updated"),
            msg_record_deleted = T("Request Canceled"),
            msg_list_empty = T("No Requests"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [
            #S3TextFilter(["committer_id$first_name",
            #              "committer_id$middle_name",
            #              "committer_id$last_name",
            #              "site_id$name",
            #              "comments",
            #              "req_id$name",
            #              "organisation_id$name"
            #              ],
            #             label = T("Search")
            #             comment=T("Search for a commitment by Committer name, Request ID, Site or Organization."),
            #             ),
            S3OptionsFilter("transit_status",
                            label = T("Transit Status"),
                            options = req_status_opts,
                            cols = 3,
                            ),
            S3OptionsFilter("fulfil_status",
                            label = T("Fulfill Status"),
                            cols = 3,
                            ),
            S3LocationFilter("site_id$location_id",
                             levels = levels,
                             hidden = True,
                             ),
            S3OptionsFilter("site_id",
                            label = T("Requested For Facility"),
                            hidden = True,
                            ),
            S3OptionsFilter("created_by",
                            label = T("Logged By"),
                            hidden = True,
                            ),
            S3DateFilter("date",
                         label = T("Date"),
                         hide_time = True,
                         input_labels = {"ge": "From", "le": "To"},
                         comment = T("Search for requests made between these dates."),
                         hidden = True,
                         ),
            S3DateFilter("date_required",
                         label = T("Date Needed By"),
                         hide_time = True,
                         input_labels = {"ge": "From", "le": "To"},
                         comment = T("Search for requests required between these dates."),
                         hidden = True,
                         ),
            ]

        if "Stock" in req_type_opts:
            filter_widgets.insert(4, S3OptionsFilter("item_category.name",
                                                     label = T("Item Category"),
                                                     hidden = True,
                                                     ))
        if len(req_type_opts) > 1:
            filter_widgets.insert(2, S3OptionsFilter("type",
                                                     label = T("Type"),
                                                     cols = len(req_type_opts),
                                                     ))
        if use_commit:
            filter_widgets.insert(2, S3OptionsFilter("commit_status",
                                                     label = T("Commit Status"),
                                                     options = req_status_opts,
                                                     cols = 3,
                                                     ))

        report_fields = ["priority",
                         "site_id$organisation_id",
                         ]
        rappend = report_fields.append
        for level in levels:
            rappend("site_id$location_id$%s" % level)
        rappend("site_id")
        # @ToDo: id gets stripped in _select_field
        fact_fields = report_fields + [(T("Requests"), "id")]

        # Reusable Field
        represent = self.req_represent
        req_id = S3ReusableField("req_id", "reference %s" % tablename,
                                 label = T("Request"),
                                 ondelete = "CASCADE",
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db,
                                                          "req_req.id",
                                                          lambda id, row:
                                                            represent(id, row,
                                                                      show_link=False),
                                                          orderby="req_req.date",
                                                          sort=True)
                                                ),
                                 sortby = "date",
                                 )
        list_fields = ["id",
                       "date",
                       "date_required",
                       "site_id",
                       "requester_id",
                       #"event_id",
                       # @ToDo: Vary by deployment_setting (easy)
                       # @ToDo: Allow a single column to support different components based on type
                       # @ToDo: Include Qty too (Computed VF in component?)
                       #(T("Items"), "item.item_id"),
                       #(T("Skills"), "skill.skill_id"),
                       ]

        if settings.get_req_use_req_number():
            list_fields.insert(1, "req_ref")
        #if len(settings.get_req_req_type()) > 1:
        #    list_fields.append("type")
        list_fields.extend(((T("Drivers"), "drivers"),
                            "priority",
                            # @ToDo: Deprecate with type-based components (see above)
                            (T("Details"), "details")
                            ))
        if use_commit:
            list_fields.append("commit_status")
        list_fields.extend(("transit_status",
                            "fulfil_status",
                            ))
        if use_commit:
            list_fields.append((T("Committed By"), "commit.site_id"))

        self.configure(tablename,
                       context = {"event": "event_id",
                                  "location": "site_id$location_id",
                                  "organisation": "site_id$organisation_id",
                                  "site": "site_id",
                                  },
                       deduplicate = self.req_req_duplicate,
                       extra_fields = ["req_ref", "type"],
                       filter_widgets = filter_widgets,
                       onaccept = self.req_onaccept,
                       ondelete = self.req_req_ondelete,
                       listadd = False,
                       list_fields = list_fields,
                       orderby = "req_req.date desc",
                       report_options = Storage(
                            rows = report_fields,
                            cols = report_fields,
                            fact = fact_fields,
                            methods = ["count", "list", "sum"],
                            defaults = Storage(
                                rows = "site_id$location_id$%s" % levels[0], # Highest-level of hierarchy
                                cols = "priority",
                                fact = "count(id)",
                                totals = True,
                                )
                            ),
                       )

        # Custom Methods
        set_method("req", "req",
                   method="check",
                   action=self.req_check)

        set_method("req", "req",
                   method="commit_all",
                   action=self.req_commit_all)

        set_method("req", "req",
                   method="copy_all",
                   action=self.req_copy_all)

        # Print Forms
        set_method("req", "req",
                   method="form",
                   action=self.req_form)

        # Components
        add_components(tablename,
                       # Documents
                       req_document = "req_id",
                       # Requested Items
                       req_req_item = {"joinby": "req_id",
                                       "multiple": multiple_req_items,
                                       },
                       # Requested Skills
                       req_req_skill = {"joinby": "req_id",
                                        "multiple": multiple_req_items,
                                        },
                       # Commitment
                       req_commit = "req_id",
                       # Item Categories
                       supply_item_category = {"link": "req_req_item_category",
                                               "joinby": "req_id",
                                               "key": "item_category_id",
                                               },

                       **{# Scheduler Jobs (for recurring requests)
                          S3Task.TASK_TABLENAME: {"name": "job",
                                                  "joinby": "req_id",
                                                  "link": "req_job",
                                                  "key": "scheduler_task_id",
                                                  "actuate": "replace",
                                                  },
                         }
                      )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(req_create_form_mods = self.req_create_form_mods,
                    req_hide_quantities = self.req_hide_quantities,
                    req_inline_form = self.req_inline_form,
                    req_prep = self.req_prep,
                    req_priority_opts = req_priority_opts,
                    req_priority_represent = self.req_priority_represent,
                    req_req_id = req_id,
                    req_req_ref = req_ref,
                    req_status_opts = req_status_opts,
                    req_type_opts = req_type_opts,
                    req_tabs = self.req_tabs,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy", "string",
                                readable = False,
                                writable = False)

        return dict(req_req_ref = lambda **attr: dummy("req_ref"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_create_form_mods():
        """
            Function to be called from REST prep functions
             - main module & components (sites & events)
        """

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        # Hide fields which don't make sense in a Create form
        table = db.req_req
        table.req_ref.readable = False
        table.commit_status.readable = table.commit_status.writable = False
        table.transit_status.readable = table.transit_status.writable = False
        table.fulfil_status.readable = table.fulfil_status.writable = False
        table.cancel.readable = table.cancel.writable = False
        table.date_recv.readable = table.date_recv.writable = False
        table.recv_by_id.readable = table.recv_by_id.writable = False

        if settings.get_req_requester_from_site():
            # Filter the list of Contacts to those for the site
            table.requester_id.widget = None
            table.requester_id.comment = S3AddResourceLink(c="pr", f="person",
                                                           vars = dict(child="requester_id",
                                                                       parent="req"),
                                                           title=s3.crud_strings["pr_person"].label_create)
            s3.jquery_ready.append('''
$.filterOptionsS3({
 'trigger':'site_id',
 'target':'requester_id',
 'lookupResource':'staff',
 'lookupURL':S3.Ap.concat('/hrm/staff_for_site/'),
 'msgNoRecords':'%s',
 'optional':true,
})''' % T("No contacts yet defined for this site"))
            #table.site_id.comment = A(T("Set as default Site"),
            #                          _id="req_req_site_id_link",
            #                          _target="_blank",
            #                          _href=URL(c="default",
            #                                    f="user",
            #                                    args=["profile"]))

        req_types = settings.get_req_req_type()
        if "People" in req_types:
            # Show the Required Until Field
            # (gets turned-off by JS for other types)
            table.date_required_until.writable = True

        if "type" not in current.request.vars:
            # Script to inject into Pages which include Request create forms
            req_helptext = '''
i18n.req_purpose="%s"
i18n.req_site_id="%s"
i18n.req_request_for_id="%s"
i18n.req_recv_by_id="%s"
i18n.req_items_purpose="%s"
i18n.req_items_site_id="%s"
i18n.req_items_recv_by_id="%s"
i18n.req_people_purpose="%s"
i18n.req_people_site_id="%s"
i18n.req_people_recv_by_id="%s"
i18n.req_next_msg="%s"
i18n.req_other_msg="%s"
i18n.req_details_mandatory="%s"''' % (table.purpose.label,
                                      table.site_id.label,
                                      table.request_for_id.label,
                                      table.recv_by_id.label,
                                      T("What the Items will be used for"),
                                      T("Deliver To"),
                                      T("Delivered To"),
                                      T("Task Details"),
                                      T("Report To"),
                                      T("Reported To"),
                                      T("Please enter the details on the next screen."),
                                      T("Please enter request details here."),
                                      T("Details field is required!"))
            s3.js_global.append(req_helptext)
            s3.scripts.append("/%s/static/scripts/S3/s3.req_create_variable.js" % current.request.application)

        else:
            s3.scripts.append("/%s/static/scripts/S3/s3.req_create.js" % current.request.application)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def req_inline_form(type, method):
        """
            Function to be called from REST prep functions
             - to add req_item & req_skill components as inline forms
        """

        T = current.T
        s3db = current.s3db
        table = s3db.req_req
        s3 = current.response.s3
        postprocess = s3.req_req_postprocess

        if type == 1:
            # Dropdown not Autocomplete
            itable = s3db.req_req_item
            itable.item_id.widget = None
            jquery_ready = s3.jquery_ready
            jquery_ready.append('''
$.filterOptionsS3({
 'trigger':{'alias':'req_item','name':'item_id'},
 'target':{'alias':'req_item','name':'item_pack_id'},
 'scope':'row',
 'lookupPrefix':'supply',
 'lookupResource':'item_pack',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')
            # Custom Form
            settings = current.deployment_settings
            fields = ["site_id",
                      "requester_id",
                      "date",
                      "priority",
                      "date_required",
                      S3SQLInlineComponent(
                        "req_item",
                        label = T("Items"),
                        fields = ["item_id",
                                  "item_pack_id",
                                  "quantity",
                                  "comments"
                                  ]
                      ),
                      "comments",
                      ]
            if method == "update":
                if settings.get_req_status_writable():
                    fields.insert(7, "fulfil_status")
                    if settings.get_req_show_quantity_transit():
                        fields.insert(7, "transit_status")
                    if settings.get_req_use_commit():
                        fields.insert(7, "commit_status")
                fields.insert(7, "date_recv")

                if settings.get_req_requester_from_site():
                    # Filter the list of Contacts to those for the site
                    table.requester_id.widget = None
                    table.requester_id.comment = S3AddResourceLink(c="pr", f="person",
                                                                    vars = dict(child="requester_id",
                                                                                parent="req"),
                                                                    title=s3.crud_strings["pr_person"].label_create)
                    jquery_ready.append('''
$.filterOptionsS3({
 'trigger':'site_id',
 'target':'requester_id',
 'lookupResource':'staff',
 'lookupURL':S3.Ap.concat('/hrm/staff_for_site/'),
 'msgNoRecords':'%s',
 'optional':true,
})''' % T("No contacts yet defined for this site"))
                    table.site_id.comment = A(T("Set as default Site"),
                                              _id="req_req_site_id_link",
                                              _target="_blank",
                                              _href=URL(c="default",
                                                        f="user",
                                                        args=["profile"]))

            if settings.get_req_items_ask_purpose():
                fields.insert(6, "purpose")
            if method != "update":
                fields.insert(1, "is_template")
            if settings.get_req_use_req_number() and \
               not settings.get_req_generate_req_number():
                fields.insert(0, "req_ref")
            if postprocess:
                crud_form = S3SQLCustomForm(*fields, postprocess=postprocess)
            else:
                crud_form = S3SQLCustomForm(*fields)
            s3db.configure("req_req", crud_form=crud_form)

        elif type == 3:
            # Custom Form
            stable = s3db.req_req_skill
            stable.skill_id.label = T("Required Skills (optional)")
            # Custom Form
            settings = current.deployment_settings
            fields = ["site_id",
                      "requester_id",
                      "date",
                      "priority",
                      "date_required",
                      "date_required_until",
                      "purpose",
                      S3SQLInlineComponent(
                        "req_skill",
                        label = T("Skills"),
                        fields = ["quantity",
                                  "skill_id",
                                  "comments"
                                  ]
                      ),
                      "comments",
                      ]
            if method == "update":
                if settings.get_req_status_writable():
                    fields.insert(8, "fulfil_status")
                    if settings.get_req_show_quantity_transit():
                        fields.insert(8, "transit_status")
                    if settings.get_req_use_commit():
                        fields.insert(8, "commit_status")
                fields.insert(8, "date_recv")

                if settings.get_req_requester_from_site():
                    # Filter the list of Contacts to those for the site
                    table.requester_id.widget = None
                    table.requester_id.comment = S3AddResourceLink(c="pr", f="person",
                                                                   vars = dict(child="requester_id",
                                                                               parent="req"),
                                                                   title=s3.crud_strings["pr_person"].label_create)
                    s3.jquery_ready.append('''
$.filterOptionsS3({
 'trigger':'site_id',
 'target':'requester_id',
 'lookupResource':'staff',
 'lookupURL':S3.Ap.concat('/hrm/staff_for_site/'),
 'msgNoRecords':'%s',
 'optional':true,
})''' % T("No contacts yet defined for this site"))
                    table.site_id.comment = A(T("Set as default Site"),
                                      _id="req_req_site_id_link",
                                      _target="_blank",
                                      _href=URL(c="default",
                                                f="user",
                                                args=["profile"]))

            else:
                fields.insert(1, "is_template")
            if settings.get_req_use_req_number() and \
               not settings.get_req_generate_req_number():
                fields.insert(0, "req_ref")
            if postprocess:
                crud_form = S3SQLCustomForm(*fields, postprocess=postprocess)
            else:
                crud_form = S3SQLCustomForm(*fields)
            s3db.configure("req_req", crud_form=crud_form)

    # -------------------------------------------------------------------------
    @staticmethod
    def req_prep(r):
        """
            Function to be called from REST prep functions
             - main module & components (sites)
        """

        if not r.component or r.component.name =="req":
            default_type = current.db.req_req.type.default
            if default_type:
                T = current.T
                req_submit_button = {1:T("Save and add Items"),
                                     3:T("Save and add People")}
                current.response.s3.crud.submit_button = req_submit_button[default_type]

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def req_represent(id, row=None, show_link=True):
        """
            Represent a Request
        """

        if row:
            table = current.db.req_req
        elif not id:
            return current.messages["NONE"]
        else:
            id = int(id)
            if id:
                db = current.db
                table = db.req_req
                row = db(table.id == id).select(table.date,
                                                table.req_ref,
                                                table.site_id,
                                                limitby=(0, 1)).first()
        try:
            if row.req_ref:
                req = row.req_ref
            else:
                req = "%s - %s" % (table.site_id.represent(row.site_id,
                                                           show_link=False),
                                   table.date.represent(row.date))
        except:
            return current.messages.UNKNOWN_OPT

        if show_link:
            return A(req,
                     _href = URL(c = "req",
                                 f = "req",
                                 args = [id]),
                     _title = current.T("Go to Request"))
        else:
            return req

    # -------------------------------------------------------------------------
    @staticmethod
    def req_commit_status_represent(opt):
        """
            Represet the Commitment Status of the Request
        """

        if opt == REQ_STATUS_COMPLETE:
            # Include the Site Name of the Committer if we can
            # @ToDo: figure out how!
            return SPAN(current.T("Complete"),
                        _class = "req_status_complete")
        else:
            return current.s3db.req_status_opts.get(opt,
                                                    current.messages.UNKNOWN_OPT)

    # -------------------------------------------------------------------------
    @staticmethod
    def req_ref_represent(value, show_link=True, pdf=False):
        """
            Represent for the Request Reference
            if show_link is True then it will generate a link to the record
            if pdf is True then it will generate a link to the PDF
        """

        if value:
            if show_link:
                db = current.db
                table = db.req_req
                req_row = db(table.req_ref == value).select(table.id,
                                                            limitby=(0, 1)
                                                            ).first()
                if req_row:
                    if pdf:
                        args = [req_row.id, "form"]
                    else:
                        args = [req_row.id]
                    return A(value,
                             _href = URL(c = "req", f = "req",
                                         args = args
                                         ),
                             )
            return B(value)

        return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def req_form(r, **attr):
        """
            Generate a PDF of a Request Form
        """

        db = current.db
        table = db.req_req
        record = db(table.id == r.id).select(limitby=(0, 1)).first()

        if record.type == 1:
            pdf_componentname = "req_item"
            list_fields = ["item_id",
                           "item_pack_id",
                           "quantity",
                           "quantity_commit",
                           "quantity_transit",
                           "quantity_fulfil",
                           ]
        elif record.type == 3:
            pdf_componentname = "req_skill"
            list_fields = ["skill_id",
                           "quantity",
                           "quantity_commit",
                           "quantity_transit",
                           "quantity_fulfil",
                           ]
        else:
            # Not Supported - redirect to normal PDF
            redirect(URL(args=current.request.args[0], extension="pdf"))

        if current.deployment_settings.get_req_use_req_number():
            filename = record.req_ref
        else:
            filename = None

        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r.resource,
                        request=r,
                        method = "list",
                        pdf_title = current.deployment_settings.get_req_form_name(),
                        pdf_filename = filename,
                        list_fields = list_fields,
                        pdf_hide_comments = True,
                        pdf_componentname = pdf_componentname,
                        pdf_header_padding = 12,
                        #pdf_footer = inv_recv_pdf_footer,
                        pdf_table_autogrow = "B",
                        pdf_paper_alignment = "Landscape",
                        **attr
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_copy_all(r, **attr):
        """
            Custom Method to copy an existing Request
            - creates a req with req_item records
        """

        db = current.db
        s3db = current.s3db
        table = s3db.req_req
        settings = current.deployment_settings
        now = current.request.now

        record = r.record
        req_id = record.id
        # Make a copy of the request record
        if settings.get_req_use_req_number():
            code = s3db.supply_get_shipping_code(settings.get_req_shortname(),
                                              record.site_id,
                                              table.req_ref,
                                              )
        else:
            code = None
        if record.date_required and record.date_required < now:
            date_required = now + datetime.timedelta(days=14)
        else:
            date_required = record.date_required
        new_req_id = table.insert(type = record.type,
                                  req_ref = code,
                                  date = now,
                                  date_required = date_required,
                                  priority = record.priority,
                                  site_id = record.site_id,
                                  purpose = record.purpose,
                                  requester_id = record.requester_id,
                                  transport_req = record.transport_req,
                                  security_req = record.security_req,
                                  comments = record.comments
                                 )
        # Make a copy of each child record
        if record.type == 1:
            # Items
            ritable = s3db.req_req_item
            items = db(ritable.req_id == req_id).select(ritable.id,
                                                        ritable.item_entity_id,
                                                        ritable.item_id,
                                                        ritable.item_pack_id,
                                                        ritable.quantity,
                                                        ritable.pack_value,
                                                        ritable.currency,
                                                        ritable.site_id,
                                                        ritable.comments)
            if items:
                insert = ritable.insert
                for item in items:
                    insert(req_id=new_req_id,
                           item_entity_id = item.item_entity_id,
                           item_id = item.item_id,
                           item_pack_id = item.item_pack_id,
                           quantity = item.quantity,
                           pack_value = item.pack_value,
                           currency = item.currency,
                           site_id = item.site_id,
                           comments = item.comments)
        elif record.type == 3:
            # People and skills
            rstable = s3db.req_req_skill
            skills = db(rstable.req_id == req_id).select(rstable.id,
                                                         rstable.skill_id,
                                                         rstable.quantity,
                                                         rstable.site_id,
                                                         rstable.comments)
            if skills:
                insert = rstable.insert
                for skill in skills:
                    insert(req_id = new_req_id,
                           skill_id = skill.skill_id,
                           quantity = skill.quantity,
                           site_id = skill.site_id,
                           comments = skill.comments)

        redirect(URL(f="req", args=[new_req_id, "update"]))


    # -------------------------------------------------------------------------
    @staticmethod
    def req_commit_all(r, **attr):
        """
            Custom Method to commit to a Request
            - creates a commit with commit_items for each req_item
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        table = s3db.req_commit

        record = r.record
        req_id = record.id

        # Check if there is an existing Commitment
        query = (table.req_id == req_id) & \
                (table.deleted == False)
        exists = db(query).select(table.id,
                                  limitby=(0, 1))
        if exists:
            # Browse existing commitments
            redirect(URL(f="req", args=[r.id, "commit"]))

        type = record.type

        # Create the commitment
        cid = table.insert(req_id=req_id,
                           type=type)

        if type == 1:
            # Items
            ritable = s3db.req_req_item
            items = db(ritable.req_id == req_id).select(ritable.id,
                                                        ritable.item_pack_id,
                                                        ritable.quantity,
                                                        ritable.comments)
            if items:
                citable = s3db.req_commit_item
                insert = citable.insert
                for item in items:
                    id = item.id
                    quantity = item.quantity
                    insert(commit_id=cid,
                           req_item_id=id,
                           item_pack_id=item.item_pack_id,
                           quantity=quantity,
                           comments=item.comments)
                    # Mark Item in the Request as Committed
                    db(ritable.id == item.id).update(quantity_commit=quantity)
            # Mark Request as Committed
            db(s3db.req_req.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            msg = T("You have committed to all items in this Request. Please check that all details are correct and update as-required.")

        elif type == 3:
            # People
            rstable = s3db.req_req_skill
            skills = db(rstable.req_id == req_id).select(rstable.id,
                                                         rstable.skill_id,
                                                         rstable.quantity,
                                                         rstable.comments)
            if skills:
                cstable = s3db.req_commit_skill
                insert = cstable.insert
                for skill in skills:
                    id = skill.id
                    quantity = skill.quantity
                    insert(commit_id=cid,
                           skill_id=skill.skill_id,
                           quantity=quantity,
                           comments=skill.comments)
                    # Mark Item in the Request as Committed
                    db(rstable.id == skill.id).update(quantity_commit=quantity)
            # Mark Request as Committed
            db(s3db.req_req.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            msg = T("You have committed for all people in this Request. Please check that all details are correct and update as-required.")

        else:
            # Other
            # Mark Request as Committed
            db(s3db.req_req.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            msg = T("You have committed to this Request. Please check that all details are correct and update as-required.")

        if "send" in r.args:
            redirect(URL(f="send_commit", args=[cid]))

        current.session.confirmation = msg
        redirect(URL(c="req", f="commit", args=[cid]))

    # -------------------------------------------------------------------------
    @staticmethod
    def req_priority_represent(id):
        """
        """

        src = URL(c="static", f="img",
                  args=["priority", "priority_%d.gif" % (id or 4)]
                )
        return DIV(IMG(_src= src))

    # -------------------------------------------------------------------------
    @staticmethod
    def req_hide_quantities(table):
        """
            Hide the Update Quantity Status Fields from Request create forms
        """

        if not current.deployment_settings.get_req_item_quantities_writable():
            table.quantity_commit.writable = table.quantity_commit.readable = False
            table.quantity_transit.writable = table.quantity_transit.readable= False
            table.quantity_fulfil.writable = table.quantity_fulfil.readable = False

    # -------------------------------------------------------------------------
    @staticmethod
    def req_tabs(r, match=True):
        """
            Add a set of Tabs for a Site's Request Tasks

            @ToDo: Roll these up like inv_tabs in inv.py
        """

        settings = current.deployment_settings
        if settings.get_org_site_inv_req_tabs():
            permit = current.auth.s3_has_permission
            if settings.has_module("req") and \
               permit("read", "req_req", c="req"):
                T = current.T
                tabs = [(T("Requests"), "req")]
                if match and permit("read", "req_req",
                                    c=current.request.controller,
                                    f="req_match"):
                    tabs.append((T("Match Requests"), "req_match/"))
                if settings.get_req_use_commit():
                    tabs.append((T("Commit"), "commit"))
                return tabs
        return []

    # -------------------------------------------------------------------------
    @staticmethod
    def req_check(r, **attr):
        """
            Check to see if your Inventory can be used to match any open Requests
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        response = current.response
        s3 = response.s3

        NONE = current.messages["NONE"]

        site_id = r.vars.site_id
        site_name = s3db.org_site_represent(site_id, show_link=False)

        output = {}
        output["title"] = T("Check Request")
        output["rheader"] = req_rheader(r, check_page=True)

        stable = s3db.org_site
        ltable = s3db.gis_location
        query = (stable.id == site_id ) & \
                (stable.location_id == ltable.id)
        location_r = db(query).select(ltable.lat,
                                      ltable.lon,
                                      limitby=(0, 1)).first()
        query = (stable.id == r.record.site_id ) & \
                (stable.location_id == ltable.id)
        req_location_r = db(query).select(ltable.lat,
                                          ltable.lon,
                                          limitby=(0, 1)).first()

        try:
            distance = current.gis.greatCircleDistance(location_r.lat,
                                                       location_r.lon,
                                                       req_location_r.lat,
                                                       req_location_r.lon,)
            output["rheader"][0].append(TR(TH(T("Distance from %s:") % site_name),
                                           TD(T("%.1f km") % distance)
                                           ))
        except:
            pass

        output["subtitle"] = T("Request Items")

        use_commit = current.deployment_settings.get_req_use_commit()

        # Get req_items & inv_items from this site
        table = s3db.req_req_item
        query = (table.req_id == r.id ) & \
                (table.deleted == False )
        req_items = db(query).select(table.id,
                                     table.item_id,
                                     table.quantity,
                                     table.item_pack_id,
                                     table.quantity_commit,
                                     table.quantity_transit,
                                     table.quantity_fulfil)
        itable = s3db.inv_inv_item
        query = (itable.site_id == site_id ) & \
                (itable.deleted == False )
        inv_items_dict = {}
        inv_items = db(query).select(itable.item_id,
                                     itable.quantity,
                                     itable.item_pack_id,
                                     # VF
                                     #itable.pack_quantity,
                                     )
        for item in inv_items:
            item_id = item.item_id
            if item_id in inv_items_dict:
                inv_items_dict[item_id] += item.quantity * item.pack_quantity()
            else:
                inv_items_dict[item_id] = item.quantity * item.pack_quantity()

        if len(req_items):
            row = TR(TH(table.item_id.label),
                     TH(table.quantity.label),
                     TH(table.item_pack_id.label),
                     TH(table.quantity_transit.label),
                     TH(table.quantity_fulfil.label),
                     TH(T("Quantity in %s's Warehouse") % site_name),
                     TH(T("Match?"))
                     )
            if use_commit:
                row.insert(3, TH(table.quantity_commit.label))
            items = TABLE(THEAD(row),
                          _id = "list",
                          _class = "dataTable display")

            supply_item_represent = table.item_id.represent
            item_pack_represent = table.item_pack_id.represent
            no_match = True
            for req_item in req_items:
                # Convert inv item quantity to req item quantity
                item_id = req_item.item_id
                if item_id in inv_items_dict:
                    inv_quantity = inv_items_dict[item_id] / req_item.pack_quantity()
                else:
                    inv_quantity = NONE

                if inv_quantity != NONE:
                    no_match = False
                    if inv_quantity < req_item.quantity:
                        status = SPAN(T("Partial"), _class = "req_status_partial")
                    else:
                        status = SPAN(T("YES"), _class = "req_status_complete")
                else:
                    status = SPAN(T("NO"), _class = "req_status_none"),

                if use_commit:
                    items.append(TR(#A(req_item.id),
                                    supply_item_represent(req_item.item_id),
                                    req_item.quantity,
                                    item_pack_represent(req_item.item_pack_id),
                                    # This requires an action btn to get the req_id
                                    req_item.quantity_commit,
                                    req_item.quantity_transit,
                                    req_item.quantity_fulfil,
                                    #req_quantity_represent(req_item.quantity_commit, "commit"),
                                    #req_quantity_represent(req_item.quantity_fulfil, "fulfil"),
                                    #req_quantity_represent(req_item.quantity_transit, "transit"),
                                    inv_quantity,
                                    status,
                                    )
                                )
                else:
                    items.append(TR(#A(req_item.id),
                                    supply_item_represent(req_item.item_id),
                                    req_item.quantity,
                                    item_pack_represent(req_item.item_pack_id),
                                    # This requires an action btn to get the req_id
                                    req_item.quantity_transit,
                                    req_item.quantity_fulfil,
                                    #req_quantity_represent(req_item.quantity_fulfil, "fulfil"),
                                    #req_quantity_represent(req_item.quantity_transit, "transit"),
                                    inv_quantity,
                                    status,
                                    )
                                )
                output["items"] = items
                #s3.actions = [req_item_inv_item_btn]
                s3.no_sspag = True # pag won't work

            if no_match:
                current.response.warning = \
                    T("%(site)s has no items exactly matching this request. There may still be other items in stock which can fulfill this request!") % \
                        dict(site=site_name)
        else:
            output["items"] = s3.crud_strings.req_req_item.msg_list_empty

        response.view = "list.html"
        s3.no_formats = True

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def req_onaccept(form):
        """
            After DB I/O
        """

        db = current.db
        s3db = current.s3db
        request = current.request
        settings = current.deployment_settings
        tablename = "req_req"
        table = s3db.req_req
        form_vars = form.vars

        id = form_vars.id
        if form_vars.get("is_template", None):
            is_template = True
            f = "req_template"
        else:
            is_template = False
            f = "req"

            # If the req_ref is None then set it up
            if settings.get_req_use_req_number():
                record = db(table.id == id).select(table.req_ref,
                                                   table.site_id,
                                                   limitby=(0, 1)).first()
                if not record.req_ref:
                    code = s3db.supply_get_shipping_code(settings.get_req_shortname(),
                                                         record.site_id,
                                                         table.req_ref,
                                                         )
                    db(table.id == id).update(req_ref = code)

        req_status = form_vars.get("req_status", None)
        if req_status is not None:
            # Translate Simple Status
            req_status = int(req_status)
            if req_status == REQ_STATUS_PARTIAL:
                # read current status
                record = db(table.id == id).select(table.commit_status,
                                                   table.fulfil_status,
                                                   limitby=(0, 1)
                                                   ).first()
                data = dict(cancel = False)
                if record.commit_status != REQ_STATUS_COMPLETE:
                    data["commit_status"] = REQ_STATUS_PARTIAL
                if record.fulfil_status == REQ_STATUS_COMPLETE:
                    data["fulfil_status"] = REQ_STATUS_PARTIAL
                db(table.id == id).update(**data)
            elif req_status == REQ_STATUS_COMPLETE:
                db(table.id == id).update(fulfil_status = REQ_STATUS_COMPLETE,
                                          cancel = False,
                                          )
            elif req_status == REQ_STATUS_CANCEL:
                db(table.id == id).update(cancel = True)
            elif req_status == REQ_STATUS_NONE:
                db(table.id == id).update(commit_status = REQ_STATUS_NONE,
                                          fulfil_status = REQ_STATUS_NONE,
                                          cancel = False)

        if settings.get_req_requester_to_site():
            requester_id = form_vars.get("requester_id", None)
            if requester_id:
                site_id = form_vars.get("site_id", None)
                # If the requester has no HR record, then create one
                hrtable = s3db.hrm_human_resource
                query = (hrtable.person_id == requester_id)
                exists = db(query).select(hrtable.id,
                                          hrtable.organisation_id,
                                          hrtable.site_id,
                                          hrtable.site_contact,
                                          limitby=(0, 1)
                                          ).first()
                if exists:
                    if site_id and not exists.site_id:
                        # Check that the Request site belongs to this Org
                        stable = s3db.org_site
                        site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                                    limitby=(0, 1)
                                                                    ).first()
                        # @ToDo: Think about branches
                        if site and site.organisation_id == exists.organisation_id:
                            # Set the HR record as being for this site
                            exists.update(site_id = site_id)
                            s3db.hrm_human_resource_onaccept(exists)
                elif site_id:
                    # Lookup the Org for the site
                    stable = s3db.org_site
                    site = db(stable.site_id == site_id).select(stable.organisation_id,
                                                                limitby=(0, 1)
                                                                ).first()
                    # Is there already a site_contact for this site?
                    ltable = s3db.hrm_human_resource_site
                    query = (ltable.site_id == site_id) & \
                            (ltable.site_contact == True)
                    already = db(query).select(ltable.id,
                                               limitby=(0, 1)
                                               ).first()
                    if already:
                        site_contact = False
                    else:
                        site_contact = True
                    hr_id = hrtable.insert(person_id = requester_id,
                                           organisation_id = site.organisation_id,
                                           site_id = site_id,
                                           site_contact = site_contact,
                                           )
                    s3db.hrm_human_resource_onaccept(Storage(id=hr_id))

        # Configure the next page to go to based on the request type
        inline_forms = settings.get_req_inline_forms()
        if inline_forms and is_template:
            s3db.configure(tablename,
                           create_next = URL(c="req",
                                             f=f,
                                             args=["[id]", "job"]),
                           update_next = URL(c="req",
                                             f=f,
                                             args=["[id]", "job"]))

        elif not inline_forms:
            if table.type.default:
                type = table.type.default
            elif "type" in form_vars:
                type = int(form_vars.type)
            else:
                type = 1
            if type == 1 and settings.has_module("inv"):
                s3db.configure(tablename,
                               create_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_item"]),
                               update_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_item"]))
            elif type == 2 and settings.has_module("asset"):
                s3db.configure(tablename,
                               create_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_asset"]),
                               update_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_asset"]))
            elif type == 3 and settings.has_module("hrm"):
                s3db.configure(tablename,
                               create_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_skill"]),
                               update_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_skill"]))
            elif type == 4 and settings.has_module("cr"):
                s3db.configure(tablename,
                               create_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_shelter"]),
                               update_next = URL(c="req",
                                                 f=f,
                                                 args=["[id]", "req_shelter"]))

    # -------------------------------------------------------------------------
    @staticmethod
    def req_req_ondelete(row):
        """
            Cleanup any scheduled tasks
        """

        db = current.db
        table = db.scheduler_task
        query = (table.function_name == "req_add_from_template") & \
                (table.args == "[%s]" % row.id)
        db(query).delete()

    # -------------------------------------------------------------------------
    @staticmethod
    def req_req_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                       of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - If the Request Number exists then it's a duplicate
        """

        request_number = item.data.get("req_ref")
        if not request_number:
            return

        table = item.table
        query = (table.req_ref == request_number)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3RequestItemModel(S3Model):
    """
    """

    names = ("req_req_item",
             "req_item_id",
             "req_item_represent",
             "req_req_item_category",
             )

    def model(self):

        T = current.T
        db = current.db

        settings = current.deployment_settings
        quantities_writable = settings.get_req_item_quantities_writable()
        use_commit = settings.get_req_use_commit()
        show_qty_transit = settings.get_req_show_quantity_transit()
        track_pack_values = settings.get_inv_track_pack_values()

        define_table = self.define_table
        req_id = self.req_req_id

        # -----------------------------------------------------------------
        # Request Items
        #
        tablename = "req_req_item"
        define_table(tablename,
                     req_id(empty=False),
                     self.supply_item_entity_id,
                     self.supply_item_id(),
                     self.supply_item_pack_id(),
                     Field("quantity", "double", notnull=True,
                           requires = IS_FLOAT_IN_RANGE(minimum=1),
                           represent=lambda v: \
                           IS_FLOAT_AMOUNT.represent(v, precision=2)),
                     Field("pack_value", "double",
                           readable=track_pack_values,
                           writable=track_pack_values,
                           label = T("Estimated Value per Pack")),
                     # @ToDo: Move this into a Currency Widget for the pack_value field
                     s3_currency(readable=track_pack_values,
                                 writable=track_pack_values),
                     self.org_site_id,
                     Field("quantity_commit", "double",
                           label = T("Quantity Committed"),
                           represent = self.req_qnty_commit_represent,
                           default = 0,
                           requires = IS_FLOAT_IN_RANGE(minimum=0, maximum=999999),
                           readable = use_commit,
                           writable = use_commit and quantities_writable),
                     Field("quantity_transit", "double",
                           label = T("Quantity in Transit"),
                           represent = self.req_qnty_transit_represent,
                           default = 0,
                           requires = IS_FLOAT_IN_RANGE(minimum=0, maximum=999999),
                           readable = show_qty_transit,
                           writable = show_qty_transit and quantities_writable),
                     Field("quantity_fulfil", "double",
                           label = T("Quantity Fulfilled"),
                           represent = self.req_qnty_fulfil_represent,
                           default = 0,
                           requires = IS_FLOAT_IN_RANGE(minimum=0, maximum=999999),
                           writable = quantities_writable),
                     Field.Method("pack_quantity",
                                  self.supply_item_pack_quantity(tablename=tablename)),
                     s3_comments(),
                     *s3_meta_fields())

        # @todo: make lazy_table
        table = db[tablename]
        table.site_id.label = T("Requested From")

        # CRUD strings
        ADD_REQUEST_ITEM = T("Add Item to Request")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_REQUEST_ITEM,
            title_display = T("Request Item Details"),
            title_list = T("Items in Request"),
            title_update = T("Edit Item in Request"),
            label_list_button = T("List Items in Request"),
            label_delete_button = T("Delete Item from Request"),
            msg_record_created = T("Item(s) added to Request"),
            msg_record_modified = T("Item(s) updated on Request"),
            msg_record_deleted = T("Item(s) deleted from Request"),
            msg_list_empty = T("No Items currently requested"))

        # Reusable Field
        req_item_id = S3ReusableField("req_item_id", "reference %s" % tablename,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db,
                                                              "req_req_item.id",
                                                              self.req_item_represent,
                                                              orderby="req_req_item.id",
                                                              sort=True)),
                                      represent = self.req_item_represent,
                                      label = T("Request Item"),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Request Item"),
                                                                      T("Select Items from the Request"))),
                                      ondelete = "CASCADE",
                                      script = '''
$.filterOptionsS3({
 'trigger':'req_item_id',
 'target':'item_pack_id',
 'lookupResource':'item_pack',
 'lookupPrefix':'supply',
 'lookupURL':S3.Ap.concat('/req/req_item_packs/'),
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''')

        if settings.get_req_prompt_match():
            # Shows the inventory items which match a requested item
            # @ToDo: Make this page a component of req_item
            create_next = URL(c="req",
                              f="req_item_inv_item",
                              args=["[id]"])
        else:
            create_next = None

        list_fields = ["id",
                       "item_id",
                       "item_pack_id",
                       ]
        lappend = list_fields.append
        if settings.get_req_prompt_match():
            lappend("site_id")
        lappend("quantity")
        if use_commit:
            lappend("quantity_commit")
        if show_qty_transit:
            lappend("quantity_transit")
        lappend("quantity_fulfil")
        lappend("comments")

        filter_widgets = [
            S3OptionsFilter("req_id$fulfil_status",
                            label = T("Status"),
                            options = self.req_status_opts,
                            cols = 3,
                            ),
            S3OptionsFilter("req_id$priority",
                            label = T("Priority"),
                            options = self.req_priority_opts,
                            cols = 3,
                            ),
            S3LocationFilter("req_id$site_id$location_id",
                             ),
            ]

        self.configure(tablename,
                       create_next = create_next,
                       deduplicate = self.req_item_duplicate,
                       deletable = settings.get_req_multiple_req_items(),
                       extra_fields = ["item_pack_id"],
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = req_item_onaccept,
                       ondelete = req_item_ondelete,
                       super_entity = "supply_item_entity",
                       )

        # ---------------------------------------------------------------------
        #
        # Req <> Item Category link table
        #
        # - used to provide a search filter
        # - populated onaccept/ondelete of req_item
        #
        tablename = "req_req_item_category"
        define_table(tablename,
                     req_id(empty=False),
                     self.supply_item_category_id(),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(req_item_id = req_item_id,
                    req_item_represent = self.req_item_represent,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(req_item_id = lambda **attr: dummy("req_item_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_represent(id, row=None):
        """
            Represent a Request Item
        """

        if row:
            # @ToDo: Optimised query where we don't need to do the join
            id = row.id
        elif not id:
            return current.messages["NONE"]

        db = current.db
        ritable = db.req_req_item
        sitable = db.supply_item
        query = (ritable.id == id) & \
                (ritable.item_id == sitable.id)
        record = db(query).select(sitable.name,
                                  limitby = (0, 1)).first()
        if record:
            return record.name
        else:
            return None

    # ---------------------------------------------------------------------
    @staticmethod
    def req_qnty_commit_represent(quantity, show_link=True):
        """
            call the generic quantity represent
        """
        return S3RequestItemModel.req_quantity_represent(quantity,
                                                         "commit",
                                                         show_link)

    # ---------------------------------------------------------------------
    @staticmethod
    def req_qnty_transit_represent(quantity, show_link=True):
        """
            call the generic quantity represent
        """
        return S3RequestItemModel.req_quantity_represent(quantity,
                                                         "transit",
                                                         show_link)

    # ---------------------------------------------------------------------
    @staticmethod
    def req_qnty_fulfil_represent(quantity, show_link=True):
        """
            call the generic quantity represent
        """
        return S3RequestItemModel.req_quantity_represent(quantity,
                                                         "fulfil",
                                                         show_link)

    # ---------------------------------------------------------------------
    @staticmethod
    def req_quantity_represent(quantity, type, show_link=True):
        """
            @ToDo: There should be better control of this feature - currently this only works
                   with req_items which are being matched by commit / send / recv
        """

        if quantity and show_link and \
           not current.deployment_settings.get_req_item_quantities_writable():
            return TAG[""](quantity,
                           A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                 ),
                             _href = "#",
                             )
                           )
        else:
            return quantity

    # -------------------------------------------------------------------------
    @staticmethod
    def req_item_duplicate(item):
        """
            This callback will be called when importing records. It will look
            to see if the record being imported is a duplicate.

            @param item: An S3ImportItem object which includes all the details
                         of the record being imported

            If the record is a duplicate then it will set the item method to update

            Rules for finding a duplicate:
                - If the Request Number matches
                - The item is the same
        """

        db = current.db

        itable = item.table
        rtable = db.req_req
        stable = db.supply_item

        req_id = None
        item_id = None
        for ref in item.references:
            if ref.entry.tablename == "req_req":
                if ref.entry.id != None:
                    req_id = ref.entry.id
                else:
                    uuid = ref.entry.item_id
                    jobitem = item.job.items[uuid]
                    req_id = jobitem.id
            elif ref.entry.tablename == "supply_item":
                if ref.entry.id != None:
                    item_id = ref.entry.id
                else:
                    uuid = ref.entry.item_id
                    jobitem = item.job.items[uuid]
                    item_id = jobitem.id

        if req_id is not None and item_id is not None:
            query = (itable.req_id == req_id) & \
                    (itable.item_id == item_id)
        else:
            return

        duplicate = db(query).select(itable.id,
                                     limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3RequestSkillModel(S3Model):
    """
    """

    names = ("req_req_skill",
             "req_skill_represent",
             )

    def model(self):

        T = current.T

        settings = current.deployment_settings
        quantities_writable = settings.get_req_skill_quantities_writable()
        use_commit = settings.get_req_use_commit()

        define_table = self.define_table

        # -----------------------------------------------------------------
        # Request Skills
        #
        tablename = "req_req_skill"
        define_table(tablename,
                     self.req_req_id(empty=False),
                     # Make this a Component
                     #Field("task",
                     #      readable=False,
                     #      writable=False, # Populated from req_req 'Purpose'
                     #      label = T("Task Details")),
                     self.hrm_multi_skill_id(
                          label = T("Required Skills"),
                          comment = T("Leave blank to request an unskilled person"),
                          represent = lambda id: \
                                      id and S3Represent(lookup="hrm_skill",
                                                         multiple=True)(id) or \
                                      T("No Skills Required"),
                          ),
                     # @ToDo: Add a minimum competency rating?
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           requires = IS_INT_IN_RANGE(1, 999999),
                           label = T("Number of People Required"),
                           ),
                     self.org_site_id,
                     Field("quantity_commit", "integer",
                           label = T("Quantity Committed"),
                           default = 0,
                           requires = IS_INT_IN_RANGE(0, 999999),
                           readable = use_commit,
                           writable = use_commit and quantities_writable),
                     Field("quantity_transit", "integer",
                           label = T("Quantity in Transit"),
                           #represent = lambda quantity_transit: \
                           # req_quantity_represent(quantity_transit,
                           #                        "transit"),
                           default = 0,
                           requires = IS_INT_IN_RANGE(0, 999999),
                           writable = quantities_writable),
                     Field("quantity_fulfil", "integer",
                           label = T("Quantity Fulfilled"),
                           default = 0,
                           requires = IS_INT_IN_RANGE(0, 999999),
                           writable = quantities_writable),
                     s3_comments(
                                 #label = T("Task Details"),
                                 #comment = DIV(_class="tooltip",
                                 #              _title="%s|%s" % (T("Task Details"),
                                 #                                T("Include any special requirements such as equipment which they need to bring.")))
                                 ),
                     *s3_meta_fields())

        # @todo: make lazy_table
        table = current.db[tablename]
        table.site_id.label = T("Requested From")

        if not settings.get_req_show_quantity_transit():
            table.quantity_transit.writable = table.quantity_transit.readable= False

        # CRUD strings
        ADD_REQUEST_SKILL = T("Add Skill to Request")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_REQUEST_SKILL,
            title_display = T("Requested Skill Details"),
            title_list = T("Requested Skills"),
            title_update = T("Edit Requested Skill"),
            label_list_button = T("List Requested Skills"),
            label_delete_button = T("Remove Skill from Request"),
            msg_record_created = T("Skill added to Request"),
            msg_record_modified = T("Requested Skill updated"),
            msg_record_deleted = T("Skill removed from Request"),
            msg_list_empty = T("No Skills currently requested"))

        list_fields = ["id",
                       "skill_id",
                       # @ToDo: Activate based on a deployment_setting
                       #"task",
                       "quantity",
                       "quantity_transit",
                       "quantity_fulfil",
                       "comments",
                       ]
        if use_commit:
            list_fields.insert(3, "quantity_commit")

        # Filter Widgets
        filter_widgets = [
            S3OptionsFilter("req_id$fulfil_status",
                            label = T("Status"),
                            options = self.req_status_opts,
                            cols = 3,
                            ),
            S3OptionsFilter("req_id$priority",
                            label = T("Priority"),
                            options = self.req_priority_opts,
                            cols = 3,
                            ),
            S3LocationFilter("req_id$site_id$location_id",
                             ),
        ]

        # Configuration
        self.configure(tablename,
                       # @ToDo: Produce a custom controller like req_item_inv_item?
                       #create_next = URL(c="req", f="req_skill_skill",
                       #                  args=["[id]"]),
                       deletable = settings.get_req_multiple_req_items(),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       onaccept = req_skill_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(req_skill_represent = self.req_skill_represent,
                    )

    # -----------------------------------------------------------------
    @staticmethod
    def req_skill_represent(id):
        """
            Used in controllers/req.py commit()
        """

        if not id:
            return current.messages["NONE"]

        db = current.db
        rstable = db.req_req_skill
        hstable = db.hrm_skill
        query = (rstable.id == id) & \
                (rstable.skill_id == hstable.id)
        record = db(query).select(hstable.name,
                                  limitby = (0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
class S3RequestRecurringModel(S3Model):
    """
    """

    names = ("req_job",)

    def model(self):

        T = current.T
        s3 = current.response.s3

        # -----------------------------------------------------------------
        # Request Job
        #
        # Jobs for Scheduling Recurring Requests
        #
        tablename = "req_job"
        self.define_table(tablename,
                          self.req_req_id(empty=False),
                          s3.scheduler_task_id(),
                          *s3_meta_fields())

        # CRUD Strings
        ADD_JOB = T("Create Job")
        s3.crud_strings[tablename] = Storage(
            label_create = ADD_JOB,
            title_display = T("Request Job"),
            title_list = T("Request Schedule"),
            title_update = T("Edit Job"),
            label_list_button = T("List Jobs"),
            msg_record_created = T("Job added"),
            msg_record_modified = T("Job updated"),
            msg_record_deleted = T("Job deleted"),
            msg_list_empty = T("No jobs configured yet"),
            msg_no_match = T("No jobs configured"))

        # Resource Configuration
        self.set_method("req", "req",
                        component_name="job",
                        method="reset",
                        action=req_job_reset)

        # Resource Configuration
        self.set_method("req", "req",
                        component_name="job",
                        method="run",
                        action=req_job_run)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3RequestSummaryModel(S3Model):
    """
        Simple Requests Management System
        - Organisations can request Money or Time from remote volunteers
        - Sites can request Time from local volunteers or accept drop-off for Goods
    """

    names = ("req_organisation_needs",
             "req_site_needs",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # -----------------------------------------------------------------
        # Summary of Needs for an Organisation
        #
        tablename = "req_organisation_needs"
        define_table(tablename,
                     self.org_organisation_id(
                         requires = self.org_organisation_requires(required=True),
                         ),
                     Field("money", "boolean",
                           label = T("Soliciting Cash Donations?"),
                           represent = s3_yes_no_represent,
                           default = False,
                           ),
                     Field("money_details", "text",
                           label = T("Details"),
                           widget = s3_richtext_widget,
                           ),
                     Field("vol", "boolean",
                           label = T("Opportunities to Volunteer Remotely?"),
                           represent = s3_yes_no_represent,
                           default = False,
                           ),
                     Field("vol_details", "text",
                           label = T("Details"),
                           widget = s3_richtext_widget,
                           ),
                     *s3_meta_fields())

        # CRUD strings
        ADD_NEEDS = T("Add Organization Needs")
        crud_strings[tablename] = Storage(
            title_display=T("Organization Needs"),
            title_update=T("Edit Organization Needs"),
            label_delete_button=T("Delete Organization Needs"),
            msg_record_created=T("Organization Needs added"),
            msg_record_modified=T("Organization Needs updated"),
            msg_record_deleted=T("Organization Needs deleted"))

        configure(tablename,
                  context = {"organisation": "organisation_id",
                             },
                  )

        # -----------------------------------------------------------------
        # Summary of Needs for a site
        #
        tablename = "req_site_needs"
        define_table(tablename,
                     self.super_link("site_id", "org_site"),
                     Field("vol", "boolean",
                           label = T("Opportunities to Volunteer On-Site?"),
                           represent = s3_yes_no_represent,
                           default = False,
                           ),
                     Field("vol_details", "text",
                           label = T("Details"),
                           widget = s3_richtext_widget,
                           ),
                     Field("goods", "boolean",
                           label = T("Drop-off Location for Goods?"),
                           represent = s3_yes_no_represent,
                           default = False,
                           ),
                     Field("goods_details", "text",
                           label = T("Details"),
                           widget = s3_richtext_widget,
                           ),
                     #s3_comments("needs",
                     #            label=T("Needs"),
                     #            comment=None,
                     #            widget=S3PriorityListWidget(),
                     #            ),
                     *s3_meta_fields())

        # CRUD strings
        ADD_NEEDS = T("Add Site Needs")
        crud_strings[tablename] = Storage(
            title_display=T("Site Needs"),
            title_update=T("Edit Site Needs"),
            label_delete_button=T("Delete Site Needs"),
            msg_record_created=T("Site Needs added"),
            msg_record_modified=T("Site Needs updated"),
            msg_record_deleted=T("Site Needs deleted"))

        configure(tablename,
                  context = {"location": "site_id$location_id",
                             "organisation": "site_id$organisation_id",
                             "site": "site_id",
                             },
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3RequestTaskModel(S3Model):
    """
        Link Requests for Skills to Tasks
    """

    names = ("req_task",)

    def model(self):

        #T = current.T

        # -----------------------------------------------------------------
        # Link Skill Requests to Tasks
        #
        tablename = "req_task_req"
        self.define_table(tablename,
                          self.project_task_id(),
                          self.req_req_id(empty=False),
                          #self.req_req_person_id(),
                          #self.req_req_skill_id(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3CommitModel(S3Model):
    """
    """

    names = ("req_commit",
             "req_commit_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        add_components = self.add_components

        settings = current.deployment_settings
        req_types = settings.get_req_req_type()
        commit_value = settings.get_req_commit_value()
        unsolicited_commit = settings.get_req_commit_without_request()
        committer_is_author = settings.get_req_committer_is_author()
        if committer_is_author:
            site_default = auth.user.site_id if auth.is_logged_in() else None
            committer_default = auth.s3_logged_in_person()
        else:
            site_default = None
            committer_default = None

        # Dropdown or Autocomplete?
        if settings.get_org_site_autocomplete():
            site_widget = S3SiteAutocompleteWidget()
            site_comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("From Facility"),
                                                 current.messages.AUTOCOMPLETE_HELP))
        else:
            site_widget = None
            site_comment = None

        # ---------------------------------------------------------------------
        # Commitments (Pledges)
        tablename = "req_commit"
        self.define_table(tablename,
                          self.super_link("site_id", "org_site",
                                          comment = site_comment,
                                          default = site_default,
                                          label = T("From Facility"),
                                          # Non-Item Requests make False in the prep
                                          readable = True,
                                          writable = True,
                                          represent = self.org_site_represent,
                                          updateable = True,
                                          widget = site_widget,
                                          ),
                          self.gis_location_id(
                                # Used for reporting on where Donations originated
                                readable = False,
                                writable = False
                                ),
                          # Non-Item Requests make True in the prep
                          self.org_organisation_id(
                                readable = False,
                                writable = False
                                ),
                          # @ToDo: deployment_setting for whether this can be empty
                          self.req_req_id(
                            empty = not unsolicited_commit,
                            ),
                          Field("type", "integer",
                                # These are copied automatically from the Req
                                readable = False,
                                writable = False,
                                ),
                          s3_datetime(default = "now",
                                      represent = "date",
                                      ),
                          s3_datetime("date_available",
                                      label = T("Date Available"),
                                      represent = "date",
                                      ),
                          self.pr_person_id("committer_id",
                                            default = committer_default,
                                            label = T("Committed By"),
                                            comment = self.pr_person_comment(child="committer_id"),
                                            ),
                          # @ToDo: Calculate this from line items in Item Commits
                          Field("value", "double",
                                label = T("Estimated Value"),
                                readable = commit_value,
                                writable = commit_value,
                                ),
                          # @ToDo: Move this into a Currency Widget for the value field
                          s3_currency(readable = commit_value,
                                      writable = commit_value,
                                      ),
                          Field("cancel", "boolean",
                                default = False,
                                label = T("Cancel"),
                                readable = False,
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        filter_widgets = [
            S3TextFilter(["committer_id$first_name",
                          "committer_id$middle_name",
                          "committer_id$last_name",
                          "site_id$name",
                          "comments",
                          "req_id$name",
                          "organisation_id$name"
                          ],
                         label = T("Search"),
                         comment = T("Search for a commitment by Committer name, Request ID, Site or Organization."),
                         ),
            S3LocationFilter("location_id",
                             hidden = True,
                             ),
            S3DateFilter("date",
                         label = T("Date"),
                         hide_time = True,
                         comment = T("Search for commitments made between these dates."),
                         hidden = True,
                         ),
            S3DateFilter("date_available",
                         label = T("Date Available"),
                         hide_time = True,
                         comment = T("Search for commitments available between these dates."),
                         hidden = True,
                         ),
            ]
        if len(req_types) > 1:
            filter_widgets.insert(1, S3OptionsFilter("type",
                                                     label = T("Type"),
                                                     cols = len(req_types),
                                                     hidden = True,
                                                     ))

        # CRUD strings
        ADD_COMMIT = T("Make Commitment")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_COMMIT,
            title_display = T("Commitment Details"),
            title_list = T("Commitments"),
            title_update = T("Edit Commitment"),
            label_list_button = T("List Commitments"),
            label_delete_button = T("Delete Commitment"),
            msg_record_created = T("Commitment Added"),
            msg_record_modified = T("Commitment Updated"),
            msg_record_deleted = T("Commitment Canceled"),
            msg_list_empty = T("No Commitments"))

        # Reusable Field
        commit_id = S3ReusableField("commit_id", "reference %s" % tablename,
                                    label = T("Commitment"),
                                    ondelete = "CASCADE",
                                    represent = self.commit_represent,
                                    requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "req_commit.id",
                                                              self.commit_represent,
                                                              orderby="req_commit.date",
                                                              sort=True)),
                                    sortby = "date",
                                    )

        self.configure(tablename,
                       context = {"event": "req_id$event_id",
                                  "location": "location_id",
                                  "organisation": "organisation_id",
                                  "request": "req_id",
                                  #"site": "site_id",
                                  "site": "req_id$site_id",
                                  },
                       filter_widgets = filter_widgets,
                       list_fields = ["site_id",
                                      "req_id",
                                      "committer_id",
                                      # @ToDo: Vary by deployment_setting (easy)
                                      # @ToDo: Allow a single column to support different components based on type
                                      # @ToDo: Include Qty too (Computed VF in component?)
                                      (T("Committed Items"), "commit_item.req_item_id$item_id"),
                                      #(T("Committed People"), "commit_person.person_id"),
                                      #(T("Committed Skills"), "commit_skill.skill_id"),
                                      "date",
                                      "date_available",
                                      "comments",
                                      ],
                       # Commitments should only be made to a specific request
                       listadd = unsolicited_commit,
                       onaccept = self.commit_onaccept,
                       ondelete = self.commit_ondelete,
                       onvalidation = self.commit_onvalidation,
                       )

        # Components
        add_components(tablename,
                       # Committed Items
                       req_commit_item = "commit_id",
                       # Committed Persons
                       req_commit_person = "commit_id",
                       # Committed Skills
                       req_commit_skill = "commit_id",
                      )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(req_commit_id = commit_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_represent(id, row=None):
        """
            Represent a Commit
        """

        if row:
            table = current.db.req_commit
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.req_commit
            row = db(table.id == id).select(table.type,
                                            table.date,
                                            table.organisation_id,
                                            table.site_id,
                                            limitby=(0, 1)).first()
        if row.type == 1:
            # Items
            return "%s - %s" % (table.site_id.represent(row.site_id),
                                table.date.represent(row.date))
        else:
            return "%s - %s" % (table.organisation_id.represent(row.organisation_id),
                                table.date.represent(row.date))

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_onvalidation(form):
        """
            Copy the request_type to the commitment
        """

        req_id = s3_get_last_record_id("req_req")
        if req_id:
            rtable = current.s3db.req_req
            query = (rtable.id == req_id)
            req_record = current.db(query).select(rtable.type,
                                                  limitby=(0, 1)).first()
            if req_record:
                form.vars.type = req_record.type

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_onaccept(form):
        """
            Update Status of Request & components
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars
        # @ToDo: Will this always be in vars?
        id = form_vars.id
        if not id:
            return

        ctable = s3db.req_commit

        site_id = form_vars.get("site_id", None)
        if site_id:
            # Set location_id to location of site
            stable = s3db.org_site
            site = db(stable.site_id == site_id).select(stable.location_id,
                                                        limitby=(0, 1)).first()
            if site and site.location_id:
                db(ctable.id == id).update(location_id = site.location_id)

        # Find the request
        rtable = s3db.req_req
        query = (ctable.id == id) & \
                (rtable.id == ctable.req_id)
        req = db(query).select(rtable.id,
                               rtable.type,
                               rtable.req_status,
                               rtable.commit_status,
                               limitby=(0, 1)).first()
        if not req:
            return
        req_id = req.id
        type = req.type
        if type == 1:
            # Items
            # Update Commit Status for Items in the Request
            # Get the full list of items in the request
            ritable = s3db.req_req_item
            query = (ritable.req_id == req_id) & \
                    (ritable.deleted == False)
            ritems = db(query).select(ritable.id,
                                      ritable.item_pack_id,
                                      ritable.quantity,
                                      # Virtual Field
                                      #ritable.pack_quantity,
                                      )
            # Get all Commits in-system
            citable = s3db.req_commit_item
            query = (ctable.req_id == req_id) & \
                    (citable.commit_id == ctable.id) & \
                    (citable.deleted == False)
            citems = db(query).select(citable.item_pack_id,
                                      citable.quantity,
                                      # Virtual Field
                                      #citable.pack_quantity,
                                      )
            commit_qty = {}
            for item in citems:
                item_pack_id = item.item_pack_id
                if item_pack_id in commit_qty:
                    commit_qty[item_pack_id] += (item.quantity * item.pack_quantity())
                else:
                    commit_qty[item_pack_id] = (item.quantity * item.pack_quantity())
            complete = False
            for item in ritems:
                if item.item_pack_id in commit_qty:
                    quantity_commit = commit_qty[item.item_pack_id]
                    db(ritable.id == item.id).update(quantity_commit=quantity_commit)
                    req_quantity = item.quantity * item.pack_quantity()
                    if quantity_commit >= req_quantity:
                        complete = True
                    else:
                        complete = False

            # Update overall Request Status
            if complete:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            else:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

        elif type == 3:
            # People
            ## If this is a single person commitment, then create the commit_person record automatically
            #table = s3db.req_commit_person
            #table.insert(commit_id = id,
            #             #skill_id = ???,
            #             person_id = auth.s3_logged_in_person())
            ## @ToDo: Mark Person's allocation status as 'Committed'

            # Update Commit Status for Skills in the Request
            # Get the full list of skills in the request
            # @ToDo: Breakdown to component Skills within multi
            rstable = s3db.req_req_skill
            query = (rstable.req_id == req_id) & \
                    (rstable.deleted == False)
            rskills = db(query).select(rstable.id,
                                       rstable.skill_id,
                                       rstable.quantity,
                                       )
            # Get all Commits in-system
            cstable = s3db.req_commit_skill
            query = (ctable.req_id == req_id) & \
                    (cstable.commit_id == ctable.id) & \
                    (cstable.deleted == False)
            cskills = db(query).select(cstable.skill_id,
                                       cstable.quantity,
                                       )
            commit_qty = {}
            for skill in cskills:
                multi_skill_id = skill.skill_id
                for skill_id in multi_skill_id:
                    if skill_id in commit_qty:
                        commit_qty[skill_id] += skill.quantity
                    else:
                        commit_qty[skill_id] = skill.quantity
            complete = False
            for skill in rskills:
                multi_skill_id = skill.skill_id
                quantity_commit = 0
                for skill_id in multi_skill_id:
                    if skill_id in commit_qty:
                        if commit_qty[skill_id] > quantity_commit:
                            quantity_commit = commit_qty[skill_id]
                db(rstable.id == skill.id).update(quantity_commit=quantity_commit)
                req_quantity = skill.quantity
                if quantity_commit >= req_quantity:
                    complete = True
                else:
                    complete = False

            # Update overall Request Status
            if complete:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            else:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

        elif type == 9:
            # Other
            # Assume Partial not Complete
            # @ToDo: Provide a way for the committer to specify this
            data = {}
            if req.commit_status == REQ_STATUS_NONE:
                data["commit_status"] = REQ_STATUS_PARTIAL
            if req.req_status == REQ_STATUS_NONE:
                # Show as 'Responded'
                data["req_status"] = REQ_STATUS_PARTIAL
            if data:
                db(rtable.id == req_id).update(**data)

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_ondelete(row):
        """
            Update Status of Request & components
        """

        db = current.db
        s3db = current.s3db
        id = row.id
        # Find the request
        ctable = s3db.req_commit
        fks = db(ctable.id == id).select(ctable.deleted_fk,
                                         limitby=(0, 1)
                                         ).first().deleted_fk
        req_id = json.loads(fks)["req_id"]
        rtable = s3db.req_req
        req = db(rtable.id == req_id).select(rtable.id,
                                             rtable.type,
                                             rtable.commit_status,
                                             limitby=(0, 1)).first()
        if not req:
            return
        req_id = req.id
        type = req.type
        if type == 1:
            # Items
            # Update Commit Status for Items in the Request
            # Get the full list of items in the request
            ritable = s3db.req_req_item
            query = (ritable.req_id == req_id) & \
                    (ritable.deleted == False)
            ritems = db(query).select(ritable.id,
                                      ritable.item_pack_id,
                                      ritable.quantity,
                                      # Virtual Field
                                      #ritable.pack_quantity,
                                      )
            # Get all Commits in-system
            # - less those from this commit
            citable = s3db.req_commit_item
            query = (ctable.req_id == req_id) & \
                    (citable.commit_id == ctable.id) & \
                    (citable.commit_id != id) & \
                    (citable.deleted == False)
            citems = db(query).select(citable.item_pack_id,
                                      citable.quantity,
                                      # Virtual Field
                                      #citable.pack_quantity,
                                      )
            commit_qty = {}
            for item in citems:
                item_pack_id = item.item_pack_id
                if item_pack_id in commit_qty:
                    commit_qty[item_pack_id] += (item.quantity * item.pack_quantity())
                else:
                    commit_qty[item_pack_id] = (item.quantity * item.pack_quantity())
            complete = False
            for item in ritems:
                if item.item_pack_id in commit_qty:
                    quantity_commit = commit_qty[item.item_pack_id]
                    db(ritable.id == item.id).update(quantity_commit=quantity_commit)
                    req_quantity = item.quantity * item.pack_quantity()
                    if quantity_commit >= req_quantity:
                        complete = True
                    else:
                        complete = False

            # Update overall Request Status
            if complete:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            elif not citems:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_NONE)
            else:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

        elif type == 3:
            # People
            ## If this is a single person commitment, then create the commit_person record automatically
            #table = s3db.req_commit_person
            #table.insert(commit_id = vars.id,
            #             #skill_id = ???,
            #             person_id = auth.s3_logged_in_person())
            ## @ToDo: Mark Person's allocation status as 'Committed'
            # Update Commit Status for Skills in the Request
            # Get the full list of skills in the request
            rstable = s3db.req_req_skill
            query = (rstable.req_id == req_id) & \
                    (rstable.deleted == False)
            rskills = db(query).select(rstable.id,
                                       rstable.skill_id,
                                       rstable.quantity,
                                       )
            # Get all Commits in-system
            # - less those from this commit
            cstable = s3db.req_commit_skill
            query = (ctable.req_id == req_id) & \
                    (cstable.commit_id == ctable.id) & \
                    (cstable.commit_id != id) & \
                    (cstable.deleted == False)
            cskills = db(query).select(cstable.skill_id,
                                       cstable.quantity,
                                       )
            commit_qty = {}
            for skill in cskills:
                multi_skill_id = skill.skill_id
                for skill_id in multi_skill_id:
                    if skill_id in commit_qty:
                        commit_qty[skill_id] += skill.quantity
                    else:
                        commit_qty[skill_id] = skill.quantity
            complete = False
            for skill in rskills:
                multi_skill_id = skill.skill_id
                quantity_commit = 0
                for skill_id in multi_skill_id:
                    if skill_id in commit_qty:
                        if commit_qty[skill_id] > quantity_commit:
                            quantity_commit = commit_qty[skill_id]
                db(rstable.id == skill.id).update(quantity_commit=quantity_commit)
                req_quantity = skill.quantity
                if quantity_commit >= req_quantity:
                    complete = True
                else:
                    complete = False

            # Update overall Request Status
            if complete:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
            elif not cskills:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_NONE)
            else:
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

        elif type == 9:
            # Other
            if req.commit_status != REQ_STATUS_NONE:
                # Assume Complete not partial
                # @ToDo: Provide a way for the committer to specify this
                db(rtable.id == req_id).update(commit_status=REQ_STATUS_NONE)

# =============================================================================
class S3CommitItemModel(S3Model):
    """
    """

    names = ("req_commit_item",
             "req_send_commit"
             )

    def model(self):

        T = current.T

        # -----------------------------------------------------------------
        # Commitment Items
        # @ToDo: Update the req_item_id in the commit_item if the req_id of the commit is changed

        tablename = "req_commit_item"
        self.define_table(tablename,
                          self.req_commit_id(),
                          #item_id,
                          #supply_item_id(),
                          self.req_item_id(),
                          self.supply_item_pack_id(),
                          Field("quantity", "double", notnull=True,
                                label = T("Quantity")),
                          Field.Method("pack_quantity",
                                       self.supply_item_pack_quantity(tablename=tablename)),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        ADD_COMMIT_ITEM = T("Add Item to Commitment")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_COMMIT_ITEM,
            title_display = T("Commitment Item Details"),
            title_list = T("Commitment Items"),
            title_update = T("Edit Commitment Item"),
            label_list_button = T("List Commitment Items"),
            label_delete_button = T("Delete Commitment Item"),
            msg_record_created = T("Commitment Item added"),
            msg_record_modified = T("Commitment Item updated"),
            msg_record_deleted = T("Commitment Item deleted"),
            msg_list_empty = T("No Commitment Items currently registered"))

        self.configure(tablename,
                       onaccept = self.commit_item_onaccept,
                       extra_fields = ["item_pack_id"])

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(# Used by commit_req() controller
                    req_commit_item_onaccept = self.commit_item_onaccept,
                    req_send_commit = self.req_send_commit,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_item_onaccept(form):
        """
            Update the Commit Status for the Request Item & Request
        """

        db = current.db

        vars = form.vars
        req_item_id = vars.req_item_id

        # Get the req_id
        ritable = db.req_req_item
        req = db(ritable.id == req_item_id).select(ritable.req_id,
                                                   limitby=(0, 1)).first()
        if not req:
            return
        req_id = req.req_id

        # Get the full list of items in the request
        query = (ritable.req_id == req_id) & \
                (ritable.deleted == False)
        ritems = db(query).select(ritable.id,
                                  ritable.item_pack_id,
                                  ritable.quantity,
                                  # Virtual Field
                                  #ritable.pack_quantity,
                                  )
        # Get all Commits in-system
        ctable = db.req_commit
        citable = db.req_commit_item
        query = (ctable.req_id == req_id) & \
                (citable.commit_id == ctable.id) & \
                (citable.deleted == False)
        citems = db(query).select(citable.item_pack_id,
                                  citable.quantity,
                                  # Virtual Field
                                  #citable.pack_quantity,
                                  )
        commit_qty = {}
        for item in citems:
            item_pack_id = item.item_pack_id
            if item_pack_id in commit_qty:
                commit_qty[item_pack_id] += (item.quantity * item.pack_quantity())
            else:
                commit_qty[item_pack_id] = (item.quantity * item.pack_quantity())
        complete = False
        for item in ritems:
            if item.item_pack_id in commit_qty:
                quantity_commit = commit_qty[item.item_pack_id]
                db(ritable.id == item.id).update(quantity_commit=quantity_commit)
                req_quantity = item.quantity * item.pack_quantity()
                if quantity_commit >= req_quantity:
                    complete = True
                else:
                    complete = False

        # Update overall Request Status
        rtable = db.req_req
        if complete:
            db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
        else:
            db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

    # -------------------------------------------------------------------------
    @staticmethod
    def req_send_commit():
        """
            Create a Shipment containing all items in a Commitment
        """

        # Get the commit record
        try:
            commit_id = current.request.args[0]
        except:
            redirect(URL(c="req",
                         f="commit"))

        db = current.db
        s3db = current.s3db
        req_table = db.req_req
        rim_table = db.req_req_item
        com_table = db.req_commit
        cim_table = db.req_commit_item
        send_table = s3db.inv_send
        tracktable = s3db.inv_track_item

        query = (com_table.id == commit_id) & \
                (com_table.req_id == req_table.id) & \
                (com_table.deleted == False)
        record = db(query).select(com_table.committer_id,
                                  com_table.site_id,
                                  com_table.organisation_id,
                                  req_table.requester_id,
                                  req_table.site_id,
                                  req_table.req_ref,
                                  limitby=(0, 1)).first()

        # @ToDo: Identify if we have stock items which match the commit items
        # If we have a single match per item then proceed automatically (as-now) & then decrement the stock quantity
        # If we have no match then warn the user & ask if they should proceed anyway
        # If we have mulitple matches then provide a UI to allow the user to select which stock items to use

        # Create an inv_send and link to the commit
        vars = Storage(sender_id = record.req_commit.committer_id,
                       site_id = record.req_commit.site_id,
                       recipient_id = record.req_req.requester_id,
                       to_site_id = record.req_req.site_id,
                       req_ref = record.req_req.req_ref,
                       status = 0)
        send_id = send_table.insert(**vars)
        vars.id = send_id

        # Get all of the committed items
        query = (cim_table.commit_id == commit_id) & \
                (cim_table.req_item_id == rim_table.id) & \
                (cim_table.deleted == False)
        records = db(query).select(rim_table.id,
                                   rim_table.item_id,
                                   rim_table.item_pack_id,
                                   rim_table.currency,
                                   rim_table.quantity,
                                   rim_table.quantity_transit,
                                   rim_table.quantity_fulfil,
                                   cim_table.quantity,
                                   )
        # Create inv_track_items for each commit item
        insert = tracktable.insert
        for row in records:
            rim = row.req_req_item
            # Now done as a VirtualField instead (looks better & updates closer to real-time, so less of a race condition)
            #quantity_shipped = max(rim.quantity_transit, rim.quantity_fulfil)
            #quantity_needed = rim.quantity - quantity_shipped
            id = insert(req_item_id = rim.id,
                        track_org_id = record.req_commit.organisation_id,
                        send_id = send_id,
                        status = 1,
                        item_id = rim.item_id,
                        item_pack_id = rim.item_pack_id,
                        currency = rim.currency,
                        #req_quantity = quantity_needed,
                        quantity = row.req_commit_item.quantity,
                        recv_quantity = row.req_commit_item.quantity,
                        )

        # Create the Waybill
        form = Storage()
        form.vars = vars
        s3db.inv_send_onaccept(form)

        # Redirect to inv_send for the send id just created
        redirect(URL(#c = "inv", or "req"
                     f = "send",
                     #args = [send_id, "track_item"]
                     args = [send_id]
                     ))

# =============================================================================
class S3CommitPersonModel(S3Model):
    """
        Commit a named individual to a Request
    """

    names = ("req_commit_person",)

    def model(self):

        T = current.T

        # -----------------------------------------------------------------
        # Committed Persons
        #
        tablename = "req_commit_person"
        self.define_table(tablename,
                          self.req_commit_id(),
                          # For reference
                          self.hrm_multi_skill_id(
                              writable=False,
                              comment=None,
                          ),
                          # This should be person not hrm as we want to mark them as allocated
                          self.pr_person_id(),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        ADD_COMMIT_PERSON = T("Add Person to Commitment")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_COMMIT_PERSON,
            title_display = T("Committed Person Details"),
            title_list = T("Committed People"),
            title_update = T("Edit Committed Person"),
            label_list_button = T("List Committed People"),
            label_delete_button = T("Remove Person from Commitment"),
            msg_record_created = T("Person added to Commitment"),
            msg_record_modified = T("Committed Person updated"),
            msg_record_deleted = T("Person removed from Commitment"),
            msg_list_empty = T("No People currently committed"))

        # @ToDo: Fix this before enabling
        #self.configure(tablename,
        #                onaccept = self.commit_person_onaccept)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_person_onaccept(form):
        """
            Not working
        """

        db = current.db
        s3db = current.s3db
        table = db.req_commit_person
        rstable = s3db.req_req_skill

        # Try to get req_skill_id from the form
        req_skill_id = 0
        if form:
            req_skill_id = form.vars.get("req_skill_id", None)
        if not req_skill_id:
            commit_skill_id = s3_get_last_record_id("req_commit_skill")
            r_commit_skill = table[commit_skill_id]
            req_skill_id = r_commit_skill.req_skill_id

        query = (table.req_skill_id == req_skill_id) & \
                (table.deleted == False)
        commit_skills = db(query).select(table.quantity)
        quantity_commit = 0
        for commit_skill in commit_skills:
            quantity_commit += commit_skill.quantity

        r_req_skill = db.req_req_skill[req_skill_id]
        rstable[req_skill_id] = dict(quantity_commit = quantity_commit)

        # Update status_commit of the req record
        s3_store_last_record_id("req_req_skill", r_req_skill.id)
        req_skill_onaccept(None)

# =============================================================================
class S3CommitSkillModel(S3Model):
    """
        Commit anonymous people to a Request
    """

    names = ("req_commit_skill",)

    def model(self):

        T = current.T

        # -----------------------------------------------------------------
        # Committed Skills
        #
        tablename = "req_commit_skill"
        self.define_table(tablename,
                          self.req_commit_id(),
                          self.hrm_multi_skill_id(),
                          Field("quantity", "double", notnull=True,
                                label = T("Quantity")),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add People to Commitment"),
            title_display = T("Committed People Details"),
            title_list = T("Committed People"),
            title_update = T("Edit Committed People"),
            label_list_button = T("List Committed People"),
            label_delete_button = T("Remove People from Commitment"),
            msg_record_created = T("People added to Commitment"),
            msg_record_modified = T("Committed People updated"),
            msg_record_deleted = T("People removed from Commitment"),
            msg_list_empty = T("No People currently committed"))

        self.configure(tablename,
                       onaccept = self.commit_skill_onaccept)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def commit_skill_onaccept(form):
        """
            Update the Commit Status for the Request Skill & Request
        """

        db = current.db

        vars = form.vars
        req_skill_id = vars.req_skill_id

        # Get the req_id
        rstable = db.req_req_skill
        req = db(rstable.id == req_skill_id).select(rstable.req_id,
                                                    limitby=(0, 1)).first()
        if not req:
            return
        req_id = req.req_id

        # Get the full list of skills in the request
        query = (rstable.req_id == req_id) & \
                (rstable.deleted == False)
        rskills = db(query).select(rstable.id,
                                   rstable.skill_id,
                                   rstable.quantity,
                                   )
        # Get all Commits in-system
        ctable = db.req_commit
        cstable = db.req_commit_skill
        query = (ctable.req_id == req_id) & \
                (cstable.commit_id == ctable.id) & \
                (cstable.deleted == False)
        cskills = db(query).select(cstable.skill_id,
                                   cstable.quantity,
                                   )
        commit_qty = {}
        for skill in cskills:
            multi_skill_id = skill.skill_id
            for skill_id in multi_skill_id:
                if skill_id in commit_qty:
                    commit_qty[skill_id] += skill.quantity
                else:
                    commit_qty[skill_id] = skill.quantity
        complete = False
        for skill in rskills:
            multi_skill_id = skill.skill_id
            quantity_commit = 0
            for skill_id in multi_skill_id:
                if skill_id in commit_qty:
                    if commit_qty[skill_id] > quantity_commit:
                        quantity_commit = commit_qty[skill_id]
            db(rstable.id == skill.id).update(quantity_commit=quantity_commit)
            req_quantity = skill.quantity
            if quantity_commit >= req_quantity:
                complete = True
            else:
                complete = False

        # Update overall Request Status
        rtable = db.req_req
        if complete:
            db(rtable.id == req_id).update(commit_status=REQ_STATUS_COMPLETE)
        else:
            db(rtable.id == req_id).update(commit_status=REQ_STATUS_PARTIAL)

# =============================================================================
def req_item_onaccept(form):
    """
        Update Request Status
        Update req_item_category link table
    """

    req_id = form.vars.get("req_id", None)
    if not req_id:
        req_id = s3_get_last_record_id("req_req")
    if not req_id:
        raise HTTP(500, "can not get req_id")

    # Update Request Status
    req_update_status(req_id)

    # Update req_item_category link table
    item_id = form.vars.get("item_id", None)
    db = current.db
    citable = db.supply_catalog_item
    cats = db(citable.item_id == item_id).select(citable.item_category_id)
    rictable = db.req_req_item_category
    for cat in cats:
        item_category_id = cat.item_category_id
        query = (rictable.deleted == False) & \
                (rictable.req_id == req_id) & \
                (rictable.item_category_id == item_category_id)
        exists = db(query).select(rictable.id,
                                  limitby=(0, 1))
        if not exists:
            rictable.insert(req_id = req_id,
                            item_category_id = item_category_id)

# =============================================================================
def req_item_ondelete(row):
    """
    """

    db = current.db
    sitable = db.supply_item
    ritable = db.req_req_item
    item = db(ritable.id == row.id).select(ritable.deleted_fk,
                                           limitby=(0, 1)).first()
    fks = json.loads(item.deleted_fk)
    req_id = fks["req_id"]
    item_id = fks["item_id"]
    citable = db.supply_catalog_item
    cats = db(citable.item_id == item_id).select(citable.item_category_id)
    for cat in cats:
        item_category_id = cat.item_category_id
        # Check if we have other req_items in the same category
        query = (ritable.deleted == False) & \
                (ritable.req_id == req_id) & \
                (ritable.item_id == sitable.id) & \
                (sitable.item_category_id == item_category_id)
        others = db(query).select(ritable.id,
                                  limitby=(0, 1))
        if not others:
            # Delete req_item_category link table
            rictable = db.req_req_item_category
            query = (rictable.req_id == req_id) & \
                    (rictable.item_category_id == item_category_id)
            db(query).delete()

# =============================================================================
def req_update_status(req_id):
    """
        Update Request Status
            commit_status, transit_status, fulfil_status
        None => quantity = 0 for ALL items
        Partial => some items have quantity > 0
        Complete => quantity_x = quantity(requested) for ALL items
    """

    db = current.db
    s3db = current.s3db
    table = s3db.req_req_item
    is_none = dict(commit = True,
                   transit = True,
                   fulfil = True)

    is_complete = dict(commit = True,
                       transit = True,
                       fulfil = True)
    # Must check all items in the req
    query = (table.req_id == req_id) & \
            (table.deleted == False )
    req_items = db(query).select(table.quantity,
                                 table.quantity_commit,
                                 table.quantity_transit,
                                 table.quantity_fulfil)

    for req_item in req_items:
        quantity = req_item.quantity
        for status_type in ["commit", "transit", "fulfil"]:
            if req_item["quantity_%s" % status_type] < quantity:
                is_complete[status_type] = False
            if req_item["quantity_%s" % status_type]:
                is_none[status_type] = False

    status_update = {}
    for status_type in ["commit", "transit", "fulfil"]:
        if is_complete[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
        elif is_none[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_NONE
        else:
            status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL

    rtable = s3db.req_req
    db(rtable.id == req_id).update(**status_update)

# =============================================================================
def req_skill_onaccept(form):
    """
        Update req_req. commit_status, transit_status, fulfil_status
        None => quantity = 0 for ALL skills
        Partial => some skills have quantity > 0
        Complete => quantity_x = quantity(requested) for ALL skills

        Create a Task for People to be assigned to
    """

    if form and form.vars.req_id:
        req_id = form.vars.req_id
    else:
        req_id = s3_get_last_record_id("req_req")
    if not req_id:
        raise HTTP(500, "can not get req_id")

    db = current.db
    s3db = current.s3db
    rtable = s3db.req_req
    query = (rtable.id == req_id)
    record = db(query).select(rtable.purpose,
                              limitby=(0, 1)).first()

    table = s3db.req_req_skill
    query = (table.req_id == req_id)
    #if record:
    #    # Copy the Task description to the Skills component
    #    db(query).update(task=record.purpose)

    is_none = dict(commit = True,
                   transit = True,
                   fulfil = True)

    is_complete = dict(commit = True,
                       transit = True,
                       fulfil = True)

    # Must check all skills in the req
    req_skills = db(query).select(table.quantity,
                                  table.quantity_commit,
                                  table.quantity_transit,
                                  table.quantity_fulfil)

    for req_skill in req_skills:
        quantity = req_skill.quantity
        for status_type in ["commit", "transit", "fulfil"]:
            if req_skill["quantity_%s" % status_type] < quantity:
                is_complete[status_type] = False
            if req_skill["quantity_%s" % status_type]:
                is_none[status_type] = False

    status_update = {}
    for status_type in ["commit", "transit", "fulfil"]:
        if is_complete[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
        elif is_none[status_type]:
            status_update["%s_status" % status_type] = REQ_STATUS_NONE
        else:
            status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL
    query = (rtable.id == req_id)
    db(query).update(**status_update)

    if current.deployment_settings.has_module("project"):
        # Add a Task to which the People can be assigned

        # Get the request record
        otable = s3db.org_site
        query = (rtable.id == req_id) & \
                (otable.id == rtable.site_id)
        record = db(query).select(rtable.req_ref,
                                  rtable.purpose,
                                  rtable.priority,
                                  rtable.requester_id,
                                  rtable.site_id,
                                  otable.location_id,
                                  limitby=(0, 1)).first()
        if not record:
            return

        name = record.req_req.req_ref or "Req: %s" % req_id
        table = s3db.project_task
        task = table.insert(name=name,
                            description=record.req_req.purpose,
                            priority=record.req_req.priority,
                            location_id=record.org_site.location_id,
                            site_id=record.req_req.site_id)

        # Add the Request as a Component to the Task
        table = s3db.table("req_task_req", None)
        if table:
            table.insert(task_id = task,
                         req_id = req_id)

# =============================================================================
def req_req_details(row):
    """ Show the requested items/skills """

    if hasattr(row, "req_req"):
        row = row.req_req
    try:
        id = row.id
        type = row.type
    except AttributeError:
        return None

    if type == 1:
        s3db = current.s3db
        itable = s3db.supply_item
        ltable = s3db.req_req_item
        query = (ltable.deleted != True) & \
                (ltable.req_id == id) & \
                (ltable.item_id == itable.id)
        items = current.db(query).select(itable.name,
                                         ltable.quantity)
        if items:
            items = ["%s %s" % (int(item.req_req_item.quantity),
                                item.supply_item.name)
                     for item in items]
            return ",".join(items)

    elif type == 3:
        s3db = current.s3db
        ltable = s3db.req_req_skill
        query = (ltable.deleted != True) & \
                (ltable.req_id == id)
        skills = current.db(query).select(ltable.skill_id,
                                          ltable.quantity)
        if skills:
            represent = S3Represent(lookup="hrm_skill",
                                    multiple=True,
                                    none=current.T("Unskilled")
                                   )
            skills = ["%s %s" % (skill.quantity,
                                 represent(skill.skill_id)) \
                      for skill in skills]
            return ",".join(skills)

    return current.messages["NONE"]

# =============================================================================
def req_req_drivers(row):
    """ Show the driver(s) details """

    if hasattr(row, "req_req"):
        row = row.req_req
    try:
        req_ref = row.req_ref
        type = row.type
    except AttributeError:
        return None

    if type == 1:
        s3db = current.s3db
        stable = s3db.inv_send
        query = (stable.deleted != True) & \
                (stable.req_ref == req_ref)
        drivers = current.db(query).select(stable.driver_name,
                                           stable.driver_phone,
                                           stable.vehicle_plate_no)
        if drivers:
            drivers = ["%s %s %s" % (driver.driver_name or "",
                                     driver.driver_phone or "",
                                     driver.vehicle_plate_no or "") \
                       for driver in drivers]
            return ",".join(drivers)

    return current.messages["NONE"]

# =============================================================================
def req_rheader(r, check_page=False):
    """ Resource Header for Requests """

    if r.representation == "html":
        if r.name == "req":
            record = r.record
            if record:

                T = current.T
                s3db = current.s3db
                request = current.request
                s3 = current.response.s3
                settings = current.deployment_settings

                use_commit = settings.get_req_use_commit()
                is_template = record.is_template

                tabs = [(T("Edit Details"), None)]
                type = record.type
                if type == 1 and settings.has_module("inv"):
                    if settings.get_req_multiple_req_items():
                        req_item_tab_label = T("Items")
                    else:
                        req_item_tab_label = T("Item")
                    tabs.append((req_item_tab_label, "req_item"))
                elif type == 3 and settings.has_module("hrm"):
                    tabs.append((T("People"), "req_skill"))
                tabs.append((T("Documents"), "document"))
                if is_template:
                    tabs.append((T("Schedule"), "job"))
                elif use_commit:
                    tabs.append((T("Commitments"), "commit"))

                if not check_page:
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                else:
                    rheader_tabs = DIV()

                site_id = request.vars.site_id
                if site_id and not is_template:
                    site_name = s3db.org_site_represent(site_id, show_link=False)
                    commit_btn = A(T("Send from %s") % site_name,
                                   _href = URL(c = "req",
                                               f = "send_req",
                                               args = [r.id],
                                               vars = dict(site_id = site_id)
                                               ),
                                   _class = "action-btn"
                                   )
                    s3.rfooter = TAG[""](commit_btn)
                elif r.component and \
                     r.component_name == "commit" and \
                     r.component_id:
                    prepare_btn = A(T("Prepare Shipment"),
                                    _href = URL(f = "send_commit",
                                                args = [r.component_id]
                                                ),
                                    _id = "send_commit",
                                    _class = "action-btn"
                                    )
                    s3.rfooter = TAG[""](prepare_btn)

                site_id = record.site_id
                if site_id:
                    db = current.db
                    stable = s3db.org_site
                if settings.get_req_show_quantity_transit() and not is_template:
                    transit_status = s3db.req_status_opts.get(record.transit_status,
                                                              "")
                    try:
                        if site_id and \
                           record.transit_status in [REQ_STATUS_PARTIAL, REQ_STATUS_COMPLETE] and \
                           record.fulfil_status in [None, REQ_STATUS_NONE, REQ_STATUS_PARTIAL]:
                            site_record = db(stable.site_id == site_id).select(stable.uuid,
                                                                               stable.instance_type,
                                                                               limitby=(0, 1)).first()
                            instance_type = site_record.instance_type
                            table = s3db[instance_type]
                            query = (table.uuid == site_record.uuid)
                            id = db(query).select(table.id,
                                                  limitby=(0, 1)).first().id
                            # @ToDo: Create this function!
                            #transit_status = SPAN(transit_status,
                            #                      A(T("Incoming Shipments"),
                            #                        _href = URL(c = instance_type.split("_")[0],
                            #                                    f = "incoming",
                            #                                    vars = {"viewing" : "%s.%s" % (instance_type, id)}
                            #                                    )
                            #                        )
                            #                      )
                    except:
                        pass
                    transit_status = (TH("%s: " % T("Transit Status")),
                                      transit_status)
                else:
                    transit_status = ("")

                table = r.table

                if settings.get_req_use_req_number() and not is_template:
                    headerTR = TR(TH("%s: " % table.req_ref.label),
                                  TD(table.req_ref.represent(record.req_ref, show_link=True))
                                  )
                else:
                    headerTR = TR(TD(settings.get_req_form_name(),
                                  _colspan=2, _class="pdf_title"),
                                  )
                if site_id:
                    org_id = db(stable.site_id == site_id).select(stable.organisation_id,
                                                                  limitby=(0, 1)
                                                                  ).first().organisation_id
                    logo = s3db.org_organisation_logo(org_id)
                    if logo:
                        headerTR.append(TD(logo, _colspan=2))

                if is_template:
                    commit_status = ("")
                    fulfil_status = ("")
                    row1 = ""
                    row3 = ""
                else:
                    if use_commit:
                        commit_status = (TH("%s: " % table.commit_status.label),
                                         table.commit_status.represent(record.commit_status))
                    else:
                        commit_status = ("")
                    fulfil_status = (TH("%s: " % table.fulfil_status.label),
                                     table.fulfil_status.represent(record.fulfil_status))
                    row1 = TR(TH("%s: " % table.date.label),
                              table.date.represent(record.date),
                              *commit_status
                              )
                    row3 = TR(TH("%s: " % table.date_required.label),
                              table.date_required.represent(record.date_required),
                              *fulfil_status
                              )

                rData = TABLE(headerTR,
                              row1,
                              TR(TH("%s: " % table.site_id.label),
                                 table.site_id.represent(site_id),
                                 *transit_status
                                 ),
                              TR(TH("%s: " % table.requester_id.label),
                                 table.requester_id.represent(record.requester_id),
                                 ),
                              row3,
                              TR(TH("%s: " % table.purpose.label),
                                 record.purpose
                                 ),
                              TR(TH("%s: " % table.comments.label),
                                 TD(record.comments or "", _colspan=3)
                                 ),
                              )

                rheader = DIV(rData,
                              rheader_tabs,
                              )
                return rheader
    return None

# =============================================================================
def req_match(rheader=None):
    """
        Function to be called from controller functions to display all
        requests for a site as a tab.
    """

    T = current.T
    s3db = current.s3db
    s3 = current.response.s3
    request = current.request
    settings = current.deployment_settings

    output = dict()

    viewing = request.get_vars.get("viewing", None)
    if not viewing:
        return output
    if "." in viewing:
        tablename, record_id = viewing.split(".", 1)
    else:
        return output

    table = s3db[tablename]
    row = current.db(table.id == record_id).select(table.site_id, 
                                                   limitby=(0, 1)).first()
    if row:
        site_id = row.site_id
    else:
        return output

    actions = [dict(url = URL(c = "req",
                              f = "req",
                              args = ["[id]", "check"],
                              vars = {"site_id": site_id}
                              ),
                    _class = "action-btn",
                    label = str(T("Check")),
                    )
               ]

    if current.auth.s3_has_permission("update", tablename, record_id):
        # @ToDo: restrict to those which we've not already committed/sent?
        if settings.get_req_use_commit():
            actions.append(
                dict(url = URL(c = "req",
                               f = "commit_req",
                               args = ["[id]"],
                               vars = {"site_id": site_id}
                               ),
                     _class = "action-btn",
                     label = str(T("Commit")),
                     )
                )
        actions.append(
                dict(url = URL(c = "req",
                               f = "send_req",
                               args = ["[id]"],
                               vars = {"site_id": site_id}
                               ),
                     _class = "action-btn dispatch",
                     label = str(T("Send")),
                     )
                )

    s3.actions = actions

    if rheader is None:
        if tablename == "org_office":
            rheader = s3db.org_rheader
        elif tablename == "org_facility":
            rheader = s3db.org_facility_rheader
        elif tablename == "inv_warehouse":
            rheader = s3db.inv_rheader
        elif tablename == "cr_shelter":
            rheader = s3db.cr_shelter_rheader
        elif tablename == "hms_hospital":
            rheader = s3db.hms_hospital_rheader

    s3.filter = (s3db.req_req.site_id != site_id)
    s3db.configure("req_req",
                   insertable = False)

    # Pre-process
    def prep(r):
        # Plugin OrgRoleManager when appropriate
        S3OrgRoleManager.set_method(r, entity=tablename, record_id=record_id)
        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.representation == "html":
            output["title"] = s3.crud_strings[tablename].title_display
        return output
    s3.postp = postp

    output = current.rest_controller("req", "req",
                                     rheader = rheader)
    return output

# =============================================================================
def req_job_reset(r, **attr):
    """
        RESTful method to reset a job status from FAILED to QUEUED,
        for "Reset" action button
    """

    if r.interactive:
        if r.component and r.component.alias == "job":
            job_id = r.component_id
            if job_id:
                S3Task.reset(job_id)
                current.session.confirmation = current.T("Job reactivated")
    r.component_id = None
    redirect(r.url(method=""))

# =============================================================================
def req_job_run(r, **attr):
    """
        RESTful method to run a job now,
        for "Run Now" action button
    """

    if r.interactive:
        if r.id:
            current.s3task.async("req_add_from_template",
                                 [r.id], # args
                                 {"user_id":current.auth.user.id} # vars
                                 )
            current.session.confirmation = current.T("Request added")
    r.component_id = None
    redirect(r.url(method=""))

# =============================================================================
def req_add_from_template(req_id):
    """
        Add a Request from a Template
    """

    fieldnames = ["type",
                  "priority",
                  "site_id",
                  "purpose",
                  "requester_id",
                  "comments",
                  ]
    db = current.db
    s3db = current.s3db
    table = s3db.req_req
    fields = [table[field] for field in fieldnames]
    # Load Template
    template = db(table.id == req_id).select(limitby=(0, 1),
                                             *fields).first()
    data = {"is_template": False}
    try:
        for field in fieldnames:
            data[field] = template[field]
    except:
        raise "Template not found: %s" % req_id

    settings = current.deployment_settings
    if settings.get_req_use_req_number():
        code = s3db.supply_get_shipping_code(settings.get_req_shortname(),
                                             template.site_id,
                                             table.req_ref,
                                             )
        data["req_ref"] = code

    id = table.insert(**data)

    if template.type == 1:
        # Copy across req_item
        table = s3db.req_req_item
        fieldnames = ["site_id",
                      "item_id",
                      "item_pack_id",
                      "quantity",
                      "pack_value",
                      "currency",
                      "comments",
                      ]
        fields = [table[field] for field in fieldnames]
        items = db(table.req_id == req_id).select(*fields)
        for item in items:
            data = {"req_id": id}
            for field in fieldnames:
                data[field] = item[field]
            table.insert(**data)

    elif template.type == 3:
        # Copy across req_skill
        table = s3db.req_req_skill
        fieldnames = ["site_id",
                      "task",
                      "skill_id",
                      "quantity",
                      "comments",
                      ]
        fields = [table[field] for field in fieldnames]
        skills = db(table.req_id == req_id).select(*fields)
        for skill in skills:
            data = {"req_id": id}
            for field in fieldnames:
                data[field] = skill[field]
            table.insert(**data)

    return id

# =============================================================================
def req_customise_req_fields():
    """
        Customize req_req fields for the Home page & dataList view
        - this assumes Simple Requests (i.e. type 'Other')
    """

    # Truncate purpose field
    from s3.s3utils import s3_trunk8
    s3_trunk8(lines=2)

    T = current.T
    db = current.db
    s3db = current.s3db

    tablename = "req_req"
    table = s3db.req_req

    crud_fields = ["date",
                   #"priority",
                   "site_id",
                   #"is_template",
                   "requester_id",
                   "purpose",
                   ]

    request = current.request
    args = request.args
    if "update.popup" in args or \
       "update" in args:
        field = table.req_status
        field.writable = True
        field.requires = IS_IN_SET({REQ_STATUS_NONE:     T("Open"),
                                    REQ_STATUS_PARTIAL:  T("Responded"),
                                    REQ_STATUS_COMPLETE: T("Resolved"),
                                    REQ_STATUS_CANCEL:   T("Cancelled"),
                                    })
        crud_fields.append("req_status")

    crud_form = S3SQLCustomForm(*crud_fields)

    list_fields = crud_fields + ["site_id$location_id",
                                 "site_id$location_id$level",
                                 "site_id$location_id$parent",
                                 "site_id$organisation_id",
                                 "site_id$comments",
                                 ]

    table.type.default = 9 # Other

    field = table.purpose
    field.label = T("Request")
    field.requires = IS_NOT_EMPTY(error_message=T("Please enter details of the Request"))
    field.represent = lambda body: XML(s3_URLise(body))

    field = table.date
    field.label = T("Date")
    # Make mandatory
    requires = field.requires
    field.requires = requires.other

    field = table.site_id
    site_id = request.get_vars.get("~.(site)", None)
    if site_id:
        field.default = site_id
        field.readable = field.writable = False
        # Lookup Site Contact
        script = \
'''var fieldname='req_req_requester_id'
var real_input=$('#'+fieldname)
$.when(S3.addPersonWidgetReady(fieldname)).then(
function(status){real_input.data('lookup_contact')(fieldname,%s)},
function(status){s3_debug(status)},
function(status){s3_debug(status)})''' % site_id
        current.response.s3.jquery_ready.append(script)
    else:
        # If the Requester is blank, then lookup default Site Contact
        script = \
'''$('#req_req_site_id').change(function(){
 var site_id=$(this).val()
 if(site_id){
  var fieldname='req_req_requester_id'
  var real_input=$('#'+fieldname)
  if(!real_input.val()&&!$('#req_req_requester_id_full_name').val()){
   real_input.data('lookup_contact')(fieldname,site_id)
}}})'''
        current.response.s3.jquery_ready.append(script)

        organisation_id = request.get_vars.get("~.(organisation)", None)
        if organisation_id:
            # Restrict to Sites belonging to this Org
            # @ToDo: Handle Branches
            filterby = "organisation_id"
            filter_opts = (organisation_id,)
            # No need to use Site Autocomplete in this case
            field.widget = None
        else:
            filterby = None
            filter_opts = None

        field.label = T("Requested for Site")
        #site_represent = s3db.org_SiteRepresent(show_link=False,
        #                                        show_type=False)
        site_represent = S3Represent(lookup="org_site")
        field.represent = site_represent
        field.requires = IS_ONE_OF(db, "org_site.site_id",
                                   site_represent,
                                   filterby = filterby,
                                   filter_opts = filter_opts,
                                   not_filterby = "obsolete",
                                   not_filter_opts = (True,),
                                   orderby = "org_site.name",
                                   sort = True,
                                   )
        field.comment = S3AddResourceLink(c="org", f="facility",
                                          vars = dict(child="site_id",
                                                      parent="req"),
                                          title=T("Add New Site"),
                                          )

    db.org_site.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")

    field = table.requester_id
    field.requires = IS_ADD_PERSON_WIDGET2()
    field.widget = S3AddPersonWidget2(controller="pr")

    filter_widgets = [
        S3TextFilter(["requester_id$first_name",
                      "requester_id$middle_name",
                      "requester_id$last_name",
                      "site_id$name",
                      "purpose",
                      #"comments",
                      ],
                     label = T("Search"),
                     comment=T("Search for a request by Site name, Requester name or free text."),
                     ),
        #S3OptionsFilter("transit_status",
        #                label = T("Transit Status"),
        #                options = s3db.req_status_opts,
        #                cols = 3,
        #                ),
        #S3OptionsFilter("fulfil_status",
        #                label = T("Fulfill Status"),
        #                options = s3db.req_status_opts,
        #                cols = 3,
        #                ),
        S3LocationFilter("site_id$location_id",
                         #hidden = True,
                         ),
        S3OptionsFilter("site_id",
                        label = T("Requested For Site"),
                        hidden = True,
                        ),
        S3DateFilter("date",
                     label = T("Date"),
                     hide_time = True,
                     input_labels = {"ge": "From", "le": "To"},
                     comment = T("Search for requests made between these dates."),
                     hidden = True,
                     ),
        #S3DateFilter("date_required",
        #             label = T("Date Needed By"),
        #             hide_time = True,
        #             input_labels = {"ge": "From", "le": "To"},
        #             comment = T("Search for requests required between these dates."),
        #             hidden = True,
        #             ),
        ]
    # @ToDo: deployment_setting
    if current.auth.s3_has_role("EDITOR"):
        filter_widgets.insert(-1, S3OptionsFilter("created_by",
                                                  label = T("Logged By"),
                                                  hidden = True,
                                                  ))

    # Return to Requests view after create/update/delete (unless done via Modal)
    url_next = URL(c="req", f="req", args="datalist")

    s3db.configure(tablename,
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   filter_formstyle = filter_formstyle,
                   filter_widgets = filter_widgets,
                   # We want the Create form to be in a modal, not inline, for consistency
                   listadd = False,
                   list_fields = list_fields,
                   list_layout = req_req_list_layout,
                   update_next = url_next,
                   )

    return table

# =============================================================================
def req_req_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Requests on the Home page & dataList view

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["req_req.id"]
    item_class = "thumbnail"

    raw = record._row
    date = record["req_req.date"]
    body = record["req_req.purpose"]

    location = record["org_site.location_id"] or ""
    level = raw["gis_location.level"]
    if level:
        location_id = raw["org_site.location_id"]
    else:
        location_id = raw["gis_location.parent"]
    if location_id:
        location_url = URL(c="gis", f="location", args=[location_id, "profile"])
    else:
        location_url = "#"

    organisation = record["org_site.organisation_id"] or ""
    organisation_id = raw["org_site.organisation_id"]
    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])

    person = record["req_req.requester_id"]
    person_id = raw["req_req.requester_id"]
    person_url = URL(c="pr", f="person", args=[person_id])
    person = A(person,
               _href=person_url,
               )

    # Avatar
    # Try Organisation Logo
    db = current.db
    otable = db.org_organisation
    row = db(otable.id == organisation_id).select(otable.logo,
                                                  limitby=(0, 1)
                                                  ).first()
    if row and row.logo:
        logo = URL(c="default", f="download", args=[row.logo])
        avatar = IMG(_src=logo,
                     _height=50,
                     _width=50,
                     _style="padding-right:5px;",
                     _class="media-object")
        avatar = A(avatar,
                   _href=org_url,
                   _class="pull-left",
                   )
    else:
        # Personal Avatar
        avatar = s3_avatar_represent(person_id,
                                     tablename="pr_person",
                                     _class="media-object")

        avatar = A(avatar,
                   _href=person_url,
                   _class="pull-left",
                   )

    # Edit Bar
    T = current.T
    auth = current.auth
    permit = auth.s3_has_permission
    table = db.req_req
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="req", f="req",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=T("Edit Request"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    s3db = current.s3db

    site = record["req_req.site_id"]
    site_id = raw["req_req.site_id"]
    table = s3db.org_facility
    facility = db(table.site_id == site_id).select(table.id,
                                                   limitby=(0, 1)
                                                   ).first()
    if facility:
        site_url = URL(c="org", f="facility",
                       args=[facility.id, "profile"])
        opts = dict(_href=site_url)
        site_comments = raw["org_site.comments"] or ""
        if site_comments:
            opts["_class"] = "s3-popover"
            opts["_data-toggle"] = "popover"
            opts["_data-content"] = site_comments
        site_link = A(site, **opts)
        card_title = TAG[""](I(_class="icon icon-request"),
                             SPAN(site_link,
                                  _class="card-title"))
    else:
        card_title = TAG[""](I(_class="icon icon-request"),
                             SPAN(" ",
                                  _class="card-title"))

    #if priority == 3:
    #    # Apply additional highlighting for High Priority
    #    item_class = "%s disaster" % item_class

    # Tallies
    # NB We assume that all records are readable here
    table = s3db.req_commit
    query = (table.deleted == False) & \
            (table.req_id == record_id)
    tally_commits = db(query).count()

    #if permit("create", table):
    if auth.is_logged_in():
        _class="s3_modal btn"
        commit_url = URL(c="req", f="commit",
                         args=["create.popup"],
                         vars={"req_id": record_id,
                               "refresh": list_id,
                               "record": record_id,
                               },
                         )
    else:
        _class="btn"
        next = "/%s/req/commit/create?req_id=%s" % (current.request.application,
                                                    record_id)
        commit_url = URL(c="default", f="user",
                         args="login",
                         vars={"_next": next,
                               },
                         )
    commit_btn = A(I(" ", _class="icon icon-truck"),
                   " ",
                   T("DONATE"),
                   _href=commit_url,
                   _class=_class,
                   _title=T("Donate to this Request"),
                   )

    # Render the item
    item = DIV(DIV(card_title,
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(SPAN(body,
                                _class="s3-truncate"),
                           DIV(person,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media pull-left",
                           ),
                       DIV(P(A(T("Donations"),
                               _href=URL(c="req", f="req",
                                         args=[record_id, "profile"],
                                         ),
                               ),
                             SPAN(tally_commits,
                                  _class="badge",
                                  ),
                             _class="tally",
                             ),
                           commit_btn,
                           _class="media pull-right",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def req_customise_commit_fields():
    """
        Customize req_commit fields for the Home page & dataList view
    """

    # Truncate comments field
    from s3.s3utils import s3_trunk8
    s3_trunk8(lines=2)

    T = current.T
    s3db = current.s3db
    settings = current.deployment_settings
    tablename = "req_commit"
    table = s3db.req_commit

    list_fields = [#"req_id", # populated automatically or not at all?
                   "organisation_id",
                   "committer_id",
                   "comments",
                   "date_available",
                   # We'd like to be able to map donations, but harder for users to enter data
                   #"location_id",
                   ]

    if settings.get_req_commit_value():
        list_fields += ["value",
                        "currency",
                        ]

    request = current.request
    args = request.args
    if "create.popup" in args or \
       "create" in args:
        req_id = request.get_vars.get("req_id", None)
        if req_id:
            table.req_id.default = req_id
        elif not settings.get_req_commit_without_request():
            current.session.error = T("Not allowed to Donate without matching to a Request!")
            redirect(URL(c="req", f="req", args=["datalist"]))
    elif "update.popup" in args or \
         "update" in args:
        list_fields.append("cancel")

    # CRUD strings
    #ADD_COMMIT = T("Make Donation")
    ADD_COMMIT = T("Add Donation")
    current.response.s3.crud_strings[tablename] = Storage(
        label_create = ADD_COMMIT,
        title_display = T("Donation Details"),
        title_list = T("Donations"),
        title_update = T("Edit Donation"),
        label_list_button = T("List Donations"),
        label_delete_button = T("Delete Donation"),
        msg_record_created = T("Donation Added"),
        msg_record_modified = T("Donation Updated"),
        msg_record_deleted = T("Donation Canceled"),
        msg_list_empty = T("No Donations"))

    auth = current.auth

    # @ToDo: deployment_setting
    if auth.s3_has_role("EDITOR"):
        editor = True
    else:
        editor = False

    field = table.committer_id
    if editor:
        field.requires = IS_ADD_PERSON_WIDGET2()
        field.widget = S3AddPersonWidget2(controller="pr")
        field.default = None
    else:
        field.writable = False

    #field = table.location_id
    #field.represent = s3db.gis_LocationRepresent(sep=" | ")
    # Required
    #field.requires = IS_LOCATION()

    field = table.comments
    field.label = T("Donation")
    field.represent = lambda body: XML(s3_URLise(body))
    field.required = True
    # @ToDo
    field.comment = None

    table.date_available.default = current.request.utcnow

    field = table.organisation_id
    field.readable = True
    field.comment = S3AddResourceLink(c="org", f="organisation_id",
                                      title=T("Create Organization"),
                                      )
    if settings.get_org_autocomplete():
        # Enable if there are many Orgs
        field.widget = S3OrganisationAutocompleteWidget()

    if editor:
        # Editor can select Org
        field.writable = True
        crud_form = S3SQLCustomForm(*list_fields)
    elif auth.user and auth.user.organisation_id:
        field.default = auth.user.organisation_id
        field.writable = False
        crud_form = S3SQLCustomForm(*list_fields)
    else:
        # Only a User representing an Org can commit for an Org
        field.default = None
        field.writable = False
        crud_fields = [f for f in list_fields if f != "organisation_id"]
        crud_form = S3SQLCustomForm(*crud_fields)

    filter_widgets = [
        S3TextFilter(["committer_id$first_name",
                      "committer_id$middle_name",
                      "committer_id$last_name",
                      "site_id$name",
                      "comments",
                      "req_id$name",
                      "organisation_id$name"
                      ],
                     label = T("Search"),
                     comment=T("Search for a commitment by Committer name, Request ID, Site or Organization."),
                     ),
        S3LocationFilter("location_id",
                         hidden = True,
                         ),
        #S3DateFilter("date",
        #             label = T("Date"),
        #             hide_time = True,
        #             input_labels = {"ge": "From", "le": "To"},
        #             comment = T("Search for commitments made between these dates."),
        #             hidden = True,
        #             ),
        S3DateFilter("date_available",
                     label = T("Date Available"),
                     hide_time = True,
                     input_labels = {"ge": "From", "le": "To"},
                     comment = T("Search for commitments available between these dates."),
                     hidden = True,
                     ),
        ]

    # Return to Requests view after create/update/delete (unless done via Modal)
    url_next = URL(c="req", f="req", args="datalist")

    s3db.configure(tablename,
                   create_next = url_next,
                   crud_form = crud_form,
                   delete_next = url_next,
                   filter_formstyle = filter_formstyle,
                   filter_widgets = filter_widgets,
                   # We want the Create form to be in a modal, not inline, for consistency
                   listadd = False,
                   list_fields = list_fields,
                   list_layout = req_commit_list_layout,
                   update_next = url_next,
                   )

    return table

# =============================================================================
def req_commit_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Commits on the Home page & dataList view

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["req_commit.id"]
    item_class = "thumbnail"

    raw = record._row
    date = record["req_commit.date_available"]
    body = record["req_commit.comments"]
    title = ""

    #location = record["req_commit.location_id"]
    #location_id = raw["req_commit.location_id"]
    #location_url = URL(c="gis", f="location", args=[location_id, "profile"])

    person = record["req_commit.committer_id"]
    person_id = raw["req_commit.committer_id"]
    person_url = URL(c="pr", f="person", args=[person_id])
    person = A(person,
               _href=person_url,
               )

    organisation_id = raw["req_commit.organisation_id"]
    if organisation_id:
        organisation = record["req_commit.organisation_id"]
        org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
        organisation = A(organisation,
                         _href=org_url,
                         _class="card-organisation",
                         )
        organisation = TAG[""](" - ",
                               organisation)
        # Use Organisation Logo
        # @ToDo: option for Personal Avatar (fallback if no Org Logo?)
        db = current.db
        otable = db.org_organisation
        row = db(otable.id == organisation_id).select(otable.logo,
                                                      limitby=(0, 1)
                                                      ).first()
        if row and row.logo:
            logo = URL(c="default", f="download", args=[row.logo])
        else:
            logo = URL(c="static", f="img", args="blank-user.gif")
        avatar = IMG(_src=logo,
                     _height=50,
                     _width=50,
                     _style="padding-right:5px;",
                     _class="media-object")
        avatar = A(avatar,
                   _href=org_url,
                   _class="pull-left",
                   )
    else:
        organisation = ""
        # Personal Avatar
        avatar = s3_avatar_represent(person_id,
                                     tablename="pr_person",
                                     _class="media-object")

        avatar = A(avatar,
                   _href=person_url,
                   _class="pull-left",
                   )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.req_commit
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="req", f="commit",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Donation"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    card_label = TAG[""](I(_class="icon icon-offer"),
                         SPAN(" %s" % title,
                              _class="card-title"))

    # Render the item
    item = DIV(DIV(card_label,
                   #SPAN(A(location,
                   #       _href=location_url,
                   #       ),
                   #     _class="location-title",
                   #     ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(SPAN(body,
                                _class="s3-truncate"),
                           DIV(person,
                               organisation,
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def filter_formstyle(row_id, label, widget, comment, hidden=False):
    """
        Custom Formstyle for FilterForm

        @param row_id: HTML id for the row
        @param label: the label
        @param widget: the form widget
        @param comment: the comment
        @param hidden: whether the row should initially be hidden or not
    """

    if hidden:
        _class = "advanced hide"
    else:
        _class= ""

    if not label:
        label = ""

    if comment:
        if current.response.s3.rtl:
            dir = "fleft"
        else:
            dir = "fright"
        comment = DIV(_class = "tooltip %s" % dir,
                      _title = "%s|%s" % (label[0][:-1], comment),
                      )
    else:
        comment = ""

    return DIV(label,
               widget,
               comment,
               _id=row_id,
               _class=_class,
               )

# END =========================================================================
