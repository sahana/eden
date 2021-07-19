# -*- coding: utf-8 -*-

""" Shelter (Camp) Registry, model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("CRShelterModel",
           "CRShelterServiceModel",
           "CRShelterInspectionModel",
           "CRShelterRegistrationModel",
           "cr_shelter_rheader",
           "cr_update_shelter_population",
           "cr_update_housing_unit_population",
           "cr_update_capacity_from_housing_units",
           "cr_check_population_availability",
           "cr_notification_dispatcher",
           "cr_resolve_shelter_flags",
           )

import json

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

NIGHT = 1
DAY_AND_NIGHT = 2

# =============================================================================
class CRShelterModel(S3Model):

    names = ("cr_shelter_type",
             "cr_shelter",
             "cr_shelter_id",
             "cr_shelter_status",
             "cr_shelter_person",
             "cr_shelter_allocation",
             "cr_shelter_unit",
             "cr_shelter_unit_id",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        settings = current.deployment_settings

        messages = current.messages
        NONE = messages["NONE"]

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link
        set_method = self.set_method

        NAME = T("Name")
        location_id = self.gis_location_id

        # ---------------------------------------------------------------------
        # Shelter types
        # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
        tablename = "cr_shelter_type"
        define_table(tablename,
                     Field("name", notnull=True,
                           label = NAME,
                           requires = [IS_NOT_EMPTY(),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     skip_imports = True,
                                                     ),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
            ADD_SHELTER_TYPE = T("Add Camp Type")
            SHELTER_TYPE_LABEL = T("Camp Type")
            crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER_TYPE,
                title_display = T("Camp Type Details"),
                title_list = T("Camp Types"),
                title_update = T("Edit Camp Type"),
                label_list_button = T("List Camp Types"),
                msg_record_created = T("Camp Type added"),
                msg_record_modified = T("Camp Type updated"),
                msg_record_deleted = T("Camp Type deleted"),
                msg_list_empty = T("No Camp Types currently registered"))
        else:
            ADD_SHELTER_TYPE = T("Create Shelter Type")
            SHELTER_TYPE_LABEL = T("Shelter Type")
            crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER_TYPE,
                title_display = T("Shelter Type Details"),
                title_list = T("Shelter Types"),
                title_update = T("Edit Shelter Type"),
                label_list_button = T("List Shelter Types"),
                msg_record_created = T("Shelter Type added"),
                msg_record_modified = T("Shelter Type updated"),
                msg_record_deleted = T("Shelter Type deleted"),
                msg_list_empty = T("No Shelter Types currently registered"))

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        represent = S3Represent(lookup=tablename, translate=True)
        shelter_type_id = S3ReusableField("shelter_type_id", "reference %s" % tablename,
                                          label = SHELTER_TYPE_LABEL,
                                          ondelete = "RESTRICT",
                                          represent = represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "cr_shelter_type.id",
                                                                  represent)),
                                          comment = S3PopupLink(c = "cr",
                                                                f = "shelter_type",
                                                                label = ADD_SHELTER_TYPE,
                                                                ),
                                          )

        # -------------------------------------------------------------------------
        # Shelter Environmental Characteristics
        # e.g. Lake, Mountain, ground type.
        tablename = "cr_shelter_environment"
        define_table(tablename,
                     Field("name", notnull=True,
                           label = NAME,
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        environment_represent = S3Represent(lookup=tablename, translate=True)
        environment_multirepresent = S3Represent(lookup=tablename,
		                                         translate=True,
                                                 multiple=True
                                                 )

        shelter_environment_id = S3ReusableField("cr_shelter_environment_id",
                                                 "list:reference cr_shelter_environment",
                                                 label = T("Environmental Characteristics"),
                                                 ondelete = "RESTRICT",
                                                 represent = environment_multirepresent,
                                                 requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                                  "cr_shelter_environment.id",
                                                                                  environment_represent,
                                                                                  multiple=True)),
                                                 sortby = "name",
                                                 widget = S3MultiSelectWidget()
                                                 )


        # -------------------------------------------------------------------------
        # Shelters
        #
        cr_shelter_opts = {1 : T("Closed"),
                           # In many languages, translations of "Open" differ
                           # between the verb and the adjective, as well as
                           # between grammatical moods or genders etc - so
                           # adding a context-comment for T() here to clarify
                           # which "Open" we mean (will not be rendered):
                           2 : T("Open##status"),
                           }

        day_and_night = settings.get_cr_day_and_night()
        dynamic = settings.get_cr_shelter_population_dynamic()

        if settings.get_cr_shelter_housing_unit_management():
            if day_and_night:
                capacity_day_comment = DIV(_class="tooltip",
                                           _title="%s|%s|%s" % (T("Capacity (Day)"),
                                                                T("Capacity of the shelter during the day"),
                                                                T("Capacity evaluated adding all defined housing unit capacities")))
                capacity_night_comment = DIV(_class="tooltip",
                                             _title="%s|%s|%s" % (T("Capacity (Night)"),
                                                                  T("Capacity of the shelter during the night"),
                                                                  T("Capacity evaluated adding all defined housing unit capacities")))
            else:
                capacity_day_comment = DIV(_class="tooltip",
                                           _title="%s|%s|%s" % (T("Capacity"),
                                                                T("Capacity of the shelter as a number of people"),
                                                                T("Capacity evaluated adding all defined housing unit capacities")))
                capacity_night_comment = None
        else:
            if day_and_night:
                capacity_day_comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (T("Capacity (Day)"),
                                                             T("Capacity of the shelter during the day")))
                capacity_night_comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Capacity (Night)"),
                                                               T("Capacity of the shelter during the night")))
            else:
                capacity_day_comment = DIV(_class="tooltip",
                                           _title="%s|%s" % (T("Capacity"),
                                                             T("Capacity of the shelter as a number of people")))
                capacity_night_comment = None

        tablename = "cr_shelter"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     # @ToDo: code_requires
                     #Field("code", length=10, # Mayon compatibility
                     #      label=T("Code")
                     #      ),
                     Field("name", notnull=True,
                           length=64,            # Mayon compatibility
                           label = T("Shelter Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                     ),
                     shelter_type_id(),          # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
                     shelter_environment_id(readable = False,
                                            writable = False,),# Enable in template if-required
                     location_id(),
                     Field("phone",
                           label = T("Phone"),
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           ),
                     Field("email", "string",
                           label = T("Email"),
                           ),
                     self.pr_person_id(label = T("Contact Person / Camp Owner")),
                     #Static field
                     Field("population", "integer",
                           label = T("Estimated Population"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = not dynamic,
                           writable = not dynamic,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Current estimated population"),
                                                           T("Current estimated population in shelter. Staff, Volunteers and Evacuees."))),
                           ),
                     Field("capacity_day", "integer",
                           default = 0,
                           label = T("Capacity (Day)") if day_and_night else T("Capacity"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = capacity_day_comment,
                           ),
                     Field("capacity_night", "integer",
                           default = 0,
                           label = T("Capacity (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = day_and_night,
                           writable = day_and_night,
                           comment = capacity_night_comment,
                           ),
                     # Dynamic field
                     Field("available_capacity_day", "integer",
                           default = 0,
                           label = T("Available Capacity (Day)") if day_and_night else T("Available Capacity"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = dynamic and day_and_night,
                           # Automatically updated
                           writable = False,
                           ),
                     # Dynamic field
                     Field("available_capacity_night", "integer",
                           default = 0,
                           label = T("Available Capacity (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = dynamic and day_and_night,
                           # Automatically updated
                           writable = False,
                           ),
                     # Dynamic field
                     Field("population_day", "integer",
                           default = 0,
                           label = T("Current Population (Day)") if day_and_night else T("Current Population"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Population (Day)"),
                                                           T("Number of people registered in the shelter for day and night"))),
                           readable = dynamic,
                           # Automatically updated
                           writable = False
                           ),
                     # Dynamic field
                     Field("population_night", "integer",
                           default = 0,
                           label = T("Current Population (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Population (Night)"),
                                                           T("Number of people registered in the shelter for the night"))),
                           readable = dynamic and day_and_night,
                           # Automatically updated
                           writable = False
                           ),
                     Field("status", "integer",
                           label = T("Status"),
                           default = 2, # Open
                           represent = S3Represent(options = cr_shelter_opts),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(cr_shelter_opts)
                                       ),
                           ),
                     s3_comments(),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: messages.OBSOLETE if opt else NONE,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # Components
        add_components(tablename,
                       cr_shelter_allocation = "shelter_id",
                       cr_shelter_registration = "shelter_id",
                       cr_shelter_unit = "shelter_id",
                       cr_shelter_status = {"name": "status",
                                            "joinby": "shelter_id",
                                            },
                       cr_shelter_service_shelter = "shelter_id",
                       cr_shelter_service = {"link": "cr_shelter_service_shelter",
                                             "joinby": "shelter_id",
                                             "key": "service_id",
                                             },
                       event_event_shelter = "shelter_id",
                       )

        # Fields for pivot table reports
        report_fields = ["name",
                         "shelter_type_id",
                         #"organisation_id",
                         "status",
                         ]
        if dynamic:
            report_fields.append("population_day")
            if day_and_night:
                report_fields.append("population_night")
        else:
            # Manual
            report_fields.append("population")

        # Text filter fields
        text_fields = ["name",
                       #"code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       "location_id$name",
                       ]

        # List fields
        list_fields = ["name",
                       "status",
                       "shelter_type_id",
                       #"shelter_service_shelter.service_id",
                       ]
        if dynamic:
            list_fields.append("capacity_day")
            if day_and_night:
                list_fields.append("capacity_night")
            list_fields.append("population_day")
            if day_and_night:
                list_fields.append("population_night")
        else:
            # Manual
            list_fields.append("population")
        list_fields.append("location_id$addr_street")
        #list_fields.append("person_id")

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()
        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)
            list_fields.append(lfield)

        # Filter widgets
        cr_shelter_status_filter_opts = dict(cr_shelter_opts)
        cr_shelter_status_filter_opts[None] = T("Unspecified")

        if settings.get_org_branches():
            org_filter = S3HierarchyFilter("organisation_id",
                                           leafonly = False,
                                           )
        else:
            org_filter = S3OptionsFilter("organisation_id",
                                         search = True,
                                         header = "",
                                         #hidden = True,
                                         )
        filter_widgets = [
                S3TextFilter(text_fields,
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                S3OptionsFilter("shelter_type_id",
                                label = T("Type"),
                                # Doesn't translate
                                #represent = "%(name)s",
                                ),
                org_filter,
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = levels,
                                 ),
                S3OptionsFilter("status",
                                label = T("Status"),
                                options = cr_shelter_status_filter_opts,
                                none = True,
                                ),
                ]

        if dynamic:
            if day_and_night:
                filter_widgets.append(S3RangeFilter("available_capacity_night",
                                                    label = T("Available Capacity (Night)"),
                                                    ))
            else:
                filter_widgets.append(S3RangeFilter("available_capacity_day",
                                                    label = T("Available Capacity"),
                                                    ))
        if day_and_night:
            filter_widgets.append(S3RangeFilter("capacity_night",
                                                label = T("Total Capacity (Night)"),
                                                ))
        else:
            filter_widgets.append(S3RangeFilter("capacity_day",
                                                label = T("Total Capacity"),
                                                ))

        # Custom create_next
        if settings.get_cr_shelter_people_registration():
            # Go to People check-in for this shelter after creation
            create_next = URL(c="cr", f="shelter",
                              args=["[id]", "shelter_registration"])
        else:
            create_next = None

        # Table configuration
        configure(tablename,
                  create_next = create_next,
                  deduplicate = S3Duplicate(),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.cr_shelter_onaccept,
                  report_options = Storage(
                        rows = report_fields,
                        cols = report_fields,
                        fact = report_fields,
                        defaults = Storage(rows = lfield, # Lowest-level of hierarchy
                                           cols = "status",
                                           fact = "count(name)",
                                           totals = True,
                                           )
                        ),
                  super_entity = ("org_site", "doc_entity", "pr_pentity"),
                  )

        # Custom method to assign HRs
        set_method("cr", "shelter",
                   method = "assign",
                   action = self.hrm_AssignMethod(component="human_resource_site"),
                   )

        # Check-in method
        set_method("cr", "shelter",
                   method="check-in",
                   action = self.org_SiteCheckInMethod,
                   )

        # Notification-dispatch method
        set_method("cr", "shelter",
                   method = "dispatch",
                   action = cr_notification_dispatcher,
                   )

        # Shelter Inspection method
        set_method("cr", "shelter",
                   method = "inspection",
                   action = CRShelterInspection,
                   )

        # CRUD strings
        if settings.get_ui_label_camp():
            ADD_SHELTER = T("Add Camp")
            SHELTER_LABEL = T("Camp")
            SHELTER_HELP = T("The Camp this Request is from")
            crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER,
                title_display = T("Camp Details"),
                title_list = T("Camps"),
                title_update = T("Edit Camp"),
                label_list_button = T("List Camps"),
                msg_record_created = T("Camp added"),
                msg_record_modified = T("Camp updated"),
                msg_record_deleted = T("Camp deleted"),
                msg_list_empty = T("No Camps currently registered"))

        else:
            ADD_SHELTER = T("Create Shelter")
            SHELTER_LABEL = T("Shelter")
            SHELTER_HELP = T("The Shelter this Request is from")
            crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER,
                title_display = T("Shelter Details"),
                title_list = T("Shelters"),
                title_update = T("Edit Shelter"),
                label_list_button = T("List Shelters"),
                msg_record_created = T("Shelter added"),
                msg_record_modified = T("Shelter updated"),
                msg_record_deleted = T("Shelter deleted"),
                msg_list_empty = T("No Shelters currently registered"))

        # Reusable field
        represent = S3Represent(lookup=tablename)
        shelter_id = S3ReusableField("shelter_id", "reference %s" % tablename,
                                     label = SHELTER_LABEL,
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "cr_shelter.id",
                                                              represent,
                                                              sort=True)),
                                     comment = S3PopupLink(c = "cr",
                                                           f = "shelter",
                                                           label = ADD_SHELTER,
                                                           title = SHELTER_LABEL,
                                                           tooltip = "%s (%s)." % (SHELTER_HELP,
                                                                                   T("optional"),
                                                                                   ),
                                                           ),
                                     widget = S3AutocompleteWidget("cr", "shelter")
                                     )

        # -------------------------------------------------------------------------
        # Shelter statuses
        # - a historical record of shelter status: opening/closing dates & populations
        #
        tablename = "cr_shelter_status"
        define_table(tablename,
                     shelter_id(ondelete = "CASCADE"),
                     s3_date(),
                     Field("status", "integer",
                           label = T("Status"),
                           represent = S3Represent(options = cr_shelter_opts),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(cr_shelter_opts)
                                       ),
                           ),
                     Field("population", "integer",
                           label = T("Population"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if settings.get_ui_label_camp():
            crud_strings[tablename] = Storage(
                label_create = T("Add Camp Status"),
                title_display = T("Camp Status Details"),
                title_list = T("Camp Statuses"),
                title_update = T("Edit Camp Status"),
                label_list_button = T("List Camp Statuses"),
                msg_record_created = T("Camp Status added"),
                msg_record_modified = T("Camp Status updated"),
                msg_record_deleted = T("Camp Status deleted"),
                msg_list_empty = T("No Camp Statuses currently registered"))
        else:
            crud_strings[tablename] = Storage(
                label_create = T("Create Shelter Status"),
                title_display = T("Shelter Status Details"),
                title_list = T("Shelter Statuses"),
                title_update = T("Edit Shelter Status"),
                label_list_button = T("List Shelter Statuses"),
                msg_record_created = T("Shelter Status added"),
                msg_record_modified = T("Shelter Status updated"),
                msg_record_deleted = T("Shelter Status deleted"),
                msg_list_empty = T("No Shelter Statuses currently registered"))

        # -------------------------------------------------------------------------
        # Housing units
        #
        cr_housing_unit_opts = {1: T("Available"),
                                2: T("Not Available"),
                                }

        cr_housing_unit_handicap_facilities = {1: T("Available"),
                                               2: T("Suitable"),
                                               3: T("Not Available"),
                                               }

        tablename = "cr_shelter_unit"
        define_table(tablename,
                     Field("name", notnull=True, length = 64,
                           label = T("Housing Unit Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     # @ToDo: Using site_id would be more flexible & link
                     #        better to default_site/auth.user.site_id
                     shelter_id(ondelete = "CASCADE"),
                     location_id(widget = S3LocationSelector(#catalog_layers=True,
                                                             points = False,
                                                             polygons = True,
                                                             ),
                                 ),
                     Field("status", "integer",
                           default = 1,
                           label = T("Status"),
                           represent = lambda opt: \
                               cr_housing_unit_opts.get(opt, messages.UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(cr_housing_unit_opts))
                           ),
                     Field("transitory", "boolean",
                           default = False,
                           label = T("Transitory Accommodation"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Transitory Accommodation"),
                                                           T("This unit is for transitory accommodation upon arrival."),
                                                           ),
                                         ),
                           # Enable in template as required:
                           readable = False,
                           writable = False,
                           ),
                     Field("bath", "boolean",
                           default = True,
                           label = T("Available Bath"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Bath Availability"),
                                                           T("Integrated bath within housing unit"),
                                                           ),
                                         ),
                           ),
                     Field("handicap_bath", "integer",
                           default = 1,
                           label = T("Bath with handicap facilities"),
                           represent = lambda opt: \
                               cr_housing_unit_handicap_facilities.get(opt, messages.UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(cr_housing_unit_handicap_facilities)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Bath Handicap Facilities"),
                                                           T("Availability of bath handicap facilities"),
                                                           ),
                                         ),
                           ),
                     Field("shower", "boolean",
                           default = True,
                           label = T("Available Shower"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Shower Availability"),
                                                           T("Integrated shower within housing unit"))),
                           ),
                     Field("handicap_shower", "integer",
                           default = 1,
                           label = T("Shower with handicap facilities"),
                           represent = lambda opt: \
                               cr_housing_unit_handicap_facilities.get(opt, messages.UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(cr_housing_unit_handicap_facilities)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Shower Handicap Facilities"),
                                                           T("Availability of shower handicap facilities"),
                                                           ),
                                         ),
                           ),
                     Field("capacity_day", "integer",
                           default = 0,
                           label = T("Housing Unit Capacity (Day)") if day_and_night else T("Housing Unit Capacity"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Housing Unit Capacity (Day)"),
                                                           T("Capacity of the housing unit for people during the day"),
                                                           ),
                                         ),
                           ),
                     Field("capacity_night", "integer",
                           default = 0,
                           label = T("Housing Unit Capacity (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           readable = day_and_night,
                           writable = day_and_night,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Housing Unit Capacity (Night)"),
                                                           T("Capacity of the housing unit for people during the night"),
                                                           ),
                                         ),
                           ),
                     Field("available_capacity_day", "integer",
                           default = 0,
                           label = T("Available Capacity (Day)") if day_and_night else T("Available Capacity"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class = "tooltip",
                                         _title = T("Currently Available Capacity (Day)"),
                                         ),
                           # Automatically updated
                           readable = dynamic,
                           writable = False,
                           ),
                     Field("available_capacity_night", "integer",
                           default = 0,
                           label = T("Population Availability (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class = "tooltip",
                                         _title = T("Currently Available Capacity (Night)"),
                                         ),
                           # Automatically updated
                           readable = dynamic and day_and_night,
                           writable = False,
                           ),
                     Field("population_day", "integer",
                           default = 0,
                           label = T("Current Population (Day)") if day_and_night else T("Current Population"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Housing Unit Current Population"),
                                                           T("Number of people registered in this housing unit for day and night"),
                                                           ),
                                         ),
                           # Automatically updated
                           readable = False,
                           writable = False,
                           ),
                     Field("population_night", "integer",
                           default = 0,
                           label = T("Current Population (Night)"),
                           represent = IS_INT_AMOUNT.represent,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Housing Unit Current Population"),
                                                           T("Number of evacuees registered in this housing unit for the night"),
                                                           ),
                                         ),
                           readable = day_and_night,
                           # Automatically updated
                           writable = False,
                           ),
                     Field("domestic_animals", "boolean",
                           default = False,
                           label = T("Free for domestic animals"),
                           represent = s3_yes_no_represent,
                           ),
                     Field.Method("cstatus", self.cr_shelter_unit_status),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        add_components(tablename,
                       cr_shelter_inspection = "shelter_unit_id",
                       )

        # List fields
        list_fields = ["id",
                       "name",
                       ]
        if day_and_night:
            list_fields += ["status", # @ToDO: Move to EVASS template
                            "handicap_bath", # @ToDO: Move to EVASS template
                            "capacity_day",
                            "capacity_night",
                            "population_day",
                            "population_night",
                            ]
        else:
            list_fields += ["available_capacity_day",
                            "capacity_day",
                            "population_day",
                            ]

        # Table configuration
        population_onaccept = lambda form: \
                                self.cr_shelter_population_onaccept(
                                            form,
                                            tablename="cr_shelter_unit",
                                            )
        configure(tablename,
                  # @ToDo: Allow multiple shelters to have the same
                  # name of unit (Requires that Shelter is in dvr/person.xsl/csv)
                  #deduplicate = S3Duplicate(primary=("shelter_id", "name")),
                  deduplicate = S3Duplicate(),
                  list_fields = list_fields,
                  # Extra fields for cr_shelter_unit_status:
                  extra_fields = ["capacity_day",
                                  "available_capacity_day",
                                  "status",
                                  ],
                  onaccept = population_onaccept,
                  ondelete = population_onaccept,
                  )

        # Reusable Field
        represent = S3Represent(lookup="cr_shelter_unit")
        shelter_unit_id = S3ReusableField("shelter_unit_id", db.cr_shelter_unit,
                                          label = T("Housing Unit"),
                                          ondelete = "RESTRICT",
                                          represent = represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "cr_shelter_unit.id",
                                                                  represent,
                                                                  orderby="shelter_id",
                                                                  #sort=True,
                                                                  )),
                                          #widget = S3AutocompleteWidget("cr", "shelter_unit")
                                          )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return {"ADD_SHELTER" : ADD_SHELTER,
                "SHELTER_LABEL" : SHELTER_LABEL,
                "cr_shelter_id" : shelter_id,
                "cr_shelter_unit_id" : shelter_unit_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"cr_shelter_id": lambda **attr: dummy("shelter_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_onaccept(form):
        """
            After DB I/O
        """

        s3db = current.s3db
        form_vars = form.vars
        shelter_id = form_vars.id

        # Update Affiliation, record ownership and component ownership
        s3db.org_update_affiliations("cr_shelter", form_vars)

        # @ToDo: Create a cr_shelter_status record

        if current.response.s3.bulk:
            # Import
            return

        if current.deployment_settings.get_cr_shelter_population_dynamic():
            # Update population and available capacity
            cr_update_shelter_population(shelter_id)

        # Create an org_site_event record
        stable = s3db.cr_shelter
        shelter = current.db(stable.id == shelter_id).select(stable.site_id,
                                                             stable.status,
                                                             stable.obsolete,
                                                             limitby = (0, 1)
                                                             ).first()
        record = form.record
        if record:
            # Update form
            obsolete = shelter.obsolete
            if obsolete != record.obsolete:
                s3db.org_site_event.insert(site_id = shelter.site_id,
                                           event = 4, # Obsolete Change
                                           comment = obsolete,
                                           )
            status = shelter.status
            if status != record.status:
                s3db.org_site_event.insert(site_id = shelter.site_id,
                                           event = 1, # Status Change
                                           status = status,
                                           )
        else:
            # Create form
            s3db.org_site_event.insert(site_id = shelter.site_id,
                                       event = 1, # Status Change
                                       status = shelter.status,
                                       )

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_unit_status(row):
        """
            Virtual Field to show the status of the unit by available capacity
            - used to colour features on the map
            0: Full
            1: Partial
            2: Empty
            3: Not Available
        """

        if hasattr(row, "cr_shelter_unit"):
            row = row.cr_shelter_unit

        if hasattr(row, "status"):
            status = row.status
        else:
            status = None

        if status == 2:
            # Not Available
            return 3

        if hasattr(row, "available_capacity_day"):
            actual = row.available_capacity_day
        else:
            actual = None

        if status is not None and actual is not None:
            if actual <= 0:
                # Full (or over-capacity)
                return 0

        if hasattr(row, "capacity_day"):
            total = row.capacity_day
            if total == 0:
                # No capacity ever, so Full
                return 0
        else:
            total = None

        if status is not None and total is not None and actual is not None:
            if actual == total:
                # Empty
                return 2
            else:
                # Partial
                return 1

        if hasattr(row, "id"):
            # Reload the record
            current.log.debug("Reloading cr_shelter_unit record")
            table = current.s3db.cr_shelter_unit
            r = current.db(table.id == row.id).select(table.status,
                                                      table.capacity_day,
                                                      table.available_capacity_day,
                                                      limitby=(0, 1)
                                                      ).first()
            if r:
                status = r.status
                if status == 2:
                    # Not Available
                    return 3
                actual = r.available_capacity_day
                if actual <= 0:
                    # Full (or over-capacity)
                    return 0
                total = r.capacity_day
                if total == 0:
                    # No capacity ever, so Full
                    return 0
                elif actual == total:
                    # Empty
                    return 2
                else:
                    # Partial
                    return 1

        return current.messages["NONE"]

# =============================================================================
class CRShelterServiceModel(S3Model):
    """ Model for Shelter Services """

    names = ("cr_shelter_service",
             "cr_shelter_service_shelter",
             )

    def model(self):

        T = current.T

        define_table = self.define_table

        # -------------------------------------------------------------------------
        # Shelter services
        # e.g. medical, housing, food, ...
        tablename = "cr_shelter_service"
        define_table(tablename,
                     Field("name", notnull=True,
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if current.deployment_settings.get_ui_label_camp():
            ADD_SHELTER_SERVICE = T("Add Camp Service")
            SHELTER_SERVICE_LABEL = T("Camp Service")
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER_SERVICE,
                title_display = T("Camp Service Details"),
                title_list = T("Camp Services"),
                title_update = T("Edit Camp Service"),
                label_list_button = T("List Camp Services"),
                msg_record_created = T("Camp Service added"),
                msg_record_modified = T("Camp Service updated"),
                msg_record_deleted = T("Camp Service deleted"),
                msg_list_empty = T("No Camp Services currently registered"))
        else:
            ADD_SHELTER_SERVICE = T("Create Shelter Service")
            SHELTER_SERVICE_LABEL = T("Shelter Service")
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = ADD_SHELTER_SERVICE,
                title_display = T("Shelter Service Details"),
                title_list = T("Shelter Services"),
                title_update = T("Edit Shelter Service"),
                label_list_button = T("List Shelter Services"),
                msg_record_created = T("Shelter Service added"),
                msg_record_modified = T("Shelter Service updated"),
                msg_record_deleted = T("Shelter Service deleted"),
                msg_list_empty = T("No Shelter Services currently registered"))

        service_represent = S3Represent(lookup=tablename, translate=True)

        service_id = S3ReusableField("service_id", "reference %s" % tablename,
                                     label = SHELTER_SERVICE_LABEL,
                                     ondelete = "RESTRICT",
                                     represent = service_represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(current.db,
                                                              "cr_shelter_service.id",
                                                              service_represent)),
                                     sortby = "name",
                                     comment = S3PopupLink(c = "cr",
                                                           f = "shelter_service",
                                                           label = ADD_SHELTER_SERVICE,
                                                           ),
                                     )
        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        # ---------------------------------------------------------------------
        # Shelter Service <> Shelter link table
        #
        tablename = "cr_shelter_service_shelter"
        define_table(tablename,
                     self.cr_shelter_id(empty = False,
                                        ondelete = "CASCADE",
                                        ),
                     service_id(empty = False,
                                ondelete = "CASCADE",
                                ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {#"cr_shelter_service_id": service_id,
                }

    # -------------------------------------------------------------------------
    #@staticmethod
    #def defaults():
    #    """ Safe defaults for names in case the module is disabled """

    #    dummy = S3ReusableField("dummy_id", "integer",
    #                            readable = False,
    #                            writable = False,
    #                            )

    #    return {"cr_shelter_service_id":  lambda **attr: dummy("service_id"),
    #            }

# =============================================================================
class CRShelterInspectionModel(S3Model):
    """ Model for Shelter / Housing Unit Flags """

    names = ("cr_shelter_flag",
             "cr_shelter_flag_id",
             "cr_shelter_inspection",
             "cr_shelter_inspection_flag",
             "cr_shelter_inspection_task",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        shelter_inspection_tasks = settings.get_cr_shelter_inspection_tasks()
        task_priority_opts = settings.get_project_task_priority_opts()

        assignee_represent = self.pr_PersonEntityRepresent(show_label = False,
                                                           #show_type = False,
                                                           )

        # ---------------------------------------------------------------------
        # Flags - flags that can be set for a shelter / housing unit
        #
        tablename = "cr_shelter_flag"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("create_task", "boolean",
                           label = T("Create Task"),
                           default = False,
                           represent = s3_yes_no_represent,
                           readable = shelter_inspection_tasks,
                           writable = shelter_inspection_tasks,
                           ),
                     Field("task_description", length=100,
                           label = T("Task Description"),
                           requires = IS_EMPTY_OR(IS_LENGTH(100)),
                           represent = lambda v: v if v else "",
                           readable = shelter_inspection_tasks,
                           writable = shelter_inspection_tasks,
                           ),
                     Field("task_priority", "integer",
                           default = 3,
                           label = T("Priority"),
                           represent = S3Represent(options=task_priority_opts),
                           requires = IS_IN_SET(task_priority_opts,
                                                zero = None,
                                                ),
                           ),
                     # Task Assignee
                     Field("task_assign_to", "reference pr_pentity",
                           label = T("Assign to"),
                           represent = assignee_represent,
                           requires = IS_EMPTY_OR(
                                           IS_ONE_OF(db, "pr_pentity.pe_id",
                                                     assignee_represent,
                                                     filterby = "instance_type",
                                                     filter_opts = ("pr_person",
                                                                    "pr_group",
                                                                    #"org_organisation",
                                                                    ),
                                                     ),
                                           ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table settings
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  onvalidation = self.shelter_flag_onvalidation,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Shelter Flag"),
            title_display = T("Shelter Flag Details"),
            title_list = T("Shelter Flags"),
            title_update = T("Edit Shelter Flag"),
            label_list_button = T("List Shelter Flags"),
            label_delete_button = T("Delete Shelter Flag"),
            msg_record_created = T("Shelter Flag created"),
            msg_record_modified = T("Shelter Flag updated"),
            msg_record_deleted = T("Shelter Flag deleted"),
            msg_list_empty = T("No Shelter Flags currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        flag_id = S3ReusableField("flag_id", "reference %s" % tablename,
                                  label = T("Shelter Flag"),
                                  represent = represent,
                                  requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                       represent,
                                                       ),
                                  sortby = "name",
                                  )

        # ---------------------------------------------------------------------
        # Shelter Inspection
        #
        tablename = "cr_shelter_inspection"
        define_table(tablename,
                     #self.cr_shelter_id(ondelete = "CASCADE",
                     #                   readable = False,
                     #                   writable = False,
                     #                   ),
                     self.cr_shelter_unit_id(ondelete = "CASCADE"),
                     s3_date(default = "now",
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Form
        crud_form = S3SQLCustomForm("shelter_unit_id",
                                    "date",
                                    S3SQLInlineLink("shelter_flag",
                                                    field = "flag_id",
                                                    multiple = True,
                                                    cols = 3,
                                                    ),
                                    "comments",
                                    )

        # List fields
        list_fields = ["shelter_unit_id",
                       "date",
                       (T("Flags"), "shelter_flag__link.flag_id"),
                       (T("Registered by"), "modified_by"),
                       "comments",
                       ]

        # Table configuration
        configure(tablename,
                  crud_form = crud_form,
                  list_fields = list_fields,
                  orderby = "%s.date desc" % tablename,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Shelter Inspection"),
            title_display = T("Shelter Inspection Details"),
            title_list = T("Shelter Inspections"),
            title_update = T("Edit Shelter Inspection"),
            label_list_button = T("List Shelter Inspections"),
            label_delete_button = T("Delete Shelter Inspection"),
            msg_record_created = T("Shelter Inspection created"),
            msg_record_modified = T("Shelter Inspection updated"),
            msg_record_deleted = T("Shelter Inspection deleted"),
            msg_list_empty = T("No Shelter Inspections currently registered"),
        )

        # Components
        self.add_components(tablename,
                            cr_shelter_flag = {"link": "cr_shelter_inspection_flag",
                                               "joinby": "inspection_id",
                                               "key": "flag_id",
                                               },
                            )

        # ---------------------------------------------------------------------
        # Shelter Inspection <=> Flag link table
        #
        represent = ShelterInspectionRepresent(show_link=True)
        tablename = "cr_shelter_inspection_flag"
        define_table(tablename,
                     Field("inspection_id", "reference cr_shelter_inspection",
                           label = T("Shelter Inspection"),
                           ondelete = "CASCADE",
                           represent = represent,
                           requires = IS_ONE_OF(db, "cr_shelter_inspection.id",
                                                represent,
                                                ),
                           ),
                     flag_id(label = T("Defect found")),
                     Field("resolved", "boolean",
                           label = T("Resolved"),
                           default = False,
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields())

        # List fields
        list_fields = ["id",
                       "inspection_id$shelter_unit_id$name",
                       "inspection_id$date",
                       (T("Registered by"), "inspection_id$modified_by"),
                       (T("Defect"), "flag_id"),
                       "resolved",
                       ]

        # Filter widgets
        filter_widgets = [S3OptionsFilter("inspection_id$shelter_unit_id",
                                          search = 10,
                                          header = True,
                                          ),
                          S3OptionsFilter("flag_id",
                                          label = T("Defect"),
                                          options = s3_get_filter_opts("cr_shelter_flag"),
                                          ),
                          S3OptionsFilter("resolved",
                                          label = T("Resolved"),
                                          options = {False: T("No"),
                                                     True: T("Yes"),
                                                     },
                                          default = False,
                                          cols = 2,
                                          ),
                          ]

        # Table Configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  # Can not be directly inserted nor edited
                  insertable = False,
                  editable = False,
                  create_onaccept = self.shelter_inspection_flag_onaccept,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Register Defect"),
            title_display = T("Defect Details"),
            title_list = T("Defects"),
            title_update = T("Edit Defect"),
            label_list_button = T("List Defects"),
            label_delete_button = T("Delete Defect"),
            msg_record_created = T("Defect created"),
            msg_record_modified = T("Defect updated"),
            msg_record_deleted = T("Defect deleted"),
            msg_list_empty = T("No Defects currently registered"),
        )

        # ---------------------------------------------------------------------
        # Inspection Flag <=> Project Task link table
        #
        tablename = "cr_shelter_inspection_task"
        define_table(tablename,
                     Field("inspection_flag_id", "reference cr_shelter_inspection_flag",
                           label = T("Defects"),
                           ondelete = "CASCADE",
                           represent = ShelterInspectionFlagRepresent(show_link=True),
                           requires = IS_ONE_OF(db, "cr_shelter_inspection_flag.id"),
                           ),
                     self.project_task_id(ondelete = "RESTRICT",
                                          ),
                     *s3_meta_fields())

        # Table Configuration
        configure(tablename,
                  list_fields = ["id",
                                 "task_id",
                                 "inspection_flag_id",
                                 "inspection_flag_id$resolved",
                                 ],
                  ondelete_cascade = self.shelter_inspection_task_ondelete_cascade,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"cr_shelter_flag_id": flag_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"cr_shelter_flag_id":  lambda **attr: dummy("flag_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def shelter_flag_onvalidation(form):
        """
            Shelter Flag form validation:
                - if create_task=True, then task_description is required
        """

        T = current.T
        formvars = form.vars

        create_task = formvars.get("create_task")
        task_description = formvars.get("task_description")

        if create_task and not task_description:
            form.errors["task_description"] = T("Task Description required")

    # -------------------------------------------------------------------------
    @staticmethod
    def shelter_inspection_flag_onaccept(form):
        """
            Shelter inspection flag onaccept:
                - auto-create task if/as configured
        """

        settings = current.deployment_settings

        if not settings.get_cr_shelter_inspection_tasks():
            # Automatic task creation disabled
            return

        try:
            record_id = form.vars.id
        except AttributeError:
            # Nothing we can do
            return

        db = current.db
        s3db = current.s3db

        # Tables
        table = s3db.cr_shelter_inspection_flag
        ftable = s3db.cr_shelter_flag
        itable = s3db.cr_shelter_inspection
        utable = s3db.cr_shelter_unit
        ltable = s3db.cr_shelter_inspection_task
        ttable = s3db.project_task

        # Get the record
        join = (itable.on(itable.id == table.inspection_id),
                utable.on(utable.id == itable.shelter_unit_id),
                ftable.on(ftable.id == table.flag_id),
                )
        left = ltable.on(ltable.inspection_flag_id == table.id)
        query = (table.id == record_id)
        row = db(query).select(table.id,
                               table.flag_id,
                               ftable.create_task,
                               ftable.task_description,
                               ftable.task_priority,
                               ftable.task_assign_to,
                               ltable.task_id,
                               itable.shelter_unit_id,
                               utable.name,
                               join = join,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return

        create_task = False
        create_link = None

        flag = row.cr_shelter_flag
        task_description = flag.task_description
        task_priority = flag.task_priority
        task_assign_to = flag.task_assign_to

        shelter_unit = row.cr_shelter_unit.name

        if flag.create_task:

            inspection_task = row.cr_shelter_inspection_task
            if inspection_task.task_id is None:

                shelter_unit_id = row.cr_shelter_inspection.shelter_unit_id
                flag_id = row.cr_shelter_inspection_flag.flag_id

                # Do we have any active task for the same problem
                # in the same shelter unit?
                active_statuses = settings.get_cr_shelter_inspection_task_active_statuses()
                left = (itable.on(itable.id == table.inspection_id),
                        ltable.on(ltable.inspection_flag_id == table.id),
                        ttable.on(ttable.id == ltable.task_id),
                        )
                query = (table.flag_id == flag_id) & \
                        (table.deleted == False) & \
                        (ttable.name == task_description) & \
                        (ttable.status.belongs(active_statuses)) & \
                        (ttable.deleted == False) & \
                        (itable.shelter_unit_id == shelter_unit_id) & \
                        (itable.deleted == False)
                row = db(query).select(ttable.id,
                                       left = left,
                                       limitby = (0, 1),
                                       ).first()
                if row:
                    # Yes => link to this task
                    create_link = row.id
                else:
                    # No => create a new task
                    create_task = True

        if create_task:

            # Create a new task
            task = {"name": "%s: %s" % (shelter_unit, task_description),
                    "priority": task_priority,
                    "pe_id": task_assign_to,
                    }
            task_id = ttable.insert(**task)
            if task_id:
                task["id"] = task_id

                # Post-process create
                s3db.update_super(ttable, task)
                auth = current.auth
                auth.s3_set_record_owner(ttable, task_id)
                auth.s3_make_session_owner(ttable, task_id)
                s3db.onaccept(ttable, task, method="create")

                create_link = task_id

        if create_link:

            # Create the cr_shelter_inspection_task link
            ltable.insert(inspection_flag_id = record_id,
                          task_id = create_link,
                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def shelter_inspection_task_ondelete_cascade(row, tablename=None):
        """
            Ondelete-cascade method for inspection task links:
                - close the linked task if there are no other
                  unresolved flags linked to it
        """

        db = current.db
        s3db = current.s3db

        # Get the task_id
        ltable = s3db.cr_shelter_inspection_task
        query = (ltable.id == row.id)
        link = db(query).select(ltable.id,
                                ltable.task_id,
                                limitby = (0, 1),
                                ).first()
        task_id = link.task_id

        # Are there any other unresolved flags linked to the same task?
        ftable = s3db.cr_shelter_inspection_flag
        ttable = s3db.project_task
        query = (ltable.task_id == task_id) & \
                (ltable.id != link.id) & \
                (ltable.deleted != True) & \
                (ftable.id == ltable.inspection_flag_id) & \
                ((ftable.resolved == False) | (ftable.resolved == None))
        other = db(query).select(ltable.id,
                                 limitby = (0, 1)
                                 ).first()
        if not other:
            # Set task to completed status
            closed = current.deployment_settings \
                            .get_cr_shelter_inspection_task_completed_status()
            db(ttable.id == task_id).update(status = closed)

            # Remove task_id (to allow deletion of the link)
            link.update_record(task_id = None)

# =============================================================================
class CRShelterRegistrationModel(S3Model):

    names = ("cr_shelter_allocation",
             "cr_shelter_registration",
             "cr_shelter_registration_history",
             "cr_shelter_registration_status_opts",
             "cr_shelter_population_onaccept",
             )

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table
        settings = current.deployment_settings

        shelter_id = self.cr_shelter_id
        person_id = self.pr_person_id

        day_and_night = settings.get_cr_day_and_night()

        # ---------------------------------------------------------------------
        # Shelter Allocation: table to allocate shelter capacity to a group
        #
        allocation_status_opts = {1: T("requested"),
                                  2: T("available"),
                                  3: T("allocated"),
                                  4: T("occupied"),
                                  5: T("departed"),
                                  6: T("obsolete"),
                                  7: T("unavailable"),
                                  }

        tablename = "cr_shelter_allocation"
        define_table(tablename,
                     shelter_id(empty = False,
                                ondelete = "CASCADE",
                                ),
                     self.pr_group_id(comment = None),
                     Field("status", "integer",
                           default = 3,
                           label = T("Status"),
                           requires = IS_IN_SET(allocation_status_opts),
                           represent = S3Represent(options = allocation_status_opts),
                           ),
                     Field("group_size_day", "integer",
                           default = 0,
                           label = T("Group Size (Day)") if day_and_night else T("Group Size"),
                           ),
                     Field("group_size_night", "integer",
                           default = 0,
                           label = T("Group Size (Night)"),
                           readable = day_and_night,
                           writable = day_and_night,
                           ),
                     *s3_meta_fields())

        population_onaccept = lambda form: \
                                self.cr_shelter_population_onaccept(
                                    form,
                                    tablename="cr_shelter_allocation",
                                    )

        configure(tablename,
                  onaccept = population_onaccept,
                  ondelete = population_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Shelter Registration: table to register a person to a shelter
        #
        cr_day_or_night_opts = {NIGHT: T("Night only"),
                                DAY_AND_NIGHT: T("Day and Night")
                                }

        # Registration status
        reg_status_opts = {1: T("Planned"),
                           2: T("Checked-in"),
                           3: T("Checked-out"),
                           }

        reg_status = S3ReusableField("registration_status", "integer",
                                     label = T("Status"),
                                     represent = S3Represent(
                                                    options=reg_status_opts,
                                                    ),
                                     requires = IS_IN_SET(reg_status_opts,
                                                          zero=None
                                                          ),
                                     )

        housing_unit = settings.get_cr_shelter_housing_unit_management()

        tablename = "cr_shelter_registration"
        define_table(tablename,
                     # @ToDo: Convert to site_id? (More flexible & easier to default, etc)
                     shelter_id(empty = False,
                                ondelete = "CASCADE",
                                ),
                     # The comment explains how to register a new person
                     # it should not be done in a popup
                     person_id(
                         comment = DIV(_class="tooltip",
                                       _title="%s|%s" % (T("Person"),
                                                         #  @ToDo: Generalise (this is EVASS-specific)
                                                         T("Type the name of a registered person \
                                                           or to add an unregistered person to this \
                                                           shelter click on Evacuees")
                                                         )
                                       ),
                         ),
                     self.cr_shelter_unit_id(readable = housing_unit,
                                             writable = housing_unit,
                                             ),
                     Field("day_or_night", "integer",
                           default = DAY_AND_NIGHT,
                           label = T("Presence in the shelter"),
                           represent = S3Represent(options=cr_day_or_night_opts
                                                   ),
                           requires = IS_IN_SET(cr_day_or_night_opts,
                                                zero=None
                                                ),
                           readable = day_and_night,
                           writable = day_and_night,
                           ),
                     reg_status(),
                     s3_datetime("check_in_date",
                                 label = T("Check-in date"),
                                 default = "now",
                                 #empty = False,
                                 future = 0,
                                 ),
                     s3_datetime("check_out_date",
                                 label = T("Check-out date"),
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        registration_onaccept = self.cr_shelter_registration_onaccept
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "shelter_id",
                                                       "shelter_unit_id",
                                                       ),
                                            ),
                  onaccept = registration_onaccept,
                  ondelete = registration_onaccept,
                  )

        if housing_unit:
            configure(tablename,
                      onvalidation = self.cr_shelter_registration_onvalidation,
                      )

        # Custom Methods
        self.set_method("cr", "shelter_registration",
                        method = "assign",
                        action = cr_AssignUnit())

        # ---------------------------------------------------------------------
        # Shelter Registration History: history of status changes
        #
        tablename = "cr_shelter_registration_history"
        define_table(tablename,
                     person_id(),
                     self.cr_shelter_id(),
                     s3_datetime(default = "now",
                                 ),
                     reg_status("previous_status",
                                label = T("Old Status"),
                                ),
                     reg_status("status",
                                label = T("New Status"),
                                ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["shelter_id",
                                 "date",
                                 (T("Status"), "status"),
                                 (T("Modified by"), "modified_by"),
                                 ],
                  insertable = False,
                  editable = False,
                  deletable = False,
                  orderby = "%s.date desc" % tablename,
                  )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return {"cr_shelter_population_onaccept": self.cr_shelter_population_onaccept,
                "cr_shelter_registration_status_opts": reg_status_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_registration_onvalidation(form):
        """
            Check if the housing unit belongs to the requested shelter
        """

        request = current.request
        controller = request.controller
        if controller == "dvr":
            # Housing Unit is not mandatory during Case Registration
            return

        unit_id = None
        shelter_id = None

        if type(form) is Row:
            form_vars = form
        else:
            form_vars = form.vars

        if controller == "cr":
            # Registration form doesn't include the Shelter
            # @ToDo: don't assume that we are running as component of the shelter
            shelter_id = form_vars.shelter_id or (form.record and form.record.shelter_id) or request.args[0]
            unit_id = form_vars.shelter_unit_id

        if unit_id is None:
            current.response.warning = current.T("Warning: No housing unit selected")
        else:
            db = current.db
            htable = db.cr_shelter_unit
            record = db(htable.id == unit_id).select(htable.shelter_id,
                                                     limitby=(0, 1)).first()

            if str(record.shelter_id) != str(shelter_id):
                error = current.T("You have to select a housing unit belonging to the shelter")
                form.errors["branch_id"] = error
                current.response.error = error

    # -------------------------------------------------------------------------
    @classmethod
    def cr_shelter_registration_onaccept(cls, form):
        """
            Registration onaccept: track status changes, update
            shelter population

            @param form: the FORM (also accepts Row)
        """

        try:
            if type(form) is Row:
                formvars = form
            else:
                formvars = form.vars
            registration_id = formvars.id
        except AttributeError:
            unit_id = None
        else:
            unit_id = formvars.get("shelter_unit_id")

            if registration_id:

                s3db = current.s3db
                db = current.db

                # Get the current status
                rtable = s3db.cr_shelter_registration
                query = (rtable.id == registration_id) & \
                        (rtable.deleted != True)
                reg = db(query).select(rtable.id,
                                       rtable.shelter_id,
                                       rtable.shelter_unit_id,
                                       rtable.registration_status,
                                       rtable.check_in_date,
                                       rtable.check_out_date,
                                       rtable.modified_on,
                                       rtable.person_id,
                                       limitby = (0, 1)
                                       ).first()

                if reg:
                    person_id = reg.person_id

                    # Unit to check availability for
                    unit_id = reg.shelter_unit_id

                    # Get the previous status
                    htable = s3db.cr_shelter_registration_history
                    query = (htable.person_id == person_id) & \
                            (htable.shelter_id == reg.shelter_id) & \
                            (htable.deleted != True)
                    row = db(query).select(htable.status,
                                           htable.date,
                                           orderby = ~htable.created_on,
                                           limitby = (0, 1)
                                           ).first()
                    if row:
                        previous_status = row.status
                        previous_date = row.date
                    else:
                        previous_status = None
                        previous_date = None

                    # Get the current status
                    current_status = reg.registration_status

                    # Get the effective date
                    if current_status == 2:
                        effective_date_field = "check_in_date"
                    elif current_status == 3:
                        effective_date_field = "check_out_date"
                    else:
                        effective_date_field = None

                    if effective_date_field:
                        # Read from registration
                        effective_date = reg[effective_date_field]
                    else:
                        # Use modified_on for history
                        effective_date = reg.modified_on

                    if current_status != previous_status or \
                       effective_date_field and not effective_date:

                        if effective_date_field:
                            # If the new status has an effective date,
                            # make sure it gets updated when the status
                            # has changed:
                            if effective_date_field not in formvars or \
                               not effective_date or \
                               previous_date and effective_date < previous_date:

                                effective_date = current.request.utcnow
                                reg.update_record(**{
                                    effective_date_field: effective_date,
                                    })

                        # Insert new history entry
                        htable.insert(previous_status = previous_status,
                                      status = current_status,
                                      date = effective_date,
                                      person_id = person_id,
                                      shelter_id = reg.shelter_id,
                                      )

                        # Update last_seen_on
                        if current.deployment_settings.has_module("dvr"):
                            s3db.dvr_update_last_seen(person_id)

        # Update population
        cls.cr_shelter_population_onaccept(form,
                                           tablename = "cr_shelter_registration",
                                           unit_id = unit_id,
                                           )

    # -------------------------------------------------------------------------
    @staticmethod
    def cr_shelter_population_onaccept(form, tablename=None, unit_id=None):
        """
            Update the shelter population, onaccept

            @param form: the FORM
            @param tablename: the table name
            @param unit_id: the shelter unit ID (to warn if full)
        """

        db = current.db
        s3db = current.s3db

        if not tablename:
            return
        table = s3db[tablename]

        try:
            if type(form) is Row:
                record_id = form.id
            else:
                record_id = form.vars.id
        except AttributeError:
            # Nothing we can do
            return

        if tablename == "cr_shelter_unit":
            unit_id = record_id

        # Get the record
        row = db(table._id == record_id).select(table._id,
                                                table.shelter_id,
                                                table.deleted,
                                                table.deleted_fk,
                                                limitby = (0, 1)
                                                ).first()

        if row:
            if row.deleted:
                if row.deleted_fk:
                    deleted_fk = json.loads(row.deleted_fk)
                else:
                    return
                shelter_id = deleted_fk.get("shelter_id")
            else:
                shelter_id = row.shelter_id

            if shelter_id:

                if current.deployment_settings.get_cr_shelter_housing_unit_management():
                    # First update housing units census
                    cr_update_capacity_from_housing_units(shelter_id)

                # Shelter census
                cr_update_shelter_population(shelter_id)

                # Warn if unit is full
                if unit_id:
                    cr_check_population_availability(unit_id,
                                                     table = s3db.cr_shelter_unit,
                                                     )

                # Warn if shelter is full
                cr_check_population_availability(shelter_id,
                                                 table = s3db.cr_shelter,
                                                 )

# =============================================================================
def cr_shelter_rheader(r, tabs=None):
    """ Resource Headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    rheader = None
    tablename, record = s3_rheader_resource(r)
    if tablename == "cr_shelter" and record:
        T = current.T
        s3db = current.s3db
        if not tabs:
            settings = current.deployment_settings
            tabs = [(T("Basic Details"), None),
                    (T("Status Reports"), "status"),
                    ]
            if settings.get_L10n_translate_org_site():
                tabs.append((T("Local Names"), "name"))
            if settings.get_cr_tags():
                tabs.append((T("Tags"), "tag"))
            if settings.get_cr_shelter_people_registration():
                tabs.extend([(T("Client Reservation"), "shelter_allocation"),
                             (T("Client Registration"), "shelter_registration"),
                             ])
            if settings.has_module("hrm"):
                STAFF = settings.get_hrm_staff_label()
                tabs.append((STAFF, "human_resource"))
                permit = current.auth.s3_has_permission
                if permit("update", tablename, r.id) and \
                   permit("create", "hrm_human_resource_site"):
                    tabs.append((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))
            if settings.get_cr_shelter_housing_unit_management():
                tabs.append((T("Housing Units"), "shelter_unit"))
            #tabs.append((T("Events"), "event_shelter"))
            #if settings.has_module("assess"):
            #    tabs.append((T("Assessments"), "rat"))

            try:
                tabs = tabs + s3db.req_tabs(r, match=False)
            except:
                pass
            try:
                tabs = tabs + s3db.inv_tabs(r)
            except:
                pass
            tabs.append((T("Assets"), "asset"))
            if settings.has_module("msg"):
                tabs.append((T("Send Notification"), "dispatch"))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if r.name == "shelter":
            location = r.table.location_id.represent(record.location_id)

            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")), record.name
                                   ),
                                TR(TH("%s: " % T("Location")), location
                                   ),
                                ),
                          rheader_tabs)
        else:
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name")), record.name
                                   ),
                                ),
                          rheader_tabs)

    return rheader

