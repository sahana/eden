# -*- coding: utf-8 -*-

"""
    VITA Person Registry, Controllers

    @author: nursix
    @author: Pratyush Nigam <pratyush.nigam@gmail.com>
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = request.controller      # @ToDo: unify prefix and module across all controllers in some cleanup sprints
prefix = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def s3_menu_postp():
    menu_selected = []
    group_id = s3mgr.get_session("pr", "group")
    if group_id:
        group = db.pr_group
        query = (group.id == group_id)
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                  URL(f="group",
                                      args=[record.id])])
    person_id = s3mgr.get_session("pr", "person")
    if person_id:
        person = db.pr_person
        query = (person.id == person_id)
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                  URL(f="person",
                                      args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

s3_menu(module, s3_menu_postp)

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Person Registry")

    # Load Model
    s3mgr.load("pr_address")

    def prep(r):
        if r.representation == "html":
            if not r.id and not r.method:
                r.method = "search"
            else:
               redirect(URL(f="person", args=request.args))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict):
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
            output.update(module_name=module_name, gender=json.dumps(gender), age=json.dumps(age), total=total)
        if r.interactive:
            if not r.component:
                label = READ
            else:
                label = UPDATE
            linkto = r.resource.crud._linkto(r)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        r.next = None
        return output
    response.s3.postp = postp

    output = s3_rest_controller("pr", "person")
    response.view = "pr/index.html"
    response.title = module_name
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    # Load Model
    s3mgr.load("pr_address")
    if deployment_settings.get_save_search_widget():
        s3mgr.load("pr_save_search")
        s3mgr.load("msg_subscription")

    # Handle Personalised Map Configs
    gis_config_form_setup()

    # Enable this to allow migration of users between instances
    #response.s3.filter = (db.pr_person.uuid == db.auth_user.person_uuid) & (db.auth_user.registration_key != "disabled")

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
                _config = db.gis_config
                # Name will be generated from person's name.
                _config.name.readable = _config.name.writable = False
                # Hide region fields
                _config.region_location_id.readable = _config.region_location_id.writable = False
                _config.show_in_menu.readable = _config.show_in_menu.writable = False
                # Common prep shared with gis config controller function.
                response.s3.gis.config_prep_helper(r, r.component_id)

            #elif r.component_name == "pe_subscription":
            #    # Load all Tables
            #    s3mgr.model.load_all_models()
            #    db.pr_pe_subscription.resource.requires = IS_IN_SET(db.tables)

            elif r.id:
                r.table.volunteer.readable = True
                r.table.volunteer.writable = True

        return True

    def postp(r, output):
        if r.component_name == "save_search":
            stable = db.pr_save_search
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
            response.s3.actions = \
            response.s3.actions + [
                                   dict(label=str(T("Load Search")),
                                        _class="action-btn",
                                        url=URL(f="load_search",
                                                args=["[id]"]))
                                   ]
            vars = {}
            #vars["person.uid"] = r.uid
            vars["subscribe"] = "[id]"
            response.s3.actions.append(dict(label=str(T("Subscribe")),
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
            response.s3.actions.append(dict(label=str(T("Unsubscribe")),
                                            _class="action-btn",
                                            url = URL(f = "person",
                                                      args = [s3_logged_in_person(),
                                                              "save_search",],
                                                      vars = var),
                                            restrict = restrict_u)
                                        )

        return output

    response.s3.prep = prep
    response.s3.postp = postp

    s3mgr.configure("pr_group_membership",
                    list_fields=["id",
                                 "group_id",
                                 "group_head",
                                 "description"
                                ])

    # Basic tabs
    tabs = [(T("Basic Details"), None),
            (T("Address"), "address"),
            (T("Contact Details"), "contact"),
            (T("Identity"), "identity"),
            (T("Groups"), "group_membership"),
            (T("Images"), "pimage")]
    if deployment_settings.has_module("dvi") or \
       deployment_settings.has_module("mpr"):
        tabs.append((T("Journal"), "note"))

    # HR tabs
    if deployment_settings.has_module("hrm"):
        # Load Models
        s3mgr.load("hrm_competency")
        db.hrm_competency.organisation_id.writable = False
        db.hrm_competency.skill_id.comment = None
        s3mgr.model.add_component("hrm_competency",
                                  pr_person="person_id")
        tabs.append((T("Skills"), "competency"))
        s3mgr.model.add_component("hrm_training",
                                  pr_person="person_id")
        tabs.append((T("Training"), "training"))
    # Configuration tabs
    if deployment_settings.get_save_search_widget():
        tabs = tabs + [#(T("Subscriptions"), "pe_subscription"),
                       (T("Saved Searches"), "save_search"),
                       (T("Subscription Details"), "subscription")]
    tabs.append((T("Map Settings"), "config"))

    s3mgr.configure("pr_person", listadd=False, insertable=True)

    output = s3_rest_controller(prefix, resourcename,
                                main="first_name",
                                extra="last_name",
                                rheader=lambda r: \
                                        pr_rheader(r, tabs=tabs))

    return output


# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """

    tablename = "pr_group"
    table = db[tablename]

    response.s3.filter = (db.pr_group.system == False) # do not show system groups

    s3mgr.configure("pr_group_membership",
                    list_fields=["id",
                                 "person_id",
                                 "group_head",
                                 "description"
                                ])

    output = s3_rest_controller(prefix, resourcename,
                rheader=lambda r: pr_rheader(r,
                    tabs = [(T("Group Details"), None),
                            (T("Address"), "address"),
                            (T("Contact Data"), "contact"),
                            (T("Members"), "group_membership")]))

    return output


