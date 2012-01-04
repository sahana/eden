# -*- coding: utf-8 -*-

"""
    Organization Registry
"""

module = "org"

# -----------------------------------------------------------------------------
# Sector
# (Cluster in UN-style terminology)
#
tablename = "org_sector"
table = db.define_table(tablename,
                        Field("abrv", length=64, notnull=True, unique=True,
                              label=T("Abbreviation")),
                        Field("name", length=128, notnull=True, unique=True,
                              label=T("Name")),
                        *s3_meta_fields())

# CRUD strings
if deployment_settings.get_ui_cluster():
    SECTOR = T("Cluster")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Cluster"),
        title_display = T("Cluster Details"),
        title_list = T("List Clusters"),
        title_update = T("Edit Cluster"),
        title_search = T("Search Clusters"),
        subtitle_create = T("Add New Cluster"),
        subtitle_list = T("Clusters"),
        label_list_button = T("List Clusters"),
        label_create_button = T("Add New Cluster"),
        label_delete_button = T("Delete Cluster"),
        msg_record_created = T("Cluster added"),
        msg_record_modified = T("Cluster updated"),
        msg_record_deleted = T("Cluster deleted"),
        msg_list_empty = T("No Clusters currently registered"))
else:
    SECTOR = T("Sector")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Sector"),
        title_display = T("Sector Details"),
        title_list = T("List Sectors"),
        title_update = T("Edit Sector"),
        title_search = T("Search Sectors"),
        subtitle_create = T("Add New Sector"),
        subtitle_list = T("Sectors"),
        label_list_button = T("List Sectors"),
        label_create_button = T("Add New Sector"),
        label_delete_button = T("Delete Sector"),
        msg_record_created = T("Sector added"),
        msg_record_modified = T("Sector updated"),
        msg_record_deleted = T("Sector deleted"),
        msg_list_empty = T("No Sectors currently registered"))

def org_sector_represent(opt):
    """ Sector/Cluster representation for multiple=True options """

    table = db.org_sector
    set = db(table.id > 0).select(table.id,
                                  table.abrv).as_dict()

    if isinstance(opt, (list, tuple)):
        opts = opt
        vals = [str(set.get(o)["abrv"]) for o in opts]
        multiple = True
    elif isinstance(opt, int):
        opts = [opt]
        vals = str(set.get(opt)["abrv"])
        multiple = False
    else:
        try:
            opt = int(opt)
        except:
            return NONE
        else:
            opts = [opt]
            vals = str(set.get(opt)["abrv"])
            multiple = False

    if multiple:
        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
    return vals

def org_sector_deduplicate(item):
    """ Import item de-duplication """

    if item.id:
        return
    if item.tablename in ("org_sector", "org_subsector"):
        table = item.table
        abrv = item.data.get("abrv", None)
        name = item.data.get("name", None)
        if abrv:
            query = (table.abrv.lower() == abrv.lower())
        elif name:
            query = (table.name.lower() == name.lower())
        else:
            return
        duplicate = db(query).select(table.id,
                                     limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
    return

s3mgr.configure("org_sector", deduplicate=org_sector_deduplicate)

sector_id = S3ReusableField("sector_id", "list:reference org_sector",
                            sortby="abrv",
                            requires = IS_NULL_OR(IS_ONE_OF(db,
                                                            "org_sector.id",
                                                            "%(abrv)s",
                                                            sort=True,
                                                            multiple=True)),
                            represent = org_sector_represent,
                            label = SECTOR,
                            ondelete = "RESTRICT")

response.s3.org_sector_id = sector_id

# =============================================================================
# (Cluster) Subsector
#
tablename = "org_subsector"
table = db.define_table(tablename,
                        sector_id(),
                        Field("abrv", length=64, notnull=True, unique=True,
                              label=T("Abbreviation")),
                        Field("name", length=128, label=T("Name")),
                        *s3_meta_fields())

# CRUD strings
if deployment_settings.get_ui_cluster():
    SUBSECTOR = T("Cluster Subsector")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Cluster Subsector"),
        title_display = T("Cluster Subsector Details"),
        title_list = T("List Cluster Subsectors"),
        title_update = T("Edit Cluster Subsector"),
        title_search = T("Search Cluster Subsectors"),
        subtitle_create = T("Add New Cluster Subsector"),
        subtitle_list = T("Cluster Subsectors"),
        label_list_button = T("List Cluster Subsectors"),
        label_create_button = T("Add Cluster Subsector"),
        label_delete_button = T("Delete Cluster Subsector"),
        msg_record_created = T("Cluster Subsector added"),
        msg_record_modified = T("Cluster Subsector updated"),
        msg_record_deleted = T("Cluster Subsector deleted"),
        msg_list_empty = T("No Cluster Subsectors currently registered"))
