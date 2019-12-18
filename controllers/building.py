# -*- coding: utf-8 -*-

"""
    Buildings Assessments module

    Data model from:
    http://www.atcouncil.org/products/downloadable-products/placards

    Postearthquake Safety Evaluation of Buildings: ATC-20
    http://www.atcouncil.org/pdfs/rapid.pdf
    This is actually based on the New Zealand variant:
    http://eden.sahanafoundation.org/wiki/BluePrintBuildingAssessments

    @ToDo: Port forms to Survey module & deprecate as much as possible of this
           module (which might be all)

    @ToDo: Hide fields for triage form server side
    - once print comes from controller then it will also skip these fields
    - less to download to browser (more scalable)

    @ToDo: add other forms (ATC-38, ATC-45)
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
# Define the Model
# @ToDo: Move to modules/s3db/building.py
# - here it isn't visible to s3db.load_all_models() or Sync
# -----------------------------------------------------------------------------
from gluon.sql import SQLCustomType

person_id = s3db.pr_person_id
location_id = s3db.gis_location_id
organisation_id = s3db.org_organisation_id

s3_datetime_format = settings.get_L10n_datetime_format()

# Options
building_area_inspected = {
    1:T("Exterior and Interior"),
    2:T("Exterior Only")
}

building_construction_types = {
    1:T("Timber frame"), # Wood frame
    2:T("Steel frame"),
    3:T("Tilt-up concrete"),
    4:T("Concrete frame"),
    5:T("Concrete shear wall"),
    6:T("Unreinforced masonry"),
    7:T("Reinforced masonry"),
    8:T("RC frame with masonry infill"),
    99:T("Other")
}

building_primary_occupancy_opts = {
    1:T("Dwelling"),
    2:T("Other residential"),
    3:T("Public assembly"),
    4:T("School"),
    5:T("Religious"),
    6:T("Commercial/Offices"),
    7:T("Industrial"),
    8:T("Government"),
    9:T("Heritage Listed"), # Historic
    99:T("Other")
}

building_evaluation_condition = {
    1:T("Minor/None"),
    2:T("Moderate"),
    3:T("Severe")
}

building_estimated_damage = {
    1:T("None"),
    2:"0-1%",
    3:"1-10%",
    4:"10-30%",
    5:"30-60%",
    6:"60-100%",
    7:"100%"
}

building_estimated_damage_image = {
    1:"tic.png",
    2:"1percent.png",
    3:"10percent.png",
    4:"10-30percent.png",
    5:"30-60percent.png",
    6:"60-100percent.png",
    7:"cross.png",
}

building_posting_l1_opts = {
    1:"%s (%s)" % (T("Inspected"), T("Green")),
    2:"%s (%s)" % (T("Restricted Use"), T("Yellow")),
    3:"%s (%s)" % (T("Unsafe"), T("Red")),
}

building_posting_l2_opts = {
    1:"%s (%s): G1" % (T("Inspected"), T("Green")),
    2:"%s (%s): G2" % (T("Inspected"), T("Green")),
    3:"%s (%s): Y1" % (T("Restricted Use"), T("Yellow")),
    4:"%s (%s): Y2" % (T("Restricted Use"), T("Yellow")),
    5:"%s (%s): R1" % (T("Unsafe"), T("Red")),
    6:"%s (%s): R2" % (T("Unsafe"), T("Red")),
    7:"%s (%s): R3" % (T("Unsafe"), T("Red")),
}

def uuid8anum():
    import uuid
    return "%s-%s" % (str(uuid.uuid4())[0:4], str(uuid.uuid4())[4:8])

s3uuid_8char = SQLCustomType(type = "string",
                             native = "VARCHAR(64)",
                             encoder = (lambda x: "'%s'" % (uuid8anum() if x == "" else str(x).replace("'", "''"))),
                             decoder = (lambda x: x))

# NZSEE Level 1 (~ATC-20 Rapid Evaluation) Safety Assessment Form ---------
resourcename = "nzseel1"
tablename = "%s_%s" % (module, resourcename)
db.define_table(tablename,
                Field("ticket_id",
                      type=s3uuid_8char,
                      length=64,
                      notnull=True,
                      unique=True,
                      writable=False,
                      default=uuid8anum(),
                      label = T("Ticket ID"),
                      represent = lambda id: id and id.upper() or T("None")
                      ),
                person_id(label=T("Inspector ID"), empty=False), # pre-populated in Controller
                organisation_id(label=T("Territorial Authority")), # Affiliation in ATC20 terminology
                Field("date", "datetime", default=request.now,
                      requires=IS_DATETIME(format=s3_datetime_format),
                      label=T("Inspection date and time")),
                #Field("daytime", "time", label=T("Inspection time")),
                Field("area", "integer", label=T("Areas inspected"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_area_inspected)),
                      represent=lambda opt: \
                      building_area_inspected.get(opt, UNKNOWN_OPT)),
                #Field("name", label=T("Building Name"), requires=IS_NOT_EMPTY()), # Included in location_id
                location_id(empty=False),
                Field("name_short",
                      label=T("Building Short Name/Business Name")),
                Field("contact_name",
                      label=T("Contact Name"),
                      requires=IS_NOT_EMPTY()),
                Field("contact_phone", label=T("Contact Phone"),
                      requires=IS_NOT_EMPTY()),
                Field("stories_above", "integer",
                      label=T("Storeys at and above ground level")), # Number of stories above ground
                Field("stories_below", "integer",
                      label=T("Below ground level")), # Number of stories below ground
                Field("footprint", "integer",
                      label=T("Total gross floor area (square meters)")),
                Field("year_built", "integer",
                      label=T("Year built")),
                Field("residential_units", "integer",
                      label=T("Number of residential units")),
                #Field("residential_units_not_habitable", "integer",
                #      label=T("Number of residential units not habitable")),
                Field("photo", "boolean",
                      label=T("Photo Taken?"),
                      represent = s3_yes_no_represent),
                Field("construction_type", "integer",
                      label=T("Type of Construction"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_construction_types)),
                      represent=lambda opt: \
                      building_construction_types.get(opt, UNKNOWN_OPT)),
                Field("construction_type_other",
                      label="(%s)" % T("specify")),
                Field("primary_occupancy", "integer",
                      label=T("Primary Occupancy"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_primary_occupancy_opts)),
                      represent=lambda opt: building_primary_occupancy_opts.get(opt, UNKNOWN_OPT)),
                Field("primary_occupancy_other",
                      label="(%s)" % T("specify")),
                Field("collapse", "integer",
                      label=T("Collapse, partial collapse, off foundation"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("leaning", "integer",
                      label=T("Building or storey leaning"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural", "integer",
                      label=T("Wall or other structural damage"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("falling", "integer",
                      label=T("Overhead falling hazard"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("slips", "integer",
                      label=T("Ground movement, settlement, slips"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("neighbour", "integer",
                      label=T("Neighbouring building hazard"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("other", "integer", label=T("Other"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("other_details",
                      label="(%s)" % T("specify")),
                Field("action_comments", "text",
                      label=T("Comments")),
                Field("posting", "integer",
                      requires=IS_IN_SET(building_posting_l1_opts),
                      represent=lambda opt: \
                      building_posting_l1_opts.get(opt, UNKNOWN_OPT)),
                Field("restrictions", "text",
                      label=T("Record any restriction on use or entry")),
                #Field("posting_comments", "text", label=T("Comments")),
                Field("barricades", "boolean",
                      label=T("Barricades are needed"),
                      represent = s3_yes_no_represent),
                Field("barricades_details", "text",
                      label="(%s)" % T("state location")),
                Field("detailed_evaluation", "boolean",
                      label=T("Level 2 or detailed engineering evaluation recommended"),
                      represent = s3_yes_no_represent),
                Field("detailed_structural", "boolean",
                      label=T("Structural"),
                      represent = s3_yes_no_represent),
                Field("detailed_geotechnical", "boolean",
                      label=T("Geotechnical"),
                      represent = s3_yes_no_represent),
                Field("detailed_other", "boolean",
                      label=T("Other"),
                      represent = s3_yes_no_represent),
                Field("detailed_other_details",
                      label="(%s)" % T("specify")),
                Field("other_recommendations", "text",
                      label=T("Other recommendations")),
                Field("estimated_damage", "integer",
                      label=T("Estimated Overall Building Damage"),
                      comment="(%s)" % T("Exclude contents"),
                      requires=IS_IN_SET(building_estimated_damage),
                      represent=lambda opt: \
                      building_estimated_damage.get(opt, UNKNOWN_OPT)),
                *s3_meta_fields())

# CRUD strings
ADD_ASSESSMENT = T("Add Level 1 Assessment")
s3.crud_strings[tablename] = Storage(
    label_create = ADD_ASSESSMENT,
    title_display = T("Level 1 Assessment Details"),
    title_list = T("Level 1 Assessments"),
    title_update = T("Edit Level 1 Assessment"),
    label_list_button = T("List Level 1 Assessments"),
    label_delete_button = T("Delete Level 1 Assessment"),
    msg_record_created = T("Level 1 Assessment added"),
    msg_record_modified = T("Level 1 Assessment updated"),
    msg_record_deleted = T("Level 1 Assessment deleted"),
    msg_list_empty = T("No Level 1 Assessments currently registered"))

building_nzseel1_search = s3base.S3Search(
        name="nzseel1_search_simple",
        label=T("Ticket ID"),
        comment=T("To search for an assessment, enter any portion of the ticket number of the assessment. You may use % as wildcard. Press 'Search' without input to list all assessments."),
        field=["ticket_id"])

# Set as default search method
s3db.configure(tablename,
                search_method=building_nzseel1_search)
# -------------------------------------------------------------------------

# NZSEE Level 2 (~ATC-20 Rapid Evaluation) Safety Assessment Form
resourcename = "nzseel2"
tablename = "%s_%s" % (module, resourcename)

db.define_table(tablename,
                Field("ticket_id",
                      type=s3uuid_8char,
                      length=64,
                      notnull=True,
                      unique=True,
                      label = T("Ticket ID"),
                      represent = lambda id: id and id.upper() or T("None")),
                person_id(label=T("Inspector ID"), empty=False), # pre-populated in Controller
                organisation_id(label=T("Territorial Authority")), # Affiliation in ATC20 terminology
                Field("date", "datetime", default=request.now,
                      requires=IS_DATETIME(format=s3_datetime_format),
                      label=T("Inspection date and time")),
                #Field("daytime", "time", label=T("Inspection time")),
                Field("area", "integer", label=T("Areas inspected"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_area_inspected)),
                      represent=lambda opt:
                      building_area_inspected.get(opt, UNKNOWN_OPT)),
                #Field("name", label=T("Building Name"), requires=IS_NOT_EMPTY()), # Included in location_id
                location_id(empty=False),
                Field("name_short",
                      label=T("Building Short Name/Business Name")),
                Field("contact_name",
                      label=T("Contact Name"),
                      requires=IS_NOT_EMPTY()),
                Field("contact_phone",
                      label=T("Contact Phone"),
                      requires=IS_NOT_EMPTY()),
                Field("stories_above", "integer",
                      label=T("Storeys at and above ground level")), # Number of stories above ground
                Field("stories_below", "integer",
                      label=T("Below ground level")), # Number of stories below ground
                Field("footprint", "integer",
                      label=T("Total gross floor area (square meters)")),
                Field("year_built", "integer",
                      label=T("Year built")),
                Field("residential_units", "integer",
                      label=T("Number of residential units")),
                #Field("residential_units_not_habitable", "integer",
                #      label=T("Number of residential units not habitable")),
                Field("photo", "boolean",
                      label=T("Photo Taken?"),
                      represent = s3_yes_no_represent),
                Field("construction_type", "integer",
                      label=T("Type of Construction"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_construction_types)),
                      represent=lambda opt: \
                      building_construction_types.get(opt, UNKNOWN_OPT)),
                Field("construction_type_other",
                      label="(%s)" % T("specify")),
                Field("primary_occupancy", "integer",
                      label=T("Primary Occupancy"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_primary_occupancy_opts)),
                      represent=lambda opt: \
                      building_primary_occupancy_opts.get(opt, UNKNOWN_OPT)),
                Field("primary_occupancy_other",
                      label="(%s)" % T("specify")),
                Field("collapse", "integer",
                      label=T("Collapse, partial collapse, off foundation"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("leaning", "integer",
                      label=T("Building or storey leaning"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural", "integer",
                      label=T("Wall or other structural damage"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("falling", "integer",
                      label=T("Overhead falling hazard"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("slips", "integer",
                      label=T("Ground movement, settlement, slips"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("neighbour", "integer",
                      label=T("Neighbouring building hazard"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("other", "integer",
                      label=T("Electrical, gas, sewerage, water, hazmats"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                #Field("other_details", label="(%s)" % T("specify")),
                Field("action_comments", "text",
                      label=T("Comments")),
                Field("posting_existing", "integer",
                      label=T("Existing Placard Type"),
                      requires=IS_IN_SET(building_posting_l1_opts),
                      represent=lambda opt: \
                      building_posting_l1_opts.get(opt, UNKNOWN_OPT)),
                Field("posting", "integer",
                      label=T("Choose a new posting based on the new evaluation and team judgement. Severe conditions affecting the whole building are grounds for an UNSAFE posting.  Localised Severe and overall Moderate conditions may require a RESTRICTED USE.  Place INSPECTED placard at main entrance. Post all other placards at every significant entrance."),
                      requires=IS_IN_SET(building_posting_l2_opts),
                      #@ToDo: comment= Guidance on meaning of options
                      represent=lambda opt: \
                      building_posting_l2_opts.get(opt, UNKNOWN_OPT)),
                Field("restrictions", "text",
                      label=T("Record any restriction on use or entry")),
                #Field("posting_comments", "text", label=T("Comments")),
                Field("barricades", "boolean",
                      label=T("Barricades are needed"),
                      represent = s3_yes_no_represent),
                Field("barricades_details", "text",
                      label="(%s)" % T("state location")),
                Field("detailed_evaluation", "boolean",
                      label=T("Level 2 or detailed engineering evaluation recommended"),
                      represent = s3_yes_no_represent),
                Field("detailed_structural", "boolean",
                      label=T("Structural"),
                      represent = s3_yes_no_represent),
                Field("detailed_geotechnical", "boolean",
                      label=T("Geotechnical"),
                      represent = s3_yes_no_represent),
                Field("detailed_other", "boolean",
                      label=T("Other"),
                      represent = s3_yes_no_represent),
                Field("detailed_other_details",
                      label="(%s)" % T("specify")),
                Field("other_recommendations", "text",
                      label=T("Other recommendations")),
                Field("estimated_damage", "integer",
                      label=T("Estimated Overall Building Damage"),
                      comment="(%s)" % T("Exclude contents"),
                      requires=IS_IN_SET(building_estimated_damage),
                      represent=lambda opt: \
                      building_estimated_damage.get(opt, UNKNOWN_OPT)),
                Field("structural_foundations", "integer",
                      label=T("Foundations"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural_roofs", "integer",
                      label=T("Roofs, floors (vertical load)"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural_columns", "integer",
                      label=T("Columns, pilasters, corbels"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural_diaphragms", "integer",
                      label=T("Diaphragms, horizontal bracing"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural_precast", "integer",
                      label=T("Pre-cast connections"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("structural_beam", "integer",
                      label=T("Beam"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_parapets", "integer",
                      label=T("Parapets, ornamentation"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_cladding", "integer",
                      label=T("Cladding, glazing"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_ceilings", "integer",
                      label=T("Ceilings, light fixtures"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_interior", "integer",
                      label=T("Interior walls, partitions"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_elevators", "integer",
                      label=T("Elevators"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_stairs", "integer",
                      label="%s/ %s" % (T("Stairs"), T("Exits")),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_utilities", "integer",
                      label=T("Utilities"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      comment= "(%s)" % T("eg. gas, electricity, water"),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("non_other", "integer",
                      label=T("Other"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("geotechnical_slope", "integer",
                      label=T("Slope failure, debris"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("geotechnical_ground", "integer",
                      label=T("Ground movement, fissures"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("geotechnical_soil", "integer",
                      label=T("Soil bulging, liquefaction"),
                      requires=IS_EMPTY_OR(IS_IN_SET(building_evaluation_condition)),
                      represent=lambda opt: \
                      building_evaluation_condition.get(opt, UNKNOWN_OPT)),
                Field("general_comments", "text",
                      label=T("General Comment")),
                Field("sketch", "upload",
                      autodelete=True,
                      requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                      error_message=T("Upload an image file (bmp, gif, jpeg or png), max. 300x300 pixels!"))),
                      label=T("Sketch"),
                      comment=S3PopupLink(c="doc",
                                          f="image",
                                          label=T("Add Photo"),
                                          title=T("Sketch"),
                                          tooltip=T("Provide an optional sketch of the entire building or damage points. Indicate damage points.")
                                          )),
                Field("recommendations", "text",
                      label=T("Recommendations for Repair and Reconstruction or Demolition"),
                      comment="(%s)" % T("Optional")),
                *s3_meta_fields())

# CRUD strings
ADD_ASSESSMENT = T("Add Level 2 Assessment")
s3.crud_strings[tablename] = Storage(
    label_create = ADD_ASSESSMENT,
    title_display = T("Level 2 Assessment Details"),
    title_list = T("Level 2 Assessments"),
    title_update = T("Edit Level 2 Assessment"),
    label_list_button = T("List Level 2 Assessments"),
    label_delete_button = T("Delete Level 2 Assessment"),
    msg_record_created = T("Level 2 Assessment added"),
    msg_record_modified = T("Level 2 Assessment updated"),
    msg_record_deleted = T("Level 2 Assessment deleted"),
    msg_list_empty = T("No Level 2 Assessments currently registered"))

building_nzseel2_search = s3base.S3Search(
        name="nzseel2_search_simple",
        label=T("Ticket ID"),
        comment=T("To search for an assessment, enter any portion the ticket number of the assessment. You may use % as wildcard. Press 'Search' without input to list all assessments."),
        field=["ticket_id"])

# Set as default search method
s3db.configure(tablename,
                search_method=building_nzseel2_search)


# -----------------------------------------------------------------------------
# Controllers
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# NZSEE Level 1 (~ATC-20 Rapid Evaluation) Safety Assessment Form -------------
def nzseel1():

    """
        RESTful CRUD controller
        @ToDo: Action Button to create a new L2 Assessment from an L1
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-populate Inspector ID
    table.person_id.default = auth.s3_logged_in_person()

    # Subheadings in forms:
    s3db.configure(tablename,
        deletable=False,
        create_next = URL(module,resourcename, args="[id]"),
        subheadings = {"name": ".", # Description in ATC-20
                       "collapse": "%s / %s" % (T("Overall Hazards"), T("Damage")),
                       "posting": ".",
                       "barricades": "%s:" % T("Further Action Recommended"),
                       "estimated_damage": ".",
                       })

    rheader = nzseel1_rheader

    output = s3_rest_controller(rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def nzseel1_rheader(r, tabs=[]):
    """ Resource Headers """

    if r.representation == "html":
        if r.name == "nzseel1":
            assess = r.record
            if assess:
                table = r.table
                rheader_tabs = s3_rheader_tabs(r, tabs)
                location = assess.location_id
                if location:
                    location = table.location_id.represent(location)
                person = assess.person_id
                if person:
                    query = (db.pr_person.id == person)
                    pe_id = db(query).select(db.pr_person.pe_id,
                                             limitby=(0, 1)).first().pe_id
                    query = (db.pr_contact.pe_id == pe_id) & \
                            (db.pr_contact.contact_method == "SMS")
                    mobile = db(query).select(db.pr_contact.value,
                                              limitby=(0, 1)).first()
                    if mobile:
                        mobile = mobile.value
                    person = s3_fullname(person)
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Person")), person,
                                    TH("%s: " % T("Mobile")), mobile,
                                  ),
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH("%s: " % T("Date")), table.date.represent(assess.date)
                                  ),
                                TR(
                                    TH(""), "",
                                    TH("%s: " % T("Ticket ID")),
                                        r.table.ticket_id.represent(assess.ticket_id),
                                  ),
                                ),
                              rheader_tabs)

                return rheader
    return None

