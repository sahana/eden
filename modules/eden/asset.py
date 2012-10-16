# -*- coding: utf-8 -*-

""" Sahana Eden Assets Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3AssetModel",
           "asset_rheader",
           "asset_types",
           "asset_log_status",
           "asset_controller",
           ]

from gluon import *
from gluon.sqlhtml import RadioWidget
from gluon.storage import Storage

from ..s3 import *
from layouts import S3AddResourceLink

ASSET_TYPE_VEHICLE   = 1   # => Extra Tab(s) for Registration Documents, Fuel Efficiency
ASSET_TYPE_RADIO     = 2   # => Extra Tab(s) for Radio Channels/Frequencies
ASSET_TYPE_TELEPHONE = 3   # => Extra Tab(s) for Contact Details & Airtime Billing
ASSET_TYPE_OTHER     = 4   # => No extra Tabs

# To pass to global scope
asset_types = {
                "VEHICLE"    : ASSET_TYPE_VEHICLE,
                "RADIO"      : ASSET_TYPE_RADIO,
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
asset_log_status = {
                "SET_BASE" : ASSET_LOG_SET_BASE,
                "ASSIGN"   : ASSET_LOG_ASSIGN,
                "RETURN"   : ASSET_LOG_RETURN,
                "CHECK"    : ASSET_LOG_CHECK,
                "REPAIR"   : ASSET_LOG_REPAIR,
                "DONATED"  : ASSET_LOG_DONATED,
                "LOST"     : ASSET_LOG_LOST,
                "STOLEN"   : ASSET_LOG_STOLEN,
                "DESTROY"  : ASSET_LOG_DESTROY,
               }

#SITE = 1
#LOCATION = 2

# =============================================================================
class S3AssetModel(S3Model):
    """
        Asset Management
    """

    names = ["asset_asset",
             "asset_log",
             "asset_log_prep",
             "asset_asset_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        settings = current.deployment_settings
        org_site_label = settings.get_org_site_label()
        vehicle = settings.has_module("vehicle")

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        #--------------------------------------------------------------------------
        # Assets
        #

        asset_type_opts = { ASSET_TYPE_VEHICLE    : T("Vehicle"),
                            #ASSET_TYPE_RADIO      : T("Radio"),
                            #ASSET_TYPE_TELEPHONE  : T("Telephone"),
                            ASSET_TYPE_OTHER      : T("Other")
                           }

        asset_item_represent = lambda id: \
            self.supply_item_represent(id, show_um = False)

        ctable = self.supply_item_category
        itable = self.supply_item

        tablename = "asset_asset"
        table = define_table(tablename,
                             super_link("track_id", "sit_trackable"),
                             super_link("doc_id", "doc_entity"),
                             Field("number",
                                   label = T("Asset Number")),
                             self.supply_item_entity_id,
                             # @ToDo: Can we set this automatically based on Item Category?
                             Field("type", "integer",
                                   readable = vehicle,
                                   writable = vehicle,
                                   requires = IS_IN_SET(asset_type_opts),
                                   default = ASSET_TYPE_OTHER,
                                   represent = lambda opt: \
                                       asset_type_opts.get(opt, UNKNOWN_OPT),
                                   label = T("Type")),
                             self.supply_item_id(represent = asset_item_represent,
                                                 requires = IS_ONE_OF(db((ctable.can_be_asset == True) & \
                                                                         (itable.item_category_id == ctable.id)),
                                                                      "supply_item.id",
                                                                      asset_item_represent,
                                                                      sort=True,
                                                                      ),
                                                 widget = None,
                                                 script = None, # No Item Pack Filter
                                                 ),
                             organisation_id(required = True,
                                             script = SCRIPT('''
$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'organisation_id',
  'Field':'site_id',
  'FieldResource':'site',
  'FieldPrefix':'org',
  'FieldID':'site_id'
 })
})'''),),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("site_id", "org_site",
                                        label = org_site_label,
                                        default = auth.user.site_id if auth.is_logged_in() else None,
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        ondelete = "RESTRICT",
                                        # Comment these to use a Dropdown & not an Autocomplete
                                        #widget = S3SiteAutocompleteWidget(),
                                        #comment = DIV(_class="tooltip",
                                        #              _title="%s|%s" % (T("Warehouse"),
                                        #                                T("Enter some characters to bring up a list of possible matches"))),
                                        represent = self.org_site_represent
                                        ),
                             Field("sn",
                                   label = T("Serial Number")),
                             organisation_id("supply_org_id",
                                             label = T("Supplier/Donor"),
                                             ondelete = "SET NULL"),
                             s3_date("purchase_date",
                                     label = T("Purchase Date")
                                     ),
                             Field("purchase_price", "double",
                                   #default=0.00,
                                   represent=lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             s3_currency("purchase_currency"),
                             # Base Location, which should always be a Site & set via Log
                             location_id(readable=False,
                                         writable=False),
                             # Populated onaccept of the log to make a component tab
                             person_id("assigned_to_id",
                                       readable=False,
                                       writable=False,
                                       comment=self.pr_person_comment(child="assigned_to_id")),
                             s3_comments(),
                             *(s3_address_fields() + s3_meta_fields()))

        # CRUD strings
        ADD_ASSET = T("Add Asset")
        crud_strings[tablename] = Storage(
            title_create = ADD_ASSET,
            title_display = T("Asset Details"),
            title_list =  T("Assets"),
            title_update = T("Edit Asset"),
            title_search = T("Search Assets"),
            title_upload = T("Import Assets"),
            subtitle_create = T("Add New Asset"),
            label_list_button =  T("List Assets"),
            label_create_button = ADD_ASSET,
            label_delete_button = T("Delete Asset"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset deleted"),
            msg_list_empty = T("No Assets currently registered"))

        # Reusable Field
        asset_id = S3ReusableField("asset_id", table,
                                   sortby="number",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db,
                                                          "asset_asset.id",
                                                          self.asset_represent,
                                                          sort=True)),
                                   represent = self.asset_represent,
                                   label = T("Asset"),
                                   comment = S3AddResourceLink(c="asset", f="asset",
                                    tooltip=T("If you don't see the asset in the list, you can add a new one by clicking link 'Add Asset'.")),
                                   ondelete = "CASCADE")

        table.virtualfields.append(AssetVirtualFields())

        # Search Method
        asset_search = S3Search(
            # Advanced Search only
            advanced=(
                    S3SearchSimpleWidget(
                        name="asset_search_text",
                        label=T("Search"),
                        comment=T("You can search by asset number, item description or comments. You may use % as wildcard. Press 'Search' without input to list all assets."),
                        field=[
                                "number",
                                "item_id$name",
                                #"item_id$category_id$name",
                                "comments",
                            ]
                      ),
                    S3SearchOptionsWidget(
                        name="asset_search_L1",
                        field="L1",
                        location_level="L1",
                        cols = 3
                    ),
                    S3SearchOptionsWidget(
                        name="asset_search_L2",
                        field="L2",
                        location_level="L2",
                        cols = 3
                    ),
                    S3SearchLocationWidget(
                        name="asset_search_map",
                        label=T("Map"),
                    ),
                    S3SearchOptionsWidget(
                        name="asset_search_item_category",
                        field="item_id$item_category_id",
                        label=T("Category"),
                        cols = 3
                    ),
            ))

        report_fields = [
                         "number",
                         (T("Category"), "item_id$item_category_id"),
                         (T("Item"), "item_id"),
                         (org_site_label, "site"),
                         "L1",
                         "L2",
                         ]

        # Resource Configuration
        configure(tablename,
                  super_entity = ("supply_item_entity", "sit_trackable"),
                  mark_required = ["organisation_id"],
                  create_next = URL(c="asset", f="asset",
                                    args=["[id]"]),
                  onaccept=self.asset_onaccept,
                  search_method=asset_search,
                  report_options=Storage(
                        search=[
                                S3SearchOptionsWidget(
                                    name="asset_search_L1",
                                    field="L1",
                                    location_level="L1",
                                    cols = 3
                                ),
                                S3SearchOptionsWidget(
                                    name="asset_search_L2",
                                    field="L2",
                                    location_level="L2",
                                    cols = 3
                                ),
                                S3SearchOptionsWidget(
                                    name="asset_search_item_category",
                                    field="item_id$item_category_id",
                                    label=T("Category"),
                                    cols = 3
                                ),
                            ],
                        rows=report_fields,
                        cols=report_fields,
                        facts=report_fields,
                        methods=["count", "list"],
                        defaults=Storage(
                                aggregate="count",
                                cols="asset.L1",
                                fact="asset.number",
                                rows="asset.item_id$item_category_id"
                            )
                        ),
                  list_fields=["id",
                               "number",
                               "item_id$item_category_id",
                               "item_id",
                               "type",
                               "purchase_date",
                               "organisation_id",
                               "site_id",
                               #"location_id",
                               "L0",
                               "L1",
                               #"L2",
                               #"L3",
                               "comments",
                               ],
                  realm_components = ["log", "presence"],
                  update_realm = True,
                )

        # Log as component of Assets
        add_component("asset_log", asset_asset="asset_id")

        # Vehicles as component of Assets
        add_component("vehicle_vehicle",
                      asset_asset=dict(joinby="asset_id",
                                       multiple=False))

        # GPS as a component of Assets
        add_component("vehicle_gps", asset_asset="asset_id")

        # =====================================================================
        # Asset Log
        #

        asset_log_status_opts = {ASSET_LOG_SET_BASE : T("Base %(facility)s Set") % dict(facility = org_site_label),
                                 ASSET_LOG_ASSIGN   : T("Assigned"),
                                 ASSET_LOG_RETURN   : T("Returned"),
                                 ASSET_LOG_CHECK    : T("Checked"),
                                 ASSET_LOG_REPAIR   : T("Repaired"),
                                 ASSET_LOG_DONATED  : T("Donated"),
                                 ASSET_LOG_LOST     : T("Lost"),
                                 ASSET_LOG_STOLEN   : T("Stolen"),
                                 ASSET_LOG_DESTROY  : T("Destroyed"),
                                 }
        #site_or_location_opts = {SITE     :T("Site"),
        #                         LOCATION :T("Location")}

        asset_condition_opts = {
                                1:T("Good Condition"),
                                2:T("Minor Damage"),
                                3:T("Major Damage"),
                                4:T("Un-Repairable"),
                                5:T("Needs Maintenance"),
                               }

        tablename = "asset_log"
        table = define_table(tablename,
                             asset_id(),
                             Field("status", "integer",
                                   label = T("Status"),
                                   requires = IS_IN_SET(asset_log_status_opts),
                                   represent = lambda opt: \
                                       asset_log_status_opts.get(opt, UNKNOWN_OPT)
                                   ),
                             s3_datetime("datetime",
                                         default="now",
                                         empty=False,
                                         represent="date",
                                         ),
                             s3_datetime("datetime_until",
                                         label = T("Date Until"),
                                         represent="date",
                                         ),
                             person_id(label = T("Assigned To")),
                             Field("check_in_to_person", "boolean",
                                   #label = T("Mobile"),      # Relabel?
                                   label = T("Track with this Person?"),
                                   comment = DIV(_class="tooltip",
                                                 #_title="%s|%s" % (T("Mobile"),
                                                 _title="%s|%s" % (T("Track with this Person?"),
                                                                   T("If selected, then this Asset's Location will be updated whenever the Person's Location is updated."))),
                                   readable = False,
                                   writable = False),
                             # The Organisation to whom the loan is made
                             organisation_id(
                                    readable = False,
                                    writable = False,
                                    widget = None
                                    ),
                             #Field("site_or_location",
                             #      "integer",
                             #      requires = IS_NULL_OR(IS_IN_SET(site_or_location_opts)),
                             #      represent = lambda opt: \
                             #          site_or_location_opts.get(opt, UNKNOWN_OPT),
                             #      widget = RadioWidget.widget,
                             #      label = T("Facility or Location")),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("site_id", "org_site",
                                        label = org_site_label,
                                        #filterby = "site_id",
                                        #filter_opts = auth.permitted_facilities(redirect_on_error=False),
                                        instance_types = auth.org_site_types,
                                        updateable = True,
                                        not_filterby = "obsolete",
                                        not_filter_opts = [True],
                                        #default = user.site_id if is_logged_in() else None,
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        represent = self.org_site_represent,
                                        #widget = S3SiteAutocompleteWidget(),
                                        comment = SCRIPT(
'''$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'organisation_id',
  'Field':'site_id',
  'FieldPrefix':'org',
  'FieldResource':'site',
  'FieldID':'site_id',
  'fncRepresent': function(record, PrepResult) {
                      var InstanceTypeNice = %(instance_type_nice)s;
                      return record.name + " (" + InstanceTypeNice[record.instance_type] + ")";
                  }
 })
})''' % dict(instance_type_nice = auth.org_site_types)),
                                              ),
                             self.org_room_id(),
                             #location_id(),
                             Field("cancel", "boolean",
                                   default = False,
                                   label = T("Cancel Log Entry"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Cancel Log Entry"),
                                                                   T("'Cancel' will indicate an asset log entry did not occur")))
                                   ),
                             Field("cond", "integer",  # condition is a MySQL reserved word
                                   requires = IS_IN_SET(asset_condition_opts,
                                                        zero = "%s..." % T("Please select")),
                                   represent = lambda opt: \
                                       asset_condition_opts.get(opt, UNKNOWN_OPT),
                                   label = T("Condition")),
                             person_id("by_person_id",
                                       label = T("Assigned By"),               # This can either be the Asset controller if signed-out from the store
                                       default = auth.s3_logged_in_person(),   # or the previous owner if passed on directly (e.g. to successor in their post)
                                       comment = self.pr_person_comment(child="by_person_id"),
                                       ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ASSIGN = T("New Entry in Asset Log")
        crud_strings[tablename] = Storage(
            title_create = ADD_ASSIGN,
            title_display = T("Asset Log Details"),
            title_list = T("Asset Log"),
            title_update = T("Edit Asset Log Entry"),
            title_search = T("Search Asset Log"),
            subtitle_create = ADD_ASSIGN,
            label_list_button = T("Asset Log"),
            label_create_button = ADD_ASSIGN,
            label_delete_button = T("Delete Asset Log Entry"),
            msg_record_created = T("Entry added to Asset Log"),
            msg_record_modified = T("Asset Log Entry updated"),
            msg_record_deleted = T("Asset Log Entry deleted"),
            msg_list_empty = T("Asset Log Empty"))

        # Resource configuration
        configure(tablename,
                  onvalidation = self.asset_log_onvalidation,
                  onaccept = self.asset_log_onaccept,
                  listadd = False,
                  list_fields = ["id",
                                 "status",
                                 "datetime",
                                 "datetime_until",
                                 "organisation_id",
                                 "site_id",
                                 "room_id",
                                 #"location_id",
                                 "cancel",
                                 "cond",
                                 "comments"]
                   )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    asset_asset_id = asset_id,
                    asset_rheader = asset_rheader,
                    asset_represent = self.asset_represent,
                    asset_log_prep = self.asset_log_prep,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        asset_id = S3ReusableField("asset_id", "integer",
                                   writable=False,
                                   readable=False)
        return Storage(asset_asset_id=asset_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_represent(id):
        """
        """

        if not id:
            return current.messages.NONE

        db = current.db
        table = db.asset_asset
        itable = db.supply_item
        btable = db.supply_brand
        query = (table.id == id) & \
                (itable.id == table.item_id)
        r = db(query).select(table.number,
                             itable.name,
                             btable.name,
                             left = btable.on(itable.brand_id == btable.id),
                             limitby=(0, 1)).first()
        try:
            represent = "%s (%s" % (r.asset_asset.number,
                                    r.supply_item.name)
            if r.supply_brand.name:
                represent = "%s, %s)" % (represent,
                                         r.supply_brand.name)
            else:
                represent = "%s)" % represent
        except:
            represent = current.messages.UNKNOWN_OPT
        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_onaccept(form):
        """
        """

        db = current.db
        auth = current.auth

        vars = form.vars
        atable = db.asset_asset

        site_id = vars.get("site_id", None)
        if site_id:
            asset_id = vars.id
            # Set the Base Location
            tracker = S3Tracker()
            asset_tracker = tracker(atable, asset_id)
            asset_tracker.set_base_location(tracker(db.org_site, site_id))
            # Add a log entry for this
            ltable = db.asset_log
            ltable.insert(asset_id = asset_id,
                          status = ASSET_LOG_SET_BASE,
                          site_id = site_id,
                          )

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_log_onvalidation(form):
        """
        """

        request = current.request

        status = int(request.post_vars.get("status", 0))
        type = request.get_vars.get("type", None)
        #if  status == asset_log_status["ASSIGN"] and type == "organisation":
            # Site or Location is required
        #    if not form.vars.site_id and not form.vars.location_id:
        #        response.error = T("The asset must be assigned to a site OR location.")
        #        form.errors.site_or_location = T("Please enter a site OR a location")

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_log_onaccept(form):
        """
        """

        request = current.request
        status = request.vars.pop("status", None)
        if not status:
            # e.g. Import or Record merger
            return

        vars = form.vars
        status = int(vars.status or status)

        db = current.db
        s3db = current.s3db
        ltable = s3db.asset_log
        asset = db(ltable.id == vars.id).select(ltable.asset_id,
                                                limitby=(0, 1)).first()
        if asset:
            asset_id = asset.asset_id
        else:
            return
        current_log = asset_get_current_log(asset_id)

        type = request.get_vars.pop("type", None)
        log_time = current_log.datetime
        current_time = vars.get("datetime", None).replace(tzinfo=None)
        if log_time <= current_time:
            # This is a current assignment
            atable = s3db.asset_asset
            tracker = S3Tracker()
            asset_tracker = tracker(atable, asset_id)

            if status == ASSET_LOG_SET_BASE:
                # Set Base Location
                asset_tracker.set_base_location(tracker(s3db.org_site,
                                                        vars.site_id))
                # Populate the address fields
                s3_address_update(atable, asset_id)
            elif status == ASSET_LOG_ASSIGN:
                if type == "person":#
                    if vars.check_in_to_person:
                        asset_tracker.check_in(s3db.pr_person, vars.person_id,
                                               timestmp = request.utcnow)
                    else:
                        asset_tracker.set_location(vars.person_id,
                                                   timestmp = request.utcnow)
                    # Update main record for component
                    db(atable.id == asset_id).update(
                                                assigned_to_id=vars.person_id
                                            )

                elif type == "site":
                    asset_tracker.check_in(s3db.org_site, vars.site_id,
                                           timestmp = request.utcnow)
                elif type == "organisation":
                    #if vars.site_or_location == SITE:
                    asset_tracker.check_in(s3db.org_site, vars.site_id,
                                           timestmp = request.utcnow)
                    #if vars.site_or_location == LOCATION:
                    #    asset_tracker.set_location(vars.location_id,
                    #                               timestmp = request.utcnow)

            elif status == ASSET_LOG_RETURN:
                # Set location to base location
                asset_tracker.set_location(asset_tracker,
                                           timestmp = request.utcnow)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def asset_log_prep(r):
        """
            Called by Controller
        """

        T = current.T
        db = current.db
        request = current.request

        table = db.asset_log

        if r.record:
            asset = Storage(r.record)
        else:
            # This is a new record
            asset = Storage()
            table.cancel.readable = False
            table.cancel.writable = False

        # This causes an error with the dataTables paginate
        # if used only in r.interactive & not also r.representation=="aadata"
        if r.method != "read" and r.method != "update":
            table.cancel.readable = False
            table.cancel.writable = False
        current_log = asset_get_current_log(asset.id)
        if request.vars.status:
            status = int(request.vars.status)
        else:
            status = 0

        if status and status != "None":
            field = table.status
            field.default = status
            field.readable = False
            field.writable = False
        elif current_log:
            table.status.default = current_log.status

        if current_log.organisation_id:
            table.organisation_id.default = current_log.organisation_id
            table.site_id.requires = IS_ONE_OF(db, "org_site.site_id",
                                               table.site_id.represent,
                                               filterby = "organisation_id",
                                               filter_opts = [current_log.organisation_id])

        crud_strings = current.response.s3.crud_strings.asset_log
        if status == ASSET_LOG_SET_BASE:
            crud_strings.subtitle_create = T("Set Base Facility/Site")
            crud_strings.msg_record_created = T("Base Facility/Site Set")
            table.by_person_id.label = T("Set By")
            table.site_id.writable = True
            table.datetime_until.readable = False
            table.datetime_until.writable = False
            table.person_id.readable = False
            table.person_id.writable = False
            table.organisation_id.readable = True
            table.organisation_id.writable = True
            table.site_id.requires = IS_ONE_OF(db, "org_site.site_id",
                                               table.site_id.represent)
            #table.site_or_location.readable = False
            #table.site_or_location.writable = False
            #table.location_id.readable = False
            #table.location_id.writable = False

        elif status == ASSET_LOG_RETURN:
            crud_strings.subtitle_create = T("Return")
            crud_strings.msg_record_created = T("Returned")
            table.person_id.label = T("Returned From")
            table.person_id.default = current_log.person_id
            #table.site_or_location.readable = False
            #table.site_or_location.writable = False
            table.site_id.readable = False
            table.site_id.writable = False
            #table.location_id.readable = False
            #table.location_id.writable = False

        elif status == ASSET_LOG_ASSIGN:
            type = request.vars.type
            # table["%s_id" % type].required = True
            if type == "person":#
                crud_strings.subtitle_create = T("Assign to Person")
                crud_strings.msg_record_created = T("Assigned to Person")
                table["person_id"].requires = IS_ONE_OF(db, "pr_person.id",
                                                        table.person_id.represent,
                                                        orderby="pr_person.first_name",
                                                        sort=True,
                                                        error_message="Person must be specified!")
                table.check_in_to_person.readable = True
                table.check_in_to_person.writable = True
            elif type == "site":
                crud_strings.subtitle_create = T("Assign to Facility/Site")
                crud_strings.msg_record_created = T("Assigned to Facility/Site")
                #field = table.site_or_location
                #field.readable = False
                #field.writable = False
                #field.default = SITE
                #table.location_id.readable = False
                #table.location_id.writable = False
            elif type == "organisation":
                crud_strings.subtitle_create = T("Assign to Organization")
                crud_strings.msg_record_created = T("Assigned to Organization")
                table.organisation_id.readable = True
                table.organisation_id.writable = True
                table.organisation_id.requires = IS_ONE_OF(db, "org_organisation.id",
                                                              table.organisation_id.represent,
                                                              orderby="org_organisation.name",
                                                              sort=True)
                table.site_id.requires = IS_ONE_OF(db, "org_site.site_id",
                                                   table.site_id.represent)
                #table.site_or_location.required = True
        elif "status" in request.get_vars:
            crud_strings.subtitle_create = T("Update Status")
            crud_strings.msg_record_created = T("Status Updated")
            table.person_id.label = T("Updated By")
            field = table.status
            field.readable = True
            field.writable = True
            field.requires = IS_IN_SET({ASSET_LOG_CHECK    : T("Check"),
                                        ASSET_LOG_REPAIR   : T("Repair"),
                                        ASSET_LOG_DONATED  : T("Donated"),
                                        ASSET_LOG_LOST     : T("Lost"),
                                        ASSET_LOG_STOLEN   : T("Stolen"),
                                        ASSET_LOG_DESTROY  : T("Destroyed"),
                                       })

# =============================================================================
def asset_get_current_log(asset_id):
    """
    """

    table = current.s3db.asset_log
    query = ( table.asset_id == asset_id ) & \
            ( table.cancel == False ) & \
            ( table.deleted == False )
    # Get the log with the maximum time
    asset_log = current.db(query).select(table.id,
                                         table.status,
                                         table.datetime,
                                         table.cond,
                                         table.person_id,
                                         table.organisation_id,
                                         table.site_id,
                                         #table.location_id,
                                         orderby = ~table.datetime,
                                         limitby=(0, 1)).first()
    if asset_log:
        return Storage(datetime = asset_log.datetime,
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
def asset_rheader(r):
    """ Resource Header for Assets """

    if r.representation == "html":
        record = r.record
        if record:

            T = current.T
            s3db = current.s3db
            s3 = current.response.s3

            NONE = current.messages.NONE

            if record.type == ASSET_TYPE_VEHICLE:
                tabs = [(T("Asset Details"), None),
                        (T("Vehicle Details"), "vehicle"),
                        (T("GPS Data"), "gps")]
            else:
                tabs = [(T("Edit Details"), None)]
            #elif record.type == s3.asset.ASSET_TYPE_RADIO:
            #    tabs.append((T("Radio Details"), "radio"))
            #elif record.type == s3.asset.ASSET_TYPE_TELEPHONE:
            #    tabs.append((T("Telephone Details"), "phone"))
            tabs.append((T("Log"), "log"))
            tabs.append((T("Documents"), "document"))

            rheader_tabs = s3_rheader_tabs(r, tabs)


            if current.request.controller == "vehicle":
                func = "vehicle"
            else:
                func = "asset"

            # @ToDo: Check permissions before displaying buttons

            asset_action_btns = [ A( T("Set Base Facility/Site"),
                                     _href = URL(f=func,
                                                 args = [record.id, "log", "create"],
                                                 vars = dict(status = ASSET_LOG_SET_BASE)
                                                ),
                                     _class = "action-btn"
                                     )
                                ]

            current_log = asset_get_current_log(record.id)
            status = current_log.status

            #if record.location_id:
            # A Base Site has been set
            # Return functionality removed  - as it doesn't set site_id & organisation_id in the logs
            #if status == ASSET_LOG_ASSIGN:
            #    asset_action_btns += [ A( T("Return"),
            #                              _href = URL(f=func,
            #                                          args = [record.id, "log", "create"],
            #                                          vars = dict(status = ASSET_LOG_RETURN)
            #                                        ),
            #                              _class = "action-btn"
            #                            )
            #                           ]
            if status < ASSET_LOG_DONATED:
                # @ToDo: deployment setting to prevent assigning assets before returning them
                # The Asset is available for assignment (not disposed)
                asset_action_btns += [ A( T("Assign to Person"),
                                          _href = URL(f=func,
                                                      args = [record.id, "log", "create"],
                                                      vars = dict(status = ASSET_LOG_ASSIGN,
                                                                  type = "person")
                                                    ),
                                          _class = "action-btn"
                                        ),
                                      A( T("Assign to Facility/Site"),
                                          _href = URL(f=func,
                                                      args = [record.id, "log", "create"],
                                                      vars = dict(status = ASSET_LOG_ASSIGN,
                                                                  type = "site")
                                                    ),
                                          _class = "action-btn"
                                        ),
                                      A( T("Assign to Organization"),
                                         _href = URL(f=func,
                                                     args = [record.id, "log", "create"],
                                                     vars = dict(status = ASSET_LOG_ASSIGN,
                                                                 type = "organisation")
                                                    ),
                                         _class = "action-btn"
                                       ),
                                    ]
            asset_action_btns += [  A( T("Update Status"),
                                       _href = URL(f=func,
                                                   args = [record.id, "log", "create"],
                                                   vars = None
                                                ),
                                       _class = "action-btn"
                                     ),
                                  ]

            table = r.table
            ltable = s3db.asset_log
            rheader = DIV(TABLE(TR( TH("%s: " % table.number.label),
                                    record.number,
                                    TH("%s: " % table.item_id.label),
                                    table.item_id.represent(record.item_id)
                                  ),
                                TR( TH("%s: " % ltable.cond.label),
                                    ltable.cond.represent(current_log.cond),
                                    TH("%s: " % ltable.status.label),
                                    ltable.status.represent(status),
                                  ),
                                TR( TH("%s: " % ltable.person_id.label),
                                    ltable.person_id.represent(current_log.person_id),
                                    TH("%s: " % ltable.site_id.label),
                                    ltable.site_id.represent(current_log.site_id),
                                  ),
                               ),
                          DIV(_style = "margin-top:5px;",
                              *asset_action_btns
                              ),
                          rheader_tabs)
            return rheader
    return None

# =============================================================================
class AssetVirtualFields:
    """ Virtual fields as dimension classes for reports """

    def site(self):
        # The site of the asset
        try:
            location_id = self.asset_asset.location_id
        except AttributeError:
            # not available
            location_id = None
        if location_id:
            s3db = current.s3db
            stable = s3db.org_site
            query = (stable.location_id == location_id)
            site = current.db(query).select(stable.name,
                                            stable.site_id,
                                            stable.instance_type,
                                            limitby=(0, 1)).first()
            if site:
                return s3db.org_site_represent(site, show_link=False)
        return current.messages.NONE

# =============================================================================
def asset_controller():
    """ RESTful CRUD controller """

    s3 = current.response.s3
    s3db = current.s3db

    # Pre-process
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            s3_address_hide(r.table)
        if r.component_name == "log":
            s3db.asset_log_prep(r)
            #if r.method == "update":
                # We don't want to exclude fields in update forms
                #pass
            #elif r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                #table = r.component.table
                #table.returned.readable = table.returned.writable = False
                #table.returned_status.readable = table.returned_status.writable = False
                # Process Base Site
                #s3db.configure(table._tablename,
                #                onaccept=asset_transfer_onaccept)
        #else:
            # @ToDo: Add Virtual Fields to the List view for 'Currently assigned to' & 'Current Location'

        return True
    s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.method != "import":
            S3CRUD.action_buttons(r, deletable=False)
            #if not r.component:
                #s3.actions.append({"url" : URL(c="asset", f="asset",
                #                               args = ["[id]", "log", "create"],
                #                               vars = {"status" : eden.asset.asset_log_status["ASSIGN"],
                #                                       "type" : "person"}),
                #                   "_class" : "action-btn",
                #                   "label" : str(T("Assign"))})
        return output
    s3.postp = postp

    output = current.rest_controller("asset", "asset",
                                     rheader=s3db.asset_rheader)
    return output

# END =========================================================================
