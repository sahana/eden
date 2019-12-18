# -*- coding: utf-8 -*-

""" Disaster Victim Identification, Controllers """

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def s3_menu_postp():
    # @todo: rewrite this for new framework
    menu_selected = []
    body_id = s3base.s3_get_last_record_id("dvi_body")
    if body_id:
        body = s3db.dvi_body
        query = (body.id == body_id)
        record = db(query).select(body.id, body.pe_label,
                                  limitby=(0, 1)).first()
        if record:
            label = record.pe_label
            response.menu_options[-3][-1].append(
                [T("Candidate Matches for Body %(label)s") % dict(label=label),
                 False, URL(f="person",
                            vars=dict(match=record.id))]
            )
            menu_selected.append(
                ["%s: %s" % (T("Body"), label),
                 False, URL(f="body", args=[record.id])]
            )
    person_id = s3base.s3_get_last_record_id("pr_person")
    if person_id:
        person = s3db.pr_person
        query = (person.id == person_id)
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = s3db.pr_person_id().represent(record.id)
            menu_selected.append(
                ["%s: %s" % (T("Person"), name),
                 False, URL(f="person", args=[record.id])]
            )
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    try:
        module_name = settings.modules[module].name_nice
    except:
        module_name = T("Disaster Victim Identification")

    btable = s3db.dvi_body
    itable = s3db.dvi_identification

    query = (btable.deleted == False)
    left = itable.on(itable.pe_id == btable.pe_id)
    body_count = btable.id.count()
    rows = db(query).select(body_count,
                            itable.status,
                            left=left,
                            groupby=itable.status)
    numbers = {None: 0}
    for row in rows:
        numbers[row[itable.status]] = row[body_count]
    total = sum(numbers.values())

    dvi_id_status = dict(s3db.dvi_id_status)
    dvi_id_status[None] = T("unidentified")
    statistics = []
    for status in dvi_id_status:
        count = numbers.get(status) or 0
        statistics.append((str(dvi_id_status[status]), count))

    response.title = module_name
    return dict(module_name=module_name,
                total=total,
                status=json.dumps(statistics))

# -----------------------------------------------------------------------------
def recreq():
    """ Recovery Requests List """

    table = s3db.dvi_recreq
    table.person_id.default = auth.s3_logged_in_person()

    def prep(r):
        if r.interactive and not r.record:
            table.status.readable = False
            table.status.writable = False
            table.bodies_recovered.readable = False
            table.bodies_recovered.writable = False
        return True
    s3.prep = prep

    output = s3_rest_controller()
    return output

# -----------------------------------------------------------------------------
def morgue():
    """ Morgue Registry """

    morgue_tabs = [(T("Morgue Details"), ""),
                   (T("Bodies"), "body"),
                   ]

    rheader = S3ResourceHeader([[(T("Morgue"), "name")]
                                ], tabs=morgue_tabs)

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive and r.id and not r.component:
            field = r.table.obsolete
            field.readable = field.writable = True
        return True
    s3.prep = prep

    output = s3_rest_controller(rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def body():
    """ Dead Bodies Registry """

    gender_opts = s3db.pr_gender_opts
    gender_opts[1] = T("unknown")

    ntable = s3db.pr_note
    ntable.status.readable = False
    ntable.status.writable = False

    dvi_tabs = [(T("Recovery"), ""),
                (T("Checklist"), "checklist"),
                (T("Images"), "image"),
                (T("Physical Description"), "physical_description"),
                (T("Effects Inventory"), "effects"),
                (T("Journal"), "note"),
                (T("Identification"), "identification"),
                ]

    rheader = S3ResourceHeader([[(T("ID Tag Number"), "pe_label")],
                                ["gender"],
                                ["age_group"],
                                ],
                                tabs=dvi_tabs)

    return s3_rest_controller(rheader=rheader)

# -----------------------------------------------------------------------------
def person():
    """ Missing Persons Registry (Match Finder) """

    table = s3db.pr_person
    s3.crud_strings["pr_person"].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons found"),
        msg_no_match = T("No Persons currently reported missing"))

    s3db.configure("pr_group_membership",
                   list_fields = ["id",
                                  "group_id",
                                  "group_head",
                                  "comments"
                                  ],
                   )

    s3db.configure("pr_person",
                   deletable = False,
                   editable = False,
                   listadd = False,
                   list_fields = ["id",
                                  "first_name",
                                  "middle_name",
                                  "last_name",
                                  "picture",
                                  "gender",
                                  "age_group"
                                  ],
                   )

    def prep(r):
        if not r.id and not r.method and not r.component:
            body_id = r.get_vars.get("match", None)
            body = db(db.dvi_body.id == body_id).select(
                      db.dvi_body.pe_label, limitby=(0, 1)).first()
            label = body and body.pe_label or "#%s" % body_id
            if body_id:
                query = dvi_match_query(body_id)
                r.resource.add_filter(query)
                s3.crud_strings["pr_person"].update(
                    #subtitle_list = T("Candidate Matches for Body %s" % label),
                    msg_no_match = T("No matching records found"))
        return True
    s3.prep = prep

    field = table.missing
    field.readable = False
    field.writable = False
    field.default = True

    table.age_group.readable = True
    table.age_group.writable = True

    # Show only missing persons in list views
    if len(request.args) == 0:
        s3.filter = (db.pr_person.missing == True)

    mpr_tabs = [(T("Missing Report"), "missing_report"),
                (T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "contact"),
                (T("Journal"), "note"),
                ]

    rheader = lambda r: s3db.pr_rheader(r, tabs=mpr_tabs)

    output = s3_rest_controller("pr", "person",
                                main = "first_name",
                                extra = "last_name",
                                rheader = rheader,
                                )
    return output

# -------------------------------------------------------------------------
def dvi_match_query(body_id):
    """
        Get a query for candidate matches between the missing
        persons registry and a dead body

        @param body_id: the dvi_body record ID
    """

    ptable = s3db.pr_person
    ntable = s3db.pr_note
    btable = s3db.dvi_body

    query = ((ptable.deleted == False) &
            (ptable.missing == True) &
            (ntable.pe_id == ptable.pe_id) &
            (ntable.status == 1))

    body = btable[body_id]
    if not body:
        return query

    # last seen should be before date of recovery
    if body.date_of_recovery:
        q = ((ntable.timestmp <= body.date_of_recovery) |
            (ntable.timestmp == None))
        query = query & q

    # age group should match
    if body.age_group and body.age_group != 1:
        q = ((ptable.age_group == None) |
            (ptable.age_group == 1) |
            (ptable.age_group == body.age_group))
        query = query & q

    # gender should match
    if body.gender and body.gender != 1:
        q = ((ptable.gender == None) |
            (ptable.gender == 1) |
            (ptable.gender == body.gender))

    return query

# -----------------------------------------------------------------------------
def tooltip():
    """ Ajax Tooltips """

    formfield = request.vars.get("formfield", None)
    if formfield:
        response.view = "pr/ajaxtips/%s.html" % formfield
    return dict()

# END =========================================================================
