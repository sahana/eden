# -*- coding: utf-8 -*-

"""
    Person Registry, Controllers
"""

module = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def s3_menu_postp():
    # Unused
    # @todo: rewrite this for new framework?
    menu_selected = []
    group_id = s3base.s3_get_last_record_id("pr_group")
    if group_id:
        group = s3db.pr_group
        query = (group.id == group_id)
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                  URL(f="group",
                                      args=[record.id])])
    person_id = s3base.s3_get_last_record_id("pr_person")
    if person_id:
        person = s3db.pr_person
        query = (person.id == person_id)
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = s3db.pr_person_id().represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                  URL(f="person",
                                      args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    try:
        module_name = settings.modules[module].name_nice
    except:
        module_name = T("Person Registry")

    # Load Model
    s3db.table("pr_address")

    def prep(r):
        if r.representation == "html":
            if r.id or r.method:
               redirect(URL(f="person", args=request.args))
        return True
    s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict):
            # Add information for Dashboard
            pr_gender_opts = s3db.pr_gender_opts
            table = db.pr_person
            gender = []
            for g_opt in pr_gender_opts:
                query = (table.deleted == False) & \
                        (table.gender == g_opt)
                count = db(query).count()
                gender.append([str(pr_gender_opts[g_opt]), int(count)])

            pr_age_group_opts = s3db.pr_age_group_opts
            dtable = db.pr_physical_description
            age = []
            for a_opt in pr_age_group_opts:
                query = (table.deleted == False) & \
                        (table.pe_id == dtable.pe_id) & \
                        (dtable.age_group == a_opt)
                count = db(query).count()
                age.append([str(pr_age_group_opts[a_opt]), int(count)])

            total = int(db(table.deleted == False).count())
            output.update(module_name=module_name,
                          gender=json.dumps(gender),
                          age=json.dumps(age),
                          total=total)
        if r.interactive:
            if not r.component:
                label = READ
            else:
                label = UPDATE
            linkto = r.resource.crud._linkto(r)("[id]")
            s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        r.next = None
        return output
    s3.postp = postp

    output = s3_rest_controller("pr", "person")
    response.view = "pr/index.html"
    response.title = module_name
    return output

