# -*- coding: utf-8 -*-

""" Sahana Eden Assessments Model

    @copyright: 2012-2014 (c) Sahana Software Foundation
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

__all__ = ("S3Assess24HModel",
           "S3AssessBuildingModel",
           "S3AssessCanvassModel",
           )

from gluon import *
from gluon.storage import Storage
from gluon.tools import callback
from ..s3 import *

T = current.T

# Common to both Building & Canvass
assess_property_type_opts = {
    1 : T("Single Family"),
    2 : T("Multi-Family/Apts"),
    3 : T("Residence is Vacation Home"),
    4 : T("Business"),
    }

# =============================================================================
class S3Assess24HModel(S3Model):
    """
        IFRC 24H Assessment form
    """

    names = ("assess_24h",
             )

    def model(self):

        T = current.T
        s3 = current.response.s3

        if s3.bulk:
            # Don't default the Team leader name for Bulk Imports
            default_person = None
        else:
            default_person = current.auth.s3_logged_in_person()

        # ---------------------------------------------------------------------
        # IFRC 24H Assessment
        #
        tablename = "assess_24h"
        self.define_table(tablename,
                          self.pr_person_id(
                            default = default_person,
                            label = ("Name of Assessment Team Leader"),
                            ),
                          s3_date(default = "now"),
                          self.gis_location_id(
                            widget = S3LocationSelector(show_map = False),
                            ),
                          Field("inhabitants", "integer",
                                label = T("Approximate number of inhabitants"),
                                ),
                          Field("inhabitants", "integer",
                                label = T("Approximate number of inhabitants"),
                                ),
                          self.pr_person_id("contact_id",
                            comment = None,
                            label = ("Name of contact person in the community"),
                            requires = IS_ADD_PERSON_WIDGET2(),
                            widget = S3AddPersonWidget2(),
                            ),
                          Field("injured", "integer",
                                label = T("# Injured"),
                                ),
                          Field("dead", "integer",
                                label = T("# Dead"),
                                ),
                          Field("missing", "integer",
                                label = T("# Missing"),
                                ),
                          Field("minor_damage", "integer",
                                label = T("# Minor Damage"),
                                ),
                          Field("moderate_damage", "integer",
                                label = T("# Moderate Damage"),
                                ),
                          Field("destroyed", "integer",
                                label = T("# Destroyed"),
                                ),
                          # tbc if-useful
                          *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            label_create = T("Create Assessment"),
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            label_list_button = T("List Assessments"),
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3AssessBuildingModel(S3Model):
    """
        Building Damage Assessment form
    """

    names = ("assess_building",
             "assess_building_rheader",
             )

    def model(self):

        T = current.T
        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

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
        assess_status2_opts = {
            1 : T("N/A"),
            2 : T("To be done"),
            3 : T("In-Progress"),
            4 : T("Finished"),
            }
        assess_priority_opts = {
            1 : T("High"),
            2 : T("Medium"),
            3 : T("Low"),
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

        #assess_tools_opts = {
        #    1 : T("Pump/Hoses"),
        #    2 : T("Flat bar"),
        #    3 : T("Dust pan"),
        #    4 : T("Large pails"),
        #    5 : T("Long pry bar"),
        #    6 : T("Brooms"),
        #    7 : T("Shovels"),
        #    8 : T("Pick axe"),
        #    9 : T("Trash bags"),
        #    10 : T("Wheelbarrows"),
        #    11 : T("Hammers"),
        #    12 : T("Cleaning Supplies"),
        #    13 : T("Crowbar"),
        #    14 : T("Sledgehammer"),
        #    15 : "",
        #    16 : T("Nail pullers/cat's claws"),
        #    17 : T("Generator"),
        #    18 : T("Screwdrivers"),
        #    19 : T("Chalk line"),
        #    20 : T("Portable lights"),
        #    21 : T("Wrench"),
        #    22 : T("Sawzall"),
        #    23 : T("Extension cords"),
        #    24 : "",
        #    25 : T("Utility knives"),
        #    26 : T("Headlamps"),
        #    21 : "",
        #    }

        #assess_mold_removal_opts = {
        #    1 : T("Wire brush"),
        #    2 : T("Demolding solution"),
        #    3 : T("Tyvek suits"),
        #    4 : T("Grinder"),
        #    5 : T("Paint brushes"),
        #    6 : T("Goggles"),
        #    7 : T("Shop vac + HEPA filter"),
        #    8 : T("Cloth rags"),
        #    9 : T("Rubber gloves"),
        #    10 : T("Ladder/step stool"),
        #    11 : T("Kllz"),
        #    #12 : T("Ladder/step stool""),
        #    }

        #assess_personal_protection_opts = {
        #    1 : T("N95 Dust masks"),
        #    2 : T("Rubber Boots"),
        #    4 : T("Respirators"),
        #    5 : T("Work gloves"),
        #    7 : T("Safety glasses"),
        #    8 : T("Hard hats"),
        #    10 : T("Boots"),
        #    11 : T("Ear plugs"),
        #    }

        #assess_skills_required_opts = {
        #    1 : T("Pump equipment"),
        #    2 : T("Mold removal"),
        #    3 : T("Demolition/gutting"),
        #    4 : T("Construction"),
        #    }

        #assess_special_skills_opts = {
        #    1 : T("Plumber"),
        #    2 : T("Engineer"),
        #    3 : T("Electrician"),
        #    4 : T("Other"),
        #    }

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

        tablename = "assess_building"
        self.define_table(tablename,
                          Field("database_id", "integer",
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
                          Field("status_gutting", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_IN_SET(assess_status2_opts)
                                        ),
                                represent = lambda opt:
                                    assess_status2_opts.get(opt,
                                                            UNKNOWN_OPT),
                                widget = lambda f, v, **attr: \
                                    SQLFORM.widgets.radio.widget(f, v, cols=4, **attr),
                                label=T("Gutting Status")),
                          Field("status_mold", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_IN_SET(assess_status2_opts)
                                        ),
                                represent = lambda opt:
                                    assess_status2_opts.get(opt,
                                                            UNKNOWN_OPT),
                                widget = lambda f, v, **attr: \
                                    SQLFORM.widgets.radio.widget(f, v, cols=4, **attr),
                                label=T("Mold Status")),
                          s3_comments("mold_notes",
                                      comment=None,
                                      label=T("Mold Notes")),
                          Field("priority", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_IN_SET(assess_priority_opts)
                                        ),
                                represent = lambda opt:
                                    assess_priority_opts.get(opt,
                                                            UNKNOWN_OPT),
                                widget = lambda f, v, **attr: \
                                    SQLFORM.widgets.radio.widget(f, v, cols=3, **attr),
                                label=T("Priority")),
                          s3_date(label=T("Intake Date")),
                          Field("assessor1",
                                represent = lambda v: v or NONE,
                                label=T("Assessor 1")),
                          Field("assessor2",
                                represent = lambda v: v or NONE,
                                label=T("Assessor 2")),
                          Field("name",
                                represent = lambda v: v or NONE,
                                label=T("Name")),
                          Field("phone",
                                requires=IS_EMPTY_OR(s3_phone_requires),
                                represent = lambda v: v or NONE,
                                label=T("Phone Number")),
                          Field("contact_other",
                                represent = lambda v: v or NONE,
                                label=T("Other Contact Information")),
                          self.gis_location_id(),
                          Field("homeowner_availability",
                                represent = lambda v: v or NONE,
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
                                represent = lambda v: v or NONE,
                                label=T("# of Inhabitants")),
                          Field("year_built", "integer",
                                requires = IS_EMPTY_OR(
                                            IS_INT_IN_RANGE(1800, 2012)
                                            ),
                                represent = lambda v: v or NONE,
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
                                represent = lambda v: v or NONE,
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
                                            IS_IN_SET(assess_construction_type_opts,
                                                        multiple=True)
                                        ),
                                represent = lambda ids: \
                                    assess_multi_type_represent(ids,
                                                                assess_construction_type_opts),
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
                                represent = lambda v: v or NONE,
                                label=T("Depth (feet)"),
                                ),
                          Field("first_flooding", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_IN_SET(yes_no_opts)
                                        ),
                                represent = lambda opt: \
                                    yes_no_opts.get(opt,
                                                    UNKNOWN_OPT),
                                widget = lambda f, v, **attr: \
                                    SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                label=T("First Floor Flooding")),
                          Field("first_flooding_depth", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_INT_IN_RANGE(1, 99)
                                            ),
                                represent = lambda v: v or NONE,
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
                          Field("asbestos", "integer",
                                requires=IS_EMPTY_OR(
                                            IS_IN_SET(yes_no_opts)
                                        ),
                                represent = lambda opt: \
                                    yes_no_opts.get(opt,
                                                    UNKNOWN_OPT),
                                widget = lambda f, v, **attr: \
                                    SQLFORM.widgets.radio.widget(f, v, cols=2, **attr),
                                label=T("Asbestos")),
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
                                represent = lambda v: v or NONE,
                                label=T("Other")),
                          s3_comments("damage_details",
                                      label=T("Additional Description of Damage"),
                                      comment=None,
                                      ),
                          s3_comments("work_plan",
                                      label=T("Work Plan"),
                                      comment=T("Describe access points, advice for team leaders"),
                                      ),
                          #Field("tools_required", "list:integer",
                          #      requires=IS_EMPTY_OR(
                          #                  IS_IN_SET(assess_tools_opts,
                          #                            multiple=True)
                          #              ),
                          #      represent = lambda ids: \
                          #          assess_multi_type_represent(ids,
                          #                                      assess_tools_opts),
                          #      widget = lambda f, v, **attr: \
                          #          CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                          #      label=T("Tools and materials required"),
                          #      ),
                          #s3_comments("tools_other",
                          #            comment=None,
                          #            label=T("Tools Other")),
                          #Field("mold_equipment", "list:integer",
                          #      requires=IS_EMPTY_OR(
                          #                  IS_IN_SET(assess_mold_removal_opts,
                          #                            multiple=True)
                          #              ),
                          #      represent = lambda ids: \
                          #          assess_multi_type_represent(ids,
                          #                                      assess_mold_removal_opts),
                          #      widget = lambda f, v, **attr: \
                          #          CheckboxesWidgetS3.widget(f, v, cols=3, **attr),
                          #      label=T("Mold removal equipment"),
                          #      ),
                          #Field("personal_protectivity", "list:integer",
                          #      requires=IS_EMPTY_OR(
                          #                  IS_IN_SET(assess_personal_protection_opts,
                          #                            multiple=True)
                          #              ),
                          #      represent = lambda ids: \
                          #          assess_multi_type_represent(ids,
                          #                                      assess_personal_protection_opts),
                          #      widget = lambda f, v, **attr: \
                          #          CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                          #      label=T("All Teams Must Have Personal Protectivity Equipment"),
                          #      ),
                          #Field("skills_required", "list:integer",
                          #      requires=IS_EMPTY_OR(
                          #                  IS_IN_SET(assess_skills_required_opts,
                          #                            multiple=True)
                          #              ),
                          #      represent = lambda ids: \
                          #          assess_multi_type_represent(ids,
                          #                                      assess_skills_required_opts),
                          #      widget = lambda f, v, **attr: \
                          #          CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                          #      label=T("Skills Required"),
                          #      ),
                          #Field("special_skills_required", "list:integer",
                          #      requires=IS_EMPTY_OR(
                          #                  IS_IN_SET(assess_special_skills_opts,
                          #                            multiple=True)
                          #              ),
                          #      represent = lambda ids: \
                          #          assess_multi_type_represent(ids,
                          #                                      assess_special_skills_opts),
                          #      widget = lambda f, v, **attr: \
                          #          CheckboxesWidgetS3.widget(f, v, cols=2, **attr),
                          #      label=T("Special Skills Required"),
                          #      ),
                          s3_comments("special_skills",
                                      comment=None,
                                      label=T("Special Tools and Skills")),
                          Field("estimated_volunteers",
                                represent = lambda v: v or NONE,
                                label=T("Estimated Volunteers"),
                                ),
                          Field("estimated_days",
                                represent = lambda v: v or NONE,
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
                          s3_comments("progress",
                                      comment=None,
                                      label=T("Progress and Notes")),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Assessment"),
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            label_list_button = T("List Assessments"),
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(["name",
                          "database_id",
                         ],
                         label = T("Name, and/or ID"),
                         comment = T("To search for a building assessment, enter the name or ID. You may use % as wildcard. Press 'Search' without input to list all assessments."),
                        ),
            S3OptionsFilter("status",
                            label = T("Status"),
                            options = assess_status_opts,
                            cols = 4,
                           ),
            S3OptionsFilter("status_gutting",
                            label = T("Gutting Status"),
                            options = assess_status2_opts,
                            cols = 4,
                           ),
            S3OptionsFilter("status_mold",
                            label = T("Mold Status"),
                            options = assess_status2_opts,
                            cols = 4,
                           ),
            S3OptionsFilter("priority",
                            label = T("Priority"),
                            options = assess_priority_opts,
                            cols = 3,
                           ),
        ]

        # Configuration
        self.configure(tablename,
                       onvalidation = self.assess_building_onvalidation,
                       filter_widgets = filter_widgets,
                       subheadings = {
                        T("Damages"): "electricity",
                        }
                       )

        # Generate Work Order
        self.set_method("assess", "building",
                        method="form",
                        action=self.assess_building_form)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(assess_building_rheader = self.assess_building_rheader,
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def assess_building_onvalidation(form):
        """
            Update the overall status from the Gutting/Mold status
        """

        vars = form.vars
        status = vars.status and int(vars.status) or None
        if status < 3:
            status_gutting = vars.status_gutting and int(vars.status_gutting) or None
            status_mold = vars.status_mold and int(vars.status_mold) or None
            if status_gutting in (3, 4) or \
               status_mold in (3, 4):

                vars.status = 3

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def assess_building_rheader(r):
        """ Resource Header """

        if r.representation != "html" or r.method == "import" or not r.record:
            # RHeaders only used in interactive views
            return None

        rheader = TABLE(A(T("Print Work Order"),
                        _href = URL(args = [r.record.id, "form"]
                                    ),
                        _class = "action-btn"
                        ))
        return rheader
    # -------------------------------------------------------------------------
    @staticmethod
    def assess_building_form(r, **attr):
        """
            Generate a PDF of a Work Order

            @ToDo: Move this to Template?
        """

        db = current.db
        table = db.assess_building
        gtable = db.gis_location
        query = (table.id == r.id)
        left = gtable.on(gtable.id == table.location_id)
        record = db(query).select(left=left,
                                  limitby=(0, 1)).first()
        location = record.gis_location
        record = record.assess_building
        address = location.get("address", current.messages["NONE"])
        header = TABLE(
                    TR(TD(),
                       TD(),
                       TD(),
                       TD("Rockaways", _align="right"),
                       ),
                    TR(TD(),
                       TD(),
                       TD(),
                       TD("HOUSEHOLD ASSESSMENT"),
                       ),
                    TR(TD(),
                       TD(),
                       TD(),
                       TD("Database ID: %s" % record.database_id),
                       ),
                    TR(TD("Intake Date: %s" % table.date.represent(record.date)),
                       ),
                    TR(TD("Assessor 1: %s" % record.assessor1,
                          _colspan=2,
                          ),
                       TD("Assessor 2: %s" % record.assessor2,
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Name: %s" % record.name),
                       TD("Phone Number: %s" % table.phone.represent(record.phone)),
                       TD("Other Contact: %s" % table.contact_other.represent(record.contact_other),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Address: %s" % address,
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Homeowner Availability: %s" % record.homeowner_availability,
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Type of Property: %s" % table.type_of_property.represent(record.type_of_property),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("# of Inhabitants: %s" % table.inhabitants.represent(record.inhabitants)),
                       TD("Year Built: %s" % table.year_built.represent(record.year_built)),
                       TD("Ownership: %s" % table.ownership.represent(record.ownership)),
                       ),
                    TR(TD("Current Residence: %s" % table.current_residence.represent(record.current_residence),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Intention to Stay Home: %s" % table.intention.represent(record.intention),
                          _colspan=2,
                          ),
                       TD("Vulnerabilities: %s" % table.vulnerability.represent(record.vulnerability),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Based on the DOB/FEMA sticker, the property is: %s" % table.building_status.represent(record.building_status),
                          _colspan=2,
                          ),
                       TD("Type of Insurance: %s" % table.insurance.represent(record.insurance),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Work Requested: %s" % table.work_requested.represent(record.work_requested),
                          _colspan=2),
                       TD("Construction Type: %s" % table.construction_type.represent(record.construction_type),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Damages"),
                       TD("Electricity: %s" % table.electricity.represent(record.electricity)),
                       TD("Gas: %s" % table.gas.represent(record.gas)),
                       TD("Basement Flooding: %s Depth: %s feet" % (table.basement_flooding.represent(record.basement_flooding),
                                                                    table.basement_flooding_depth.represent(record.basement_flooding_depth))),
                       ),
                    TR(TD(),
                       TD("Drywall: %s" % table.drywall.represent(record.drywall)),
                       TD("Floor: %s" % table.floor.represent(record.floor)),
                       TD("First Floor Flooding: %s Depth: %s feet" % (table.first_flooding.represent(record.first_flooding),
                                                                       table.first_flooding_depth.represent(record.first_flooding_depth))),
                       ),
                    TR(TD("Remove Loose Debris: %s" % table.remove_loose_debris.represent(record.remove_loose_debris)),
                       TD("Remove Furniture: %s" % table.remove_furniture.represent(record.remove_furniture)),
                       TD("Remove Water Heater: %s" % table.remove_water_heater.represent(record.remove_water_heater)),
                       TD("Remove Major Appliances: %s" % table.remove_appliances.represent(record.remove_appliances)),
                       ),
                    TR(TD("Asbestos: %s" % table.asbestos.represent(record.asbestos)),
                       ),
                    TR(TD("Source of Damages: %s" % table.damage_source.represent(record.damage_source),
                          _colspan=2,
                          ),
                       TD("Other: %s" % table.damage_source_other.represent(record.damage_source_other),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Additional Description of Damage: %s" % table.damage_details.represent(record.damage_details),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Workplan: %s" % table.work_plan.represent(record.work_plan),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Special Skills: %s" % table.special_skills.represent(record.special_skills),
                          _colspan=4,
                          ),
                       ),
                     TR(TD("Estimated Volunteers: %s" % table.estimated_volunteers.represent(record.estimated_volunteers),
                          _colspan=2,
                          ),
                       TD("Estimated Days: %s" % table.estimated_days.represent(record.estimated_days),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Additional Needs: %s" % table.additional_needs.represent(record.additional_needs),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Approval: %s" % table.approval.represent(record.approval)),
                       TD("Details: %s" % table.approval_details.represent(record.approval_details),
                          _colspan=3,
                          ),
                       ),
                    TR(TD("Permission from Owner to Work: %s" % table.permission.represent(record.permission),
                          _colspan=2,
                          ),
                       TD("Date Ready: %s" % table.date_ready.represent(record.date_ready),
                          _colspan=2,
                          ),
                       ),
                    TR(TD("Comments: %s" % table.comments.represent(record.comments),
                          _colspan=4,
                          ),
                       ),
                    TR(TD("Progress and Notes: %s" % table.progress.represent(record.progress),
                          _colspan=4,
                          _rowspan=4,
                          ),
                       ),
                    )

        WORK_ORDER = current.T("Work Order")
        from s3.s3export import S3Exporter
        exporter = S3Exporter().pdf
        return exporter(r,
                        method = "read",
                        pdf_title = WORK_ORDER,
                        pdf_filename = "%s %s" % (WORK_ORDER,
                                                  record.database_id),
                        pdf_header = header,
                        pdf_header_padding = 12,
                        pdf_table_autogrow = "B",
                        **attr
                        )

# =============================================================================
class S3AssessCanvassModel(S3Model):
    """
        Building Canvassing form
    """

    names = ("assess_canvass",)

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
        self.define_table(tablename,
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
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Assessment"),
            title_display = T("Assessment Details"),
            title_list = T("Assessments"),
            title_update = T("Edit Assessment"),
            label_list_button = T("List Assessments"),
            label_delete_button = T("Delete Assessment"),
            msg_record_created = T("Assessment added"),
            msg_record_modified = T("Assessment updated"),
            msg_record_deleted = T("Assessment deleted"),
            msg_list_empty = T("No Assessments found")
        )

        filter_widgets = [
            S3TextFilter(["location_id$name",
                          "location_id$addr_street",
                         ],
                         label=T("Building Name or Address"),
                         comment=T("To search for a building canvass assessment, enter the Building Name or Addresss. You may use % as wildcard. Press 'Search' without input to list all assessments."),
                        ),
            S3OptionsFilter("status",
                            label=T("Status"),
                            options = status_opts,
                            cols = 3,
                           ),
        ]

        self.configure(tablename,
                       filter_widgets = filter_widgets,
                      )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

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