else:
    SUBSECTOR = T("Subsector")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Subsector"),
        title_display = T("Subsector Details"),
        title_list = T("List Subsectors"),
        title_update = T("Edit Subsector"),
        title_search = T("Search Subsectors"),
        subtitle_create = T("Add New Subsector"),
        subtitle_list = T("Subsectors"),
        label_list_button = T("List Subsectors"),
        label_create_button = T("Add Subsector"),
        label_delete_button = T("Delete Subsector"),
        msg_record_created = T("Subsector added"),
        msg_record_modified = T("Subsector updated"),
        msg_record_deleted = T("Subsector deleted"),
        msg_list_empty = T("No Subsectors currently registered"))

def org_subsector_represent(id):
    """ Subsector ID representation """

    table = db.org_subsector
    query = (table.id == id)
    record = db(query).select(table.sector_id,
                              table.abrv,
                              limitby=(0, 1)).first()
    return org_subsector_requires_represent(record)

def org_subsector_requires_represent(record):
    """ Used to generate text for the Select """

    table = db.org_sector
    if record:
        query = (table.id == record.sector_id)
        sector_record = db(query).select(table.abrv,
                                          limitby=(0, 1)).first()
        if sector_record:
            sector = sector_record.abrv
        else:
            sector = NONE
        return "%s:%s" % (sector, record.abrv)
    else:
        return NONE

subsector_id = S3ReusableField("subsector_id",
                               db.org_subsector, sortby="abrv",
                               requires = IS_NULL_OR(IS_ONE_OF(db,
                                                               "org_subsector.id",
                                                               org_subsector_requires_represent,
                                                               sort=True)),
                               represent = org_subsector_represent,
                               label = SUBSECTOR,
                               #comment = Script to filter the sector_subsector drop down
                               ondelete = "RESTRICT")

s3mgr.configure("org_subsector", deduplicate=org_sector_deduplicate)
s3mgr.model.add_component("org_subsector", org_sector="sector_id")

# =============================================================================
# Organizations
#
organisation_type_opts = {
    1:T("Government"),
    2:T("Embassy"),
    3:T("International NGO"),
    4:T("Donor"),               # Don't change this number without changing organisation_popup.html
    6:T("National NGO"),
    7:T("UN"),
    8:T("International Organization"),
    9:T("Military"),
    10:T("Private"),
    11:T("Intergovernmental Organization"),
    12:T("Institution"),
    13:T("Red Cross / Red Crescent")
    #12:"MINUSTAH"   Haiti-specific
}

resourcename = "organisation"
tablename = "org_organisation"
table = db.define_table(tablename,
                        super_link("pe_id", "pr_pentity"),
                        #Field("privacy", "integer", default=0),
                        #Field("archived", "boolean", default=False),
                        Field("name", notnull=True, unique=True,
                              length=128,           # Mayon Compatibility
                              label = T("Name")),
                        Field("acronym", length=8, label = T("Acronym"),
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Acronym"),
                                                               T("Acronym of the organization's name, eg. IFRC.")))),
                        Field("type", "integer", label = T("Type"),
                              requires = IS_NULL_OR(IS_IN_SET(organisation_type_opts)),
                              represent = lambda opt: \
                                organisation_type_opts.get(opt, UNKNOWN_OPT)),
                        sector_id(),
                        #Field("registration", label=T("Registration")),    # Registration Number
                        Field("region", label=T("Region")),
                        Field("country", "string", length=2,
                              label = T("Home Country"),
                              requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                  lambda: gis.get_countries(key_type="code"),
                                  zero = SELECT_LOCATION)),
                              represent = lambda code: \
                                  gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                        Field("website", label = T("Website"),
                              requires = IS_NULL_OR(IS_URL()),
                              represent = s3_url_represent),
                        Field("twitter",                        # deprecated by contact component
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Twitter"),
                                                               T("Twitter ID or #hashtag")))),
                        Field("donation_phone", label = T("Donation Phone #"),
                              requires = IS_NULL_OR(s3_phone_requires),
                              comment = DIV( _class="tooltip",
                                             _title="%s|%s" % (T("Donation Phone #"),
                                                               T("Phone number to donate to this organization's relief efforts.")))),
                        s3_comments(),
                        #document_id(), # Better to have multiple Documents on a Tab
                        *s3_meta_fields())

# Organisation table CRUD settings --------------------------------------------
#
ADD_ORGANIZATION = T("Add Organization")
LIST_ORGANIZATIONS = T("List Organizations")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_ORGANIZATION,
    title_display = T("Organization Details"),
    title_list = LIST_ORGANIZATIONS,
    title_update = T("Edit Organization"),
    title_search = T("Search Organizations"),
    title_upload = T("Import Organizations"),
    subtitle_create = T("Add New Organization"),
    subtitle_list = T("Organizations"),
    label_list_button = LIST_ORGANIZATIONS,
    label_create_button = T("Add New Organization"),
    label_delete_button = T("Delete Organization"),
    msg_record_created = T("Organization added"),
    msg_record_modified = T("Organization updated"),
    msg_record_deleted = T("Organization deleted"),
    msg_list_empty = T("No Organizations currently registered"))