# -----------------------------------------------------------------------------
# NZSEE Level 2 (~ATC-20 Rapid Evaluation) Safety Assessment Form
def nzseel2():

    """
        RESTful CRUD controller
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-populate Inspector ID
    table.person_id.default = auth.s3_logged_in_person()

    # Subheadings in forms:
    s3db.configure(tablename,
        deletable=False,
        create_next = URL(module,resourcename, args="[id]"),
        subheadings = {"name": ".", # Description in ATC-20
                       "collapse": "%s / %s" % (T("Overall Hazards"), T("Damage")),
                       "posting_existing": ".",
                       "barricades": "%s:" % T("Further Action Recommended"),
                       "estimated_damage": ".",
                       "structural_foundations": "%s / %s" % (T("Structural Hazards"), T("Damage")),
                       "non_parapets": "%s / %s" % (T("Non-structural Hazards"), T("Damage")),
                       "geotechnical_slope": "%s / %s" % (T("Geotechnical Hazards"), T("Damage")),
                       })

    rheader = nzseel2_rheader

    output = s3_rest_controller(rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def nzseel2_rheader(r, tabs=[]):
    """ Resource Headers """

    if r.representation == "html":
        if r.name == "nzseel2":
            assess = r.record
            if assess:
                table = r.table
                rheader_tabs = s3_rheader_tabs(r, tabs)
                location = assess.location_id
                if location:
                    location = table.location_id.represent(location)
                person = assess.person_id
                if person:
                    query = (db.pr_person.id == person)
                    pe_id = db(query).select(db.pr_person.pe_id,
                                             limitby=(0, 1)).first().pe_id
                    query = (db.pr_contact.pe_id == pe_id) & \
                            (db.pr_contact.contact_method == "SMS")
                    mobile = db(query).select(db.pr_contact.value,
                                              limitby=(0, 1)).first()
                    if mobile:
                        mobile = mobile.value
                    person = s3_fullname(person)
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Person")), person,
                                    TH("%s: " % T("Mobile")), mobile,
                                  ),
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH("%s: " % T("Date")), table.date.represent(assess.date)
                                  ),
                                TR(
                                    TH(""), "",
                                    TH("%s: " % T("Ticket ID")),
                                        r.table.ticket_id.represent(assess.ticket_id),
                                  ),
                                ),
                              rheader_tabs)

                return rheader
    return None

# -----------------------------------------------------------------------------
def report():
    """
        A report providing assessment totals, and breakdown by assessment type and status.
        e.g. Level 1 (red, yellow, green) Level 2 (R1-R3, Y1-Y2, G1-G2)

        @ToDo: Make into a Custom Method to be able to support Table ACLs
        (currently protected by Controller ACL)
    """

    level1 = Storage()
    table = db.building_nzseel1
    # Which is more efficient?
    # A) 4 separate .count() in DB
    # B) Pulling all records into Python & doing counts in Python
    query = (table.deleted == False)
    level1.total = db(query).count()
    filter = (table.posting == 1)
    level1.green = db(query & filter).count()
    filter = (table.posting == 2)
    level1.yellow = db(query & filter).count()
    filter = (table.posting == 3)
    level1.red = db(query & filter).count()

    level2 = Storage()
    table = db.building_nzseel2
    query = (table.deleted == False)
    level2.total = db(query).count()
    filter = (table.posting.belongs((1, 2)))
    level2.green = db(query & filter).count()
    filter = (table.posting.belongs((3, 4)))
    level2.yellow = db(query & filter).count()
    filter = (table.posting.belongs((5, 6, 7)))
    level2.red = db(query & filter).count()

    return dict(level1=level1,
                level2=level2)

# -----------------------------------------------------------------------------
#def getformatedData(dbresult):
#    result = []
#    cnt = -1;
#    # Format the results
#    for row in dbresult:
#        damage = row.estimated_damage
#        try:
#            trueDate = row.date #datetime.datetime.strptime(row.date, "%Y-%m-%d %H:%M:%S")
#        except:
#            trueDate = row.created_on
#        date = trueDate.strftime("%d %b %Y")
#        hour = trueDate.strftime("%H")
#        key = (date, hour)
#        if (cnt == -1) or (result[cnt][0] != key):
#            result.append([key , 0, 0, 0, 0, 0, 0, 0, 1])
#            cnt += 1
#        else:
#            result[cnt][8] += 1
#        result[cnt][damage] += 1
#
#    return result

def getformatedData(dbresult):
    result = []
    cntT = cntH = -1
    for row in dbresult:
        damage = row.estimated_damage
        try:
            trueDate = row.date
        except:
            trueDate = row.created_on
        date = trueDate.strftime("%d %b %Y")
        hour = trueDate.strftime("%H")
        keyT = (date, "Total")
        keyH = (date, hour)
        if (cntT == -1) or (result[cntT][0] != keyT):
            result.append([keyT, 0, 0, 0, 0, 0, 0, 0, 0])
            cntT = cntH + 1
            cntH = cntT
        if (result[cntH][0] != keyH):
            result.append([keyH, 0, 0, 0, 0, 0, 0, 0, 0])
            cntH += 1
        result[cntT][8] += 1
        result[cntH][8] += 1
        result[cntT][damage] += 1
        result[cntH][damage] += 1

    return result


def timeline():
    """
        A report providing assessments received broken down by time
    """
    result = Storage()
    inspection = []
    creation = []
    # raw SQL command
    # select `date`, estimated_damage FROM building_nzseel1 WHERE deleted = "F" ORDER BY `date` DESC

    table = db.building_nzseel1
    dbresult = db(table.deleted == False).select(table.date,
                                                 table.estimated_damage,
                                                 orderby=~table.date,
                                                )
    inspection = getformatedData(dbresult)

    # Here is the raw SQL command
    # select created_on, estimated_damage FROM building_nzseel1 WHERE deleted = "F" ORDER BY created_on DESC
    dbresult = db(table.deleted == False).select(table.created_on,
                                                 table.estimated_damage,
                                                 orderby=~table.created_on,
                                                )
    creation = getformatedData(dbresult)

    totals = [0, 0, 0, 0, 0, 0, 0, 0]
    for line in inspection:
        if line[0][1] == "Total":
            for i in range(8):
                totals[i] += line[i + 1]

    return dict(inspection=inspection,
                creation=creation,
                totals= totals
                )

# -----------------------------------------------------------------------------

def adminLevel():
    """
        A report providing assessments received broken down by administration level
    """
    # raw SQL command
    # select parent, `path`, estimated_damage FROM building_nzseel1, gis_location WHERE building_nzseel1.deleted = "F" and (gis_location.id = building_nzseel1.location_id)
    tableNZ1 = db.building_nzseel1
    ltable = s3db.gis_location
    query = (tableNZ1.location_id == ltable.id) & (tableNZ1.deleted == False)
    dbresult = db(query).select(ltable.path,
                                ltable.parent,
                                tableNZ1.estimated_damage
                               )

    result = []
    temp = {}

    # Format the results
    for row in dbresult:
        parent = row.gis_location.parent ##report[0]
        path   = row.gis_location.path #report[1]
        damage = row.building_nzseel1.estimated_damage #report[2]

        if parent in temp:
            temp[parent][7] += 1
        else:
            temp[parent] = [0, 0, 0, 0, 0, 0, 0, 1]
        temp[parent][damage - 1] += 1
    gis = {}
    for (key) in temp.keys():
        # raw SQL command
        # "select name, parent FROM gis_location WHERE gis_location.id = '%s'" % key
        row = ltable(key)
        if row == None:
            gis[key] = T("Unknown")
        else:
            gis[key] = row.name

    for (key, item) in temp.items():
        if gis.has_key(key):
            name = gis[key]
        else:
            name = T("Unknown")
        result.append((name, item))
    return dict(report=result,
                )

# -----------------------------------------------------------------------------