# -----------------------------------------------------------------------------
def pimage():

    """ RESTful CRUD controller """

    # Load Model
    s3mgr.load("pr_address")

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def contact():

    """ RESTful CRUD controller """

    # Load Model
    s3mgr.load("pr_address")

    table = db.pr_contact

    table.pe_id.label = T("Person/Group")
    table.pe_id.readable = True
    table.pe_id.writable = True

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def presence():

    """
        RESTful CRUD controller
        - needed for Map Popups (no Menu entry for direct access)

        @deprecated - People now use Base Location pr_person.location_id
    """

    # Load Model
    s3mgr.load("pr_presence")

    table = db.pr_presence

    # Settings suitable for use in Map Popups

    table.pe_id.readable = True
    table.pe_id.label = "Name"
    table.pe_id.represent = person_represent
    table.observer.readable = False
    table.presence_condition.readable = False
    # @ToDo: Add Skills

    return s3_rest_controller(prefix, resourcename)

# -----------------------------------------------------------------------------
#def group_membership():

    #""" RESTful CRUD controller """

    #return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def pentity():

    """ RESTful CRUD controller """

    # Load Model
    s3mgr.load("pr_address")

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def download():

    """
        Download a file.
        @todo: deprecate? (individual download handler probably not needed)
    """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

# -----------------------------------------------------------------------------
def guide():
    return dict()

# -----------------------------------------------------------------------------
def person_duplicates():

    """ Handle De-duplication of People

        @todo: permissions, audit, update super entity, PEP8, optimization?
        @todo: check for component data!
        @todo: user accounts, subscriptions?
    """

    # Shortcut
    persons = db.pr_person

    table_header = THEAD(TR(TH(T("Person 1")),
                            TH(T("Person 2")),
                            TH(T("Match Percentage")),
                            TH(T("Resolve"))))

    # Calculate max possible combinations of records
    # To handle the AJAX requests by the dataTables jQuery plugin.
    totalRecords = db(persons.id > 0).count()

    item_list = []
    if request.vars.iDisplayStart:
        end = int(request.vars.iDisplayLength) + int(request.vars.iDisplayStart)
        records = db((persons.id > 0) & \
                     (persons.deleted == False) & \
                     (persons.first_name != None)).select(persons.id,         # Should this be persons.ALL?
                                                          persons.pe_label,
                                                          persons.missing,
                                                          persons.first_name,
                                                          persons.middle_name,
                                                          persons.last_name,
                                                          persons.preferred_name,
                                                          persons.local_name,
                                                          persons.age_group,
                                                          persons.gender,
                                                          persons.date_of_birth,
                                                          persons.nationality,
                                                          persons.country,
                                                          persons.religion,
                                                          persons.marital_status,
                                                          persons.occupation,
                                                          persons.tags,
                                                          persons.comments)

        # Calculate the match percentage using Jaro wrinkler Algorithm
        count = 1
        i = 0
        for onePerson in records: #[:len(records)/2]:
            soundex1= soundex(onePerson.first_name)
            array1 = []
            array1.append(onePerson.pe_label)
            array1.append(str(onePerson.missing))
            array1.append(onePerson.first_name)
            array1.append(onePerson.middle_name)
            array1.append(onePerson.last_name)
            array1.append(onePerson.preferred_name)
            array1.append(onePerson.local_name)
            array1.append(pr_age_group_opts.get(onePerson.age_group, T("None")))
            array1.append(pr_gender_opts.get(onePerson.gender, T("None")))
            array1.append(str(onePerson.date_of_birth))
            array1.append(pr_nations.get(onePerson.nationality, T("None")))
            array1.append(pr_nations.get(onePerson.country, T("None")))
            array1.append(pr_religion_opts.get(onePerson.religion, T("None")))
            array1.append(pr_marital_status_opts.get(onePerson.marital_status, T("None")))
            array1.append(onePerson.occupation)

            # Format tags into an array
            if onePerson.tags != None:
                tagname = []
                for item in onePerson.tags:
                    tagname.append(pr_impact_tags.get(item, T("None")))
                array1.append(tagname)

            else:
                array1.append(onePerson.tags)

            array1.append(onePerson.comments)
            i = i + 1
            j = 0
            for anotherPerson in records: #[len(records)/2:]:
                soundex2 = soundex(anotherPerson.first_name)
                if j >= i:
                    array2 =[]
                    array2.append(anotherPerson.pe_label)
                    array2.append(str(anotherPerson.missing))
                    array2.append(anotherPerson.first_name)
                    array2.append(anotherPerson.middle_name)
                    array2.append(anotherPerson.last_name)
                    array2.append(anotherPerson.preferred_name)
                    array2.append(anotherPerson.local_name)
                    array2.append(pr_age_group_opts.get(anotherPerson.age_group, T("None")))
                    array2.append(pr_gender_opts.get(anotherPerson.gender, T("None")))
                    array2.append(str(anotherPerson.date_of_birth))
                    array2.append(pr_nations.get(anotherPerson.nationality, T("None")))
                    array2.append(pr_nations.get(anotherPerson.country, T("None")))
                    array2.append(pr_religion_opts.get(anotherPerson.religion, T("None")))
                    array2.append(pr_marital_status_opts.get(anotherPerson.marital_status, T("None")))
                    array2.append(anotherPerson.occupation)

                    # Format tags into an array
                    if anotherPerson.tags != None:
                        tagname = []
                        for item in anotherPerson.tags:
                            tagname.append(pr_impact_tags.get(item, T("None")))
                        array2.append(tagname)
                    else:
                        array2.append(anotherPerson.tags)

                    array2.append(anotherPerson.comments)
                    if count > end and request.vars.max != "undefined":
                        count = int(request.vars.max)
                        break;
                    if onePerson.id == anotherPerson.id:
                        continue
                    else:
                        mpercent = jaro_winkler_distance_row(array1, array2)
                        # Pick all records with match percentage is >50 or whose soundex values of first name are equal
                        if int(mpercent) > 50 or (soundex1 == soundex2):
                            count = count + 1
                            item_list.append([onePerson.first_name,
                                              anotherPerson.first_name,
                                              mpercent,
                                              "<a href=\"../pr/person_resolve?perID1=%i&perID2=%i\", class=\"action-btn\">Resolve</a>" % (onePerson.id, anotherPerson.id)
                                             ])
                        else:
                            continue
                j = j + 1
        item_list = item_list[int(request.vars.iDisplayStart):end]
        # Convert data to JSON
        result  = []
        result.append({
                    "sEcho" : request.vars.sEcho,
                    "iTotalRecords" : count,
                    "iTotalDisplayRecords" : count,
                    "aaData" : item_list
                    })
        output = json.dumps(result)
        # Remove unwanted brackets
        output = output[1:]
        output = output[:-1]
        return output

    else:
        # Don't load records except via dataTables (saves duplicate loading & less confusing for user)
        items = DIV((TABLE(table_header, TBODY(), _id="list", _class="dataTable display")))
        return(dict(items=items))