s3mgr.configure(tablename,
                super_entity = "pr_pentity",
                list_fields = ["id",
                               "name",
                               "acronym",
                               "type",
                               "sector_id",
                               "country",
                               "website"
                            ])

s3mgr.model.add_component("project_project",
                          org_organisation=Storage(
                                link="project_organisation",
                                joinby="organisation_id",
                                key="project_id",
                                actuate="embed",
                                autocomplete="name",
                                autodelete=False))

# -----------------------------------------------------------------------------
def organisation_represent(id, showlink=False, acronym=True):
    if isinstance(id, Row):
        # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
        org = id
    else:
        table = db.org_organisation
        query = (table.id == id)
        org = db(query).select(table.name,
                               table.acronym,
                               limitby = (0, 1)).first()
    if org:
        represent = org.name
        if acronym and org.acronym:
            represent = "%s (%s)" % (represent,
                                     org.acronym)
        if showlink:
            represent = A(represent,
                         _href = URL(c="org", f="organisation", args = [id]))
    else:
        represent = NONE

    return represent

organisation_popup_url = URL(c="org", f="organisation",
                             args="create",
                             vars=dict(format="popup"))

organisation_comment = DIV(A(ADD_ORGANIZATION,
                           _class="colorbox",
                           _href=organisation_popup_url,
                           _target="top",
                           _title=ADD_ORGANIZATION),
                         DIV(DIV(_class="tooltip",
                                 _title="%s|%s" % (T("Organization"),
                                                   T("Enter some characters to bring up a list of possible matches")))))
                                                   # Replace with this one if using dropdowns & not autocompletes
                                                   #T("If you don't see the Organization in the list, you can add a new one by clicking link 'Add Organization'.")))))

from_organisation_comment = copy.deepcopy(organisation_comment)
from_organisation_comment[0]["_href"] = organisation_comment[0]["_href"].replace("popup", "popup&child=from_organisation_id")

organisation_id = S3ReusableField("organisation_id",
                                  db.org_organisation, sortby="name",
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                  organisation_represent,
                                                                  orderby="org_organisation.name",
                                                                  sort=True)),
                                  represent = organisation_represent,
                                  label = T("Organization"),
                                  comment = organisation_comment,
                                  ondelete = "RESTRICT",
                                  # Comment this to use a Dropdown & not an Autocomplete
                                  widget = S3OrganisationAutocompleteWidget()
                                 )

response.s3.org_organisation_id = organisation_id

# -----------------------------------------------------------------------------
def organisation_multi_represent(opt):
    """
        Organisation representation
        for multiple=True options
    """

    table = db.org_organisation
    query = (table.deleted == False)
    set = db(query).select(table.id,
                           table.name).as_dict()

    if isinstance(opt, (list, tuple)):
        opts = opt
        vals = [str(set.get(o)["name"]) for o in opts]
    elif isinstance(opt, int):
        opts = [opt]
        vals = str(set.get(opt)["name"])
    else:
        return NONE

    if len(opts) > 1:
        vals = ", ".join(vals)
    else:
        vals = len(vals) and vals[0] or ""
    return vals

organisations_id = S3ReusableField("organisations_id",
                                   "list:reference org_organisation",
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                                   "%(name)s",
                                                                   multiple=True,
                                                                   #filterby="acronym",
                                                                   #filter_opts=vol_orgs,
                                                                   orderby="org_organisation.name",
                                                                   sort=True)),
                                   represent = organisation_multi_represent,
                                   label = T("Organizations"),
                                   ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
organisation_search = s3base.S3OrganisationSearch(
        # simple = (s3base.S3SearchSimpleWidget(
            # name="org_search_text_simple",
            # label = T("Search"),
            # comment = T("Search for an Organization by name or acronym."),
            # field = [ "name",
                      # "acronym",
                    # ]
            # )
        # ),
        advanced = (s3base.S3SearchSimpleWidget(
            name = "org_search_text_advanced",
            label = T("Search"),
            comment = T("Search for an Organization by name or acronym"),
            field = [ "name",
                      "acronym",
                    ]
            ),
            s3base.S3SearchOptionsWidget(
                name = "org_search_type",
                label = T("Type"),
                field = ["type"],
                cols = 2
            ),
            s3base.S3SearchOptionsWidget(
                name = "org_search_sector",
                label = T("Sector"),
                field = ["sector_id"],
                represent = org_sector_represent,
                cols = 3
            ),
            # Doesn't work on all versions of gluon/sqlhtml.py
            s3base.S3SearchOptionsWidget(
                name = "org_search_home_country",
                label = T("Home Country"),
                field = ["country"],
                cols = 3
            ),
        )
    )

s3mgr.configure(tablename,
                search_method=organisation_search)

# Components of organisations
# Documents
s3mgr.model.add_component("doc_document", org_organisation="organisation_id")

# Images
s3mgr.model.add_component("doc_image", org_organisation="organisation_id")