# =============================================================================
def cr_update_housing_unit_population(shelter_id):
    """
        Update housing unit population number.
        To be called onaccept/ondelete of cr_shelter_registration and
        cr_shelter_allocation.

        @param shelter_id: the Shelter ID
    """

    db = current.db
    settings = current.deployment_settings

    htable = db.cr_shelter_unit
    rtable = db.cr_shelter_registration

    rjoin = (htable.id == rtable.shelter_unit_id) & \
            (rtable.deleted != True)

    check_out_is_final = settings.get_cr_check_out_is_final()
    if check_out_is_final:
        rtable &= (rtable.registration_status != 3)

    query = (htable.shelter_id == shelter_id) & \
            (htable.status == 1) & \
            (htable.deleted != True)

    rcount = rtable.id.count()

    day_and_night = settings.get_cr_day_and_night()
    if day_and_night:

        for daytime in (True, False):

            if daytime:
                fn_capacity = "capacity_day"
                fn_population = "population_day"
                fn_available_capacity = "available_capacity_day"
                left = rtable.on(rjoin & (rtable.day_or_night == DAY_AND_NIGHT))
            else:
                fn_capacity = "capacity_night"
                fn_population = "population_night"
                fn_available_capacity = "available_capacity_night"
                left = rtable.on(rjoin)

            rows = db(query).select(htable.id,
                                    htable[fn_capacity],
                                    htable[fn_population],
                                    htable[fn_available_capacity],
                                    rtable.id.count(),
                                    groupby = htable.id,
                                    left = left,
                                    )

            for row in rows:

                data = {}

                unit = row[str(htable)]
                population = row[rcount]

                # Update population
                current_population = unit[fn_population]
                if current_population != population:
                    data[fn_population] = population

                # Update daytime capacity
                capacity = unit[fn_capacity]
                if capacity > 0:
                    available_capacity = capacity - population
                else:
                    available_capacity = 0
                if unit[fn_available_capacity] != available_capacity:
                    data[fn_available_capacity] = available_capacity

                # Write only if data have changed
                if data:
                    db(htable.id == unit.id).update(**data)

    else:
        left = rtable.on(rjoin)
        rows = db(query).select(htable.id,
                                htable.capacity_day,
                                htable.capacity_night,
                                htable.population_day,
                                htable.population_night,
                                htable.available_capacity_day,
                                htable.available_capacity_night,
                                rcount,
                                groupby = htable.id,
                                left = left,
                                )

        for row in rows:

            data = {}

            unit = row[str(htable)]
            population = row[rcount]

            # Update daytime population/capacity
            current_population = unit.population_day
            if current_population != population:
                data["population_day"] = population
            capacity = unit.capacity_day
            if capacity > 0:
                available_capacity = capacity - population
            else:
                available_capacity = 0
            if unit.available_capacity_day != available_capacity:
                data["available_capacity_day"] = available_capacity

            # Update daytime population/capacity
            current_population = unit.population_night
            if current_population != population:
                data["population_night"] = population
            capacity = unit.capacity_night
            if capacity > 0:
                available_capacity = capacity - population
            else:
                available_capacity = 0
            if unit.available_capacity_night != available_capacity:
                data["available_capacity_night"] = available_capacity

            # Write only if data have changed
            if data:
                unit_id = unit.id
                db(htable.id == unit_id).update(**data)

