# -*- coding: utf-8 -*-

""" Sahana Eden Assets Model

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

__all__ = ("AssetModel",
           #"AssetHRModel",
           #"AssetTeamModel",
           "AssetTelephoneModel",
           #"asset_rheader",
           "asset_types",
           "asset_log_status",
           "asset_controller",
           "asset_AssetRepresent",
           )

import json

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# Dependency list for translate-module
depends = ["supply"]

ASSET_TYPE_VEHICLE   = 1   # => Extra Tab(s) for Registration Documents, Fuel Efficiency
#ASSET_TYPE_RADIO     = 2   # => Extra Tab(s) for Radio Channels/Frequencies
ASSET_TYPE_TELEPHONE = 3   # => Extra Tab(s) for Contact Details & Airtime Billing
ASSET_TYPE_OTHER     = 4   # => No extra Tabs

# To pass to global scope
asset_types = {"VEHICLE"    : ASSET_TYPE_VEHICLE,
               #"RADIO"      : ASSET_TYPE_RADIO,
               "TELEPHONE"  : ASSET_TYPE_TELEPHONE,
               "OTHER"      : ASSET_TYPE_OTHER,
               }

ASSET_LOG_SET_BASE = 1
ASSET_LOG_ASSIGN   = 2
ASSET_LOG_RETURN   = 3
ASSET_LOG_CHECK    = 4
ASSET_LOG_REPAIR   = 5
ASSET_LOG_DONATED  = 32
ASSET_LOG_LOST     = 33
ASSET_LOG_STOLEN   = 34
ASSET_LOG_DESTROY  = 35

# To pass to global scope
asset_log_status = {"SET_BASE" : ASSET_LOG_SET_BASE,
                    "ASSIGN"   : ASSET_LOG_ASSIGN,
                    "RETURN"   : ASSET_LOG_RETURN,
                    "CHECK"    : ASSET_LOG_CHECK,
                    "REPAIR"   : ASSET_LOG_REPAIR,
                    "DONATED"  : ASSET_LOG_DONATED,
                    "LOST"     : ASSET_LOG_LOST,
                    "STOLEN"   : ASSET_LOG_STOLEN,
                    "DESTROY"  : ASSET_LOG_DESTROY,
                    }

# =============================================================================
class AssetModel(S3Model):
    """
        Asset Management
    """

    names = ("asset_asset",
             "asset_item",
             "asset_log",
             "asset_asset_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        user = auth.user
        LOGGED_IN = auth.is_logged_in()
        org_site_types = auth.org_site_types
        s3 = current.response.s3

        item_id = self.supply_item_id
        item_entity_id = self.supply_item_entity_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        person_id = self.pr_person_id

        settings = current.deployment_settings
        org_site_label = settings.get_org_site_label()
        #radios = settings.get_asset_radios()
        telephones = settings.get_asset_telephones()
        vehicles = settings.has_module("vehicle")
        types = telephones or vehicles

        # Shortcuts
        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        #--------------------------------------------------------------------------
        # Assets
        #
        asset_type_opts = {ASSET_TYPE_OTHER : T("Other"),
                           }
        #if radios:
        #    asset_type_opts[ASSET_TYPE_RADIO] = T("Radio")
        if telephones:
            asset_type_opts[ASSET_TYPE_TELEPHONE] = T("Telephone")
        if vehicles:
            asset_type_opts[ASSET_TYPE_VEHICLE] = T("Vehicle")

        asset_condition_opts = {1: T("Good Condition"),
                                2: T("Minor Damage"),
                                3: T("Major Damage"),
                                4: T("Un-Repairable"),
                                5: T("Needs Maintenance"),
                                }

        # @ToDo: make this lookup Lazy (also in event.py)
        ctable = self.supply_item_category
        asset_categories = db(ctable.can_be_asset == True).select(ctable.id)
        asset_category_ids = [row.id for row in asset_categories]

        supply_item_represent = self.supply_item_represent

        tablename = "asset_asset"
        define_table(tablename,
                     # Instances
                     super_link("track_id", "sit_trackable"),
                     super_link("doc_id", "doc_entity"),
                     item_entity_id(),
                     Field("number",
                           label = T("Asset Number"),
                           ),
                     Field("type", "integer",
                           # @ToDo: We could set this automatically based on Item Category
                           default = ASSET_TYPE_OTHER,
                           label = T("Type"),
                           represent = s3_options_represent(asset_type_opts),
                           requires = IS_IN_SET(asset_type_opts),
                           readable = types,
                           writable = types,
                           ),
                     item_id(represent = supply_item_represent,
                             requires = IS_ONE_OF(db, "supply_item.id",
                                                  supply_item_represent,
                                                  filterby = "item_category_id",
                                                  filter_opts = asset_category_ids,
                                                  sort = True,
                                                  ),
                             script = None, # No Item Pack Filter
                             widget = None,
                             ),
                     Field("kit", "boolean",
                           default = False,
                           label = T("Kit?"),
                           represent = lambda opt: T("Yes") if opt else NONE,
                           # @ToDo: deployment_setting
                           readable = False,
                           writable = False,
                           ),
                     organisation_id(default = user.organisation_id if LOGGED_IN else None,
                                     requires = self.org_organisation_requires(updateable = True,
                                                                               #required = True,
                                                                               ),
                                     required = True,
                                     script = \
'''$.filterOptionsS3({
 'trigger':'organisation_id',
 'target':'site_id',
 'lookupResource':'site',
 'lookupPrefix':'org',
 'lookupField':'site_id',
 'lookupURL':S3.Ap.concat('/org/sites_for_org.json/')
})''',
                                     ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                default = user.site_id if LOGGED_IN else None,
                                empty = False,
                                instance_types = org_site_types,
                                label = org_site_label,
                                ondelete = "RESTRICT",
                                readable = True,
                                writable = True,
                                represent = self.org_site_represent,
                                # Comment these to use a Dropdown & not an Autocomplete
                                #widget = S3SiteAutocompleteWidget(),
                                #comment = DIV(_class = "tooltip",
                                #              _title = "%s|%s" % (T("Warehouse"),
                                #                                  messages.AUTOCOMPLETE_HELP,
                                #                                  ),
                                #              ),
                                ),
                     Field("sn",
                           label = T("Serial Number"),
                           ),
                     organisation_id("supply_org_id",
                                     label = T("Supplier/Donor"),
                                     ondelete = "SET NULL",
                                     ),
                     s3_date("purchase_date",
                             label = T("Purchase Date"),
                             ),
                     Field("purchase_price", "double",
                           #default = 0.00,
                           label = T("Purchase Price"),
                           represent = float_represent,
                           ),
                     s3_currency("purchase_currency"),
                     # Base Location, which should always be a Site & set via Log
                     location_id(readable = False,
                                 writable = False,
                                 ),
                     # Populated onaccept of the log to make a component tab
                     person_id("assigned_to_id",
                               readable = False,
                               writable = False,
                               comment = self.pr_person_comment(child = "assigned_to_id"),
                               ),
                     # Populated onaccept of the log for reporting/filtering
                     Field("cond", "integer",
                           label = T("Condition"),
                           represent = s3_options_represent(asset_condition_opts),
                           #readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_ASSET = T("Create Asset")
        crud_strings[tablename] = Storage(
            label_create = ADD_ASSET,
            title_display = T("Asset Details"),
            title_list =  T("Assets"),
            title_update = T("Edit Asset"),
            title_upload = T("Import Assets"),
            label_list_button =  T("List Assets"),
            label_delete_button = T("Delete Asset"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset deleted"),
            msg_list_empty = T("No Assets currently registered"),
            )

        asset_represent = asset_AssetRepresent(show_link = True)

        # Reusable Field
        asset_id = S3ReusableField("asset_id", "reference %s" % tablename,
                                   label = T("Asset"),
                                   ondelete = "CASCADE",
                                   represent = asset_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "asset_asset.id",
                                                          asset_represent,
                                                          sort = True,
                                                          )),
                                   sortby = "number",
                                   comment = S3PopupLink(c = "asset",
                                                         f = "asset",
                                                         label = ADD_ASSET,
                                                         title = T("Asset"),
                                                         ),
                                   )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        list_fields = ["item_id$item_category_id",
                       "item_id",
                       "number",
                       #"type",
                       #"purchase_date",
                       (T("Assigned To"), "assigned_to_id"),
                       "organisation_id",
                       "site_id",
                       ]

        report_fields = ["number",
                         (T("Category"), "item_id$item_category_id"),
                         (T("Item"), "item_id"),
                         "organisation_id",
                         "site_id",
                         "cond",
                         ]

        text_fields = ["number",
                       "item_id$name",
                       #"item_id$category_id$name",
                       "comments",
                       ]

        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)
            list_fields.append(lfield)

        list_fields.extend(("cond",
                            "comments",
                            ))

        if settings.get_org_branches():
            org_filter = S3HierarchyFilter("organisation_id",
                                           # Can be unhidden in customise_xx_resource if there is a need to use a default_filter
                                           hidden = True,
                                           leafonly = False,
                                           )
        else:
            org_filter = S3OptionsFilter("organisation_id",
                                         search = True,
                                         header = "",
                                         # Can be unhidden in customise_xx_resource if there is a need to use a default_filter
                                         hidden = True,
                                         )

        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         comment = T("You can search by asset number, item description or comments. You may use % as wildcard. Press 'Search' without input to list all assets."),
                         #_class = "filter-search",
                         ),
            S3OptionsFilter("item_id$item_category_id",
                            ),
            org_filter,
            S3LocationFilter("location_id",
                             levels = levels,
                             hidden = True,
                             ),
            S3OptionsFilter("cond",
                            hidden = True,
                            ),
            ]

        report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = [(T("Number of items"), "count(number)")],
            defaults=Storage(cols = "location_id$%s" % levels[0], # Highest-level of hierarchy
                             fact = "count(number)",
                             rows = "item_id$item_category_id",
                             totals = True,
                             )
            )

        # Default summary
        summary = [{"name": "addform",
                    "common": True,
                    "widgets": [{"method": "create"}],
                    },
                   {"name": "table",
                    "label": "Table",
                    "widgets": [{"method": "datatable"}]
                    },
                   {"name": "report",
                    "label": "Report",
                    "widgets": [{"method": "report",
                                 "ajax_init": True}]
                    },
                   {"name": "map",
                    "label": "Map",
                    "widgets": [{"method": "map",
                                 "ajax_init": True}],
                    },
                   ]

        # Resource Configuration
        configure(tablename,
                  context = {"incident": "incident.id",
                             "location": "location_id",
                             "organisation": "organisation_id",
                             },
                  # Open Tabs after creation
                  create_next = URL(c="asset", f="asset",
                                    args = ["[id]"],
                                    ),
                  deduplicate = S3Duplicate(primary = ("number",
                                                       ),
                                            secondary = ("site_id",
                                                         "organisation_id",
                                                         ),
                                            ignore_case = False,
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  mark_required = ("organisation_id",),
                  onaccept = self.asset_onaccept,
                  realm_components = ("log", "presence"),
                  report_options = report_options,
                  summary = summary,
                  super_entity = ("doc_entity", "sit_trackable", "supply_item_entity"),
                  update_realm = True,
                  )

        # Components
        add_components(tablename,
                       asset_group = "asset_id",
                       asset_item = "asset_id",
                       asset_log = "asset_id",
                       asset_human_resource = "asset_id",
                       asset_telephone = "asset_id",
                       asset_telephone_usage = "asset_id",
                       event_incident = {"link": "event_asset",
                                         "joinby": "asset_id",
                                         "key": "incident_id",
                                         "actuate": "hide",
                                         },
                       hrm_human_resource = {"link": "asset_human_resource",
                                             "joinby": "asset_id",
                                             "key": "human_resource_id",
                                             "actuate": "hide",
                                             },
                       vehicle_gps = "asset_id",
                       vehicle_vehicle = {"joinby": "asset_id",
                                          "multiple": False,
                                          },
                       )

        # =====================================================================
        # Asset Items
        # - to allow building ad-hoc Kits
        #
        tablename = "asset_item"
        define_table(tablename,
                     item_entity_id(),
                     asset_id(ondelete = "CASCADE"),
                     item_id(represent = supply_item_represent,
                             requires = IS_ONE_OF(db, "supply_item.id",
                                                  supply_item_represent,
                                                  filterby = "item_category_id",
                                                  filter_opts = asset_category_ids,
                                                  sort = True,
                                                  ),
                             script = None, # No Item Pack Filter
                             widget = None,
                             ),
                     Field("quantity", "integer", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           requires = IS_INT_IN_RANGE(1, None),
                           ),
                     Field("sn",
                           label = T("Serial Number"),
                           ),
                     organisation_id("supply_org_id",
                                     label = T("Supplier/Donor"),
                                     ondelete = "SET NULL",
                                     ),
                     s3_date("purchase_date",
                             label = T("Purchase Date"),
                             ),
                     Field("purchase_price", "double",
                           #default = 0.00,
                           represent = float_represent,
                           ),
                     s3_currency("purchase_currency"),
                     # Base Location, which should always be a Site & set via Log
                     location_id(readable = False,
                                 writable = False,
                                 ),
                     s3_comments(comment = None),
                     *s3_meta_fields())

        # =====================================================================
        # Asset Log
        #
        asset_log_status_opts = {ASSET_LOG_SET_BASE : T("Base %(facility)s Set") % {"facility": org_site_label},
                                 ASSET_LOG_ASSIGN   : T("Assigned"),
                                 ASSET_LOG_RETURN   : T("Returned"),
                                 ASSET_LOG_CHECK    : T("Checked"),
                                 ASSET_LOG_REPAIR   : T("Repaired"),
                                 ASSET_LOG_DONATED  : T("Donated"),
                                 ASSET_LOG_LOST     : T("Lost"),
                                 ASSET_LOG_STOLEN   : T("Stolen"),
                                 ASSET_LOG_DESTROY  : T("Destroyed"),
                                 }

        if auth.permission.format == "html":
            # T isn't JSON serializable
            site_types = {}
            for key in list(org_site_types.keys()):
                site_types[key] = s3_str(org_site_types[key])
            site_types = json.dumps(site_types)
            script = '''
$.filterOptionsS3({
 'trigger':'organisation_id',
 'target':'site_id',
 'lookupPrefix':'org',
 'lookupResource':'site',
 'lookupField':'site_id',
 'fncRepresent': function(record,PrepResult){
  var InstanceTypeNice=%(instance_type_nice)s
  return record.name+" ("+InstanceTypeNice[record.instance_type]+")"
}})''' % {"instance_type_nice": site_types}
        else:
            script = None

        tablename = "asset_log"
        define_table(tablename,
                     asset_id(),
                     Field("status", "integer",
                           label = T("Status"),
                           represent = s3_options_represent(asset_log_status_opts),
                           requires = IS_IN_SET(asset_log_status_opts),
                           ),
                     s3_datetime(default = "now",
                                 empty = False,
                                 represent = "date",
                                 ),
                     s3_datetime("date_until",
                                 label = T("Date Until"),
                                 represent = "date",
                                 ),
                     person_id(label = T("Assigned To")),
                     Field("check_in_to_person", "boolean",
                           label = T("Track with this Person?"),

                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Track with this Person?"),
                                                             T("If selected, then this Asset's Location will be updated whenever the Person's Location is updated."),
                                                             ),
                                         ),
                           readable = False,
                           writable = False,
                           ),
                     # The Organisation to whom the loan is made
                     organisation_id(readable = False,
                                     widget = None,
                                     writable = False,
                                     ),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("site_id", "org_site",
                                #default = user.site_id if LOGGED_IN else None,
                                empty = False,
                                label = org_site_label,
                                #filterby = "site_id",
                                #filter_opts = auth.permitted_facilities(redirect_on_error=False),
                                instance_types = org_site_types,
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                represent = self.org_site_represent,
                                readable = True,
                                writable = True,
                                script = script,
                                updateable = True,
                                #widget = S3SiteAutocompleteWidget(),
                                ),
                     self.org_site_layout_id(# This has the URL adjusted for the right site_id by s3.asset_log.js
                                             comment = S3PopupLink(c = "org",
                                                                   f = "site",
                                                                   args = ["[id]", "layout", "create"],
                                                                   vars = {"prefix": "asset",
                                                                           "parent": "log",
                                                                           "child": "layout_id",
                                                                           },
                                                                   label = T("Create Location"),
                                                                   _id = "asset_log_layout_id-create-btn",
                                                                   ),
                                             ),
                     Field("cancel", "boolean",
                           default = False,
                           label = T("Cancel Log Entry"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Cancel Log Entry"),
                                                             T("'Cancel' will indicate an asset log entry did not occur"),
                                                             ),
                                         ),
                           ),
                     Field("cond", "integer",  # condition is a MySQL reserved word
                           label = T("Condition"),
                           represent = s3_options_represent(asset_condition_opts),
                           requires = IS_IN_SET(asset_condition_opts,
                                                zero = "%s..." % T("Please select")),
                           ),
                     person_id("by_person_id",
                               default = auth.s3_logged_in_person(),   # This can either be the Asset controller if signed-out from the store
                               label = T("Assigned By"),               # or the previous owner if passed on directly (e.g. to successor in their post)
                               comment = self.pr_person_comment(child = "by_person_id"),
                               ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("New Entry in Asset Log"),
            title_display = T("Asset Log Details"),
            title_list = T("Asset Log"),
            title_update = T("Edit Asset Log Entry"),
            label_list_button = T("Asset Log"),
            label_delete_button = T("Delete Asset Log Entry"),
            msg_record_created = T("Entry added to Asset Log"),
            msg_record_modified = T("Asset Log Entry updated"),
            msg_record_deleted = T("Asset Log Entry deleted"),
            msg_list_empty = T("Asset Log Empty"),
            )

        # Resource configuration
        configure(tablename,
                  listadd = False,
                  list_fields = ["date",
                                 "status",
                                 "date_until",
                                 "organisation_id",
                                 "site_id",
                                 "layout_id",
                                 "person_id",
                                 #"location_id",
                                 "cancel",
                                 "cond",
                                 "comments",
                                 ],
                  onaccept = self.asset_log_onaccept,
                  orderby = "asset_log.date desc",
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"asset_asset_id": asset_id,
                "asset_represent": asset_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        return {"asset_asset_id": S3ReusableField.dummy("asset_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_onaccept(form):
        """
            After DB I/O
        """

        if current.response.s3.bulk:
            # Import or Sync
            return

        db = current.db
        atable = db.asset_asset

        form_vars_get = form.vars.get
        asset_id = form_vars_get("id")
        kit = form_vars_get("kit")
        organisation_id = form_vars_get("organisation_id")
        site_id = form_vars_get("site_id")

        if not organisation_id or not site_id:
            # Component Tab: load record to read
            asset = db(atable.id == asset_id).select(atable.organisation_id,
                                                     atable.site_id,
                                                     limitby = (0, 1),
                                                     ).first()
            organisation_id = asset.organisation_id
            site_id = asset.site_id

        record = form.record
        if record:
            old_site_id = record.site_id
        else:
            old_site_id = None

        if site_id and \
           site_id != old_site_id:
            # Set the Base Location
            stable = db.org_site
            site = db(stable.site_id == site_id).select(stable.location_id,
                                                        limitby = (0, 1),
                                                        ).first()
            location_id = site.location_id
            tracker = S3Tracker()
            asset_tracker = tracker(atable, asset_id)
            asset_tracker.set_base_location(location_id)
            if kit:
                # Also populate location_id field in component items
                aitable = db.asset_item
                db(aitable.asset_id == asset_id).update(location_id = location_id)

            # Add a log entry for this
            ltable = db.asset_log
            ltable.insert(asset_id = asset_id,
                          status = ASSET_LOG_SET_BASE,
                          organisation_id = organisation_id,
                          site_id = site_id,
                          cond = 1,
                          )

        if kit:
            # Empty any inappropriate fields
            db(atable.id == asset_id).update(supplier_org_id = None,
                                             purchase_date = None,
                                             purchase_price = None,
                                             purchase_currency = None,
                                             )
        else:
            # Delete any component items
            aitable = db.asset_item
            ids = db(aitable.asset_id == asset_id).select(aitable.id).as_list()
            if ids:
                resource = current.s3db.resource("asset_item",
                                                 id = ids,
                                                 )
                resource.delete()

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_log_onaccept(form):
        """
            After DB I/O
        """

        # Custom methods to allow form customization for specific cases
        # Original method passed from asset_log_prep()
        method = current.response.s3.asset_log_method
        if method == "setbase":
            status = ASSET_LOG_SET_BASE
        elif method in ("assignperson", "assignsite", "assignorg"):
            status = ASSET_LOG_ASSIGN
        else:
            status = None

        if not status:
            if not current.response.s3.asset_import:
                # e.g. Record merger or Sync
                return
            # Import
            db = current.db
            form_vars = form.vars
            asset_id = form_vars.asset_id
            status = int(form_vars.status)
            new = True
        else:
            # Interactive
            form_vars = form.vars
            status = int(form_vars.status or status)

            db = current.db
            ltable = db.asset_log
            row = db(ltable.id == form_vars.id).select(ltable.asset_id,
                                                       limitby = (0, 1),
                                                       ).first()
            try:
                asset_id = row.asset_id
            except:
                return

            current_log = asset_get_current_log(asset_id)

            log_time = current_log.date
            current_time = form_vars.get("date").replace(tzinfo = None)
            new = log_time <= current_time

        if new:
            # This is a current assignment
            atable = db.asset_asset
            aitable = db.asset_item
            tracker = S3Tracker()
            asset_tracker = tracker(atable, asset_id)

            if status == ASSET_LOG_SET_BASE:
                # Set Base Location
                site_id = form_vars.get("site_id")
                stable = db.org_site
                site = db(stable.site_id == site_id).select(stable.location_id,
                                                            limitby = (0, 1),
                                                            ).first()
                location_id = site.location_id
                asset_tracker.set_base_location(location_id)
                # Also do component items
                db(aitable.asset_id == asset_id).update(location_id = location_id)

            elif status == ASSET_LOG_ASSIGN:
                if method == "assignsite":
                    asset_tracker.check_in(db.org_site, form_vars.site_id,
                                           timestmp = current.request.utcnow)
                    # Also do component items
                    locations = asset_tracker.get_location(_fields = [db.gis_location.id])
                    try:
                        db(aitable.asset_id == asset_id).update(location_id = locations[0].id)
                    except:
                        pass

                elif method == "assignorg":
                    site_id = form_vars.get("site_id")
                    if site_id:
                        asset_tracker.check_in(db.org_site, site_id,
                                               timestmp = current.request.utcnow)
                        # Also do component items
                        locations = asset_tracker.get_location(_fields = [db.gis_location.id])
                        try:
                            db(aitable.asset_id == asset_id).update(location_id = locations[0].id)
                        except:
                            pass
                    else:
                        # We can no longer track location
                        asset_tracker.check_out()

                else:
                    if form_vars.check_in_to_person:
                        asset_tracker.check_in(db.pr_person, form_vars.person_id,
                                               timestmp = current.request.utcnow)
                        # Also do component items
                        # @ToDo: Have these move when the person moves
                        locations = asset_tracker.get_location(_fields = [db.gis_location.id])
                        try:
                            db(aitable.asset_id == asset_id).update(location_id = locations[0].id)
                        except:
                            pass
                    else:
                        location_id = asset_tracker.set_location(form_vars.person_id,
                                                                 timestmp = current.request.utcnow)
                        # Also do component items
                        db(aitable.asset_id == asset_id).update(location_id = location_id)
                    # Update main record for component
                    db(atable.id == asset_id).update(assigned_to_id = form_vars.person_id)

            elif status == ASSET_LOG_RETURN:
                # Set location to base location
                location_id = asset_tracker.set_location(asset_tracker,
                                                         timestmp = current.request.utcnow)
                # Also do component items
                db(aitable.asset_id == asset_id).update(location_id = location_id)

            # Update condition in main record
            db(atable.id == asset_id).update(cond = form_vars.cond)

# =============================================================================
#class AssetHRModel(S3Model):
#    """
#        Optionally link Assets to Human Resources
#        - useful for staffing a vehicle
#    """

