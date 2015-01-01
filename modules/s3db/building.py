# -*- coding: utf-8 -*-

""" Sahana Eden Building Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3BuildingModel"]

from gluon import *
from gluon.sql import SQLCustomType
try:
    from gluon.dal.objects import Row
except ImportError:
    # old web2py
    from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3BuildingModel(S3Model):

    names = ("building_nzseel1",
             "building_nzseel2")

    def model(self):

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings
        request = current.request
        s3 = current.response.s3
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

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

        # NZSEE Level 1 (~ATC-20 Rapid Evaluation) Safety Assessment Form -----
        tablename = "building_nzseel1"
        self.define_table(tablename,
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

        # ---------------------------------------------------------------------

        # NZSEE Level 2 (~ATC-20 Rapid Evaluation) Safety Assessment Form
        tablename = "building_nzseel2"

        self.define_table(tablename,
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
                              comment=S3AddResourceLink(c="doc",
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

        return {}
# END =========================================================================