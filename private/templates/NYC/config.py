# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.html import A, URL
from gluon.storage import Storage

from s3 import s3_fullname

T = current.T
settings = current.deployment_settings

"""
    Template settings for NYC Prepared
"""

# Pre-Populate
settings.base.prepopulate = ("NYC",)

settings.base.system_name = T("NYC Prepared")
settings.base.system_name_short = T("NYC Prepared")

# Theme (folder to use for views/layout.html)
settings.base.theme = "NYC"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
settings.ui.filter_formstyle = "table_inline"

settings.msg.parser = "NYC"

# Uncomment to Hide the language toolbar
settings.L10n.display_toolbar = False
# Default timezone for users
settings.L10n.utc_offset = "UTC -0500"
# Uncomment these to use US-style dates in English
settings.L10n.date_format = "%m-%d-%Y"
# Start week on Sunday
settings.L10n.firstDOW = 0
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","
# Default Country Code for telephone numbers
settings.L10n.default_country_code = 1
# Enable this to change the label for 'Mobile Phone'
settings.ui.label_mobile_phone = "Cell Phone"
# Enable this to change the label for 'Postcode'
settings.ui.label_postcode = "ZIP Code"
# Uncomment to disable responsive behavior of datatables
# - Disabled until tested
settings.ui.datatables_responsive = False
# PDF to Letter
settings.base.paper_size = T("Letter")

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ("US",)

settings.fin.currencies = {
    "USD" : T("United States Dollars"),
}

settings.L10n.languages = OrderedDict([
    ("en", "English"),
    ("es", "Español"),
])

# Authentication settings
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
# Should users be allowed to register themselves?
settings.security.self_registration = "index"
# Do new users need to verify their email address?
settings.auth.registration_requires_verification = True
# Do new users need to be approved by an administrator prior to being able to login?
settings.auth.registration_requires_approval = True
# Always notify the approver of a new (verified) user, even if the user is automatically approved
#settings.auth.always_notify_approver = False
# Uncomment this to request the Mobile Phone when a user registers
settings.auth.registration_requests_mobile_phone = True
# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True
# Uncomment this to request the Site when a user registers
#settings.auth.registration_requests_site = True

# Roles that newly-registered users get automatically
#settings.auth.registration_roles = { 0: ["comms_dispatch"]}

#settings.auth.registration_link_user_to = {"staff":T("Staff"),
#                                           #"volunteer":T("Volunteer")
#                                           }
settings.auth.registration_link_user_to_default = "staff"

settings.security.policy = 5 # Controller, Function & Table ACLs

# Enable this to have Open links in IFrames open a full page in a new tab
settings.ui.iframe_opens_full = True
settings.ui.label_attachments = "Media"
settings.ui.update_label = "Edit"

# Uncomment to disable checking that LatLons are within boundaries of their parent
#settings.gis.check_within_parent_boundaries = False
# GeoNames username
settings.gis.geonames_username = "eden_nyc"

# Uncomment to show created_by/modified_by using Names not Emails
settings.ui.auth_user_represent = "name"

# Record Approval
settings.auth.record_approval = True
settings.auth.record_approval_required_for = ("org_organisation",)

# -----------------------------------------------------------------------------
# Audit
def audit_write(method, tablename, form, record, representation):
    if not current.auth.user:
        # Don't include prepop
        return False
    if tablename in ("cms_post",
                     "org_facility",
                     "org_organisation",
                     "req_req",
                     ):
        # Perform normal Audit
        return True
    else:
        # Don't Audit non user-visible resources
        return False

settings.security.audit_write = audit_write

# -----------------------------------------------------------------------------
# CMS
# Uncomment to use Bookmarks in Newsfeed
settings.cms.bookmarks = True
# Uncomment to use have Filter form in Newsfeed be open by default
settings.cms.filter_open = True
# Uncomment to adjust filters in Newsfeed when clicking on locations instead of opening the profile page
settings.cms.location_click_filters = True
# Uncomment to use organisation_id instead of created_by in Newsfeed
settings.cms.organisation = "post_organisation.organisation_id"
# Uncomment to use org_group_id in Newsfeed
settings.cms.organisation_group = "post_organisation_group.group_id"
# Uncomment to use person_id instead of created_by in Newsfeed
settings.cms.person = "person_id"
# Uncomment to use Rich Text editor in Newsfeed
settings.cms.richtext = True
# Uncomment to show Links in Newsfeed
settings.cms.show_links = True
# Uncomment to show Tags in Newsfeed
settings.cms.show_tags = True
# Uncomment to show post Titles in Newsfeed
settings.cms.show_titles = True

# -----------------------------------------------------------------------------
# Inventory Management
# Uncomment to customise the label for Facilities in Inventory Management
settings.inv.facility_label = "Facility"
# Uncomment if you need a simpler (but less accountable) process for managing stock levels
#settings.inv.direct_stock_edits = True
# Uncomment to call Stock Adjustments, 'Stock Counts'
settings.inv.stock_count = True
# Uncomment to not track pack values
settings.inv.track_pack_values = False
settings.inv.send_show_org = False
# Types common to both Send and Receive
settings.inv.shipment_types = {
        1: T("Other Warehouse")
    }
settings.inv.send_types = {
        #21: T("Distribution")
    }
settings.inv.send_type_default = 1
settings.inv.item_status = {
        #0: current.messages["NONE"],
        #1: T("Dump"),
        #2: T("Sale"),
        #3: T("Reject"),
        #4: T("Surplus")
   }

# -----------------------------------------------------------------------------
# Organisations
#
# Enable the use of Organisation Groups
settings.org.groups = "Network"
# Make Services Hierarchical
settings.org.services_hierarchical = True
# Set the label for Sites
settings.org.site_label = "Facility"
#settings.org.site_label = "Location"
# Uncomment to show the date when a Site (Facilities-only for now) was last contacted
settings.org.site_last_contacted = True
# Enable certain fields just for specific Organisations
# empty list => disabled for all (including Admin)
#settings.org.dependent_fields = { \
#     "pr_person_details.mother_name"             : [],
#     "pr_person_details.father_name"             : [],
#     "pr_person_details.company"                 : [],
#     "pr_person_details.affiliations"            : [],
#     "vol_volunteer.active"                      : [],
#     "vol_volunteer_cluster.vol_cluster_type_id"      : [],
#     "vol_volunteer_cluster.vol_cluster_id"          : [],
#     "vol_volunteer_cluster.vol_cluster_position_id" : [],
#     }
# Uncomment to use an Autocomplete for Site lookup fields
settings.org.site_autocomplete = True
# Extra fields to search in Autocompletes & display in Representations
settings.org.site_autocomplete_fields = ("organisation_id$name",
                                         "location_id$addr_street",
                                         )
