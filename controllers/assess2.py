# -*- coding: utf-8 -*-

"""
    Assessments

    This module currently contains 2 types of Assessments
      * Flexible Impact Assessments (including Mobile access)

      * Rapid Assessment Tool (from ECB: http://www.ecbproject.org/page/48)
        @ToDo: Migrate this to a Template in the Survey module

        @ToDo Validation similar to sitrep_school_report_onvalidation()
        http://bazaar.launchpad.net/~flavour/sahana-eden/trunk/annotate/head:/models/sitrep.py#L99

    It also contains some Baseline Data:
      * Populations
    http://eden.sahanafoundation.org/wiki/BluePrintBaselineData
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
# Define the Model
# @ToDo: Move to modules/s3db/assess.py
# - here it isn't visible to s3db.load_all_models() or Sync
# -----------------------------------------------------------------------------
assess_severity_opts = {
    0: T("Low"),
    1: T("Medium"),
    2: T("High"),
    3: T("Very High"),
}

assess_colour_opts = {
    0:"green",
    1:"yellow",
    2:"orange",
    3:"red"
}

def s3_assess_severity_represent(value):
    if value:
        return IMG(_src="/%s/static/img/%s_circle_16px.png" %
                        (appname, assess_colour_opts[value]),
                   _alt= value,
                   _align="middle"
                   )
    else:
        return NONE

repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name
S3Represent = s3base.S3Represent

add_components = s3db.add_components
configure = s3db.configure
crud_strings = s3.crud_strings
define_table = db.define_table

location_id = s3db.gis_location_id
person_id = s3db.pr_person_id
organisation_id = s3db.org_organisation_id
organisation_represent = s3db.org_organisation_represent
sector_id = s3db.org_sector_id
human_resource_id = s3db.hrm_human_resource_id
ireport_id = s3db.irs_ireport_id

# Impact as component of assessments
add_components("assess_assess", impact_impact="assess_id")

def assess_tables():
    """ Load the Assess Tables when needed """

    module = "assess"

    # =========================================================================
    # Flexible Impact Assessments
    # =========================================================================
    # Assessment
    #
    resourcename = "assess"
    tablename = "assess_assess"
    define_table(tablename,
                 Field("datetime", "datetime",
                       label = T("Date & Time"),
                       default = request.utcnow),
                 location_id(widget = S3LocationAutocompleteWidget(),
                             requires = IS_LOCATION()),
                 organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile=True)),
                 person_id("assessor_person_id",
                           label = T("Assessor"),
                           default = auth.s3_logged_in_person()),
                 s3_comments(),
                 ireport_id(),      # Assessment can be linked to an Incident Report
                 *s3_meta_fields())

    assess_id = S3ReusableField("assess_id", "reference %s" % tablename,
                                requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "assess_assess.id", "%(id)s")
                                            ),
                                represent = lambda id: id,
                                label = T("Assessment"),
                                ondelete = "RESTRICT")

    # CRUD strings
    crud_strings[tablename] = Storage(
        label_create = T("Add Assessment"),
        title_display = T("Assessment Details"),
        title_list = T("Assessments"),
        title_update = T("Edit Assessment"),
        label_list_button = T("List Assessments"),
        label_delete_button = T("Delete Assessment"),
        msg_record_created = T("Assessment added"),
        msg_record_modified = T("Assessment updated"),
        msg_record_deleted = T("Assessment deleted"),
        msg_list_empty = T("No Assessments currently registered"),
        )

    # assess_assess as component of org_organisation
    add_components("org_organisation", assess_assess="organisation_id")

    # Hide Add Assessment functionality. Users should only add assessments
    # through the Basic Assessment.
    configure(tablename,
              insertable=False)

    # =========================================================================
    # Baseline Type
    #
    tablename = "assess_baseline_type"
    define_table(tablename,
                 Field("name", length=128, notnull=True, unique=True),
                 *s3_meta_fields())

    # CRUD strings
    ADD_BASELINE_TYPE = T("Add Baseline Type")
    crud_strings[tablename] = Storage(
        label_create = ADD_BASELINE_TYPE,
        title_display = T("Baseline Type Details"),
        title_list = T("Baseline Types"),
        title_update = T("Edit Baseline Type"),
        label_list_button = T("List Baseline Types"),
        label_delete_button = T("Delete Baseline Type"),
        msg_record_created = T("Baseline Type added"),
        msg_record_modified = T("Baseline Type updated"),
        msg_record_deleted = T("Baseline Type deleted"),
        msg_list_empty = T("No Baseline Types currently registered"),
        )

    def baseline_type_comment():
        # ToDo: Is this membership check required?
        if auth.has_membership(auth.id_group("'Administrator'")):
            return S3PopupLink(c="assess",
                               f="baseline_type",
                               label=ADD_BASELINE_TYPE)
        else:
            return None

    represent = S3Represent(tablename)
    baseline_type_id = S3ReusableField("baseline_type_id", "reference %s" % tablename,
                                       sortby="name",
                                       requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                        "assess_baseline_type.id",
                                                                        represent,
                                                                        sort=True)),
                                       represent = represent,
                                       label = T("Baseline Type"),
                                       comment = baseline_type_comment(),
                                       ondelete = "RESTRICT"
                                       )

    # =========================================================================
    # Baseline
    #
    tablename = "assess_baseline"
    define_table(tablename,
                 # Hide FK fields in forms
                 assess_id(readable = False, writable = False),
                 baseline_type_id(),
                 Field("value", "double"),
                 s3_comments(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = Storage(
        label_create = T("Add Baseline"),
        title_display = T("Baselines Details"),
        title_list = T("Baselines"),
        title_update = T("Edit Baseline"),
        label_list_button = T("List Baselines"),
        label_delete_button = T("Delete Baseline"),
        msg_record_created = T("Baseline added"),
        msg_record_modified = T("Baseline updated"),
        msg_record_deleted = T("Baseline deleted"),
        msg_list_empty = T("No Baselines currently registered"),
        )

    # Baseline as component of assessments
    add_components("assess_assess", assess_baseline="assess_id")

    # =========================================================================
    # Summary
    #
    tablename = "assess_summary"
    define_table(tablename,
                 assess_id(readable = False, writable = False),
                 sector_id(),
                 #Field("value", "double"),
                 Field("value", "integer",
                       default = 0,
                       label = T("Severity"),
                       represent = s3_assess_severity_represent,
                       requires = IS_EMPTY_OR(IS_IN_SET(assess_severity_opts)),
                       widget = SQLFORM.widgets.radio.widget,
                       ),
                 s3_comments(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = Storage(
        label_create = T("Add Assessment Summary"),
        title_display = T("Assessment Summary Details"),
        title_list = T("Assessment Summaries"),
        title_update = T("Edit Assessment Summary"),
        label_list_button = T("List Assessment Summaries"),
        label_delete_button = T("Delete Assessment Summary"),
        msg_record_created = T("Assessment Summary added"),
        msg_record_modified = T("Assessment Summary updated"),
        msg_record_deleted = T("Assessment Summary deleted"),
        msg_list_empty = T("No Assessment Summaries currently registered"),
        )

    # Summary as component of assessments
    add_components("assess_assess",
                   assess_summary="assess_id",
                   )

    # Pass variables back to global scope (response.s3.*)
    return dict(assess_id = assess_id,
                )

# =========================================================================
# Rapid Assessment Tool
# =========================================================================
def rat_tables():
    """ Load the RAT Tables when needed """

    module = "assess"

    # Load the models we depend on
    if settings.has_module("cr"):
        shelter_id = s3db.shelter_id
    if settings.has_module("hrm"):
        human_resource_id = s3db.hrm_human_resource_id
    else:
        human_resource_id = s3db.pr_person_id

    # Section CRUD strings
    rat_section_crud_strings = Storage(
        label_create = T("Add Section"),
        title_display = T("Section Details"),
        title_list = T("Sections"),
        title_update = "",
        label_list_button = T("List Sections"),
        label_delete_button = T("Delete Section"),
        msg_record_created = T("Section updated"),
        msg_record_modified = T("Section updated"),
        msg_record_deleted = T("Section deleted"),
        msg_list_empty = T("No Sections currently registered"),
        )

    # -------------------------------------------------------------------------
    # Common options
    rat_walking_time_opts = {
        1: T("0-15 minutes"),
        2: T("15-30 minutes"),
        3: T("30-60 minutes"),
        4: T("over one hour"),
        999: NOT_APPLICABLE
    }

    # -------------------------------------------------------------------------
    # Helper functions
    def rat_represent_multiple(set, opt):
        """
            Represent an IS_IN_SET with multiple=True as
            comma-separated list of options

            @param set: the options set as dict
            @param opt: the selected option(s)
        """

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(set.get(o, o)) for o in opts]
        #elif isinstance(opt, basestring):
        #    opts = opt.split("|")
        #    vals = [str(set.get(int(o), o)) for o in opts if o]
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(set.get(opt, opt))
        else:
            return T("None")
        if len(opts) > 1:
            vals = ", ".join(vals)
        else:
            vals = len(vals) and vals[0] or ""
        return vals

    def rat_tooltip(tooltip, multiple=False):
        """
            Prepare tooltip
        """

        if multiple:
            comment = DIV("(%s)" % T("Select all that apply"),
                          DIV(_class="tooltipbody",
                              _title="|%s" % T(tooltip)))
        else:
            comment = DIV(DIV(_class="tooltipbody",
                              _title="|%s" % T(tooltip)))
        return comment

    def rat_label_and_tooltip(label, tooltip, multiple=False):
        """
            Prepare tooltip that incorporates a field's label
        """

        label = T(label)
        if multiple:
            comment = DIV("(%s)" % T("Select all that apply"),
                          DIV(_class="tooltip",
                              _title="%s|%s" % (T(label), T(tooltip))))
        else:
            comment = DIV(DIV(_class="tooltip",
                              _title="%s|%s" % (T(label), T(tooltip))))
        return {"label": label, "comment": comment}

    rat_interview_location_opts = {
        1:T("Village"),
        2:T("Urban area"),
        3:T("Collective center"),
        4:T("Informal camp"),
        5:T("Formal camp"),
        6:T("School"),
        7:T("Mosque"),
        8:T("Church"),
        99:T("Other")
    }

    rat_interviewee_opts = {
        1:T("Male"),
        2:T("Female"),
        3:T("Village Leader"),
        4:T("Informal Leader"),
        5:T("Community Member"),
        6:T("Religious Leader"),
        7:T("Police"),
        8:T("Healthcare Worker"),
        9:T("School Teacher"),
        10:T("Womens Focus Groups"),
        11:T("Child (< 18 yrs)"),
        99:T("Other")
    }

    rat_accessibility_opts = {
        1:T("2x4 Car"),
        2:T("4x4 Car"),
        3:T("Truck"),
        4:T("Motorcycle"),
        5:T("Boat"),
        6:T("Walking Only"),
        7:T("No access at all"),
        99:T("Other")
    }

    # Main Resource -----------------------------------------------------------
    # contains Section 1: Identification Information
    #
    tablename = "assess_rat"
    define_table(tablename,
                 Field("date", "date",
                       default = datetime.datetime.today(),
                       requires = [IS_DATE(format = settings.get_L10n_date_format()),
                                   IS_NOT_EMPTY()],
                       ),
                 location_id(requires = IS_LOCATION(),
                             widget = S3LocationAutocompleteWidget(),
                             ),
                 human_resource_id("staff_id", label=T("Staff")),
                 human_resource_id("staff2_id", label=T("Staff2")),
                 Field("interview_location", "list:integer",
                       label = T("Interview taking place at"),
                       represent = lambda opt, set=rat_interview_location_opts: \
                                      rat_represent_multiple(set, opt),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_interview_location_opts,
                                                        multiple=True,
                                                        zero=None)),
                       #widget = SQLFORM.widgets.checkboxes.widget,
                       comment = "(%s)" % T("Select all that apply"),
                       ),
                 Field("interviewee", "list:integer",
                       label = T("Person interviewed"),
                       represent = lambda opt, set=rat_interviewee_opts: \
                                    rat_represent_multiple(set, opt),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_interviewee_opts,
                                                        multiple=True,
                                                        zero=None)),
                       #widget = SQLFORM.widgets.checkboxes.widget,
                       comment = "(%s)" % T("Select all that apply"),
                       ),
                 Field("accessibility", "integer",
                       label = T("Accessibility of Affected Location"),
                       represent = lambda opt: rat_accessibility_opts.get(opt, opt),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_accessibility_opts,
                                                        zero=None)),
                       ),
                 s3_comments(),
                 #document_id(),  # Better to have multiple Documents on a Tab
                 s3db.shelter_id(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = Storage(
        label_create = T("Add Rapid Assessment"),
        title_display = T("Rapid Assessment Details"),
        title_list = T("Rapid Assessments"),
        title_update = T("Edit Rapid Assessment"),
        label_list_button = T("List Rapid Assessments"),
        label_delete_button = T("Delete Rapid Assessment"),
        msg_record_created = T("Rapid Assessment added"),
        msg_record_modified = T("Rapid Assessment updated"),
        msg_record_deleted = T("Rapid Assessment deleted"),
        msg_list_empty = T("No Rapid Assessments currently registered"),
        )

    # -------------------------------------------------------------------------
    def rat_assessment_onaccept(form):

        id = form.vars.get("id", None)

        if id:
            for x in xrange(2, 10):
                section = "assess_section%s" % x
                set = db(db[section].assessment_id == id)
                record = set.select(db[section].id, limitby=(0, 1)).first()
                if not record:
                    db[section].insert(assessment_id=id)

    # -------------------------------------------------------------------------
    def rat_represent(id):
        """ Represent assessment as string """

        table = db.assess_rat
        row = db(table.id == id).select(table.date,
                                        table.staff_id,
                                        table.staff2_id,
                                        table.location_id,
                                        limitby = (0, 1)).first()

        if row:
            date = row.date and str(row.date) or ""
            location = row.location_id and s3db.gis_LocationRepresent()(row.location_id) or ""

            table = db.org_staff
            org = ["", ""]
            i = 0
            for staff_id in [row.staff_id, row.staff2_id]:
                if staff_id:
                    staff = db(table.id == staff_id).select(table.organisation_id,
                                                            limitby=(0, 1)).first()
                    if staff:
                        i += 1
                        org[i] = organisation_represent(staff.organisation_id)

            assessment_represent = XML("<div>%s %s, %s %s</div>" % (location, org[0], org[1], date))

        else:
            assessment_represent = NONE

        return assessment_represent


    # -------------------------------------------------------------------------
    # re-usable field
    assessment_id = S3ReusableField("assessment_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "assess_rat.id",
                                                          rat_represent,
                                                          orderby="assess_rat.id")
                                                          ),
                                    #represent = rat_represent,
                                    readable = False, writable = False,
                                    #label = T("Rapid Assessment"),
                                    #comment = A(ADD_ASSESSMENT,
                                    #            _class="s3_add_resource_link",
                                    #            _href=URL(c="assess", f="rat",
                                    #                      args="create",
                                    #                      vars=dict(format="popup")),
                                    #            _target="top",
                                    #            _title=ADD_ASSESSMENT),
                                    ondelete = "RESTRICT")

    # Assessment as component of cr_shelter.
    # RAT has components itself, so best not to constrain within the parent resource tabs
    # - therefore disable the listadd & jump out of the tabs for Create/Update
    add_components("cr_shelter", assess_rat="shelter_id")

    configure(tablename,
              listadd=False,    # We override this in the RAT controller for when not a component
              onaccept=rat_assessment_onaccept)

    # Section 2: Demographic --------------------------------------------------

    tablename = "assess_section2"
    define_table(tablename,
                 assessment_id(),
                 Field("population_total", "integer",
                       label = T("Total population of site visited"),
                       comment = T("people"),
                       ),
                Field("households_total", "integer",
                      label = T("Total # of households of site visited"),
                      comment = T("households"),
                      ),
                Field("population_affected", "integer",
                      label = T("Estimated # of people who are affected by the emergency"),
                      comment = T("people"),
                      ),
                Field("households_affected", "integer",
                      label = T("Estimated # of households who are affected by the emergency"),
                      comment = T("households"),
                      ),
                Field("male_05", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 0-5"),
                      ),
                Field("male_612", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 6-12"),
                      ),
                Field("male_1317", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 13-17"),
                      ),
                Field("male_1825", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 18-25"),
                      ),
                Field("male_2660", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 26-60"),
                      ),
                Field("male_61", "double",
                      label = T("Number/Percentage of affected population that is Male & Aged 61+"),
                      ),
                Field("female_05", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 0-5"),
                      ),
                Field("female_612", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 6-12")),
                Field("female_1317", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 13-17")),
                Field("female_1825", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 18-25")),
                Field("female_2660", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 26-60")),
                Field("female_61", "double",
                      label = T("Number/Percentage of affected population that is Female & Aged 61+")),
                Field("dead_women", "integer",
                      label = T("How many Women (18 yrs+) are Dead due to the crisis"),
                      comment = T("people")),  # @ToDo: Should this say "Number of people"?
                Field("dead_men", "integer",
                      label = T("How many Men (18 yrs+) are Dead due to the crisis"),
                      comment = T("people")),
                Field("dead_girl", "integer",
                      label = T("How many Girls (0-17 yrs) are Dead due to the crisis"),
                      comment = T("people")),
                Field("dead_boy", "integer",
                      label = T("How many Boys (0-17 yrs) are Dead due to the crisis"),
                      comment = T("people")),
                Field("injured_women", "integer",
                      label = T("How many Women (18 yrs+) are Injured due to the crisis"),
                      comment = T("people")),
                Field("injured_men", "integer",
                      label = T("How many Men (18 yrs+) are Injured due to the crisis"),
                      comment = T("people")),
                Field("injured_girl", "integer",
                      label = T("How many Girls (0-17 yrs) are Injured due to the crisis"),
                      comment = T("people")),
                Field("injured_boy", "integer",
                      label = T("How many Boys (0-17 yrs) are Injured due to the crisis"),
                      comment = T("people")),
                Field("missing_women", "integer",
                      label = T("How many Women (18 yrs+) are Missing due to the crisis"),
                      comment = T("people")),
                Field("missing_men", "integer",
                      label = T("How many Men (18 yrs+) are Missing due to the crisis"),
                      comment = T("people")),
                Field("missing_girl", "integer",
                      label = T("How many Girls (0-17 yrs) are Missing due to the crisis"),
                      comment = T("people")),
                Field("missing_boy", "integer",
                      label = T("How many Boys (0-17 yrs) are Missing due to the crisis"),
                      comment = T("people")),
                Field("household_head_elderly", "integer",
                      label = T("Elderly person headed households (>60 yrs)"),
                      comment = T("households")),
                Field("household_head_female", "integer",
                      label = T("Female headed households"),
                      comment = T("households")),
                Field("household_head_child", "integer",
                      label = T("Child headed households (<18 yrs)"),
                      comment = T("households")),
                Field("disabled_physical", "integer",
                      label = T("Persons with disability (physical)"),
                      comment = T("people")),
                Field("disabled_mental", "integer",
                      label = T("Persons with disability (mental)"),
                      comment = T("people")),
                Field("pregnant", "integer",
                      label = T("Pregnant women"),
                      comment = T("people")),
                Field("lactating", "integer",
                      label = T("Lactating women"),
                      comment = T("people")),
                Field("minorities", "integer",
                      label = T("Migrants or ethnic minorities"),
                      comment = T("people")),
                s3_comments(),
                *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 3: Shelter & Essential NFIs -------------------------------------

    rat_houses_salvmat_types = {
        1: T("Wooden plank"),
        2: T("Zinc roof"),
        3: T("Bricks"),
        4: T("Wooden poles"),
        5: T("Door frame"),
        6: T("Window frame"),
        7: T("Roof tile"),
        999: NOT_APPLICABLE
    }

    rat_water_container_types = {
        1: T("Jerry can"),
        2: T("Bucket"),
        3: T("Water gallon"),
        99: T("Other (specify)")
    }

    tablename = "assess_section3"
    define_table(tablename,
                 assessment_id(),
                 Field("houses_total", "integer",
                       label = T("Total number of houses in the area"),
                       requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                       ),
                 Field("houses_destroyed", "integer",
                       requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                       **rat_label_and_tooltip(
                           "Number of houses destroyed/uninhabitable",
                           "How many houses are uninhabitable (uninhabitable = foundation and structure destroyed)?")),
                 Field("houses_damaged", "integer",
                       requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                       **rat_label_and_tooltip(
                           "Number of houses damaged, but usable",
                           "How many houses suffered damage but remain usable (usable = windows broken, cracks in walls, roof slightly damaged)?")),
                 Field("houses_salvmat", "list:integer",
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_houses_salvmat_types,
                                                        multiple=True,
                                                        zero=None)),
                       represent = lambda opt, set=rat_houses_salvmat_types: \
                                       rat_represent_multiple(set, opt),
                       **rat_label_and_tooltip(
                           "Salvage material usable from destroyed houses",
                           "What type of salvage material can be used from destroyed houses?",
                           multiple=True)),
                 Field("water_containers_available", "boolean",
                       **rat_label_and_tooltip(
                           "Water storage containers available for HH",
                           "Do households have household water storage containers?")),
                 Field("water_containers_sufficient", "boolean",
                       **rat_label_and_tooltip(
                           "Water storage containers sufficient per HH",
                           "Do households each have at least 2 containers (10-20 litres each) to hold water?")),
                 Field("water_containers_types", "list:integer",
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_water_container_types,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_water_container_types: \
                                       rat_represent_multiple(set, opt),
                       **rat_label_and_tooltip(
                           "Types of water storage containers available",
                           "What types of household water storage containers are available?",
                           multiple=True)),
                 Field("water_containers_types_other",
                       label = T("Other types of water storage containers")),
                 Field("cooking_equipment_available", "boolean",
                       **rat_label_and_tooltip(
                           "Appropriate cooking equipment/materials in HH",
                           "Do households have appropriate equipment and materials to cook their food (stove, pots, dished plates, and a mug/drinking vessel, etc)?")),
                 Field("sanitation_items_available", "boolean",
                       **rat_label_and_tooltip(
                           "Reliable access to sanitation/hygiene items",
                           "Do people have reliable access to sufficient sanitation/hygiene items (bathing soap, laundry soap, shampoo, toothpaste and toothbrush)?")),
                 Field("sanitation_items_available_women", "boolean",
                       **rat_label_and_tooltip(
                           "Easy access to sanitation items for women/girls",
                           "Do women and girls have easy access to sanitary materials?")),
                 Field("bedding_materials_available", "boolean",
                       **rat_label_and_tooltip(
                           "Bedding materials available",
                           "Do households have bedding materials available (tarps, plastic mats, blankets)?")),
                 Field("clothing_sets_available", "boolean",
                       **rat_label_and_tooltip(
                           "Appropriate clothing available",
                           "Do people have at least 2 full sets of clothing (shirts, pants/sarong, underwear)?")),
                 Field("nfi_assistance_available", "boolean",
                       **rat_label_and_tooltip(
                           "Shelter/NFI assistance received/expected",
                           "Have households received any shelter/NFI assistance or is assistance expected in the coming days?")),
                 Field("kits_hygiene_received", "boolean",
                       label = T("Hygiene kits received")),
                 Field("kits_hygiene_source",
                       label = T("Hygiene kits, source")),
                 Field("kits_household_received", "boolean",
                       label = T("Household kits received")),
                 Field("kits_household_source",
                       label = T("Household kits, source")),
                 Field("kits_dwelling_received", "boolean",
                       label = T("Family tarpaulins received")),  # @ToDo: Better label, perhaps? A tarp isn't a dwelling.
                 Field("kits_dwelling_source",
                       label = T("Family tarpaulins, source")),
                 s3_comments(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 4 - Water and Sanitation ----------------------------------------

    rat_water_source_types = {
        1: T("PDAM"),
        2: T("Dug Well"),
        3: T("Spring"),
        4: T("River"),
        5: T("Other Faucet/Piped Water"),
        99: T("Other (describe)"),
        999: NOT_APPLICABLE
    }

    rat_water_coll_person_opts = {
        1: T("Child"),
        2: T("Adult male"),
        3: T("Adult female"),
        4: T("Older person (>60 yrs)"),
        999: NOT_APPLICABLE
    }

    rat_defec_place_types = {
        1: T("open defecation"),
        2: T("pit"),
        3: T("latrines"),
        4: T("river"),
        99: T("other")
    }

    rat_defec_place_animals_opts = {
        1: T("enclosed area"),
        2: T("within human habitat"),
        999: NOT_APPLICABLE
    }

    rat_latrine_types = {
        1: T("flush latrine with septic tank"),
        2: T("pit latrine"),
        999: NOT_APPLICABLE
    }

    tablename = "assess_section4"
    define_table(tablename,
                assessment_id(),
                Field("water_source_pre_disaster_type", "integer",
                      label = T("Type of water source before the disaster"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types,
                                                       zero=None)),
                      represent = lambda opt: rat_water_source_types.get(opt,
                                                                         UNKNOWN_OPT)),
                Field("water_source_pre_disaster_description",
                      label = T("Description of water source before the disaster")),
                Field("dwater_source_type", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types,
                                                       zero=None)),
                      represent = lambda opt: rat_water_source_types.get(opt,
                                                                         UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Current type of source for drinking water",
                          "What is your major source of drinking water?")),
                Field("dwater_source_description",
                      label = T("Description of drinking water source")),
                Field("dwater_reserve",
                      **rat_label_and_tooltip(
                          "How long will this water resource last?",
                          "Specify the minimum sustainability in weeks or days.")),
                Field("swater_source_type", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_water_source_types,
                                                       zero=None)),
                      represent = lambda opt: rat_water_source_types.get(opt,
                                                                         UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Current type of source for sanitary water",
                          "What is your major source of clean water for daily use (ex: washing, cooking, bathing)?")),
                Field("swater_source_description",
                      label = T("Description of sanitary water source")),
                Field("swater_reserve",
                      **rat_label_and_tooltip(
                          "How long will this water resource last?",
                          "Specify the minimum sustainability in weeks or days.")),
                Field("water_coll_time", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_walking_time_opts,
                                                       zero=None)),
                      represent = lambda opt: rat_walking_time_opts.get(opt,
                                                                        UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Time needed to collect water",
                          "How long does it take you to reach the available water resources? Specify the time required to go there and back, including queuing time, by foot.")),
                Field("water_coll_safe", "boolean",
                      label = T("Is it safe to collect water?"),
                      default = True),
                Field("water_coll_safety_problems",
                      label = T("If no, specify why")),
                Field("water_coll_person", "integer",
                      label = T("Who usually collects water for the family?"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_water_coll_person_opts,
                                                       zero=None)),
                      represent = lambda opt: rat_water_coll_person_opts.get(opt,
                                                                             UNKNOWN_OPT)),
                Field("defec_place_type",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_defec_place_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt: rat_defec_place_types.get(opt,
                                                                        UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Type of place for defecation",
                          "Where do the majority of people defecate?",
                          multiple=True)),
                Field("defec_place_description",
                      label = T("Description of defecation area")),
                Field("defec_place_distance", "integer",
                      label = T("Distance between defecation area and water source"),
                      comment = T("meters")),
                Field("defec_place_animals", "integer",
                      label = T("Defecation area for animals"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_defec_place_animals_opts,
                                                       zero = None)),
                      represent = lambda opt: rat_defec_place_animals_opts.get(opt,
                                                                               UNKNOWN_OPT)),
                Field("close_industry", "boolean",
                      **rat_label_and_tooltip(
                          "Industry close to village/camp",
                          "Is there any industrial or agro-chemical production close to the affected area/village?")),
                Field("waste_disposal",
                      **rat_label_and_tooltip(
                          "Place for solid waste disposal",
                          "Where is solid waste disposed in the village/camp?")),
                Field("latrines_number", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of latrines",
                          "How many latrines are available in the village/IDP centre/Camp?")),
                Field("latrines_type", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_latrine_types,
                                                       zero=None)),
                      represent = lambda opt: rat_latrine_types.get(opt,
                                                                    UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Type of latrines",
                          "What type of latrines are available in the village/IDP centre/Camp?")),
                Field("latrines_separation", "boolean",
                      **rat_label_and_tooltip(
                          "Separate latrines for women and men",
                          "Are there separate latrines for women and men available?")),
                Field("latrines_distance", "integer",
                      **rat_label_and_tooltip(
                          "Distance between shelter and latrines",
                          "Distance between latrines and temporary shelter in meters")),
                s3_comments(),
                *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 5 - Health ------------------------------------------------------

    rat_health_services_types = {
        1: T("Community Health Center"),
        2: T("Hospital")
    }

    rat_health_problems_opts = {
        1: T("Respiratory Infections"),
        2: T("Diarrhea"),
        3: T("Dehydration"),
        99: T("Other (specify)")
    }

    rat_infant_nutrition_alternative_opts = {
        1: T("Porridge"),
        2: T("Banana"),
        3: T("Instant Porridge"),
        4: T("Air tajin"),
        99: T("Other (specify)")
    }

    tablename = "assess_section5"
    define_table(tablename,
                assessment_id(),
                Field("health_services_pre_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Health services functioning prior to disaster",
                          "Were there health services functioning for the community prior to the disaster?")),
                Field("medical_supplies_pre_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Basic medical supplies available prior to disaster",
                          "Were basic medical supplies available for health services prior to the disaster?")),
                Field("health_services_post_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Health services functioning since disaster",
                          "Are there health services functioning for the community since the disaster?")),
                Field("medical_supplies_post_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Basic medical supplies available since disaster",
                          "Are basic medical supplies available for health services since the disaster?")),
                Field("medical_supplies_reserve", "integer",
                      label = T("How many days will the supplies last?")),
                Field("health_services_available_types", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_health_services_types,
                                                       zero=None, multiple=True)),
                      represent = lambda opt: \
                                      rat_represent_multiple(rat_health_services_types, opt),
                      **rat_label_and_tooltip(
                          "Types of health services available",
                          "What types of health services are still functioning in the affected area?",
                          multiple=True)),
                Field("staff_number_doctors", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of doctors actively working",
                          "How many doctors in the health centers are still actively working?")),
                Field("staff_number_nurses", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of nurses actively working",
                          "How many nurses in the health centers are still actively working?")),
                Field("staff_number_midwives", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of midwives actively working",
                          "How many midwives in the health centers are still actively working?")),
                Field("health_service_walking_time", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_walking_time_opts,
                                                       zero=None)),
                      represent = lambda opt: rat_walking_time_opts.get(opt,
                                                                        UNKNOWN_OPT),
                      **rat_label_and_tooltip(
                          "Walking time to the health service",
                          "How long does it take you to walk to the health service?")),
                Field("health_problems_adults", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_health_problems_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_health_problems_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Current type of health problems, adults",
                          "What types of health problems do people currently have?",
                          multiple=True)),
                Field("health_problems_adults_other",
                      label = T("Other current health problems, adults")),
                Field("health_problems_children", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_health_problems_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_health_problems_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Current type of health problems, children",
                          "What types of health problems do children currently have?",
                          multiple=True)),
                Field("health_problems_children_other",
                      label = T("Other current health problems, children")),
                Field("chronical_illness_cases", "boolean",  # @ToDo: "chronic illness"?
                      **rat_label_and_tooltip(
                          "People with chronical illnesses",
                          "Are there people with chronical illnesses in your community?")),
                Field("chronical_illness_children", "boolean",
                      **rat_label_and_tooltip(
                          "Children with chronical illnesses",
                          "Are there children with chronical illnesses in your community?")),
                Field("chronical_illness_elderly", "boolean",
                      **rat_label_and_tooltip(
                          "Older people with chronical illnesses",
                          "Are there older people with chronical illnesses in your community?")),
                Field("chronical_care_sufficient", "boolean",
                      **rat_label_and_tooltip(
                          "Sufficient care/assistance for chronically ill",
                          "Are the chronically ill receiving sufficient care and assistance?")),
                Field("malnutrition_present_pre_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Malnutrition present prior to disaster",
                          "Were there cases of malnutrition in this area prior to the disaster?")),
                Field("mmd_present_pre_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Micronutrient malnutrition prior to disaster",
                          "Were there reports or evidence of outbreaks of any micronutrient malnutrition disorders before the emergency?")),
                Field("breast_milk_substitutes_pre_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Breast milk substitutes used prior to disaster",
                          "Were breast milk substitutes used prior to the disaster?")),
                Field("breast_milk_substitutes_post_disaster", "boolean",
                      **rat_label_and_tooltip(
                          "Breast milk substitutes in use since disaster",
                          "Are breast milk substitutes being used here since the disaster?")),
                Field("infant_nutrition_alternative", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_infant_nutrition_alternative_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_infant_nutrition_alternative_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Alternative infant nutrition in use",
                          "Babies who are not being breastfed, what are they being fed on?",
                          multiple=True)),
                Field("infant_nutrition_alternative_other",
                      label = T("Other alternative infant nutrition in use")),
                Field("u5_diarrhea", "boolean",
                      **rat_label_and_tooltip(
                          "Diarrhea among children under 5",
                          "Are there cases of diarrhea among children under the age of 5?")),
                Field("u5_diarrhea_rate_48h", "integer",
                      **rat_label_and_tooltip(
                          "Approx. number of cases/48h",
                          "Approximately how many children under 5 with diarrhea in the past 48 hours?")),
                s3_comments(),
                *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 6 - Nutrition/Food Security -------------------------------------

    rat_main_dish_types = {
        1: T("Rice"),
        2: T("Noodles"),
        3: T("Biscuits"),
        4: T("Corn"),
        5: T("Wheat"),
        6: T("Cassava"),
        7: T("Cooking Oil")
    }

    rat_side_dish_types = {
        1: T("Salted Fish"),
        2: T("Canned Fish"),
        3: T("Chicken"),
        4: T("Eggs"),
        99: T("Other (specify)")
    }

    rat_food_stock_reserve_opts = {
        1: T("1-3 days"),
        2: T("4-7 days"),
        3: T("8-14 days")
    }

    rat_food_source_types = {
        1: "Local market",
        2: "Field cultivation",
        3: "Food stall",
        4: "Animal husbandry",
        5: "Raising poultry",
        99: "Other (specify)"
    }

    tablename = "assess_section6"
    define_table(tablename,
                assessment_id(),
                Field("food_stocks_main_dishes", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_main_dish_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_main_dish_types: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Existing food stocks, main dishes",
                          "What food stocks exist? (main dishes)",
                          multiple=True)),
                # @ToDo: Should there be a field "food_stocks_other_main_dishes"?
                Field("food_stocks_side_dishes", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_side_dish_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_side_dish_types: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Existing food stocks, side dishes",
                          "What food stocks exist? (side dishes)",
                          multiple=True)),
                Field("food_stocks_other_side_dishes",
                      label = T("Other side dishes in stock")),
                Field("food_stocks_reserve", "integer",
                      label = T("How long will the food last?"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_food_stock_reserve_opts,
                                                       zero=None)),
                      represent = lambda opt: rat_food_stock_reserve_opts.get(opt,
                                                                              UNKNOWN_OPT)),
                Field("food_sources", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_food_source_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_food_source_types: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Usual food sources in the area",
                          "What are the people's normal ways to obtain food in this area?",
                          multiple=True)),
                Field("food_sources_other",
                      label = T("Other ways to obtain food")),
                Field("food_sources_disruption", "boolean",
                      **rat_label_and_tooltip(
                          "Normal food sources disrupted",
                          "Have normal food sources been disrupted?")),
                Field("food_sources_disruption_details",
                      label = T("If yes, which and how")),
                Field("food_assistance_available", "boolean",
                      **rat_label_and_tooltip(
                          "Food assistance available/expected",
                          "Have the people received or are you expecting any medical or food assistance in the coming days?")),
                Field("food_assistance_details", "text",
                      label = T("If yes, specify what and by whom")),
                s3_comments(),
                *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 7 - Livelihood --------------------------------------------------

    rat_income_source_opts = {
        1: T("Agriculture"),
        2: T("Fishing"),
        3: T("Poultry"),
        4: T("Casual Labor"),
        5: T("Small Trade"),
        6: T("Other")
    }

    rat_expense_types = {
        1: T("Education"),
        2: T("Health"),
        3: T("Food"),
        4: T("Hygiene"),
        5: T("Shelter"),
        6: T("Clothing"),
        7: T("Funeral"),
        8: T("Alcohol"),
        99: T("Other (specify)")
    }

    rat_cash_source_opts = {
        1: T("Family/friends"),
        2: T("Government"),
        3: T("Bank/micro finance"),
        4: T("Humanitarian NGO"),
        99: T("Other (specify)")
    }

    rat_ranking_opts = xrange(1, 7)

    tablename = "assess_section7"
    define_table(tablename,
                assessment_id(),
                Field("income_sources_pre_disaster", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_income_source_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_income_source_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Main income sources before disaster",
                          "What were your main sources of income before the disaster?",
                          multiple=True)),
                Field("income_sources_post_disaster", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_income_source_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_income_source_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Current main income sources",
                          "What are your main sources of income now?",
                          multiple=True)),
                Field("main_expenses", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_expense_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_expense_types: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Current major expenses",
                          "What do you spend most of your income on now?",
                          multiple=True)),
                Field("main_expenses_other",
                      label = T("Other major expenses")),

                Field("business_damaged", "boolean",
                      **rat_label_and_tooltip(
                          "Business damaged",
                          "Has your business been damaged in the course of the disaster?")),
                Field("business_cash_available", "boolean",
                      **rat_label_and_tooltip(
                          "Cash available to restart business",
                          "Do you have access to cash to restart your business?")),
                Field("business_cash_source", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_cash_source_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_cash_source_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Main cash source",
                          "What are your main sources of cash to restart your business?")),
                Field("rank_reconstruction_assistance", "integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None)),
                      **rat_label_and_tooltip(
                          "Immediate reconstruction assistance, Rank",
                          "Assistance for immediate repair/reconstruction of houses")),
                Field("rank_farmland_fishing_assistance", "integer",
                      label = T("Farmland/fishing material assistance, Rank"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))),
                Field("rank_poultry_restocking", "integer",
                      label = T("Poultry restocking, Rank"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))),
                Field("rank_health_care_assistance", "integer",
                      label = T("Health care assistance, Rank"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))),
                Field("rank_transportation_assistance", "integer",
                      label = T("Transportation assistance, Rank"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))),
                Field("other_assistance_needed",
                      label = T("Other assistance needed")),
                Field("rank_other_assistance", "integer",
                      label = T("Other assistance, Rank"),
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_ranking_opts, zero=None))),

                s3_comments(),
                *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Section 8 - Education ---------------------------------------------------

    rat_schools_salvmat_types = {
        1: T("Wooden plank"),
        2: T("Zinc roof"),
        3: T("Bricks"),
        4: T("Wooden poles"),
        5: T("Door frame"),
        6: T("Window frame"),
        7: T("Roof tile"),
        999: NOT_APPLICABLE
    }

    rat_alternative_study_places = {
        1: T("Community Centre"),
        2: T("Church"),
        3: T("Mosque"),
        4: T("Open area"),
        5: T("Government building"),
        6: T("Other (specify)"),
        999: NOT_APPLICABLE
    }

    rat_school_attendance_barriers_opts = {
        1: T("School used for other purpose"),
        2: T("School destroyed"),
        3: T("Lack of school uniform"),
        4: T("Lack of transport to school"),
        5: T("Children not enrolled in new school"),
        6: T("School heavily damaged"),
        7: T("Desire to remain with family"),
        8: T("Lack of supplies at school"),
        9: T("Displaced"),
        10: T("Other (specify)"),
        999: NOT_APPLICABLE
    }

    tablename = "assess_section8"
    define_table(tablename,
                assessment_id(),
                Field("schools_total", "integer",
                      label = T("Total number of schools in affected area"),
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))),
                Field("schools_public", "integer",
                      label = T("Number of public schools"),
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))),
                Field("schools_private", "integer",
                      label = T("Number of private schools"),
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))),
                Field("schools_religious", "integer",
                      label = T("Number of religious schools"),
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))),

                Field("schools_destroyed", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of schools destroyed/uninhabitable",
                          "uninhabitable = foundation and structure destroyed")),
                Field("schools_damaged", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of schools damaged but usable",
                          "windows broken, cracks in walls, roof slightly damaged")),
                Field("schools_salvmat", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_schools_salvmat_types,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_schools_salvmat_types: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Salvage material usable from destroyed schools",
                          "What type of salvage material can be used from destroyed schools?",
                          multiple=True)),

                Field("alternative_study_places_available", "boolean",
                      **rat_label_and_tooltip(
                          "Alternative places for studying available",
                          "Are there alternative places for studying?")),
                Field("alternative_study_places_number", "integer",
                      label = T("Number of alternative places for studying"),
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))),
                Field("alternative_study_places", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_alternative_study_places,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_alternative_study_places: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Alternative places for studying",
                          "Where are the alternative places for studying?",
                          multiple=True)),
                Field("alternative_study_places_other",
                      label = T("Other alternative places for study")),

                Field("schools_open_pre_disaster", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of schools open before disaster",
                          "How many primary/secondary schools were opening prior to the disaster?")),
                Field("schools_open_post_disaster", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of schools open now",
                          "How many of the primary/secondary schools are now open and running a regular schedule of class?")),

                Field("teachers_active_pre_disaster", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of teachers before disaster",
                          "How many teachers worked in the schools prior to the disaster?")),
                Field("teachers_affected_by_disaster", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Number of teachers affected by disaster",
                          "How many teachers have been affected by the disaster (affected = unable to work)?")),

                Field("children_0612_female", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Girls 6-12 yrs in affected area",
                          "How many primary school age girls (6-12) are in the affected area?")),
                Field("children_0612_male", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Boys 6-12 yrs in affected area",
                          "How many primary school age boys (6-12) are in the affected area?")),
                Field("children_0612_not_in_school_female", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Girls 6-12 yrs not attending school",
                          "How many of the primary school age girls (6-12) in the area are not attending school?")),
                Field("children_0612_not_in_school_male", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Boys 6-12 yrs not attending school",
                          "How many of the primary school age boys (6-12) in the area are not attending school?")),

                Field("children_1318_female", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Girls 13-18 yrs in affected area",
                          "How many secondary school age girls (13-18) are in the affected area?")),
                Field("children_1318_male", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Boys 13-18 yrs in affected area",
                          "How many secondary school age boys (13-18) are in the affected area?")),
                Field("children_1318_not_in_school_female", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Girls 13-18 yrs not attending school",
                          "How many of the secondary school age girls (13-18) in the area are not attending school?")),
                Field("children_1318_not_in_school_male", "integer",
                      requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                      **rat_label_and_tooltip(
                          "Boys 13-18 yrs not attending school",
                          "How many of the secondary school age boys (13-18) in the area are not attending school?")),

                Field("school_attendance_barriers", "list:integer",
                      requires = IS_EMPTY_OR(IS_IN_SET(rat_school_attendance_barriers_opts,
                                                       zero=None,
                                                       multiple=True)),
                      represent = lambda opt, set=rat_school_attendance_barriers_opts: \
                                      rat_represent_multiple(set, opt),
                      **rat_label_and_tooltip(
                          "Factors affecting school attendance",
                          "What are the factors affecting school attendance?",
                          multiple=True)),
                Field("school_attendance_barriers_other",
                      label = T("Other factors affecting school attendance")),

                Field("school_assistance_available", "boolean",
                      **rat_label_and_tooltip(
                          "School assistance received/expected",
                          "Have schools received or are expecting to receive any assistance?")),
                Field("school_assistance_tents_available", "boolean",
                      label = T("School tents received")),
                Field("school_assistence_tents_source",
                      label = T("School tents, source")),
                Field("school_assistance_materials_available", "boolean",
                      label = T("Education materials received")),
                Field("school_assistance_materials_source",
                      label = T("Education materials, source")),
                Field("school_assistance_other_available", "boolean",
                      label = T("Other school assistance received")),
                Field("school_assistance_other",
                      label = T("Other school assistance, details")),
                Field("school_assistance_other_source",
                      label = T("Other school assistance, source")),
                s3_comments(),
                *s3_meta_fields())

    # @ToDo: onvalidation!

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )


    # Section 9 - Protection --------------------------------------------------

    rat_fuzzy_quantity_opts = {
        1: T("None"),
        2: T("Few"),
        3: T("Some"),
        4: T("Many")
    }

    rat_quantity_opts = {
        1: "1-10",
        2: "11-50",
        3: "51-100",
        4: "100+"
    }

    rat_child_activity_opts = {
        1: T("Playing"),
        2: T("Domestic chores"),
        3: T("School/studying"),
        4: T("Doing nothing (no structured activity)"),
        5: T("Working or other to provide money/food"),
        99: T("Other (specify)")
    }

    rat_child_activity_post_disaster_opts = rat_child_activity_opts.copy()
    rat_child_activity_post_disaster_opts.update({
        6: T("Disaster clean-up/repairs")
    })

    tablename = "assess_section9"
    define_table(tablename,
                 assessment_id(),
                 Field("vulnerable_groups_safe_env", "boolean",
                       label = T("Safe environment for vulnerable groups"),
                       comment = rat_tooltip("Are the areas that children, older people, and people with disabilities live in, play in and walk through on a daily basis physically safe?")),
                 Field("safety_children_women_affected", "boolean",
                       label = T("Safety of children and women affected by disaster?"),
                       comment = rat_tooltip("Has the safety and security of women and children in your community changed since the emergency?")),
                 Field("sec_incidents", "boolean",
                       label = T("Known incidents of violence since disaster"),
                       comment = rat_tooltip("Do you know of any incidents of violence?")),
                 Field("sec_incidents_gbv", "boolean",
                       label = T("Known incidents of violence against women/girls"),
                       comment = rat_tooltip("Without mentioning any names or indicating anyone, do you know of any incidents of violence against women or girls occuring since the disaster?")),
                 Field("sec_current_needs",
                       label = T("Needs to reduce vulnerability to violence"),
                       comment = rat_tooltip("What should be done to reduce women and children's vulnerability to violence?")),
                 Field("children_separated", "integer",
                       label = T("Children separated from their parents/caregivers"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of children separated from their parents or caregivers?")),
                 Field("children_separated_origin",
                       label = T("Origin of the separated children"),
                       comment = rat_tooltip("Where are the separated children originally from?")),
                 Field("children_missing", "integer",
                       label = T("Parents/Caregivers missing children"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of parents/caregivers missing children?")),
                 Field("children_orphaned", "integer",
                       label = T("Children orphaned by the disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of children that have been orphaned by the disaster?")),
                 Field("children_unattended", "integer",
                       label = T("Children living on their own (without adults)"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of children living on their own (without adults)?")),
                 Field("children_disappeared", "integer",
                       label = T("Children who have disappeared since the disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of children that have disappeared without explanation in the period since the disaster?")),
                 Field("children_evacuated", "integer",
                       label = T("Children that have been sent to safe places"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of children that have been sent to safe places?")),
                 Field("children_evacuated_to",
                       label = T("Places the children have been sent to"),
                       comment = rat_tooltip("Where have the children been sent?")),
                 Field("children_with_older_caregivers", "integer",
                       label = T("Older people as primary caregivers of children"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_fuzzy_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_fuzzy_quantity_opts.get(opt,
                                                                           UNKNOWN_OPT),
                       comment = rat_tooltip("Do you know of older people who are primary caregivers of children?")),
                 Field("children_in_disabled_homes", "boolean",
                       label = T("Children in homes for disabled children"),
                       comment = rat_tooltip("Are there children living in homes for disabled children in this area?")),
                 Field("children_in_orphanages", "boolean",
                       label = T("Children in orphanages"),
                       comment = rat_tooltip("Are there children living in orphanages in this area?")),
                 Field("children_in_boarding_schools", "boolean",
                       label = T("Children in boarding schools"),
                       comment = rat_tooltip("Are there children living in boarding schools in this area?")),
                 Field("children_in_juvenile_detention", "boolean",
                       label = T("Children in juvenile detention"),
                       comment = rat_tooltip("Are there children living in juvenile detention in this area?")),
                 Field("children_in_adult_prisons", "boolean",
                       label = T("Children in adult prisons"),
                       comment = rat_tooltip("Are there children living in adult prisons in this area?")),
                 Field("people_in_adult_prisons", "boolean",
                       label = T("Adults in prisons"),
                       comment = rat_tooltip("Are there adults living in prisons in this area?")),
                 Field("people_in_care_homes", "boolean",
                       label = T("Older people in care homes"),
                       comment = rat_tooltip("Are there older people living in care homes in this area?")),
                 Field("people_in_institutions_est_total", "integer",
                       label = T("Estimated total number of people in institutions"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_quantity_opts,
                                                        zero=None)),
                       represent = lambda opt: rat_quantity_opts.get(opt,
                                                                     UNKNOWN_OPT),
                       comment = rat_tooltip("What is the estimated total number of people in all of these institutions?")),
                 Field("staff_in_institutions_present", "boolean",
                       label = T("Staff present and caring for residents"),
                       comment = rat_tooltip("Are there staff present and caring for the residents in these institutions?")),
                 Field("adequate_food_water_in_institutions", "boolean",
                       label = T("Adequate food and water available"),
                       comment = rat_tooltip("Is adequate food and water available for these institutions?")),
                 Field("child_activities_u12f_pre_disaster", "list:integer",
                       label = T("Activities of girls <12yrs before disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                       rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How did girls <12yrs spend most of their time prior to the disaster?",
                                             multiple=True)),
                 Field("child_activities_u12f_pre_disaster_other",
                       label = T("Other activities of girls<12yrs before disaster")),
                 Field("child_activities_u12m_pre_disaster", "list:integer",
                       label = T("Activities of boys <12yrs before disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How did boys <12yrs spend most of their time prior to the disaster?",
                                             multiple=True)),
                 Field("child_activities_u12m_pre_disaster_other",
                       label = T("Other activities of boys <12yrs before disaster")),
                 Field("child_activities_o12f_pre_disaster", "list:integer",
                       label = T("Activities of girls 13-17yrs before disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How did boys girls 13-17yrs spend most of their time prior to the disaster?",
                                             multiple=True)),
                 Field("child_activities_o12f_pre_disaster_other",
                       label = T("Other activities of girls 13-17yrs before disaster")),
                 Field("child_activities_o12m_pre_disaster", "list:integer",
                       label = T("Activities of boys 13-17yrs before disaster"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How did boys 13-17yrs spend most of their time prior to the disaster?",
                                             multiple=True)),
                 Field("child_activities_o12m_pre_disaster_other",
                       label = T("Other activities of boys 13-17yrs before disaster")),

                 Field("child_activities_u12f_post_disaster", "list:integer",
                       label = T("Activities of girls <12yrs now"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How do girls <12yrs spend most of their time now?",
                                             multiple=True)),
                 Field("child_activities_u12f_post_disaster_other",
                       label = T("Other activities of girls<12yrs")),
                 Field("child_activities_u12m_post_disaster", "list:integer",
                       label = T("Activities of boys <12yrs now"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How do boys <12yrs spend most of their time now?",
                                              multiple=True)),
                 Field("child_activities_u12m_post_disaster_other",
                       label = T("Other activities of boys <12yrs")),
                 Field("child_activities_o12f_post_disaster", "list:integer",
                       label = T("Activities of girls 13-17yrs now"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How do girls 13-17yrs spend most of their time now?",
                                             multiple=True)),
                 Field("child_activities_o12f_post_disaster_other",
                       label = T("Other activities of girls 13-17yrs")),
                 Field("child_activities_o12m_post_disaster", "list:integer",
                       label = T("Activities of boys 13-17yrs now"),
                       requires = IS_EMPTY_OR(IS_IN_SET(rat_child_activity_opts,
                                                        zero=None,
                                                        multiple=True)),
                       represent = lambda opt, set=rat_child_activity_opts: \
                                        rat_represent_multiple(set, opt),
                       comment = rat_tooltip("How do boys 13-17yrs spend most of their time now?",
                                             multiple=True)),
                 Field("child_activities_o12m_post_disaster_other",
                       label = T("Other activities of boys 13-17yrs")),

                 Field("coping_activities_elderly", "boolean",
                       label = T("Older people participating in coping activities"),
                       comment = rat_tooltip("Do older people in your community participate in activities that help them cope with the disaster? (ex. meetings, religious activities, volunteer in the community clean-up, etc)")),
                 Field("coping_activities_women", "boolean",
                       label = T("Women participating in coping activities"),
                       comment = rat_tooltip("Do women in your community participate in activities that help them cope with the disaster? (ex. meetings, religious activities, volunteer in the community clean-up, etc)")),
                 Field("coping_activities_disabled", "boolean",
                       label = T("Disabled participating in coping activities"),
                       comment = rat_tooltip("Do people with disabilities in your community participate in activities that help them cope with the disaster? (ex. meetings, religious activities, volunteer in the community clean-up, etc)")),
                 Field("coping_activities_minorities", "boolean",
                       label = T("Minorities participating in coping activities"),
                       comment = rat_tooltip("Do minority members in your community participate in activities that help them cope with the disaster? (ex. meetings, religious activities, volunteer in the community clean-up, etc)")),
                 Field("coping_activities_adolescent", "boolean",
                       label = T("Adolescent participating in coping activities"),
                       comment = rat_tooltip("Do adolescent and youth in your community participate in activities that help them cope with the disaster? (ex. meetings, religious activities, volunteer in the community clean-up, etc)")),

                 Field("current_general_needs", "text",
                       label = T("Current greatest needs of vulnerable groups"),
                       comment = rat_tooltip("In general, what are the greatest needs of older people, people with disabilities, children, youth and women in your community?")),

                 s3_comments(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = rat_section_crud_strings

    configure(tablename,
              deletable = False,
              )

    # Sections as components of RAT
    add_components("assess_rat",
                   assess_section2 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section3 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section4 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section5 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section6 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section7 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section8 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   assess_section9 = {"joinby": "assessment_id",
                                      "multiple": False,
                                      },
                   )

    # -----------------------------------------------------------------------------
    def assess_rat_summary(r, **attr):

        """ Aggregate reports """

        if r.name == "rat":
            if r.representation == "html":
                return dict()
            elif r.representation == "xls":
                return None
            else:
                # Other formats?
                raise HTTP(501, ERROR.BAD_FORMAT)
        else:
            raise HTTP(405, ERROR.BAD_METHOD)


    s3db.set_method("assess", "rat",
                     method="summary",
                     action=assess_rat_summary)

    # Pass variables back to global scope (response.s3.*)

# =========================================================================
# UN Common Operational Datasets
# =========================================================================

# Population Statistics
tablename = "assess_population"
define_table(tablename,
             location_id(widget = S3LocationAutocompleteWidget(),
                         requires = IS_LOCATION()),
             Field("population", "integer"),
             Field("households", "integer"),
             Field("median_age", "double"),
             Field("average_family_size", "double"),
             Field("effective_date", "datetime"),
             s3_comments(),
             *S3MetaFields.sync_meta_fields())

# CRUD strings
crud_strings[tablename] = Storage(
    label_create = T("Add Population Statistic"),
    title_display = T("Population Statistic Details"),
    title_list = T("Population Statistics"),
    title_update = T("Edit Population Statistic"),
    label_list_button = T("List Population Statistics"),
    label_delete_button = T("Delete Population Statistic"),
    msg_record_created = T("Population Statistic added"),
    msg_record_modified = T("Population Statistic updated"),
    msg_record_deleted = T("Population Statistic deleted"),
    msg_list_empty = T("No Population Statistics currently registered"),
    )

# Impact as component of incident reports
#add_components("irs_ireport", impact_impact="ireport_id")

# =========================================================================
def impact_tables():
    """ Load the Impact tables as-needed """

    sector_id = s3db.org_sector_id
    ireport_id = s3db.irs_ireport_id

    # Load the models we depend on
    if settings.has_module("assess"):
        assess_tables()
    assess_id = s3.assess_id

    module = "impact"

    # -------------------------------------------------------------------------
    # Impact Type
    resourcename = "type"
    tablename = "%s_%s" % (module, resourcename)
    db.define_table(tablename,
                    Field("name", length=128, notnull=True, unique=True),
                    sector_id(),
                    *s3_meta_fields())

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        label_create = T("Add Impact Type"),
        title_display = T("Impact Type Details"),
        title_list = T("Impact Types"),
        title_update = T("Edit Impact Type"),
        label_list_button = T("List Impact Types"),
        label_delete_button = T("Delete Impact Type"),
        msg_record_created = T("Impact Type added"),
        msg_record_modified = T("Impact Type updated"),
        msg_record_deleted = T("Impact Type deleted"),
        msg_list_empty = T("No Impact Types currently registered"),
        )

    def impact_type_comment():
        if auth.has_membership(auth.id_group("'Administrator'")):
            return S3PopupLink(c="assess",
                               f="type",
                               vars=dict(child="impact_type_id"))
        else:
            return None

    represent = S3Represent(tablename)
    impact_type_id = S3ReusableField("impact_type_id", "reference %s" % tablename,
                                     sortby="name",
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db,
                                                              "impact_type.id",
                                                              represent,
                                                              sort=True)),
                                     represent = represent,
                                     label = T("Impact Type"),
                                     comment = impact_type_comment(),
                                     ondelete = "RESTRICT")

    # =====================================================================
    # Impact
    # Load model
    ireport_id = s3db.irs_ireport_id

    tablename = "assess_impact"
    define_table(tablename,
                 ireport_id(readable=False, writable=False),
                 assess_id(readable=False, writable=False),
                 impact_type_id(),
                 Field("value", "double"),
                 Field("severity", "integer",
                       requires = IS_EMPTY_OR(IS_IN_SET(assess_severity_opts)),
                       widget=SQLFORM.widgets.radio.widget,
                       represent = s3_assess_severity_represent,
                       default = 0),
                 s3_comments(),
                 *s3_meta_fields())

    # CRUD strings
    crud_strings[tablename] = Storage(
        label_create = T("Add Impact"),
        title_display = T("Impact Details"),
        title_list = T("Impacts"),
        title_update = T("Edit Impact"),
        label_list_button = T("List Impacts"),
        label_delete_button = T("Delete Impact"),
        msg_record_created = T("Impact added"),
        msg_record_modified = T("Impact updated"),
        msg_record_deleted = T("Impact deleted"),
        msg_list_empty = T("No Impacts currently registered"))

# =============================================================================
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def create():
    """ Redirect to assess/create """
    redirect(URL(f="assess", args="create"))

# =============================================================================
# UN Common Operational Datasets
# =============================================================================
def population():

    """ RESTful controller """

    output = s3_rest_controller()
    return output

# =============================================================================
# Rapid Assessments
# =============================================================================
def rat():

    """ Rapid Assessments, RESTful controller """

    # Load Models
    assess_tables()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Villages only
    #table.location_id.requires = IS_EMPTY_OR(IS_ONE_OF(db(db.gis_location.level == "L5"),
    #                                                   "gis_location.id",
    #                                                   repr_select, sort=True))

    # Subheadings in forms:
    configure("assess_section2",
              subheadings = {"population_total": T("Population and number of households"),
                             "dead_women": T("Fatalities"),
                             "injured_women": T("Casualties"),
                             "missing_women": T("Missing Persons"),
                             "household_head_elderly": T("General information on demographics"),
                             "comments": T("Comments"),
                             })
    configure("assess_section3",
              subheadings = {"houses_total": T("Access to Shelter"),
                             "water_containers_available": T("Water storage containers in households"),
                             "cooking_equipment_available": T("Other non-food items"),
                             "nfi_assistance_available": T("Shelter/NFI Assistance"),
                             "comments": T("Comments"),
                             })
    configure("assess_section4",
              subheadings = {"water_source_pre_disaster_type": T("Water supply"),
                             "water_coll_time": T("Water collection"),
                             "defec_place_type": T("Places for defecation"),
                             "close_industry": T("Environment"),
                             "latrines_number": T("Latrines"),
                             "comments": T("Comments"),
                             })
    configure("assess_section5",
              subheadings = {"health_services_pre_disaster": T("Health services status"),
                             "health_problems_adults": T("Current health problems"),
                             "malnutrition_present_pre_disaster": T("Nutrition problems"),
                             "comments": T("Comments"),
                             })
    configure("assess_section6",
              subheadings = {"food_stocks_main_dishes": T("Existing food stocks"),
                             "Food sources": T("food_sources"),
                             "food_assistance_available": T("Food assistance"),
                             "comments": T("Comments"),
                             })
    configure("assess_section7",
              subheadings = {"income_sources_pre_disaster": "%s / %s" % \
                                (T("Sources of income"), T("Major expenses")),
                             "business_damaged": T("Access to cash"),
                             "rank_reconstruction_assistance": T("Current community priorities"),
                             "comments": T("Comments"),
                             })
    configure("assess_section8",
              subheadings = {"schools_total": T("Access to education services"),
                             "alternative_study_places_available": T("Alternative places for studying"),
                             "schools_open_pre_disaster": T("School activities"),
                             "children_0612_female": T("School attendance"),
                             "school_assistance_available": T("School assistance"),
                             "comments": T("Comments"),
                             })
    configure("assess_section9",
              subheadings = {"vulnerable_groups_safe_env": T("Physical Safety"),
                             "children_separated": T("Separated children, caregiving arrangements"),
                             "children_in_disabled_homes": T("Persons in institutions"),
                             "child_activities_u12f_pre_disaster": T("Activities of children"),
                             "coping_activities_elderly": T("Coping Activities"),
                             "current_general_needs": T("Current general needs"),
                             "comments": T("Comments"),
                             })

    # @ToDo  Generalize this and make it available as a function that other
    # component prep methods can call to set the default for a join field.
    def prep(r):
        if r.interactive:
            # Pre-populate staff ID
            staff_id = auth.s3_logged_in_human_resource()
            if staff_id:
                r.table.staff_id.default = staff_id

            if r.method == "create":
                # If this assessment is being created as a component of a shelter,
                # it will have the shelter id in its vars.
                shelter_id = r.get_vars.get("rat.shelter_id", None)
                if shelter_id:
                    try:
                        shelter_id = int(shelter_id)
                    except ValueError:
                        pass
                    else:
                        r.table.shelter_id.default = shelter_id
        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        s3_action_buttons(r, deletable=False)
        # Redirect to update view to open tabs
        if r.representation == "html" and r.method == "create":
            r.next = r.url(method="", id=s3base.s3_get_last_record_id("assess_rat"))
        return output
    response.s3.postp = postp

    # Over-ride the listadd since we're not a component here
    configure(tablename, create_next="", listadd=True)

    tabs = [(T("Identification"), None),
            (T("Demographic"), "section2"),
            (T("Shelter & Essential NFIs"), "section3"),
            (T("WatSan"), "section4"),
            (T("Health"), "section5"),
            (T("Nutrition"), "section6"),
            (T("Livelihood"), "section7"),
            (T("Education"), "section8"),
            (T("Protection"), "section9"),
            ]

    rheader = lambda r: rat_rheader(r,
                                    tabs)

    output = s3_rest_controller(rheader=rheader,
                                s3ocr_config={"tabs": tabs})

    response.s3.stylesheets.append( "S3/rat.css" )
    return output


# -----------------------------------------------------------------------------
def rat_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        if r.name == "rat":
            report = r.record
            if report:
                htable = db.hrm_human_resource
                rheader_tabs = s3_rheader_tabs(r, tabs, paging=True)
                location = report.location_id
                if location:
                    location = r.table.location_id.represent(location)
                staff = report.staff_id
                if staff:
                    organisation_represent = htable.organisation_id.represent
                    query = (htable.id == staff)
                    organisation_id = db(query).select(htable.organisation_id,
                                                       limitby=(0, 1)).first().organisation_id
                    organisation = organisation_represent(organisation_id)
                else:
                    organisation = None
                staff = report.staff2_id
                if staff:
                    query = (htable.id == staff)
                    organisation2_id = db(query).select(htable.organisation_id,
                                                       limitby=(0, 1)).first().organisation_id
                    if organisation2_id == organisation_id:
                        organisation2 = None
                    else:
                        organisation2 = organisation_represent(organisation_id)
                else:
                    organisation2 = None
                if organisation2:
                    orgs = "%s, %s" % (organisation, organisation2)
                else:
                    orgs = organisation
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH("%s: " % T("Date")), report.date
                                  ),
                                TR(
                                    TH("%s: " % T("Organizations")), orgs,
                                  )
                                ),
                              rheader_tabs)

                return rheader
    return None

# =============================================================================
# Flexible Impact Assessments
# =============================================================================
def assess_rheader(r, tabs=[]):
    """ Resource Headers for Flexible Impact Assessments """

    if r.representation == "html":

        rheader_tabs = s3_rheader_tabs(r, tabs)
        assess = r.record
        if assess:
            table = db.assess_assess
            rheader = DIV(TABLE(TR(
                                   TH("%s: " % T("Date & Time")),
                                   table.datetime.represent(assess.datetime),
                                   TH("%s: " % T("Location")),
                                   table.location_id.represent(assess.location_id),
                                   TH("%s: " % T("Assessor")),
                                   table.assessor_person_id.represent(assess.assessor_person_id),
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader

    return None

# -----------------------------------------------------------------------------
def assess():
    """ RESTful CRUD controller """

    # Load Models
    assess_tables()
    impact_tables()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if session.s3.mobile and r.method == "create" and r.interactive:
            # redirect to mobile-specific form:
            redirect(URL(f="assess_short_mobile"))
        return True
    response.s3.prep = prep

    #table.incident_id.comment = DIV(_class="tooltip",
    #                                _title="%s|%s" % (T("Incident"),
    #                                                  T("Optional link to an Incident which this Assessment was triggered by.")))

    tabs = [(T("Edit Details"), None),
            (T("Baselines"), "baseline"),
            (T("Impacts"), "impact"),
            (T("Summary"), "summary"),
            #(T("Requested"), "ritem"),
            ]

    rheader = lambda r: assess_rheader(r, tabs)

    return s3_rest_controller(rheader=rheader)

# -----------------------------------------------------------------------------
def impact_type():
    """ RESTful CRUD controller """

    # Load Models
    impact_tables()

    module = "impact"
    resourcename = "type"

    return s3_rest_controller(module, resourcename)

# -----------------------------------------------------------------------------
def baseline_type():
    """ RESTful CRUD controller """

    # Load Models
    assess_tables()

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def baseline():
    """ RESTful CRUD controller """

    # Load Models
    assess_tables()

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def summary():
    """ RESTful CRUD controller """

    # Load Models
    assess_tables()

    return s3_rest_controller()

# =============================================================================
def basic_assess():
    """ Custom page to hide the complexity of the Assessments/Impacts/Summary model: PC Browser version """

    if not auth.is_logged_in():
        session.error = T("Need to be logged-in to be able to submit assessments")
        redirect(URL(c="default", f="user", args=["login"]))

    # Load Models
    assess_tables()
    impact_tables()

    # See if we've been created from an Incident
    ireport_id = request.vars.get("ireport_id")
    if ireport_id:
        # Location is the same as the calling Incident
        table = db.irs_ireport
        row = db(table.id == ireport_id).select(table.location_id,
                                                limitby=(0, 1)).first()
        if row:
            irs_location_id = row.location_id
            location = table.location_id.represent(irs_location_id)
        else:
            irs_location_id = None
            location = None
        custom_assess_fields = (("impact", 1),
                                ("impact", 2),
                                ("impact", 3),
                                ("impact", 4),
                                ("impact", 5),
                                ("impact", 6),
                                ("impact", 7),
                                ("assess", "comments"),
                                )
        form, form_accepted, assess_id = custom_assess(custom_assess_fields,
                                                       location_id=irs_location_id)
    else:
        location = None
        custom_assess_fields = (("assess", "location_id", "selector"),
                                ("impact", 1),
                                ("impact", 2),
                                ("impact", 3),
                                ("impact", 4),
                                ("impact", 5),
                                ("impact", 6),
                                ("impact", 7),
                                ("assess", "comments"),
                                )
        form, form_accepted, assess_id = custom_assess(custom_assess_fields)

    if form_accepted:
        session.confirmation = T("Basic Assessment Reported")
        redirect(URL(f="assess", args=[assess_id, "impact"]))

    return dict(title = T("Basic Assessment"),
                location = location,
                form = form)

# -----------------------------------------------------------------------------
def mobile_basic_assess():
    """ Custom page to hide the complexity of the Assessments/Impacts/Summary model: Mobile device version """

    if not auth.is_logged_in():
        redirect(URL(c="default", f="index"))

    # Load Models
    assess_tables()
    impact_tables()

    custom_assess_fields = (("assess", "location_id", "auto"),
                            ("impact", 1),
                            ("impact", 2),
                            ("impact", 3),
                            ("impact", 4),
                            ("impact", 5),
                            ("impact", 6),
                            ("impact", 7),
                            ("assess", "comments"),
                            )

    form, form_accepted, assess_id = custom_assess(custom_assess_fields)

    if form_accepted:
        form = FORM(H1(settings.get_system_name_short()),
                    H2(T("Short Assessment")),
                    P(T("Assessment Reported")),
                    A(T("Report Another Assessment..."),
                      _href = URL(r=request)
                      ),
                    _class = "mobile",
                    )

    return dict(form = form)

# -----------------------------------------------------------------------------
def color_code_severity_widget(widget, name):
    """ Utility function to colour-code Severity options """

    for option, color in zip(widget, ["green", "yellow", "orange", "red"]):
        option[0].__setitem__("_style", "background-color:%s;" % color)
        option[0][0].__setitem__("_name", name)

    return widget

# -----------------------------------------------------------------------------
def custom_assess(custom_assess_fields, location_id=None):
    """
        Build a custom page to hide the complexity of the
            Assessments/Impacts/Summary model

        @ToDo: Improved validation
         - the existing .double JS isn't 100% reliable & this currently crashes
           the back-end upon submission if bad data slips through
    """

    # Load Models
    assess_tables()
    impact_tables()

    form_rows = []
    comment = ""
    for field in custom_assess_fields:
        name = "custom_%s_%s" % (field[0], field[1])
        if field[0] == "assess":
            if field[1] == "comments":
                label = "%s:" % db.assess_assess[ field[1] ].label
                #widget = db.assess_assess[ field[1] ].widget
                widget = TEXTAREA(_name = name,
                                  _class = "double",
                                  _type = "text")

            elif field[1] == "location_id":
                if field[2] == "auto":
                    # HTML5 Geolocate
                    label = "%s:" % T("Location")
                    #widget = db.assess_assess[ field[1] ].widget
                    widget = DIV(INPUT(_name = name,
                                       _type = "text"),
                             INPUT(_name = "gis_location_lat",
                                   _id = "gis_location_lat",
                                   _type = "text"),
                             INPUT(_name = "gis_location_lon",
                                   _id = "gis_location_lon",
                                   _type = "text"))
                else:
                    # Location Selector
                    label = "%s:" % T("Location")
                    #widget = SELECT(_id = name,
                    #                _class = "reference gis_location",
                    #                _name = "location_id")
                    #response.s3.gis.location_id = "custom_assess_location_id"
                    widget = db.assess_assess.location_id.widget(field=db.assess_assess.location_id,
                                                                 value="")

        elif field[0] == "baseline":
            label = S3Represent(lookup="assess_baseline_type")(field[1])
            label = "%s:" % T(label)
            widget = INPUT(_name = name,
                           _class = "double",
                           _type = "text")

        elif field[0] == "impact":
            label = S3Represent(lookup="assess_impact_type")(field[1])
            label = "%s:" % T(label)
            value_widget = INPUT(_name = name,
                                 _class = "double",
                                 _type = "text")
            severity_widget = db.assess_summary.value.widget(db.impact_impact.severity,
                                                             0,
                                                             _name = "%s_severity" % name
                                                            )
            severity_widget = color_code_severity_widget(severity_widget,
                                                         "%s_severity" % name)

            widget = DIV(value_widget,
                         DIV("%s:" % T("Severity")),
                         severity_widget,
                         XML("&nbsp"))

        elif field[0] == "summary":
            label = "%s:" % T(org_subsector_represent(field[1]))
            widget = db.assess_summary.value.widget(db.assess_summary.value,
                                                    0, _name = name)
            widget = color_code_severity_widget(widget)

        # Add the field components to the form_rows
        if field[0] == "title":
            form_rows.append(TR(H3( field[1] )))
        else:
            form_rows = form_rows + list(s3_formstyle("%s__row" % name,
                                                      label,
                                                      widget,
                                                      comment))

    form = FORM(TABLE(*form_rows),
                INPUT(_value = T("Save"), _type = "submit"))
    assess_id = None

    form_accepted = form.accepts(request.vars, session)
    if form_accepted:
        record_dict = {"organisation_id" : session.s3.organisation_id}

        for field in custom_assess_fields:
            if field[0] != "assess" or field[1] == "location":
                continue
            name = "custom__assess_%s" % field[1]
            if name in request.vars:
                record_dict[field[1]] = request.vars[name]

        # Add Location (must happen first)
        if "custom_assess_location_id" in request.vars:
            # Auto
            location_dict = {}
            if "gis_location_lat" in request.vars:
                location_dict["lat"] = request.vars["gis_location_lat"]
            if "gis_location_lon" in request.vars:
                location_dict["lon"] = request.vars["gis_location_lon"]
            location_dict["name"] = request.vars["custom_assess_location_id"]
            record_dict["location_id"] = s3db.gis_location.insert(**location_dict)

        if "location_id" in request.vars:
            # Location Selector
            record_dict["location_id"] = request.vars["location_id"]

        if location_id:
            # Location_id was passed to function
            record_dict["location_id"] = location_id

        # Add Assessment
        assess_id = db.assess_assess.insert(**record_dict)

        fk_dict = dict(baseline = "baseline_type_id",
                       impact = "impact_type_id",
                       summary = "subsector_id"
                      )

        component_dict = dict(baseline = "assess_baseline",
                              impact = "impact_impact",
                              summary = "assess_summary"
                            )

        # Add Assessment Components
        sector_summary = {}
        for field in custom_assess_fields:
            if field[0] == "assess":
                continue
            record_dict = {}
            name = "custom_%s_%s" % (field[0], field[1])
            if name in request.vars:
                record_dict["assess_id"] = assess_id
                record_dict[fk_dict[ field[0] ] ] = field[1]
                record_dict["value"] = request.vars[name]

                if field[0] == "impact":
                    severity = int(request.vars[name + "_severity"])
                    record_dict["severity"] = severity

                    if not record_dict["value"] and not record_dict["severity"]:
                        # Do not record impact if there is no data for it.
                        # Should we still average severity though? Now not doing this
                        continue

                    # Record the Severity per sector
                    table = db.impact_type
                    row = db(table.id == field[1]).select(table.sector_id,
                                                          limitby=(0, 1)
                                                          ).first()
                    sector_id = row.sector_id
                    if sector_id in sector_summary:
                        sector_summary[sector_id].append(severity)
                    elif sector_id:
                        sector_summary[sector_id] = [severity]

                db[component_dict[ field[0] ] ].insert(**record_dict)

        # Add Cluster summaries
        # @ToDo: make sure that this doesn't happen if there are sectors in the assess
        for sector_id in sector_summary:
            severity_values = sector_summary[sector_id]
            db.assess_summary.insert(assess_id = assess_id,
                                     sector_id = sector_id,
                                     # Average severity
                                     value = sum(severity_values) / len(severity_values)
                                     )

        # Send Out Notification SMS
        #message = "Sahana: " + T("New Assessment reported from") + " %s by %s %s" % ( location_dict["name"],
        #                                                         session.auth.user.first_name,
        #                                                         session.auth.user.last_name
        #                                                         )
        # Hard coded notification message for Demo
        #msg.send_by_pe_id(3,
        #                  message=message,
        #                  contact_method = 2)

    return form, form_accepted, assess_id

# =============================================================================
def type():
    """ RESTful CRUD controller """

    return s3_rest_controller("impact", "type")

# =============================================================================
def impact():
    """ RESTful CRUD controller """

    return s3_rest_controller("impact", "impact")

# END =========================================================================