# -----------------------------------------------------------------------------
def organisation_rheader(r, tabs=[]):
    """ Organization page headers """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        rheader_tabs = s3_rheader_tabs(r, tabs)

        organisation = r.record
        if organisation.sector_id:
            _sectors = org_sector_represent(organisation.sector_id)
        else:
            _sectors = None

        try:
            _type = organisation_type_opts[organisation.type]
        except KeyError:
            _type = None

        table = r.table

        if deployment_settings.get_ui_cluster():
            sector_label = T("Cluster(s)")
        else:
            sector_label = T("Sector(s)")

        rheader = DIV(TABLE(
            TR(
                TH("%s: " % table.name.label),
                organisation.name,
                TH("%s: " % sector_label),
                _sectors),
            TR(
                #TH(A(T("Edit Organization"),
                #    _href=URL(r=request, c="org", f="organisation",
                              #args=[r.id, "update"],
                              #vars={"_next": _next})))
                TH("%s: " % table.type.label),
                _type,
                )
        ), rheader_tabs)

        return rheader

    return None

# -----------------------------------------------------------------------------
# Enable this to allow migration of users between instances
#s3mgr.model.add_component(db.auth_user,
#                          org_organisation="organisation_id")

# -----------------------------------------------------------------------------
def organisation_controller():
    """ RESTful CRUD controller """

    # Tabs
    tabs = [(T("Basic Details"), None)]
    if deployment_settings.has_module("hrm"):
        tabs.append((T("Staff & Volunteers"), "human_resource"))
    tabs.append((T("Offices"), "office"))
    #tabs.append((T("Facilities"), "site")) # Ticket 195
    if deployment_settings.has_module("assess"):
        s3mgr.load("assess_assess")
        tabs.append((T("Assessments"), "assess"))
    tabs.append((T("Projects"), "project"))
    # @ToDo
    #tabs.append((T("Tasks"), "task"))

    # Pre-process
    def prep(r):
        if r.interactive:
            r.table.country.default = gis.get_default_country("code")
            if r.component_name == "human_resource" and r.component_id:
                # Workaround until widget is fixed:
                hr_table = db.hrm_human_resource
                hr_table.person_id.widget = None
                hr_table.person_id.writable = False
            elif r.component_name == "office" and \
               r.method and r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                table = r.component.table
                address_hide(table)
                # Process Base Location
                #s3mgr.configure(table._tablename,
                #                onaccept=address_onaccept)
            elif r.component_name == "task" and \
                 r.method != "update" and r.method != "read":
                    # Create or ListCreate
                    r.component.table.organisation_id.default = r.id
                    r.component.table.status.writable = False
                    r.component.table.status.readable = False
            elif r.component_name == "project" and r.link:
                # Hide/show host role after project selection in embed-widget
                tn = r.link.tablename
                s3mgr.configure(tn, post_process="hide_host_role($('#%s').val());")
                script = "s3.hide_host_role.js"
                response.s3.scripts.append( "%s/%s" % (response.s3.script_dir, script))
        return True
    response.s3.prep = prep

    rheader = lambda r: organisation_rheader(r, tabs=tabs)
    output = s3_rest_controller("org", "organisation",
                                native=False, rheader=rheader)
    return output

# -----------------------------------------------------------------------------
# Donors are a type of Organization
#
def donor_represent(donor_ids):
    """ Representation of donor record IDs """
    table = db.org_organisation
    if not donor_ids:
        return NONE
    elif isinstance(donor_ids, (list, tuple)):
        query = (table.id.belongs(donor_ids))
        donors = db(query).select(table.name)
        return ", ".join([donor.name for donor in donors])
    else:
        query = (table.id == donor_ids)
        donor = db(query).select(table.name,
                                 limitby=(0, 1)).first()
        return donor and donor.name or NONE

ADD_DONOR = T("Add Donor")
ADD_DONOR_HELP = T("The Donor(s) for this project. Multiple values can be selected by holding down the 'Control' key.")
donor_id = S3ReusableField("donor_id",
                           "list:reference org_organisation",
                           sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id",
                                                           "%(name)s",
                                                           multiple=True,
                                                           filterby="type",
                                                           filter_opts=[4])),
                           represent = donor_represent,
                           label = T("Funding Organization"),
                           comment = DIV(A(ADD_DONOR,
                                           _class="colorbox",
                                           _href=URL(c="org", f="organisation",
                                                     args="create",
                                                     vars=dict(format="popup",
                                                               child="donor_id")),
                                           _target="top",
                                           _title=ADD_DONOR),
                                        DIV( _class="tooltip",
                                             _title="%s|%s" % (ADD_DONOR,
                                                               ADD_DONOR_HELP))),
                           ondelete = "RESTRICT")