# Uncomment to hide inv & req tabs from Sites
#settings.org.site_inv_req_tabs = True

# -----------------------------------------------------------------------------
def facility_marker_fn(record):
    """
        Function to decide which Marker to use for Facilities Map
        @ToDo: Legend
    """

    db = current.db
    s3db = current.s3db
    table = db.org_facility_type
    ltable = db.org_site_facility_type
    query = (ltable.site_id == record.site_id) & \
            (ltable.facility_type_id == table.id)
    rows = db(query).select(table.name)
    types = [row.name for row in rows]

    # Use Marker in preferential order
    if "Hub" in types:
        marker = "warehouse"
    elif "Medical Clinic" in types:
        marker = "hospital"
    elif "Food" in types:
        marker = "food"
    elif "Relief Site" in types:
        marker = "asset"
    elif "Residential Building" in types:
        marker = "residence"
    #elif "Shelter" in types:
    #    marker = "shelter"
    else:
        # Unknown
        marker = "office"
    if settings.has_module("req"):
        # Colour code by open/priority requests
        reqs = record.reqs
        if reqs == 3:
            # High
            marker = "%s_red" % marker
        elif reqs == 2:
            # Medium
            marker = "%s_yellow" % marker
        elif reqs == 1:
            # Low
            marker = "%s_green" % marker

    mtable = db.gis_marker
    try:
        marker = db(mtable.name == marker).select(mtable.image,
                                                  mtable.height,
                                                  mtable.width,
                                                  cache=s3db.cache,
                                                  limitby=(0, 1)
                                                  ).first()
    except:
        marker = db(mtable.name == "office").select(mtable.image,
                                                    mtable.height,
                                                    mtable.width,
                                                    cache=s3db.cache,
                                                    limitby=(0, 1)
                                                    ).first()
    return marker

# -----------------------------------------------------------------------------
def org_facility_onvalidation(form):
    """
        Default the name to the Street Address
    """

    form_vars = form.vars
    name = form_vars.get("name", None)
    if name:
        return
    address = form_vars.get("address", None)
    if address:
        form_vars.name = address
    else:
        # We need a default
        form_vars.name = current.db.org_facility.location_id.represent(form_vars.location_id)

# -----------------------------------------------------------------------------
def customise_org_facility_controller(**attr):

    s3db = current.s3db
    s3 = current.response.s3

    # Tell the client to request per-feature markers
    s3db.configure("org_facility", marker_fn=facility_marker_fn)

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        if r.method not in ("read", "update"):
            types = r.get_vars.get("site_facility_type.facility_type_id__belongs", None)
            if not types:
                # Hide Private Residences
                from s3 import FS
                s3.filter = FS("site_facility_type.facility_type_id$name") != "Private Residence"

        if r.interactive:
            tablename = "org_facility"
            table = s3db[tablename]

            if not r.component and r.method in (None, "create", "update"):
                from s3 import IS_LOCATION, S3LocationSelector, S3MultiSelectWidget
                field = table.location_id
                if r.method in ("create", "update"):
                    field.label = "" # Gets replaced by widget
                levels = ("L2", "L3")
                field.requires = IS_LOCATION()
                field.widget = S3LocationSelector(levels=levels,
                                                  hide_lx=False,
                                                  reverse_lx=True,
                                                  show_address=True,
                                                  show_postcode=True,
                                                  )
                table.organisation_id.widget = S3MultiSelectWidget(multiple=False)

            if r.get_vars.get("format", None) == "popup":
                # Coming from req/create form
                # Hide most Fields
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                # We default this onvalidation
                table.name.notnull = False
                table.name.requires = None
                crud_form = S3SQLCustomForm(S3SQLInlineComponent(
                                                "site_facility_type",
                                                label = T("Facility Type"),
                                                fields = [("", "facility_type_id")],
                                                multiple = False,
                                                required = True,
                                            ),
                                            "name",
                                            "location_id",
                                            )
                s3db.configure(tablename,
                               crud_form = crud_form,
                               onvalidation = org_facility_onvalidation,
                               )

        return True
    s3.prep = custom_prep

    return attr

settings.customise_org_facility_controller = customise_org_facility_controller