# =============================================================================
def cr_update_shelter_population(shelter_id):
    """
        Update population and available capacity numbers, to be
        called onaccept/ondelete of cr_shelter_registration and
        cr_shelter_allocation.

        @param shelter_id: the shelter record ID
    """

    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings

    stable = s3db.cr_shelter

    # Get the shelter record
    record = db(stable._id == shelter_id).select(stable.id,
                                                 stable.capacity_day,
                                                 stable.capacity_night,
                                                 limitby=(0, 1)).first()

    # Get population numbers
    rtable = s3db.cr_shelter_registration
    query = (rtable.shelter_id == shelter_id) & \
            (rtable.deleted != True)
    if settings.get_cr_check_out_is_final():
        query &= (rtable.registration_status != 3)

    cnt = rtable._id.count()
    rows = db(query).select(rtable.day_or_night,
                            cnt,
                            groupby=rtable.day_or_night,
                            orderby=rtable.day_or_night)

    population_day = population_night = 0
    for row in rows:
        reg_type = row[rtable.day_or_night]
        number = row[cnt]
        if reg_type == NIGHT and number:
            population_night = number
        elif reg_type == DAY_AND_NIGHT and number:
            population_day = number
    # population_day is both day /and/ night
    population_night += population_day

    # Get allocation numbers
    # @ToDo: deployment_setting to disable Allocations
    atable = s3db.cr_shelter_allocation
    query = (atable.shelter_id == shelter_id) & \
            (atable.status.belongs((1, 2, 3, 4))) & \
            (atable.deleted != True)
    dcnt = atable.group_size_day.sum()
    ncnt = atable.group_size_night.sum()
    row = db(query).select(dcnt, ncnt, limitby=(0, 1), orderby=dcnt).first()
    if row:
        if row[dcnt] is not None:
            allocated_capacity_day = row[dcnt]
        else:
            allocated_capacity_day = 0
        if row[ncnt] is not None:
            allocated_capacity_night = row[ncnt]
        else:
            allocated_capacity_night = 0
    else:
        allocated_capacity_day = allocated_capacity_night = 0

    # Compute available capacity
    capacity_day = record.capacity_day
    if capacity_day:
        available_capacity_day = capacity_day - \
                                 population_day - \
                                 allocated_capacity_day
    else:
        available_capacity_day = 0
    capacity_night = record.capacity_night
    if capacity_night:
        available_capacity_night = record.capacity_night - \
                                   population_night - \
                                   allocated_capacity_night
    else:
        available_capacity_night = 0

    if settings.get_cr_shelter_housing_unit_management():
        cr_update_housing_unit_population(shelter_id)

    # Update record
    record.update_record(population_day=population_day,
                         population_night=population_night,
                         available_capacity_day=available_capacity_day,
                         available_capacity_night=available_capacity_night)