# -----------------------------------------------------------------------------
def person():
    """ RESTful CRUD controller """

    # Enable this to allow migration of users between instances
    #s3.filter = (s3db.pr_person.pe_id == s3db.pr_person_user.pe_id) & \
                #(s3db.auth_user.id == s3db.pr_person_user.user_id) & \
                #(s3db.auth_user.registration_key != "disabled")

    # Organisation Dependent Fields
    # @ToDo: Deprecate (only used by IFRC template)
    set_org_dependent_field = settings.set_org_dependent_field
    set_org_dependent_field("pr_person_details", "father_name")
    set_org_dependent_field("pr_person_details", "mother_name")
    set_org_dependent_field("pr_person_details", "affiliations")
    set_org_dependent_field("pr_person_details", "company")

    def prep(r):
        if r.representation == "json" and \
           not r.component and session.s3.filter_staff:
            person_ids = session.s3.filter_staff
            session.s3.filter_staff = None
            r.resource.add_filter = (~(db.pr_person.id.belongs(person_ids)))

        elif r.interactive:
            if r.representation == "popup":
                # Hide "pe_label" and "missing" fields in person popups
                table = r.table
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False

                # S3SQLCustomForm breaks popup return, so disable
                s3db.clear_config("pr_person", "crud_form")
            if r.component:
                component_name = r.component_name
                if component_name == "config":
                    ctable = s3db.gis_config
                    s3db.gis_config_form_setup()
                    # Name will be generated from person's name.
                    field = ctable.name
                    field.readable = field.writable = False
                    # Hide Location
                    field = ctable.region_location_id
                    field.readable = field.writable = False

                elif component_name == "competency":
                    ctable = s3db.hrm_competency
                    ctable.organisation_id.writable = False
                    ctable.skill_id.comment = None

                elif component_name == "group_membership":
                    s3db.configure("pr_group_membership",
                                   list_fields = ["id",
                                                  "group_id",
                                                  "group_head",
                                                  "comments",
                                                  ],
                                   )

        return True
    s3.prep = prep

    # Address tab
    if settings.get_pr_use_address():
        address_tab = (T("Address"), "address")
    else:
        address_tab = None

    # Contacts Tabs
    contacts_tabs = []
    set_method = s3db.set_method
    setting = settings.get_pr_contacts_tabs()
    if "all" in setting:
        s3db.set_method(module, resourcename,
                        method = "contacts",
                        action = s3db.pr_Contacts)
        contacts_tabs.append((settings.get_pr_contacts_tab_label("all"),
                              "contacts",
                              ))
    if "public" in setting:
        s3db.set_method(module, resourcename,
                        method = "public_contacts",
                        action = s3db.pr_Contacts)
        contacts_tabs.append((settings.get_pr_contacts_tab_label("public_contacts"),
                              "public_contacts",
                              ))
    if "private" in setting and auth.is_logged_in():
        s3db.set_method(module, resourcename,
                        method = "private_contacts",
                        action = s3db.pr_Contacts)
        contacts_tabs.append((settings.get_pr_contacts_tab_label("private_contacts"),
                              "private_contacts",
                              ))

    # All tabs
    tabs = [(T("Basic Details"), None),
            address_tab,
            ]
    if contacts_tabs:
        tabs.extend(contacts_tabs)

    tabs.extend([(T("Images"), "image"),
                 (T("Identity"), "identity"),
                 (T("Education"), "education"),
                 (T("Groups"), "group_membership"),
                 (T("Journal"), "note"),
                 (T("Skills"), "competency"),
                 (T("Training"), "training"),
                 (T("Map Settings"), "config"),
                 ])

    s3db.configure("pr_person",
                   insertable = True,
                   listadd = False,
                   )

    output = s3_rest_controller(main = "first_name",
                                extra = "last_name",
                                rheader = lambda r: \
                                            s3db.pr_rheader(r, tabs=tabs))

    return output