# =============================================================================
# Site
#
# @ToDo: Rename as Facilities (ICS terminology)
#
# Site is a generic type for any facility (office, hospital, shelter,
# warehouse, project site etc.) and serves the same purpose as pentity does for person
# entity types:  It provides a common join key name across all types of
# sites, with a unique value for each sites.  This allows other types that
# are useful to any sort of site to have a common way to join to any of
# them.  It's especially useful for component types.
#
org_site_types = auth.org_site_types

tablename = "org_site"
table = super_entity(tablename, "site_id", org_site_types,
                     # @ToDo: Make Sites Trackable (Mobile Hospitals & Warehouses)
                     #super_link("track_id", "sit_trackable"),
                     #Field("code",
                     #      length=10,           # Mayon compatibility
                     #      notnull=True,
                     #      unique=True,
                     #      label=T("Code")),
                     Field("name",
                           length=64,           # Mayon compatibility
                           notnull=True,
                           #unique=True,
                           label=T("Name")),
                     location_id(),
                     organisation_id(),
                     *s3_ownerstamp())

# -----------------------------------------------------------------------------
def org_site_represent(id, default_label="[no label]", link = True):
    """ Represent a facility in option fields or list views """

    site_str = NONE
    site_table = db.org_site

    if not id:
        return site_str

    if isinstance(id, Row) and "instance_type" in id:
        # Do not repeat the lookup if already done by IS_ONE_OF
        site = id
    else:
        site = db(site_table._id == id).select(site_table.instance_type,
                                               limitby=(0, 1)).first()
        if not site:
            return site_str

    instance_type = site.instance_type
    try:
        table = db[instance_type]
    except:
        return site_str

    # All the current types of facility have a required "name" field that can
    # serve as their representation.
    query = (table.site_id == id)
    if instance_type == "org_office":
        record = db(query).select(table.id,
                                  table.type,
                                  table.name, limitby=(0, 1)).first()
    else:
        record = db(query).select(table.id,
                                  table.name, limitby=(0, 1)).first()

    instance_type_nice = site_table.instance_type.represent(instance_type)

    try:
        if instance_type == "org_office" and record.type == 5:
             instance_type_nice = T("Warehouse")
    except:
        pass

    if record:
        site_str = "%s (%s)" % (record.name, instance_type_nice)
    else:
        # Since name is notnull for all types so far, this won't be reached.
        site_str = "[site %d] (%s)" % (id, instance_type_nice)

    if link and record:
        c, f = instance_type.split("_")
        site_str = A(site_str,
                     _href = URL(c=c, f=f,
                                 args = [record.id],
                                 extension = "" # removes the .aaData extension in paginated views!
                                 ))

    return site_str

s3.org_site_represent = org_site_represent

# -----------------------------------------------------------------------------
site_id = super_link("site_id", "org_site",
                     #writable = True,
                     #readable = True,
                     label = T("Facility"),
                     default = auth.user.site_id if auth.is_logged_in() else None,
                     represent = org_site_represent,
                     # Comment these to use a Dropdown & not an Autocomplete
                     widget = S3SiteAutocompleteWidget(),
                     comment = DIV(_class="tooltip",
                                   _title="%s|%s" % (T("Facility"),
                                                     T("Enter some characters to bring up a list of possible matches")))
                    )

response.s3.org_site_id = site_id

# Components of sites

# Documents
s3mgr.model.add_component("doc_document", org_site=super_key(db.org_site))

# Images
s3mgr.model.add_component("doc_image", org_site=super_key(db.org_site))

# =============================================================================
# Rooms (for Sites)
# @ToDo: Validate to ensure that rooms are unique per facility
#
tablename = "org_room"
table = db.define_table(tablename,
                        site_id, # site_id
                        Field("name", length=128, notnull=True),
                        *s3_meta_fields())

# CRUD strings
ADD_ROOM = T("Add Room")
LIST_ROOMS = T("List Rooms")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_ROOM,
    title_display = T("Room Details"),
    title_list = LIST_ROOMS,
    title_update = T("Edit Room"),
    title_search = T("Search Rooms"),
    subtitle_create = T("Add New Room"),
    subtitle_list = T("Rooms"),
    label_list_button = LIST_ROOMS,
    label_create_button = ADD_ROOM,
    label_delete_button = T("Delete Room"),
    msg_record_created = T("Room added"),
    msg_record_modified = T("Room updated"),
    msg_record_deleted = T("Room deleted"),
    msg_list_empty = T("No Rooms currently registered"))

room_comment = DIV(A(ADD_ROOM,
                     _class="colorbox",
                     _href=URL(c="org", f="room",
                               args="create",
                               vars=dict(format="popup")),
                     _target="top",
                     _title=ADD_ROOM),
                   DIV( _class="tooltip",
                        _title="%s|%s" % (ADD_ROOM,
                                          T("Select a Room from the list or click 'Add Room'"))),
                   # Filters Room based on site
                   SCRIPT("""S3FilterFieldChange({
                                 'FilterField':   'site_id',
                                 'Field':         'room_id',
                                 'FieldPrefix':   'org',
                                 'FieldResource': 'room',
                                 });""")
                    )