# =============================================================================
def cr_check_population_availability(unit_id, table):
    """
        Evaluate the population capacity availability.
        Show a non blocking warning in case the people in the shelter/housing unit are more than its capacity

        @param unit_id: the shelter ID / housing unit ID
        @param table: related tablename (cr_shelter or cr_shelter_housing_unit)
    """

    T = current.T
    db = current.db
    response = current.response

    record = db(table.id == unit_id).select(table.capacity_day,
                                            table.population_day,
                                            table.capacity_night,
                                            table.population_night,
                                            limitby=(0, 1)
                                            ).first()

    day_and_night = current.deployment_settings.get_cr_day_and_night()

    warning = None
    full_day = full_night = False

    capacity_day = record.capacity_day
    population_day = record.population_day
    if capacity_day is not None and \
       population_day and \
       population_day >= capacity_day:
        full_day = True

    if day_and_night:
        capacity_night = record.capacity_night
        population_night = record.population_night
        if capacity_night is not None and \
           population_night and \
           population_night >= capacity_night:
            full_night = True

    tablename = table._tablename
    if not day_and_night and full_day or full_day and full_night:
        if tablename == "cr_shelter":
            warning = T("Warning: this shelter is full")
        elif tablename == "cr_shelter_unit":
            warning = T("Warning: this housing unit is full")
    elif full_day:
        if tablename == "cr_shelter":
            warning = T("Warning: this shelter is full for daytime")
        elif tablename == "cr_shelter_unit":
            warning = T("Warning: this housing unit is full for daytime")
    elif full_night:
        if tablename == "cr_shelter":
            warning = T("Warning: this shelter is full for the night")
        elif tablename == "cr_shelter_unit":
            warning = T("Warning: this housing unit is full for the night")

    if warning:
        response = current.response
        response_warning = response.warning
        if response_warning:
            response.warning = "%s - %s" % (response_warning, warning)
        else:
            response.warning = warning