# -----------------------------------------------------------------------------
def address():
    """ RESTful CRUD controller """

    # CRUD pre-process
    def prep(r):
        person_id = get_vars.get("person", None)
        if person_id:
            # Coming from s3.contacts.js [s3db.pr_contacts()]
            # - currently not used as can't load Google Maps properly
            # Lookup the controller
            controller = get_vars.get("controller", "pr")
            # Lookup the access
            access = get_vars.get("access", None)
            if access is None:
                method = "contacts"
            elif access == "1":
                method = "private_contacts"
            elif access == "2":
                method = "public_contacts"
            s3db.configure("pr_address",
                            create_next = URL(c=controller,
                                              f="person",
                                              args=[person_id, method]),
                            update_next = URL(c=controller,
                                              f="person",
                                              args=[person_id, method])
                            )
            if r.method == "create":
                table = s3db.pr_person
                pe_id = db(table.id == person_id).select(table.pe_id,
                                                         limitby=(0, 1)
                                                         ).first().pe_id
                s3db.pr_address.pe_id.default = pe_id

        else:
            field = s3db.pr_address.pe_id
            if r.method == "create":
                pe_id = get_vars.get("~.pe_id", None)
                if pe_id:
                    # Coming from Profile page
                    field.default = pe_id
                else:
                    field.label = T("Entity")
                    field.readable = field.writable = True
            else:
                # No known workflow uses this
                field.label = T("Entity")
                field.readable = field.writable = True

        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def contact():
    """ RESTful CRUD controller """

    # CRUD pre-process
    def prep(r):
        person_id = get_vars.get("person", None)
        if person_id:
            # Coming from s3.contacts.js [s3db.pr_Contacts()]
            # Lookup the controller
            controller = get_vars.get("controller", "pr")
            # Lookup the access
            access = get_vars.get("access", None)
            if access is None:
                method = "contacts"
            elif access == "1":
                method = "private_contacts"
            elif access == "2":
                method = "public_contacts"
            s3db.configure("pr_contact",
                           create_next = URL(c=controller,
                                             f="person",
                                             args=[person_id, method]),
                           update_next = URL(c=controller,
                                             f="person",
                                             args=[person_id, method])
                           )
            if r.method == "create":
                table = s3db.pr_person
                pe_id = db(table.id == person_id).select(table.pe_id,
                                                         limitby=(0, 1)
                                                         ).first().pe_id
                table = s3db.pr_contact
                table.pe_id.default = pe_id
                # Public or Private?
                if access:
                    table.access.default = access
        else:
            field = s3db.pr_contact.pe_id
            if r.method in ("create", "create.popup"):
                # Coming from Profile page
                pe_id = get_vars.get("~.pe_id", None)
                if pe_id:
                    field.default = pe_id
                else:
                    field.label = T("Entity")
                    field.readable = field.writable = True
            else:
                # @ToDo: Document which workflow uses this?
                field.label = T("Entity")
                field.readable = field.writable = True
                from s3 import S3TextFilter, S3OptionsFilter
                filter_widgets = [S3TextFilter(["value",
                                                "comments",
                                                ],
                                               label = T("Search"),
                                               comment = T("You can search by value or comments."),
                                               ),
                                  S3OptionsFilter("contact_method"),
                                  ]
                s3db.configure("pr_contact",
                               filter_widgets = filter_widgets,
                               )

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def contact_emergency():
    """
        RESTful controller to allow creating/editing of emergency contact
        records within contacts()
    """

    # CRUD pre-process
    def prep(r):
        person_id = get_vars.get("person", None)
        if person_id:
            controller = get_vars.get("controller", "pr")
            # Lookup the access
            access = get_vars.get("access", None)
            if access is None:
                method = "contacts"
            elif access == "1":
                method = "private_contacts"
            elif access == "2":
                method = "public_contacts"
            s3db.configure("pr_contact_emergency",
                           create_next = URL(c=controller,
                                             f="person",
                                             args=[person_id, method]),
                           update_next = URL(c=controller,
                                             f="person",
                                             args=[person_id, method])
                           )
            if r.method == "create":
                table = s3db.pr_person
                query = (table.id == person_id)
                pe_id = db(query).select(table.pe_id,
                                         limitby=(0, 1)).first().pe_id
                s3db.pr_contact_emergency.pe_id.default = pe_id
        else:
            field = s3db.pr_contact_emergency.pe_id
            if r.method == "create" and r.representation == "popup":
                # Coming from Profile page
                pe_id = get_vars.get("~.pe_id", None)
                if pe_id:
                    field.default = pe_id
                else:
                    field.label = T("Entity")
                    field.readable = field.writable = True

        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search_ac for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.method == "search_ac"
    return s3_rest_controller(module, "person")

# -----------------------------------------------------------------------------
def forum():
    """ RESTful CRUD controller """

    # CRUD pre-process
    def prep(r):
        if auth.s3_has_role("ADMIN"):
            # No restrictions
            return True

        from s3 import FS
        if r.id:
            if r.method == "join":
                # Only possible for Public Groups
                filter_ = FS("forum_type") == 1
            elif r.method == "request":
                # Only possible for Private Groups
                filter_ = FS("forum_type") == 2
            else:
                # Can only see Public Groups
                filter_ = FS("forum_type") == 1
                user = auth.user
                if user:
                    # unless the User is a Member of them
                    filter_ |= FS("forum_membership.person_id$pe_id") == user.pe_id
        else:
            # Cannot see Seceret Groups
            filter_ = FS("forum_type") != 3
            user = auth.user
            if user:
                # unless the User is a Member of them
                filter_ |= FS("forum_membership.person_id$pe_id") == user.pe_id

        r.resource.add_filter(filter_)

        return True
    s3.prep = prep

    output = s3_rest_controller(rheader = s3db.pr_rheader)
    return output