# -----------------------------------------------------------------------------
def delete_person():

    """
        To delete references to the old record and replace it with the new one.

        @todo: components??? cannot simply be re-linked!
        @todo: user accounts?
        @todo: super entity not updated!
    """

    # @ToDo: Error gracefully if conditions not satisfied
    old = request.vars.old
    new = request.vars.new

    # Find all tables which link to the pr_person table
    tables = s3_table_links("pr_person")

    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == old
            db(query).update(**{field:new})

    # Remove the record
    db(db.pr_person.id == old).update(deleted=True)
    return "Other Record Deleted, Linked Records Updated Successfully"

# -----------------------------------------------------------------------------
def person_resolve():

    """
        This opens a popup screen where the de-duplication process takes place.

        @todo: components??? cannot simply re-link!
        @todo: user accounts linked to these records?
        @todo: update the super entity!
        @todo: use S3Resources, implement this as a method handler
    """

    # @ToDo: Error gracefully if conditions not satisfied
    perID1 = request.vars.perID1
    perID2 = request.vars.perID2

    # Shortcut
    persons = db.pr_person

    count = 0
    for field in persons:
        id1 = str(count) + "Right"      # Gives a unique number to each of the arrow keys
        id2 = str(count) + "Left"
        count  = count + 1;
        # Comment field filled with buttons
        field.comment = DIV(TABLE(TR(TD(INPUT(_type="button", _id=id1, _class="rightArrows", _value="-->")),
                                     TD(INPUT(_type="button", _id=id2, _class="leftArrows", _value="<--")))))
        record = persons[perID1]
    myUrl = URL(c="pr", f="person")
    form1 = SQLFORM(persons, record, _id="form1", _action=("%s/%s" % (myUrl, perID1)))

    # For the second record remove all the comments to save space.
    for field in persons:
        field.comment = None
    record = persons[perID2]
    form2 = SQLFORM(persons, record, _id="form2", _action=("%s/%s" % (myUrl, perID2)))
    return dict(form1=form1, form2=form2, perID1=perID1, perID2=perID2)


#------------------------------------------------------------------------------
#Function to redirect for loading the search
#
def load_search():
    var = {}
    var["load"] = request.args[0]
    s3mgr.load("pr_save_search")
    rows = db(db.pr_save_search.id == request.args[0]).select(db.pr_save_search.ALL)
    import cPickle
    for row in rows:
        search_vars = cPickle.loads(row.search_vars)
        prefix = str(search_vars["prefix"])
        function = str(search_vars["function"])
        break
    redirect(URL(r=request, c=prefix, f=function, args=["search"],vars=var))
    return


# END =========================================================================