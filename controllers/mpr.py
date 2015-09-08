# -*- coding: utf-8 -*-

""" Missing Person Registry """

module = request.controller
prefix = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % prefix)

action = lambda l, u: dict(label=str(l), url=str(u), _class="action-btn")

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Missing Persons
    s3_redirect_default(URL(f="person"))

# -----------------------------------------------------------------------------
def person():
    """ Missing Persons List """

    tablename = "pr_person"

    # Module-specific CRUD strings
    # Must load model first:
    table = s3db.pr_person
    s3.crud_strings[tablename].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons"),
        label_create = T("Report a Missing Person"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons currently reported missing"))

    # List-fields
    list_fields=["id",
                 (T("Picture"), "picture.image"),
                 "first_name",
                 "middle_name",
                 "last_name",
                 "gender",
                 "age_group",
                 (T("Status"), "missing"),
                 ]

    # Filter widgets
    from s3 import S3TextFilter, S3OptionsFilter
    filter_widgets = [S3TextFilter(["first_name",
                                    "middle_name",
                                    "last_name",
                                    ],
                                    label=T("Search"),
                                    comment=T("You can search by first, middle or last name, and use * as wildcard."),
                                    ),
                      S3OptionsFilter("missing",
                                      label = T("Status"),
                                      options = {True: T("Missing"),
                                                 False: T("Found"),
                                                 },
                                      default = True,
                                      cols = 2,
                                      ),
                      ]

    # Reconfigure table
    s3db.configure(tablename,
                   filter_widgets = filter_widgets,
                   list_fields = list_fields,
                   # Redirect to missing report entry
                   create_next = URL(c="mpr", f="person",
                                     args=["[id]", "note", "create"],
                                     vars={"status": "missing"},
                                     ),
                   )

    def prep(r):
        if not r.component:
            resource = r.resource
            query = FS("note.status").belongs((1, 2, 3))
            resource.add_filter(query)

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

        elif r.component_name == "image":

            s3.crud_strings["pr_image"]["label_create"] = T("Add Image")

        elif r.component_name == "note":
            ntable = db.pr_note
            status = r.vars.get("status", None)
            if status:
                if status == "missing":
                    ntable.status.default = 1
                    ntable.status.writable = False
                    ntable.timestmp.label = T("Date/Time when last seen")
                    ntable.note_text.label = T("Circumstances of disappearance")
                    s3.crud_strings[str(ntable)].label_create = "Add Missing Report"
                elif status == "found":
                    ntable.status.default = 2
                    ntable.status.writable = False
                    ntable.timestmp.label = T("Date/Time when found")
                    ntable.note_text.label = T("Comments")
                    s3.crud_strings[str(ntable)].abel_create = "Add Find Report"
                else:
                    ntable.status.default = 99
                    ntable.status.writable = True
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                label = READ
                linkto = URL(f="person", args=("[id]", "note"))
            else:
                label = UPDATE
                linkto = r.resource.crud._linkto(r)("[id]")
            s3.actions = [action(label, linkto)]
            if not r.component:
                label = str(T("Found"))
                linkto = URL(f = "person",
                             args = ("[id]", "note", "create"),
                             vars = {"status": "found"},
                             )
                s3.actions.append(action(label, linkto))
        return output
    s3.postp = postp

    # Set default for "missing" field to True and hide it
    field = table.missing
    field.default = True
    field.readable = field.writable = False

    # We're not using pe_labels here
    field = table.pe_label
    field.readable = field.writable = False

    # Enable Age Group
    field = table.age_group
    field.readable = field.writable = True

    # Module-specific tabs
    mpr_tabs = [(T("Person Details"), None),
                (T("Journal"), "note"),
                (T("Images"), "image"),
                (T("Physical Description"), "physical_description"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "contact"),
                ]
    rheader = lambda r: s3db.pr_rheader(r, tabs=mpr_tabs)

    return s3_rest_controller("pr", "person", rheader=rheader)

# END =========================================================================