# -----------------------------------------------------------------------------
#def forum_membership():
#    """ RESTful CRUD controller """
#
#    output = s3_rest_controller()
#
#    return output

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    FS = s3base.S3FieldSelector
    s3.filter = (FS("group.system") == False) # do not show system groups

    # Modify list_fields for the component tab
    table = s3db.pr_group_membership
    s3db.configure("pr_group_membership",
                   list_fields = ["id",
                                  "person_id",
                                  "group_head",
                                  "comments"
                                  ],
                   )

    rheader = lambda r: \
        s3db.pr_rheader(r, tabs = [(T("Group Details"), None),
                                   (T("Address"), "address"),
                                   (T("Contact Data"), "contact"),
                                   (T("Members"), "group_membership")
                                   ])

    output = s3_rest_controller(rheader = rheader)

    return output

# -----------------------------------------------------------------------------
def group_member_role():
    """ Group Member Roles: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def group_status():
    """ Group Statuses: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def image():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def education():
    """ RESTful CRUD controller """

    def prep(r):
        if r.method in ("create", "create.popup", "update", "update.popup"):
            # Coming from Profile page?
            person_id = get_vars.get("~.person_id", None)
            if person_id:
                field = s3db.pr_education.person_id
                field.default = person_id
                field.readable = field.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def education_level():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def language():
    """ RESTful CRUD controller """

    def prep(r):
        if r.method in ("create", "create.popup", "update", "update.popup"):
            # Coming from Profile page?
            person_id = get_vars.get("~.person_id", None)
            if person_id:
                field = s3db.pr_language.person_id
                field.default = person_id
                field.readable = field.writable = False

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def occupation_type():
    """ Occupation Types: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def religion():
    """ Religions: RESTful CRUD Controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
#def contact():
#    """ RESTful CRUD controller """
#
#    table = s3db.pr_contact
#
#    table.pe_id.label = T("Person/Group")
#    table.pe_id.readable = True
#    table.pe_id.writable = True
#
#    return s3_rest_controller()

# -----------------------------------------------------------------------------
def presence():
    """
        RESTful CRUD controller
        - needed for Map Popups (no Menu entry for direct access)

        @deprecated - People now use Base Location pr_person.location_id
    """

    table = s3db.pr_presence

    # Settings suitable for use in Map Popups

    table.pe_id.readable = True
    table.pe_id.label = "Name"
    table.pe_id.represent = s3db.pr_person_id().represent
    table.observer.readable = False
    table.presence_condition.readable = False
    # @ToDo: Add Skills

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def pentity():
    """
        RESTful CRUD controller
        - limited to just search_ac for use in Autocompletes
    """

    s3.prep = lambda r: r.method == "search_ac"
    return s3_rest_controller()

# -----------------------------------------------------------------------------
def affiliation():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def role():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def slot():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def tooltip():
    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return {}

# =============================================================================
def filter():
    """
        REST controller for saved filters
    """

    # Page length
    s3.dl_pagelength = 10

    def postp(r, output):
        if r.interactive and isinstance(output, dict):
            # Hide side menu
            menu.options = None

            output["title"] = T("Saved Filters")

            # Script for inline-editing of filter title
            options = {"cssclass": "jeditable-input",
                       "tooltip": str(T("Click to edit"))}
            script = '''$('.jeditable').editable('%s',%s)''' % \
                     (URL(), json.dumps(options))
            s3.jquery_ready.append(script)
        return output
    s3.postp = postp

    output = s3_rest_controller()
    return output

# =============================================================================
def subscription():
    """
        REST controller for subscriptions
        - to allow Admins to control subscriptions for people
    """

    output = s3_rest_controller()
    return output

# =============================================================================
def human_resource():
    """
        RESTful CRUD controller for options.s3json lookups
        - needed for templates, like DRMP, where HRM fields are embedded inside
          pr_person form
    """

    if auth.permission.format != "s3json":
        return ""

    # Pre-process
    def prep(r):
        if r.method != "options":
            return False
        return True
    s3.prep = prep

    return s3_rest_controller("hrm", "human_resource")

# =============================================================================
# Messaging
# =============================================================================
def compose():
    """ Send message to people/teams """

    return s3db.pr_compose()

# END =========================================================================
