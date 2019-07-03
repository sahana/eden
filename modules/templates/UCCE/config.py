# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Settings for UCCE: User-Centred Community Engagement
        A project for Oxfam & Save the Children run with Eclipse Experience
    """

    T = current.T

    settings.base.system_name = T("User-Centred Community Engagement")
    settings.base.system_name_short = T("UCCE")

    # PrePopulate data
    settings.base.prepopulate += ("UCCE",)
    settings.base.prepopulate_demo += ("UCCE/Demo",)

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "UCCE"
    # Custom Logo
    settings.ui.menu_logo = "/%s/static/themes/UCCE/img/ee_logo.png" % current.request.application

    # Authentication settings
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations

    settings.security.policy = 6 # Controller, Function, Table ACLs and Entity Realm

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
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
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        # Currently-needed for Profile link:
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
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
            module_type = 10,
        )),
        ("dc", Storage(
           name_nice = T("Assessments"),
           #description = "Data collection tool",
           restricted = True,
           module_type = 5
        )),
        ("project", Storage(
           name_nice = T("Projects"),
           restricted = True,
           module_type = 5
        )),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

    settings.ui.filter_clear = False
    settings.search.filter_manager = False

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import cms_post_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Guide"),
            title_display = T("Guide Details"),
            title_list = T("Guides"),
            title_update = T("Edit Guide"),
            #title_upload = T("Import Guides"),
            label_list_button = T("List Guides"),
            label_delete_button = T("Delete Guide"),
            msg_record_created = T("Guide added"),
            msg_record_modified = T("Guide updated"),
            msg_record_deleted = T("Guide deleted"),
            msg_list_empty = T("No Guides currently registered"))

        s3db = current.s3db
        f = s3db.cms_post.series_id
        f.label = T("Category")
        f.readable = f.writable = True

        s3db.configure("cms_post",
                       crud_form = S3SQLCustomForm("series_id",
                                                   "title",
                                                   "body",
                                                   ),
                       list_fields = ["series_id",
                                      "title",
                                      "body",
                                      ],
                       list_layout = cms_post_list_layout,
                       filter_widgets = [S3TextFilter(["title",
                                                       "series_id",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search guide"),
                                                      ),
                                         ],
                       )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -----------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "datalist":
                # Filter out non-Guides
                from s3 import FS
                r.resource.add_filter(FS("post_module.module") == None)

            return result
        s3.prep = prep

        attr["dl_rowsize"] = 2

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import dc_target_list_layout

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Survey"),
            title_display = T("Survey Details"),
            title_list = T("Surveys"),
            title_update = T("Edit Survey"),
            #title_upload = T("Import Surveys"),
            label_list_button = T("List Surveys"),
            label_delete_button = T("Delete Survey"),
            msg_record_created = T("Survey added"),
            msg_record_modified = T("Survey updated"),
            msg_record_deleted = T("Survey deleted"),
            msg_list_empty = T("No Surveys currently registered"))


        current.s3db.configure("dc_target",
                               crud_form = S3SQLCustomForm("name"),
                               listadd = False,
                               list_fields = ["name",
                                              "project.name",
                                              ],
                               list_layout = dc_target_list_layout,
                               filter_widgets = [S3TextFilter(["name",
                                                               ],
                                                              #formstyle = text_filter_formstyle,
                                                              label = "",
                                                              _placeholder = T("Search project or survey"),
                                                              ),
                                                 ],
                               )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -----------------------------------------------------------------------------
    def customise_dc_target_controller(**attr):

        attr["dl_rowsize"] = 2

        return attr

    settings.customise_dc_target_controller = customise_dc_target_controller

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3TextFilter

        from templates.UCCE.controllers import project_project_list_layout

        s3db = current.s3db

        user = current.auth.user
        organisation_id = user and user.organisation_id
        if organisation_id:
            f = s3db.project_project.organisation_id
            f.default = organisation_id
            f.readable = f.writable = False

        s3db.configure("project_project",
                       crud_form = S3SQLCustomForm("organisation_id",
                                                   "name",
                                                   ),
                       list_fields = ["name",
                                      ],
                       list_layout = project_project_list_layout,
                       filter_widgets = [S3TextFilter(["name",
                                                       ],
                                                      #formstyle = text_filter_formstyle,
                                                      label = "",
                                                      _placeholder = T("Search project or survey"),
                                                      ),
                                         ],
                       )

    settings.customise_project_project_resource = customise_project_project_resource

# END =========================================================================