# -----------------------------------------------------------------------------
def customise_org_organisation_resource(r, tablename):

    from gluon.html import DIV, INPUT
    from s3 import S3MultiSelectWidget, S3SQLCustomForm, S3SQLInlineLink, S3SQLInlineComponent, S3SQLInlineComponentMultiSelectWidget

    s3db = current.s3db

    if r.tablename == "org_organisation":
        if r.id:
            # Update form
            ctable = s3db.pr_contact
            query = (ctable.pe_id == r.record.pe_id) & \
                    (ctable.contact_method == "RSS") & \
                    (ctable.deleted == False)
            rss = current.db(query).select(ctable.poll,
                                           limitby=(0, 1)
                                           ).first()
            if rss and not rss.poll:
                # Remember that we don't wish to import
                rss_import = "on"
            else:
                # Default
                rss_import = None
        else:
            # Create form: Default
            rss_import = None
    else:
        # Component
        if r.component_id:
            # Update form
            db = current.db
            otable = s3db.org_organisation
            org = db(otable.id == r.component_id).select(otable.pe_id,
                                                         limitby=(0, 1)
                                                         ).first()
            try:
                pe_id = org.pe_id
            except:
                current.log.error("Org %s not found: cannot set rss_import correctly" % r.component_id)
                # Default
                rss_import = None
            else:
                ctable = s3db.pr_contact
                query = (ctable.pe_id == pe_id) & \
                        (ctable.contact_method == "RSS") & \
                        (ctable.deleted == False)
                rss = db(query).select(ctable.poll,
                                       limitby=(0, 1)
                                       ).first()
                if rss and not rss.poll:
                    # Remember that we don't wish to import
                    rss_import = "on"
                else:
                    # Default
                    rss_import = None
        else:
            # Create form: Default
            rss_import = None

    mtable = s3db.org_group_membership
    mtable.group_id.widget = S3MultiSelectWidget(multiple=False)
    mtable.status_id.widget = S3MultiSelectWidget(multiple=False,
                                                  create=dict(c="org",
                                                              f="group_membership_status",
                                                              label=str(T("Add New Status")),
                                                              parent="group_membership",
                                                              child="status_id"
                                                              ))
    crud_form = S3SQLCustomForm(
        "name",
        "acronym",
        S3SQLInlineLink(
            "organisation_type",
            field = "organisation_type_id",
            label = T("Type"),
            multiple = False,
            #widget = "hierarchy",
        ),
        S3SQLInlineComponentMultiSelectWidget(
        # activate hierarchical org_service:
        #S3SQLInlineLink(
            "service",
            label = T("Services"),
            field = "service_id",
            # activate hierarchical org_service:
            #leafonly = False,
            #widget = "hierarchy",
        ),
        S3SQLInlineComponent(
            "group_membership",
            label = T("Network"),
            fields = [("", "group_id"),
                      ("", "status_id"),
                      ],
            ),
        S3SQLInlineComponent(
            "address",
            label = T("Address"),
            multiple = False,
            # This is just Text - put into the Comments box for now
            # Ultimately should go into location_id$addr_street
            fields = [("", "comments")],
        ),
        S3SQLInlineComponentMultiSelectWidget(
            "location",
            label = T("Neighborhoods Served"),
            field = "location_id",
            filterby = dict(field = "level",
                            options = "L4"
                            ),
            # @ToDo: GroupedCheckbox Widget or Hierarchical MultiSelectWidget
            #cols = 5,
        ),
        "phone",
        S3SQLInlineComponent(
            "contact",
            name = "phone2",
            label = T("Phone2"),
            multiple = False,
            fields = [("", "value")],
            filterby = dict(field = "contact_method",
                            options = "WORK_PHONE"
                            )
        ),
        S3SQLInlineComponent(
            "contact",
            name = "email",
            label = T("Email"),
            multiple = False,
            fields = [("", "value")],
            filterby = dict(field = "contact_method",
                            options = "EMAIL"
                            )
        ),
        "website",
        S3SQLInlineComponent(
            "contact",
            comment = DIV(INPUT(_type="checkbox",
                                _name="rss_no_import",
                                value = rss_import,
                                ),
                          T("Don't Import Feed")),
            name = "rss",
            label = T("RSS"),
            multiple = False,
            fields = [("", "value"),
                      #(T("Don't Import Feed"), "poll"),
                      ],
            filterby = dict(field = "contact_method",
                            options = "RSS"
                            )
        ),
        S3SQLInlineComponent(
            "document",
            name = "iCal",
            label = "iCAL",
            multiple = False,
            fields = [("", "url")],
            filterby = dict(field = "name",
                            options="iCal"
                            )
        ),
        S3SQLInlineComponent(
            "document",
            name = "data",
            label = T("Data"),
            multiple = False,
            fields = [("", "url")],
            filterby = dict(field = "name",
                            options="Data"
                            )
        ),
        S3SQLInlineComponent(
            "contact",
            name = "twitter",
            label = T("Twitter"),
            multiple = False,
            fields = [("", "value")],
            filterby = dict(field = "contact_method",
                            options = "TWITTER"
                            )
        ),
        S3SQLInlineComponent(
            "contact",
            name = "facebook",
            label = T("Facebook"),
            multiple = False,
            fields = [("", "value")],
            filterby = dict(field = "contact_method",
                            options = "FACEBOOK"
                            )
        ),
        "comments",
        postprocess = pr_contact_postprocess,
    )

    from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter
    # activate hierarchical org_service:
    #from s3 import S3LocationFilter, S3OptionsFilter, S3TextFilter, S3HierarchyFilter
    filter_widgets = [
        S3TextFilter(["name", "acronym"],
                     label = T("Name"),
                     _class = "filter-search",
                     ),
        S3OptionsFilter("group_membership.group_id",
                        label = T("Network"),
                        represent = "%(name)s",
                        #hidden = True,
                        ),
        S3LocationFilter("organisation_location.location_id",
                         label = T("Neighborhood"),
                         levels = ("L3", "L4"),
                         #hidden = True,
                         ),
        S3OptionsFilter("service_organisation.service_id",
                        #label = T("Service"),
                        #hidden = True,
                        ),
        # activate hierarchical org_service:
        #S3HierarchyFilter("service_organisation.service_id",
        #                  #label = T("Service"),
        #                  #hidden = True,
        #                  ),
        S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                        label = T("Type"),
                        #hidden = True,
                        ),
        ]

    list_fields = ["name",
                   (T("Type"), "organisation_organisation_type.organisation_type_id"),
                   (T("Services"), "service.name"),
                   "phone",
                   (T("Email"), "email.value"),
                   "website"
                   #(T("Neighborhoods Served"), "location.name"),
                   ]

    s3db.configure("org_organisation",
                   crud_form = crud_form,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   )

settings.customise_org_organisation_resource = customise_org_organisation_resource

# -----------------------------------------------------------------------------
def customise_org_organisation_controller(**attr):

    s3db = current.s3db
    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive:
            if r.component_name == "facility":
                if r.method in (None, "create", "update"):
                    from s3 import IS_LOCATION, S3LocationSelector
                    table = s3db.org_facility
                    field = table.location_id
                    if r.method in ("create", "update"):
                        field.label = "" # Gets replaced by widget
                    levels = ("L2", "L3")
                    field.requires = IS_LOCATION()
                    field.widget = S3LocationSelector(levels=levels,
                                                      hide_lx=False,
                                                      reverse_lx=True,
                                                      show_address=True,
                                                      show_postcode=True,
                                                      )
            elif r.component_name == "human_resource":
                # Don't assume that user is from same org/site as Contacts they create
                r.component.table.site_id.default = None

        return result
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            if "rheader" in output:
                # Custom Tabs
                tabs = [(T("Basic Details"), None),
                        (T("Contacts"), "human_resource"),
                        (T("Facilities"), "facility"),
                        (T("Projects"), "project"),
                        (T("Assets"), "asset"),
                        ]
                output["rheader"] = s3db.org_rheader(r, tabs=tabs)
        return output
    s3.postp = custom_postp

    return attr

settings.customise_org_organisation_controller = customise_org_organisation_controller

