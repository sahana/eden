# -*- coding: utf-8 -*-

"""
    Person Registry, Controllers

    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def s3_menu_postp():
    # @todo: rewrite this for new framework
    menu_selected = []
    group_id = s3mgr.get_session("pr", "group")
    if group_id:
        group = s3db.pr_group
        query = (group.id == group_id)
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                  URL(f="group",
                                      args=[record.id])])
    person_id = s3mgr.get_session("pr", "person")
    if person_id:
        person = s3db.pr_person
        query = (person.id == person_id)
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            person_represent = s3db.pr_person_represent
            name = person_represent(record.id)
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
        module_name = deployment_settings.modules[module].name_nice
    except:
        module_name = T("Person Registry")

    # Load Model
    s3db.table("pr_address")

    def prep(r):
        if r.representation == "html":
            if not r.id and not r.method:
                r.method = "search"
            else:
               redirect(URL(f="person", args=request.args))
        return True
    s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict):
            # Add information for Dashboard
            pr_gender_opts = s3db.pr_gender_opts
            pr_age_group_opts = s3db.pr_age_group_opts
            table = db.pr_person
            gender = []
            for g_opt in pr_gender_opts:
                query = (table.deleted == False) & \
                        (table.gender == g_opt)
                count = db(query).count()
                gender.append([str(pr_gender_opts[g_opt]), int(count)])

            age = []
            for a_opt in pr_age_group_opts:
                query = (table.deleted == False) & \
                        (table.age_group == a_opt)
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

    # Custom Method for Contacts
    s3db.set_method(module, resourcename,
                    method="contacts",
                    action=s3db.pr_contacts)

    def prep(r):
        if r.representation == "json" and \
           not r.component and session.s3.filter_staff:
            person_ids = session.s3.filter_staff
            session.s3.filter_staff = None
            r.resource.add_filter = (~(db.pr_person.id.belongs(person_ids)))
        elif r.interactive:
            if r.representation == "popup":
                # Hide "pe_label" and "missing" fields in person popups
                r.table.pe_label.readable = False
                r.table.pe_label.writable = False
                r.table.missing.readable = False
                r.table.missing.writable = False

            if r.component_name == "config":
                _config = s3db.gis_config
                s3db.gis_config_form_setup()
                # Name will be generated from person's name.
                _config.name.readable = _config.name.writable = False
                # Hide Location
                _config.region_location_id.readable = _config.region_location_id.writable = False

            elif r.component_name == "competency":
                ctable = s3db.hrm_competency
                ctable.organisation_id.writable = False
                ctable.skill_id.comment = None

            #elif r.component_name == "pe_subscription":
            #    # Load all Tables
            #    s3db.load_all_models()
            #    db.pr_pe_subscription.resource.requires = IS_IN_SET(db.tables)

            elif r.id:
                r.table.volunteer.readable = True
                r.table.volunteer.writable = True

        return True
    s3.prep = prep

    def postp(r, output):
        if r.component_name == "save_search":
            stable = s3db.pr_save_search
            # Handle Subscribe/Unsubscribe requests
            if "subscribe" in r.get_vars:
                save_search_id = r.get_vars.get("subscribe", None)
                stable[save_search_id] = dict(subscribed = True)
            if "unsubscribe" in r.get_vars:
                save_search_id = r.get_vars.get("unsubscribe", None)
                stable[save_search_id] = dict(subscribed = False)

            s3_action_buttons(r)
            rows = db(stable.subscribed == False).select(stable.id)
            restrict_s = [str(row.id) for row in rows]
            rows = db(stable.subscribed == True).select(stable.id)
            restrict_u = [str(row.id) for row in rows]
            s3.actions = s3.actions + [
                                        dict(label=str(T("Load Search")),
                                             _class="action-btn",
                                             url=URL(f="load_search",
                                                     args=["[id]"]))
                                      ]
            vars = {}
            #vars["person.uid"] = r.uid
            vars["subscribe"] = "[id]"
            s3.actions.append(dict(label=str(T("Subscribe")),
                                   _class="action-btn",
                                   url = URL(f = "person",
                                             args = [s3_logged_in_person(),
                                                     "save_search"],
                                             vars = vars),
                                   restrict = restrict_s)
                             )
            var = {}
            #var["person.uid"] = r.uid
            var["unsubscribe"] = "[id]"
            s3.actions.append(dict(label=str(T("Unsubscribe")),
                              _class="action-btn",
                              url = URL(f = "person",
                                        args = [s3_logged_in_person(),
                                                "save_search",],
                                        vars = var),
                              restrict = restrict_u)
                             )

        return output
    s3.postp = postp

    s3db.configure("pr_group_membership",
                    list_fields=["id",
                                 "group_id",
                                 "group_head",
                                 "description"
                                ])

    # Basic tabs
    tabs = [(T("Basic Details"), None),
            (T("Address"), "address"),
            #(T("Contacts"), "contact"),
            (T("Contact Details"), "contacts"),
            (T("Images"), "image"),
            (T("Identity"), "identity"),
            (T("Education"), "education"),
            (T("Groups"), "group_membership"),
            (T("Journal"), "note"),
            (T("Skills"), "competency"),
            (T("Training"), "training"),
        ]

    # Configuration tabs
    if deployment_settings.get_save_search_widget():
        tabs = tabs + [(T("Saved Searches"), "save_search"),
                       (T("Subscription Details"), "subscription")]
    tabs.append((T("Map Settings"), "config"))

    s3db.configure("pr_person", listadd=False, insertable=True)

    output = s3_rest_controller(main="first_name",
                                extra="last_name",
                                rheader=lambda r: \
                                        s3db.pr_rheader(r, tabs=tabs))

    return output

# -----------------------------------------------------------------------------
def address():
    """
        RESTful controller to allow creating/editing of address records within
        contacts()
    """

    # CRUD pre-process
    def prep(r):
        controller = request.get_vars.get("controller", "pr")
        person_id = request.get_vars.get("person", None)
        if person_id and controller:
            s3db.configure("pr_address",
                            create_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"]),
                            update_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"])
                            )
            if r.method == "create":
                table = s3db.pr_person
                query = (table.id == person_id)
                pe_id = db(query).select(table.pe_id,
                                         limitby=(0, 1)).first().pe_id
                s3db.pr_address.pe_id.default = pe_id
        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def contact():
    """
        RESTful controller to allow creating/editing of contact records within
        contacts()
    """

    # CRUD pre-process
    def prep(r):
        controller = request.get_vars.get("controller", "pr")
        person_id = request.get_vars.get("person", None)
        if person_id:
            s3db.configure("pr_contact",
                            create_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"]),
                            update_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"])
                            )
            if r.method == "create":
                table = s3db.pr_person
                query = (table.id == person_id)
                pe_id = db(query).select(table.pe_id,
                                         limitby=(0, 1)).first().pe_id
                s3db.pr_contact.pe_id.default = pe_id
        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def contact_emergency():
    """
        RESTful controller to allow creating/editing of emergency contact
        records within contacts()
    """

    # CRUD pre-process
    def prep(r):
        controller = request.get_vars.get("controller", "pr")
        person_id = request.get_vars.get("person", None)
        if person_id:
            s3db.configure("pr_contact_emergency",
                            create_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"]),
                            update_next=URL(c=controller,
                                            f="person",
                                            args=[person_id, "contacts"])
                            )
            if r.method == "create":
                table = s3db.pr_person
                query = (table.id == person_id)
                pe_id = db(query).select(table.pe_id,
                                         limitby=(0, 1)).first().pe_id
                s3db.pr_contact_emergency.pe_id.default = pe_id
        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def person_search():
    """
        Person REST controller
        - limited to just search.json for use in Autocompletes
        - allows differential access permissions
    """

    s3.prep = lambda r: r.representation == "json" and \
                        r.method == "search"
    return s3_rest_controller(module, "person")

# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """

    tablename = "pr_group"
    table = s3db[tablename]

    s3.filter = (table.system == False) # do not show system groups

    s3db.configure("pr_group_membership",
                    list_fields=["id",
                                 "person_id",
                                 "group_head",
                                 "description"
                                ])

    rheader = lambda r: s3db.pr_rheader(r, tabs = [(T("Group Details"), None),
                                                   (T("Address"), "address"),
                                                   (T("Contact Data"), "contact"),
                                                   (T("Members"), "group_membership")
                                                  ])

    output = s3_rest_controller(rheader=rheader)

    return output

# -----------------------------------------------------------------------------
def image():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def education():
    """ RESTful CRUD controller """

    tablename = "pr_education"
    table = s3db[tablename]
    return s3_rest_controller("pr", "education")

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
    table.pe_id.represent = s3db.pr_person_represent
    table.observer.readable = False
    table.presence_condition.readable = False
    # @ToDo: Add Skills

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def pentity():
    """
        RESTful CRUD controller
        - limited to just search.json for use in Autocompletes
    """

    s3.prep = lambda r: r.representation in ("s3json", "json", "xml")
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
def tooltip():
    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

#------------------------------------------------------------------------------
# Function to redirect for loading the search
#
def load_search():
    var = {}
    var["load"] = request.args[0]
    table = s3db.pr_save_search
    rows = db(table.id == request.args[0]).select(table.ALL)
    import cPickle
    for row in rows:
        search_vars = cPickle.loads(row.search_vars)
        prefix = str(search_vars["prefix"])
        function = str(search_vars["function"])
        break
    redirect(URL(r=request, c=prefix, f=function, args=["search"],vars=var))
    return

# END =========================================================================
