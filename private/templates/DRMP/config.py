# -*- coding: utf-8 -*-

from gluon import current, URL
from gluon.html import *
from gluon.storage import Storage
from gluon.validators import IS_NULL_OR

from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3layouts import S3AddResourceLink
from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent
from s3.s3fields import S3Represent
from s3.s3resource import S3FieldSelector
from s3.s3utils import s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_LOCATION_SELECTOR2, IS_ONE_OF
from s3.s3widgets import S3LocationAutocompleteWidget, S3LocationSelectorWidget2

T = current.T
settings = current.deployment_settings

"""
    Template settings for DRM Portal
"""

# =============================================================================
# System Settings
# -----------------------------------------------------------------------------
# Authorization Settings
settings.auth.registration_requires_approval = True
settings.auth.registration_requires_verification = True
settings.auth.registration_requests_organisation = True
settings.auth.registration_organisation_required = True
settings.auth.registration_requests_site = False

settings.auth.registration_link_user_to = {"staff": T("Staff")}

settings.auth.record_approval = False

# -----------------------------------------------------------------------------
# Security Policy
settings.security.policy = 3 # Controllers
settings.security.map = True

# Owner Entity
settings.auth.person_realm_human_resource_site_then_org = False

# -----------------------------------------------------------------------------
# Pre-Populate
settings.base.prepopulate = ["DRMP"]

settings.base.system_name = T("Disaster Risk Management Portal")
settings.base.system_name_short = T("DRMP")

# -----------------------------------------------------------------------------
# Theme (folder to use for views/layout.html)
settings.base.theme = "DRMP"
settings.ui.formstyle_row = "bootstrap"
settings.ui.formstyle = "bootstrap"
#settings.gis.map_height = 600
#settings.gis.map_width = 854

# -----------------------------------------------------------------------------
# L10n (Localization) settings
settings.L10n.languages = OrderedDict([
    ("en", "English"),
    #("tet", "Tetum"),
])
# Default Language
settings.L10n.default_language = "en"
# Default timezone for users
settings.L10n.utc_offset = "UTC +0900"
# Number formats (defaults to ISO 31-0)
# Decimal separator for numbers (defaults to ,)
settings.L10n.decimal_separator = "."
# Thousands separator for numbers (defaults to space)
settings.L10n.thousands_separator = ","

# Restrict the Location Selector to just certain countries
# NB This can also be over-ridden for specific contexts later
# e.g. Activities filtered to those of parent Project
settings.gis.countries = ["TL"]

# Until Validation Errors fixed in LocationSelector2
settings.gis.check_within_parent_boundaries = False

# -----------------------------------------------------------------------------
# Finance settings
settings.fin.currencies = {
    "AUD" : T("Australian Dollars"),
    "EUR" : T("Euros"),
    "GBP" : T("Great British Pounds"),
    "USD" : T("United States Dollars"),
}

# -----------------------------------------------------------------------------
# Enable this for a UN-style deployment
#settings.ui.cluster = True
# Enable this to use the label 'Camp' instead of 'Shelter'
settings.ui.camp = True

# -----------------------------------------------------------------------------
# Save Search Widget
settings.save_search.widget = False

# Uncomment to restrict the export formats available
settings.ui.export_formats = ["xls"]

settings.ui.update_label = "Edit"

# =============================================================================
# Module Settings

# -----------------------------------------------------------------------------
# Human Resource Management
settings.hrm.staff_label = "Contacts"
# Uncomment to allow Staff & Volunteers to be registered without an email address
settings.hrm.email_required = False
# Uncomment to show the Organisation name in HR represents
settings.hrm.show_organisation = True
# Uncomment to disable Staff experience
settings.hrm.staff_experience = False
# Uncomment to disable the use of HR Credentials
settings.hrm.use_credentials = False
# Uncomment to disable the use of HR Skills
settings.hrm.use_skills = False
# Uncomment to disable the use of HR Teams
settings.hrm.use_teams = False

# -----------------------------------------------------------------------------
# Org
settings.org.site_label = "Office"

# -----------------------------------------------------------------------------
# Project
# Uncomment this to use multiple Organisations per project
settings.project.multiple_organisations = True