# -----------------------------------------------------------------------------
def customise_org_group_controller(**attr):

    s3db = current.s3db
    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if not r.component:

            table = s3db.org_group

            list_fields = ["name",
                           "mission",
                           "website",
                           "meetings",
                           ]

            s3db.configure("org_group",
                           list_fields = list_fields,
                           )

            if r.interactive:
                from gluon.html import DIV, INPUT
                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                if r.method != "read":
                    from gluon.validators import IS_EMPTY_OR
                    from s3 import IS_LOCATION, S3LocationSelector
                    field = table.location_id
                    field.label = "" # Gets replaced by widget
                    #field.requires = IS_LOCATION()
                    #field.requires = IS_EMPTY_OR(IS_LOCATION()) # That's the default!
                    field.widget = S3LocationSelector(levels = ("L2",),
                                                      points = True,
                                                      polygons = True,
                                                      )
                    # Default location to Manhattan
                    db = current.db
                    gtable = db.gis_location
                    query = (gtable.name == "New York") & \
                            (gtable.level == "L2")
                    manhattan = db(query).select(gtable.id,
                                                 limitby=(0, 1)).first()
                    if manhattan:
                        field.default = manhattan.id

                table.mission.readable = table.mission.writable = True
                table.meetings.readable = table.meetings.writable = True

                if r.id:
                    # Update form
                    ctable = s3db.pr_contact
                    query = (ctable.pe_id == r.record.pe_id) & \
                            (ctable.contact_method == "RSS") & \
                            (ctable.deleted == False)
                    rss = current.db(query).select(ctable.poll,
                                                   limitby=(0, 1)
                                                   ).first()
                    if rss and not rss.poll:
                        # Remember that we don't wish to import
                        rss_import = "on"
                    else:
                        # Default
                        rss_import = None
                else:
                    # Create form: Default
                    rss_import = None

                crud_form = S3SQLCustomForm(
                    "name",
                    "location_id",
                    "mission",
                    S3SQLInlineComponent(
                        "contact",
                        name = "phone",
                        label = T("Phone"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "WORK_PHONE"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "contact",
                        name = "email",
                        label = T("Email"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "EMAIL"
                                        )
                    ),
                    "website",
                    S3SQLInlineComponent(
                        "contact",
                        comment = DIV(INPUT(_type="checkbox",
                                            _name="rss_no_import",
                                            value = rss_import,
                                            ),
                                      T("Don't Import Feed")),
                        name = "rss",
                        label = T("RSS"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "RSS"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "document",
                        name = "iCal",
                        label = "iCAL",
                        multiple = False,
                        fields = [("", "url")],
                        filterby = dict(field = "name",
                                        options="iCal"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "document",
                        name = "data",
                        label = T("Data"),
                        multiple = False,
                        fields = [("", "url")],
                        filterby = dict(field = "name",
                                        options="Data"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "contact",
                        name = "twitter",
                        label = T("Twitter"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "TWITTER"
                                        )
                    ),
                    S3SQLInlineComponent(
                        "contact",
                        name = "facebook",
                        label = T("Facebook"),
                        multiple = False,
                        fields = [("", "value")],
                        filterby = dict(field = "contact_method",
                                        options = "FACEBOOK"
                                        )
                    ),
                    "meetings",
                    "comments",
                    postprocess = pr_contact_postprocess,
                )

                s3db.configure("org_group",
                               crud_form = crud_form,
                               )

        elif r.component_name == "pr_group":
            list_fields = [#(T("Network"), "group_team.org_group_id"),
                           "name",
                           "description",
                           "meetings",
                           (T("Chairperson"), "chairperson"),
                           "comments",
                           ]

            s3db.configure("pr_group",
                           list_fields = list_fields,
                           )

        elif r.component_name == "organisation":
            # Add Network Status to List Fields
            list_fields = s3db.get_config("org_organisation", "list_fields")
            list_fields.insert(1, "group_membership.status_id")

        return result
    s3.prep = custom_prep

    if current.auth.s3_logged_in():
        # Allow components with components (such as org/group) to breakout from tabs
        attr["native"] = True

    return attr

settings.customise_org_group_controller = customise_org_group_controller

# -----------------------------------------------------------------------------
# Persons
# Uncomment to hide fields in S3AddPersonWidget
settings.pr.request_dob = False
settings.pr.request_gender = False
# Doesn't yet work (form fails to submit)
#settings.pr.select_existing = False
settings.pr.show_emergency_contacts = False
# Only show Private Contacts Tab (Public is done via Basic Details tab)
settings.pr.contacts_tabs = ("private",)

# -----------------------------------------------------------------------------
# Persons
def customise_pr_person_controller(**attr):
    """
        Non-logged in users can access pr/person
        Logged-in users access via hrm/person
    """

    s3db = current.s3db
    s3 = current.response.s3
    AUTHENTICATED = current.auth.is_logged_in()

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        #if r.method == "validate":
        #    # Can't validate image without the file
        #    image_field = s3db.pr_image.image
        #    image_field.requires = None

        if r.interactive or r.representation == "aadata":

            if not r.component:
                hr_fields = ["organisation_id",
                             "job_title_id",
                             "site_id",
                             ]
                if r.method in ("create", "update"):
                    get_vars = r.get_vars
                    # Context from a Profile page?"
                    organisation_id = get_vars.get("(organisation)", None)
                    if organisation_id:
                        field = s3db.hrm_human_resource.organisation_id
                        field.default = organisation_id
                        field.readable = field.writable = False
                        hr_fields.remove("organisation_id")
                    site_id = get_vars.get("(site)", None)
                    if site_id:
                        field = s3db.hrm_human_resource.site_id
                        field.default = site_id
                        field.readable = field.writable = False
                        hr_fields.remove("site_id")
                    else:
                        s3db.hrm_human_resource.site_id.default = None

                # ImageCrop widget doesn't currently work within an Inline Form
                #image_field = s3db.pr_image.image
                #from gluon.validators import IS_IMAGE
                #image_field.requires = IS_IMAGE()
                #image_field.widget = None

                from s3 import S3SQLCustomForm, S3SQLInlineComponent
                MOBILE = settings.get_ui_label_mobile_phone()
                EMAIL = T("Email")

                s3_sql_custom_fields = ["first_name",
                                        #"middle_name",
                                        "last_name",
                                        S3SQLInlineComponent(
                                            "human_resource",
                                            name = "human_resource",
                                            label = "",
                                            multiple = False,
                                            fields = hr_fields,
                                            ),
                                        S3SQLInlineComponent(
                                            "contact",
                                            name = "email",
                                            label = EMAIL,
                                            #multiple = True,
                                            fields = [("", "value")],
                                            filterby = [dict(field = "contact_method",
                                                             options = "EMAIL"),
                                                        dict(field = "access",
                                                             options = 2),
                                                        ]
                                            ),
                                        S3SQLInlineComponent(
                                            "contact",
                                            name = "phone",
                                            label = MOBILE,
                                            #multiple = True,
                                            fields = [("", "value")],
                                            filterby = [dict(field = "contact_method",
                                                             options = "SMS"),
                                                        dict(field = "access",
                                                             options = 2),
                                                        ]
                                            ),
                                        #S3SQLInlineComponent(
                                        #    "image",
                                        #    name = "image",
                                        #    label = T("Photo"),
                                        #    multiple = False,
                                        #    fields = [("", "image")],
                                        #    filterby = dict(field = "profile",
                                        #                    options=[True]
                                        #                    )
                                        #    ),
                                        ]
                if r.method != "update":
                    other_contact_opts = current.msg.CONTACT_OPTS.keys()
                    other_contact_opts.remove("EMAIL")
                    other_contact_opts.remove("SMS")

                    s3_sql_custom_fields.append(S3SQLInlineComponent("contact",
                                                                     name = "contact",
                                                                     label = T("Additional Public Contact Info"),
                                                                     #multiple = True,
                                                                     fields = [("", "contact_method"),
                                                                               ("", "value"),
                                                                               ],
                                                                     filterby = [dict(field = "access",
                                                                                      options = 2),
                                                                                 dict(field = "contact_method",
                                                                                      options = other_contact_opts),
                                                                                 ]
                                                                     ))

                crud_form = S3SQLCustomForm(*s3_sql_custom_fields)

                list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
                               "first_name",
                               #"middle_name",
                               "last_name",
                               (T("Job Title"), "human_resource.job_title_id"),
                               (T("Office"), "human_resource.site_id"),
                               ]

                if AUTHENTICATED:
                    # @ToDo: Filter these to Public to allow access to ANONYMOUS too
                    list_fields += [(MOBILE, "phone.value"),
                                    (EMAIL, "email.value"),
                                    ]

                s3db.configure(r.tablename,
                               crud_form = crud_form,
                               list_fields = list_fields,
                               )

            elif r.component_name == "group_membership":
                s3db.pr_group_membership.group_head.label = T("Group Chairperson")

        return result
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive and isinstance(output, dict):
            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output and hasattr(output["item"], "add_class"):
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    if not AUTHENTICATED:
        # Remove RHeader Tabs
        tabs = None
        attr["rheader"] = lambda r: s3db.pr_rheader(r, tabs=tabs)

    return attr

settings.customise_pr_person_controller = customise_pr_person_controller

# -----------------------------------------------------------------------------
# Groups
def chairperson(row):
    """
       Virtual Field to show the chairperson of a group
    """

    if hasattr(row, "pr_group"):
        row = row.pr_group
    try:
        group_id = row.id
    except:
        # not available
        return current.messages["NONE"]

    db = current.db
    mtable = db.pr_group_membership
    ptable = db.pr_person
    query = (mtable.group_id == group_id) & \
            (mtable.group_head == True) & \
            (mtable.person_id == ptable.id)
    chairs = db(query).select(ptable.first_name,
                              ptable.middle_name,
                              ptable.last_name,
                              ptable.id)
    if chairs:
        # Only used in list view so HTML is OK
        if current.auth.is_logged_in():
            controller = "hrm"
        else:
            controller = "pr"
        return ",".join([A(s3_fullname(chair),
                           _href=URL(c=controller, f="person", args=chair.id)).xml()
                         for chair in chairs])
    else:
        return current.messages["NONE"]

# -----------------------------------------------------------------------------
def customise_pr_group_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        from s3 import S3Represent, S3TextFilter, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineComponent

        s3db = current.s3db

        s3db.org_group_team.org_group_id.represent = S3Represent(lookup="org_group",
                                                                 show_link=True)

        crud_form = S3SQLCustomForm("name",
                                    "description",
                                    S3SQLInlineComponent("group_team",
                                                         label = T("Network"),
                                                         fields = [("", "org_group_id")],
                                                         # @ToDo: Make this optional?
                                                         multiple = False,
                                                         ),
                                    "meetings",
                                    "comments",
                                    )

        filter_widgets = [
            S3TextFilter(["name",
                          "description",
                          "comments",
                          "group_team.org_group_id$name",
                          ],
                         label = T("Search"),
                         comment = T("You can search by by group name, description or comments and by network name. You may use % as wildcard. Press 'Search' without input to list all."),
                         #_class = "filter-search",
                         ),
            S3OptionsFilter("group_team.org_group_id",
                            label = T("Network"),
                            #hidden = True,
                            ),
            ]

        # Need to re-do list_fields as get over_written by hrm_group_controller()
        list_fields = [(T("Network"), "group_team.org_group_id"),
                       "name",
                       "description",
                       "meetings",
                       (T("Chairperson"), "chairperson"),
                       "comments",
                       ]

        s3db.configure("pr_group",
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

        s3db.pr_group_membership.group_head.label = T("Group Chairperson")
        if r.component_name == "group_membership":
            from s3layouts import S3AddResourceLink
            s3db.pr_group_membership.person_id.comment = \
                S3AddResourceLink(c="pr", f="person",
                                  title=T("Create Person"),
                                  tooltip=current.messages.AUTOCOMPLETE_HELP)
        #else:
        #    # RHeader wants a simplified version, but don't want inconsistent across tabs
        #    s3db.pr_group_membership.group_head.label = T("Chairperson")

        return True
    s3.prep = custom_prep

    return attr

settings.customise_pr_group_controller = customise_pr_group_controller

# -----------------------------------------------------------------------------
def customise_pr_group_resource(r, tablename):
    """
        Customise pr_group resource (in group & org_group controllers)
            - runs after controller customisation
            - but runs before prep
    """

    s3db = current.s3db

    table = s3db.pr_group

    field = table.group_type
    field.default = 3 # Relief Team, to show up in hrm/group
    field.readable = field.writable = False

    table.name.label = T("Name")
    table.description.label = T("Description")
    table.meetings.readable = table.meetings.writable = True

    # Increase size of widget
    from s3 import s3_comments_widget
    table.description.widget = s3_comments_widget

    from gluon import Field
    table.chairperson = Field.Method("chairperson", chairperson)

    # Format for filter_widgets & imports
    s3db.add_components("pr_group",
                        org_group_team = "group_id",
                        )

    s3db.configure("pr_group",
                   # Redirect to member list when a new group has been created
                   create_next = URL(c="hrm", f="group",
                                     args=["[id]", "group_membership"]),
                   )

settings.customise_pr_group_resource = customise_pr_group_resource

# -----------------------------------------------------------------------------
def pr_contact_postprocess(form):
    """
        Import Organisation/Network RSS Feeds
    """

    s3db = current.s3db
    form_vars = form.vars

    rss_url = form_vars.rsscontact_i_value_edit_0 or \
              form_vars.rsscontact_i_value_edit_none
    if not rss_url:
        if form.record:
            # Update form
            old_rss = form.record.sub_rsscontact
            import json
            data = old_rss = json.loads(old_rss)["data"]
            if data:
                # RSS feed is being deleted, so we should disable it
                old_rss = data[0]["value"]["value"]
                table = s3db.msg_rss_channel
                old = current.db(table.url == old_rss).select(table.channel_id,
                                                              table.enabled,
                                                              limitby = (0, 1)
                                                              ).first()
                if old and old.enabled:
                    s3db.msg_channel_disable("msg_rss_channel", old.channel_id)
                return
        else:
            # Nothing to do :)
            return

    # Check if we already have a channel for this Contact
    db = current.db
    name = form_vars.name
    table = s3db.msg_rss_channel
    name_exists = db(table.name == name).select(table.id,
                                                table.channel_id,
                                                table.enabled,
                                                table.url,
                                                limitby = (0, 1)
                                                ).first()

    no_import = current.request.post_vars.get("rss_no_import", None)

    if name_exists:
        if name_exists.url == rss_url:
            # No change to either Contact Name or URL
            if no_import:
                if name_exists.enabled:
                    # Disable channel (& associated parsers)
                    s3db.msg_channel_disable("msg_rss_channel",
                                             name_exists.channel_id)
                return
            elif name_exists.enabled:
                # Nothing to do :)
                return
            else:
                # Enable channel (& associated parsers)
                s3db.msg_channel_enable("msg_rss_channel",
                                        name_exists.channel_id)
                return

        # Check if we already have a channel for this URL
        url_exists = db(table.url == rss_url).select(table.id,
                                                     table.channel_id,
                                                     table.enabled,
                                                     limitby = (0, 1)
                                                     ).first()
        if url_exists:
            # We have 2 feeds: 1 for the Contact & 1 for the URL
            # Disable the old Contact one and link the URL one to this Contact
            # and ensure active or not as appropriate
            # Name field is unique so rename old one
            name_exists.update_record(name="%s (Old)" % name)
            if name_exists.enabled:
                # Disable channel (& associated parsers)
                s3db.msg_channel_disable("msg_rss_channel",
                                         name_exists.channel_id)
            url_exists.update_record(name=name)
            if no_import:
                if url_exists.enabled:
                    # Disable channel (& associated parsers)
                    s3db.msg_channel_disable("msg_rss_channel",
                                             url_exists.channel_id)
                return
            elif url_exists.enabled:
                # Nothing to do :)
                return
            else:
                # Enable channel (& associated parsers)
                s3db.msg_channel_enable("msg_rss_channel",
                                        url_exists.channel_id)
                return
        else:
            # Update the URL
            name_exists.update_record(url=rss_url)
            if no_import:
                if name_exists.enabled:
                    # Disable channel (& associated parsers)
                    s3db.msg_channel_disable("msg_rss_channel",
                                             name_exists.channel_id)
                return
            elif name_exists.enabled:
                # Nothing to do :)
                return
            else:
                # Enable channel (& associated parsers)
                s3db.msg_channel_enable("msg_rss_channel",
                                        name_exists.channel_id)
                return
    else:
        # Check if we already have a channel for this URL
        url_exists = db(table.url == rss_url).select(table.id,
                                                     table.channel_id,
                                                     table.enabled,
                                                     limitby = (0, 1)
                                                     ).first()
        if url_exists:
            # Either Contact has changed Name or this feed is associated with
            # another Contact
            # - update Feed name
            url_exists.update_record(name=name)
            if no_import:
                if url_exists.enabled:
                    # Disable channel (& associated parsers)
                    s3db.msg_channel_disable("msg_rss_channel",
                                             url_exists.channel_id)
                return
            elif url_exists.enabled:
                # Nothing to do :)
                return
            else:
                # Enable channel (& associated parsers)
                s3db.msg_channel_enable("msg_rss_channel",
                                        url_exists.channel_id)
                return
        elif no_import:
            # Nothing to do :)
            return
        #else:
        #    # Create a new Feed
        #    pass

    # Add RSS Channel
    _id = table.insert(name=name, enabled=True, url=rss_url)
    record = dict(id=_id)
    s3db.update_super(table, record)

    # Enable
    channel_id = record["channel_id"]
    s3db.msg_channel_enable("msg_rss_channel", channel_id)

    # Setup Parser
    table = s3db.msg_parser
    _id = table.insert(channel_id=channel_id,
                       function_name="parse_rss",
                       enabled=True)
    s3db.msg_parser_enable(_id)

    # Check Now
    async = current.s3task.async
    async("msg_poll", args=["msg_rss_channel", channel_id])
    async("msg_parse", args=[channel_id, "parse_rss"])

# -----------------------------------------------------------------------------
# Human Resource Management
# Uncomment to chage the label for 'Staff'
settings.hrm.staff_label = "Contacts"
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to allow Staff & Volunteers to be registered without an Organisation
settings.hrm.org_required = False
# Uncomment to show the Organisation name in HR represents
settings.hrm.show_organisation = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable the use of HR Certificates
settings.hrm.use_certificates = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to enable the use of HR Education
settings.hrm.use_education = False
# Uncomment to disable the use of HR Skills
#settings.hrm.use_skills = False
# Uncomment to disable the use of HR Trainings
settings.hrm.use_trainings = False
# Uncomment to disable the use of HR Description
settings.hrm.use_description = False
# Change the label of "Teams" to "Groups"
settings.hrm.teams = "Groups"
# Custom label for Organisations in HR module
#settings.hrm.organisation_label = "National Society / Branch"
settings.hrm.organisation_label = "Organization"

# -----------------------------------------------------------------------------
def customise_hrm_human_resource_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation == "aadata":
            if not r.component:
                from s3 import S3TextFilter, S3OptionsFilter, S3LocationFilter
                filter_widgets = [
                    S3TextFilter(["person_id$first_name",
                                  "person_id$middle_name",
                                  "person_id$last_name",
                                  ],
                                 label = T("Name"),
                                 ),
                    S3OptionsFilter("organisation_id",
                                    filter = True,
                                    header = "",
                                    hidden = True,
                                    ),
                    S3OptionsFilter("group_person.group_id",
                                    label = T("Network"),
                                    #filter = True,
                                    #header = "",
                                    hidden = True,
                                    ),
                    S3LocationFilter("location_id",
                                     label = T("Location"),
                                     levels = ("L1", "L2", "L3", "L4"),
                                     hidden = True,
                                     ),
                    S3OptionsFilter("site_id",
                                    hidden = True,
                                    ),
                    S3OptionsFilter("training.course_id",
                                    label = T("Training"),
                                    hidden = True,
                                    ),
                    S3OptionsFilter("group_membership.group_id",
                                    label = T("Team"),
                                    filter = True,
                                    header = "",
                                    hidden = True,
                                    ),
                    ]

                s3db = current.s3db
                s3db.configure("hrm_human_resource",
                               filter_widgets = filter_widgets,
                               )

                s3db.pr_contact.access.default = 2 # Primary contacts should be Public
                field = r.table.site_id
                # Don't assume that user is from same org/site as Contacts they create
                field.default = None
                # Use a hierarchical dropdown instead of AC
                field.widget = None
                script = \
'''$.filterOptionsS3({
 'trigger':'organisation_id',
 'target':'site_id',
 'lookupResource':'site',
 'lookupURL':'/%s/org/sites_for_org/',
 'optional':true
})''' % r.application
                s3.jquery_ready.append(script)

        return result
    s3.prep = custom_prep

    return attr

settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

# -----------------------------------------------------------------------------
def customise_hrm_human_resource_resource(r, tablename):
    """
        Customise hrm_human_resource resource (in facility, human_resource, organisation & person controllers)
            - runs after controller customisation
            - but runs before prep
    """

    s3db = current.s3db
    from s3 import S3SQLCustomForm, S3SQLInlineComponent
    crud_form = S3SQLCustomForm("person_id",
                                "organisation_id",
                                "site_id",
                                S3SQLInlineComponent(
                                    "group_person",
                                    label = T("Network"),
                                    link = False,
                                    fields = [("", "group_id")],
                                    multiple = False,
                                    ),
                                "job_title_id",
                                "start_date",
                                )
    list_fields = ["id",
                   "person_id",
                   "job_title_id",
                   "organisation_id",
                   (T("Network"), "group_person.group_id"),
                   (T("Groups"), "person_id$group_membership.group_id"),
                   "site_id",
                   #"site_contact",
                   (T("Email"), "email.value"),
                   (settings.get_ui_label_mobile_phone(), "phone.value"),
                   ]

    s3db.configure("hrm_human_resource",
                   crud_form = crud_form,
                   list_fields = list_fields,
                   )

settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

# -----------------------------------------------------------------------------
def customise_hrm_job_title_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if r.interactive or r.representation == "aadata":
            table = current.s3db.hrm_job_title
            table.organisation_id.readable = table.organisation_id.writable = False
            table.type.readable = table.type.writable = False

        return result
    s3.prep = custom_prep

    return attr

settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

# -----------------------------------------------------------------------------
# Projects
# Use codes for projects (called 'blurb' in NYC)
settings.project.codes = True
# Uncomment this to use settings suitable for detailed Task management
settings.project.mode_task = False
# Uncomment this to use Activities for projects
settings.project.activities = True
# Uncomment this to use Milestones in project/task.
settings.project.milestones = False
# Uncomment this to disable Sectors in projects
settings.project.sectors = False
# Multiple partner organizations
settings.project.multiple_organisations = True

def customise_project_project_controller(**attr):

    s3 = current.response.s3

    # Custom prep
    standard_prep = s3.prep
    def custom_prep(r):
        # Call standard prep
        if callable(standard_prep):
            result = standard_prep(r)
        else:
            result = True

        if not r.component and (r.interactive or r.representation == "aadata"):
            from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
            s3db = current.s3db

            table = r.table
            tablename = "project_project"
            table.code.label = T("Project blurb (max. 100 characters)")
            table.code.max_length = 100
            table.comments.label = T("How people can help")

            script = '''$('#project_project_code').attr('maxlength','100')'''
            s3.jquery_ready.append(script)

            crud_form = S3SQLCustomForm(
                "organisation_id",
                "name",
                "code",
                "description",
                "status_id",
                "start_date",
                "end_date",
                "calendar",
                #"drr.hfa",
                #"objectives",
                "human_resource_id",
                # Activities
                S3SQLInlineComponent(
                    "location",
                    label = T("Location"),
                    fields = [("", "location_id")],
                ),
                # Partner Orgs
                S3SQLInlineComponent(
                    "organisation",
                    name = "partner",
                    label = T("Partner Organizations"),
                    fields = ["organisation_id",
                              "comments", # NB This is labelled 'Role' in DRRPP
                              ],
                    filterby = dict(field = "role",
                    options = "2"
                    )
                ),
                S3SQLInlineComponent(
                    "document",
                    name = "media",
                    label = T("URLs (media, fundraising, website, social media, etc."),
                    fields = ["document_id",
                              "name",
                              "url",
                              "comments",
                              ],
                    filterby = dict(field = "name")
                ),
                S3SQLInlineComponentCheckbox(
                    "activity_type",
                    label = T("Categories"),
                    field = "activity_type_id",
                    cols = 3,
                    # Filter Activity Type by Project
                    filter = {"linktable": "project_activity_type_project",
                              "lkey": "project_id",
                              "rkey": "activity_type_id",
                              },
                ),
                #"budget",
                #"currency",
                "comments",
            )

            from s3 import S3TextFilter, S3OptionsFilter, S3LocationFilter, S3DateFilter
            filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "description",
                              "organisation.name",
                              "organisation.acronym",
                              ],
                             label = T("Name"),
                             _class = "filter-search",
                             ),
                S3OptionsFilter("status_id",
                                label = T("Status"),
                                # Not translateable
                                #represent = "%(name)s",
                                cols = 3,
                                ),
                #S3OptionsFilter("theme_project.theme_id",
                #                label = T("Theme"),
                #                #hidden = True,
                #                ),
                S3LocationFilter("location.location_id",
                                 label = T("Location"),
                                 levels = ("L1", "L2", "L3", "L4"),
                                 #hidden = True,
                                 ),
                # @ToDo: Widget to handle Start & End in 1!
                S3DateFilter("start_date",
                             label = T("Start Date"),
                             hide_time = True,
                             #hidden = True,
                             ),
                S3DateFilter("end_date",
                             label = T("End Date"),
                             hide_time = True,
                             #hidden = True,
                             ),
                ]

            list_fields = ["id",
                           "name",
                           "code",
                           "organisation_id",
                           "start_date",
                           "end_date",
                           (T("Locations"), "location.location_id"),
                           ]

            s3db.configure(tablename,
                           crud_form = crud_form,
                           filter_widgets = filter_widgets,
                           list_fields = list_fields,
                           )

        return result
    s3.prep = custom_prep

    return attr

settings.customise_project_project_controller = customise_project_project_controller

# -----------------------------------------------------------------------------
# Requests Management
settings.req.req_type = ["People", "Stock"]#, "Summary"]
settings.req.prompt_match = False
#settings.req.use_commit = False
settings.req.requester_optional = True
settings.req.date_writable = False
settings.req.item_quantities_writable = True
settings.req.skill_quantities_writable = True
settings.req.items_ask_purpose = False
#settings.req.use_req_number = False
# Label for Requester
settings.req.requester_label = "Site Contact"
# Filter Requester as being from the Site
settings.req.requester_from_site = True
# Label for Inventory Requests
settings.req.type_inv_label = "Supplies"
# Uncomment to enable Summary 'Site Needs' tab for Offices/Facilities
settings.req.summary = True

# -----------------------------------------------------------------------------
def req_req_postprocess(form):
    """
        Runs after crud_form completes
        - creates a cms_post in the newswire
        - @ToDo: Send out Tweets
    """

    req_id = form.vars.id

    db = current.db
    s3db = current.s3db
    rtable = s3db.req_req

    # Read the full record
    row = db(rtable.id == req_id).select(rtable.type,
                                         rtable.site_id,
                                         rtable.requester_id,
                                         rtable.priority,
                                         rtable.date_required,
                                         rtable.purpose,
                                         rtable.comments,
                                         limitby=(0, 1)
                                         ).first()

    # Build Title & Body from the Request details
    priority = rtable.priority.represent(row.priority)
    date_required = row.date_required
    if date_required:
        date = rtable.date_required.represent(date_required)
        title = "%(priority)s by %(date)s" % dict(priority=priority,
                                                  date=date)
    else:
        title = priority
    body = row.comments
    if row.type == 1:
        # Items
        ritable = s3db.req_req_item
        items = db(ritable.req_id == req_id).select(ritable.item_id,
                                                    ritable.item_pack_id,
                                                    ritable.quantity)
        item_represent = s3db.supply_item_represent
        pack_represent = s3db.supply_item_pack_represent
        for item in items:
            item = "%s %s %s" % (item.quantity,
                                 pack_represent(item.item_pack_id),
                                 item_represent(item.item_id))
            body = "%s\n%s" % (item, body)
    else:
        # Skills
        body = "%s\n%s" % (row.purpose, body)
        rstable = s3db.req_req_skill
        skills = db(rstable.req_id == req_id).select(rstable.skill_id,
                                                     rstable.quantity)
        skill_represent = s3db.hrm_multi_skill_represent
        for skill in skills:
            item = "%s %s" % (skill.quantity, skill_represent(skill.skill_id))
            body = "%s\n%s" % (item, body)

    # Lookup series_id
    stable = s3db.cms_series
    try:
        series_id = db(stable.name == "Request").select(stable.id,
                                                        cache=s3db.cache,
                                                        limitby=(0, 1)
                                                        ).first().id
    except:
        # Prepop hasn't been run
        series_id = None

    # Location is that of the site
    otable = s3db.org_site
    location_id = db(otable.site_id == row.site_id).select(otable.location_id,
                                                           limitby=(0, 1)
                                                           ).first().location_id
    # Create Post
    ptable = s3db.cms_post
    _id = ptable.insert(series_id=series_id,
                        title=title,
                        body=body,
                        location_id=location_id,
                        person_id=row.requester_id,
                        )
    record = dict(id=_id)
    s3db.update_super(ptable, record)

    # Add source link
    url = "%s%s" % (settings.get_base_public_url(),
                    URL(c="req", f="req", args=req_id))
    s3db.doc_document.insert(doc_id=record["doc_id"],
                             url=url,
                             )

# -----------------------------------------------------------------------------
def customise_req_req_resource(r, tablename):

    from s3layouts import S3AddResourceLink
    current.s3db.req_req.site_id.comment = \
        S3AddResourceLink(c="org", f="facility",
                          vars = dict(child="site_id"),
                          title=T("Create Facility"),
                          tooltip=current.messages.AUTOCOMPLETE_HELP)

    current.response.s3.req_req_postprocess = req_req_postprocess

    if not r.component and r.method in ("create", "update"):
        script = \
'''$('#req_req_site_id').change(function(){
var url=$('#person_add').attr('href')
url=url.split('?')
var q=S3.queryString.parse(url[1])
q['(site)']=$(this).val()
url=url[0]+'?'+S3.queryString.stringify(q)
$('#person_add').attr('href',url)})'''
        current.response.s3.jquery_ready.append(script)

settings.customise_req_req_resource = customise_req_req_resource

# -----------------------------------------------------------------------------
# Comment/uncomment modules here to disable/enable them
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
    ("admin", Storage(
            name_nice = T("Admin"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
    ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
    ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
    # Uncomment to enable internal support requests
    #("support", Storage(
    #        name_nice = T("Support"),
    #        #description = "Support Requests",
    #        restricted = True,
    #        module_type = None  # This item is handled separately for the menu
    #    )),
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 9,     # 8th item in the menu
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
    ("org", Storage(
            name_nice = T("Locations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 4
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Contacts"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 3,
        )),
    #("vol", Storage(
    #        name_nice = T("Volunteers"),
    #        #description = "Human Resources Management",
    #        restricted = True,
    #        module_type = 2,
    #    )),
    ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          module_type = 10,
      )),
    ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = None,
        )),
    ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
    ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
    ("inv", Storage(
            name_nice = T("Inventory"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 10
        )),
    #("proc", Storage(
    #        name_nice = T("Procurement"),
    #        #description = "Ordering & Purchasing of Goods & Services",
    #        restricted = True,
    #        module_type = 10
    #    )),
    ("asset", Storage(
            name_nice = T("Assets"),
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 10,
        )),
    # Vehicle depends on Assets
    #("vehicle", Storage(
    #        name_nice = T("Vehicles"),
    #        #description = "Manage Vehicles",
    #        restricted = True,
    #        module_type = 10,
    #    )),
    ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 1,
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 10
        )),
    ("assess", Storage(
            name_nice = T("Assessments"),
            #description = "Rapid Assessments & Flexible Impact Assessments",
            restricted = True,
            module_type = 5,
        )),
    ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
    ("survey", Storage(
            name_nice = T("Surveys"),
            #description = "Create, enter, and manage surveys.",
            restricted = True,
            module_type = 5,
        )),
    #("cr", Storage(
    #        name_nice = T("Shelters"),
    #        #description = "Tracks the location, capacity and breakdown of victims in Shelters",
    #        restricted = True,
    #        module_type = 10
    #    )),
    #("dvr", Storage(
    #       name_nice = T("Disaster Victim Registry"),
    #       #description = "Allow affected individuals & households to register to receive compensation and distributions",
    #       restricted = False,
    #       module_type = 10,
    #   )),
    #("member", Storage(
    #       name_nice = T("Members"),
    #       #description = "Membership Management System",
    #       restricted = True,
    #       module_type = 10,
    #   )),
    # @ToDo: Rewrite in a modern style
    #("budget", Storage(
    #        name_nice = T("Budgeting Module"),
    #        #description = "Allows a Budget to be drawn up",
    #        restricted = True,
    #        module_type = 10
    #    )),
    # @ToDo: Port these Assessments to the Survey module
    #("building", Storage(
    #        name_nice = T("Building Assessments"),
    #        #description = "Building Safety Assessments",
    #        restricted = True,
    #        module_type = 10,
    #    )),
])