# Reusable field for other tables to reference
room_id = S3ReusableField("room_id", db.org_room, sortby="name",
                          requires = IS_NULL_OR(IS_ONE_OF(db, "org_room.id", "%(name)s")),
                          represent = lambda id: \
                            (id and [db(db.org_room.id == id).select(db.org_room.name,
                                                                     limitby=(0, 1)).first().name] or [NONE])[0],
                          label = T("Room"),
                          comment = room_comment,
                          ondelete = "RESTRICT")

# =============================================================================
# Offices
#
org_office_type_opts = {    # @ToDo: Migrate these to constants: s3.OFFICE_TYPE
    1:T("Headquarters"),
    2:T("Regional"),
    3:T("National"),
    4:T("Field"),
    5:T("Warehouse"),       # Don't change this number, as it affects the Inv module, KML Export stylesheet & OrgAuth
}

ADD_OFFICE = T("Add Office")
office_comment = DIV(A(ADD_OFFICE,
                       _class="colorbox",
                       _href=URL(c="org", f="office",
                                 args="create",
                                 vars=dict(format="popup")),
                       _target="top",
                       _title=ADD_OFFICE),
                     DIV( _class="tooltip",
                          _title="%s|%s" % (ADD_OFFICE,
                                            T("If you don't see the Office in the list, you can add a new one by clicking link 'Add Office'."))))

response.s3.org_office_comment = office_comment

resourcename = "office"
tablename = "org_office"
table = db.define_table(tablename,
                        super_link("pe_id", "pr_pentity"),
                        super_link("site_id", "org_site"),
                        Field("name", notnull=True,
                              length=64,           # Mayon Compatibility
                              label = T("Name")),
                        Field("code",
                              length=10,
                              # Deployments that don't wants office codes can hide them
                              #readable=False,
                              #writable=False,
                              # Mayon compatibility
                              # @ToDo: Deployment Setting to add validator to make these unique
                              #notnull=True,
                              #unique=True,
                              label=T("Code")),
                        organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                        Field("type", "integer", label = T("Type"),
                              requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts)),
                              represent = lambda opt: \
                                org_office_type_opts.get(opt, UNKNOWN_OPT)),
                        Field("office_id", "reference org_office", # This form of hierarchy may not work on all Databases
                              label = T("Parent Office"),
                              comment = office_comment),
                        location_id(),
                        Field("phone1", label = T("Phone 1"),
                              requires = IS_NULL_OR(s3_phone_requires)),
                        Field("phone2", label = T("Phone 2"),
                              requires = IS_NULL_OR(s3_phone_requires)),
                        Field("email", label = T("Email"),
                              requires = IS_NULL_OR(IS_EMAIL())),
                        Field("fax", label = T("Fax"),
                              requires = IS_NULL_OR(s3_phone_requires)),
                        # @ToDo: Calculate automatically from org_staff (but still allow manual setting for a quickadd)
                        #Field("international_staff", "integer",
                        #      label = T("# of National Staff"),
                        #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                        #Field("national_staff", "integer",
                        #      label = T("# of International Staff"),
                        #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))),
                        # @ToDo: Move to Fixed Assets
                        #Field("number_of_vehicles", "integer",
                        #      label = T("# of Vehicles"),
                        #      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))),
                        #Field("vehicle_types", label = T("Vehicle Types")),
                        #Field("equipment", label = T("Equipment")),
                        Field("obsolete", "boolean",
                              label = T("Obsolete"),
                              represent = lambda bool: \
                                (bool and [T("Obsolete")] or [NONE])[0],
                              default = False),
                        #document_id(),  # Better to have multiple Documents on a Tab
                        s3_comments(),
                        *(address_fields() + s3_meta_fields()))

# Field settings
table.office_id.requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id",
                                                "%(name)s",
                                                filterby = "type",
                                                filter_opts = [1, 2, 3, 4] # All bar '5' (Warehouse)
                                                ))
table.office_id.represent = lambda id: \
    (id and [db(db.org_office.id == id).select(db.org_office.name,
                                               limitby=(0, 1)).first().name] or [NONE])[0]

if not deployment_settings.get_gis_building_name():
    table.building_name.readable = False

# CRUD strings
LIST_OFFICES = T("List Offices")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_OFFICE,
    title_display = T("Office Details"),
    title_list = LIST_OFFICES,
    title_update = T("Edit Office"),
    title_search = T("Search Offices"),
    title_upload = T("Import Offices"),
    subtitle_create = T("Add New Office"),
    subtitle_list = T("Offices"),
    label_list_button = LIST_OFFICES,
    label_create_button = T("Add New Office"),
    label_delete_button = T("Delete Office"),
    msg_record_created = T("Office added"),
    msg_record_modified = T("Office updated"),
    msg_record_deleted = T("Office deleted"),
    msg_list_empty = T("No Offices currently registered"))