# -----------------------------------------------------------------------------
def location_represent(id, row=None):
    """
        Custom Representation of Locations
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        table = current.s3db.gis_location
        row = current.db(table.id == id).select(table.L1,
                                                table.L2,
                                                table.L3,
                                                limitby=(0, 1)).first()

    represent = "%s | %s | %s" % (s3_unicode(row.L1) if row.L1 else "",
                                  s3_unicode(row.L2) if row.L2 else "",
                                  s3_unicode(row.L3) if row.L3 else "",
                                  )
    return represent

# -----------------------------------------------------------------------------
def customize_cms_post(**attr):
    """
        Customize cms_post controller
    """

    s3 = current.response.s3

    # Custom PreP
    standard_prep = s3.prep
    def custom_prep(r):
        if r.interactive:
            s3db = current.s3db
            table = s3db.cms_post

            field = table.series_id
            field.label = T("Type")
            field.readable = field.writable = True
            #field.requires = field.requires.other
            #field = table.name
            #field.readable = field.writable = False
            #field = table.title
            #field.readable = field.writable = False
            field = table.avatar
            field.default = True
            #field.readable = field.writable = False
            field = table.replies
            field.default = False
            #field.readable = field.writable = False
            field = table.location_id
            field.label = ""
            field.represent = location_represent
            field.requires = IS_NULL_OR(
                                IS_LOCATION_SELECTOR2(levels=["L1", "L2", "L3"])
                             )
            field.widget = S3LocationSelectorWidget2(levels=["L1", "L2", "L3"])
            table.created_by.represent = s3_auth_user_represent_name
            field = table.body
            field.label = T("Text")
            field.widget = None
            #table.comments.readable = table.comments.writable = False

            # Filter from a Profile page?"
            event_id = current.request.get_vars.get("(event)", None)
            if event_id:
                crud_form = S3SQLCustomForm(
                    "series_id",
                    "body",
                    "location_id",
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )
                def create_onaccept(form):
                    table = current.s3db.event_event_post
                    table.insert(event_id=event_id, post_id=form.vars.id)

                s3db.configure("cms_post",
                               create_onaccept = create_onaccept, 
                               )
            else:
                crud_form = S3SQLCustomForm(
                    "series_id",
                    "body",
                    "location_id",
                    S3SQLInlineComponent(
                        "event_post",
                        label = T("Disaster(s)"),
                        multiple = False,
                        fields = ["event_id"],
                        orderby = "event_id$name",
                    ),
                    S3SQLInlineComponent(
                        "document",
                        name = "file",
                        label = T("Files"),
                        fields = ["file",
                                  #"comments",
                                  ],
                    ),
                )

            # Return to List view after create/update/delete
            url_next = URL(c="default", f="index", args="updates")

            list_fields = ["series_id",
                           "location_id",
                           "created_on",
                           "body",
                           "created_by",
                           "created_by$organisation_id",
                           "document.file",
                           "event_post.event_id",
                           ]

            s3db.configure("cms_post",
                           create_next = url_next,
                           delete_next = url_next,
                           update_next = url_next,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )

            #crud_settings = current.response.s3.crud
            #crud_settings.formstyle = "bootstrap"
            #crud_settings.submit_button = T("Save changes")
            # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
            #crud_settings.submit_style = "btn btn-primary"

            s3.cancel = True

        # Call standard prep
        # (Done afterwards to ensure type field gets hidden)
        if callable(standard_prep):
            result = standard_prep(r)
            if not result:
                return False

        return True
    s3.prep = custom_prep

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive:
            if "form" in output:
                output["form"].add_class("cms_post")
            elif "item" in output:
                output["item"].add_class("cms_post")

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_cms_post = customize_cms_post

# -----------------------------------------------------------------------------
def render_events(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Events on the Disaster Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "event_event.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["event_event.name"]
    date = record["event_event.zero_hour"]
    closed = raw["event_event.closed"]
    event_type = record["event_event_type.name"]

    if closed:
        edit_bar = DIV()
    else:
        item_class = "%s disaster" % item_class

        permit = current.auth.s3_has_permission
        table = resource.table
        if permit("update", table, record_id=record_id):
            edit_btn = A(I(" ", _class="icon icon-edit"),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "update.popup"],
                                   vars={"refresh": listid,
                                         "record": record_id}),
                         _class="s3_modal",
                         _title=current.response.s3.crud_strings.event_event.title_update,
                         )
        else:
            edit_btn = ""
        if permit("delete", table, record_id=record_id):
            delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                           _class="dl-item-delete",
                          )
        else:
            delete_btn = ""
        edit_bar = DIV(edit_btn,
                       delete_btn,
                       _class="edit-bar fright",
                       )

    # Render the item
    item = DIV(DIV(A(IMG(_class="media-object",
                         _src=URL(c="static",
                                  f="themes",
                                  args=["DRMP", "img", "%s.png" % event_type]),
                         ),
                     _class="pull-left",
                     _href="#",
                     ),
  		           edit_bar,
                   DIV(A(H5(name,
                            _class="media-heading"),
                         SPAN(date,
                              _class="date-title",
                              ),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "profile"]),
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def render_profile_posts(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for CMS Posts on the Profile pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "cms_post.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    series = record["cms_post.series_id"]
    date = record["cms_post.created_on"]
    body = record["cms_post.body"]
    event_id = raw["event_event_post.event_id"]
    location = record["cms_post.location_id"]
    location_id = raw["cms_post.location_id"]
    location_url = URL(c="gis", f="location", args=[location_id])
    author = record["cms_post.created_by"]
    author_id = raw["cms_post.created_by"]
    organisation = record["auth_user.organisation_id"]
    organisation_id = raw["auth_user.organisation_id"]
    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])

    db = current.db
    s3db = current.s3db
    ltable = s3db.pr_person_user
    ptable = db.pr_person
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = db(query).select(ptable.id,
                           limitby=(0, 1)
                           ).first()
    if row:
        person_url = URL(c="hrm", f="person", args=[row.id])
    else:
        person_url = "#"
    author = A(author,
               _href=person_url,
               )

    # Use Personal Avatar
    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    #avatar = s3_avatar_represent(author_id,
    #                             _class="media-object")
    #avatar = A(avatar,
    #           _href=person_url,
    #           _class="pull-left",
    #           )

    # Use Organisation Logo
    otable = db.org_organisation
    row = db(otable.id == organisation_id).select(otable.logo,
                                                  limitby=(0, 1)
                                                  ).first()
    if row and row.logo:
        logo = URL(c="default", f="download", args=[row.logo])
    else:
        logo = ""
    avatar = IMG(_src=logo,
                 _height=50,
                 _width=50,
                 #_style="padding-right:5px;",
                 _class="media-object")
    avatar = A(avatar,
               _href=org_url,
               _class="pull-left",
               )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = db.cms_post
    if permit("update", table, record_id=record_id):
        vars = {"refresh": listid,
                "record": record_id,
                "~.series_id$name": series,
                }
        f = current.request.function
        if f == "event" and event_id:
            vars["(event)"] = event_id
        if f == "location" and location_id:
            vars["(location)"] = location_id
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="post",
                               args=[record_id, "update.popup"],
                               vars=vars),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.cms_post.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except IOError:
                doc_name = current.messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(I(_class="icon-file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(I(_class="icon-paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    # Render the item
    class SMALL(DIV):
        tag = "small"

    item = DIV(DIV(DIV(avatar,
                       P(SMALL(" ", author, " ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               ),
                         _class="citation"),
                       _class="span1"),
                   DIV(SPAN(A(location,
                              _href=location_url,
                              ),
                            _class="location-title"),
                        " ",
                        SPAN(date,
                             _class="date-title"),
                        edit_bar,
                        P(body,
                          _class="card_comments"),
                        docs,
                       _class="span5 card-details"),
                   _class="row",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def customize_event_event(**attr):
    """
        Customize event_event controller
        - Profile Page
    """

    s3db = current.s3db
    s3 = current.response.s3

    # Customise the cms_post table as that is used for the widgets
    customize_cms_post()

    # Represent used in rendering
    current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

    # Load normal Model
    table = s3db.event_event

    alerts_widget = dict(label = "Alerts",
                         title_create = "Add New Alert",
                         type = "datalist",
                         tablename = "cms_post",
                         context = "event",
                         filter = S3FieldSelector("series_id$name") == "Alert",
                         icon = "icon-alert",
                         marker = "alert",
                         list_layout = render_profile_posts,
                         )
    map_widget = dict(label = "Location",
                      type = "map",
                      context = "event",
                      icon = "icon-map-marker",
                      height = 383,
                      width = 568,
                      )
    incidents_widget = dict(label = "Incidents",
                            title_create = "Add New Incident",
                            type = "datalist",
                            tablename = "cms_post",
                            context = "event",
                            filter = S3FieldSelector("series_id$name") == "Incident",
                            icon = "icon-warning-sign",
                            marker = "incident",
                            list_layout = render_profile_posts,
                            )
    assessments_widget = dict(label = "Assessments",
                              title_create = "Add New Assessment",
                              type = "datalist",
                              tablename = "cms_post",
                              context = "event",
                              filter = S3FieldSelector("series_id$name") == "Assessment",
                              icon = "icon-info-sign",
                              marker = "assessment",
                              list_layout = render_profile_posts,
                              )
    activities_widget = dict(label = "Activities",
                             title_create = "Add New Activity",
                             type = "datalist",
                             tablename = "cms_post",
                             context = "event",
                             filter = S3FieldSelector("series_id$name") == "Activity",
                             icon = "icon-activity",
                             marker = "activity",
                             list_layout = render_profile_posts,
                             )
    reports_widget = dict(label = "Reports",
                          title_create = "Add New Report",
                          type = "datalist",
                          tablename = "cms_post",
                          context = "event",
                          filter = S3FieldSelector("series_id$name") == "Report",
                          icon = "icon-report",
                          marker = "report",
                          list_layout = render_profile_posts,
                          )
    comments_widget = dict(label = "Comments",
                           type = "comments",
                           icon = "icon-comments-alt",
                           colspan = 2,
                           )
    s3db.configure("event_event",
                   create_next = URL(c="event", f="event",
                                     args=["[id]", "profile"]),
                   # We want the Create form to be in a modal, not inline, for consistency
                   listadd = False,
                   list_layout = render_events,
                   profile_widgets=[alerts_widget,
                                    map_widget,
                                    incidents_widget,
                                    assessments_widget,
                                    activities_widget,
                                    reports_widget,
                                    #comments_widget,
                                    ],
                   )

    ADD_EVENT = T("New Disaster")
    s3.crud_strings["event_event"] = Storage(
        title_create = ADD_EVENT,
        title_display = T("Disaster Details"),
        title_list = T("Disasters"),
        title_update = T("Edit Disaster"),
        title_search = T("Search Disasters"),
        subtitle_create = T("Add New Disaster"),
        label_list_button = T("List Disasters"),
        label_create_button = ADD_EVENT,
        label_delete_button = T("Delete Disaster"),
        msg_record_created = T("Disaster added"),
        msg_record_modified = T("Disaster updated"),
        msg_record_deleted = T("Disaster deleted"),
        msg_list_empty = T("No Disasters currently registered"))

    #crud_settings = s3.crud
    #crud_settings.formstyle = "bootstrap"
    #crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive and \
           current.auth.s3_has_permission("create", r.table):
            # Insert a Button to Create New in Modal
            output["showadd_btn"] = A(I(_class="icon icon-plus-sign big-add"),
                                      _href=URL(c="event", f="event",
                                                args=["create.popup"],
                                                vars={"refresh":"datalist"}),
                                      _class="btn btn-primary s3_modal",
                                      _role="button",
                                      _title=T("Add New Disaster"),
                                      )

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_event_event = customize_event_event

# -----------------------------------------------------------------------------
def render_locations(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Locations on the Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "gis_location.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = raw["gis_location.name"]
    level = raw["gis_location.level"]
    L1 = raw["gis_location.L1"]
    L2 = raw["gis_location.L2"]
    L3 = raw["gis_location.L3"]

    if level == "L1":
        represent = name
    if level == "L2":
        represent = "%s (%s)" % (name, L1)
    elif level == "L3":
        represent = "%s (%s, %s)" % (name, L2, L1)
    else:
        # L0 or specific
        represent = name

    permit = current.auth.s3_has_permission
    table = current.db.gis_location
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="gis", f="location",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.gis_location.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(A(represent,
                     _href=URL(c="gis", f="location",
                               args=[record_id, "profile"]),
                     ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def customize_gis_location(**attr):
    """
        Customize gis_location controller
        - Profile Page
    """

    s3db = current.s3db
    s3 = current.response.s3

    # Customise the cms_post table as that is used for the widgets
    customize_cms_post()

    # Represent used in rendering
    current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

    # Load normal Model
    table = s3db.gis_location

    alerts_widget = dict(label = "Alerts",
                         title_create = "Add New Alert",
                         type = "datalist",
                         tablename = "cms_post",
                         context = "location",
                         filter = S3FieldSelector("series_id$name") == "Alert",
                         icon = "icon-alert",
                         marker = "alert",
                         list_layout = render_profile_posts,
                         )
    map_widget = dict(label = "Location",
                      type = "map",
                      context = "location",
                      icon = "icon-map-marker",
                      height = 383,
                      width = 568,
                      )
    incidents_widget = dict(label = "Incidents",
                            title_create = "Add New Incident",
                            type = "datalist",
                            tablename = "cms_post",
                            context = "location",
                            filter = S3FieldSelector("series_id$name") == "Incident",
                            icon = "icon-warning-sign",
                            marker = "incident",
                            list_layout = render_profile_posts,
                            )
    assessments_widget = dict(label = "Assessments",
                              title_create = "Add New Assessment",
                              type = "datalist",
                              tablename = "cms_post",
                              context = "location",
                              filter = S3FieldSelector("series_id$name") == "Assessment",
                              icon = "icon-info-sign",
                              marker = "assessment",
                              list_layout = render_profile_posts,
                              )
    activities_widget = dict(label = "Activities",
                             title_create = "Add New Activity",
                             type = "datalist",
                             tablename = "cms_post",
                             context = "location",
                             filter = S3FieldSelector("series_id$name") == "Activity",
                             icon = "icon-activity",
                             marker = "activity",
                             list_layout = render_profile_posts,
                             )
    reports_widget = dict(label = "Reports",
                          title_create = "Add New Report",
                          type = "datalist",
                          tablename = "cms_post",
                          context = "location",
                          filter = S3FieldSelector("series_id$name") == "Report",
                          icon = "icon-report",
                          marker = "report",
                          list_layout = render_profile_posts,
                          )
    comments_widget = dict(label = "Comments",
                           type = "comments",
                           icon = "icon-comments-alt",
                           colspan = 2,
                           )
    s3db.configure("gis_location",
                   list_layout = render_locations,
                   profile_widgets=[alerts_widget,
                                    map_widget,
                                    incidents_widget,
                                    assessments_widget,
                                    activities_widget,
                                    reports_widget,
                                    #comments_widget,
                                    ],
                   )

    #crud_settings = s3.crud
    #crud_settings.formstyle = "bootstrap"
    #crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    return attr

settings.ui.customize_gis_location = customize_gis_location

# -----------------------------------------------------------------------------
def render_organisations(listid, resource, rfields, record, **attr):
    """
        Custom dataList item renderer for Organisations on the Stakeholder Selection Page

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "org_organisation.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    name = record["org_organisation.name"]
    logo = raw["org_organisation.logo"]
    #address = record["office.location_id$addr_street"]

    org_url = URL(c="org", f="organisation", args=[record_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    permit = current.auth.s3_has_permission
    table = current.db.org_organisation
    if permit("update", table, record_id=record_id):
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="org", f="organisation",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.response.s3.crud_strings.org_organisation.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-remove-sign"),
                       _class="dl-item-delete",
                      )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(logo,
                   DIV(A(name,
                         _href=org_url,
                         ),
                       #address,
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def customize_org_organisation(**attr):
    """
        Customize org_organisation controller
        - Profile Page
    """

    s3db = current.s3db
    s3 = current.response.s3

    # Customise the cms_post table as that is used for the widgets
    customize_cms_post()

    # Represent used in rendering
    current.auth.settings.table_user.organisation_id.represent = s3db.org_organisation_represent

    # Load normal Model
    table = s3db.org_organisation

    alerts_widget = dict(label = "Alerts",
                         title_create = "Add New Alert",
                         type = "datalist",
                         tablename = "cms_post",
                         context = "organisation",
                         filter = S3FieldSelector("series_id$name") == "Alert",
                         icon = "icon-alert",
                         marker = "alert",
                         list_layout = render_profile_posts,
                         )
    map_widget = dict(label = "Location",
                      type = "map",
                      context = "organisation",
                      icon = "icon-map-marker",
                      height = 383,
                      width = 568,
                      )
    incidents_widget = dict(label = "Incidents",
                            title_create = "Add New Incident",
                            type = "datalist",
                            tablename = "cms_post",
                            context = "organisation",
                            filter = S3FieldSelector("series_id$name") == "Incident",
                            icon = "icon-warning-sign",
                            marker = "incident",
                            list_layout = render_profile_posts,
                            )
    assessments_widget = dict(label = "Assessments",
                              title_create = "Add New Assessment",
                              type = "datalist",
                              tablename = "cms_post",
                              context = "organisation",
                              filter = S3FieldSelector("series_id$name") == "Assessment",
                              icon = "icon-info-sign",
                              marker = "assessment",
                              list_layout = render_profile_posts,
                              )
    activities_widget = dict(label = "Activities",
                             title_create = "Add New Activity",
                             type = "datalist",
                             tablename = "cms_post",
                             context = "organisation",
                             filter = S3FieldSelector("series_id$name") == "Activity",
                             icon = "icon-activity",
                             marker = "activity",
                             list_layout = render_profile_posts,
                             )
    reports_widget = dict(label = "Reports",
                          title_create = "Add New Report",
                          type = "datalist",
                          tablename = "cms_post",
                          context = "organisation",
                          filter = S3FieldSelector("series_id$name") == "Report",
                          icon = "icon-report",
                          marker = "report",
                          list_layout = render_profile_posts,
                          )
    comments_widget = dict(label = "Comments",
                           type = "comments",
                           icon = "icon-comments-alt",
                           colspan = 2,
                           )
    s3db.configure("org_organisation",
                   list_fields = ["id",
                                  "name",
                                  "logo",
                                  ],
                   list_layout = render_organisations,
                   profile_widgets=[alerts_widget,
                                    map_widget,
                                    incidents_widget,
                                    assessments_widget,
                                    activities_widget,
                                    reports_widget,
                                    #comments_widget,
                                    ],
                   )

    ADD_ORGANISATION = T("New Stakeholder")
    s3.crud_strings["org_organisation"] = Storage(
        title_create = ADD_ORGANISATION,
        title_display = T("Stakeholder Details"),
        title_list = T("Stakeholders"),
        title_update = T("Edit Stakeholder"),
        title_search = T("Search Stakeholders"),
        subtitle_create = T("Add New Stakeholder"),
        label_list_button = T("List Stakeholders"),
        label_create_button = ADD_ORGANISATION,
        label_delete_button = T("Delete Stakeholder"),
        msg_record_created = T("Stakeholder added"),
        msg_record_modified = T("Stakeholder updated"),
        msg_record_deleted = T("Stakeholder deleted"),
        msg_list_empty = T("No Stakeholders currently registered"))

    #crud_settings = s3.crud
    #crud_settings.formstyle = "bootstrap"
    #crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"

    return attr

settings.ui.customize_org_organisation = customize_org_organisation

# -----------------------------------------------------------------------------
def customize_project_project(**attr):
    """
        Customize project_project controller
    """

    s3 = current.response.s3
    s3db = current.s3db
    db = current.db

    tablename = "project_project"
    table = s3db.project_project
    
    # Remove rheader
    attr["rheader"] = None
    
    # Configure fields 
    table.human_resource_id.label = T("Focal Person")
    table.budget.label = "%s (USD)" % T("Budget")
    # Better in column label & otherwise this construction loses thousands separators
    #table.budget.represent = lambda value: "%d USD" % value

    # Project Locations must be districts
    ltable = s3db.project_location
    ltable.location_id.label = ""
    ltable.location_id.represent = S3Represent(lookup="gis_location")
    ltable.location_id.requires = IS_ONE_OF(db, "gis_location.id",
                                            S3Represent(lookup="gis_location"),
                                            sort = True,
                                            filterby = "level",
                                            filter_opts = ["L1"]
                                            )
    # Don't add new Locations here
    ltable.location_id.comment = None
    # Simple dropdown
    ltable.location_id.widget = None

    crud_form = S3SQLCustomForm(
        "name",
        "organisation_id",
        S3SQLInlineComponent(
            "location",
            label = T("Districts"),
            fields = ["location_id"],
            orderby = "location_id$name",
            render_list = True
        ),
        "human_resource_id",
        "start_date",
        "end_date",
        # Partner Orgs
        S3SQLInlineComponent(
            "organisation",
            name = "partner",
            label = T("Partner Organisations"),
            fields = ["organisation_id",
                      ],
            filterby = dict(field = "role",
                            options = "2"
                            )
        ),
        # Donors
        S3SQLInlineComponent(
            "organisation",
            name = "donor",
            label = T("Donor(s)"),
            fields = ["organisation_id", "amount", "currency"],
            filterby = dict(field = "role",
                            options = "3"
                            )
        ),
        "budget",
        "comments",
    )

    list_fields = ["name",
                   "organisation_id",
                   "human_resource_id",
                   "start_date",
                   "end_date",
                   "budget",
                   ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   list_fields = list_fields)

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="project", f="project",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="project", f="project",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="project", f="project",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("project_project")
            elif "item" in output:
                output["item"].add_class("project_project")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_project_project = customize_project_project

# -----------------------------------------------------------------------------
def customize_org_resource(**attr):
    """
        Customize org_resource controller
    """

    s3 = current.response.s3

    table = current.s3db.org_resource
    
    # Configure fields
    #table.site_id.readable = table.site_id.readable = False
    table.location_id.requires = IS_ONE_OF(current.db, "gis_location.id",
                                           S3Represent(lookup="gis_location"),
                                           sort = True,
                                           filterby = "level",
                                           filter_opts = ["L1"]
                                           )
    table.location_id.widget = None
    
    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="org", f="resource",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="org", f="resource",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="org", f="resource",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("org_resource")
            elif "item" in output:
                output["item"].add_class("org_resource")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_org_resource = customize_org_resource

# -----------------------------------------------------------------------------
def customize_org_office(**attr):
    """
        Customize org_office controller
    """

    s3 = current.response.s3

    table = current.s3db.org_office
    
    # Configure fields
    table.code.readable = table.code.writable = False
    table.office_type_id.readable = table.office_type_id.writable = False
    table.phone1.readable = table.phone1.writable = False
    table.phone2.readable = table.phone2.writable = False
    table.email.readable = table.email.writable = False
    table.fax.readable = table.fax.writable = False
    table.location_id.requires = IS_ONE_OF(current.db, "gis_location.id",
                                           S3Represent(lookup="gis_location"),
                                           sort = True,
                                           filterby = "level",
                                           filter_opts = ["L1"]
                                           )
    table.location_id.widget = None
    
    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="org", f="office",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="org", f="office",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="org", f="office",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("org_office")
            elif "item" in output:
                output["item"].add_class("org_office")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_org_office = customize_org_office

# -----------------------------------------------------------------------------
def customize_pr_person(**attr):
    """
        Customize pr_person controller
    """

    s3db = current.s3db
    s3 = current.response.s3

    tablename = "pr_person"
    table = s3db.pr_person
    
    # CRUD Strings
    ADD_CONTACT = T("Add New Contact")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Contact"),
        title_display = T("Contact Details"),
        title_list = T("Contacts"),
        title_update = T("Edit Contact Details"),
        title_search = T("Search Contacts"),
        subtitle_create = ADD_CONTACT,
        label_list_button = T("List Contacts"),
        label_create_button = ADD_CONTACT,
        label_delete_button = T("Delete Contact"),
        msg_record_created = T("Contact added"),
        msg_record_modified = T("Contact details updated"),
        msg_record_deleted = T("Contact deleted"),
        msg_list_empty = T("No Contacts currently registered"))

    MOBILE = settings.get_ui_label_mobile_phone()
    EMAIL = T("Email")

    htable = s3db.hrm_human_resource
    htable.organisation_id.widget = None
    field = htable.site_id
    represent = S3Represent(lookup="org_site")
    field.represent = represent
    field.requires = IS_ONE_OF(current.db, "org_site.site_id",
                               represent,
                               orderby = "org_site.name")
    field.comment = S3AddResourceLink(c="org", f="office",
                                      vars={"child": "site_id"},
                                      label=T("Add New Office"),
                                      title=T("Office"),
                                      tooltip=T("If you don't see the Office in the list, you can add a new one by clicking link 'Add New Office'."))

    s3db.pr_contact.value.label = ""

    crud_form = S3SQLCustomForm(
            "first_name",
            #"middle_name",
            "last_name",
            S3SQLInlineComponent(
                "human_resource",
                name = "human_resource",
                label = "",
                multiple = False,
                fields = ["organisation_id",
                          "job_title_id",
                          "site_id",
                          ],
                filterby = dict(field = "contact_method",
                                options = "SMS"
                                )
            ),
            S3SQLInlineComponent(
                "contact",
                name = "phone",
                label = MOBILE,
                multiple = False,
                fields = ["value",
                          ],
                filterby = dict(field = "contact_method",
                                options = "SMS"
                                )
            ),
            S3SQLInlineComponent(
                "contact",
                name = "email",
                label = EMAIL,
                multiple = False,
                fields = ["value",
                          ],
                filterby = dict(field = "contact_method",
                                options = "EMAIL"
                                )
            ),
        )

    list_fields = [(current.messages.ORGANISATION, "human_resource.organisation_id"),
                   "first_name",
                   #"middle_name",
                   "last_name",
                   (T("Job Title"), "human_resource.job_title_id"),
                   (T("Office"), "human_resource.site_id"),
                   (MOBILE, "phone.value"),
                   (EMAIL, "email.value"),
                   ]

    s3db.configure(tablename,
                   crud_form = crud_form,
                   list_fields = list_fields,
                   listadd = True,
                   )

    # Move fields to their desired Locations
    # Disabled as breaks submission of inline_component
    #i18n = []
    #iappend = i18n.append
    #iappend('''i18n.office="%s"''' % T("Office"))
    #iappend('''i18n.organisation="%s"''' % T("Organization"))
    #iappend('''i18n.job_title="%s"''' % T("Job Title"))
    #i18n = '''\n'''.join(i18n)
    #s3.js_global.append(i18n)
    #s3.scripts.append('/%s/static/themes/DRMP/js/contacts.js' % current.request.application)

    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        if r.interactive:
            output["rheader"] = None
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="pr", f="person",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="pr", f="person",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="pr", f="person",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("pr_person")
            elif "item" in output:
                output["item"].add_class("pr_person")

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_pr_person = customize_pr_person

# -----------------------------------------------------------------------------
def customize_hrm_job_title(**attr):
    """
        Customize hrm_job_title controller
    """

    s3 = current.response.s3

    table = current.s3db.hrm_job_title
    
    # Configure fields
    field = table.organisation_id
    field.readable = field.writable = False
    field.default = None
    
    # Custom postp
    standard_postp = s3.postp
    def custom_postp(r, output):
        if r.interactive:
            actions = [dict(label=str(T("Open")),
                            _class="action-btn",
                            url=URL(c="hrm", f="job_title",
                                    args=["[id]", "read"]))
                       ]
            has_permission = current.auth.s3_has_permission
            if has_permission("update", table):
                actions.append(dict(label=str(T("Edit")),
                                    _class="action-btn",
                                    url=URL(c="hrm", f="job_title",
                                            args=["[id]", "update"])))
            if has_permission("delete", table):
                actions.append(dict(label=str(T("Delete")),
                                    _class="action-btn",
                                    url=URL(c="hrm", f="job_title",
                                            args=["[id]", "delete"])))
            s3.actions = actions
            if "form" in output:
                output["form"].add_class("hrm_job_title")
            elif "item" in output:
                output["item"].add_class("hrm_job_title")

        # Call standard postp
        if callable(standard_postp):
            output = standard_postp(r, output)

        return output
    s3.postp = custom_postp

    return attr

settings.ui.customize_hrm_job_title = customize_hrm_job_title

# =============================================================================
# Template Modules
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
            name_nice = T("Administration"),
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
    ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
    ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 1,     # 1st item in the menu
        )),
    ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = None
        )),
    ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = None
        )),
    # All modules below here should be possible to disable safely
    ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = None,
        )),
    ("cms", Storage(
            name_nice = T("Content Management"),
            restricted = True,
            module_type = None,
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
    ("event", Storage(
            name_nice = T("Disasters"),
            #description = "Events",
            restricted = True,
            module_type = None
        )),
    ("project", Storage(
            name_nice = T("Projects"),
            restricted = True,
            module_type = None
        )),
    ("asset", Storage(
            name_nice = T("Assets"),
            restricted = True,
            module_type = None
        )),
    ("supply", Storage(
            name_nice = "Supply",
            restricted = True,
            module_type = None
        )),
])
