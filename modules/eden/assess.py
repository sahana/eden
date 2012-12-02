# -*- coding: utf-8 -*-

""" Sahana Eden Assessments Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3AssessBuildingModel",
           "S3AssessCanvassModel",
           ]

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *

T = current.T

assess_additional_needs_opts = {
    1 : T("Shelter"),
    2 : T("Information -Mold -FEMA -Legal"),
    3 : T("Other"),
    4 : T("Food"),
    }

assess_construction_type_opts = {
    1 : T("Concrete"),
    2 : T("Brick"),
    3 : T("Wood Frame"),
    4 : T("Metal Stud"),
    4 : T("Other"),
    }

assess_damage_opts = {
    1 : T("Primarily Flood"),
    2 : T("Wind/Wind driven rain"),
    3 : T("Other"),
    }

assess_insurance_opts = {
    1 : T("Property"),
    2 : T("Flood (Structure)"),
    3 : T("Wind/Hurricane"),
    4 : T("Sewer Back-up"),
    5 : T("Flood (Contents)"),
    6 : T("NONE"),
    }

assess_property_type_opts = {
    1 : T("Single Family"),
    2 : T("Multi-Family/Apts"),
    3 : T("Residence is Vacation Home"),
    4 : T("Business"),
    }

assess_tools_opts = {
    1 : T("Pump/Hoses"),
    2 : T("Flat bar"),
    3 : T("Dust pan"),
    4 : T("Large pails"),
    5 : T("Long pry bar"),
    6 : T("Brooms"),
    7 : T("Shovels"),
    8 : T("Pick axe"),
    9 : T("Trash bags"),
    10 : T("Wheelbarrows"),
    11 : T("Hammers"),
    12 : T("Cleaning Supplies"),
    13 : T("Crowbar"),
    14 : T("Sledgehammer"),
    15 : "",
    16 : T("Nail pullers/cat's claws"),
    17 : T("Generator"),
    18 : T("Screwdrivers"),
    19 : T("Chalk line"),
    20 : T("Portable lights"),
    21 : T("Wrench"),
    22 : T("Sawzall"),
    23 : T("Extension cords"),
    24 : "",
    25 : T("Utility knives"),
    26 : T("Headlamps"),
    21 : "",
    }

assess_mold_removal_opts = {
    1 : T("Wire brush"),
    2 : T("Demolding solution"),
    3 : T("Tyvek suits"),
    4 : T("Grinder"),
    5 : T("Paint brushes"),
    6 : T("Goggles"),
    7 : T("Shop vac + HEPA filter"),
    8 : T("Cloth rags"),
    9 : T("Rubber gloves"),
    10 : T("Ladder/step stool"),
    11 : T("Kllz"),
    #12 : T("Ladder/step stool""),
    }

assess_personal_protection_opts = {
    1 : T("N95 Dust masks"),
    2 : T("Rubber Boots"),
    4 : T("Respirators"),
    5 : T("Work gloves"),
    7 : T("Safety glasses"),
    8 : T("Hard hats"),
    10 : T("Boots"),
    11 : T("Ear plugs"),
    }

assess_skills_required_opts = {
    1 : T("Pump equipment"),
    2 : T("Mold removal"),
    3 : T("Demolition/gutting"),
    4 : T("Construction"),
    }

assess_special_skills_opts = {
    1 : T("Plumber"),
    2 : T("Engineer"),
    3 : T("Electrician"),
    4 : T("Other"),
    }

assess_vulnerability_opts = {
    1 : T("Elderly"),
    2 : T("Disabled"),
    3 : T("Small Children"),
    4 : T("Single Female Head of Household"),
    }

assess_work_requested_opts = {
    1 : T("Pump out water"),
    2 : T("Mud/sand removal"),
    3 : T("Demolition/Gutting"),
    4 : T("Clean up debris"),
    5 : T("Mold removal"),
    6 : T("Sanitization"),
    }

# =============================================================================
class S3AssessBuildingModel(S3Model):
    """
        Building Damage Assessment form
    """

    names = ["assess_building",
             ]

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Building Assessment
        #
        approved_opts = {
            1 : T("Approved"),
            2 : T("Rejected"),
            }
        assess_status_opts = {
            1 : T("Assessed"),
            2 : T("Ready to Start"),
            3 : T("In-Progress"),
            4 : T("Finished"),
            }
        building_status_opts = {
            1 : T("Green"),
            2 : T("Yellow"),
            3 : T("Red (unsafe)"),
            }
        on_off_opts = {
            1 : T("On"),
            2 : T("Off"),
            } 
        ownership_opts = {
            1: T("Rent"),
            2: T("Own"),
            }
        yes_no_opts = {
            1: T("Yes"),
            2: T("No"),
            }

        tablename = "assess_building"
        table = self.define_table(tablename,
                                  Field("database_id",
                                        label=T("Database ID")),
                                  Field("status", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_status_opts)
                                                ),
                                        represent = lambda opt:
                                            assess_status_opts.get(opt,
                                                                   UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=4, **attr),
                                        label=T("Status")),
                                  s3_date(label=T("Intake Date")),
                                  Field("assessor1",
                                        label=T("Assessor 1")),
                                  Field("assessor2",
                                        label=T("Assessor 2")),
                                  Field("name",
                                        label=T("Name")),
                                  Field("phone",
                                        requires=IS_NULL_OR(s3_phone_requires),
                                        label=T("Phone Number")),
                                  self.gis_location_id(),
                                  Field("homeowner_availability",
                                        label=T("Homeowner Availability")),
                                  Field("type_of_property", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_property_type_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_property_type_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=4, **attr),
                                        label=T("Type of Property")),
                                  Field("inhabitants", "integer",
                                        label=T("# of Inhabitants")),
                                  Field("year_built", "integer",
                                        requires = IS_EMPTY_OR(
                                                    IS_INT_IN_RANGE(1800, 2012)
                                                    ),
                                        label=T("Year Built")),
                                  Field("current_residence", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Current Residence")),
                                  Field("ownership", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(ownership_opts)
                                                ),
                                        represent = lambda opt: \
                                            ownership_opts.get(opt,
                                                               UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Ownership")),
                                  Field("intention",
                                        label=T("Intention to Stay Home")),
                                  Field("vulnerability", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_vulnerability_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_vulnerability_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=4, **attr),
                                        label=T("Vulnerabilities")),
                                  Field("building_status", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(building_status_opts)
                                                ),
                                        represent = lambda opt:
                                            building_status_opts.get(opt,
                                                                     UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=3, **attr),
                                        label=T("Based on the DOB/FEMA sticker, the property is")),
                                  Field("insurance", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_insurance_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_insurance_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                                        label=T("Type of Insurance")),
                                  Field("work_requested", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_work_requested_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_work_requested_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                                        label=T("Work Requested")),
                                  Field("construction_type", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_work_requested_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_work_requested_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=4, **attr),
                                        label=T("Construction Type (Check all that apply)"),
                                        ),
                                  Field("electricity", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(on_off_opts)
                                                ),
                                        represent = lambda opt: \
                                            on_off_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Electricity")),
                                  Field("gas", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(on_off_opts)
                                                ),
                                        represent = lambda opt: \
                                            on_off_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Gas")),
                                  Field("basement_flooding", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Basement Flooding")),
                                  Field("basement_flooding_depth", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_INT_IN_RANGE(1, 99)
                                                    ),
                                        label=T("Depth (feet)"),
                                        ),
                                  Field("drywall", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Drywall")),
                                  Field("floor", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Floor")),
                                  Field("remove_loose_debris", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Remove Loose Debris")),
                                  Field("remove_furniture", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Remove Furniture")),
                                  Field("remove_water_heater", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Remove Water Heater")),
                                  Field("remove_appliances", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Remove Major Appliances")),
                                  Field("damage_source", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_damage_opts)
                                                ),
                                        represent = lambda opt: \
                                            assess_damage_opts.get(opt,
                                                                   UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=3, **attr),
                                        label=T("Damage Source")),
                                  Field("damage_source_other",
                                        label=T("Other")),
                                  s3_comments("damage_details",
                                              label=T("Additional Description of Damage"),
                                              comment=None,
                                              ),
                                  s3_comments("work_plan",
                                              label=T("Work Plan"),
                                              comment=T("Describe access points, advice for team leaders"),
                                              ),
                                  Field("tools_required", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_tools_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_tools_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                                        label=T("Tools and materials required"),
                                        ),
                                  s3_comments("tools_other",
                                              comment=None,
                                              label=T("Tools Other")),
                                  Field("mold_equipment", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_mold_removal_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_mold_removal_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                                        label=T("Mold removal equipment"),
                                        ),
                                  Field("personal_protectivity", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_personal_protection_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_personal_protection_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                                        label=T("All Teams Must Have Personal Protectivity Equipment"),
                                        ),
                                  Field("skills_required", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_skills_required_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_skills_required_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                                        label=T("Special Skills Required"),
                                        ),
                                  Field("special_skills_required", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_special_skills_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_special_skills_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                                        label=T("Special Skills Required"),
                                        ),
                                  s3_comments("special_skills_other",
                                              comment=None,
                                              label=T("Other")),
                                  Field("estimated_volunteers",
                                        label=T("Estimated Volunteers"),
                                        ),
                                  Field("estimated_days",
                                        label=T("Estimated Days"),
                                        ),
                                  Field("additional_needs", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_additional_needs_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_additional_needs_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                                        label=T("Additional Needs"),
                                        ),
                                  Field("approval", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(approved_opts)
                                                ),
                                        represent = lambda opt:
                                            approved_opts.get(opt,
                                                             UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Approved")),
                                  s3_comments("approval_details",
                                              comment=None,
                                              label=T("Details")),
                                  Field("permission", "integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(yes_no_opts)
                                                ),
                                        represent = lambda opt: \
                                            yes_no_opts.get(opt,
                                                            UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                        label=T("Permission from Owner to Work")),
                                  s3_date("date_ready",
                                          label=T("Date Ready")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_ASSESS = T("Add Assessment")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ASSESS,
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            title_search = T("Search Assessments"),
            subtitle_create = T("Add New Assessment"),
            label_list_button = T("List Assessments"),
            label_create_button = ADD_ASSESS,
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        building_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                        name="building_search_advanced",
                        label=T("Name, and/or ID"),
                        comment=T("To search for a building assessment, enter the name or ID. You may use % as wildcard. Press 'Search' without input to list all assessments."),
                        field=["name",
                               "database_id",
                               ]
                      ),
                      S3SearchOptionsWidget(
                        name="building_search_status",
                        label=T("Status"),
                        field="status",
                        options = assess_status_opts,
                        cols = 3
                      ))
            )

        self.configure(tablename,
                       search_method = building_search,
                       subheadings = {
                        T("Damages"): "electricity",
                        }
                       )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
class S3AssessCanvassModel(S3Model):
    """
        Building Canvassing form
    """

    names = ["assess_canvass",
             ]

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Canvassing
        #
        status_opts = {
            1 : T("Not actioned"),
            2 : T("Actioned"),
            }

        tablename = "assess_canvass"
        table = self.define_table(tablename,
                                  Field("status", "integer",
                                        default = 1,
                                        requires = IS_IN_SET(status_opts),
                                        represent = lambda opt:
                                            status_opts.get(opt,
                                                                   UNKNOWN_OPT),
                                        widget = lambda f, v, **attr: \
                                            SQLFORM.widgets.radio.widget(f, v, cols=4, **attr),
                                        label=T("Status")),
                                  s3_date(),
                                  self.gis_location_id(),
                                  Field("type_of_property", "list:integer",
                                        requires=IS_EMPTY_OR(
                                                    IS_IN_SET(assess_property_type_opts,
                                                              multiple=True)
                                                ),
                                        represent = lambda ids: \
                                            assess_multi_type_represent(ids,
                                                                        assess_property_type_opts),
                                        widget = lambda f, v, **attr: \
                                            CheckboxesWidgetS3.widget(f, v, cols=4, **attr),
                                        label=T("Type of Property")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_ASSESS = T("Add Assessment")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ASSESS,
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            title_search = T("Search Assessments"),
            subtitle_create = T("Add New Assessment"),
            label_list_button = T("List Assessments"),
            label_create_button = ADD_ASSESS,
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        canvass_search = S3Search(
            advanced=(S3SearchSimpleWidget(
                        name="canvass_search_advanced",
                        label=T("Building Name or Address"),
                        comment=T("To search for a building canvass assessment, enter the Building Name or Addresss. You may use % as wildcard. Press 'Search' without input to list all assessments."),
                        field=["location_id$name",
                               "location_id$addr_street",
                               ]
                      ),
                      S3SearchOptionsWidget(
                        name="canvass_search_status",
                        label=T("Status"),
                        field="status",
                        options = status_opts,
                        cols = 3
                      ))
            )

        self.configure(tablename,
                       search_method = canvass_search,
                       )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3.*)
        #
        return Storage()

# =============================================================================
def assess_multi_type_represent(ids, opts):
    """
        Represent Multiple Types (list:integer)
    """

    if not ids:
        return current.messages["NONE"]

    ids = [ids] if type(ids) is not list else ids

    strings = [str(opts.get(id)) for id in ids]

    return ", ".join(strings)

# END =========================================================================