# =============================================================================
def cr_update_capacity_from_housing_units(shelter_id):
    """
        Update shelter capacity numbers, new capacity numbers are evaluated
        adding together all housing unit capacities.
        To be called onaccept/ondelete of cr_shelter_registration and
        cr_shelter_allocation.

        @param shelter_id: the shelter record ID
    """

    db = current.db

    stable = db.cr_shelter
    htable = db.cr_shelter_unit

    query = (htable.shelter_id == shelter_id) & \
            (htable.status == 1) & \
            (htable.deleted != True)

    total_capacity_day = htable.capacity_day.sum()
    total_capacity_night = htable.capacity_night.sum()
    row = db(query).select(total_capacity_day,
                           total_capacity_night,
                           ).first()

    if row:
        total_capacity_day = row[total_capacity_day]
        total_capacity_night = row[total_capacity_night]
    else:
        total_capacity_day = total_capacity_night = 0

    db(stable._id==shelter_id).update(capacity_day = total_capacity_day,
                                      capacity_night = total_capacity_night,
                                      )

# =============================================================================
def cr_notification_dispatcher(r, **attr):
    """
        Send a notification.
    """

    if r.representation == "html" and \
        r.name == "shelter" and r.id and not r.component:

        T = current.T
        msg = current.msg
        record = r.record

        message = ""
        text = ""

        s_id = record.id
        s_name = record.name
        s_phone = record.phone
        s_email = record.email
        s_status = record.status

        if s_phone in ("", None):
            s_phone = T("Not Defined")
        if s_email in ("", None):
            s_phone = T("Not Defined")
        if s_status in ("", None):
            s_status = T("Not Defined")
        else:
            if s_status == 1:
                s_status = "Open"
            elif s_status == 2:
                s_status = "Close"
            else:
                s_status = "Unassigned Shelter Status"

        text += "************************************************"
        text += "\n%s " % T("Automatic Message")
        text += "\n%s: %s " % (T("Shelter ID"), s_id)
        text += " %s: %s" % (T("Shelter name"), s_name)
        text += "\n%s: %s " % (T("Email"), s_email)
        text += " %s: %s" % (T("Phone"), s_phone)
        text += "\n%s: %s " % (T("Working Status"), s_status)
        text += "\n************************************************\n"

        # Encode the message as an OpenGeoSMS
        #message = msg.prepare_opengeosms(record.location_id,
        #                                 code="ST",
        #                                 map="google",
        #                                 text=text)

        # URL to redirect to after message sent
        url = URL(c="cr", f="shelter", args=r.id)

        # Create the form
        opts = {"type": "SMS",
                # @ToDo: deployment_setting
                "subject": T("Deployment Request"),
                "message": message + text,
                "url": url,
                }

        output = msg.compose(**opts)

        # Maintain RHeader for consistency
        if attr.get("rheader"):
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        output["title"] = T("Send Notification")
        current.response.view = "msg/compose.html"
        return output

    else:
        r.error(405, current.messages.BAD_METHOD)