# CRUD strings
ADD_WH = T("Add Warehouse")
LIST_WH = T("List Warehouses")
s3_warehouse_crud_strings = Storage(
    title_create = ADD_WH,
    title_display = T("Warehouse Details"),
    title_list = LIST_WH,
    title_update = T("Edit Warehouse"),
    title_search = T("Search Warehouses"),
    title_upload = T("Import Warehouses"),
    subtitle_create = T("Add New Warehouse"),
    subtitle_list = T("Warehouses"),
    label_list_button = LIST_WH,
    label_create_button = T("Add New Warehouse"),
    label_delete_button = T("Delete Warehouse"),
    msg_record_created = T("Warehouse added"),
    msg_record_modified = T("Warehouse updated"),
    msg_record_deleted = T("Warehouse deleted"),
    msg_list_empty = T("No Warehouses currently registered"))

# Reusable field for other tables to reference
office_id = S3ReusableField("office_id", db.org_office,
                sortby="default/indexname",
                requires = IS_NULL_OR(IS_ONE_OF(db, "org_office.id", "%(name)s")),
                represent = lambda id: \
                    (id and [db(db.org_office.id == id).select(db.org_office.name,
                                                               limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Office"),
                comment = office_comment,
                ondelete = "RESTRICT")

def org_office_deduplicate(item):
    """
        Import item deduplication, match by name and location_id (if given)

        @param item: the S3ImportItem instance
    """

    if item.id:
        return
    if item.tablename == "org_office":
        table = item.table
        name = "name" in item.data and item.data.name
        query = (table.name.lower() == name.lower())
        if "location_id" in item.data:
            location_id = item.data.location_id
            # This doesn't find deleted records:
            query = query & (table.location_id == location_id)
        duplicate = db(query).select(table.id,
                                     limitby=(0, 1)).first()
        if duplicate is None and location_id:
            # Search for deleted offices with this name
            query = (table.name.lower() == name.lower()) & \
                    (table.deleted == True)
            row = db(query).select(table.id, table.deleted_fk,
                                   limitby=(0, 1)).first()
            if row:
                fkeys = json.loads(row.deleted_fk)
                if "location_id" in fkeys and \
                   str(fkeys["location_id"]) == str(location_id):
                    duplicate = row
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# -----------------------------------------------------------------------------
# Offices as component of Organisations
s3mgr.model.add_component(table,
                          org_organisation="organisation_id")

s3mgr.configure(tablename,
                super_entity=("pr_pentity", "org_site"),
                onvalidation=address_onvalidation,
                deduplicate=org_office_deduplicate,
                list_fields=[ "id",
                              "name",
                              "organisation_id",   # Filtered in Component views
                              "type",
                              "L0",
                              "L1",
                              "L2",
                              "L3",
                              #"L4",
                              "phone1",
                              "email"
                            ])

# -----------------------------------------------------------------------------
def office_rheader(r, tabs=[]):

    """ Office/Warehouse page headers """

    if r.representation == "html":

        tablename, record = s3_rheader_resource(r)
        if tablename == "org_office" and record:
            office = record

            tabs = [(T("Basic Details"), None),
                    #(T("Contact Data"), "contact"),
                    ]
            if deployment_settings.has_module("hrm"):
                tabs.append((T("Staff"), "human_resource"))
            try:
                tabs = tabs + response.s3.req_tabs(r)
            except:
                pass
            try:
                tabs = tabs + response.s3.inv_tabs(r)
            except:
                pass

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = db.org_organisation
            query = (table.id == office.organisation_id)
            organisation = db(query).select(table.name,
                                            limitby=(0, 1)).first()
            if organisation:
                org_name = organisation.name
            else:
                org_name = None

            rheader = DIV(TABLE(
                          TR(
                             TH("%s: " % T("Name")),
                             office.name,
                             TH("%s: " % T("Type")),
                             org_office_type_opts.get(office.type,
                                                      UNKNOWN_OPT),
                             ),
                          TR(
                             TH("%s: " % T("Organization")),
                             org_name,
                             TH("%s: " % T("Location")),
                             gis_location_represent(office.location_id),
                             ),
                          TR(
                             TH("%s: " % T("Email")),
                             office.email,
                             TH("%s: " % T("Telephone")),
                             office.phone1,
                             ),
                          #TR(TH(A(T("Edit Office"),
                          #        _href=URL(c="org", f="office",
                          #                  args=[r.id, "update"],
                          #                  vars={"_next": _next})))
                          #   )
                              ),
                          rheader_tabs)

            if r.component and r.component.name == "req":
                # Inject the helptext script
                rheader.append(response.s3.req_helptext_script)

            return rheader
    return None

# -----------------------------------------------------------------------------
def office_controller():
    """ RESTful CRUD controller """

    tablename = "org_office"
    table = db[tablename]

    # Load Models to add tabs
    if deployment_settings.has_module("inv"):
        s3mgr.load("inv_inv_item")
    elif deployment_settings.has_module("req"):
        # (gets loaded by Inv if available)
        s3mgr.load("req_req")

    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]

    office_search = s3base.S3Search(
        advanced=(s3base.S3SearchSimpleWidget(
                    name="office_search_text",
                    label=T("Search"),
                    comment=T("Search for office by text."),
                    field=["name", "comments", "email"]
                  ),
                  s3base.S3SearchOptionsWidget(
                    name="office_search_org",
                    label=T("Organization"),
                    comment=T("Search for office by organization."),
                    field=["organisation_id"],
                    represent ="%(name)s",
                    cols = 3
                  ),
                  s3base.S3SearchLocationHierarchyWidget(
                    gis,
                    name="office_search_location",
                    comment=T("Search for office by location."),
                    represent ="%(name)s",
                    cols = 3
                  ),
                  s3base.S3SearchLocationWidget(
                    name="office_search_map",
                    label=T("Map"),
                  ),
        ))
    s3mgr.configure(tablename,
                    search_method = office_search)

    # Pre-processor
    def prep(r):
        table = r.table
        if r.representation == "popup":
            organisation = r.vars.organisation_id or \
                           session.s3.organisation_id or ""
            if organisation:
                table.organisation_id.default = organisation

        elif r.representation == "plain":
            # Map popups want less clutter
            table.obsolete.readable = False

        if r.record and deployment_settings.has_module("hrm"):
            # Cascade the organisation_id from the office to the staff
            hrm_table = db.hrm_human_resource
            hrm_table.organisation_id.default = r.record.organisation_id
            hrm_table.organisation_id.writable = False

        if r.interactive or r.representation == "aadata":
            if deployment_settings.has_module("inv"):
                # Filter out Warehouses, since they have a dedicated controller
                response.s3.filter = (db.org_office.type != 5) | \
                                     (db.org_office.type == None)

        if r.interactive:
            if deployment_settings.has_module("inv"):
                # Don't include Warehouses in the type dropdown
                org_office_type_opts.pop(5)
                db.org_office.type.requires = IS_NULL_OR(IS_IN_SET(org_office_type_opts))

            if r.record and r.record.type == 5: # 5 = Warehouse
                s3.crud_strings[tablename] = s3_warehouse_crud_strings

            if r.method == "create":
                table.obsolete.readable = table.obsolete.writable = False
                if r.vars.organisation_id and r.vars.organisation_id != "None":
                    table.organisation_id.default = r.vars.organisation_id

            if r.method and r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                r.table.obsolete.writable = False
                r.table.obsolete.readable = False
                address_hide(table)

            if r.component:
                if r.component.name == "inv_item" or \
                   r.component.name == "recv" or \
                   r.component.name == "send":
                    # Filter out items which are already in this inventory
                    response.s3.inv_prep(r)
                elif r.component.name == "human_resource":
                    # Filter out people which are already staff for this office
                    s3_filter_staff(r)
                    # Cascade the organisation_id from the hospital to the staff
                    hrm_table.organisation_id.default = r.record.organisation_id
                    hrm_table.organisation_id.writable = False

                elif r.component.name == "req":
                    if r.method != "update" and r.method != "read":
                        # Hide fields which don't make sense in a Create form
                        # inc list_create (list_fields over-rides)
                        response.s3.req_create_form_mods()

        return True
    response.s3.prep = prep

    rheader = office_rheader

    return s3_rest_controller("org", "office", rheader=rheader)

# =============================================================================
# Domain table
#
# When users register their email address is checked against this list.
# If the Domain matches, then they are automatically assigned to the
# Organization.
# If there is no Approvals email then the user is automatically approved.
# If there is an Approvals email then the approval request goes to this
# address
# If a user registers for an Organization & the domain doesn't match (or
# isn't listed) then the approver gets the request
tablename = "auth_organisation"

if deployment_settings.get_auth_registration_requests_organisation():
    ORG_HELP = T("If this field is populated then a user who specifies this Organization when signing up will be assigned as a Staff of this Organization unless their domain doesn't match the domain field.")
else:
    ORG_HELP = T("If this field is populated then a user with the Domain specified will automatically be assigned as a Staff of this Organization")

DOMAIN_HELP = T("If a user verifies that they own an Email Address with this domain, the Approver field is used to determine whether & by whom further approval is required.")
APPROVER_HELP = T("The Email Address to which approval requests are sent (normally this would be a Group mail rather than an individual). If the field is blank then requests are approved automatically if the domain matches.")

table = db.define_table(tablename,
                        organisation_id(
                              comment=DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Organization"),
                                                            ORG_HELP))),
                        Field("domain",
                              label=T("Domain"),
                              comment=DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Domain"),
                                                            DOMAIN_HELP))),
                        Field("approver",
                              label=T("Approver"),
                              requires=IS_NULL_OR(IS_EMAIL()),
                              comment=DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Approver"),
                                                            APPROVER_HELP))),
                        s3_comments(),
                        *s3_meta_fields())

# END =========================================================================