#    names = ("asset_human_resource",)

#    def model(self):

#        #T = current.T

#        # ---------------------------------------------------------------------
#        # Assets <> Human Resources
#        #
#        tablename = "asset_human_resource"
#        self.define_table(tablename,
#                          self.asset_asset_id(empty = False),
#                          self.hrm_human_resource_id(empty = False,
#                                                     ondelete = "CASCADE",
#                                                     ),
#                          #s3_comments(),
#                          *s3_meta_fields())

#        # ---------------------------------------------------------------------
#        # Pass names back to global scope (s3.*)
#        #
#        return None

# =============================================================================
#class AssetTeamModel(S3Model):
#    """
#        Optionally link Assets to Teams
#    """

#    names = ("asset_group",)

#    def model(self):

#        #T = current.T

#        # ---------------------------------------------------------------------
#        # Assets <> Groups
#        #
#        tablename = "asset_group"
#        self.define_table(tablename,
#                          self.asset_asset_id(empty = False),
#                          self.pr_group_id(comment = None,
#                                           empty = False,
#                                           ),
#                          #s3_comments(),
#                          *s3_meta_fields())

#        # ---------------------------------------------------------------------
#        # Pass names back to global scope (s3.*)
#        #
#        return None

# =============================================================================
class AssetTelephoneModel(S3Model):
    """
        Extend the Assset Module for Telephones:
            Usage Costs
    """

    names = ("asset_telephone",
             "asset_telephone_usage",
             )

    def model(self):

        T = current.T

        #--------------------------------------------------------------------------
        # Asset Telephones
        #
        tablename = "asset_telephone"
        self.define_table(tablename,
                          self.asset_asset_id(empty = False),
                          # @ToDo: Filter to Suppliers
                          self.org_organisation_id(label = T("Airtime Provider")),
                          # We'll need something more complex here as there may be a per-month cost with bundled units
                          #Field("unit_cost", "double",
                          #      label = T("Unit Cost"),
                          #      ),
                          s3_comments(),
                          *s3_meta_fields())

        #--------------------------------------------------------------------------
        # Telephone Usage Costs
        #
        # @ToDo: Virtual Fields for Month/Year for Reporting
        #
        tablename = "asset_telephone_usage"
        self.define_table(tablename,
                          self.asset_asset_id(empty = False),
                          s3_date(label = T("Start Date")),
                          # @ToDo: Validation to ensure not before Start Date
                          s3_date("end_date",
                                  label = T("End Date"),
                                  start_field = "asset_telephone_usage_date",
                                  default_interval = 1,
                                  ),
                          Field("units_used", "double", # 'usage' is a reserved word in MySQL
                                label = T("Usage"),
                                ),
                          # mins, Mb (for BGANs)
                          #Field("unit",
                          #      label = T("Usage"),
                          #      ),
                          # @ToDo: Calculate this from asset_telephone fields
                          #Field("cost", "double",
                          #      label = T("Cost"),
                          #      ),
                          #s3_currency(),
                          s3_comments(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

# =============================================================================
def asset_get_current_log(asset_id):
    """
        Get the current log entry for this asset
    """

    table = current.s3db.asset_log
    query = (table.asset_id == asset_id) & \
            (table.cancel == False)
    # Get the log with the maximum time
    asset_log = current.db(query).select(table.id,
                                         table.status,
                                         table.date,
                                         table.cond,
                                         table.person_id,
                                         table.organisation_id,
                                         table.site_id,
                                         #table.location_id,
                                         limitby = (0, 1),
                                         orderby = ~table.date,
                                         ).first()
    if asset_log:
        return Storage(date = asset_log.date,
                       person_id = asset_log.person_id,
                       cond = int(asset_log.cond or 0),
                       status = int(asset_log.status or 0),
                       organisation_id = asset_log.organisation_id,
                       site_id = asset_log.site_id,
                       #location_id = asset_log.location_id
                       )
    else:
        return Storage()

# =============================================================================
def asset_log_prep(r):
    """
        Called by Controller
    """

    T = current.T
    db = current.db

    table = db.asset_log

    # Custom methods to allow form customization for specific cases
    method = r.method
    # Pass method via response.s3.asset_log_method to asset_log_onaccept()
    current.response.s3.asset_log_method = method

    if method == "update":
        # Can only Cancel entry
        for f in table.fields:
            if f == "cancel":
                continue
            else:
                table[f].writable = False
        return
    elif method == "read":
        return

    # This causes an error with the dataTables paginate
    # if used only in r.interactive & not also r.representation=="aadata"
    table.cancel.readable = table.cancel.writable = False

    current_log = asset_get_current_log(r.id)

    if method == "setbase":
        status = ASSET_LOG_SET_BASE
        r.method = "create"
    elif method in ("assignperson", "assignsite", "assignorg"):
        status = ASSET_LOG_ASSIGN
        r.method = "create"
    elif method == "return":
        status = ASSET_LOG_RETURN
        r.method = "create"
    else:
        status = 0

    if status:
        field = table.status
        field.default = status
        field.readable = field.writable = False
    elif current_log:
        table.status.default = current_log.status

    crud_strings = current.response.s3.crud_strings.asset_log

    if status == ASSET_LOG_SET_BASE:
        crud_strings.msg_record_created = T("Base Facility/Site Set")
        table.by_person_id.label = T("Set By")
        table.date_until.readable = table.date_until.writable = False
        table.person_id.readable = table.person_id.writable = False
        table.organisation_id.readable = table.organisation_id.writable = True
        # Start Empty
        table.layout_id.widget.filter = (FS("site_id") == 0)

    elif status == ASSET_LOG_RETURN:
        crud_strings.msg_record_created = T("Returned")
        table.date_until.readable = table.date_until.writable = False
        table.person_id.readable = table.person_id.writable = False
        table.by_person_id.default = current_log.person_id
        table.by_person_id.label = T("Returned By")
        #table.organisation_id.default = current_log.organisation_id
        #table.site_id.default = current_log.site_id
        table.site_id.readable = table.site_id.writable = False
        table.layout_id.readable = table.layout_id.writable = False

    elif status == ASSET_LOG_ASSIGN:
        if method == "assignperson":
            crud_strings.msg_record_created = T("Assigned to Person")
            table.person_id.requires = table.person_id.requires.other
            table.check_in_to_person.readable = table.check_in_to_person.writable = True
            table.site_id.requires = IS_EMPTY_OR(table.site_id.requires)
            # Start Empty
            table.layout_id.widget.filter = (FS("site_id") == 0)

        elif method == "assignsite":
            crud_strings.msg_record_created = T("Assigned to Facility/Site")
            # Start Empty
            table.layout_id.widget.filter = (FS("site_id") == 0)

        elif method == "assignorg":
            crud_strings.msg_record_created = T("Assigned to Organization")
            field = table.organisation_id
            field.readable = field.writable = True
            field.requires = field.requires.other
            table.site_id.requires = IS_EMPTY_OR(table.site_id.requires)
            # Start Empty
            table.layout_id.widget.filter = (FS("site_id") == 0)
    else:
        # Can Update Status &/or Condition
        crud_strings.msg_record_created = T("Status Updated")
        table.by_person_id.label = T("Updated By")
        table.date_until.readable = table.date_until.writable = False
        table.person_id.readable = table.person_id.writable = False
        table.site_id.readable = table.site_id.writable = False
        table.layout_id.readable = table.layout_id.writable = False
        field = table.status
        field.readable = field.writable = True
        field.requires = IS_IN_SET({ASSET_LOG_CHECK    : T("Check"),
                                    ASSET_LOG_REPAIR   : T("Repair"),
                                    ASSET_LOG_DONATED  : T("Donated"),
                                    ASSET_LOG_LOST     : T("Lost"),
                                    ASSET_LOG_STOLEN   : T("Stolen"),
                                    ASSET_LOG_DESTROY  : T("Destroyed"),
                                    })

# =============================================================================
def asset_rheader(r):
    """ Resource Header for Assets """

    if r.representation == "html":
        record = r.record
        if record:

            T = current.T
            s3db = current.s3db
            s3 = current.response.s3

            if record.type == ASSET_TYPE_TELEPHONE:
                tabs = [(T("Asset Details"), None, {"native": True}),
                        (T("Telephone Details"), "telephone"),
                        (T("Usage"), "telephone_usage"),
                        ]

            #elif record.type == s3.asset.ASSET_TYPE_RADIO:
            #    tabs.append((T("Radio Details"), "radio"))

            elif record.type == ASSET_TYPE_VEHICLE:
                STAFF = current.deployment_settings.get_hrm_staff_label()
                tabs = [(T("Asset Details"), None, {"native": True}),
                        (T("Vehicle Details"), "vehicle"),
                        (STAFF, "human_resource"),
                        (T("Assign %(staff)s") % {"staff": STAFF}, "assign"),
                        (T("Check-In"), "check-in"),
                        (T("Check-Out"), "check-out"),
                        (T("GPS Data"), "presence"),
                        ]
            else:
                # Generic Asset
                tabs = [(T("Edit Details"), None)]

            tabs += [(T("Log"), "log"),
                     (T("Documents"), "document"),
                     ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            asset_id = record.id
            current_log = asset_get_current_log(asset_id)
            status = current_log.status

            table = r.table
            ltable = s3db.asset_log
            rheader = DIV(TABLE(TR(TH("%s: " % table.number.label),
                                   record.number,
                                   TH("%s: " % table.item_id.label),
                                   table.item_id.represent(record.item_id)
                                   ),
                                TR(TH("%s: " % ltable.cond.label),
                                   ltable.cond.represent(current_log.cond),
                                   TH("%s: " % ltable.status.label),
                                   ltable.status.represent(status),
                                   ),
                                TR(TH("%s: " % ltable.person_id.label),
                                   ltable.person_id.represent(current_log.person_id),
                                   TH("%s: " % ltable.site_id.label),
                                   ltable.site_id.represent(current_log.site_id),
                                   ),
                                ),
                          rheader_tabs,
                          )

            # RFooter Buttons
            # @ToDo: Check permissions before displaying buttons

            if r.controller == "vehicle":
                func = "vehicle"
            else:
                func = "asset"

            asset_action_btns = [A(T("Set Base Facility/Site"),
                                   _href = URL(f=func,
                                               args = [asset_id, "log", "setbase"],
                                               ),
                                   _class = "action-btn",
                                   ),
                                 ]

            #if record.location_id:
            # A Base Site has been set
            # Return functionality removed  - as it doesn't set site_id & organisation_id in the logs
            if status == ASSET_LOG_ASSIGN:
                asset_action_btns.append(A(T("Return"),
                                           _href = URL(f=func,
                                                       args = [asset_id, "log", "return"],
                                                       ),
                                           _class = "action-btn",
                                           ))

            if status < ASSET_LOG_DONATED:
                # The Asset is available for assignment (not disposed)
                # @ToDo: deployment setting to prevent assigning assets before returning them
                asset_action_btns += [A(T("Assign to Person"),
                                        _href = URL(f=func,
                                                    args = [asset_id, "log", "assignperson"],
                                                    ),
                                        _class = "action-btn",
                                        ),
                                      A(T("Assign to Facility/Site"),
                                        _href = URL(f=func,
                                                    args = [asset_id, "log", "assignsite"],
                                                    ),
                                        _class = "action-btn",
                                        ),
                                      A(T("Assign to Organization"),
                                        _href = URL(f=func,
                                                    args = [asset_id, "log", "assignorg"],
                                                    ),
                                        _class = "action-btn",
                                        ),
                                      ]

            asset_action_btns.append(A(T("Update Status"),
                                       _href = URL(f=func,
                                                   args = [asset_id, "log", "create"],
                                                   ),
                                       _class = "action-btn",
                                       ))

            s3.rfooter = TAG[""](*asset_action_btns)

            return rheader
    return None

# =============================================================================
def asset_controller():
    """ RESTful CRUD controller """

    s3 = current.response.s3

    # Pre-process
    def prep(r):
        # Location Filter
        from .gis import gis_location_filter
        gis_location_filter(r)

        if r.component_name == "log":
            asset_log_prep(r)
        else:
            item_id = r.get_vars.get("item_id")
            if item_id:
                # e.g. coming from Incident Action Plan
                f  = r.table.item_id
                f.default = item_id
                f.writable = False
                f.comment = False

        return True
    s3.prep = prep

    # Import pre-process
    def import_prep(tree):
        # Flag that this is an Import (to distinguish from Sync)
        current.response.s3.asset_import = True

    s3.import_prep = import_prep

    # Post-processor
    def postp(r, output):
        if r.interactive and r.method != "import":
            if r.component_name == "log":
                script = "/%s/static/scripts/S3/s3.asset_log.js" % r.application
                s3.scripts.append(script)
            else:
                script = "/%s/static/scripts/S3/s3.asset.js" % r.application
                s3.scripts.append(script)
            s3_action_buttons(r, deletable=False)
        return output
    s3.postp = postp

    output = current.rest_controller("asset", "asset",
                                     rheader = asset_rheader,
                                     )
    return output

# =============================================================================
class asset_AssetRepresent(S3Represent):
    """ Representation of Assets """

    def __init__(self,
                 fields = ("number",), # unused
                 show_link = False,
                 translate = False,
                 multiple = False,
                 ):

        super(asset_AssetRepresent,
              self).__init__(lookup = "asset_asset",
                             fields = fields,
                             show_link = show_link,
                             translate = translate,
                             multiple = multiple,
                             )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for organisation rows, does a
            left join with the parent organisation. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            Args:
                values: the organisation IDs
        """

        db = current.db
        s3db = current.s3db
        table = s3db.asset_asset
        itable = db.supply_item
        btable = db.supply_brand

        qty = len(values)
        if qty == 1:
            query = (table.id == values[0])
            limitby = (0, 1)
        else:
            query = (table.id.belongs(values))
            limitby = (0, qty)

        query &= (itable.id == table.item_id)

        rows = db(query).select(table.id,
                                table.number,
                                table.type,
                                itable.name,
                                btable.name,
                                left = btable.on(itable.brand_id == btable.id),
                                limitby = limitby,
                                )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            Args:
                row: the asset_asset Row
        """

        # Custom Row (with the item & brand left-joined)
        number = row["asset_asset.number"]
        item = row["supply_item.name"]
        brand = row.get("supply_brand.name", None)

        if not number:
            return self.default
        represent = "%s (%s" % (number, item)
        if brand:
            represent = "%s, %s)" % (represent, brand)
        else:
            represent = "%s)" % represent
        return s3_str(represent)

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            Args:
                k: the key (site_id)
                v: the representation of the key
                row: the row with this key
        """

        if row:
            atype = row.get("asset_asset.type", None)
            if atype == 1:
                return A(v,
                         _href = URL(c="vehicle", f="vehicle",
                                     args = [k],
                                     # remove the .aaData extension in paginated views
                                     extension = ""
                                     ),
                         )
        k = s3_str(k)
        return A(v,
                 _href = self.linkto.replace("[id]", k) \
                                    .replace("%5Bid%5D", k),
                 )

# END =========================================================================
