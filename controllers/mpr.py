# -*- coding: utf-8 -*-

"""
    Missing Person Registry

    @author: nursix
"""

module = request.controller
prefix = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % prefix)

MISSING = str(T("Missing"))
FOUND = str(T("Found"))
DETAILS = str(T("Details"))

action = lambda l, u: dict(label=str(l), url=str(u), _class="action-btn")

# -----------------------------------------------------------------------------
def index():
    """ Home Page """

    try:
        module_name = settings.modules[prefix].name_nice
    except:
        module_name = T("Missing Persons Registry")

    prefix = "pr"
    resourcename = "person"
    tablename = "%s_%s" % (prefix, resourcename)
    table = s3db[tablename]

    report_url = URL(c="mpr", f=resourcename,
                     args=["[id]", "note"],
                     vars=dict(status="missing"))
    s3db.configure(tablename,
                    create_next=report_url,
                    list_fields=["id",
                                 "first_name",
                                 "middle_name",
                                 "last_name",
                                 "picture",
                                 "gender",
                                 "age_group",
                                 "missing"])

    def prep(r):
        if r.representation == "html":
            if not r.id and not r.method:
                r.method = "search"
            else:
               redirect(URL(resourcename, args=request.args))
        return True
    s3.prep = prep

    def postp(r, output):
        s3.actions = []
        if not r.component:
            open_button_label = DETAILS
            if auth.s3_logged_in():
                mreport = URL(resourcename,
                              args=["[id]", "note", "create"],
                              vars=dict(status="missing"))
                freport = URL(resourcename,
                              args=["[id]", "note", "create"],
                              vars=dict(status="found"))
                s3.actions = [action(MISSING, mreport),
                                       action(FOUND, freport)]
                # Is the current user reported missing?
                if isinstance(output, dict):
                    person = s3_logged_in_person()
                    if person and db.pr_person[person].missing:
                        myself = URL(resourcename,
                                     args=[person, "note", "create"],
                                     vars=dict(status="found"))
                        output.update(myself=myself)
        else:
            open_button_label = UPDATE
        #linkto = r.resource.crud._linkto(r, update=True)("[id]")
        linkto = URL(resourcename,
                     args=["[id]", "note"])
        s3.actions.append(action(open_button_label, linkto))
        return output
    s3.postp = postp

    output = s3_rest_controller(prefix, resourcename,
                                module_name=module_name)
    response.view = "mpr/index.html"
    response.title = module_name
    return output

# -----------------------------------------------------------------------------
def person():
    """ Missing Persons List """

    prefix = "pr"
    tablename = "%s_%s" % (prefix, resourcename)
    table = s3db[tablename]

    s3.crud_strings[tablename].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons currently reported missing"))

    s3db.configure("pr_group_membership",
                    list_fields=["id",
                                 "group_id",
                                 "group_head",
                                 "description"
                                ])

    s3db.configure(tablename,
                    create_next = URL(c="mpr", f="person",
                                      args=["[id]", "note", "create"],
                                      vars=dict(status="missing")),
                    list_fields=["id",
                                 "first_name",
                                 "middle_name",
                                 "last_name",
                                 "picture",
                                 "gender",
                                 "age_group",
                                 "missing"
                                ])

    def prep(r):
        if r.interactive and not r.id:
            r.resource.add_filter(db.pr_person.missing == True)
        if r.component_name == "config":
            _config = s3db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id",
                               "uuid",
                               "mci",
                               "update_record",
                               "delete_record"]:
                    _config[key].default = defaults[key]
        elif r.component_name == "note":
            ntable = db.pr_note
            status = r.vars.get("status", None)
            if status:
                if status == "missing":
                    ntable.status.default = 1
                    ntable.status.writable = False
                    ntable.timestmp.label = T("Date/Time when last seen")
                    ntable.note_text.label = T("Circumstances of disappearance")
                    s3.crud_strings[str(ntable)].update(
                        title_create = "Add Missing Report",
                        subtitle_create = "Add Missing Report")
                elif status == "found":
                    ntable.status.default = 2
                    ntable.status.writable = False
                    ntable.timestmp.label = T("Date/Time when found")
                    ntable.note_text.label = T("Comments")
                    s3.crud_strings[str(ntable)].update(
                        title_create = "Add Find Report",
                        subtitle_create = "Add Find Report")
                else:
                    ntable.status.default = 99
                    ntable.status.writable = True
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                label = READ
                linkto = URL(f="person",
                             args=("[id]", "note"))
            else:
                label = UPDATE
                linkto = r.resource.crud._linkto(r)("[id]")
            s3.actions = [action(label, linkto)]
            if not r.component:
                label = FOUND
                linkto = URL(f="person",
                             args=("[id]", "note", "create"),
                             vars=dict(status="found"))
                s3.actions.append(action(label, linkto))
        return output
    s3.postp = postp

    ptable = db.pr_person
    field = ptable.missing
    field.default = True
    field.readable = False
    field.writable = False

    ptable.pe_label.readable = False
    ptable.pe_label.writable = False
    ptable.occupation.readable = False
    ptable.occupation.writable = False
    ptable.age_group.readable = True
    ptable.age_group.writable = True

    mpr_tabs = [(T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "contact"),
                (T("Journal"), "note")]
    rheader = lambda r: s3db.pr_rheader(r, tabs=mpr_tabs)

    output = s3_rest_controller("pr", resourcename, rheader=rheader)
    return output

# END =========================================================================