# =============================================================================
class cr_AssignUnit(S3CRUD):
    """
        Assign a Person to a Housing Unit
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        try:
            person_id = int(r.get_vars["person_id"])
        except (AttributeError, ValueError, TypeError):
            r.error(400, current.messages.BAD_REQUEST)

        self.settings = current.response.s3.crud
        sqlform = self._config("crud_form")
        self.sqlform = sqlform if sqlform else S3SQLDefaultForm()
        self.data = None

        # Create or Update?
        table = current.s3db.cr_shelter_registration
        query = (table.deleted == False) & \
                (table.person_id == person_id)
        exists = current.db(query).select(table.id,
                                          limitby=(0, 1)
                                          ).first()
        if exists:
            # Update form
            r.method = "update" # Ensure correct View template is used
            self.record_id = exists.id
            output = self.update(r, **attr)
        else:
            # Create form
            r.method = "create" # Ensure correct View template is used
            self.data = {"person_id": person_id}
            output = self.create(r, **attr)

        return output

# =============================================================================
class ShelterInspectionFlagRepresent(S3Represent):
    """ Representations of Shelter Inspection Flags """

    def __init__(self, show_link=False):
        """
            Constructor

            @param show_link: represent as link to the shelter inspection
        """

        super(ShelterInspectionFlagRepresent, self).__init__(
                                       lookup="cr_shelter_inspection_flag",
                                       show_link=show_link,
                                       )

    # ---------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Link inspection flag representations to the inspection record

            @param k: the inspection flag ID
            @param v: the representation
            @param row: the row from lookup_rows
        """

        if row:
            inspection_id = row.cr_shelter_inspection.id
            if inspection_id:
                return A(v, _href=URL(c="cr",
                                      f="shelter_inspection",
                                      args=[inspection_id],
                                      ),
                         )
        return v

    # ---------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a Row

            @param row: the Row
        """

        details = {"unit": row.cr_shelter_unit.name,
                   "date": row.cr_shelter_inspection.date,
                   "flag": row.cr_shelter_flag.name,
                   }

        return "%(unit)s (%(date)s): %(flag)s" % details

    # ---------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        s3db = current.s3db

        table = self.table
        ftable = s3db.cr_shelter_flag
        itable = s3db.cr_shelter_inspection
        utable = s3db.cr_shelter_unit

        left = (ftable.on(ftable.id == table.flag_id),
                itable.on(itable.id == table.inspection_id),
                utable.on(utable.id == itable.shelter_unit_id),
                )
        count = len(values)
        if count == 1:
            query = (table.id == values[0])
        else:
            query = (table.id.belongs(values))
        limitby = (0, count)

        rows = current.db(query).select(table.id,
                                        utable.name,
                                        itable.id,
                                        itable.date,
                                        ftable.name,
                                        left = left,
                                        limitby = limitby,
                                        )
        return rows

# =============================================================================
class ShelterInspectionRepresent(S3Represent):
    """ Representations of Shelter Inspections """

    def __init__(self, show_link=False):
        """
            Constructor

            @param show_link: represent as link to the shelter inspection
        """

        super(ShelterInspectionRepresent, self).__init__(
                                       lookup="cr_shelter_inspection",
                                       show_link=show_link,
                                       )

    # ---------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Link inspection flag representations to the inspection record

            @param k: the inspection flag ID
            @param v: the representation
            @param row: the row from lookup_rows
        """

        if row:
            inspection_id = row.cr_shelter_inspection.id
            if inspection_id:
                return A(v, _href=URL(c="cr",
                                      f="shelter_inspection",
                                      args=[inspection_id],
                                      ),
                         )
        return v

    # ---------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a Row

            @param row: the Row
        """

        details = {"unit": row.cr_shelter_unit.name,
                   "date": row.cr_shelter_inspection.date,
                   }

        return "%(date)s: %(unit)s" % details

    # ---------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        s3db = current.s3db

        table = self.table

        utable = s3db.cr_shelter_unit
        left = utable.on(utable.id == table.shelter_unit_id)

        count = len(values)
        if count == 1:
            query = (table.id == values[0])
        else:
            query = (table.id.belongs(values))
        limitby = (0, count)

        rows = current.db(query).select(table.id,
                                        table.date,
                                        utable.name,
                                        left = left,
                                        limitby = limitby,
                                        )
        return rows

# =============================================================================
class CRShelterInspection(S3Method):
    """
        Mobile-optimized UI for shelter inspection
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Main entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        if not self.permitted():
            current.auth.permission.fail()

        output = {}
        representation = r.representation

        if representation == "html":
            if r.http in ("GET", "POST"):
                output = self.inspection_form(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif representation == "json":
            if r.http == "POST":
                output = self.inspection_ajax(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def permitted(self):
        """
            @todo: docstring
        """

        # @todo: implement
        return True

    # -------------------------------------------------------------------------
    def inspection_form(self, r, **attr):
        """
            Generate the form

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings
        response = current.response

        output = {}

        # Limit selection of shelter units to current shelter
        record = r.record
        if record:
            utable = s3db.cr_shelter_unit
            dbset = db(utable.shelter_id == record.id)
        else:
            dbset = db

        # Representation methods for form widgets
        shelter_unit_represent = S3Represent(lookup="cr_shelter_unit")
        shelter_flag_represent = S3Represent(lookup="cr_shelter_flag",
                                             translate=True,
                                             )

        # Standard form fields and data
        formfields = [Field("shelter_unit_id",
                            label = T("Housing Unit"),
                            requires = IS_ONE_OF(dbset, "cr_shelter_unit.id",
                                                 shelter_unit_represent,
                                                 orderby = "shelter_id",
                                                 ),
                            widget = S3MultiSelectWidget(multiple = False,
                                                         search = True,
                                                         ),
                            ),
                      Field("shelter_flags",
                            label = T("Defects"),
                            requires = IS_ONE_OF(db, "cr_shelter_flag.id",
                                                 shelter_flag_represent,
                                                 multiple = True,
                                                 ),
                            widget = S3GroupedOptionsWidget(
                                        cols = 2,
                                        size = None,
                                        ),
                            ),
                      s3_comments(comment=None),
                      ]

        # Buttons
        submit_btn = INPUT(_class = "tiny primary button submit-btn",
                           _name = "submit",
                           _type = "button",
                           _value = T("Submit"),
                           )

        buttons = [submit_btn]

        # Add the cancel-action
        buttons.append(A(T("Cancel"), _class = "cancel-action action-lnk"))

        # Generate form
        widget_id = "shelter-inspection-form"
        formstyle = settings.get_ui_formstyle()
        form = SQLFORM.factory(record = None,
                               showid = False,
                               formstyle = formstyle,
                               table_name = "shelter_inspection",
                               buttons = buttons,
                               #hidden = hidden,
                               _id = widget_id,
                               *formfields)

        output["form"] = form

        # Custom view
        response.view = self._view(r, "cr/shelter_inspection.html")

        # Inject JS
        options = {"ajaxURL": r.url(None,
                                    method = "inspection",
                                    representation = "json",
                                    ),
                   }
        self.inject_js(widget_id, options)

        return output

    # -------------------------------------------------------------------------
    def inspection_ajax(self, r, **attr):
        """
            Ajax-registration of shelter inspection

            @param r: the S3Request instance
            @param attr: controller parameters
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        # Load JSON data from request body
        s = r.body
        s.seek(0)
        try:
            data = json.load(s)
        except (ValueError, TypeError):
            r.error(400, current.ERROR.BAD_REQUEST)

        shelter_unit_id = data.get("u")
        if shelter_unit_id:
            # Register shelter inspection
            error = False

            # Read comments
            comments = data.get("c")

            # Find inspection record
            update = False
            itable = s3db.cr_shelter_inspection
            query = (itable.shelter_unit_id == shelter_unit_id) & \
                    (itable.date == current.request.utcnow.date()) & \
                    (itable.deleted != True)
            row = db(query).select(itable.id,
                                   limitby = (0, 1),
                                   ).first()
            if row:
                # Update this inspection
                update = True
                inspection_id = row.id
                row.update_record(comments = comments)
            else:
                # Create a new inspection
                inspection_id = itable.insert(shelter_unit_id = shelter_unit_id,
                                              comments = comments,
                                              )
            if inspection_id:
                # Currently selected flags
                flag_ids = data.get("f")

                if update:
                    # Remove all flags linked to the current inspection
                    # which are not in the current selection
                    query = (FS("inspection_id") == inspection_id)
                    if flag_ids:
                        query &= ~(FS("flag_id").belongs(flag_ids))
                    fresource = s3db.resource("cr_shelter_inspection_flag",
                                              filter = query,
                                              )
                    fresource.delete(cascade=True)

                if flag_ids:

                    # Determine which flags have been newly selected
                    ftable = s3db.cr_shelter_inspection_flag
                    if update:
                        query = (ftable.inspection_id == inspection_id) & \
                                (ftable.deleted == False)
                        rows = db(query).select(ftable.flag_id)
                        new = set(flag_ids) - set(row.flag_id for row in rows)
                    else:
                        new = set(flag_ids)

                    # Create links to newly selected flags
                    ftable = s3db.cr_shelter_inspection_flag
                    data = {"inspection_id": inspection_id,
                            }
                    for flag_id in new:
                        data["flag_id"] = flag_id
                        success = ftable.insert(**data)
                        if not success:
                            error = True
                            break
                        else:
                            # Call onaccept to auto-create tasks
                            record = Storage(data)
                            record["id"] = success
                            s3db.onaccept(ftable, record)
            else:
                error = True

            if error:
                db.rollback()
                output = {"a": s3_str(T("Error registering shelter inspection")),
                          }
            else:
                output = {"m": s3_str(T("Registration successful")),
                          }
        else:
            # Error - no shelter unit selected
            output = {"a": s3_str(T("No shelter unit selected")),
                      }

        return json.dumps(output)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_js(widget_id, options):
        """
            Helper function to inject static JS and instantiate
            the shelterInspection widget

            @param widget_id: the node ID where to instantiate the widget
            @param options: dict of widget options (JSON-serializable)
        """

        s3 = current.response.s3
        appname = current.request.application

        # Static JS
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.shelter_inspection.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.shelter_inspection.min.js" % appname
        scripts.append(script)

        # Instantiate widget
        scripts = s3.jquery_ready
        script = '''$('#%(id)s').shelterInspection(%(options)s)''' % \
                 {"id": widget_id, "options": json.dumps(options)}
        if script not in scripts:
            scripts.append(script)

# -------------------------------------------------------------------------
def cr_resolve_shelter_flags(task_id):
    """
        If a task is set to an inactive status, then mark all linked
        shelter inspection flags as resolved

        @param task_id: the task record ID
    """

    db = current.db
    s3db = current.s3db

    active_statuses = current.deployment_settings \
                             .get_cr_shelter_inspection_task_active_statuses()

    # Get the task
    ttable = s3db.project_task
    query = (ttable.id == task_id)
    task = db(query).select(ttable.id,
                            ttable.status,
                            limitby = (0, 1),
                            ).first()

    if task and task.status not in active_statuses:

        # Mark all shelter inspection flags as resolved
        ltable = s3db.cr_shelter_inspection_task
        ftable = s3db.cr_shelter_inspection_flag
        query = (ltable.task_id == task.id) & \
                (ftable.id == ltable.inspection_flag_id) & \
                ((ftable.resolved == False) | (ftable.resolved == None))
        rows = db(query).select(ftable.id)
        ids = set(row.id for row in rows)
        db(ftable.id.belongs(ids)).update(resolved=True)

# END =========================================================================
