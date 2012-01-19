# -*- coding: utf-8 -*-

"""
    Global menus
"""

if auth.permission.format in ("html"):

    # Language Menu (available in all screens)
    s3.menu_lang = [ T("Language"), True, "#"]
    _menu_lang = []
    for language in s3.l10n_languages.keys():
        _menu_lang.append([s3.l10n_languages[language], False,
                        URL(args=request.args,
                            vars={"_language":language})])
    s3.menu_lang.append(_menu_lang)

    # Help Menu (available in all screens)
    s3.menu_help = [ T("Help"), True, "#",
            [
                [T("Contact us"), False,
                URL(c="default", f="contact")],
                [T("About"), False, URL(c="default", f="about")],
            ]
        ]

    # Auth Menu (available in all screens)
    if not auth.is_logged_in():

        login_next = URL(args=request.args, vars=request.vars)
        if request.controller == "default" and \
        request.function == "user" and \
        "_next" in request.get_vars:
            login_next = request.get_vars["_next"]

        self_registration = deployment_settings.get_security_self_registration()

        if self_registration:
            s3.menu_auth = [T("Login"), True,
                            URL(c="default", f="user/login",
                                vars=dict(_next=login_next)),
                    [
                        [T("Login"), False,
                        URL(c="default", f="user/login", vars=dict(_next=login_next))],
                        [T("Register"), False,
                        URL(c="default", f="user/register", vars=dict(_next=login_next))],
                        [T("Lost Password"), False,
                        URL(c="default", f="user/retrieve_password")]
                    ]
                ]
        else:
            s3.menu_auth = [T("Login"), True,
                            URL(c="default", f="user/login", vars=dict(_next=login_next)),
                    [
                        [T("Lost Password"), False,
                        URL(c="default", f="user/retrieve_password")]
                    ]
                ]
    else:
        s3.menu_auth = [auth.user.email, True, None,
                [
                    [T("Logout"), False,
                    URL(c="default", f="user/logout")],
                    [T("User Profile"), False,
                    URL(c="default", f="user/profile")],
                    [T("Personal Data"), False,
                    URL(c="pr", f="person",
                        vars={"person.uid" : auth.user.person_uuid})],
                    [T("Contact Details"), False,
                    URL(c="pr", f="person",
                        args="contact",
                        vars={"person.uid" : auth.user.person_uuid})],
                    #[T("Subscriptions"), False,
                    # URL(c="pr", f="person",
                    #     args="pe_subscription",
                    #     vars={"person.uid" : auth.user.person_uuid})],
                    [T("Change Password"), False,
                    URL(c="default", f="user/change_password")],
                    ["----", False, None],
                    [{"name": T("Rapid Data Entry"),
                    "id": "rapid_toggle",
                    "value": session.s3.rapid_data_entry is True},
                    False, URL(c="default", f="rapid")]
                ]
            ]



    # Menu for Admin module
    # (defined here as used in several different Controller files)
    admin_menu_messaging = [
                [T("Email Settings"), False,
                URL(c="msg", f="email_settings", args=[1, "update"])],
                [T("SMS Settings"), False,
                URL(c="msg", f="setting", args=[1, "update"])],
                [T("Twitter Settings"), False,
                URL(c="msg", f="twitter_settings", args=[1, "update"])],
        ]
    admin_menu_options = [
        [T("Settings"), False, URL(c="admin", f="settings"),
            admin_menu_messaging,
            # Hidden until useful again
            #[T("Edit Themes"), False, URL(c="admin", f="theme")]
        ],
        [T("User Management"), False, URL(c="admin", f="user"), [
            [T("Users"), False, URL(c="admin", f="user")],
            [T("Roles"), False, URL(c="admin", f="role")],
            [T("Organizations"), False, URL(c="admin", f="organisation")],
            #[T("Roles"), False, URL(c="admin", f="group")],
            #[T("Membership"), False, URL(c="admin", f="membership")],
        ]],
        [T("Database"), False, URL(c="appadmin", f="index"), [
            # @ToDo: UI for the current Import approach (S3CSV)
            [T("Import"), False, URL(c="admin", f="import_file")],
            #[T("Import"), False, URL(c="admin", f="import_data")],
            #[T("Export"), False, URL(c="admin", f="export_data")],
            #[T("Import Jobs"), False, URL(c="admin", f="import_job")],
            [T("Raw Database access"), False, URL(c="appadmin", f="index")]
        ]],
        # Hidden until ready for production
        [T("Synchronization"), False, URL(c="sync", f="index"), [
            [T("Settings"), False, aURL(p="update", c="sync", f="config",
                                        args=["1", "update"])],
            [T("Repositories"), False, URL(c="sync", f="repository")],
            [T("Log"), False, URL(c="sync", f="log")],
        ]],
        #[T("Edit Application"), False,
        # URL(a="admin", c="default", f="design", args=[request.application])],
        [T("Tickets"), False, URL(c="admin", f="errors")],
        [T("Portable App"), False, URL(c="admin", f="portable")],
    ]

    # Modules Menu (available in all Controllers)
    # NB This is just a default menu - most deployments will customise this
    s3.menu_modules = []
    # Home always 1st
    _module = deployment_settings.modules["default"]
    s3.menu_modules.append([_module.name_nice, False,
                            URL(c="default", f="index")])

    # Modules to hide due to insufficient permissions
    hidden_modules = auth.permission.hidden_modules()

    # The Modules to display at the top level (in order)
    for module_type in [1, 2, 3, 4, 5, 6]:
        for module in deployment_settings.modules:
            if module in hidden_modules:
                continue
            _module = deployment_settings.modules[module]
            if (_module.module_type == module_type):
                if not _module.access:
                    s3.menu_modules.append([_module.name_nice, False,
                                            aURL(c=module, f="index")])
                else:
                    authorised = False
                    groups = re.split("\|", _module.access)[1:-1]
                    for group in groups:
                        if s3_has_role(group):
                            authorised = True
                    if authorised == True:
                        s3.menu_modules.append([_module.name_nice, False,
                                                URL(c=module, f="index")])

    # Modules to display off the 'more' menu
    modules_submenu = []
    for module in deployment_settings.modules:
        if module in hidden_modules:
            continue
        _module = deployment_settings.modules[module]
        if (_module.module_type == 10):
            if not _module.access:
                modules_submenu.append([_module.name_nice, False,
                                        aURL(c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module.access)[1:-1]
                for group in groups:
                    if s3_has_role(group):
                        authorised = True
                if authorised == True:
                    modules_submenu.append([_module.name_nice, False,
                                            URL(c=module, f="index")])
    if modules_submenu:
        # Only show the 'more' menu if there are entries in the list
        module_more_menu = ([T("more"), False, "#"])
        module_more_menu.append(modules_submenu)
        s3.menu_modules.append(module_more_menu)

    # Admin always last
    if s3_has_role(ADMIN):
        _module = deployment_settings.modules["admin"]
        s3.menu_admin = [_module.name_nice, True,
                        URL(c="admin", f="index"), [
                            [T("Settings"), False, URL(c="admin", f="settings")],
                            [T("Users"), False, URL(c="admin", f="user")],
                            [T("Database"), False, URL(c="appadmin", f="index")],
                            [T("Import"), False, URL(c="admin", f="import_file")],
                            [T("Synchronization"), False, URL(c="sync", f="index")],
                            [T("Tickets"), False, URL(c="admin", f="errors")],
                        ]]
    else:
        s3.menu_admin = []

    # Build overall menu out of components
    response.menu = s3.menu_modules
    response.menu.append(s3.menu_help)
    response.menu.append(s3.menu_auth)
    if deployment_settings.get_L10n_display_toolbar():
        response.menu.append(s3.menu_lang)
    if deployment_settings.get_gis_menu():
        # Do not localize this string.
        s3.gis_menu_placeholder = "GIS menu placeholder"
        # Add a placeholder for the regions menu, which cannot be constructed
        # until the gis_config table is available. Put it near the language menu.
        response.menu.append(s3.gis_menu_placeholder)
    if s3.menu_admin:
        response.menu.append(s3.menu_admin)


    # Menu helpers ================================================================
    def s3_menu(controller, postp=None, prep=None):
        """
            appends controller specific options to global menu
            picks up from 01_menu, called from controllers

            @postp - additional postprocessor,
                    assuming postp acts on response.menu_options
            @prep  - pre-processor
            @ToDo: FIXIT - alter here when you alter controller name
        """
        if controller in s3_menu_dict:

            if prep:
                prep()

            # menu
            menu_config = s3_menu_dict[controller]
            menu = menu_config["menu"]

            # role hooks
            if s3_has_role(ADMIN) and "on_admin" in menu_config:
                menu.extend(menu_config["on_admin"])

            if s3_has_role(EDITOR) and "on_editor" in menu_config:
                menu.extend(menu_config["on_editor"])

            # conditionals
            conditions = [x for x in menu_config if re.match(r"condition[0-9]+", x)]
            for condition in conditions:
                if menu_config[condition]():
                    menu.extend(menu_config["conditional%s" % condition[9:]])

            response.menu_options = menu

            if postp:
                postp()

    # =============================================================================
    # Role-dependent Menu options
    # =============================================================================
    if s3_has_role(ADMIN):
        pr_menu = [
                [T("Person"), False, aURL(f="person", args=None), [
                    [T("New"), False, aURL(p="create", f="person", args="create")],
                    [T("Search"), False, aURL(f="index")],
                    [T("List All"), False, aURL(f="person")],
                ]],
                [T("Groups"), False, aURL(f="group"), [
                    [T("New"), False, aURL(p="create", f="group", args="create")],
                    [T("List All"), False, aURL(f="group")],
                ]],
            ]
    else:
        pr_menu = []

    # =============================================================================
    # Settings-dependent Menu options
    # =============================================================================
    # CRUD strings for inv_recv
    # (outside condtional model load since need to be visible to menus)
    if deployment_settings.get_inv_shipment_name() == "order":
        ADD_RECV = T("Add Order")
        LIST_RECV = T("List Orders")
        s3.crud_strings["inv_recv"] = Storage(
            title_create = ADD_RECV,
            title_display = T("Order Details"),
            title_list = LIST_RECV,
            title_update = T("Edit Order"),
            title_search = T("Search Orders"),
            subtitle_create = ADD_RECV,
            subtitle_list = T("Orders"),
            label_list_button = LIST_RECV,
            label_create_button = ADD_RECV,
            label_delete_button = T("Delete Order"),
            msg_record_created = T("Order Created"),
            msg_record_modified = T("Order updated"),
            msg_record_deleted = T("Order canceled"),
            msg_list_empty = T("No Orders registered")
        )
    else:
        ADD_RECV = T("Receive Shipment")
        LIST_RECV = T("List Received Shipments")
        s3.crud_strings["inv_recv"] = Storage(
            title_create = ADD_RECV,
            title_display = T("Received Shipment Details"),
            title_list = LIST_RECV,
            title_update = T("Edit Received Shipment"),
            title_search = T("Search Received Shipments"),
            subtitle_create = ADD_RECV,
            subtitle_list = T("Received Shipments"),
            label_list_button = LIST_RECV,
            label_create_button = ADD_RECV,
            label_delete_button = T("Delete Received Shipment"),
            msg_record_created = T("Shipment Created"),
            msg_record_modified = T("Received Shipment updated"),
            msg_record_deleted = T("Received Shipment canceled"),
            msg_list_empty = T("No Received Shipments")
        )

    if deployment_settings.get_project_community_activity():
        list_activities_label = T("List All Communities")
        import_activities_label = T("Import Project Communities")
    else:
        list_activities_label = T("List All Activities")
        import_activities_label = T("Import Project Activities")

    if deployment_settings.get_project_drr():
        project_menu = {
            "menu": [
                [T("Projects"), False, aURL(f="project"),[
                    [T("Add New Project"), False, aURL(p="create", f="project", args="create")],
                    [T("List All Projects"), False, aURL(f="project")],
                    [list_activities_label, False, aURL(f="activity")],
                    [T("Search"), False, aURL(f="project", args="search")],
                ]],
                [T("Reports"), False, aURL(f="report"),[
                    [T("Who is doing What Where"), False, aURL(f="activity", args="report")],
                    [T("Beneficiaries"),
                    False, aURL(f="beneficiary",
                                args="report",
                                vars=Storage(rows="project_id",
                                            cols="bnf_type$name",
                                            fact="number",
                                            aggregate="sum"))],
                    [T("Funding"), False, aURL(f="organisation", args="report")],
                ]],
                [T("Import"), False, aURL(f="index"),[
                    [T("Import Projects"), False, aURL(p="create", f="project",
                                                    args="import")],
                    [T("Import Project Organizations"), False, aURL(p="create", f="organisation",
                                                                    args="import")],
                    [import_activities_label, False, aURL(p="create", f="activity",
                                                                args="import")],
                ]],
                [T("Activity Types"), False, aURL(f="activity_type"),[
                    [T("Add New Activity Type"), False, aURL(p="create", f="activity_type", args="create")],
                    [T("List All Activity Types"), False, aURL(f="activity_type")],
                    #[T("Search"), False, aURL(f="activity_type", args="search")]
                ]],
                [T("Hazards"), False, aURL(f="hazard"),[
                    [T("Add New Hazard"), False, aURL(p="create", f="hazard", args="create")],
                    [T("List All Hazards"), False, aURL(f="hazard")],
                ]],
                [T("Project Themes"), False, aURL(f="theme"),[
                    [T("Add New Theme"), False, aURL(p="create", f="theme", args="create")],
                    [T("List All Themes"), False, aURL(f="theme")],
                ]],
                [T("Beneficiary Types"), False, aURL(f="beneficiary_type"),[
                    [T("Add New Type"), False, aURL(p="create", f="beneficiary_type", args="create")],
                    [T("List All Types"), False, aURL(f="beneficiary_type")],
                ]],
            ],

        }

    elif s3_has_role("STAFF"):
        project_menu = {
            "menu": [
                [T("Projects"), False, aURL(f="project"),[
                    #[T("Add New Project"), False, aURL(p="create", f="project", args="create")],
                    [T("List Projects"), False, aURL(f="project")],
                    [T("Open Tasks for Project"), False, aURL(f="project", vars={"tasks":1})],
                ]],
                #[T("Tasks"), False, aURL(f="task"),[
                    #[T("Add New Task"), False, aURL(p="create", f="task", args="create")],
                    #[T("List All Tasks"), False, aURL(f="task")],
                    #[T("Search"), False, aURL(f="task", args="search")],
                #]],
                [T("Daily Work"), False, aURL(f="time"),[
                    [T("All Tasks"), False, aURL(f="task", args="search")],
                    [T("My Logged Hours"), False, aURL(f="time", vars={"mine":1})],
                    [T("Last Week's Work"),
                    False, aURL(f="time",
                                args="report",
                                vars={"rows":"person_id",
                                    "cols":"day",
                                    "fact":"hours",
                                    "aggregate":"sum",
                                    "week":1})],
                    [T("My Open Tasks"), False, aURL(f="task", vars={"mine":1})],
                ]],
            ],
            "on_admin": [
                [T("Admin"), False, None,[
                    [T("Activity Types"), False, aURL(f="activity_type")],
                    [T("Organizations"), False, aURL(f="organisation")],
                    [T("Import Tasks"), False, aURL(p="create", f="task",
                                                    args="import")],
                ]],
                [T("Reports"), False, aURL(f="report"),[
                    [T("Activity Report"),
                    False, aURL(f="activity",
                                args="report",
                                vars=Storage(rows="project_id",
                                            cols="name",
                                            fact="time_actual",
                                            aggregate="sum"))],
                    [T("Project Time Report"),
                    False, aURL(f="time",
                                args="report",
                                vars=Storage(rows="project",
                                            cols="person_id",
                                            fact="hours",
                                            aggregate="sum"))],
                ]],
            ]
        }
    else:
        project_menu = {
            "menu": [
                [T("Projects"), False, aURL(f="project"),[
                    [T("List All Projects"), False, aURL(f="project")],
                ]],
            ],
        }

    # -------------------------------------------------------------------------
    hrm_menu = {
        "menu": [],

        # NOTE: session.s3.hrm.mode is set by menu pre-processor in controller
        #       so can't simply make an if/else here :/

        "condition1": lambda: session.s3.hrm.mode is not None,
        "conditional1": [
                [T("Profile"),
                 True, aURL(c="hrm",
                            f="person",
                            vars=dict(mode="personal"))
                ]],

        "condition2": lambda: (session.s3.hrm.mode is not None) and (session.s3.hrm.orgs or ADMIN in session.s3.roles),
        "conditional2": [[T("Human Resources"),
                          True, aURL(c="hrm",
                                     f="index")]],

        "condition3": lambda: session.s3.hrm.mode is None,
        "conditional3": [
            [T("Staff"), False, aURL(c="hrm",
                                     f="human_resource",
                                     vars=dict(group="staff")), [
                [T("New Staff Member"), False, aURL(p="create",
                                                    c="hrm",
                                                    f="human_resource",
                                                    args="create",
                                                    vars=dict(group="staff"))],
                [T("List All"), False, aURL(c="hrm",
                                            f="human_resource",
                                            vars=dict(group="staff"))],
                [T("Search"), False, aURL(c="hrm",
                                          f="human_resource",
                                          args="search",
                                          vars=dict(group="staff"))],
                [T("Report Expiring Contracts"), False, aURL(c="hrm",
                                                             f="human_resource",
                                                             vars=dict(group="staff",
                                                                       expiring=1))],
                [T("Import"), False, aURL(p="create",
                                          c="hrm",
                                          f="person",
                                          args=["import"],
                                          vars=dict(group="staff"))],
                #[T("Dashboard"), False, aURL(f="index")],
            ]],
            [T("Volunteers"), False, aURL(c="hrm",
                                          f="human_resource",
                                          vars=dict(group="volunteer")), [
                [T("New Volunteer"), False, aURL(p="create",
                                                 c="hrm",
                                                 f="human_resource",
                                                 args="create",
                                                 vars=dict(group="volunteer"))],
                [T("List All"), False, aURL(c="hrm",
                                            f="human_resource",
                                            vars=dict(group="volunteer"))],
                [T("Search"), False, aURL(c="hrm",
                                          f="human_resource",
                                          args="search",
                                          vars=dict(group="volunteer"))],
                [T("Import"), False, aURL(p="create",
                                          c="hrm",
                                          f="person",
                                          args=["import"],
                                          vars=dict(group="volunteer"))],
            ]],
            [T("Teams"), False, aURL(c="hrm",
                                     f="group"), [
                [T("New Team"), False, aURL(c="hrm",
                                            f="group",
                                            args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="group")],
            ]],
            [T("Job Role Catalog"), False, aURL(c="hrm",
                                                f="job_role"), [
                [T("New Job Role"), False, aURL(c="hrm",
                                                f="job_role",
                                                args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="job_role")],
            ]],
            [T("Skill Catalog"), False, URL(c="hrm",
                                            f="skill"), [
                [T("New Skill"), False, aURL(p="create",
                                             c="hrm",
                                             f="skill",
                                             args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="skill")],
                #[T("Skill Provisions"), False, aURL(c="hrm",
                #                                    f="skill_provision")],
            ]],
            [T("Training Events"), False, URL(c="hrm",
                                              f="training_event"), [
                [T("New Training Event"), False, aURL(p="create",
                                                      c="hrm",
                                                      f="training_event",
                                                      args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="training_event")],
                [T("Training Report"), False, aURL(c="hrm",
                                                   f="training",
                                                   args=["report"],
                                                   vars=dict(rows="course_id",
                                                             cols="month",
                                                             fact="person_id",
                                                             aggregate="count"))],
                [T("Import Participant List"), False, aURL(p="create",
                                                           c="hrm",
                                                           f="training",
                                                           args=["import"])],
            ]],
            [T("Training Course Catalog"), False, URL(c="hrm",
                                                      f="course"), [
                [T("New Training Course"), False, aURL(p="create",
                                                       c="hrm",
                                                       f="course",
                                                       args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="course")],
                [T("Course Certificates"), False, aURL(c="hrm",
                                                       f="course_certificate")],
            ]],
            [T("Certificate Catalog"), False, URL(c="hrm",
                                                  f="certificate"), [
                [T("New Certificate"), False, aURL(p="create",
                                                   c="hrm",
                                                   f="certificate",
                                                   args="create")],
                [T("List All"), False, aURL(c="hrm",
                                            f="certificate")],
                [T("Skill Equivalence"), False, aURL(c="hrm",
                                                     f="certificate_skill")],
            ]],
            # Add the "personal" section to the menu (right)
            [T("Personal Profile"), True, aURL(c="hrm",
                                               f="person",
                                               vars=dict(mode="personal"))]
        ],
    }

    # =============================================================================
    # Default Menu Configurations for Controllers
    # =============================================================================
    """
        Dict structure -
            Key - controller name
            Value - Dict
                - menu      : default menu options
                - on_admin  : extensions for ADMIN role
                - on_editor : extensions for EDITOR role
            @NOTE: subject to change depending on changes in S3Menu / requirements
    """
    s3_menu_dict = {

        # ASSESS Controller
        # -------------------------------------------------------------------------
        "assess": {
            "menu": [
                [T("Rapid Assessments"), False, aURL(f="rat"), [
                    [T("New"), False, aURL(p="create", f="rat", args="create")],
                    [T("List All"), False, aURL(f="rat")],
                    #[T("Search"), False, URL(f="rat", args="search")],
                ]],
                [T("Impact Assessments"), False, aURL(f="assess"), [
                    #[T("New"), False, aURL(p="create", f="assess", args="create")],
                    [T("New"), False, aURL(p="create", f="basic_assess")],
                    [T("List All"), False, aURL(f="assess")],
                    [T("Mobile"), False, aURL(f="mobile_basic_assess")],
                    #[T("Search"), False, aURL(f="assess", args="search")],
                ]],
                [T("Baseline Data"), False, URL(f="#"), [
                    [T("Population"), False, aURL(f="population")],
                ]],
            ],

            "on_admin": [
                [T("Edit Options"), False, URL(f="#"), [
                    [T("List / Add Baseline Types"), False, aURL(f="baseline_type")],
                    [T("List / Add Impact Types"), False, aURL(f="impact_type")],
                ]],
            ]
        },

        # ASSET Controller
        # -------------------------------------------------------------------------
        "asset": {
            "menu": [
                #[T("Home"), False, aURL(c="asset", f="index")],
                [T("Assets"), False, aURL(c="asset", f="asset"),
                [
                    [T("New"), False, aURL(p="create", c="asset", f="asset",
                                           args="create")],
                    [T("List All"), False, aURL(c="asset", f="asset")],
                    [T("Search"), False, aURL(c="asset", f="asset",
                                              args="search")],
                    [T("Import"), False, aURL(p="create", c="asset", f="asset",
                                              args="import")],
                ]],
                [T("Items"), False, aURL(c="asset", f="item"),
                [
                    [T("New"), False, aURL(p="create", c="asset", f="item",
                                           args="create")],
                    [T("List All"), False, aURL(c="asset", f="item")],
                ]],
            ]
        },

        # BUDGET Controller
        # -------------------------------------------------------------------------
        "budget": {
            "menu": [
                [T("Parameters"), False, aURL(f="parameters")],
                [T("Items"), False, aURL(f="item"), [
                    [T("New"), False, aURL(p="create", f="item", args="create")],
                    [T("List"), False, aURL(f="item")],
                ]],
                [T("Kits"), False, aURL(f="kit"), [
                    [T("New"), False, aURL(p="create", f="kit", args="create")],
                    [T("List"), False, aURL(f="kit")],
                ]],
                [T("Bundles"), False, aURL(f="bundle"), [
                    [T("New"), False, aURL(p="create", f="bundle", args="create")],
                    [T("List"), False, aURL(f="bundle")],
                ]],
                [T("Staff"), False, aURL(f="staff"), [
                    [T("New"), False, aURL(p="create", f="staff", args="create")],
                    [T("List"), False, aURL(f="staff")],
                ]],
                [T("Locations"), False, aURL(f="location"), [
                    [T("New"), False, aURL(p="create", f="location", args="create")],
                    [T("List"), False, aURL(f="location")],
                ]],
                [T("Projects"), False, aURL(f="project"), [
                    [T("New"), False, aURL(p="create", f="project", args="create")],
                    [T("List"), False, aURL(f="project")],
                ]],
                [T("Budgets"), False, aURL(f="budget"), [
                    [T("New"), False, aURL(p="create", f="budget", args="create")],
                    [T("List"), False, aURL(f="budget")],
                ]]
            ],
        },

        # BUILDING Controller
        # -------------------------------------------------------------------------
        "building": {
            "menu": [
                [T("NZSEE Level 1"), False, aURL(f="nzseel1"), [
                    [T("Submit New (triage)"), False, aURL(p="create", f="nzseel1",
                                                        args="create",
                                                        vars={"triage":1})],
                    [T("Submit New (full form)"), False, aURL(p="create", f="nzseel1",
                                                            args="create")],
                    [T("Search"), False, aURL(f="nzseel1", args="search")],
                    [T("List"), False, aURL(f="nzseel1")],
                ]],
                [T("NZSEE Level 2"), False, aURL(f="nzseel2"), [
                    [T("Submit New"), False, aURL(p="create", f="nzseel2",
                                                args="create")],
                    [T("Search"), False, aURL(f="nzseel2", args="search")],
                    [T("List"), False, aURL(f="nzseel2")],
                ]],
                [T("Report"), False, aURL(f="index"),
                [
                [T("Snapshot"), False, aURL(f="report")],
                [T("Assessment timeline"), False, aURL(f="timeline")],
                [T("Assessment admin level"), False, aURL(f="adminLevel")],
                ]
                ]
            ]
        },

        # CLIMATE Controller
        # -------------------------------------------------------------------------
        "climate": {
            "menu": [
                [T("Home"), False, aURL(f="index")],
                [T("Station Parameters"), False, aURL(f="station_parameter")],
                [T("Saved Queries"), False, aURL(f="save_query")],
                [T("Purchase Data"), False, aURL(f="purchase")],
            ],
        },

        # CR / Shelter Registry Controller
        # -------------------------------------------------------------------------
        "cr": {
            "menu": [
                [ # @ToDo - Fix s3.crud_strings["cr_shelter"].subtitle_list
                T("Camps") if deployment_settings.get_ui_camp() else T("Shelters"), False, aURL(f="shelter"), [
                    [T("New"), False, aURL(p="create", f="shelter", args="create")],
                    [T("List All"), False, aURL(f="shelter")],
                    # @ToDo Search by type, services, location, available space
                    #[T("Search"), False, URL(f="shelter", args="search")],
                ]],
            ],

            "on_editor": [
                [
                    T("Camp Types and Services") if deployment_settings.get_ui_camp() \
                    else T("Shelter Types and Services"),
                    False, URL(f="#"),
                    [
                        [T("List / Add Services"), False, URL(f="shelter_service")],
                        [T("List / Add Types"), False, URL(f="shelter_type")],

                    ]
                ],
            ]
        },

        # DELPHI / Delphi Decision Maker
        # -------------------------------------------------------------------------
        "delphi": {
            "menu": [
                [T("Active Problems"), False, aURL(f="problem"), [
                                            [T("New"), False, aURL(p="create", f="problem", args="create")],
                                            [T("List All"), False, aURL(f="problem")],
                ]],
                [T("Groups"), False, aURL(f="group"), [
                                            [T("New"), False, aURL(p="create", f="group", args="create")],
                                            [T("List All"), False, aURL(f="group")],
                ]],
                #[T("Solutions"), False, aURL(f="solution")],
            ],

            "on_admin": [
                #[T("Groups"), False, URL(f="group")],
                #[T("Group Memberships"), False, URL(f="membership")],
                #[T("Problem Administration"), False, URL(f="problem")],
            ]
        },

        # DOC / Document Library
        # -------------------------------------------------------------------------
        "doc": {
            "menu": [
                [T("Documents"), False, aURL(f="document"),[
                    [T("New"), False, aURL(p="create", f="document", args="create")],
                    [T("List All"), False, aURL(f="document")],
                    #[T("Search"), False, aURL(f="ireport", args="search")]
                ]],
                [T("Photos"), False, aURL(f="image"),[
                    [T("New"), False, aURL(p="create", f="image", args="create")],
                    [T("List All"), False, aURL(f="image")],
                    #[T("Bulk Uploader"), False, aURL(f="bulk_upload")]
                    #[T("Search"), False, aURL(f="ireport", args="search")]
                ]]],
        },

        # DVI / Disaster Victim Identification
        # -------------------------------------------------------------------------
        "dvi": {
            "menu": [
                #[T("Home"), False, URL(f="index")],
                [T("Body Recovery"), False, aURL(f="recreq"),[
                    [T("New Request"),
                    False, aURL(p="create", f="recreq",
                                args="create")],
                    [T("List Current"),
                    False, aURL(f="recreq",
                                vars={"recreq.status":"1,2,3"})],
                    [T("List All"),
                    False, aURL(f="recreq")],
                ]],
                [T("Dead Bodies"), False, aURL(f="body"),[
                    [T("New"),
                    False, aURL(p="create", f="body",
                                args="create")],
                    [T("Search"),
                    False, aURL(f="body",
                                args="search")],
                    [T("List all"),
                    False, aURL(f="body")],
                    [T("List unidentified"),
                    False, aURL(f="body",
                                vars=dict(status="unidentified"))],
                    [T("Report by Age/Gender"),
                    False, aURL(f="body",
                                args=["report"],
                                vars=dict(rows="age_group",
                                        cols="gender",
                                        fact="pe_label",
                                        aggregate="count"))],
                ]],
                [T("Missing Persons"), False, aURL(f="person"), [
                    [T("List all"), False, aURL(f="person")],
                ]],
                [T("Morgues"), False, aURL(f="morgue"),[
                    [T("New"),
                    False, aURL(p="create", f="morgue",
                                args="create")],
                    [T("List All"),
                    False, aURL(f="morgue")],
                ]],
                [T("Help"), False, URL(f="index")]
            ]
        },

        # DVR / Disaster Victim Registry
        # -------------------------------------------------------------------------
        "dvr": {
            "menu": [
                [T("Add Disaster Victims"), False,  aURL(f="index"),[
                    [T("Add new Group"), False, aURL(p="create", f="index")],
                    [T("Add new Individual"), False, aURL(p="create", f="index")]
                ]],
                [T("Edit Disaster Victims"), False,  aURL(f="index"),[
                    [T("Search and Edit Group"), False, aURL(f="index")],
                    [T("Search and Edit Individual"), False, aURL(f="index")]
                ]],
                [T("List Groups"), False,  aURL(f="index"),[
                    [T("List Groups/View Members"), False, aURL(f="index")]
                ]],
                [T("Reports"), False,  aURL(f="index"),[
                    [T("Drill Down by Group"), False, aURL(f="index")],
                    [T("Drill Down by Shelter"), False, aURL(f="index")],
                    [T("Drill Down by Incident"), False, aURL(f="index")]
                ]],
            ]
        },

        # EVENT / Event Module
        # -------------------------------------------------------------------------
        "event": {
            "menu": [
                        [T("Scenarios"), False, aURL(c="scenario", f="scenario"), [
                            [T("New Scenario"), False, aURL(p="create", c="scenario",
                                                            f="scenario",
                                                            args="create")],
                            [T("View All"), False, aURL(c="scenario", f="scenario")]
                        ]],
                        [T("Events"), False, aURL(c="event", f="event"), [
                            [T("New Event"), False, aURL(p="create", c="event", f="event",
                                                         args="create")],
                            [T("View All"), False, aURL(c="event", f="event")]
                        ]],
                    ]   \
                    if deployment_settings.has_module("scenario") else \
                    [
                        [T("Events"), False, aURL(c="event", f="event"), [
                            [T("New Event"), False, aURL(p="create", c="event", f="event",
                                                         args="create")],
                            [T("View All"), False, aURL(c="event", f="event")]
                        ]]
                    ],
        },

        # FIRE
        # -------------------------------------------------------------------------
        "fire": {
            "menu": [
                [T("Fire Stations"), False, aURL(c="fire", f="station"),
                [
                    [T("New"), False, aURL(p="create", c="fire", f="station",
                                        args="create")],
                    [T("List All"), False, aURL(c="fire", f="station")],
                    [T("Search"), False, aURL(c="fire", f="station",
                                            args="search")],
                    [T("Import Stations"), False, aURL(c="fire", f="station",
                                            args="import.xml")],
                    [T("Import Vehicles"), False, aURL(c="fire", f="station_vehicle",
                                            args="import.xml")],
                ]],
                [T("Water Sources"), False, aURL(c="fire", f="water_source"),
                [
                    [T("New"), False, aURL(p="create", c="fire", f="water_source",
                                        args="create")],
                    [T("List All"), False, aURL(c="fire", f="water_source")],
                    [T("Search"), False, aURL(c="fire", f="water_source",
                                            args="search")],
                    [T("Import"), False, aURL(c="fire", f="water_source",
                                            args="import.xml")],
                ]],
                [T("Hazard Points"), False, aURL(c="fire", f="hazard_point"),
                [
                    [T("New"), False, aURL(p="create", c="fire", f="hazard_point",
                                        args="create")],
                    [T("List All"), False, aURL(c="fire", f="hazard_point")],
                    [T("Search"), False, aURL(c="fire", f="hazard_point",
                                            args="search")],
                    [T("Import"), False, aURL(c="fire", f="hazard_point",
                                            args="import.xml")],
                ]],
            ]
        },

        # GIS / GIS Controllers
        # -------------------------------------------------------------------------
        "gis": {
            "menu": [
                [T("Locations"), False, aURL(f="location"), [
                    [T("New Location"), False, aURL(p="create", f="location",
                                                    args="create")],
                    [T("New Location Group"), False, aURL(p="create", f="location",
                                                        args="create",
                                                        vars={"group": 1})],
                    [T("List All"), False, aURL(f="location")],
                    [T("Search"), False, aURL(f="location", args="search")],
                    #[T("Geocode"), False, aURL(f="geocode_manual")],
                ]],
                [T("Fullscreen Map"), False, aURL(f="map_viewing_client")],
                # Currently not got geocoding support
                #[T("Bulk Uploader"), False, aURL(c="doc", f="bulk_upload")]
            ],

            "condition1": lambda: not deployment_settings.get_security_map() or s3_has_role(MAP_ADMIN),
            "conditional1": [[T("Service Catalogue"), False, URL(f="map_service_catalogue")]]
        },

        # HMS / Hospital Status Assessment and Request Management System
        # -------------------------------------------------------------------------
        "hms": {
            "menu": [
                [T("Hospitals"), False, aURL(f="hospital", args="search"), [
                    [T("New"), False, aURL(p="create", f="hospital",
                                           args="create")],
                    [T("Search"), False, aURL(f="hospital", args="search")],
                    [T("List All"), False, aURL(f="hospital")],
                    #["----", False, None],
                    #[T("Show Map"), False, URL(c="gis", f="map_viewing_client",
                                               #vars={"kml_feed" : "%s/hms/hospital.kml" %
                                                    #s3.base_url,
                                                    #"kml_name" : "Hospitals_"})],
                ]],
                [T("Help"), False, URL(f="index")]
            ],
        },

        # HRM
        # -------------------------------------------------------------------------
        "hrm": hrm_menu,

        # INV / Inventory
        # -------------------------------------------------------------------------
        "inv": {
            "menu": [
                    #[T("Home"), False, aURL(c="inv", f="index")],
                    [T("Warehouses"), False, aURL(c="inv", f="warehouse"), [
                        [T("New"), False, aURL(p="create", c="inv",
                                               f="warehouse",
                                               args="create")],
                        [T("List All"), False, aURL(c="inv", f="warehouse")],
                        [T("Search"), False, aURL(c="inv", f="warehouse",
                                                  args="search")],
                        [T("Import"), False, aURL(p="create", c="inv",
                                                  f="warehouse",
                                                  args=["import"])],
                    ]],
                    [T("Warehouse Stock"), False, aURL(c="inv", f="warehouse"), [
                        [T("Search Warehouse Stock"), False, aURL(c="inv",
                                                                  f="inv_item",
                                                                  args="search")],
                        [s3.crud_strings.inv_recv.title_search, False, aURL(c="inv", f="recv",
                                                                            args="search")],
                        [T("Import"), False, aURL(p="create", c="inv", f="inv_item",
                                                  args=["import"])],
                    ]],
                    [s3.crud_strings.inv_recv.subtitle_list, False, aURL(c="inv", f="recv"), [
                        [T("New"), False, aURL(p="create", c="inv",
                                               f="recv",
                                               args="create")],
                        [T("List All"), False, aURL(c="inv", f="recv")],
                        [s3.crud_strings.inv_recv.title_search, False, aURL(c="inv",
                                                                            f="recv",
                                                                            args="search")],
                    ]],
                    [T("Sent Shipments"), False, aURL(c="inv", f="send"), [
                        [T("New"), False, aURL(p="create", c="inv",
                                               f="send",
                                               args="create")],
                        [T("List All"), False, aURL(c="inv", f="send")],
                    ]],
                    [T("Items"), False, aURL(c="supply", f="item"), [
                        [T("New"), False, aURL(p="create", c="supply",
                                               f="item",
                                               args="create")],
                        [T("List All"), False, aURL(c="supply", f="item")],
                        [T("Search"), False, aURL(c="supply", f="catalog_item",
                                                  args="search")],
                    ]],

                    # Catalog Items moved to be next to the Item Categories
                    #[T("Catalog Items"), False, aURL(c="supply", f="catalog_item"), [
                    #    [T("New"), False, aURL(p="create", c="supply", f="catalog_item",
                    #                          args="create")],
                    #    [T("List All"), False, aURL(c="supply", f="catalog_item")],
                    #    [T("Search"), False, aURL(c="supply", f="catalog_item",
                    #                             args="search")],
                    ##]],
                    #
                    [T("Catalogs"), False, aURL(c="supply", f="catalog"), [
                        [T("New"), False, aURL(p="create", c="supply",
                                               f="catalog",
                                               args="create")],
                        [T("List All"), False, aURL(c="supply", f="catalog")],
                        #[T("Search"), False, aURL(c="supply", f="catalog",
                        #                         args="search")],
                    ]]
                ],

            "on_admin": [[T("Item Categories"), False, aURL(c="supply", f="item_category"), [
                    [T("New Item Category"), False, aURL(p="create",
                                                         c="supply",
                                                         f="item_category",
                                                         args="create")],
                    [T("List All"), False, aURL(c="supply", f="item_category")]
                ]]]
        },

        # IRS / Incident Report System
        # -------------------------------------------------------------------------
        "irs": {
            "menu": [
                [T("Incident Reports"), False, aURL(f="ireport"),[
                    [T("New"), False, aURL(p="create", f="ireport", args="create")],
                    [T("List All"), False, aURL(f="ireport")],
                    [T("Open Incidents"), False, aURL(f="ireport", vars={"open":1})],
                    [T("Timeline"), False, aURL(f="ireport", args="timeline")],
                    #[T("Search"), False, aURL(f="ireport", args="search")]
                ]],
            ],

            "on_admin": [[T("Incident Categories"), False, aURL(f="icategory"),[
                    [T("New"), False, aURL(p="create", f="icategory", args="create")],
                    [T("List All"), False, aURL(f="icategory")],
                ]],
                ["Ushahidi " + T("Import"), False, aURL(f="ireport", args="ushahidi")]
            ]
        },

        # SURVEY / Survey Controller
        # -------------------------------------------------------------------------
        "survey": {
            "menu": [
                [T("Assessment Templates"), False, aURL(f="template"), [
                    #[T("New"), False, aURL(p="create", f="template", args="create")],
                    [T("List All"), False, aURL(f="template")],
                ]],
                #[T("Section"), False, aURL(f="section"), [
                #    [T("New"), False, aURL(p="create", f="section", args="create")],
                #    [T("List All"), False, aURL(f="section")]]],
                [T("Event Assessments"), False, aURL(f="series"), [
                    [T("New"), False, aURL(p="create", f="series", args="create")],
                    [T("List All"), False, aURL(f="series")],
                ]],
                ],
            "on_admin": [
                [T("Administration"), False, aURL(f="complete"), [
                    #[T("New"), False, aURL(p="create", f="complete", args="create")],
                    #[T("List All"), False, aURL(f="complete")],
                    [T("Import Templates"), False, aURL(f="question_list",
                                                        args="import")],
                    [T("Import Completed Responses"), False, aURL(f="complete",
                                                                  args="import")]
                ]],
                ]
        },

        # MPR / Missing Person Registry
        # -------------------------------------------------------------------------
        "mpr": {
            "menu": [
                [T("Missing Persons"),
                False, aURL(f="person"), [
                    [T("New"),
                    False, aURL(p="create", f="person",
                                args="create")],
                    [T("Search"),
                    False, aURL(f="index")],
                    [T("List All"),
                    False, aURL(f="person")],
                ]],
            ],
        },

        # MSG / Messaging Controller
        # -------------------------------------------------------------------------
        "msg": {
            "menu": [
                [T("Compose"), False, URL(c="msg", f="compose")],
                [T("Distribution groups"), False, aURL(f="group"), [
                    [T("List/Add"), False, aURL(f="group")],
                    [T("Group Memberships"), False, aURL(f="group_membership")],
                ]],
                [T("Log"), False, aURL(f="log")],
                [T("Outbox"), False, aURL(f="outbox")],
                #[T("Search Twitter Tags"), False, aURL(f="twitter_search"),[
                #    [T("Queries"), False, aURL(f="twitter_search")],
                #    [T("Results"), False, aURL(f="twitter_search_results")]
                #]],
                #["CAP", False, aURL(f="tbc")]
            ],

            "on_admin": [
                [T("Administration"), False, URL(f="#"), admin_menu_messaging],
            ]
        },

        # ORG / Organization Registry
        # -------------------------------------------------------------------------
        "org": {
            "menu": [
                    [T("Organizations"), False, aURL(c="org", f="organisation"), [
                        [T("New"), False,
                        aURL(p="create", c="org", f="organisation",
                            args="create")],
                        [T("List All"), False, aURL(c="org", f="organisation")],
                        [T("Search"), False, aURL(c="org", f="organisation",
                                                args="search")],
                        [T("Import"), False, aURL(c="org", f="organisation",
                                                args="import")]
                    ]],
                    [T("Offices"), False, aURL(c="org", f="office"), [
                        [T("New"), False,
                        aURL(p="create", c="org", f="office",
                            args="create")],
                        [T("List All"), False, aURL(c="org", f="office")],
                        [T("Search"), False, aURL(c="org", f="office",
                                                args="search")],
                        [T("Import"), False, aURL(c="org", f="office",
                                                args="import")]
                    ]],
                ],
        },

        # PATIENT / Patient Tracking Module
        # -------------------------------------------------------------------------
        "patient": {
            "menu": [
                    [T("Patients"), False, URL(f="patient"), [
                        [T("New"), False, aURL(p="create", f="patient",
                                               args="create")],
                        [T("List All"), False, aURL(f="patient")],
                        [T("Search"), False, aURL(f="patient",
                                                  args="search")]
                    ]]],
        },

        # PR / VITA Person Registry
        # --------------------------------------------------------------------------
        "pr": {
            "menu": pr_menu
        },

        # PROC / Procurement
        # -------------------------------------------------------------------------
        "proc": {
            "menu": [
                [T("Home"), False, aURL(f="index")],
                [T("Procurement Plans"), False, aURL(f="plan"),[
                    [T("New"), False, aURL(p="create", f="plan", args="create")],
                    [T("List All"), False, aURL(f="plan")],
                    #[T("Search"), False, aURL(f="plan", args="search")]
                ]],
                [T("Suppliers"), False, aURL(f="supplier"),[
                    [T("New"), False, aURL(p="create", f="supplier", args="create")],
                    [T("List All"), False, aURL(f="supplier")],
                    #[T("Search"), False, aURL(f="supplier", args="search")]
                ]],
            ],

        },

        # PROJECT / Project Tracking & Management
        # -------------------------------------------------------------------------
        "project": project_menu,

        # REQ / Request Management
        # -------------------------------------------------------------------------
        "req": {
            "menu": [[T("Requests"), False, aURL(c="req", f="req"), [
                        [T("New"), False, aURL(p="create", c="req", f="req",
                                               args="create")],
                        [T("List All"), False, aURL(c="req", f="req")],
                        [T("List All Requested Items"), False, aURL(c="req", f="req_item")],
                        [T("List All Requested Skills"), False, aURL(c="req", f="req_skill")],
                        #[T("Search Requested Items"), False, aURL(c="req",
                        #                                          f="req_item",
                        #                                          args="search")],
                    ]],
                    [T("Commitments"), False, aURL(c="req", f="commit"), [
                        [T("List All"), False, aURL(c="req", f="commit")]
                    ]],
                ]
        },

        # SYNC
        # -------------------------------------------------------------------------
        "sync": {
            "menu": admin_menu_options
        },

        # VEHICLE
        # -------------------------------------------------------------------------
        "vehicle": {
            "menu": [
                #[T("Home"), False, aURL(c="vehicle", f="index")],
                [T("Vehicles"), False, aURL(c="vehicle", f="vehicle"),
                [
                    [T("New"), False, aURL(p="create", c="vehicle", f="vehicle",
                                           args="create")],
                    [T("List All"), False, aURL(c="vehicle", f="vehicle")],
                    [T("Search"), False, aURL(c="vehicle", f="vehicle",
                                              args="search")],
                ]],
            ]
        },

        # VOL / Volunteer
        # -------------------------------------------------------------------------
        "vol": {
            "menu": [],
            "condition1": lambda: (auth.user is not None) and deployment_settings.has_module("hrm"),
            "conditional1": [
                [T("My Details"), False, aURL(f="person", args="")]
            ],

            "condition2": lambda: (auth.user is not None) and (deployment_settings.has_module("project")),
            "conditional2": [
                [T("My Tasks"), False, aURL(f="task", args="")],
            ]
        },

        # ADMIN
        # -------------------------------------------------------------------------
        "admin": {
            "menu": admin_menu_options
        },

    }

    # Duplicate menus - some controllers might re-use menu defined in certain models Eg. inv, supply
    s3_menu_dict["supply"] = s3_menu_dict["inv"]
    s3_menu_dict["scenario"] = s3_menu_dict["event"]

else:
    s3_menu = lambda *args, **vars: None
    s3.menu_lang = []
    s3.menu_help = []
    s3.menu_auth = []
    s3.menu_modules = []
    response.menu = []

# END =========================================================================
