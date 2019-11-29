# -*- coding: utf-8 -*-

""" Sahana Eden Organisation Model

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("S3OrganisationModel",
           "S3OrganisationNameModel",
           "S3OrganisationBranchModel",
           "S3OrganisationCapacityModel",
           "S3OrganisationGroupModel",
           "S3OrganisationGroupPersonModel",
           "S3OrganisationGroupTeamModel",
           "S3OrganisationLocationModel",
           "S3OrganisationOrganisationModel",
           "S3OrganisationResourceModel",
           "S3OrganisationSectorModel",
           "S3OrganisationServiceModel",
           "S3OrganisationTagModel",
           "S3OrganisationTeamModel",
           "S3OrganisationTypeTagModel",
           "S3SiteModel",
           "S3SiteDetailsModel",
           "S3SiteNameModel",
           "S3SiteShiftModel",
           "S3SiteTagModel",
           "S3SiteLocationModel",
           "S3FacilityModel",
           "org_facility_rheader",
           "S3RoomModel",
           "S3OfficeModel",
           "S3OfficeTypeTagModel",
           "org_organisation_logo",
           "org_organisation_address",
           "org_parents",
           "org_root_organisation",
           "org_root_organisation_name",
           "org_organisation_requires",
           "org_region_options",
           "org_rheader",
           "org_site_staff_config",
           "org_organisation_controller",
           "org_office_controller",
           "org_facility_controller",
           "org_update_affiliations",
           "org_OrganisationRepresent",
           "org_SiteRepresent",
           "org_SiteCheckInMethod",
           #"org_AssignMethod",
           #"org_CapacityReport",
           "org_logo_represent",
           "org_customise_org_resource_fields",
           "org_organisation_list_layout",
           "org_resource_list_layout",
           "org_update_root_organisation",
           )

import json

from gluon import *

from ..s3 import *
from s3compat import StringIO
from s3dal import Row
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3OrganisationModel(S3Model):
    """
        Organisations
    """

    names = ("org_organisation_type",
             "org_organisation_type_id",
             "org_region",
             "org_region_country",
             "org_region_id",
             "org_region_represent",
             "org_organisation",
             "org_organisation_crud_fields",
             "org_organisation_id",
             "org_organisation_organisation_type",
             "org_organisation_user",
             "org_organisation_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis
        messages = current.messages
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        NONE = messages["NONE"]

        hierarchical_organisation_types = settings.get_org_organisation_types_hierarchical()
        multiple_organisation_types = settings.get_org_organisation_types_multiple()

        use_country = settings.get_org_country()

        # ---------------------------------------------------------------------
        # Organisation Types
        #
        tablename = "org_organisation_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("parent", "reference org_organisation_type", # This form of hierarchy may not work on all Databases
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_organisation_types,
                           writable = hierarchical_organisation_types,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename, translate=True)

        if hierarchical_organisation_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_organisation_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="org_organisation_type.name"))
            organisation_type_widget = S3HierarchyWidget(lookup = "org_organisation_type",
                                                         represent = type_represent,
                                                         multiple = multiple_organisation_types,
                                                         #leafonly = True,
                                                         )
            type_filter = S3HierarchyFilter("organisation_organisation_type.organisation_type_id",
                                            label = T("Type"),
                                            #multiple = multiple_organisation_types,
                                            )
            type_widget = "hierarchy"
        else:
            hierarchy = None
            organisation_type_widget = None
            type_filter = S3OptionsFilter("organisation_organisation_type.organisation_type_id",
                                          label = T("Type"),
                                          #multiple = multiple_organisation_types,
                                          )
            type_widget = "multiselect"

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Organization Type"),
            title_display = T("Organization Type Details"),
            title_list = T("Organization Types"),
            title_update = T("Edit Organization Type"),
            label_list_button = T("List Organization Types"),
            label_delete_button = T("Delete Organization Type"),
            msg_record_created = T("Organization Type added"),
            msg_record_modified = T("Organization Type updated"),
            msg_record_deleted = T("Organization Type deleted"),
            msg_list_empty = T("No Organization Types currently registered"))

        organisation_type_id = S3ReusableField("organisation_type_id",
            "reference %s" % tablename,
            label = T("Organization Type"),
            ondelete = "SET NULL",
            represent = type_represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "org_organisation_type.id",
                                  type_represent,
                                  sort = True
                                  )),
            sortby = "name",
            widget = organisation_type_widget,
            comment = S3PopupLink(c = "org",
                                  f = "organisation_type",
                                  label = T("Create Organization Type"),
                                  title = T("Organization Type"),
                                  tooltip = T("If you don't see the Type in the list, you can add a new one by clicking link 'Create Organization Type'."),
                                  ),
            )

        configure(tablename,
                  # Not needed since unique=True but would be
                  # if we removed to make these variable by Org
                  #deduplicate = S3Duplicate(),
                  hierarchy = hierarchy,
                  )

        # Components
        add_components(tablename,
                       # Tags
                       org_organisation_type_tag = {"name": "tag",
                                                    "joinby": "organisation_type_id",
                                                    },
                       )

        if settings.get_org_regions():

            hierarchical_regions = current.deployment_settings.get_org_regions_hierarchical()

            # ---------------------------------------------------------------------
            # Organisation Regions
            #
            tablename = "org_region"
            define_table(tablename,
                         Field("name", length=128,
                               label = T("Name"),
                               requires = [IS_NOT_EMPTY(),
                                           IS_LENGTH(64),
                                           ],
                               ),
                         Field("parent", "reference org_region", # This form of hierarchy may not work on all Databases
                               # Label hard-coded for IFRC currently
                               label = T("Zone"),
                               ondelete = "RESTRICT",
                               readable = hierarchical_regions,
                               writable = hierarchical_regions,
                               ),
                         # Can add Path, Level, L0, L1 if-useful for performance, widgets, etc
                         s3_comments(),
                         *s3_meta_fields())

            region_represent = S3Represent(lookup=tablename, translate=True)

            if hierarchical_regions:
                hierarchy = "parent"
                # Can't be defined in-line as otherwise get a circular reference
                table = db[tablename]
                table.parent.represent = region_represent
                table.parent.requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "org_region.id",
                                                      region_represent,
                                                      # Limited to just 1 level of parent
                                                      # IFRC requirement
                                                      filterby="parent",
                                                      filter_opts=(None,),
                                                      orderby="org_region.name"))
                # IFRC: Only show the Regions, not the Zones
                opts_filter = ("parent", (None,))
            else:
                hierarchy = None
                opts_filter = (None, None)

            # CRUD strings
            crud_strings[tablename] = Storage(
                label_create = T("Add Region"),
                title_display = T("Region Details"),
                title_list = T("Regions"),
                title_update = T("Edit Region"),
                label_list_button = T("List Regions"),
                label_delete_button = T("Delete Region"),
                msg_record_created = T("Region added"),
                msg_record_modified = T("Region updated"),
                msg_record_deleted = T("Region deleted"),
                msg_list_empty = T("No Regions currently registered"))

            region_id = S3ReusableField("region_id", "reference %s" % tablename,
                label = T("Region"),
                ondelete = "SET NULL",
                represent = region_represent,
                requires = IS_EMPTY_OR(
                            IS_ONE_OF(db, "org_region.id",
                                      region_represent,
                                      sort=True,
                                      not_filterby=opts_filter[0],
                                      not_filter_opts=opts_filter[1],
                                      )),
                sortby = "name",
                comment = S3PopupLink(c = "org",
                                      f = "region",
                                      label = T("Add Region"),
                                      title = T("Region"),
                                      tooltip = T("If you don't see the Type in the list, you can add a new one by clicking link 'Add Region'."),
                                      ),
                )

            configure(tablename,
                      deduplicate = S3Duplicate(),
                      hierarchy = hierarchy,
                      )

            if settings.get_org_region_countries():
                # Components
                add_components(tablename,
                               # Tags
                               org_region_country = {"name": "country",
                                                     "joinby": "region_id",
                                                     },
                               )

                # ---------------------------------------------------------------------
                # Region countries
                #
                tablename = "org_region_country"
                define_table(tablename,
                             region_id(),
                             self.gis_country_id(),
                             s3_comments(),
                             *s3_meta_fields())

        else:
            region_represent = None
            region_id = S3ReusableField("region_id", "integer",
                                        readable = False,
                                        writable = False)

        # ---------------------------------------------------------------------
        # Organisations
        # http://xmlns.com/foaf/0.1/Organisation
        #
        tablename = "org_organisation"
        define_table(tablename,
                     self.super_link("pe_id", "pr_pentity"),
                     Field("root_organisation", "reference org_organisation",
                           ondelete = "CASCADE",
                           readable = False,
                           writable = False,
                           represent = S3Represent(lookup="org_organisation"),
                           ),
                     Field("name", notnull=True,
                           length=128, # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     # http://hxl.humanitarianresponse.info/#abbreviation
                     Field("acronym", length=16,
                           label = T("Acronym"),
                           represent = lambda val: val or "",
                           requires = IS_LENGTH(16),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Acronym"),
                                                           T("Acronym of the organization's name, eg. IFRC.")))
                           ),
                     #Field("registration", label = T("Registration")),    # Registration Number
                     region_id(),
                     Field("country", length=2,
                           label = T("Home Country"),
                           represent = self.gis_country_code_represent,
                           requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                        lambda: gis.get_countries(key_type="code"),
                                        zero = messages.SELECT_LOCATION
                                        )),
                           readable = use_country,
                           writable = use_country,
                           ),
                     # Simple free-text contact field, can be enabled
                     # in templates as needed
                     Field("contact",
                           label = T("Contact"),
                           readable = False,
                           writable = False,
                           ),
                     # @ToDo: Deprecate with Contact component
                     Field("phone",
                           label = T("Phone #"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           #readable = False,
                           #writable = False,
                           ),
                     # http://hxl.humanitarianresponse.info/#organisationHomepage
                     Field("website",
                           label = T("Website"),
                           represent = s3_url_represent,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("year", "integer",
                           label = T("Year"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(1850, 2100)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Year"),
                                                           T("Year that the organization was founded"))),
                           ),
                     Field("logo", "upload",
                           label = T("Logo"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.doc_image_represent,
                           requires = [IS_EMPTY_OR(IS_IMAGE(maxsize=(400, 400),
                                                            error_message=T("Upload an image file (png or jpeg), max. 400x400 pixels!"))),
                                       IS_EMPTY_OR(IS_UPLOAD_FILENAME())],
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Logo"),
                                                           T("Logo of the organization. This should be a png or jpeg file and it should be no larger than 400x400"))),
                           uploadfolder = os.path.join(current.request.folder, "uploads"),
                           ),
                     s3_comments(),
                     #document_id(), # Better to have multiple Documents on a Tab
                     #Field("privacy", "integer", default=0),
                     #Field("archived", "boolean", default=False),
                     *s3_meta_fields())

        crud_fields = ["name",
                       "acronym",
                       S3SQLInlineLink(
                            "organisation_type",
                            field = "organisation_type_id",
                            # Disable "Search"-field in multi-select widget:
                            # - default "auto" shows Search field at 10 or more options,
                            #   which adds unnecessary complexity to a commonly and
                            #   often early used form (e.g. create Org when registering)
                            search = False,
                            label = T("Type"),
                            multiple = multiple_organisation_types,
                            widget = type_widget,
                            ),
                       "region_id",
                       "country" if use_country else None,
                       "phone",
                       "website",
                       "year",
                       "logo",
                       "comments",
                       ]

        use_sector = settings.get_org_sector()
        if use_sector:
            crud_fields.insert(3, S3SQLInlineLink("sector",
                                                  columns = 4,
                                                  label = T("Sectors"),
                                                  field = "sector_id",
                                                  ),
                               )

        crud_form = S3SQLCustomForm(*crud_fields)

        # CRUD strings
        ADD_ORGANIZATION = T("Create Organization")
        crud_strings[tablename] = Storage(
            label_create = ADD_ORGANIZATION,
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            title_upload = T("Import Organizations"),
            label_list_button = T("List Organizations"),
            label_delete_button = T("Delete Organization"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization deleted"),
            msg_list_empty = T("No Organizations currently registered"))

        # Default widget
        if settings.get_org_autocomplete():
            tooltip = messages.AUTOCOMPLETE_HELP
            default_widget = S3OrganisationAutocompleteWidget(default_from_profile = True)
        else:
            tooltip = T("If you don't see the Organization in the list, you can add a new one by clicking link 'Create Organization'.")
            default_widget = None
        org_widgets = {"default": default_widget}

        # Representation for foreign keys
        org_organisation_represent = org_OrganisationRepresent(show_link = True)

        # Fields for text filter
        text_fields = ["name",
                       "acronym",
                       "comments",
                       ]
        if use_sector:
            text_fields += ["sector.name", "sector.abrv"]

        if settings.get_L10n_translate_org_organisation():
            text_fields.extend(("name.name_l10n",
                                "name.acronym_l10n"
                                ))

        if settings.get_org_branches():

            # Additional text filter fields for branches
            text_fields.extend(("parent.name",
                                "parent.acronym",
                                ))
            text_comment = T("You can search by name, acronym, comments or parent name or acronym.")

            # Hierarchy configuration and widget
            configure(tablename,
                      # link table alias (organisation_branch) is ambiguous here
                      # => need to specify the full join
                      hierarchy = "parent__link.organisation_id",
                      hierarchy_link = "parent",
                      )
            org_widgets["hierarchy"] = S3HierarchyWidget(lookup="org_organisation",
                                                         represent=org_organisation_represent,
                                                         multiple=False,
                                                         leafonly=False,
                                                         )
        else:
            text_comment = T("You can search by name, acronym or comments")

        # Reusable field
        organisation_comment = S3PopupLink(c = "org",
                                           f = "organisation",
                                           label = ADD_ORGANIZATION,
                                           title = ADD_ORGANIZATION,
                                           tooltip = tooltip,
                                           )
        auth = current.auth
        organisation_id = S3ReusableField("organisation_id", "reference %s" % tablename,
                                          comment = organisation_comment,
                                          default = auth.user.organisation_id if auth.is_logged_in() \
                                                                              else None,
                                          label = messages.ORGANISATION,
                                          ondelete = "RESTRICT",
                                          represent = org_organisation_represent,
                                          requires = org_organisation_requires(),
                                          sortby = "name",
                                          widgets = org_widgets,
                                          )

        list_fields = ["id",
                       "name",
                       "acronym",
                       (T("Type"), "organisation_organisation_type.organisation_type_id"),
                       "website"
                       ]

        if use_sector:
            list_fields.insert(4, (T("Sectors"), "sector_organisation.sector_id"))

        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       comment = text_comment,
                                       #_class = "filter-search",
                                       ),
                          ]
        append = filter_widgets.append

        # Don't add Type or Sector Filters for Supplier organizations in the asset and inv controllers
        # or for Training Centers
        if current.request.function not in ("supplier", "training_center"):
            append(type_filter)
            if use_sector:
                append(S3OptionsFilter("sector_organisation.sector_id",
                                       options = lambda: \
                                           s3_get_filter_opts("org_sector",
                                                              location_filter=True,
                                                              none=True,
                                                              translate=True),
                                       )
                       )

        if use_country:
            append(S3OptionsFilter("country",
                                   #label = T("Home Country"),
                                   ),
                   )

        report_fields = ["organisation_organisation_type.organisation_type_id",
                         ]
        if use_country:
            report_fields.append("country")

        default_col = "organisation_organisation_type.organisation_type_id"
        if use_sector:
            report_fields.insert(1, "sector_organisation.sector_id")
            default_row = "sector_organisation.sector_id"
        elif use_country:
            default_row = "country"
        else:
            # Single column (switch axes)
            default_row = default_col
            default_col = None

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Number of Organizations"), "count(id)"),
                                         (T("List of Organizations"), "list(name)"),
                                         ],
                                 defaults=Storage(rows = default_row,
                                                  cols = default_col,
                                                  fact = "count(id)",
                                                  totals = True,
                                                  chart = "spectrum:cols",
                                                  #table = "collapse",
                                                  ),
                                 )

        location_context = settings.get_org_organisation_location_context()

        configure(tablename,
                  context = {"location": location_context,
                             },
                  crud_form = crud_form,
                  deduplicate = org_OrganisationDuplicate.duplicate,
                  filter_widgets = filter_widgets,
                  hierarchy_export = {"root": "Organisation",
                                      "branch": "Branch",
                                      },
                  list_fields = list_fields,
                  list_layout = org_organisation_list_layout,
                  list_orderby = "org_organisation.name",
                  onaccept = self.org_organisation_onaccept,
                  ondelete = self.org_organisation_ondelete,
                  referenced_by = [(auth.settings.table_user_name,
                                    "organisation_id")],
                  report_options = report_options,
                  super_entity = "pr_pentity",
                  )

        # Custom Method for S3OrganisationAutocompleteWidget
        self.set_method("org", "organisation",
                        method = "search_ac",
                        action = self.org_search_ac)

        # Components
        add_components(tablename,
                       # Documents
                       doc_document = "organisation_id",
                       doc_image = "organisation_id",
                       doc_card_config = "organisation_id",
                       # Groups
                       org_group = {"link": "org_group_membership",
                                    "joinby": "organisation_id",
                                    "key": "group_id",
                                    "actuate": "hide",
                                    },
                       # Format for InlineComponent/filter_widget
                       org_group_membership = "organisation_id",
                       # Names
                       org_organisation_name = {"name": "name",
                                                "joinby": "organisation_id",
                                                },
                       # Tags
                       org_organisation_tag = {"name": "tag",
                                               "joinby": "organisation_id",
                                               },
                       # Sites
                       org_site = "organisation_id",
                       # Facilities
                       org_facility = "organisation_id",
                       # Offices
                       org_office = "organisation_id",
                       # Warehouses
                       inv_warehouse = "organisation_id",
                       # Staff/Volunteers
                       hrm_human_resource = "organisation_id",
                       pr_person = {"link": "hrm_human_resource",
                                    "joinby": "organisation_id",
                                    "key": "person_id",
                                    "actuate": "link",
                                    },
                       # Members
                       member_membership = "organisation_id",
                       # Locations served
                       gis_location = {"link": "org_organisation_location",
                                       "joinby": "organisation_id",
                                       "key": "location_id",
                                       "actuate": "hide",
                                       },
                       # Format for filter_widget
                       org_organisation_location = "organisation_id",
                       # Types
                       org_organisation_type = {"link": "org_organisation_organisation_type",
                                                "joinby": "organisation_id",
                                                "key": "organisation_type_id",
                                                "multiple": multiple_organisation_types,
                                                "actuate": "hide",
                                                },
                       # Format for filter_widget
                       org_organisation_organisation_type = "organisation_id",
                       # Catalogs
                       supply_catalog = "organisation_id",
                       # Resources
                       org_resource = "organisation_id",
                       # Religion
                       pr_religion = {"link": "pr_religion_organisation",
                                      "joinby": "organisation_id",
                                      "key": "religion_id",
                                      "multiple": False,
                                      "actuate": "hide",
                                      },
                       pr_religion_organisation = "organisation_id",
                       # Sectors
                       org_sector = {"link": "org_sector_organisation",
                                     "joinby": "organisation_id",
                                     "key": "sector_id",
                                     "actuate": "hide",
                                     },
                       # Format for filter_widget
                       org_sector_organisation = "organisation_id",
                       # Services
                       org_service = {"link": "org_service_organisation",
                                      "joinby": "organisation_id",
                                      "key": "service_id",
                                      "actuate": "hide",
                                      },
                       # Service Locations
                       org_service_location = ({"name": "service_location",
                                                "joinby": "organisation_id",
                                                },
                                               {"name": "active_service_location",
                                                "joinby": "organisation_id",
                                                "filterby": {
                                                    "status": "ACTIVE",
                                                    },
                                                },
                                               ),
                       # Format for filter_widget
                       org_service_organisation = "organisation_id",
                       # Assets
                       asset_asset = "organisation_id",
                       # Needs
                       req_need = {"name": "needs",
                                   "link": "req_need_organisation",
                                   "joinby": "organisation_id",
                                   "key": "need_id",
                                   "multiple": False,
                                   },
                       # Requests
                       #req_req = "donated_by_id",

                       # Enable this to allow migration of users between instances
                       #auth_user = "organisation_id",

                       # Related Organisations
                       org_organisation = (# Branches
                                           {"name": "branch",
                                            "link": "org_organisation_branch",
                                            "joinby": "organisation_id",
                                            "key": "branch_id",
                                            "actuate": "embed",
                                            "autocomplete": "name",
                                            "autodelete": True,
                                            },
                                           # Parent (for imports)
                                           {"name": "parent",
                                            "link": "org_organisation_branch",
                                            "joinby": "branch_id",
                                            "key": "organisation_id",
                                            "actuate": "embed",
                                            "autocomplete": "name",
                                            "autodelete": False,
                                            },
                                           # 'Supported' Organisations
                                           #{"name": "supported",
                                           # "link": "org_organisation_organisation",
                                           # "joinby": "parent_id",
                                           # "key": "organisation_id",
                                           # "actuate": "embed",
                                           # "autocomplete": "name",
                                           # "autodelete": True,
                                           # },
                                           # 'Supporting' Organisation
                                           {"name": "supported_by",
                                            "link": "org_organisation_organisation",
                                            "joinby": "organisation_id",
                                            "key": "parent_id",
                                            "actuate": "embed",
                                            "autocomplete": "name",
                                            "autodelete": False,
                                            },
                                           ),

                       # Population Outreach (referral agencies)
                       po_area = {"link": "po_organisation_area",
                                  "joinby": "organisation_id",
                                  "key": "area_id",
                                  },
                       po_organisation_area = "organisation_id",
                       po_organisation_household = "organisation_id",
                       po_referral_organisation = "organisation_id",
                       )

        # Beneficiary/Case Management
        if settings.has_module("br"):
            # Use BR for org-specific categories in case management
            add_components(tablename,
                           br_need = "organisation_id",
                           br_assistance_theme = "organisation_id",
                           )
        else:
            # Use DVR for org-specific categories in case management
            add_components(tablename,
                           dvr_need = "organisation_id",
                           dvr_response_theme = "organisation_id",
                           )

        # Projects
        if settings.get_project_multiple_organisations():
            # Use link table
            add_components(tablename,
                           project_project = {"link": "project_organisation",
                                              "joinby": "organisation_id",
                                              "key": "project_id",
                                              # Embed widget doesn't currently
                                              # support 2 fields of same name (8 hours)
                                              #"actuate": "embed",
                                              "actuate": "hide",
                                              "autocomplete": "name",
                                              "autodelete": False,
                                              },
                            # Format for filter_widget
                            project_organisation = {"name": "project_organisation",
                                                    "joinby": "organisation_id",
                                                    },
                            )

        else:
            # Direct link
            add_components(tablename,
                           project_project = "organisation_id",
                           )

        if settings.get_project_activities():
            add_components(tablename,
                           project_activity = {"link": "project_activity_organisation",
                                               "joinby": "organisation_id",
                                               "key": "activity_id",
                                               "actuate": "replace",
                                               "autodelete": False,
                                               },
                           )

        # ---------------------------------------------------------------------
        # Organisation <-> Organisation Type
        #
        tablename = "org_organisation_organisation_type"
        define_table(tablename,
                     organisation_id(empty = False,
                                     ondelete = "CASCADE",
                                     ),
                     organisation_type_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                     *s3_meta_fields())

        configure(tablename,
                  # Whilst S3SQLInlineLink can resolve duplicates automatically, imports cannot
                  deduplicate = S3Duplicate(primary = ("organisation_id",
                                                       "organisation_type_id",
                                                       ),
                                            ),
                  onaccept = self.org_organisation_organisation_type_onaccept,
                  ondelete = self.org_organisation_organisation_type_ondelete,
                  xml_post_parse = self.org_organisation_organisation_type_xml_post_parse,
                  )

        # ---------------------------------------------------------------------
        # Organisation <-> User
        #
        utable = auth.settings.table_user
        tablename = "org_organisation_user"
        define_table(tablename,
                     Field("user_id", utable),
                     organisation_id(empty = False,
                                     ondelete = "CASCADE",
                                     ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"org_organisation_type_id": organisation_type_id,
                "org_organisation_crud_fields": crud_fields,
                "org_organisation_id": organisation_id,
                "org_organisation_represent": org_organisation_represent,
                "org_region_id": region_id,
                "org_region_represent": region_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_onaccept(form):
        """
            Set default root_organisation ID
            If a logo was uploaded then create the extra versions
        """

        form_vars_get = form.vars.get

        # Set default root_organisation ID
        db = current.db
        record_id = form_vars_get("id")
        if record_id:
            otable = db.org_organisation
            query = (otable.id == record_id) & \
                    (otable.root_organisation == None)
            db(query).update(root_organisation = otable.id)

        newfilename = form_vars_get("logo_newfilename")
        if newfilename:
            # Create the extra versions of the Logo
            s3db = current.s3db
            image = form.request_vars.logo
            s3db.pr_image_modify(image.file,
                                 newfilename,
                                 image.filename,
                                 size = (None, 60),
                                 )
            s3db.pr_image_modify(image.file,
                                 newfilename,
                                 image.filename,
                                 size = (None, 60),
                                 to_format = "bmp",
                                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_ondelete(row):
        """
            If an Org is deleted then remove Logo
        """

        db = current.db
        table = db.org_organisation
        deleted_row = db(table.id == row.id).select(table.logo,
                                                    limitby=(0, 1)
                                                    ).first()
        if deleted_row and deleted_row.logo:
            current.s3db.pr_image_delete_all(deleted_row.logo)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_organisation_type_onaccept(form):
        """
            Update the realm entity of the organisation after changing the
            organisation type (otherwise type-dependent realm rules won't
            ever take effect since the org_organisation record is written
            before the org_organisation_organisation_type)

            @param form: the Form
        """

        # Get the type-link
        try:
            record_id = form.vars.id
        except AttributeError:
            return
        table = current.s3db.org_organisation_organisation_type
        row = current.db(table.id == record_id).select(table.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()

        if row:
            # Update the realm entity
            current.auth.set_realm_entity("org_organisation",
                                          row.organisation_id,
                                          force_update = True,
                                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_organisation_type_ondelete(row):
        """
            Update the realm entity of the organisation after removing an
            organisation type (otherwise type-dependent realm rules won't
            take effect)

            @param form: the Row
        """

        # Get the type-link
        try:
            record_id = row.id
        except AttributeError:
            return
        table = current.s3db.org_organisation_organisation_type
        row = current.db(table.id == record_id).select(table.deleted_fk,
                                                       limitby = (0, 1),
                                                       ).first()
        if row and row.deleted_fk:
            # Find the organisation ID
            try:
                deleted_fk = json.loads(row.deleted_fk)
            except ValueError:
                return
            organisation_id = deleted_fk.get("organisation_id")

            # Update the realm entity
            current.auth.set_realm_entity("org_organisation",
                                          organisation_id,
                                          force_update = True,
                                          )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_organisation_organisation_type_xml_post_parse(element, record):
        """
            Check for defaults provided by project/organisation.xsl
        """

        org_type_default = element.xpath('data[@field="_organisation_type_id"]')
        if org_type_default:
            org_type_default = org_type_default[0].text
            db = current.db
            table = db.org_organisation_type
            row = None
            # These default mappings can be overridden per-deployment
            if org_type_default == "Donor":
                row = db(table.name == "Bilateral").select(table.id,
                                                           cache=current.s3db.cache,
                                                           limitby=(0, 1)).first()
            elif org_type_default == "Partner":
                row = db(table.name == "NGO").select(table.id,
                                                     cache=current.s3db.cache,
                                                     limitby=(0, 1)).first()
            elif org_type_default in ("Host National Society",
                                      "Partner National Society"):
                row = db(table.name == "Red Cross / Red Crescent").select(table.id,
                                                                          cache=current.s3db.cache,
                                                                          limitby=(0, 1)
                                                                          ).first()
            if row:
                # Note this sets only the default, so won't override existing or explicit values
                record._organisation_type_id = row.id

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_search_ac(r, **attr):
        """
            JSON search method for S3OrganisationAutocompleteWidget
            - searches name & acronym for both this organisation & the parent
              of branches
            @param r: the S3Request
            @param attr: request attributes
        """

        _vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = _vars.term or _vars.value or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower().strip()

        if not value:
            r.error(400, "Missing option! Require value")

        response = current.response
        resource = r.resource
        table = resource.table
        settings = current.deployment_settings

        use_branches = settings.get_org_branches()
        search_l10n = settings.get_L10n_translate_org_organisation()

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        query = (FS("organisation.name").lower().like(value + "%")) | \
                (FS("organisation.acronym").lower().like(value + "%"))
        if use_branches:
            query |= (FS("parent.name").lower().like(value + "%")) | \
                     (FS("parent.acronym").lower().like(value + "%"))
        if search_l10n:
            query |= (FS("name.name_l10n").lower().like(value + "%")) | \
                     (FS("name.acronym_l10n").lower().like(value + "%"))

        if "link" in _vars:
            link_filter = S3EmbeddedComponentWidget.link_filter_query(table, _vars.link)
            if link_filter:
                query &= link_filter

        resource.add_filter(query)

        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        limit = int(_vars.limit or MAX_SEARCH_RESULTS)
        if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
            output = [
                {"label": str(current.T("There are more than %(max)s results, please input more characters.") % \
                    {"max": MAX_SEARCH_RESULTS})}
                ]
        else:
            # Fields to return
            fields = ["id",
                      "name",
                      "acronym",
                      ]
            if use_branches:
                fields.append("parent.name")
            if search_l10n:
                fields += ["name.name_l10n",
                           "name.acronym_l10n",
                           ]

            rows = resource.select(fields,
                                   start = 0,
                                   limit = limit,
                                   orderby = table.name,
                                   as_rows = True,
                                   )
            output = []
            append = output.append
            for row in rows:
                acronym = ""
                if use_branches or search_l10n:
                    _row = row[table]
                else:
                    _row = row
                if search_l10n:
                    name = row["org_organisation_name.name_l10n"] or _row.name
                    acronym = row["org_organisation_name.acronym_l10n"] or _row.acronym
                else:
                    name = _row.name
                    acronym = _row.acronym
                record = {"id": _row.id,
                          "name": name,
                          }
                if acronym:
                    record["acronym"] = acronym

                if "org_parent_organisation" in row:
                    parent = object.__getattribute__(row, "org_parent_organisation")
                    if parent.name is not None:
                        record["parent"] = parent.name

                # Determine if input matches the organisation name or
                # the acronym, or neither (e.g. input matching the
                # parent organisation)
                value_len = len(value)
                name_match = s3_unicode(name)[:value_len].lower() == value
                acronym_match = acronym and \
                                s3_unicode(acronym)[:value_len].lower() == value
                if name_match:
                    nextString = name[value_len:]
                    if nextString != "":
                        record["matchString"] = name[:value_len]
                        record["nextString"] = nextString
                elif acronym_match:
                    nextString = acronym[value_len:]
                    if nextString != "":
                        record["matchString"] = acronym[:value_len]
                        record["nextString"] = nextString
                        record["match"] = "acronym"

                append(record)

        response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

# =============================================================================
class S3OrganisationNameModel(S3Model):
    """
        Organsiation Names model
        - local names/acronyms for Organisations
    """

    names = ("org_organisation_name",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "org_organisation_name"
        self.define_table(tablename,
                          self.org_organisation_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          s3_language(empty = False),
                          Field("name_l10n",
                                label = T("Local Name"),
                                ),
                          Field("acronym_l10n",
                                label = T("Local Acronym"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_id",
                                                            "language",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationBranchModel(S3Model):
    """
        Organisation Branches
    """

    names = ("org_organisation_branch",)

    def model(self):

        T = current.T

        organisation_id = self.org_organisation_id

        # ---------------------------------------------------------------------
        # Organisation Branches
        #
        tablename = "org_organisation_branch"
        self.define_table(tablename,
                          organisation_id(ondelete = "CASCADE"),
                          organisation_id("branch_id",
                                          default = None,
                                          label = T("Branch"),
                                          ondelete = "CASCADE",
                                          ),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Branch Organization"),
            title_display = T("Branch Organization Details"),
            title_list = T("Branch Organizations"),
            title_update = T("Edit Branch Organization"),
            #title_upload = T("Import Branch Organizations"),
            label_list_button = T("List Branch Organizations"),
            label_delete_button = T("Delete Branch"),
            msg_record_created = T("Branch Organization added"),
            msg_record_modified = T("Branch Organization updated"),
            msg_record_deleted = T("Branch Organization deleted"),
            msg_list_empty = T("No Branch Organizations currently registered"))

        self.configure(tablename,
                       # An Organisation can only be a branch of one Organisation:
                       deduplicate = S3Duplicate(primary = ("branch_id",)),
                       onaccept = self.org_branch_onaccept,
                       ondelete = self.org_branch_ondelete,
                       onvalidation = self.org_branch_onvalidation,
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_onvalidation(form):
        """
            Prevent an Organisation from being a Branch of itself
            - this is for interactive forms, imports are caught in .xsl
        """

        request_vars = form.request_vars
        if request_vars and \
           request_vars.branch_id and \
           request_vars.organisation_id and \
           int(request_vars.branch_id) == int(request_vars.organisation_id):
            error = current.T("Cannot make an Organization a branch of itself!")
            form.errors["branch_id"] = error
            current.response.error = error

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations
        """

        id_ = form.vars.id
        db = current.db
        s3db = current.s3db

        # Fields a branch organisation inherits from its parent organisation
        # (components added later)
        inherit = ["region_id",
                   "country",
                   ]

        otable = s3db.org_organisation
        ltable = db.org_organisation_branch
        btable = db.org_organisation.with_alias("org_branch_organisation")

        ifields = [otable[fn] for fn in inherit] + \
                  [btable[fn] for fn in inherit]

        left = [otable.on(ltable.organisation_id == otable.id),
                btable.on(ltable.branch_id == btable.id)]

        record = db(ltable.id == id_).select(otable.root_organisation,
                                             btable.root_organisation,
                                             ltable.branch_id,
                                             ltable.organisation_id,
                                             ltable.deleted,
                                             ltable.deleted_fk,
                                             *ifields,
                                             left=left,
                                             limitby=(0, 1)).first()

        if record:
            organisation = record.org_organisation
            branch = record.org_branch_organisation
            link = record.org_organisation_branch

            branch_id = link.branch_id
            organisation_id = link.organisation_id

            if branch_id and organisation_id and not link.deleted:

                # Eliminate duplicate affiliations
                query = (ltable.branch_id == branch_id) & \
                        (ltable.organisation_id == organisation_id) & \
                        (ltable.id != id_) & \
                        (ltable.deleted != True)

                deleted_fk = {"branch_id": branch_id,
                              "organisation_id": organisation_id,
                              }
                db(query).update(deleted=True,
                                 branch_id=None,
                                 organisation_id=None,
                                 deleted_fk=json.dumps(deleted_fk))

                # Inherit fields from parent organisation
                update = dict((field, organisation[field])
                                for field in inherit
                                if not branch[field] and organisation[field])
                if update:
                    db(otable.id == branch_id).update(**update)

                record_ids = (organisation_id, branch_id)

                # Inherit Org Types
                ltable = db.org_organisation_organisation_type
                rows = db(ltable.organisation_id.belongs(record_ids)) \
                                            .select(ltable.organisation_id,
                                                    ltable.organisation_type_id,
                                                    )

                org_types = set()
                branch_types = set()
                for row in rows:
                    if row.organisation_id == organisation_id:
                        org_types.add(row.organisation_type_id)
                    else:
                        branch_types.add(row.organisation_type_id)
                for t in org_types - branch_types:
                    link_id = ltable.insert(organisation_id = branch_id,
                                            organisation_type_id = t,
                                            )
                    form = Storage(vars = Storage(id = link_id))
                    S3OrganisationModel.org_organisation_organisation_type_onaccept(link_id)

                # Inherit Org Sectors
                ltable = s3db.org_sector_organisation
                rows = db(ltable.organisation_id.belongs(record_ids)) \
                                            .select(ltable.organisation_id,
                                                    ltable.sector_id,
                                                    )
                org_sectors = set()
                branch_sectors = set()
                for row in rows:
                    if row.organisation_id == organisation_id:
                        org_sectors.add(row.sector_id)
                    else:
                        branch_sectors.add(row.sector_id)
                for s in org_sectors - branch_sectors:
                    ltable.insert(organisation_id = branch_id,
                                  sector_id = s,
                                  )

            org_update_affiliations("org_organisation_branch", link)

            # Update the root organisation
            if link.deleted or \
               branch.root_organisation is None or \
               branch.root_organisation != organisation.root_organisation:
                org_update_root_organisation(branch_id)

            # Update realm entity, because realm rules may depend
            # on branch relationships and/or inherited data
            current.auth.set_realm_entity(otable, branch_id, force_update=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_branch_ondelete(row):
        """
            Update affiliations
        """

        db = current.db
        table = db.org_organisation_branch
        record = db(table.id == row.id).select(table.branch_id,
                                               table.deleted,
                                               table.deleted_fk,
                                               limitby=(0, 1)).first()
        if record:
            org_update_affiliations("org_organisation_branch", record)

# =============================================================================
class S3OrganisationCapacityModel(S3Model):
    """
        (Branch) Organisational Capacity Assessment
        - Flexible Questions (Dynamic Data Model)
    """

    names = ("org_capacity_indicator",
             "org_capacity_assessment",
             "org_capacity_assessment_data",
             )

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Indicators
        #
        tablename = "org_capacity_indicator"
        define_table(tablename,
                     Field("section"),
                     Field("header"),
                     Field("number", "integer"),
                     Field("name"),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # (Branch) Organisational Capacity Assessment
        #
        tablename = "org_capacity_assessment"
        define_table(tablename,
                     self.org_organisation_id(empty = False),
                     s3_date(future = 0),
                     self.pr_person_id(label = T("Lead Facilitator")),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Create Assessment"),
                title_display = T("Assessment Details"),
                title_list = T("Assessments"),
                title_update = T("Edit Assessment"),
                label_list_button = T("List Assessments"),
                label_delete_button = T("Delete Assessment"),
                msg_record_created = T("Assessment added"),
                msg_record_modified = T("Assessment updated"),
                msg_record_deleted = T("Assessment removed"),
                msg_list_empty = T("No Assessments currently registered"))

        # Components
        self.add_components(tablename,
                            org_capacity_assessment_data = {"name": "data",
                                                            "joinby": "assessment_id",
                                                            },
                            )

        # ---------------------------------------------------------------------
        # (Branch) Organisational Capacity Assessment Data
        #
        tablename = "org_capacity_assessment_data"
        define_table(tablename,
                     Field("assessment_id", "reference org_capacity_assessment",
                           readable = False,
                           writable = False,
                           ),
                     Field("indicator_id", "reference org_capacity_indicator",
                           represent = S3Represent(lookup="org_capacity_indicator",
                                                   fields=["number", "name"],
                                                   field_sep=". "),
                           writable = False,
                           ),
                     Field("rating",
                           label = T("Rating"),
                           requires = IS_IN_SET(("A","B","C","D","E","F")),
                           ),
                     Field("ranking", "integer",
                           label = T("Ranking"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET((1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)),
                                      ),
                           ),
                     *s3_meta_fields()
                     )

        # Custom Report Method
        self.set_method("org", "capacity_assessment_data",
                        method = "custom_report",
                        action = org_CapacityReport())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationGroupModel(S3Model):
    """
        Organisation Group Model
        - 'Coalitions' or 'Networks'
    """

    names = ("org_group",
             "org_group_membership",
             "org_group_membership_status",
             "org_group_id",
             "org_group_represent",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Organization Groups
        #
        tablename = "org_group"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     Field("name", notnull=True, unique=True, length=128,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("mission",
                           label = T("Mission"),
                           represent = lambda v: v or NONE,
                           # Enable as-required in Custom Forms
                           readable = False,
                           writable = False,
                           ),
                     Field("website",
                           label = T("Website"),
                           represent = s3_url_represent,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("meetings",
                           label = T("Meetings"),
                           represent = lambda v: v or NONE,
                           # Enable as-required in Custom Forms
                           readable = False,
                           writable = False,
                           ),
                     self.gis_location_id(
                         widget = S3LocationSelector(#catalog_layers = True,
                                                     points = False,
                                                     polygons = True,
                                                     )
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        label = current.deployment_settings.get_org_groups()
        if label == "Coalition":
            crud_strings[tablename] = Storage(
                label_create = T("Create Coalition"),
                title_display = T("Coalition Details"),
                title_list = T("Coalitions"),
                title_update = T("Update Coalition"),
                label_list_button = T("List Coalitions"),
                label_delete_button = T("Remove Coalition"),
                msg_record_created = T("Coalition added"),
                msg_record_modified = T("Coalition updated"),
                msg_record_deleted = T("Coalition removed"),
                msg_list_empty = T("No Coalitions currently recorded"))
        elif label == "Network":
            crud_strings[tablename] = Storage(
                label_create = T("Create Network"),
                title_display = T("Network Details"),
                title_list = T("Networks"),
                title_update = T("Edit Network"),
                label_list_button = T("List Networks"),
                label_delete_button = T("Remove Network"),
                msg_record_created = T("Network added"),
                msg_record_modified = T("Network updated"),
                msg_record_deleted = T("Network removed"),
                msg_list_empty = T("No Networks currently recorded"))
        else:
            # Functionality is disabled but model is being loaded via load_all_models()
            label = "Group"

        configure(tablename,
                  list_fields = ["name",
                                 "comments",
                                 ],
                  referenced_by = [(current.auth.settings.table_user_name,
                                    "org_group_id")],
                  super_entity = ("doc_entity", "pr_pentity"),
                  )

        group_represent = S3Represent(lookup=tablename)
        group_id = S3ReusableField("group_id", "reference %s" % tablename,
                                   label = T(label),
                                   # Always links via Link Tables
                                   ondelete = "CASCADE",
                                   represent = group_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "org_group.id",
                                                          group_represent,
                                                          sort=True,
                                                          updateable=True,
                                                          )),
                                   sortby = "name",
                                   )

        # Components
        self.add_components(tablename,
                            org_group_membership = {"name": "membership",
                                                    "joinby": "group_id",
                                                    },
                            org_organisation = {"joinby": "group_id",
                                                "key": "organisation_id",
                                                "link": "org_group_membership",
                                                "actuate": "replace",
                                                },
                            pr_group = {"name": "pr_group",
                                        "joinby": "org_group_id",
                                        "key": "group_id",
                                        "link": "org_group_team",
                                        "actuate": "replace",
                                        },
                            )

        # Custom Method to Assign Orgs
        self.set_method("org", "group",
                        method = "assign",
                        action = org_AssignMethod(component="membership"))

        # ---------------------------------------------------------------------
        # Group membership status
        #
        tablename = "org_group_membership_status"
        define_table(tablename,
                     Field("name", notnull=True, unique=True, length=128,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
                label_create = T("Create Status"),
                title_display = T("Status Details"),
                title_list = T("Statuses"),
                title_update = T("Edit Status"),
                label_list_button = T("List Statuses"),
                label_delete_button = T("Delete Status"),
                msg_record_created = T("Status added"),
                msg_record_modified = T("Status updated"),
                msg_record_deleted = T("Status removed"),
                msg_list_empty = T("No Statuses currently defined"))

        represent = S3Represent(lookup=tablename)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "SET NULL",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "org_group_membership_status.id",
                                                          represent,
                                                          sort=True,
                                                          )),
                                    sortby = "name",
                                    )

        # ---------------------------------------------------------------------
        # Group membership
        #
        tablename = "org_group_membership"
        define_table(tablename,
                     group_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     self.org_organisation_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                     status_id(),
                     *s3_meta_fields()
                     )

        configure(tablename,
                  onaccept = self.group_membership_onaccept,
                  ondelete = self.group_membership_onaccept,
                  )

        # Pass names back to global scope (s3.*)
        return {"org_group_id": group_id,
                "org_group_represent": group_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations
        """

        if hasattr(form, "vars"):
            _id = form.vars.id
        elif isinstance(form, Row) and "id" in form:
            _id = form.id
        else:
            return

        db = current.db
        mtable = db.org_group_membership

        if _id:
            record = db(mtable.id == _id).select(limitby=(0, 1)).first()
        else:
            return
        if record:
            organisation_id = record.organisation_id
            group_id = record.group_id
            if organisation_id and group_id and not record.deleted:
                query = (mtable.organisation_id == organisation_id) & \
                        (mtable.group_id == group_id) & \
                        (mtable.id != record.id) & \
                        (mtable.deleted != True)
                deleted_fk = {"organisation_id": organisation_id,
                              "group_id": group_id}
                db(query).update(deleted = True,
                                 organisation_id = None,
                                 group_id = None,
                                 deleted_fk = json.dumps(deleted_fk))
            org_update_affiliations("org_group_membership", record)

# =============================================================================
class S3OrganisationGroupPersonModel(S3Model):
    """
        Link table between Organisation Groups & Persons
    """

    names = ("org_group_person_status",
             "org_group_person",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table
        crud_strings = current.response.s3.crud_strings

        # ---------------------------------------------------------------------
        # Person<=>Organisation Group membership status
        #
        tablename = "org_group_person_status"
        define_table(tablename,
                     Field("name", notnull=True, unique=True, length=128,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        crud_strings[tablename] = Storage(
                label_create = T("Create Status"),
                title_display = T("Status Details"),
                title_list = T("Statuses"),
                title_update = T("Edit Status"),
                label_list_button = T("List Statuses"),
                label_delete_button = T("Delete Status"),
                msg_record_created = T("Status added"),
                msg_record_modified = T("Status updated"),
                msg_record_deleted = T("Status removed"),
                msg_list_empty = T("No Statuses currently defined"))

        represent = S3Represent(lookup=tablename)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "SET NULL",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "org_group_person_status.id",
                                                          represent,
                                                          sort=True,
                                                          )),
                                    sortby = "name",
                                    )

        # ---------------------------------------------------------------------
        # Link table between Organisation Groups & Persons
        #
        tablename = "org_group_person"
        define_table(tablename,
                     self.org_group_id("org_group_id",
                                       empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     status_id(),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("org_group_id",
                                                            "person_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationGroupTeamModel(S3Model):
    """
        Link table between Organisation Groups & Teams
    """

    names = ("org_group_team",)

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Link table between Organisation Groups & Teams
        #
        tablename = "org_group_team"
        self.define_table(tablename,
                          self.org_group_id("org_group_id",
                                            empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          self.pr_group_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("org_group_id",
                                                            "group_id",
                                                            ),
                                                 ),
                       onaccept = self.org_group_team_onaccept,
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def org_group_team_onaccept(form):
        """
            Update affiliations
        """

        from .pr import OU

        if hasattr(form, "vars"):
            _id = form.vars.id
        elif isinstance(form, Row) and "id" in form:
            _id = form.id
        else:
            return

        if not _id:
            return

        db = current.db
        table = db.org_group_team

        record = db(table.id == _id).select(table.group_id,
                                            table.org_group_id,
                                            limitby=(0, 1)).first()
        if record:
            org_group = ("org_group", record.org_group_id)
            pr_group = ("pr_group", record.group_id)
            current.s3db.pr_add_affiliation(org_group, pr_group,
                                            role="Groups",
                                            role_type=OU,
                                            )

# =============================================================================
class S3OrganisationLocationModel(S3Model):
    """
        Organisation Location Model
        - Locations served by an Organisation
    """

    names = ("org_organisation_location",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organizations <> Locations Link Table
        #
        tablename = "org_organisation_location"
        self.define_table(tablename,
                          self.org_organisation_id(),
                          self.gis_location_id(
                            #represent = self.gis_LocationRepresent(sep=", "),
                            requires = IS_LOCATION(),
                            widget = S3LocationAutocompleteWidget()
                          ),
                          s3_comments(),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Location"),
            title_display = T("Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_upload = T("Import Location data"),
            label_list_button = T("List Locations"),
            msg_record_created = T("Location added to Organization"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location removed from Organization"),
            msg_list_empty = T("No Locations found for this Organization"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_id",
                                                            "location_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationOrganisationModel(S3Model):
    """
        Link table between Organisations & Organisations
        - can be used to provide non-hierarchical relationships
        e.g. "Supports" (as used by IFRC offices for National Societies)
        To report on the full hierarchy of branches, can use the root_organisation field
    """

    names = ("org_organisation_organisation",)

    def model(self):

        #T = current.T
        organisation_id = self.org_organisation_id

        # ---------------------------------------------------------------------
        # Link table between Organisations & Organisations
        #
        tablename = "org_organisation_organisation"
        self.define_table(tablename,
                          organisation_id("parent_id",
                                          empty = False,
                                          ondelete = "CASCADE",
                                          ),
                          organisation_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                          # Add this later if 2 or more usecases need to share this same table within a single template
                          #role_id(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_id",
                                                            "parent_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationResourceModel(S3Model):
    """
        Organisation Resource Model
        - depends on Stats module
    """

    names = ("org_resource",
             "org_resource_type",
             )

    def model(self):

        #settings = current.deployment_settings
        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Organisation Resource Model needs Stats module enabling")
            return {}

        T = current.T
        #auth = current.auth
        crud_strings = current.response.s3.crud_strings
        super_link = self.super_link
        configure = self.configure

        # ---------------------------------------------------------------------
        # Resource Type data
        #
        tablename = "org_resource_type"
        self.define_table(tablename,
                          super_link("parameter_id", "stats_parameter"),
                          Field("name",
                                label = T("Resource Type"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        ADD_RESOURCE_TYPE = T("Create Resource Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_RESOURCE_TYPE,
            title_display = T("Resource Type Details"),
            title_list = T("Resource Types"),
            title_update = T("Edit Resource Type"),
            title_upload = T("Import Resource Types"),
            label_list_button = T("Resource Types"),
            label_delete_button = T("Delete Resource Type"),
            msg_record_created = T("Resource Type added"),
            msg_record_modified = T("Resource Type updated"),
            msg_record_deleted = T("Resource Type deleted"),
            msg_list_empty = T("No Resource Types defined"))

        # Resource Configuration
        configure(tablename,
                  super_entity = "stats_parameter",
                  )

        # ---------------------------------------------------------------------
        # Resource data
        #
        tablename = "org_resource"
        self.define_table(tablename,
                          # Instance
                          super_link("data_id", "stats_data"),
                          self.org_organisation_id(ondelete="CASCADE"),
                          # Consider adding this
                          #self.super_link("site_id", "org_site",
                          #                label = current.deployment_settings.get_org_site_label(),
                          #                instance_types = auth.org_site_types,
                          #                orderby = "org_site.name",
                          #                realms = auth.permission.permitted_realms("org_site",
                          #                                                          method="create"),
                          #                not_filterby = "obsolete",
                          #                not_filter_opts = (True,),
                          #                readable = True,
                          #                writable = True,
                          #                represent = self.org_site_represent,
                          #                ),
                          self.gis_location_id(),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("parameter_id", "stats_parameter",
                                     label = T("Resource Type"),
                                     instance_types = ("org_resource_type",),
                                     represent = S3Represent(lookup="stats_parameter",
                                                             translate=True),
                                     readable = True,
                                     writable = True,
                                     empty = False,
                                     comment = S3PopupLink(c = "org",
                                                           f = "resource_type",
                                                           vars = {"child": "parameter_id"},
                                                           title = ADD_RESOURCE_TYPE,
                                                           ),
                                     ),
                          Field("value", "integer",
                                label = T("Quantity"),
                                requires = IS_INT_IN_RANGE(0, None),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Resource"),
            title_display = T("Resource Details"),
            title_list = T("Resource Inventory"),
            title_update = T("Edit Resource"),
            title_map = T("Map of Resources"),
            title_upload = T("Import Resources"),
            label_list_button = T("Resource Inventory"),
            label_delete_button = T("Delete Resource"),
            msg_record_created = T("Resource added"),
            msg_record_modified = T("Resource updated"),
            msg_record_deleted = T("Resource deleted"),
            msg_list_empty = T("No Resources in Inventory"))

        # Filter Widgets
        filter_widgets = [S3TextFilter(["organisation_id$name",
                                        "location_id",
                                        "parameter_id$name",
                                        "comments",
                                        ],
                                       label = T("Search")),
                          S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          ),
                          ]

        # Report options
        report_fields = ["organisation_id",
                         "parameter_id",
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Total Number of Resources"), "sum(value)"),
                                         (T("Number of Resources"), "count(value)"),
                                         ],
                                 defaults=Storage(rows = "organisation_id",
                                                  cols = "parameter_id",
                                                  fact = "sum(value)",
                                                  totals = True,
                                                  chart = "barchart:rows",
                                                  #table = "collapse",
                                                  )
                                 )

        configure(tablename,
                  context = {"location": "location_id",
                             "organisation": "organisation_id",
                             },
                  filter_widgets = filter_widgets,
                  list_layout = org_resource_list_layout,
                  report_options = report_options,
                  super_entity = "stats_data",
                  )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationSectorModel(S3Model):
    """
        Organisation Sector Model
    """

    names = ("org_sector",
             "org_sector_id",
             #"org_subsector",
             "org_sector_organisation",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        NONE = current.messages["NONE"]

        location = current.session.s3.location_filter
        if location:
            filterby = "location_id"
            filter_opts = (location, None)
        else:
            filterby = None
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Sector
        # (Cluster in UN-style terminology)
        #
        tablename = "org_sector"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           represent = lambda v: T(v) if v is not None \
                                                    else NONE,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("abrv", length=64, #notnull=True,
                           label = T("Abbreviation"),
                           requires = IS_LENGTH(64),
                           ),
                     self.gis_location_id(
                        requires = IS_EMPTY_OR(IS_LOCATION()),
                        widget = S3LocationAutocompleteWidget(),
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if current.deployment_settings.get_ui_label_cluster():
            SECTOR = T("Cluster")
            ADD_SECTOR = T("Create Cluster")
            tooltip = T("If you don't see the Cluster in the list, you can add a new one by clicking link 'Add New Cluster'.")
            crud_strings[tablename] = Storage(
                label_create = ADD_SECTOR,
                title_display = T("Cluster Details"),
                title_list = T("Clusters"),
                title_update = T("Edit Cluster"),
                label_list_button = T("List Clusters"),
                label_delete_button = T("Delete Cluster"),
                msg_record_created = T("Cluster added"),
                msg_record_modified = T("Cluster updated"),
                msg_record_deleted = T("Cluster deleted"),
                msg_list_empty = T("No Clusters currently registered"))
        else:
            SECTOR = T("Sector")
            ADD_SECTOR = T("Create Sector")
            tooltip = T("If you don't see the Sector in the list, you can add a new one by clicking link 'Create Sector'.")
            crud_strings[tablename] = Storage(
                label_create = ADD_SECTOR,
                title_display = T("Sector Details"),
                title_list = T("Sectors"),
                title_update = T("Edit Sector"),
                label_list_button = T("List Sectors"),
                label_delete_button = T("Delete Sector"),
                msg_record_created = T("Sector added"),
                msg_record_modified = T("Sector updated"),
                msg_record_deleted = T("Sector deleted"),
                msg_list_empty = T("No Sectors currently registered"))

        configure("org_sector",
                  deduplicate = self.org_sector_duplicate,
                  onaccept = self.org_sector_onaccept,
                  )

        sector_comment = lambda child: S3PopupLink(c = "org",
                                                   f = "sector",
                                                   vars = {"child": child},
                                                   label = ADD_SECTOR,
                                                   title = SECTOR,
                                                   tooltip = tooltip,
                                                   )

        represent = S3Represent(lookup=tablename, translate=True)
        sector_id = S3ReusableField("sector_id", "reference %s" % tablename,
                                    label = SECTOR,
                                    ondelete = "SET NULL",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "org_sector.id",
                                                          represent,
                                                          sort=True,
                                                          filterby=filterby,
                                                          filter_opts=filter_opts,
                                                          )),
                                    sortby = "abrv",
                                    comment = sector_comment("sector_id"),
                                    )

        # Components
        add_components(tablename,
                       org_organisation = {"link": "org_sector_organisation",
                                           "joinby": "sector_id",
                                           "key": "organisation_id",
                                           "actuate": "hide",
                                          },
                       org_sector_organisation = {"joinby": "sector_id",
                                                  },
                       project_project = {"link": "project_sector_project",
                                          "joinby": "sector_id",
                                          "key": "project_id",
                                          "actuate": "hide",
                                          },
                       #project_activity_type = {"link": "project_activity_type_sector",
                       #                         "joinby": "sector_id",
                       #                         "key": "activity_type_id",
                       #                         "actuate": "hide",
                       #                         },
                       #project_theme = {"link": "project_theme_sector",
                       #                 "joinby": "sector_id",
                       #                 "key": "theme_id",
                       #                 "actuate": "hide",
                       #                 },
                       #org_subsector = "sector_id",
                       )

        # =====================================================================
        # (Cluster) Subsector
        #
        # tablename = "org_subsector"
        # define_table(tablename,
        #              sector_id(),
        #              Field("name", length=128,
        #                    label = T("Name"),
        #                    requires = IS_LENGTH(128),
        #                    ),
        #              Field("abrv", length=64,
        #                    notnull=True, unique=True,
        #                    label = T("Abbreviation"),
        #                    requires = IS_LENGTH(64),
        #                    ),
        #              *s3_meta_fields())

        ##CRUD strings
        # if settings.get_ui_label_cluster():
            # SUBSECTOR = T("Cluster Subsector")
            # crud_strings[tablename] = Storage(
                # label_create = T("Create Cluster Subsector"),
                # title_display = T("Cluster Subsector Details"),
                # title_list = T("Cluster Subsectors"),
                # title_update = T("Edit Cluster Subsector"),
                # label_list_button = T("List Cluster Subsectors"),
                # label_delete_button = T("Delete Cluster Subsector"),
                # msg_record_created = T("Cluster Subsector added"),
                # msg_record_modified = T("Cluster Subsector updated"),
                # msg_record_deleted = T("Cluster Subsector deleted"),
                # msg_list_empty = T("No Cluster Subsectors currently registered"))
        # else:
            # SUBSECTOR = T("Subsector")
            # crud_strings[tablename] = Storage(
                # label_create = T("Add Subsector"),
                # title_display = T("Subsector Details"),
                # title_list = T("Subsectors"),
                # title_update = T("Edit Subsector"),
                # label_list_button = T("List Subsectors"),
                # label_delete_button = T("Delete Subsector"),
                # msg_record_created = T("Subsector added"),
                # msg_record_modified = T("Subsector updated"),
                # msg_record_deleted = T("Subsector deleted"),
                # msg_list_empty = T("No Subsectors currently registered"))

        # subsector_id = S3ReusableField("subsector_id", "reference %s" % tablename,
        #                                label = SUBSECTOR,
        #                                ondelete = "SET NULL",
        #                                represent = self.org_subsector_represent,
        #                                requires = IS_EMPTY_OR(
        #                                               IS_ONE_OF(db, "org_subsector.id",
        #                                                         self.org_subsector_represent,
        #                                                         sort=True)),
        #                                sortby = "abrv",
        #                                #comment = Script to filter the sector_subsector drop down
        #                                )

        # configure("org_subsector",
        #           deduplicate = self.org_sector_duplicate,
        #           )

        # ---------------------------------------------------------------------
        # Organizations <> Sectors Link Table
        #
        tablename = "org_sector_organisation"
        define_table(tablename,
                     sector_id(),
                     self.org_organisation_id(
                         ondelete = "CASCADE",
                         ),
                     Field("lead", "boolean",
                           label = T("Lead Organization?"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Lead Organization?"),
                                                           T("If the organization is a lead for this sector."))),
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Sector"),
            title_display = T("Sector"),
            title_list = T("Sectors"),
            title_update = T("Edit Sector"),
            title_upload = T("Import Sector data"),
            label_list_button = T("List Sectors"),
            msg_record_created = T("Sector added to Organization"),
            msg_record_modified = T("Sector updated"),
            msg_record_deleted = T("Sector removed from Organization"),
            msg_list_empty = T("No Sectors found for this Organization"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("organisation_id",
                                                       "sector_id",
                                                       ),
                                            ),
                  )

        # Pass names back to global scope (s3.*)
        return {"org_sector_id": sector_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_duplicate(item):
        """ Import item de-duplication """

        data = item.data
        abrv = data.get("abrv")
        name = data.get("name")
        table = item.table
        if abrv:
            query = (table.abrv.lower() == s3_unicode(abrv).lower())
        elif name:
            query = (table.name.lower() == s3_unicode(name).lower())
        else:
            return
        duplicate = current.db(query).select(table.id,
                                             table.name,
                                             limitby=(0, 1)).first()
        if duplicate:
            if not name:
                # Reference imports use abbreviation only,
                # but name is required => retain original name
                data["name"] = duplicate.name
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
        elif not name:
            # Do not allow reference imports to create new sectors
            error = "Invalid sector: %s" % abrv
            item.accepted = False
            item.error = error
            if item.element is not None:
                item.element.set(current.xml.ATTRIBUTE["error"], error)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_sector_onaccept(form):
        """ If no abrv is set then set it from the name """

        _id = form.vars.id

        # Read the record
        db = current.db
        table = db.org_sector
        record = db(table.id == _id).select(table.abrv,
                                            table.name,
                                            limitby=(0, 1)).first()
        if not record.abrv:
            db(table.id == _id).update(abrv = record.name[:64])

    # -------------------------------------------------------------------------
    #@staticmethod
    #def org_subsector_represent(id, row=None):
    #    """ Subsector ID representation """

    #    if row:
    #        return row.name
    #    elif not id:
    #        return current.messages["NONE"]

    #    db = current.db
    #    table = db.org_subsector
    #    r = db(table.id == id).select(table.name,
    #                                  table.sector_id,
    #                                  limitby=(0, 1)
    #                                  ).first()
    #    try:
    #        sector = db(table.id == r.sector_id).select(table.abrv,
    #                                                    limitby=(0, 1)
    #                                                    ).first()
    #        if sector:
    #            return "%s: %s" % (sector.abrv, current.T(r.name))
    #        else:
    #            return current.T(r.name)
    #    except:
    #        return current.messages.UNKNOWN_OPT

# =============================================================================
class S3OrganisationServiceModel(S3Model):
    """
        Organisation Service Model
    """

    names = ("org_service",
             "org_service_id",
             "org_service_organisation",
             "org_service_location",
             #"org_service_location_service",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        organisation_id = self.org_organisation_id

        hierarchical_service_types = settings.get_org_services_hierarchical()

        # ---------------------------------------------------------------------
        # Service
        #
        tablename = "org_service"
        service_represent = S3Represent(lookup = tablename,
                                        # Questionable UX:
                                        #hierarchy = hierarchical_service_types,
                                        translate = True,
                                        )

        define_table(tablename,
                     Field("root_service", "reference org_service",
                           ondelete = "CASCADE",
                           readable = False,
                           writable = False,
                           ),
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     # This form of hierarchy may not work on all Databases:
                     Field("parent", "reference org_service",
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_service_types,
                           writable = hierarchical_service_types,
                           ),
                     s3_comments(),
                     *s3_meta_fields(),
                     on_define = lambda table: \
                        [table.parent.set_attributes(
                            represent = service_represent,
                            requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                     "org_service.id",
                                                      service_represent,
                                                      # If limiting to just 1 level of parent
                                                      #filterby="parent",
                                                      #filter_opts=(None,),
                                                      orderby="org_service.name",
                                                      )),
                            ),
                         table.root_service.set_attributes(
                            represent = service_represent,
                            ),
                         ]
                     )

        if hierarchical_service_types:
            hierarchy = "parent"
            onaccept = self.org_service_onaccept
            widget = S3HierarchyWidget(lookup = "org_service",
                                       represent = service_represent,
                                       multiple = False,
                                       leafonly = True,
                                       )
        else:
            hierarchy = None
            onaccept = None
            widget = None

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Service"),
            title_display = T("Service Details"),
            title_list = T("Services"),
            title_update = T("Edit Service"),
            title_upload = T("Import Services"),
            label_list_button = T("List Services"),
            label_delete_button = T("Delete Service"),
            msg_record_created = T("Service added"),
            msg_record_modified = T("Service updated"),
            msg_record_deleted = T("Service deleted"),
            msg_list_empty = T("No Services currently registered"))

        # Reusable Field
        service_id = S3ReusableField("service_id", "reference %s" % tablename,
                                     label = T("Services"),
                                     ondelete = "CASCADE",
                                     represent = service_represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "org_service.id",
                                                              service_represent,
                                                              sort = True,
                                                              )),
                                     sortby = "name",
                                     widget = widget,
                                     )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("parent",),
                                            ),
                  hierarchy = hierarchy,
                  onaccept = onaccept,
                  )

        # ---------------------------------------------------------------------
        # Organizations <> Services Link Table
        # - normally use org_service_location instead, but can use this simpler
        #   variant if-required
        #
        tablename = "org_service_organisation"
        define_table(tablename,
                     service_id(),
                     organisation_id(),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Service"),
            title_display = T("Service"),
            title_list = T("Services"),
            title_update = T("Edit Service"),
            label_list_button = T("List Services"),
            msg_record_created = T("Service added to Organization"),
            msg_record_modified = T("Service updated"),
            msg_record_deleted = T("Service removed from Organization"),
            msg_list_empty = T("No Services found for this Organization"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("organisation_id",
                                                       "service_id",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Service status options
        #
        service_status_opts = (("PLANNED", T("Planned")),
                               ("ACTIVE", T("Active")),
                               ("SUSPENDED", T("Suspended")),
                               ("DISCONTINUED", T("Discontinued")),
                               )

        # ---------------------------------------------------------------------
        # Organizations <> Services <> Locations Link Table
        #
        SITE = settings.get_org_site_label()

        tablename = "org_service_location"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     organisation_id(
                        default = current.auth.root_org(),
                        requires = self.org_organisation_requires(
                                    required = True,
                                    # Only allowed to add Projects for Orgs
                                    # that the user has write access to
                                    updateable = True,
                                    ),
                        ),
                     # The site where the organisation provides services:
                     # (component not instance)
                     super_link("site_id", "org_site",
                                label = SITE,
                                readable = True,
                                writable = True,
                                represent = self.org_site_represent,
                                ),
                     # Alternative 1: bare location (e.g. Lx)
                     # - can be enabled in template as required
                     self.gis_location_id(readable = False,
                                          writable = False,
                                          ),
                     # Alternative 2: free-text for location
                     # - can be enabled in template as required
                     Field("location",
                           label = T("Location"),
                           readable = False,
                           writable = False,
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     s3_date("start_date",
                             label = T("Start Date"),
                             default = "now",
                             set_min = "#org_service_location_end_date",
                             ),
                     s3_date("end_date",
                             label = T("End Date"),
                             set_max = "#org_service_location_start_date",
                             ),
                     Field("status",
                           default = "ACTIVE",
                           label = T("Status"),
                           represent = S3Represent(options=dict(service_status_opts)),
                           requires = IS_IN_SET(service_status_opts,
                                                sort = False,
                                                zero = None,
                                                ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Service"),
            title_display = T("Service Details"),
            title_list = T("Services"),
            title_update = T("Edit Service"),
            title_upload = T("Import Services"),
            label_list_button = T("List Services"),
            label_delete_button = T("Delete Service"),
            msg_record_created = T("Service added"),
            msg_record_modified = T("Service updated"),
            msg_record_deleted = T("Service deleted"),
            msg_list_empty = T("No Services currently registered"))

        # CRUD form
        service_widget = "hierarchy" if hierarchical_service_types else None
        crud_form = S3SQLCustomForm(
                        "organisation_id",
                        "site_id",
                        S3SQLInlineLink("service",
                                        field = "service_id",
                                        widget = service_widget,
                                        ),
                        "description",
                        "status",
                        "start_date",
                        "end_date",
                        "comments",
                        )

        # List fields
        list_fields = ["organisation_id",
                       "site_id",
                       "service_location_service.service_id",
                       "description",
                       "status",
                       "start_date",
                       "end_date",
                       "comments",
                       ]

        # Report axes
        report_fields = ["organisation_id",
                         "site_id",
                         "service_location_service.service_id",
                         ]
        add_report_field = report_fields.append

        # Location levels (append to list fields and report axes)
        # @ToDo: deployment_setting for Site vs Location
        levels = current.gis.get_relevant_hierarchy_levels()
        for level in levels:
            lfield = "location_id$%s" % level
            #list_fields.append(lfield)
            add_report_field(lfield)

        if "L0" in levels:
            default_row = "location_id$L0"
        elif "L1" in levels:
            default_row = "location_id$L1"
        elif "L2" in levels:
            default_row = "location_id$L2"

        # Table configuration
        configure(tablename,
                  crud_form = crud_form,
                  deduplicate = self.org_service_location_deduplicate,
                  list_fields = list_fields,
                  report_options = Storage(
                    rows = report_fields,
                    cols = report_fields,
                    fact = [(T("Number of Organizations"),
                             "count(organisation_id)",
                             ),
                            ],
                    defaults = Storage(
                        rows = default_row,
                        cols = "service_location_service.service_id",
                        fact = "count(organisation_id)",
                        totals = True,
                    )
                  ),
                  super_entity = "doc_entity",
                  )

        # Components
        self.add_components(tablename,
                            #org_service_location_service = "service_location_id",
                            org_service = {"link": "org_service_location_service",
                                           "joinby": "service_location_id",
                                           "key": "service_id",
                                           "actuate": "link",
                                           "autodelete": False,
                                           },
                            )

        # Reusable field
        service_location_id = S3ReusableField("service_location_id",
                                              "reference %s" % tablename,
                                              ondelete = "CASCADE",
                                              requires = IS_ONE_OF(current.db,
                                                            "org_service_location.id",
                                                         ),
                                              )


        # ---------------------------------------------------------------------
        # Service types at service location
        #
        tablename = "org_service_location_service"
        define_table(tablename,
                     service_location_id(),
                     service_id(),
                     #s3_comments(),
                     *s3_meta_fields()
                     )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("service_location_id",
                                                       "service_id",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"org_service_id": service_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False,
                                )

        return {"org_service_id": lambda name="service_id", **attr: \
                                         dummy(name, **attr),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def org_service_onaccept(form):
        """ Update the root_service """

        org_service_root_service(form.vars["id"])

    # -------------------------------------------------------------------------
    @staticmethod
    def org_service_location_deduplicate(item):
        """ Import item de-duplication """

        table = item.table
        data = item.data

        organisation_id = data.organisation_id
        if organisation_id:

            query = (table.organisation_id == organisation_id)

            site_id = data.site_id
            location_id = data.location_id
            location = data.location

            if site_id:
                query &= (table.site_id == site_id)
            elif location_id:
                query &= (table.location_id == location_id)
            elif location:
                query &= (table.location == location)
            else:
                query &= (table.site_id == None) & \
                         (table.location_id == None) & \
                         (table.location == None)

            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

# =============================================================================
def org_service_root_service(service_id):
    """ Update the root_service """

    db = current.db
    table = current.s3db.org_service

    # Read the record
    record = db(table.id == service_id).select(table.id,
                                               table.root_service,
                                               table.parent,
                                               ).first()

    try:
        parent = record.parent
        current_root = record.root_service
    except AttributeError:
        current.log.error("Cannot find record with service_id: %s" % service_id)
        raise

    if parent:
        # Lookup the parent record recursively
        if parent == service_id:
            # Error caused by non-unique tuids in import XSLT (fixed now,
            # but catching it anyway for the sake of a proper error message)
            raise KeyError("Service #%s showing with parent #%s" % (service_id, parent))

        new_root = org_service_root_service(parent)
    else:
        # We are the root
        new_root = service_id

    if current_root != new_root:

        # Update this record and all its descendants
        def descendants(ids):

            rows = db(table.parent.belongs(ids)).select(table.id)
            children = set(row.id for row in rows)

            if children:
                children |= descendants(children)
                return ids | children
            else:
                return ids

        # If this node doesn't have the correct root, the children
        # won't have either, so update them all
        nodes = descendants({service_id})
        db(table.id.belongs(nodes)).update(root_service=new_root)

    return new_root

# =============================================================================
class S3OrganisationTagModel(S3Model):
    """
        Organisation Tags
    """

    names = ("org_organisation_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organisation Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL, FTS
        # - can be a Triple Store for Semantic Web support
        # - can be used to add custom fields
        #
        tablename = "org_organisation_tag"
        self.define_table(tablename,
                          self.org_organisation_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3OrganisationTeamModel(S3Model):
    """
        Link table between Organisations & Teams
    """

    names = ("org_organisation_team",)

    def model(self):

        # ---------------------------------------------------------------------
        # Link table between Organisations & Teams
        #
        tablename = "org_organisation_team"
        self.define_table(tablename,
                          self.org_organisation_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          self.pr_group_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_id",
                                                            "group_id",
                                                            ),
                                                 ),
                       onaccept = self.organisation_team_onaccept,
                       ondelete = self.organisation_team_ondelete,
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def organisation_team_onaccept(form):
        """
            Onaccept of org_organisation_team:
                - update affiliations (OU relationships) of the team
        """

        try:
            record_id = form.vars.id
        except AttributeError:
            record_id = None

        if not record_id:
            return

        org_update_affiliations("org_organisation_team", record_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def organisation_team_ondelete(row):
        """
            Ondelete of org_organisation_team:
                - update affiliations (OU relationships) of the team
        """

        org_update_affiliations("org_organisation_team", row.id)

# =============================================================================
class S3OrganisationTypeTagModel(S3Model):
    """
        Organisation Type Tags
    """

    names = ("org_organisation_type_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organisation Type Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "org_organisation_type_tag"
        self.define_table(tablename,
                          self.org_organisation_type_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("organisation_type_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3SiteModel(S3Model):
    """
        Site Super-Entity
    """

    names = ("org_site",
             "org_site_requires",
             "org_site_id",
             "org_site_represent",
             )

    def model(self):

        T = current.T
        auth = current.auth

        messages = current.messages
        NONE = messages["NONE"]
        OBSOLETE = messages.OBSOLETE

        add_components = self.add_components
        set_method = self.set_method

        # =====================================================================
        # Site / Facility (ICS terminology)
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
        self.super_entity(tablename, "site_id", org_site_types,
                          # @ToDo: Make Sites Trackable (Mobile Hospitals & Warehouses)
                          #super_link("track_id", "sit_trackable"),
                          Field("code",
                                label = T("Code"),
                                length = 10, # Mayon compatibility
                                requires = IS_LENGTH(10),
                                writable = False,
                                ),
                          Field("name", notnull=True,
                                length = 64, # Mayon compatibility
                                #unique=True,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          self.gis_location_id(),
                          self.org_organisation_id(),
                          Field("obsolete", "boolean",
                                default = False,
                                label = T("Obsolete"),
                                represent = lambda opt: OBSOLETE if opt else NONE,
                                readable = False,
                                writable = False,
                                ),
                          Field("comments", "text"),
                          *S3MetaFields.owner_meta_fields())

        # ---------------------------------------------------------------------
        settings = current.deployment_settings
        org_site_label = settings.get_org_site_label()
        if settings.get_org_site_autocomplete():
            widget=S3SiteAutocompleteWidget()
            comment=DIV(_class="tooltip",
                        _title="%s|%s" % (org_site_label,
                                          messages.AUTOCOMPLETE_HELP))
        else:
            widget = None
            comment = None

        org_site_represent = org_SiteRepresent(show_link=True)

        site_id = lambda: self.super_link("site_id", "org_site",
                                          comment = comment,
                                          #default = auth.user.site_id if auth.is_logged_in() else None,
                                          label = org_site_label,
                                          orderby = "org_site.name",
                                          #readable = True,
                                          represent = org_site_represent,
                                          widget = widget,
                                          #writable = True,
                                          )

        # Custom Method for S3SiteAutocompleteWidget
        set_method("org", "site",
                   method = "search_ac",
                   action = self.site_search_ac)

        # Custom Method for S3AddPersonWidget
        # @ToDo: One for HRMs
        set_method("org", "site",
                   method = "site_contact_person",
                   action = self.site_contact_person)

        # Custom Method to Assign HRs
        # - done in instances
        #set_method("org", "site",
        #           method = "assign",
        #           action = self.hrm_AssignMethod(component="human_resource_site"))

        list_fields = ["id",
                       "code",
                       "instance_type",
                       "name",
                       "organisation_id",
                       "location_id",
                       ]

        self.configure(tablename,
                       context = {"location": "location_id",
                                  "organisation": "organisation_id",
                                  "org_group": "organisation_id$group_membership.group_id",
                                  },
                       list_fields = list_fields,
                       # Include site_id in JSON (for filterOptionsS3):
                       json_fields = list_fields + ["site_id"],
                       onaccept = self.org_site_onaccept,
                       ondelete_cascade = self.org_site_ondelete_cascade,
                       referenced_by = [(auth.settings.table_user_name,
                                         "site_id")],
                       )

        # Components
        add_components(tablename,
                       # Facility Types
                       org_facility_type = {"link": "org_site_facility_type",
                                            "joinby": "site_id",
                                            "key": "facility_type_id",
                                            "actuate": "hide",
                                            },

                       # Locations
                       org_site_location = ({"name": "location",
                                             "joinby": "site_id",
                                            },
                                            ),

                       # Local Names
                       org_site_name = {"name": "name",
                                        "joinby": "site_id",
                                        },

                       # Status
                       org_site_status = {"name": "status",
                                          "joinby": "site_id",
                                          "multiple": False,
                                          },

                       # Tags
                       org_site_tag = {"name": "tag",
                                       "joinby": "site_id",
                                       },

                       # Assets
                       asset_asset = "site_id",

                       # Documents
                       doc_document = "site_id",
                       doc_image = "site_id",

                       # Human Resources
                       # - direct component (suitable for Create/List)
                       hrm_human_resource = "site_id",
                       # - via link table (suitable for Assign)
                       hrm_human_resource_site = "site_id",

                       # Inventory
                       inv_inv_item = "site_id",
                       inv_recv = "site_id",
                       inv_send = "site_id",

                       # Groups: Coalitions/Networks
                       org_group = {"link": "org_site_org_group",
                                    "joinby": "site_id",
                                    "key": "group_id",
                                    "actuate": "hide",
                                    },
                       # Format for InlineComponent/filter_widget
                       org_site_org_group = "site_id",

                       # Needs
                       req_need = {"name": "needs",
                                   "link": "req_need_site",
                                   "joinby": "site_id",
                                   "key": "need_id",
                                   "multiple": False,
                                   },

                       # Requests
                       req_req = "site_id",
                       req_commit = "site_id",

                       # Shifts
                       #org_site_shift = "site_id",
                       hrm_shift = {"link": "org_site_shift",
                                    "joinby": "site_id",
                                    "key": "shift_id",
                                    "actuate": "replace",
                                    },

                       # Procurement Plans
                       proc_plan = "site_id",
                       )

        # Pass names back to global scope (s3.*)
        return {"org_site_id": site_id,
                "org_site_represent": org_site_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def org_site_onaccept(form):
        """
            Create the code from the name
        """

        name = form.vars.name
        if not name:
            return
        code_len = current.deployment_settings.get_org_site_code_len()
        temp_code = name[:code_len].upper()
        db = current.db
        site_table = db.org_site
        query = (site_table.code == temp_code)
        row = db(query).select(site_table.id,
                               limitby=(0, 1)).first()
        if row:
            code = temp_code
            temp_code = None
            wildcard_bit = 1
            length = len(code)
            max_wc_bit = pow(2, length)
            while not temp_code and wildcard_bit < max_wc_bit:
                wildcard_posn = []
                for w in range(length):
                    if wildcard_bit & pow(2, w):
                        wildcard_posn.append(length - (1 + w))
                wildcard_bit += 1
                code_list = S3SiteModel.getCodeList(code, wildcard_posn)
                temp_code = S3SiteModel.returnUniqueCode(code, wildcard_posn,
                                                         code_list)
        if temp_code:
            db(site_table.site_id == form.vars.site_id).update(code=temp_code)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_site_ondelete_cascade(form):
        """
            Update realm entity in all related HRs

            @todo: clean up records which RESTRICT the site_id
        """

        site_id = form.site_id
        htable = current.s3db.hrm_human_resource
        query = (htable.site_id == site_id)

        db = current.db
        rows = db(query).select(htable.id)
        db(query).update(site_id = None)
        current.auth.set_realm_entity(htable, rows, force_update=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def getCodeList(code, wildcard_posn=[]):
        """
            Called by org_site_onaccept
        """

        temp_code = ""
        # Inject the wildcard charater in the right positions
        for posn in range(len(code)):
            if posn in wildcard_posn:
                temp_code += "%"
            else:
                temp_code += code[posn]
        # Now set up the db call
        db = current.db
        site_table = db.org_site
        query = site_table.code.like(temp_code)
        rows = db(query).select(site_table.id,
                                site_table.code)
        # Extract the rows in the database to provide a list of used codes
        codeList = []
        for record in rows:
            codeList.append(record.code)
        return codeList

    # -------------------------------------------------------------------------
    @staticmethod
    def returnUniqueCode(code, wildcard_posn=[], code_list=[]):
        """
            Called by org_site_onaccept
        """

        # Select the replacement letters with numbers first and then
        # followed by the letters in least commonly used order
        replacement_char = "1234567890ZQJXKVBWPYGUMCFLDHSIRNOATE"
        rep_posn = [0] * len(wildcard_posn)
        finished = False
        while (not finished):
            # Find the next code to try
            temp_code = ""
            r = 0
            for posn in range(len(code)):
                if posn in wildcard_posn:
                    temp_code += replacement_char[rep_posn[r]]
                    r += 1
                else:
                    temp_code += code[posn]
            if temp_code not in code_list:
                return temp_code
            # Set up the next rep_posn
            p = 0
            while (p < len(wildcard_posn)):
                if rep_posn[p] == 35: # the maximum number of replacement characters
                    rep_posn[p] = 0
                    p += 1
                else:
                    rep_posn[p] = rep_posn[p] + 1
                    break
            # If no new permutation of replacement characters has been found
            if p == len(wildcard_posn):
                return None

    # -------------------------------------------------------------------------
    @staticmethod
    def site_contact_person(r, **attr):
        """
            JSON lookup method for S3AddPersonWidget
        """

        site_id = r.id
        if not site_id:
            r.error(400, "No id provided!")

        db = current.db
        s3db = current.s3db
        ltable = s3db.hrm_human_resource_site
        htable = db.hrm_human_resource
        query = (ltable.site_id == site_id) & \
                (ltable.site_contact == True) & \
                (ltable.human_resource_id == htable.id)
        person = db(query).select(htable.person_id,
                                  limitby=(0, 1)).first()

        if person:
            attr = dict(attr)
            attr["person_id"] = person.person_id
            return s3db.pr_person_lookup(r, **attr)
        else:
            current.response.headers["Content-Type"] = "application/json"
            output = json.dumps(None, separators=SEPARATORS)
            return output

    # -------------------------------------------------------------------------
    @staticmethod
    def site_search_ac(r, **attr):
        """
            JSON search method for S3SiteAutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        response = current.response
        resource = r.resource
        settings = current.deployment_settings

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        _vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term" instead of "value"
        # (old JQuery Autocomplete uses "q" instead of "value")
        value = _vars.term or _vars.value or _vars.q or None

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower().strip()

        if not value:
            r.error(400, "Missing option! Require value")

        # Construct query
        query = (FS("name").lower().like(value + "%"))

        # Add template specific search criteria
        extra_fields = settings.get_org_site_autocomplete_fields()
        for field in extra_fields:
            if "addr_street" in field:
                # Need to be able to get through the street number
                query |= (FS(field).lower().like("%" + value + "%"))
            else:
                query |= (FS(field).lower().like(value + "%"))

        resource.add_filter(query)

        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        limit = int(_vars.limit or MAX_SEARCH_RESULTS)
        if (not limit or limit > MAX_SEARCH_RESULTS) and resource.count() > MAX_SEARCH_RESULTS:
            output = [
                {"label": str(current.T("There are more than %(max)s results, please input more characters.") % \
                    {"max": MAX_SEARCH_RESULTS})}
                ]
        else:
            # default fields to return
            fields = ["name",
                      "site_id",
                      ]

            # Add template specific fields to return
            fields += extra_fields

            rows = resource.select(fields,
                                   start=0,
                                   limit=limit,
                                   orderby="name",
                                   as_rows=True)
            output = []
            append = output.append
            for row in rows:
                # Populate record
                _row = row.get("org_site", row)
                record = {"id": _row.site_id,
                          "name": _row.name,
                          }

                # Populate fields only if present
                org = row.get("org_organisation.name", None)
                if org:
                    record["org"] = org
                L1 = row.get("gis_location.L1", None)
                if L1:
                    record["L1"] = L1
                L2 = row.get("gis_location.L2", None)
                if L2:
                    record["L2"] = L2
                L3 = row.get("gis_location.L3", None)
                if L3:
                    record["L3"] = L3
                L4 = row.get("gis_location.L4", None)
                if L4:
                    record["L4"] = L4
                addr_street = row.get("gis_location.addr_street", None)
                if addr_street:
                    record["addr"] = addr_street

                # Populate match information (if applicable)
                s3_set_match_strings(record, value)
                append(record)

        response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

# =============================================================================
class S3SiteDetailsModel(S3Model):
    """ Extra optional details for Sites """

    names = ("org_site_status",
             "org_site_org_group",
             )

    def model(self):

        T = current.T

        define_table = self.define_table
        super_link = self.super_link

        settings = current.deployment_settings
        last_contacted = settings.get_org_site_last_contacted()

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        facility_status_opts = {
            1: T("Normal"),
            2: T("Compromised"),
            3: T("Evacuating"),
            4: T("Closed"),
            99: T("No Response"),
        }

        power_supply_type_opts = {
            1: T("Grid"),
            2: T("Generator"),
            98: T("Other"),
            99: T("None"),
        }

        # ---------------------------------------------------------------------
        # Site Status
        #
        tablename = "org_site_status"
        define_table(tablename,
                     # Component not instance
                     super_link("site_id", "org_site"),
                     Field("facility_status", "integer",
                           requires = IS_EMPTY_OR(
                                      IS_IN_SET(facility_status_opts)),
                           label = T("Facility Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       facility_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                     s3_date("date_reopening",
                             label = T("Estimated Reopening Date"),
                             readable = False,
                             writable = False,
                             ),
                     Field("power_supply_type", "integer",
                           label = T("Power Supply Type"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(power_supply_type_opts,
                                                  zero=None)),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       power_supply_type_opts.get(opt,
                                                                  UNKNOWN_OPT)),
                     s3_date("last_contacted",
                             label = T("Last Contacted"),
                             readable = last_contacted,
                             writable = last_contacted,
                             ),
                     *s3_meta_fields())

        # CRUD Strings
        site_label = settings.get_org_site_label()
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add %(site_label)s Status") % {"site_label": site_label},
            title_display = T("%(site_label)s Status") % {"site_label": site_label},
            title_list = T("%(site_label)s Status") % {"site_label": site_label},
            title_update = T("Edit %(site_label)s Status") % {"site_label": site_label},
            label_list_button = T("List %(site_label)s Status") % {"site_label": site_label},
            msg_record_created = T("%(site_label)s Status added") % {"site_label": site_label},
            msg_record_modified = T("%(site_label)s Status updated") % {"site_label": site_label},
            msg_record_deleted = T("%(site_label)s Status deleted") % {"site_label": site_label},
            msg_list_empty = T("There is no status for this %(site_label)s yet. Add %(site_label)s Status.") % {"site_label": site_label},
            )

        # ---------------------------------------------------------------------
        # Sites <> Coalitions link table
        #
        tablename = "org_site_org_group"
        define_table(tablename,
                     # Component not instance
                     super_link("site_id", "org_site"),
                     self.org_group_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3SiteNameModel(S3Model):
    """
        Site Names model
        - local names/acronyms for Sites/Facilities
    """

    names = ("org_site_name",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "org_site_name"
        self.define_table(tablename,
                          # Component not instance
                          self.super_link("site_id", "org_site"),
                          s3_language(empty = False),
                          Field("name_l10n",
                                label = T("Local Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("language",
                                                            "site_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3SiteShiftModel(S3Model):
    """
        Site Shifts model
    """

    names = ("org_site_shift",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Shifts for a Site
        #
        tablename = "org_site_shift"
        self.define_table(tablename,
                          # Component not instance
                          self.super_link("site_id", "org_site"),
                          self.hrm_shift_id(ondelete = "CASCADE"),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        #site_label = current.deployment_settings.get_org_site_label()
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("New Shift"),
        #    title_display = T("Shift Details"),
        #    title_list = T("Shifts"),
        #    title_update = T("Edit Shift"),
        #    #title_upload = T("Import Shift data"),
        #    label_list_button = T("List Shifts"),
        #    msg_record_created = T("Shift added to %(site_label)s") % {"site_label": site_label},
        #    msg_record_modified = T("Shift updated"),
        #    msg_record_deleted = T("Shift removed from %(site_label)s") % {"site_label": site_label},
        #    msg_list_empty = T("No Shifts found for this %(site_label)s") % {"site_label": site_label},
        #    )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3SiteTagModel(S3Model):
    """
        Site Tags
    """

    names = ("org_site_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Site Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "org_site_tag"
        self.define_table(tablename,
                          # Component not instance
                          self.super_link("site_id", "org_site"),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary=("site_id",
                                                          "tag",
                                                          ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3SiteLocationModel(S3Model):
    """
        Site Location Model
        - Locations served by a Site/Facility
    """

    names = ("org_site_location",)

    def model(self):

        T = current.T
        auth = current.auth

        # ---------------------------------------------------------------------
        # Sites <> Locations Link Table
        #
        tablename = "org_site_location"
        self.define_table(tablename,
                          # Component not instance
                          self.super_link("site_id", "org_site",
                                          label = current.deployment_settings.get_org_site_label(),
                                          instance_types = auth.org_site_types,
                                          orderby = "org_site.name",
                                          realms = auth.permission.permitted_realms("org_site",
                                                                                    method="create"),
                                          not_filterby = "obsolete",
                                          not_filter_opts = (True,),
                                          readable = True,
                                          writable = True,
                                          represent = self.org_site_represent,
                                          ),
                          self.gis_location_id(
                            #represent = self.gis_LocationRepresent(sep=", "),
                            represent = S3Represent(lookup="gis_location"),
                            requires = IS_LOCATION(),
                            widget = S3LocationAutocompleteWidget()
                          ),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        site_label = current.deployment_settings.get_org_site_label()
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("New Location"),
            title_display = T("Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_upload = T("Import Location data"),
            label_list_button = T("List Locations"),
            msg_record_created = T("Location added to %(site_label)s") % {"site_label": site_label},
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location removed from %(site_label)s") % {"site_label": site_label},
            msg_list_empty = T("No Locations found for this %(site_label)s") % {"site_label": site_label})

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("site_id",
                                                            "location_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3FacilityModel(S3Model):
    """
        Generic Site
    """

    names = ("org_facility_type",
             "org_facility",
             "org_site_facility_type",
             "org_facility_type_id", # Passed to global for s3translate
             "org_facility_geojson",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        messages = current.messages
        NONE = messages["NONE"]
        OBSOLETE = messages.OBSOLETE

        hierarchical_facility_types = settings.get_org_facility_types_hierarchical()

        # ---------------------------------------------------------------------
        # Facility Types (generic)
        #
        tablename = "org_facility_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("parent", "reference org_facility_type", # This form of hierarchy may not work on all Databases
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_facility_types,
                           writable = hierarchical_facility_types,
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        type_represent = S3Represent(lookup = tablename,
                                     # Questionable UX:
                                     #hierarchy = hierarchical_facility_types,
                                     translate = True,
                                     )

        if hierarchical_facility_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_facility_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="org_facility_type.name"))
            list_fields = [(T("Type"), "parent"),
                           #(T("SubType"), "name"),
                           "name",
                           "comments",
                           ]
        else:
            hierarchy = None
            list_fields = ["name",
                           "comments",
                           ]

        # CRUD strings
        # @ToDo: Flexible Labelling: 'Facility, 'Place', 'Site'
        ADD_FAC = T("Create Facility Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_FAC,
            title_display = T("Facility Type Details"),
            title_list = T("Facility Types"),
            title_update = T("Edit Facility Type"),
            title_upload = T("Import Facility Types"),
            label_list_button = T("List Facility Types"),
            label_delete_button = T("Delete Facility Type"),
            msg_record_created = T("Facility Type added"),
            msg_record_modified = T("Facility Type updated"),
            msg_record_deleted = T("Facility Type deleted"),
            msg_list_empty = T("No Facility Types currently registered"))

        facility_type_id = S3ReusableField("facility_type_id",
            "reference %s" % tablename,
            label = T("Facility Type"),
            ondelete = "CASCADE",
            represent = type_represent,
            # Only used by org_site_facility_type
            requires = IS_ONE_OF(db, "org_facility_type.id",
                                 type_represent,
                                 sort = True,
                                 ),
            sortby = "name",
            comment = S3PopupLink(c = "org",
                                  f = "facility_type",
                                  label = ADD_FAC,
                                  title = T("Facility Type"),
                                  tooltip = T("If you don't see the Type in the list, you can add a new one by clicking link 'Create Facility Type'."),
                                  ),
            )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  hierarchy = hierarchy,
                  list_fields = list_fields,
                  )

        # ---------------------------------------------------------------------
        # Facilities (generic)
        #
        if settings.get_org_facility_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "org_facility.code"),
                                         ])
        else:
            code_requires = IS_LENGTH(10)

        tablename = "org_facility"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("code", length=10, # Mayon compatibility
                           #notnull=True,
                           label = T("Code"),
                           # Deployments that don't wants office codes can hide them
                           #readable=False, writable=False,
                           represent = lambda v: v or NONE,
                           requires = code_requires,
                           ),
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                        ),
                     self.gis_location_id(),
                     Field("opening_times",
                           label = T("Opening Times"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("contact",
                           label = T("Contact"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("phone1",
                           label = T("Phone 1"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("phone2",
                           label = T("Phone 2"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("email",
                           label = T("Email"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     Field("website",
                           label = T("Website"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: OBSOLETE if opt else NONE,
                           readable = False,
                           writable = False,
                           ),
                     Field("main_facility", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field.Method("inv", org_site_has_inv),
                     Field.Method("assets", org_site_has_assets),
                     Field.Method("reqs", org_site_top_req_priority),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Facility"),
            title_display = T("Facility Details"),
            title_list = T("Facilities"),
            title_update = T("Edit Facility"),
            title_map = T("Map of Facilities"),
            title_upload = T("Import Facilities"),
            label_list_button = T("List Facilities"),
            label_delete_button = T("Delete Facility"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility deleted"),
            msg_list_empty = T("No Facilities currently registered"))

        text_fields = ["name",
                       "code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       ]

        report_fields = ["name",
                         "site_facility_type.facility_type_id",
                         "organisation_id",
                         ]

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()
        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)

        if hierarchical_facility_types:
            type_filter = S3HierarchyFilter("site_facility_type.facility_type_id",
                                            #label = T("Type"),
                                            )
        else:
            type_filter = S3OptionsFilter("site_facility_type.facility_type_id",
                                          # @ToDo: Introspect need for header based on # records
                                          #header = True,
                                          #label = T("Type"),
                                          # Doesn't support translation
                                          #represent = "%(name)s",
                                          )


        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         #_class = "filter-search",
                         ),
            type_filter,
            S3OptionsFilter("organisation_id",
                            # @ToDo: Introspect need for header based on # records
                            #header = True,
                            #label = T("Organization"),
                            # Doesn't support l10n
                            #represent = "%(name)s",
                            ),
            S3LocationFilter("location_id",
                             # @ToDo: Display by default in Summary Views but not others?
                             #hidden = True,
                             #label = T("Location"),
                             levels = levels,
                             ),
            ]

        groups = settings.get_org_groups()
        if groups:
            report_fields.append("site_org_group.group_id")
            filter_widgets.insert(1,
               S3OptionsFilter("site_org_group.group_id",
                               # @ToDo: Introspect need for header based on # records
                               #header = True,
                               represent = "%(name)s",
                               ))

        if settings.get_org_regions():
            report_fields.append("organisation_id$region_id")
            if settings.get_org_regions_hierarchical():
                filter_widget =  S3HierarchyFilter("organisation_id$region_id",
                                                   #hidden = True,
                                                   label = T("Region"),
                                                   )
            else:
                filter_widget = S3OptionsFilter("organisation_id$region_id",
                                                #hidden = True,
                                                label = T("Region"),
                                                )
            filter_widgets.insert(1, filter_widget)

        if settings.has_module("inv"):
            report_fields.append((T("Inventory"), "inv"))
            filter_widgets.append(
                S3OptionsFilter("inv",
                                label = T("Inventory"),
                                options = {True: T("Yes"),
                                           False: T("No"),
                                           },
                                cols = 2,
                                ))

        if settings.has_module("asset"):
            report_fields.append((T("Assets"), "assets"))
            filter_widgets.append(
                S3OptionsFilter("assets",
                                label = T("Assets"),
                                options = {True: T("Yes"),
                                           False: T("No"),
                                           },
                                cols = 2,
                                ))

        if settings.has_module("req"):
            # @ToDo: Report should show Total Open/Closed Requests
            report_fields.append((T("Highest Priority Open Requests"), "reqs"))
            filter_widgets.append(
                S3OptionsFilter("reqs",
                                label = T("Highest Priority Open Requests"),
                                options = lambda: self.req_priority_opts,
                                cols = 3,
                                ))

        report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = [(T("Number of Facilities"), "count(id)"),
                    (T("List of Facilities"), "list(name)"),
                    ],
            defaults = Storage(rows = lfield, # Lowest-level of hierarchy
                               cols = "site_facility_type.facility_type_id",
                               fact = "count(id)",
                               totals = True,
                               chart = "barchart:rows",
                               ),
            )

        # Custom Form
        if hierarchical_facility_types:
            type_widget = "hierarchy"
        else:
            type_widget = "groupedopts"
        crud_form = S3SQLCustomForm("name",
                                    "code",
                                    S3SQLInlineLink(
                                          "facility_type",
                                          label = T("Facility Type"),
                                          field = "facility_type_id",
                                          widget = type_widget,
                                          cols = 3,
                                    ),
                                    "organisation_id",
                                    "location_id",
                                    "opening_times",
                                    "contact",
                                    "phone1",
                                    "phone2",
                                    "email",
                                    "website",
                                    #S3SQLInlineComponent(
                                    #    "status",
                                    #    label = T("Status"),
                                    #    fields = ["last_contacted"],
                                    #    multiple = False,
                                    #),
                                    "obsolete",
                                    "comments",
                                    )

        list_fields = ["name",
                       "code",
                       "site_facility_type.facility_type_id",
                       "organisation_id",
                       "location_id",
                       "opening_times",
                       "contact",
                       "phone1",
                       "phone2",
                       "email",
                       "website",
                       "comments",
                       ]

        configure(tablename,
                  context = {"location": "location_id",
                             "organisation": "organisation_id",
                             "org_group": "organisation_id$group_membership.group_id",
                             "request": "req.id",
                             },
                  crud_form = crud_form,
                  deduplicate = self.org_facility_duplicate,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.org_facility_onaccept,
                  realm_components = ("contact_emergency",
                                      "physical_description",
                                      "config",
                                      "image",
                                      "req",
                                      "send",
                                      "human_resource_site",
                                      "note",
                                      "contact",
                                      "role",
                                      "asset",
                                      "commit",
                                      "inv_item",
                                      "document",
                                      "recv",
                                      "address",
                                      ),
                  report_options = report_options,
                  super_entity = ("doc_entity", "org_site", "pr_pentity"),
                  update_realm = True,
                  )

        # Custom Method to Assign HRs
        self.set_method("org", "facility",
                        method = "assign",
                        action = self.hrm_AssignMethod(component="human_resource_site"))

        # ---------------------------------------------------------------------
        # Link Table: Sites <> Facility Types
        # - currently just used for Facilities but can be easily used by other
        #   Site types as-required
        #
        tablename = "org_site_facility_type"
        define_table(tablename,
                     # Component not instance
                     super_link("site_id", "org_site",
                                instance_types = current.auth.org_site_types,
                                label = settings.get_org_site_label(),
                                orderby = "org_site.name",
                                represent = self.org_site_represent,
                                not_filterby = "obsolete",
                                not_filter_opts = (True,),
                                readable = True,
                                writable = True,
                                ),
                     facility_type_id(),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {"org_facility_type_id": facility_type_id,
                "org_facility_geojson": self.org_facility_geojson,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        form_vars = form.vars

        if "main_facility" in form_vars and form_vars.main_facility:
            # Should be only one main facility per organisation
            record_id = form_vars.id
            if record_id:
                db = current.db
                table = current.s3db.org_facility
                organisation_id = form_vars.organisation_id
                if not organisation_id:
                    query = table.id == record_id
                    row = db(query).select(table.organisation_id,
                                           limitby=(0, 1)).first()
                    if row:
                        organisation_id = row.organisation_id
                if organisation_id:
                    query = (table.id != record_id) & \
                            (table.organisation_id == organisation_id)
                    db(query).update(main_facility = False)

        org_update_affiliations("org_facility", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def org_facility_duplicate(item):
        """ Import item de-duplication """

        data = item.data
        name = data.get("name")
        org = data.get("organisation_id")
        #address = data.get("address")

        table = item.table
        query = (table.name.lower() == s3_unicode(name).lower())
        if org:
            # Either same Org or no Org defined yet
            query = query & ((table.organisation_id == org) | \
                             (table.organisation_id == None))
        #if address:
        #    query = query & (table.address == address)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -----------------------------------------------------------------------------
    @staticmethod
    def org_facility_geojson(jsonp=True,
                             decimals=4):
        """
            Produce a static GeoJSON[P] feed of Facility data
            Designed to be run on a schedule to serve a high-volume website
            - current.task.schedule_task("s3db_task", "org_facility_geojson", period=86400, repeats=0)
        """

        from shapely.geometry import Point
        from ..geojson import dumps

        db = current.db
        s3db = current.s3db
        stable = s3db.org_facility
        ltable = db.org_site_facility_type
        ttable = db.org_facility_type
        gtable = db.gis_location
        #ntable = s3db.req_need

        # Limit the number of decimal places
        formatter = ".%sf" % decimals

        # All Facilities
        query = (stable.deleted != True) & \
                (stable.obsolete != True) & \
                (gtable.id == stable.location_id)
        #lquery = (ntable.deleted != True) & \
        #         (ntable.site_id == stable.site_id)
        left = [#ntable.on(lquery),
                ltable.on(stable.site_id == ltable.site_id),
                ttable.on(ttable.id == ltable.facility_type_id),
                ]
        facs = db(query).select(stable.id,
                                stable.name,
                                ttable.name,
                                stable.comments,
                                stable.opening_times,
                                stable.phone1,
                                stable.phone2,
                                stable.email,
                                stable.website,
                                #ntable.needs,
                                gtable.addr_street,
                                gtable.L1,
                                gtable.L4,
                                gtable.lat,
                                gtable.lon,
                                left=left,
                                )
        features = []
        append = features.append
        for f in facs:
            g = f.gis_location
            x = g.lon
            y = g.lat
            if x is None or y is None:
                continue
            x = float(format(x, formatter))
            y = float(format(y, formatter))
            shape = Point(x, y)
            # Compact Encoding
            geojson = dumps(shape, separators=SEPARATORS)
            o = f.org_facility
            properties = {"id": o.id,
                          "name": o.name,
                          }
            if f.get("org_facility_type.name"):
                properties["type"] = f["org_facility_type.name"]
            if o.opening_times:
                properties["open"] = o.opening_times
            if o.comments:
                properties["comments"] = o.comments
            if g.addr_street:
                properties["addr"] = g.addr_street
            if g.L1:
                # Encode smaller if-possible
                L1 = g.L1
                #if L1 == "New York":
                #    properties["L1"] = "NY"
                #elif L1 == "New Jersey":
                #    properties["L1"] = "NJ"
                #else:
                properties["L1"] = L1
            if g.L4:
                properties["L4"] = g.L4
            if o.phone1:
                properties["ph1"] = o.phone1
            if o.phone2:
                properties["ph2"] = o.phone2
            if o.email:
                properties["email"] = o.email
            if o.website:
                properties["web"] = o.website
            #n = f.req_site_needs
            #if n:
            #    if n.needs:
            #        needs = json.loads(n.needs)
            #        if "urgent" in needs:
            #            properties["urgent"] = needs["urgent"]
            #        if "need" in needs:
            #            properties["need"] = needs["need"]
            #        if "no" in needs:
            #            properties["no"] = needs["no"]
            f = {"type": "Feature",
                 "properties": properties,
                 "geometry": json.loads(geojson)
                 }
            append(f)
        data = {"type": "FeatureCollection",
                "features": features
                }
        output = json.dumps(data, separators=SEPARATORS)
        if jsonp:
            filename = "facility.geojsonp"
            output = "grid(%s)" % output
        else:
            filename = "facility.geojson"
        path = os.path.join(current.request.folder,
                            "static", "cache",
                            filename)
        File = open(path, "w")
        File.write(output)
        File.close()

# -----------------------------------------------------------------------------
def org_facility_rheader(r, tabs=None):
    """
        RHeader for facilities when doing a req_match
    """

    T = current.T
    s3db = current.s3db

    # Need to use this format as otherwise /inv/incoming?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)
    r.record = record
    r.table = s3db[tablename]

    tabs = [(T("Details"), None)]
    try:
        tabs = tabs + s3db.req_tabs(r)
    except:
        pass
    try:
        tabs = tabs + s3db.inv_tabs(r)
    except:
        pass
    rheader_fields = [["name"], ["location_id"]]
    rheader = S3ResourceHeader(rheader_fields, tabs)(r)
    return rheader

# =============================================================================
class S3RoomModel(S3Model):
    """
        Rooms are a location within a Site
        - used by Asset module
    """

    names = ("org_room",
             "org_room_id",
             )

    def model(self):

        T = current.T
        db = current.db

        # ---------------------------------------------------------------------
        # Rooms (for Sites)
        # @ToDo: Validate to ensure that rooms are unique per facility
        #
        tablename = "org_room"
        self.define_table(tablename,
                          self.org_site_id(), # site_id
                          Field("name", length=128, notnull=True,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(128),
                                            ],
                                ),
                          *s3_meta_fields())

        # CRUD strings
        ADD_ROOM = T("Create Room")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_ROOM,
            title_display = T("Room Details"),
            title_list = T("Rooms"),
            title_update = T("Edit Room"),
            label_list_button = T("List Rooms"),
            label_delete_button = T("Delete Room"),
            msg_record_created = T("Room added"),
            msg_record_modified = T("Room updated"),
            msg_record_deleted = T("Room deleted"),
            msg_list_empty = T("No Rooms currently registered"))

        room_comment = DIV(
                           S3PopupLink(c = "org",
                                       f = "room",
                                       label = ADD_ROOM,
                                       tooltip = T("Select a Room from the list or click 'Create Room'"),
                                       ),
                           # Filters Room based on site
                           SCRIPT(
'''$.filterOptionsS3({
 'trigger':'site_id',
 'target':'room_id',
 'lookupPrefix':'org',
 'lookupResource':'room'
})''')
                           )

        # Reusable field for other tables to reference
        represent = S3Represent(lookup=tablename)
        room_id = S3ReusableField("room_id", "reference %s" % tablename,
                                  label = T("Room"),
                                  ondelete = "SET NULL",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "org_room.id",
                                                          represent
                                                          )),
                                  sortby = "name",
                                  comment = room_comment,
                                  )

        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        # Pass names back to global scope (s3.*)
        return {"org_room_id": room_id,
                }

# =============================================================================
class S3OfficeModel(S3Model):

    names = ("org_office",
             "org_office_type",
             "org_office_type_id",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        messages = current.messages
        NONE = messages["NONE"]
        OBSOLETE = messages.OBSOLETE

        settings = current.deployment_settings
        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        organisation_id = self.org_organisation_id
        super_link = self.super_link

        auth = current.auth
        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)
        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Office Types
        #
        tablename = "org_office_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
                                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_OFFICE_TYPE = T("Create Office Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_OFFICE_TYPE,
            title_display = T("Office Type Details"),
            title_list = T("Office Types"),
            title_update = T("Edit Office Type"),
            label_list_button = T("List Office Types"),
            label_delete_button = T("Delete Office Type"),
            msg_record_created = T("Office Type added"),
            msg_record_modified = T("Office Type updated"),
            msg_record_deleted = T("Office Type deleted"),
            msg_list_empty = T("No Office Types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        office_type_id = S3ReusableField("office_type_id", "reference %s" % tablename,
                            label = T("Office Type"),
                            ondelete = "SET NULL",
                            represent = represent,
                            requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_office_type.id",
                                                  represent,
                                                  sort=True,
                                                  filterby="organisation_id",
                                                  filter_opts=filter_opts,
                                                  )),
                            sortby = "name",
                            comment = S3PopupLink(c = "org",
                                                  f = "office_type",
                                                  label = ADD_OFFICE_TYPE,
                                                  title = T("Office Type"),
                                                  tooltip = T("If you don't see the Type in the list, you can add a new one by clicking link 'Create Office Type'."),
                                                  ),
                            )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  )

        # Components
        add_components(tablename,
                       # Tags
                       org_office_type_tag = {"name": "tag",
                                              "joinby": "office_type_id",
                                              },
                       )

        # ---------------------------------------------------------------------
        # Offices
        #
        if settings.get_org_office_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "org_office.code"),
                                         ])
        else:
            code_requires = IS_LENGTH(10)

        tablename = "org_office"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("code", length=10, # Mayon compatibility
                           label = T("Code"),
                           # Deployments that don't wants office codes can hide them
                           #readable=False,
                           #writable=False,
                           requires = code_requires,
                           ),
                     organisation_id(
                         requires = org_organisation_requires(required=True,
                                                              updateable=True),
                         ),
                     office_type_id(
                                    #readable = False,
                                    #writable = False,
                                    ),
                     self.gis_location_id(),
                     Field("phone1",
                           label = T("Phone 1"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("phone2",
                           label = T("Phone 2"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("email",
                           label = T("Email"),
                           represent = lambda v: v or "",
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     Field("fax",
                           label = T("Fax"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: OBSOLETE if opt else NONE,
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_fields = ["name",
                       "code",
                       "organisation_id",
                       "office_type_id",
                       "location_id",
                       "phone1",
                       "phone2",
                       "email",
                       "fax",
                       "obsolete",
                       "comments",
                       ]

        crud_form = S3SQLCustomForm(*crud_fields)

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Office"),
            title_display = T("Office Details"),
            title_list = T("Offices"),
            title_update = T("Edit Office"),
            title_upload = T("Import Offices"),
            title_map = T("Map of Offices"),
            label_list_button = T("List Offices"),
            label_delete_button = T("Delete Office"),
            msg_record_created = T("Office added"),
            msg_record_modified = T("Office updated"),
            msg_record_deleted = T("Office deleted"),
            msg_list_empty = T("No Offices currently registered"))

        if settings.get_org_branches():
            ORGANISATION = T("Organization/Branch")
            comment = T("Search for office by organization or branch.")
            org_filter = S3HierarchyFilter("organisation_id",
                                           label = ORGANISATION,
                                           comment = comment,
                                           #hidden = True,
                                           )
        else:
            ORGANISATION = T("Organization")
            comment = T("Search for office by organization.")
            org_filter = S3OptionsFilter("organisation_id",
                                         label = ORGANISATION,
                                         comment = comment,
                                         # Doesn't support l10n
                                         #represent = "%(name)s",
                                         #hidden = True,
                                         )

        text_fields = ["name",
                       "code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       ]

        report_fields = ["name",
                         "organisation_id", # Filtered in Component views
                         "office_type_id",
                         ]

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()
        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)

        list_fields = list(report_fields)
        list_fields += [(T("Address"), "location_id$addr_street"),
                        "phone1",
                        "email",
                        ]

        filter_widgets = [
                S3TextFilter(text_fields,
                             label = T("Search"),
                             #_class = "filter-search",
                             ),
                #S3OptionsFilter("office_type_id",
                #                label = T("Type"),
                #                #hidden = True,
                #                ),
                org_filter,
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = levels,
                                 #hidden = True,
                                 ),
                ]

        report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = ["count(id)",
                    "list(name)",
                    ],
            defaults = Storage(rows = lfield, # Lowest-level of hierarchy
                               cols = "office_type_id",
                               fact = "count(id)",
                               totals = True,
                               chart = "spectrum:rows",
                               ),
            )


        configure(tablename,
                  context = {"location": "location_id",
                             "organisation": "organisation_id",
                             "org_group": "organisation_id$group_membership.group_id",
                             },
                  crud_form = crud_form,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.org_office_onaccept,
                  realm_components = ("contact_emergency",
                                      "config",
                                      "image",
                                      "req",
                                      "send",
                                      "human_resource_site",
                                      "note",
                                      "contact",
                                      "role",
                                      "asset",
                                      "commit",
                                      "inv_item",
                                      "document",
                                      "recv",
                                      "address",
                                      ),
                  report_options = report_options,
                  super_entity = ("doc_entity", "pr_pentity", "org_site"),
                  update_realm = True,
                  )

        # Pass names back to global scope (s3.*)
        return {"org_office_type_id": office_type_id,
                }

    # ---------------------------------------------------------------------
    @staticmethod
    def org_office_onaccept(form):
        """
            * Update Affiliation and Realms
            * Process injected fields
        """

        # Affiliation, record ownership and component ownership
        org_update_affiliations("org_office", form.vars)

# =============================================================================
class S3OfficeTypeTagModel(S3Model):
    """
        Office Type Tags
    """

    names = ("org_office_type_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Office Type Tags
        # - Key-Value extensions
        # - can be used to provide conversions to external systems, such as:
        #   * HXL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "org_office_type_tag"
        self.define_table(tablename,
                          self.org_office_type_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())



        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("office_type_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def org_organisation_address(row):
    """ The address of the first office """

    if hasattr(row, "org_organisation"):
        row = row.org_organisation
    try:
        organisation_id = row.id
    except AttributeError:
        # not available
        return current.messages["NONE"]

    db = current.db
    s3db = current.s3db

    otable = s3db.org_office
    gtable = s3db.gis_location
    query = (otable.deleted != True) & \
            (otable.organisation_id == organisation_id) & \
            (otable.location_id == gtable.id)
    row = db(query).select(gtable.addr_street, limitby=(0, 1)).first()

    return row.addr_street if row else current.messages["NONE"]

# =============================================================================
def org_organisation_logo(org,
                          #type="png",
                          ):
    """
        Return a logo of the organisation with the given org, if one exists

        The org can either be the id of the organisation
               or a Row of the organisation

        @ToDo: The type can either be png or bmp and is the format of the saved image
    """

    if not org:
        return None

    s3db = current.s3db
    if isinstance(org, Row):
        # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
        record = org
    else:
        table = s3db.org_organisation
        record = current.db(table.id == org).select(table.name,
                                                    table.acronym,
                                                    table.logo,
                                                    limitby = (0, 1),
                                                    ).first()

    if record and record.logo:
        #format = None
        #if type == "bmp":
        #    format = "bmp"
        size = (None, 60)
        image = s3db.pr_image_library_represent(record.logo, size=size)
        url_small = URL(c="default", f="download", args=image)
        if record.acronym is None or record.acronym == "":
            alt = "%s logo" % record.name
        else:
            alt = "%s logo" % record.acronym
        logo = IMG(_src=url_small,
                   _alt=alt,
                   _height=60,
                   )
        return logo
    return ""

# =============================================================================
def org_parents(organisation_id, path=None):
    """
        Lookup the parent organisations of a branch organisation

        @param organisation_id: the organisation's record ID

        @return: list of ids of the parent organisations, starting with the immediate parent
    """

    if not organisation_id:
        return path
    if path is None:
        path = []

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = s3db.org_organisation.with_alias("org_branch_organisation")
    ltable = s3db.org_organisation_branch

    query = (btable.id == organisation_id)
    join = (ltable.deleted != True) & \
           (btable.deleted != True) & \
           (otable.deleted != True) & \
           (btable.id == ltable.branch_id) & \
           (otable.id == ltable.organisation_id)
    row = db(query & join).select(otable.id,
                                  limitby=(0, 1)).first()

    if row is not None:
        # Parent exists
        organisation_id = row.id
        path.insert(0, organisation_id)
        return org_parents(organisation_id, path)
    else:
        # This is the root org
        return path

# =============================================================================
def org_root_organisation(organisation_id):
    """
        Lookup the root organisation of a branch organisation

        @param organisation_id: the organisation's record ID

        @return: id of the root organisation,
                 or None if no root organisation can be found
    """

    if not organisation_id:
        return None

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = s3db.org_organisation.with_alias("org_branch_organisation")
    ltable = s3db.org_organisation_branch

    query = (btable.id == organisation_id)
    join = (ltable.deleted != True) & \
           (btable.deleted != True) & \
           (otable.deleted != True) & \
           (btable.id == ltable.branch_id) & \
           (otable.id == ltable.organisation_id)
    row = db(query & join).select(otable.id,
                                  limitby=(0, 1)).first()

    if row is not None:
        # Parent exists
        return org_root_organisation(row.id)
    else:
        # This is the root org
        return organisation_id

# =============================================================================
def org_root_organisation_name(organisation_id):
    """
        Lookup the root organisation name of a branch organisation

        @param organisation_id: the organisation's record ID

        @return: name of the root organisation,
                 or None if no root organisation can be found
    """

    if not organisation_id:
        return None

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = s3db.org_organisation.with_alias("org_branch_organisation")
    ltable = s3db.org_organisation_branch

    query = (btable.id == organisation_id)
    join = (ltable.deleted != True) & \
           (btable.deleted != True) & \
           (otable.deleted != True) & \
           (btable.id == ltable.branch_id) & \
           (otable.id == ltable.organisation_id)
    row = db(query & join).select(otable.id,
                                  limitby=(0, 1)).first()

    if row is not None:
        # Parent exists
        return org_root_organisation_name(row.id)
    else:
        # This is the root org
        row = db(otable.id == organisation_id).select(otable.name,
                                                      limitby=(0, 1)).first()
        if row:
            return row.name

# =============================================================================
def org_organisation_requires(required = False,
                              realms = None,
                              updateable = False
                              ):
    """
        @param required: Whether the selection is optional or mandatory
        @param realms: Whether the list should be filtered to just those
                       belonging to a list of realm entities
        @param updateable: Whether the list should be filtered to just those
                           which the user has Write access to
        @ToDo: Option to remove Branches
        @ToDo: Option to only include Branches
    """

    requires = IS_ONE_OF(current.db, "org_organisation.id",
                         org_OrganisationRepresent(),
                         realms = realms,
                         updateable = updateable,
                         orderby = "org_organisation.name",
                         sort = True)
    if not required:
        requires = IS_EMPTY_OR(requires)
    return requires

# =============================================================================
def org_region_options(zones=False):
    """
        Get all options for region IDs

        @param zones: select only zones if True, otherwise only regions
        @return: dict of {org_region.id: representation}
    """

    represent = current.s3db.org_region_represent
    if represent is None:
        return {}

    db = current.db
    rtable = db.org_region
    if zones:
        query = (rtable.parent == None)
    else:
        query = (rtable.parent != None)
    query &= (rtable.deleted != True)
    rows = db(query).select(rtable.id, rtable.name)
    options = represent.bulk(None, rows=rows)
    options.pop(None, None) # Remove the None options
    return options

# =============================================================================
class org_OrganisationRepresent(S3Represent):
    """ Representation of Organisations """

    def __init__(self,
                 show_link = False,
                 linkto = None,
                 parent = True,
                 acronym = True,
                 multiple = False,
                 skip_dt_orderby = False,
                 ):

        self.acronym = acronym

        settings = current.deployment_settings
        # Translation uses org_organisation_name & not T()
        translate = settings.get_L10n_translate_org_organisation()
        if translate:
            self.language = language = current.session.s3.language
            if language == current.deployment_settings.get_L10n_default_language():
                translate = False

        if skip_dt_orderby:
            # org/branch component which doesn't like the left join
            self.skip_dt_orderby = True

        if parent and not settings.get_org_branches():
            parent = False

        if parent or translate:
            self.lookup_rows = self.custom_lookup_rows
            self.parent = parent
            fields = None
        else:
            # Can use standard lookup of fields
            self.parent = False
            fields = ["name",
                      "acronym",
                      ]

        super(org_OrganisationRepresent,
              self).__init__(lookup="org_organisation",
                             fields=fields,
                             show_link=show_link,
                             linkto=linkto,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for organisation rows, does a
            left join with the parent organisation. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the organisation IDs
        """

        s3db = current.s3db
        otable = s3db.org_organisation

        fields = [otable.id,
                  otable.name,
                  otable.acronym,
                  ]

        show_parent = self.parent
        if show_parent:
            btable = s3db.org_organisation_branch
            ptable = otable.with_alias("org_parent_organisation")

            fields.append(ptable.name)

            left = [btable.on((btable.branch_id == otable.id) &
                              (btable.deleted != True)),
                    ptable.on(ptable.id == btable.organisation_id),
                    ]
        else:
            left = []

        if self.translate:
            ltable = s3db.org_organisation_name

            left.append(ltable.on((ltable.organisation_id == otable.id) & \
                                  (ltable.deleted != True) & \
                                  (ltable.language == self.language)))

            fields.extend([ltable.name_l10n, ltable.acronym_l10n])

            if show_parent:
                lptable = ltable.with_alias("org_parent_organisation_name")
                fields.append(lptable.name_l10n)

                left.append(lptable.on(lptable.organisation_id == btable.organisation_id))

        count = len(values)
        if count == 1:
            query = (otable.id == values[0])
        else:
            query = (otable.id.belongs(values))

        rows = current.db(query).select(left=left, limitby=(0, count), *fields)
        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the org_organisation Row
        """

        show_parent = self.parent
        if self.translate:
            # Custom Row (with the name_l10n left-joined)
            name = row["org_organisation_name.name_l10n"] or \
                   row["org_organisation.name"]
            acronym = row["org_organisation_name.acronym_l10n"] or \
                      row["org_organisation.acronym"]
            if show_parent:
                parent = row["org_parent_organisation_name.name_l10n"] or \
                         row["org_parent_organisation.name"]
        else:
            if show_parent:
                # Custom Row (with the parent left-joined)
                name = row["org_organisation.name"]
                acronym = row["org_organisation.acronym"]
                parent = row["org_parent_organisation.name"]
            else:
                # Standard row (from fields)
                name = row["name"]
                acronym = row["acronym"]

        if not name:
            return self.default
        if self.acronym and acronym:
            name = "%s (%s)" % (name, acronym)
        if show_parent and parent:
            name = "%s > %s" % (parent, name)

        return s3_str(name)

    # -------------------------------------------------------------------------
    def dt_orderby(self, field, direction, orderby, left):
        """
            Custom orderby logic for datatables

            @ToDo: Support for self.translate = True
                   need to handle the inevitable NULL values which vary in
                   order by DB, although perhaps DB handling doesn't matter
                   here.
        """

        otable = current.s3db.org_organisation
        left.add(otable.on(field == otable.id))

        if self.parent:
            # If we use a hierarchical representation, order by root
            # organisation name first because it appears before the
            # branch name:
            rotable = otable.with_alias("org_root_organisation")
            left.add(rotable.on(otable.root_organisation == rotable.id))

            orderby.extend(["org_root_organisation.name%s" % direction,
                            "org_organisation.name%s" % direction,
                            ])
        #elif self.translate:
        #    # Order by translated name
        #    orderby.append("org_organisation_name.name_l10n%s" % direction)
        else:
            # Otherwise: order by organisation name
            # e.g. the branches component view
            orderby.append("org_organisation.name%s" % direction)

# =============================================================================
class org_SiteRepresent(S3Represent):
    """ Representation of Sites """

    def __init__(self,
                 show_link = False,
                 multiple = False,
                 show_type = True,
                 ):

        settings = current.deployment_settings

        # Translation uses org_site_name & not T()
        translate = settings.get_L10n_translate_org_site()
        language = current.session.s3.language
        if language == settings.get_L10n_default_language():
            translate = False

        if show_type or show_link or translate:
            # Need a custom lookup
            self.lookup_rows = self.custom_lookup_rows

        self.L10n = {}
        self.show_type = show_type

        super(org_SiteRepresent, self).__init__(lookup = "org_site",
                                                fields = ["name"],
                                                show_link = show_link,
                                                translate = translate,
                                                multiple = multiple,
                                                )

    # -------------------------------------------------------------------------
    def bulk(self, values, rows=None, list_type=False, show_link=True, include_blank=True):
        """
            Represent multiple values as dict {value: representation}

            @param values: list of values
            @param rows: the referenced rows (if values are foreign keys)
            @param show_link: render each representation as link
            @param include_blank: Also include a blank value

            @return: a dict {value: representation}
        """

        show_link = show_link and self.show_link
        if show_link and not rows:
            # Retrieve the rows
            rows = self.lookup_rows(None, values)

        self._setup()

        # Get the values
        if rows and self.table:
            values = [row["org_site.site_id"] for row in rows]
        else:
            values = [values] if type(values) is not list else values

        # Lookup the representations
        if values:
            labels = self._lookup(values, rows=rows)
            if show_link:
                link = self.link
                rows = self.rows
                labels = {k: link(k, v, rows.get(k)) for k, v in labels.items()}
            for v in values:
                if v not in labels:
                    labels[v] = self.default
        else:
            labels = {}
        if include_blank:
            labels[None] = self.none
        return labels

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for site rows, does a left join with any
            instance_types found.
            Parameters key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the site IDs
        """

        db = current.db
        s3db = current.s3db
        stable = s3db.org_site

        show_type = self.show_type
        show_link = self.show_link

        count = len(values)
        if count == 1:
            value = values[0]
            query = (stable.site_id == value)
        else:
            query = (stable.site_id.belongs(values))
        limitby = (0, count)

        fields = [stable.site_id,
                  stable.name,
                  ]
        if show_type or show_link:
            fields.append(stable.instance_type)

        rows = db(query).select(limitby=limitby, *fields)
        self.queries += 1

        if show_type:

            # Collect the site_ids
            site_ids = set(row.site_id for row in rows)

            # Retrieve the facility type links
            ltable = s3db.org_site_facility_type
            query = ltable.site_id.belongs(site_ids)
            links = db(query).select(ltable.site_id,
                                     ltable.facility_type_id,
                                     )

            # Collect all type IDs and type IDs per site_id
            all_types = set()
            facility_types = {}

            for link in links:

                facility_type_id = link.facility_type_id
                all_types.add(facility_type_id)

                site_id = link.site_id
                if site_id in facility_types:
                    facility_types[site_id].append(facility_type_id)
                else:
                    facility_types[site_id] = [facility_type_id]

            # Bulk-represent all type IDs
            # (stores the representations in the S3Represent)
            ltable.facility_type_id.represent.bulk(list(all_types))

            # Add the list of corresponding type IDs to each row
            for row in rows:
                row.facility_types = facility_types.get(row.site_id) or []

        if show_link:

            # Collect site_ids per instance type
            site_ids = {}
            for row in rows:
                instance_type = row.instance_type
                if instance_type in site_ids:
                    site_ids[instance_type].add(row.site_id)
                else:
                    site_ids[instance_type] = {row.site_id}

            # Retrieve site ID / instance ID pairs per instance_type
            instance_ids = {}
            for instance_type in site_ids:
                table = s3db.table(instance_type)
                if not table:
                    continue
                query = table.site_id.belongs(site_ids[instance_type])
                instances = db(query).select(table._id,
                                             table.site_id,
                                             )
                self.queries += 1
                key = table._id.name
                for instance in instances:
                    instance_ids[instance.site_id] = instance[key]

            # Add the instance ID to each row
            for row in rows:
                row.instance_id = instance_ids.get(row.site_id)

        if self.translate:

            table = s3db.org_site_name
            query = (table.deleted == False) & \
                    (table.language == current.session.s3.language)
            if count == 1:
                query &= (table.site_id == value)
            else:
                query &= (table.site_id.belongs(values))
            self.l10n = db(query).select(table.site_id,
                                         table.name_l10n,
                                         limitby = (0, count),
                                         ).as_dict(key="site_id")

        return rows

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            @param k: the key (site_id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        if row:
            try:
                instance_type = row["org_site.instance_type"]
                instance_id = row.instance_id
            except (AttributeError, KeyError):
                return v
            else:
                c, f = instance_type.split("_", 1)
                return A(v, _href=URL(c=c, f=f, args=[instance_id],
                                      # remove the .aaData extension in paginated views
                                      extension=""
                                      ))
        else:
            # We have no way to determine the linkto
            return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the org_site Row
        """

        if self.translate:
            l10n_row = self.l10n.get(row["org_site.site_id"])
            if l10n_row:
                name = l10n_row["name_l10n"]
            else:
                name = row["org_site.name"]
        else:
            name = row["org_site.name"]

        if not name:
            return self.default

        if self.show_type:
            instance_type = row["org_site.instance_type"]
            facility_types = row.get("facility_types")

            if facility_types:
                ltable = current.s3db.org_site_facility_type
                represent = ltable.facility_type_id.represent
                type_names = represent.multiple(facility_types)
                name = "%s (%s)" % (name, type_names)
            else:
                instance_type = current.auth.org_site_types.get(instance_type, None)
                if instance_type:
                    name = "%s (%s)" % (name, instance_type)

        return s3_str(name)

# =============================================================================
class org_SiteCheckInMethod(S3Method):
    """
        Custom Method to allow a trackable resource to check-in/out to a Site
        e.g. using a Barcode scanner (for the person's pe_label)
    """

    def apply_method(self, r, **attr):
        """
            Entry point for the REST API

            @param r: the S3Request
            @param attr: controller parameters
        """

        output = {}

        representation = r.representation
        if representation == "html":
            if r.http == "GET":
                output = self.check_in_form(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        elif representation == "json":
            if r.http == "POST":
                output = self.submit_ajax(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def check_in_form(self, r, **attr):
        """
            Render the check-in page

            @param r: the S3Request
            @param attr: controller parameters
        """

        T = current.T
        response = current.response
        settings = current.deployment_settings

        output = {"title": T("Check-in")}

        request_vars = r.get_vars
        label = request_vars.get("label")

        # Identify the person
        person = None
        pe_label = None
        if label is not None:
            person = self.get_person(label)
            if person is None:
                response.error = T("No person found with this ID number")

        # Get the person data
        person_data = None
        if person:
            status = self.status(r, person)
            if not status.get("valid"):
                person = None
                response.error = status.get("error",
                                    T("Person not allowed to check-in/out at this site"))
            else:
                pe_label = person.pe_label
                person_data = self.ajax_data(person, status)

        # Standard form fields and data
        formfields = [Field("label",
                            label = T("ID"),
                            requires = IS_NOT_EMPTY(error_message=T("Enter or scan an ID")),
                            widget = self.label_input,
                            ),
                      Field("person",
                            label = "",
                            writable = False,
                            default = "",
                            ),
                      Field("status",
                            label = "",
                            writable = False,
                            default = "",
                            ),
                      Field("info",
                            label = "",
                            writable = False,
                            default = "",
                            ),
                      ]

        # Initial data
        data = {"id": "",
                "label": pe_label,
                "person": "",
                "status": "",
                "info": "",
                }

        # Hidden inputs
        hidden = {
            "data": json.dumps(person_data)
        }

        # Form buttons
        check_btn = INPUT(_class = "tiny secondary button check-btn",
                          _name = "check",
                          _type = "submit",
                          _value = T("Check ID"),
                          )
        check_in_btn = INPUT(_class = "tiny primary button check-in-btn",
                             _name = "check_in",
                             _type = "submit",
                             _value = T("Check-in"),
                             )
        check_out_btn = INPUT(_class = "tiny primary button check-out-btn",
                              _name = "check_out",
                              _type = "submit",
                              _value = T("Check-out"),
                              )

        buttons = [check_btn, check_in_btn, check_out_btn]
        buttons.append(A(T("Cancel"),
                         _class="cancel-action action-lnk",
                         _href=r.url(vars={}),
                         ))

        # Generate the form and add it to the output
        formstyle = settings.get_ui_formstyle()
        widget_id = "check-in-form"
        table_name = "site_check_in"
        form = SQLFORM.factory(record = data if person else None,
                               showid = False,
                               formstyle = formstyle,
                               table_name = table_name,
                               buttons = buttons,
                               hidden = hidden,
                               _id = widget_id,
                               *formfields)
        output["form"] = form

        # Inject JS
        options = {"tableName": table_name,
                   "ajaxURL": r.url(None,
                                    representation = "json",
                                    ),
                   "noPictureAvailable": s3_str(T("No picture available")),
                   "statusCheckedIn": s3_str(T("checked-in")),
                   "statusCheckedOut": s3_str(T("checked-out")),
                   "statusNone": s3_str(current.messages["NONE"]),
                   "statusLabel": s3_str(T("Status")),
                   }
        self.inject_js(widget_id, options)

        response.view = "org/site_check_in.html"

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def label_input(field, value, **attributes):
        """
            Custom widget for label input, providing a clear-button
            (for ease of use on mobile devices where no ESC exists)

            @param field: the Field
            @param value: the current value
            @param attributes: HTML attributes

            NB: expects Foundation theme
        """

        from gluon.sqlhtml import StringWidget

        default = {"value": (value is not None and str(value)) or ""}
        attr = StringWidget._attributes(field, default, **attributes)

        placeholder = current.T("Enter or scan ID")
        attr["_placeholder"] = placeholder

        postfix = ICON("fa fa-close")

        widget = DIV(DIV(INPUT(**attr),
                         _class="small-11 columns",
                         ),
                     DIV(SPAN(postfix, _class="postfix clear-btn"),
                         _class="small-1 columns",
                         ),
                     _class="row collapse",
                     )

        return widget

    # -------------------------------------------------------------------------
    def submit_ajax(self, r, **attr):
        """
            Perform ajax actions, accepts a JSON object as input:
                {m: the method (check|check-in|check-out)
                 l: the PE label
                 }

            @param r: the S3Request
            @param attr: controller parameters
        """

        T = current.T

        # Load JSON data from request body
        s = r.body
        s.seek(0)
        try:
            data = json.load(s)
        except (ValueError, TypeError):
            r.error(400, current.ERROR.BAD_REQUEST)

        # Initialize
        output = {}
        error = None
        alert = None
        alert_type = 'success'

        # Identify the person
        label = data.get("l")
        person = self.get_person(label)

        if person is None:
            error = T("No person found with this ID number")
        else:
            status = self.status(r, person)
            if not status.get("valid"):
                person = None
                error = status.get("error",
                            T("Person not allowed to check-in/out at this site"))

        if person:
            method = data.get("m")
            if method == "check":

                ajax_data = self.ajax_data(person, status)
                output.update(ajax_data)

            elif method == "check-in":

                check_in_allowed = status.get("check_in_allowed")

                if not check_in_allowed or status.get("info") is not None:
                    ajax_data = self.ajax_data(person, status)
                    output.update(ajax_data)

                if status.get("status") == 1:
                    alert = T("Client was already checked-in")
                    alert_type = "warning"
                else:
                    if not check_in_allowed:
                        alert = T("Check-in denied")
                        alert_type = "error"
                    else:
                        self.check_in(r, person)
                        output["s"] = 1
                        alert = T("Checked-in successfully!")

            elif method == "check-out":

                check_out_allowed = status.get("check_out_allowed")

                if not check_out_allowed or status.get("info") is not None:
                    ajax_data = self.ajax_data(person, status)
                    output.update(ajax_data)

                if status.get("status") == 2:
                    alert = T("Client was already checked-out")
                    alert_type = "warning"
                else:
                    if not check_out_allowed:
                        alert = T("Check-out denied")
                        alert_type = "error"
                    else:
                        self.check_out(r, person)
                        output["s"] = 2
                        alert = T("Checked-out successfully!")

            else:
                r.error(405, current.ERROR.BAD_METHOD)

        # Input-field error
        if error:
            output["e"] = s3_str(error)

        # Page alert
        if alert:
            output["m"] = (s3_str(alert), alert_type)

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(output)

    # -------------------------------------------------------------------------
    @classmethod
    def ajax_data(cls, person, status):
        """
            Convert person details and current check-in status into
            a JSON-serializable dict for Ajax-actions

            @param person: the person record
            @param status: the status dict (from status())
        """

        person_details = cls.person_details(person)
        output = {"d": s3_str(person_details),
                  "i": True if status.get("check_in_allowed") else False,
                  "o": True if status.get("check_out_allowed") else False,
                  "s": status.get("status"),
                  }

        profile_picture = cls.profile_picture(person)
        if profile_picture:
            output["p"] = profile_picture

        info = status.get("info")
        if info:
            output["a"] = s3_str(info)

        return output

    # -------------------------------------------------------------------------
    def get_person(self, label):
        """
            Get the person record for the label

            @param label: the PE label
        """

        s3db = current.s3db

        # Fields to extract
        fields = ["id",
                  "pe_id",
                  "pe_label",
                  "first_name",
                  "middle_name",
                  "last_name",
                  "date_of_birth",
                  "gender",
                  "location_id",
                  ]

        query = (FS("pe_label") == label)
        presource = s3db.resource("pr_person",
                                  components=[],
                                  filter = query,
                                  )
        rows = presource.select(fields,
                                start = 0,
                                limit = 1,
                                as_rows = True,
                                )

        return rows[0] if rows else None

    # -------------------------------------------------------------------------
    @staticmethod
    def status(r, person):
        """
            Check the check-in/out status for a person at this site,
            invokes the check_in_status hook for the site resource
            to obtain current status information.

            @param r: the S3Request
            @param site_id: the site ID
            @param person: the person record

            @return: a dict like:
                     {valid: True|False, whether the person record is valid
                             for check-in/out at this site
                      status: 1 = currently checked-in at this site
                              2 = currently checked-out from this site
                              None = no previous status available
                      info: string or XML to render in info-field
                      check_in_allowed: True|False
                      check_out_allowed: True|False
                      error: error message to display in check-in form
                      }
        """

        # Default values
        result =  {"valid": True,
                   "status": None,
                   "info": None,
                   "check_in_allowed": True,
                   "check_out_allowed": True,
                   "error": None,
                   }

        check_in_status = current.s3db.get_config(r.tablename,
                                                  "check_in_status",
                                                  )
        if check_in_status:
            status = check_in_status(r.record, person)
        else:
            status = None

        if isinstance(status, dict):
            result.update(status)
        else:
            result["status"] = status

        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def person_details(person):
        """
            Format the person details

            @param person: the person record (Row)
        """

        T = current.T

        name = s3_fullname(person)
        dob = person.date_of_birth
        if dob:
            dob = S3DateTime.date_represent(dob)
            details = "%s (%s %s)" % (name, T("Date of Birth"), dob)
        else:
            details = name

        return SPAN(details, _class = "person-details")

    # -------------------------------------------------------------------------
    @staticmethod
    def profile_picture(person):
        """
            Get the profile picture URL for a person

            @param person: the person record (Row)

            @return: the profile picture URL (relative URL), or None if
                     no profile picture is available for that person
        """

        try:
            pe_id = person.pe_id
        except AttributeError:
            return None

        table = current.s3db.pr_image
        query = (table.pe_id == pe_id) & \
                (table.profile == True) & \
                (table.deleted != True)
        row = current.db(query).select(table.image, limitby=(0, 1)).first()

        if row:
            return URL(c="default", f="download", args=row.image)
        else:
            return None

    # -------------------------------------------------------------------------
    def check_in(self, r, person):
        """
            Check-in the person at this site, invokes the site_check_in
            hook for the site resource

            @param r: the S3Request
            @param person: the person record
        """

        s3db = current.s3db
        ptable = s3db.pr_person

        from s3 import S3Trackable
        person_id = person.id
        record = r.record

        # Update tracking location for the person
        tracker = S3Trackable(ptable, record_id=person_id)
        tracker.set_location(record.location_id)

        # Callback
        site_check_in = s3db.get_config(r.tablename, "site_check_in")
        if site_check_in:
            site_check_in(record.site_id, person_id)

    # -------------------------------------------------------------------------
    def check_out(self, r, person):
        """
            Check-out the person from this site, invokes the site_check_out
            hook for the site resource

            @param r: the S3Request
            @param person: the person record
        """

        s3db = current.s3db
        ptable = s3db.pr_person

        from s3 import S3Trackable
        person_id = person.id

        record = r.record

        tracker = S3Trackable(ptable, record_id=person_id)
        tracker.set_location(person.location_id)

        site_check_out = s3db.get_config(r.tablename, "site_check_out")
        if site_check_out:
            site_check_out(record.site_id, person_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_js(widget_id, options):
        """
            Helper function to inject static JS and instantiate the
            client-side widget

            @param widget_id: the node ID where to instantiate the widget
            @param options: dict of widget options (JSON-serializable)
        """

        s3 = current.response.s3
        appname = current.request.application

        # Static JS
        scripts = s3.scripts
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.sitecheckin.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.ui.sitecheckin.min.js" % appname
        scripts.append(script)

        # Instantiate widget
        scripts = s3.jquery_ready
        script = '''$('#%(id)s').siteCheckIn(%(options)s)''' % \
                 {"id": widget_id, "options": json.dumps(options)}
        if script not in scripts:
            scripts.append(script)

# =============================================================================
def org_site_has_assets(row, tablename="org_facility"):
    """ Whether a Site has Assets """

    if not current.deployment_settings.has_module("asset"):
        return False

    if hasattr(row, tablename):
        row = row[tablename]
    try:
        record_id = row.id
    except AttributeError:
        return None

    s3db = current.s3db
    atable = s3db.asset_asset
    stable = s3db[tablename]

    query = (atable.deleted != True) & \
            (stable.id == record_id) & \
            (atable.site_id == stable.site_id)

    asset = current.db(query).select(atable.id,
                                     limitby=(0, 1)).first()

    if asset:
        return True
    else:
        return False

# =============================================================================
def org_site_has_inv(row, tablename="org_facility"):
    """ Whether a Site has Inventory """

    if not current.deployment_settings.has_module("inv"):
        return False

    if hasattr(row, tablename):
        row = row[tablename]
    try:
        record_id = row.id
    except AttributeError:
        return None

    s3db = current.s3db
    itable = s3db.inv_inv_item
    stable = s3db[tablename]

    query = (itable.deleted != True) & \
            (stable.id == record_id) & \
            (itable.site_id == stable.site_id) & \
            (itable.quantity > 0)

    inv = current.db(query).select(itable.id,
                                   limitby=(0, 1)).first()

    if inv:
        return True
    else:
        return False

# =============================================================================
def org_site_top_req_priority(row, tablename="org_facility"):
    """ Highest priority of open requests for a site """

    if not current.deployment_settings.has_module("req"):
        return None

    try:
        from .req import REQ_STATUS_COMPLETE
    except ImportError:
        return None

    if hasattr(row, tablename):
        row = row[tablename]
    try:
        record_id = row.id
    except AttributeError:
        return None

    s3db = current.s3db
    rtable = s3db.req_req
    stable = s3db[tablename]

    query = (rtable.deleted != True) & \
            (stable.id == record_id) & \
            (rtable.site_id == stable.site_id) & \
            (rtable.fulfil_status != REQ_STATUS_COMPLETE) & \
            (rtable.is_template == False)

    req = current.db(query).select(rtable.id,
                                   rtable.priority,
                                   orderby=~rtable.priority,
                                   limitby=(0, 1)).first()

    if req:
        return req.priority
    else:
        return None

# =============================================================================
def org_rheader(r, tabs=None):
    """ Organisation/Office/Facility/Group page headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    # Need to use this format as otherwise req_match?viewing=org_office.x
    # doesn't have an rheader
    tablename, record = s3_rheader_resource(r)

    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    s3db = current.s3db

    # These 2 needed for req_match
    r.record = record
    r.table = table = s3db[tablename]
    settings = current.deployment_settings

    if tablename == "org_organisation":
        # Tabs
        if not tabs:
            skip_branches = False

            if settings.get_org_offices_tab():
                offices = (T("Offices"), "office")
            else:
                offices = None

            # If a filter is being applied to the Organisations, amend the tabs accordingly
            type_filter = current.request.get_vars.get("organisation_type.name",
                                                       None)
            if type_filter:
                if type_filter == "Supplier":
                    skip_branches = True
                    tabs = [(T("Basic Details"), None, {"native": 1}),
                            offices,
                            (T("Warehouses"), "warehouse"),
                            (T("Contacts"), "human_resource"),
                            ]
                elif type_filter == "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency":
                    tabs = [(T("Basic Details"), None, {"native": 1}),
                            offices,
                            (T("Warehouses"), "warehouse"),
                            (T("Contacts"), "human_resource"),
                            (T("Projects"), "project"),
                            ]
                else:
                    if type_filter == "Training Center":
                        # e.g.RMSAmericas
                        skip_branches = True
                    tabs = [(T("Basic Details"), None, {"native": 1}),
                            ]
            else:
                if settings.get_org_facilities_tab():
                    facilities =  (T("Facilities"), "facility")
                else:
                    facilities = None

                tabs = [(T("Basic Details"), None),
                        offices,
                        (T("Warehouses"), "warehouse"),
                        facilities,
                        (T("Staff & Volunteers"), "human_resource"),
                        (T("Assets"), "asset"),
                        #(T("Tasks"), "task"),
                        ]
                append_tab = tabs.append
                if settings.get_org_projects_tab():
                    append_tab((T("Projects"), "project"))
                if settings.get_org_tags():
                    append_tab((T("Tags"), "tag"))
                if settings.get_org_resources_tab():
                    append_tab((T("Resources"), "resource"))
                if settings.get_org_needs_tab():
                    append_tab((T("Needs"), "needs"))
                if settings.get_org_service_locations():
                    append_tab((T("Service Locations"), "service_location"))
                if settings.get_org_documents_tab():
                    append_tab((T("Documents"), "document"))
                if settings.get_org_pdf_card_configs():
                    append_tab((T("Cards"), "card_config"))

                # Org-specific categories for beneficiary/case management
                if settings.has_module("br"):
                    labels = s3db.br_terminology()
                    if settings.get_br_needs_org_specific():
                        append_tab((T("Need Types"), "need"))
                    if settings.get_br_assistance_themes() and \
                       settings.get_br_assistance_themes_org_specific():
                        append_tab((labels.THEMES, "assistance_theme"))

                # Org Role Manager always last
                append_tab((T("User Roles"), "roles"))

            if settings.get_L10n_translate_org_organisation():
                tabs.insert(1, (T("Local Names"), "name"))

            # Use branches?
            if settings.get_org_branches() and not skip_branches:
                if settings.get_org_branches_tree_view():
                    presentation = "hierarchy"
                else:
                    presentation = "branch"
                tabs.insert(1, (T("Branches"), presentation))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV()
        logo = org_organisation_logo(record)

        record_data = TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                               ),
                            )

        db = current.db
        record_id = record.id

        if record.acronym:
            record_data.append(TR(TH("%s: " % table.acronym.label),
                                  record.acronym))

        if record.root_organisation != record_id:
            btable = s3db.org_organisation_branch
            query = (btable.branch_id == record.id) & \
                    (btable.organisation_id == table.id)
            row = db(query).select(table.id,
                                   table.name,
                                   limitby=(0, 1)
                                   ).first()
            if row:
                record_data.append(TR(TH("%s: " % T("Branch of")),
                                      A(row.name, _href=URL(args=[row.id, "read"])),
                                      ))

        if settings.get_org_organisation_type_rheader():
            ltable = s3db.org_organisation_organisation_type
            query = (ltable.organisation_id == record_id) & \
                    (ltable.deleted == False)
            rows = db(query).select(ltable.organisation_type_id)
            if rows:
                if settings.get_org_organisation_types_multiple():
                    label = T("Types")
                else:
                    label = T("Type")
                record_data.append(TR(TH("%s: " % label),
                                      ltable.organisation_type_id.represent.multiple([row.organisation_type_id for row in rows])))

        if settings.get_org_sector_rheader():
            ltable = s3db.org_sector_organisation
            query = (ltable.organisation_id == record_id) & \
                    (ltable.deleted == False)
            rows = db(query).select(ltable.sector_id)
            if rows:
                if settings.get_ui_label_cluster():
                    label = T("Clusters")
                else:
                    label = T("Sectors")
                record_data.append(TR(TH("%s: " % label),
                                      ltable.sector_id.represent.multiple([row.sector_id for row in rows])))

        if settings.get_org_country() and record.country:
            record_data.append(TR(TH("%s: " % table.country.label),
                                  table.country.represent(record.country)))

        if record.website:
            record_data.append(TR(TH("%s: " % table.website.label),
                                  A(record.website, _href=record.website)))

        if logo:
            rheader.append(TABLE(TR(TD(logo),
                                    TD(record_data),
                                    )))
        else:
            rheader.append(record_data)

        rheader.append(rheader_tabs)

    elif tablename in ("org_office", "org_facility"):

        tabs = [(T("Basic Details"), None),
                #(T("Contact Data"), "contact"),
                ]
        append_tab = tabs.append

        SHIFTS = settings.get_org_facility_shifts()
        if settings.get_L10n_translate_org_site():
            append_tab((T("Local Names"), "name"))
        if settings.get_org_tags():
            append_tab((T("Tags"), "tag"))
        if settings.has_module("hrm") and \
           (r.controller != "inv" or settings.get_inv_facility_manage_staff()):
            STAFF = settings.get_hrm_staff_label()
            append_tab((STAFF, "human_resource"))
            if not SHIFTS:
                permitted = current.auth.s3_has_permission
                if permitted("update", tablename, r.id) and \
                   permitted("create", "hrm_human_resource_site"):
                    append_tab((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))
        if SHIFTS:
            append_tab((T("Shifts"), "shift"))
        if settings.has_module("inv"):
            tabs = tabs + s3db.inv_tabs(r)
        if settings.get_org_needs_tab():
            append_tab((T("Needs"), "needs"))
        elif settings.has_module("req"):
            tabs = tabs + s3db.req_tabs(r)
        if settings.has_module("asset"):
            append_tab((T("Assets"), "asset"))

        tabs.extend(((T("Attachments"), "document"),
                     (T("User Roles"), "roles"),
                     ))

        if tablename == "org_office":
            rheader_fields = [["name", "organisation_id", "email"],
                              ["office_type_id", "location_id", "phone1"],
                              ]
        else:
            def facility_type_lookup(record):
                db = current.db
                ltable = db.org_site_facility_type
                ttable = db.org_facility_type
                query = (ltable.site_id == record.site_id) & \
                        (ltable.facility_type_id == ttable.id)
                rows = db(query).select(ttable.name)
                if rows:
                    return ", ".join([row.name for row in rows])
                else:
                    return current.messages["NONE"]
            rheader_fields = [["name",
                               "organisation_id",
                               "email",
                               ],
                              [(T("Facility Type"), facility_type_lookup),
                               "location_id",
                               "phone1",
                               ],
                              ]

        rheader_fields, rheader_tabs = S3ResourceHeader(rheader_fields,
                                                        tabs)(r, as_div=True)

        # Inject logo
        logo = org_organisation_logo(record.organisation_id)
        if logo:
            rheader = DIV(TABLE(TR(TD(logo),
                                   TD(rheader_fields))))
        else:
            rheader = DIV(rheader_fields)

        rheader.append(rheader_tabs)

        if settings.has_module("inv"):
            # Build footer
            s3db.inv_rfooter(r, record)

    elif tablename == "org_group":
        tabs = [(T("Basic Details"), None),
                (T("Member Organizations"), "organisation"),
                (T("Groups"), "pr_group"),
                (T("Documents"), "document"),
                ]
        if current.auth.s3_has_permission("create", "org_group_membership"):
            tabs.insert(2, (T("Add Organization"), "assign"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(
                            TH("%s: " % table.name.label),
                            record.name,
                            )),
                      rheader_tabs)

    elif tablename in ("org_organisation_type", "org_office_type"):
        tabs = [(T("Basic Details"), None),
                (T("Tags"), "tag"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(TABLE(TR(
                            TH("%s: " % table.name.label),
                            record.name,
                            )),
                      rheader_tabs)

    return rheader

# =============================================================================
def org_organisation_controller():
    """
        Organisation Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    # Pre-process
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.representation == "json":
            r.table.pe_id.readable = True
            list_fields = s3db.get_config(r.tablename,
                                          "list_fields") or []
            s3db.configure(r.tablename,
                           list_fields=list_fields + ["pe_id"]
                           )

        elif r.representation == "xls" and r.component_name == "branch":
            # Improve XLS export of Branches
            table = s3db.org_organisation_branch
            table.organisation_id.represent = \
                org_OrganisationRepresent(acronym=False)
            table.branch_id.represent = org_OrganisationRepresent(parent = False)
            s3db.configure("org_organisation_branch",
                           list_fields = ["organisation_id",
                                          "branch_id",
                                          # Not working - makes for an empty export:
                                          #(T("SubBranch"), "branch_id$branch.branch_id"),
                                          ],
                           )

        elif r.interactive or r.representation == "aadata":

            otable = r.table

            gis = current.gis
            otable.country.default = gis.get_default_country("code")

            f = r.function
            if settings.get_org_regions() and f != "organisation":
                # Non-default function name (e.g. project/partners)
                # => use same function for options lookup after popup-create
                popup_link = otable.region_id.comment
                if popup_link and isinstance(popup_link, S3PopupLink):
                    popup_link.vars["parent"] = f

            method = r.method
            component = r.component

            use_branches = settings.get_org_branches()
            type_filter = r.get_vars.get("organisation_type.name", None)

            if use_branches and not component and \
               not r.record and \
               r.method != "deduplicate" and \
               (not type_filter or type_filter != "Training Center"):
                # Filter out branches from multi-record views
                branch_filter = (FS("parent.id") == None)
                # Filter Locations
                lfilter = current.session.s3.location_filter
                if lfilter:
                    # Include those whose parent is in a different country
                    gtable = s3db.gis_location
                    query = (gtable.id == lfilter)
                    row = db(query).select(gtable.id,
                                           gtable.name,
                                           gtable.level,
                                           gtable.path,
                                           limitby=(0, 1)).first()
                    if row and row.level:
                        if row.level != "L0":
                            code = gis.get_parent_country(row, key_type="code")
                        else:
                            ttable = s3db.gis_location_tag
                            query = (ttable.tag == "ISO2") & \
                                    (ttable.location_id == row.id)
                            tag = db(query).select(ttable.value,
                                                   limitby=(0, 1)).first()
                            code = tag.value
                        branch_filter |= (FS("parent.country") != code) | \
                                         (FS("parent.country") == None)
                r.resource.add_filter(branch_filter)

            if not component or r.component_name == "branch":
                if not component:
                    keyvalue = settings.get_ui_auto_keyvalue()
                    if keyvalue:
                        # What Keys do we have?
                        kvtable = s3db.org_organisation_tag
                        keys = db(kvtable.deleted == False).select(kvtable.tag,
                                                                   distinct=True)
                        if keys:
                            tablename = "org_organisation"
                            crud_fields = s3db.org_organisation_crud_fields
                            cappend = crud_fields.append
                            add_component = s3db.add_components
                            list_fields = s3db.get_config(tablename,
                                                          "list_fields")
                            lappend = list_fields.append
                            for key in keys:
                                tag = key.tag
                                label = T(tag.title())
                                cappend(S3SQLInlineComponent("tag",
                                                             label = label,
                                                             name = tag,
                                                             multiple = False,
                                                             fields = [("", "value")],
                                                             filterby = {"field": "tag",
                                                                         "options": tag,
                                                                         }
                                                             ))
                                add_component(tablename,
                                              org_organisation_tag = {"name": tag,
                                                                      "joinby": "organisation_id",
                                                                      "filterby": {
                                                                          "tag": tag,
                                                                          },
                                                                      },
                                              )
                                lappend((label, "%s.value" % tag))
                            crud_form = S3SQLCustomForm(*crud_fields)
                            s3db.configure(tablename,
                                           crud_form = crud_form,
                                           )

                if type_filter:
                    type_names = [s3_unicode(name).lower().strip()
                                  for name in type_filter.split(",")]
                    field = s3db.org_organisation_organisation_type.organisation_type_id
                    field.comment = None # Don't want to create new types here
                    if len(type_names) == 1:
                        # Strip Type from list_fields
                        list_fields = s3db.get_config("org_organisation",
                                                      "list_fields")
                        try:
                            list_fields.remove("organisation_organisation_type.organisation_type_id")
                        except ValueError:
                            # Already removed
                            pass
                        if not method or method == "create":
                            # Default the Type
                            type_table = s3db.org_organisation_type
                            query = (type_table.name == type_filter)
                            row = db(query).select(type_table.id,
                                                   limitby=(0, 1)).first()
                            type_id = row and row.id
                            if type_id:
                                field.default = type_id
                                field.writable = False
                                crud_form = s3db.get_config("org_organisation",
                                                            "crud_form")
                                for e in crud_form.elements:
                                    if e.selector == "organisation_type":
                                        e.options.label = ""
                    elif not method or method in ("create", "update"):
                        # Limit the Type
                        type_table = s3db.org_organisation_type
                        fquery = (type_table.name.lower().belongs(type_names))
                        field.requires = IS_ONE_OF(db(fquery),
                                                   "org_organisation_type.id",
                                                   label=field.represent,
                                                   error_message=T("Please choose a type"),
                                                   sort=True)
            if component:
                cname = r.component_name
                if cname == "human_resource" and r.component_id:
                    # Workaround until widget is fixed:
                    htable = s3db.hrm_human_resource
                    htable.person_id.widget = None
                    htable.person_id.writable = False

                elif cname == "branch":
                    # Branches default to the same type/country as the parent
                    record = r.record
                    otable.region_id.default = record.region_id
                    otable.country.default = record.country
                    ottable = s3db.org_organisation_organisation_type
                    row = db(ottable.organisation_id == record.id).select(ottable.organisation_type_id,
                                                                          limitby=(0, 1),
                                                                          ).first()
                    if row:
                        ottable.organisation_type_id.default = row.organisation_type_id
                    ostable = s3db.org_sector_organisation
                    row = db(ostable.organisation_id == record.id).select(ostable.sector_id,
                                                                          limitby=(0, 1),
                                                                          ).first()
                    if row:
                        ostable.sector_id.default = row.sector_id
                    # Represent orgs without the parent prefix as we have that context already
                    branch_represent = org_OrganisationRepresent(parent = False,
                                                                 skip_dt_orderby = True,
                                                                 )
                    s3db.org_organisation_branch.branch_id.represent = branch_represent


                elif cname == "task" and \
                     method != "update" and method != "read":
                    # Create or ListCreate
                    ttable = component.table
                    ttable.organisation_id.default = r.id
                    ttable.status.writable = False
                    ttable.status.readable = False

                elif cname == "asset":
                    # Filter the Site field
                    field = s3db.super_link("site_id", "org_site",
                                            empty = False,
                                            filterby="organisation_id",
                                            filter_opts=(r.id,),
                                            represent = s3db.org_site_represent,
                                            )
                    atable = s3db.asset_asset
                    atable.site_id.requires = field.requires
                    # Stay within Organisation tab
                    s3db.configure("asset_asset",
                                   create_next = None,
                                   )

                elif cname == "project" and r.link:
                    # Hide/show host role after project selection in embed-widget
                    tn = r.link.tablename
                    s3db.configure(tn,
                                   post_process='''S3.hide_host_role($('#%s').val())''')
                    s3.scripts.append("/%s/static/scripts/S3/s3.hide_host_role.js" % \
                        r.application)

                    s3db.configure("project_project",
                                   create_next = None,
                                   )

                elif cname == "assistance_theme":
                    # Filter sector_id to the sectors of the current org
                    ttable = component.table
                    stable = s3db.org_sector
                    ltable = s3db.org_sector_organisation

                    left = ltable.on(ltable.sector_id == stable.id)
                    dbset = db((ltable.organisation_id == r.id) & \
                               (ltable.deleted == False))

                    field = ttable.sector_id
                    field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "org_sector.id",
                                                           field.represent,
                                                           left = left,
                                                           ))

                    # If need types are org-specific, filter need_id to org's needs
                    if settings.get_br_needs_org_specific():
                        ntable = s3db.br_need

                        dbset = db(ntable.organisation_id == r.id)

                        field = ttable.need_id
                        field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "br_need.id",
                                                               field.represent,
                                                               ))

                elif cname == "card_config":
                    s3db.doc_update_card_type_requires(r.component_id, r.id)

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Modify action button to open staff instead of human_resource
                # (Delete not overridden to keep errors within Tab)
                read_url = URL(c="hrm", f="staff", args=["[id]"])
                update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
                S3CRUD.action_buttons(r, read_url=read_url,
                                         update_url=update_url)

            elif r.component_name == "branch" and r.record and \
                 isinstance(output, dict) and \
                 "showadd_btn" in output:
                treeview_link = A(current.T("Show Branch Hierarchy"),
                                  _href=r.url(method="hierarchy", component=""),
                                  _class="action-btn",
                                  )
                output["showadd_btn"] = TAG[""](output["showadd_btn"],
                                                treeview_link,
                                                )
        return output
    s3.postp = postp

    output = current.rest_controller("org", "organisation",
                                     # Need to be explicit since can also come from HRM or Project controllers
                                     csv_stylesheet = ("org", "organisation.xsl"),
                                     csv_template = ("org", "organisation"),
                                     # Don't allow components with components (such as document) to breakout from tabs
                                     native = False,
                                     rheader = org_rheader,
                                     )
    return output

# =============================================================================
def org_site_staff_config(r):
    """
        Configure the Staff tab for Sites
    """

    table = current.s3db.hrm_human_resource

    settings = current.deployment_settings
    if settings.has_module("vol"):
        if settings.get_hrm_show_staff():
            if settings.get_org_site_volunteers():
                # Show the type field
                field = table.type
                field.label = current.T("Type")
                field.readable = field.writable = True
            #else:
            #    # Filter to just Staff
            #    r.resource.add_filter(FS("human_resource.type") == 1)
        elif settings.get_org_site_volunteers():
            # Default to Volunteers
            table.type.default = 2

    # Cascade the organisation_id from the site to the staff
    field = table.organisation_id
    field.default = r.record.organisation_id
    field.writable = False
    field.comment = None

    # Filter out people which are already staff for this office
    # - this only works for an IS_ONE_OF dropdown
    # - @ToDo: Pass a flag to pr_search_ac via S3AddPersonWidget to do the same thing
    #site_id = record.site_id
    #try:
    #    person_id_field = r.target()[2].person_id
    #except:
    #    pass
    #else:
    #    query = (htable.site_id == site_id) & \
    #            (htable.deleted == False)
    #    staff = current.db(query).select(htable.person_id)
    #    person_ids = [row.person_id for row in staff]
    #    try:
    #        person_id_field.requires.set_filter(not_filterby = "id",
    #                                            not_filter_opts = person_ids)
    #    except:
    #        pass

# =============================================================================
def org_office_controller():
    """
        Office Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    #T = current.T
    s3db = current.s3db
    request = current.request
    s3 = current.response.s3
    #settings = current.deployment_settings

    # Get default organisation_id
    req_vars = request.vars
    organisation_id = req_vars["organisation_id"]
    if type(organisation_id) is list:
        req_vars["organisation_id"] = organisation_id[0]
    organisation_id = req_vars["organisation_id"] or \
                      current.session.s3.organisation_id or \
                      ""

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        table = r.table
        if organisation_id:
            table.organisation_id.default = organisation_id

        if r.representation == "plain":
            # Map popups want less clutter
            table.obsolete.readable = False

        if r.interactive:
            if r.component:
                cname = r.component_name
                if cname in ("inv_item", "recv", "send"):
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                    # Remove CRUD generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )

                elif cname == "human_resource":
                    org_site_staff_config(r)

                elif cname == "req" and r.method not in ("update", "read"):
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()

                elif cname == "asset":
                    # Default/Hide the Organisation & Site fields
                    record = r.record
                    atable = s3db.asset_asset
                    field = atable.organisation_id
                    field.default = record.organisation_id
                    field.readable = field.writable = False
                    field = atable.site_id
                    field.default = record.site_id
                    field.readable = field.writable = False
                    # Stay within Office tab
                    s3db.configure("asset_asset",
                                   create_next = None)

            elif r.method in ("create", "update"):
                if r.method == "update":
                    table.obsolete.readable = table.obsolete.writable = True
                # Context from a Profile page?"
                org_id = request.get_vars.get("(organisation)", None)
                if org_id:
                    field = table.organisation_id
                    field.default = org_id
                    field.readable = field.writable = False

            elif r.id:
                table.obsolete.readable = table.obsolete.writable = True

        elif r.representation == "geojson":
            marker_fn = s3db.get_config("org_office", "marker_fn")
            if marker_fn:
                # Load these models now as they'll be needed when we encode
                mtable = s3db.gis_marker

        elif r.representation == "xls":
            list_fields = r.resource.get_config("list_fields")
            list_fields += ["location_id$lat",
                            "location_id$lon",
                            "location_id$inherited",
                            ]

        return True
    s3.prep = prep

    # Post-process
    def postp(r, output):
        if r.interactive and r.component_name == "human_resource":
            # Modify action button to open staff instead of human_resource
            # (Delete not overridden to keep errors within Tab)
            read_url = URL(c="hrm", f="staff", args=["[id]"])
            update_url = URL(c="hrm", f="staff", args=["[id]", "update"])
            S3CRUD.action_buttons(r, read_url=read_url,
                                     update_url=update_url)
        return output
    s3.postp = postp

    output = current.rest_controller("org", "office",
                                     # Don't allow components with components (such as document) to breakout from tabs
                                     native = False,
                                     rheader = org_rheader,
                                     )
    return output

# =============================================================================
def org_facility_controller():
    """
        Facility Controller, defined in the model for use from
        multiple controllers for unified menus
    """

    db = current.db
    s3db = current.s3db
    s3 = current.response.s3

    # Pre-processor
    def prep(r):
        # Location Filter
        s3db.gis_location_filter(r)

        if r.interactive:
            if not r.component:
                method = r.method
                get_vars = r.get_vars
                type_filter = get_vars.get("facility_type.name", None)
                if type_filter:
                    type_names = [s3_unicode(name).lower().strip()
                                  for name in type_filter.split(",")]
                    field = s3db.org_site_facility_type.facility_type_id
                    field.comment = None # Don't want to create new types here
                    if len(type_names) == 1:
                        # Strip Type from list_fields
                        list_fields = s3db.get_config("org_facility",
                                                      "list_fields")
                        try:
                            list_fields.remove("site_facility_type.facility_type_id")
                        except ValueError:
                            # Already removed
                            pass
                        if not method or method == "create":
                            # Default the Type
                            type_table = s3db.org_facility_type
                            query = (type_table.name == type_filter)
                            row = db(query).select(type_table.id,
                                                   limitby=(0, 1)).first()
                            type_id = row and row.id
                            if type_id:
                                field.default = type_id
                                field.writable = False
                                crud_form = s3db.get_config("org_facility",
                                                            "crud_form")
                                for e in crud_form.elements:
                                    if e.selector == "facility_type":
                                        e.options.label = ""

                if r.id:
                    table = r.table
                    field = table.obsolete
                    field.readable = field.writable = True
                    if method == "update" and \
                       r.representation == "popup" and \
                       get_vars.get("profile") == "org_organisation":
                        # Coming from organisation profile
                        # Don't allow change of organisation_id in this case
                        field = table.organisation_id
                        field.writable = False
                        field.readable = False

                elif method == "create":
                    table = r.table
                    name = get_vars.get("name")
                    if name:
                        table.name.default = name
                    if r.representation == "popup" and \
                       get_vars.get("profile") == "org_organisation":
                        # Coming from organisation profile
                        organisation_id = None
                        for k in ("~.organisation_id", "(organisation)", "~.(organisation)"):
                            if k in get_vars:
                                organisation_id = get_vars[k]
                                break
                        if organisation_id is not None:
                            # Don't allow change of organisation_id in this case
                            field = table.organisation_id
                            field.default = organisation_id
                            field.writable = False
                            field.readable = False

                elif method == "report":
                    table.organisation_id.represent = org_OrganisationRepresent() # show_link = False

            else:
                cname = r.component_name
                if cname in ("inv_item", "recv", "send"):
                    # Filter out items which are already in this inventory
                    s3db.inv_prep(r)

                    # remove CRUD-generated buttons in the tabs
                    s3db.configure("inv_inv_item",
                                   create = False,
                                   deletable = False,
                                   editable = False,
                                   listadd = False,
                                   )

                elif cname == "human_resource":
                    org_site_staff_config(r)

                elif cname == "req" and r.method not in ("update", "read"):
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    s3db.req_create_form_mods()

                elif cname == "asset":
                    # Default/Hide the Organisation & Site fields
                    record = r.record
                    atable = s3db.asset_asset
                    field = atable.organisation_id
                    field.default = record.organisation_id
                    field.readable = field.writable = False
                    field = atable.site_id
                    field.default = record.site_id
                    field.readable = field.writable = False
                    # Stay within Facility tab
                    s3db.configure("asset_asset",
                                   create_next = None,
                                   )

        elif r.representation == "geojson":
            # Load these models now as they'll be needed when we encode
            mtable = s3db.gis_marker

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.component_name == "shift":
            # Normal Action Buttons
            S3CRUD.action_buttons(r)
            # Custom Action Buttons
            s3.actions += [{"label": s3_str(current.T("Assign")),
                            "url": URL(c = "hrm",
                                       f = "shift",
                                       args = ["[id]", "assign"],
                                       ),
                            "_class": "action-btn",
                            },
                           ]

        elif r.representation == "plain" and r.record:
            # Custom Map Popup
            T = current.T
            record = r.record
            output = TABLE()
            append = output.append
            # Edit button
            append(TR(TD(A(T("Edit"),
                           _target="_blank",
                           _id="edit-btn",
                           _href=URL(args=[r.id, "update"])))))

            # Name
            append(TR(TD(B("%s:" % T("Name"))),
                      TD(record.name)))

            site_id = record.site_id

            # Type(s)
            ttable = db.org_facility_type
            ltable = db.org_site_facility_type
            query = (ltable.site_id == site_id) & \
                    (ltable.facility_type_id == ttable.id)
            rows = db(query).select(ttable.name)
            if rows:
                append(TR(TD(B("%s:" % ltable.facility_type_id.label)),
                          TD(", ".join([row.name for row in rows]))))

            ftable = r.table
            # Comments
            if record.comments:
                append(TR(TD(B("%s:" % ftable.comments.label)),
                          TD(ftable.comments.represent(record.comments))))

            # Organisation (better with just name rather than Represent)
            # @ToDo: Make this configurable - some users will only see
            #        their staff so this is a meaningless field for them
            table = db.org_organisation
            org = db(table.id == record.organisation_id).select(table.name,
                                                                limitby=(0, 1)
                                                                ).first()
            if org:
                append(TR(TD(B("%s:" % ftable.organisation_id.label)),
                          TD(org.name)))

            if current.deployment_settings.has_module("req"):
                # Open High/Medium priority Requests
                rtable = s3db.req_req
                query = (rtable.site_id == site_id) & \
                        (rtable.fulfil_status != 2) & \
                        (rtable.priority.belongs((2, 3)))
                reqs = db(query).select(rtable.id,
                                        rtable.req_ref,
                                        rtable.type,
                                        )
                if reqs:
                    append(TR(TD(B("%s:" % T("Requests")))))
                    req_types = {1: "req_item",
                                 3: "req_skill",
                                 8: "",
                                 9: "",
                                 }
                    vals = [A(req.req_ref,
                              _href=URL(c="req", f="req",
                                        args=[req.id, req_types[req.type]])) for req in reqs]
                    for val in vals:
                        append(TR(TD(val, _colspan=2)))

            # Street address
            gtable = s3db.gis_location
            stable = s3db.org_site
            query = (gtable.id == stable.location_id) & \
                    (stable.id == site_id)
            location = db(query).select(gtable.addr_street,
                                        limitby=(0, 1)).first()
            if location.addr_street:
                append(TR(TD(B("%s:" % gtable.addr_street.label)),
                          TD(location.addr_street)))

            # Opening Times
            opens = record.opening_times
            if opens:
                append(TR(TD(B("%s:" % ftable.opening_times.label)),
                          TD(opens)))

            # Phone number
            contact = record.contact
            if contact:
                append(TR(TD(B("%s:" % ftable.contact.label)),
                          TD(contact)))

            # Phone number
            phone1 = record.phone1
            if phone1:
                append(TR(TD(B("%s:" % ftable.phone1.label)),
                          TD(phone1)))

            # Email address (as hyperlink)
            email = record.email
            if email:
                append(TR(TD(B("%s:" % ftable.email.label)),
                          TD(A(email, _href="mailto:%s" % email))))

            # Website (as hyperlink)
            website = record.website
            if website:
                append(TR(TD(B("%s:" % ftable.website.label)),
                          TD(A(website, _href=website))))

        return output
    s3.postp = postp

    output = current.rest_controller("org", "facility",
                                     rheader = org_rheader,
                                     )
    return output

# =============================================================================
# Hierarchy Manipulation
# =============================================================================
def org_update_affiliations(table, record):
    """
        Update OU affiliations related to this record

        @param table: the table
        @param record: the record
    """

    if hasattr(table, "_tablename"):
        rtype = table._tablename
    else:
        rtype = table

    if rtype == "org_organisation_branch":

        ltable = current.s3db.org_organisation_branch
        if not isinstance(record, Row):
            record = current.db(ltable.id == record).select(ltable.ALL,
                                                            limitby=(0, 1),
                                                            ).first()
        if not record:
            return
        organisation_update_affiliations(record)

    elif rtype == "org_group_membership":

        mtable = current.s3db.org_group_membership
        if not isinstance(record, Row):
            record = current.db(mtable.id == record).select(mtable.ALL,
                                                            limitby=(0, 1),
                                                            ).first()
        if not record:
            return
        org_group_update_affiliations(record)

    elif rtype == "org_site" or rtype in current.auth.org_site_types:

        if "organisation_id" not in record:
            # Probably created on component tab, so form does not have the
            # organisation_id => reload record to get it
            rtable = current.s3db[rtype]
            try:
                query = (rtable._id == record[rtable._id.name])
            except (KeyError, AttributeError):
                return
            record = current.db(query).select(rtable.ALL,
                                              limitby=(0, 1)).first()

        org_site_update_affiliations(record)

    elif rtype == "org_organisation_team":

        if not isinstance(record, Row) or "group_id" not in record:
            ltable = current.s3db.org_organisation_team
            record = current.db(ltable.id == record).select(ltable.id,
                                                            ltable.organisation_id,
                                                            ltable.group_id,
                                                            ltable.deleted,
                                                            ltable.deleted_fk,
                                                            limitby=(0, 1),
                                                            ).first()
        if not record:
            return
        org_team_update_affiliations(record)

# =============================================================================
def organisation_update_affiliations(record):
    """
        Update affiliations for a branch organisation

        @param record: the org_organisation_branch record
    """

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            branch_id = fk["branch_id"]
        except:
            return
    else:
        branch_id = record.branch_id

    from .pr import OU
    BRANCHES = "Branches"

    db = current.db
    s3db = current.s3db
    otable = s3db.org_organisation
    btable = otable.with_alias("branch")
    ltable = db.org_organisation_branch
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    o = otable._tablename
    b = btable._tablename
    r = rtable._tablename

    # Get current memberships
    query = (ltable.branch_id == branch_id) & \
            (ltable.deleted != True)
    left = [otable.on(ltable.organisation_id == otable.id),
            btable.on(ltable.branch_id == btable.id)]
    rows = db(query).select(otable.pe_id, btable.pe_id, left=left)
    current_memberships = [(row[o].pe_id, row[b].pe_id) for row in rows]

    # Get current affiliations
    query = (rtable.deleted != True) & \
            (rtable.role == BRANCHES) & \
            (rtable.pe_id == etable.pe_id) & \
            (etable.instance_type == o) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == btable.pe_id) & \
            (btable.id == branch_id)
    rows = db(query).select(rtable.pe_id, btable.pe_id)
    current_affiliations = [(row[r].pe_id, row[b].pe_id) for row in rows]

    # Remove all affiliations which are not current memberships
    remove_affiliation = s3db.pr_remove_affiliation
    for a in current_affiliations:
        org, branch = a
        if a not in current_memberships:
            remove_affiliation(org, branch, role=BRANCHES)
        else:
            current_memberships.remove(a)

    # Add affiliations for all new memberships
    add_affiliation = s3db.pr_add_affiliation
    for m in current_memberships:
        org, branch = m
        add_affiliation(org, branch, role=BRANCHES, role_type=OU)

# =============================================================================
def org_group_update_affiliations(record):
    """
        Update affiliations for organisation group memberships

        @param record: the org_group_membership record
    """

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            organisation_id = fk["organisation_id"]
        except (TypeError, ValueError, KeyError):
            return
    else:
        organisation_id = record.organisation_id

    s3db = current.s3db

    # Get the organisation pe_id
    org_pe_id = s3db.pr_get_pe_id("org_organisation", organisation_id)
    if not org_pe_id:
        return

    from .pr import OU
    MEMBERS = "Members"

    db = current.db
    mtable = s3db.org_group_membership
    gtable = db.org_group
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    # Get current memberships
    query = (mtable.organisation_id == organisation_id) & \
            (mtable.deleted != True)
    left = gtable.on(mtable.group_id == gtable.id)
    rows = db(query).select(gtable.pe_id, left=left)
    current_memberships = set(row["pe_id"] for row in rows)

    # Get current affiliations
    query = (atable.pe_id == org_pe_id) & \
            (atable.deleted != True) & \
            (rtable.id == atable.role_id) & \
            (rtable.role == MEMBERS) & \
            (rtable.deleted != True) & \
            (etable.pe_id == rtable.pe_id) & \
            (etable.instance_type == "org_group")
    rows = db(query).select(rtable.pe_id)
    current_affiliations = set(row["pe_id"] for row in rows)

    # Remove all affiliations which are not current memberships
    obsolete = current_affiliations - current_memberships
    remove_affiliation = s3db.pr_remove_affiliation
    for group_pe_id in obsolete:
        remove_affiliation(group_pe_id, org_pe_id, role=MEMBERS)

    # Add affiliations for all new memberships
    new =  current_memberships - current_affiliations
    add_affiliation = s3db.pr_add_affiliation
    for group_pe_id in new:
        add_affiliation(group_pe_id, org_pe_id, role=MEMBERS, role_type=OU)

# =============================================================================
def org_site_update_affiliations(record):
    """
        Update the affiliations of an org_site instance

        @param record: the org_site instance record
    """

    from .pr import OU
    SITES = "Sites"

    db = current.db
    s3db = current.s3db
    otable = db.org_organisation
    ptable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    o_pe_id = None
    s_pe_id = record.get("pe_id")

    organisation_id = record.get("organisation_id")
    if organisation_id:
        org = db(otable.id == organisation_id).select(otable.pe_id,
                                                      limitby=(0, 1)).first()
        if org:
            o_pe_id = org.pe_id
    if s_pe_id:
        query = (atable.deleted != True) & \
                (atable.pe_id == s_pe_id) & \
                (rtable.deleted != True) & \
                (rtable.id == atable.role_id) & \
                (rtable.role == SITES) & \
                (ptable.pe_id == rtable.pe_id) & \
                (ptable.instance_type == str(otable))
        rows = db(query).select(rtable.pe_id)
        seen = False

        remove_affiliation = s3db.pr_remove_affiliation
        for row in rows:
            if o_pe_id == None or o_pe_id != row.pe_id:
                remove_affiliation(row.pe_id, s_pe_id, role=SITES)
            elif o_pe_id == row.pe_id:
                seen = True
        if o_pe_id and not seen:
            s3db.pr_add_affiliation(o_pe_id, s_pe_id, role=SITES,
                                    role_type=OU)

# =============================================================================
def org_team_update_affiliations(record):
    """
        Update affiliations for an organisation team

        @param record: the org_organisation_team record
    """

    # Get the group_id of the team
    if record.deleted:
        group_id = None
        if record.deleted_fk:
            try:
                fk = json.loads(record.deleted_fk)
            except (TypeError, ValueError, KeyError):
                pass
            else:
                group_id = fk.get("group_id")
    else:
        group_id = record.group_id
    if not group_id:
        # Nothing we can do
        return

    s3db = current.s3db

    # Get the pe_id of the team
    team_pe_id = s3db.pr_get_pe_id("pr_group", group_id)
    if not team_pe_id:
        # Nothing we can do
        return

    from .pr import OU
    TEAMS = "Groups" # Backwards-compatibility, but should be "Teams"

    db = current.db

    # Get current memberships (=organisation pe_ids)
    ltable = s3db.org_organisation_team
    otable = s3db.org_organisation
    query = (ltable.group_id == group_id) & \
            (ltable.deleted == False)
    left = otable.on(ltable.organisation_id == otable.id)
    rows = db(query).select(otable.pe_id, left=left)
    current_memberships = set(row["pe_id"] for row in rows)

    # Get current affiliations (=organisation pe_ids)
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation
    query = (atable.pe_id == team_pe_id) & \
            (atable.deleted == False) & \
            (rtable.id == atable.role_id) & \
            (rtable.role == TEAMS) & \
            (rtable.deleted == False) & \
            (etable.pe_id == rtable.pe_id) & \
            (etable.instance_type == "org_organisation")
    rows = db(query).select(rtable.pe_id)
    current_affiliations = set(row["pe_id"] for row in rows)

    # Remove all affiliations which are not current memberships
    obsolete = current_affiliations - current_memberships
    remove_affiliation = s3db.pr_remove_affiliation
    for org_pe_id in obsolete:
        remove_affiliation(org_pe_id, team_pe_id, role=TEAMS)

    # Add affiliations for all new memberships
    new =  current_memberships - current_affiliations
    add_affiliation = s3db.pr_add_affiliation
    for org_pe_id in new:
        add_affiliation(org_pe_id, team_pe_id, role=TEAMS, role_type=OU)

# =============================================================================
def org_update_root_organisation(organisation_id, root_org=None):
    """
        Update the root organisation of an org_organisation

        @param organisation_id: the org_organisation record ID
        @param root_org: the root organisation record ID (for
                         internal use in update cascade only)

        @return: the root organisation ID
    """

    # @todo: make immune against circular references!

    db = current.db

    s3db = current.s3db
    otable = s3db.org_organisation
    ltable = s3db.org_organisation_branch

    if root_org is None:

        # Batch update (introspective)
        if isinstance(organisation_id, (list, tuple, set)):
            for organisation in organisation_id:
                org_update_root_organisation(organisation)
            return None

        # Get the parent organisation
        query = (ltable.branch_id == organisation_id) & \
                (ltable.organisation_id == otable.id)
        parent_org = db(query).select(otable.id,
                                      otable.root_organisation,
                                      limitby=(0, 1)).first()
        if not parent_org:
            # No parent organisation? => this is the root organisation
            root_org = organisation_id
        else:
            # Use parent organisation's root_organisation
            root_org = parent_org.root_organisation
            if not root_org:
                # Not present? => update it
                root_org = org_update_root_organisation(parent_org.id)

    if root_org is not None:

        # Update the record(s)
        if isinstance(organisation_id, (list, tuple, set)):
            oquery = (otable.id.belongs(organisation_id))
            bquery = (ltable.organisation_id.belongs(organisation_id))
        else:
            oquery = (otable.id == organisation_id)
            bquery = (ltable.organisation_id == organisation_id)
        db(oquery).update(root_organisation=root_org)

        # Propagate to all branches (explicit batch update)
        branches = db(bquery).select(ltable.branch_id)
        if branches:
            branch_ids = set(branch.branch_id for branch in branches)
            org_update_root_organisation(branch_ids, root_org=root_org)

    return root_org

# =============================================================================
class org_OrganisationDuplicate(object):
    """ Import item deduplication, match by name or l10_name """

    @classmethod
    def duplicate(cls, item):
        """
            Main method, to be set for the "deduplicate" hook

            @param item: the S3ImportItem
        """

        try:
            duplicate_id = cls.identify(item)
        except ValueError:
            # Ambiguous => reject the item
            error = "Ambiguous data, try specifying parent organisation: %s" % item.data.get("name")
            item.accepted = False
            item.error = error
            if item.element is not None:
                item.element.set(current.xml.ATTRIBUTE["error"], error)
            return

        if duplicate_id:
            item.id = duplicate_id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @classmethod
    def identify(cls, item=None, uid=None):
        """
            Get the record ID that corresponds to the given import item
            or UUID

            @param item: the import item
            @param uid: the UUID

            @return: the record ID if successfully identified, or
                     None if there is no record for that item yet
            @raise ValueError: if there are multiple matches in the DB
        """

        if item.id:
            # Already identified
            return item.id

        if uid is not None:
            # Try to find the record for this UUID
            table = item.table if item else current.s3db.org_organisation
            row = current.db(table.uuid == uid).select(table.id,
                                                       limitby=(0, 1)).first()
            if row:
                return row.id

        # Do we have any name matches?
        name_matches = cls.name_match(item)
        if not name_matches:
            return None

        # Do we have a parent specified by the source?
        parent_id, parent_uid, parent_item = cls.parent(item)

        if not any((parent_id, parent_uid, parent_item)):

            if len(name_matches) == 1:
                # Single name match (+ no parent item = no conflict)
                match = list(name_matches.keys())[0]
                name = name_matches[match].get("name")
                if name:
                    item.data.name = name
                return match

            else:
                # Multiple name matches, look for a single root org match
                hits = [k for k, v in name_matches.items()
                              if v.get("parent") is None]
                if len(hits) == 1:
                    # Single root organisation match
                    match = hits[0]
                    name = name_matches[match].get("name")
                    if name:
                        item.data.name = name
                    return match

                else:
                    # Multiple or no root organisation matches (=ambiguous)
                    raise ValueError
        else:
            if not parent_id:
                # Try to identify the parent (recurse)
                parent_id = cls.identify(item = parent_item,
                                         uid = parent_uid,
                                         )
            if not parent_id:
                # Parent does not yet exist, so branch must be new too
                return None

            hits = [k for k, v in name_matches.items()
                          if v.get("parent") == parent_id]

            if len(hits) == 0:
                # No name match under the same parent => new branch
                return None

            if len(hits) == 1:
                # Single name match under the same parent
                match = hits[0]
                name = name_matches[match].get("name")
                if name:
                    item.data.name = name
                return match

            else:
                # Multiple name matches under the same parent (=ambiguous)
                raise ValueError

        # Default
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def name_match(cls, item):
        """
            Find all name matches for the given import item

            @param item: the import item
            @return: a dict {id: name, parent: parent_id} of records which
                     match the import item by name, or alternatively by
                     local name if enabled and no direct name match
        """

        matches = {}

        name = item.data.get("name")
        if not name:
            return matches

        db = current.db
        s3db = current.s3db

        table = item.table

        # Search by name
        lower_name = s3_unicode(name).lower()
        query = (table.name.lower() == lower_name) & \
                (table.deleted == False)
        rows = db(query).select(table.id, table.name)

        if not rows and current.deployment_settings.get_L10n_translate_org_organisation():
            # Search by local name
            ltable = s3db.org_organisation_name
            query = (ltable.name_l10n.lower() == lower_name) & \
                    (ltable.organisation_id == table.id) & \
                    (ltable.deleted != True)
            rows = db(query).select(table.id, table.name)

        if rows:
            # Get the parents for all matches
            matches = {row.id: {"name": row.name} for row in rows}

            btable = s3db.org_organisation_branch
            query = (btable.branch_id.belongs(set(matches.keys()))) & \
                    (btable.deleted != True)
            links = db(query).select(btable.organisation_id,
                                     btable.branch_id,
                                     )
            for link in links:
                matches[link.branch_id]["parent"] = link.organisation_id

        return matches

    # -------------------------------------------------------------------------
    @classmethod
    def parent(cls, item):
        """
            Find the parent for the given import item

            @param item: the import item
            @return: a tuple (id, uid, item) for the parent
        """

        parent_id = parent_uid = parent_item = None

        is_key = lambda fk, name: fk == name or \
                                  isinstance(fk, (tuple, list)) and \
                                  fk[1] == name

        all_items = item.job.items
        for link_item in all_items.values():
            if link_item.tablename == "org_organisation_branch":
                references = link_item.references
                parent = branch = None
                for reference in references:
                    fk = reference.field
                    if is_key(fk, "branch_id"):
                        branch = reference.entry
                    elif is_key(fk, "organisation_id"):
                        parent = reference.entry
                    if parent and branch:
                        break
                if parent and branch and branch.item_id == item.item_id:
                    parent_id = parent.id
                    parent_uid = parent.uid
                    parent_item = all_items.get(parent.item_id)
                    break

        return parent_id, parent_uid, parent_item

# =============================================================================
class org_AssignMethod(S3Method):
    """
        Custom Method to allow organisations to be assigned to something
        e.g. Organisation Group
    """

    def __init__(self, component):
        """
            @param component: the Component in which to create records
        """

        self.component = component

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        try:
            component = r.resource.components[self.component]
        except KeyError:
            current.log.error("Invalid Component!")
            raise

        if component.link:
            component = component.link

        tablename = component.tablename

        # Requires permission to create component
        authorised = current.auth.s3_has_permission("create", tablename)
        if not authorised:
            r.unauthorised()

        T = current.T
        s3db = current.s3db

        get_vars = r.get_vars
        response = current.response

        if r.http == "POST":
            added = 0
            post_vars = r.post_vars
            if all([n in post_vars for n in ("assign", "selected", "mode")]):
                fkey = component.fkey
                record = r.record
                if fkey in record:
                    # SuperKey
                    record_id = r.record[fkey]
                else:
                    record_id = r.id
                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                db = current.db
                table = s3db[tablename]
                if selected:
                    # Handle exclusion filter
                    if post_vars.mode == "Exclusive":
                        if "filterURL" in post_vars:
                            filters = S3URLQuery.parse_url(post_vars.ajaxURL)
                        else:
                            filters = None
                        query = ~(FS("id").belongs(selected))
                        hresource = s3db.resource("org_organisation",
                                                  filter=query, vars=filters)
                        rows = hresource.select(["id"], as_rows=True)
                        selected = [str(row.id) for row in rows]

                    query = (table.organisation_id.belongs(selected)) & \
                            (table[fkey] == record_id) & \
                            (table.deleted != True)
                    rows = db(query).select(table.id)
                    rows = dict((row.id, row) for row in rows)
                    onaccept = component.get_config("create_onaccept",
                                                    component.get_config("onaccept",
                                                                         None)
                                                    )
                    for organisation_id in selected:
                        try:
                            org_id = int(organisation_id.strip())
                        except ValueError:
                            continue
                        if org_id not in rows:
                            link = Storage(organisation_id = organisation_id)
                            link[fkey] = record_id
                            _id = table.insert(**link)
                            if onaccept:
                                link["id"] = _id
                                form = Storage(vars=link)
                                onaccept(form)
                            added += 1
            current.session.confirmation = T("%(number)s assigned") % \
                                           {"number": added}
            if added > 0:
                redirect(URL(args=[r.id, "organisation"], vars={}))
            else:
                redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            # Filter widgets
            filter_widgets = []

            # List fields
            list_fields = ["id",
                           "name",
                           ]

            # Data table
            resource = s3db.resource("org_organisation")
            totalrows = resource.count()
            if "pageLength" in get_vars:
                display_length = get_vars["pageLength"]
                if display_length == "None":
                    display_length = None
                else:
                    display_length = int(display_length)
            else:
                display_length = 25
            if display_length:
                limit = 4 * display_length
            else:
                limit = None
            dtfilter, orderby, left = resource.datatable_filter(list_fields, get_vars)
            resource.add_filter(dtfilter)
            data = resource.select(list_fields,
                                   start=0,
                                   limit=limit,
                                   orderby=orderby,
                                   left=left,
                                   count=True,
                                   represent=True)
            filteredrows = data["numrows"]
            dt = S3DataTable(data["rfields"], data["rows"])
            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Add"), "assign")]

            if r.representation == "html":
                # Page load
                resource.configure(deletable = False)

                profile_url = URL(c = "org",
                                  f = "organisation",
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = profile_url,
                                      update_url = profile_url)
                response.s3.no_formats = True

                # Data table (items)
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url=URL(args = r.args,
                                                extension="aadata",
                                                vars={},
                                                ),
                                dt_bulk_actions=dt_bulk_actions,
                                dt_pageLength=display_length,
                                dt_pagination="true",
                                dt_searching="false",
                                )

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    _vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=_vars)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f="human_resource",
                                          args=["filter.options"],
                                          vars={})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear=filter_clear,
                                               formstyle=filter_formstyle,
                                               submit=filter_submit,
                                               ajax=True,
                                               url=filter_submit_url,
                                               ajaxurl=filter_ajax_url,
                                               _class="filter-form",
                                               _id="datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = resource.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target="datatable",
                                          alias=alias)
                else:
                    ff = ""

                output = {"items": items,
                          "title": T("Add Organization"),
                          "list_filter_form": ff,
                          }

                response.view = "list_filter.html"
                return output

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions)
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class org_CapacityReport(S3Method):
    """
        Custom Report Method for Organisation Capacity Assessment Data
    """

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        if r.http == "GET":
            if r.representation == "html":

                T = current.T

                output = {"title": T("Branch Organisational Capacity Assessment")}
                current.response.view = "org/capacity_report.html"

                # Maintain RHeader for consistency
                if attr.get("rheader"):
                    rheader = attr["rheader"](r)
                    if rheader:
                        output["rheader"] = rheader

                data = self._extract(r)
                if data is None:
                    output["items"] = current.response.s3.crud_strings["org_capacity_assessment"].msg_list_empty
                    return output

                indicators, orgs, consolidated = data

                # Build the output table
                rows = []
                rappend = rows.append
                section = None
                for i in indicators:
                    if i.section != section:
                        section = i.section
                        rappend(TR(TD(section), _class="odd"))
                    title = TD("%s. %s" % (i.number, i.name))
                    row = TR(title)
                    append = row.append
                    indicator_id = i.id
                    values = consolidated[indicator_id]
                    for v in ("A", "B", "C", "D", "E", "F"):
                        append(TD(values[v]))
                    for o in orgs:
                        rating = orgs[o].get(indicator_id, "")
                        append(TD(rating))
                    rappend(row)

                orepresent = org_OrganisationRepresent(parent = False,
                                                       acronym = False)
                orgs = [TH(orepresent(o)) for o in orgs]

                items = TABLE(THEAD(TR(TH("TOPICS", _rowspan=2),
                                       TH("Consolidated Ratings", _colspan=6),
                                       ),
                                    TR(TH("A"),
                                       TH("B"),
                                       TH("C"),
                                       TH("D"),
                                       TH("E"),
                                       TH("F"),
                                       *orgs
                                       ),
                                    ),
                              TBODY(*rows),
                              )

                output["items"] = items

                return output

            elif r.representation == "xls":
                data = self._extract(r)
                if data is None:
                    current.session.error = current.response.s3.crud_strings["org_capacity_assessment"].msg_list_empty
                    redirect(URL(f="capacity_assessment", extension=""))
                return self._xls(data)

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def _extract(r):
        """
            Method to read the data

            @param r: the S3Request
        """

        # Read all the permitted data
        resource = r.resource
        resource.load()
        rows = resource._rows

        if not len(rows):
            return None

        db = current.db
        s3db = current.s3db

        # Read all the Indicators
        itable = s3db.org_capacity_indicator
        indicators = db(itable.deleted == False).select(itable.id,
                                                        itable.number,
                                                        itable.section,
                                                        itable.name,
                                                        orderby = itable.number,
                                                        )

        # Find all the Assessments
        assessments = [row.assessment_id for row in rows]
        atable = s3db.org_capacity_assessment
        assessments = db(atable.id.belongs(assessments)).select(atable.id,
                                                                atable.organisation_id,
                                                                #atable.date,
                                                                # We will just include the most recent for each organisation
                                                                orderby = ~atable.date,
                                                                )

        # Find all the Organisations and the Latest Assessments
        latest_assessments = {}
        orgs = {}
        for a in assessments:
            o = a.organisation_id
            if o not in orgs:
                latest_assessments[a.id] = o
                orgs[o] = {}

        # Calculate the Consolidated Ratings & populate the individual ratings
        consolidated = {}
        for i in indicators:
            consolidated[i.id] = {"A": 0,
                                  "B": 0,
                                  "C": 0,
                                  "D": 0,
                                  "E": 0,
                                  "F": 0,
                                  }
        for row in rows:
            a = row.assessment_id
            if a in latest_assessments:
                indicator = row.indicator_id
                rating = row.rating
                # Update the Consolidated
                consolidated[indicator][rating] += 1
                # Lookup which org this data belongs to
                o = latest_assessments[a]
                # Populate the Individual
                orgs[o][indicator] = rating

        return indicators, orgs, consolidated

    # -------------------------------------------------------------------------
    @staticmethod
    def _xls(data):
        """
            Method to output as XLS

            @ToDo: Finish & use HTML2XLS method in XLS codec to be DRY & reusable
        """

        try:
            import xlwt
        except ImportError:
            from s3.codecs.xls import S3XLS
            if current.auth.permission.format in S3Request.INTERACTIVE_FORMATS:
                current.session.error = S3XLS.ERROR.XLWT_ERROR
                redirect(URL(extension=""))
            else:
                error = S3XLS.ERROR.XLWT_ERROR
                current.log.error(error)
                return error

        indicators, orgs, consolidated = data

        # Build the output XLS
        # @ToDo: Configurability if used outside IFRC
        title = "BOCA"

        #COL_WIDTH_MULTIPLIER = S3XLS.COL_WIDTH_MULTIPLIER

        # Create the workbook
        book = xlwt.Workbook(encoding="utf-8")

        # Add a sheet
        # Can't have a / in the sheet_name, so replace any with a space
        #sheet_name = str(title.replace("/", " "))
        sheet_name = title
        # sheet_name cannot be over 31 chars
        if len(sheet_name) > 31:
            sheet_name = sheet_name[:31]
        sheet1 = book.add_sheet(sheet_name)

        # Header
        styleHeader = xlwt.XFStyle()
        styleHeader.font.bold = True
        styleHeader.pattern.pattern = styleHeader.pattern.SOLID_PATTERN
        styleHeader.pattern.pattern_fore_colour = 0x2C # pale_blue S3XLS.HEADER_COLOUR
        # Merged cells (rowspan, then colspan)
        sheet1.write_merge(0, 1, 0, 0, "TOPICS", styleHeader)
        sheet1.write_merge(0, 0, 1, 6, "Consolidated Ratings", styleHeader)
        sheet1.row(1).write(1, "A", styleHeader)
        sheet1.row(1).write(2, "B", styleHeader)
        sheet1.row(1).write(3, "C", styleHeader)
        sheet1.row(1).write(4, "D", styleHeader)
        sheet1.row(1).write(5, "E", styleHeader)
        sheet1.row(1).write(6, "F", styleHeader)
        orepresent = org_OrganisationRepresent(parent = False,
                                               acronym = False)
        col = 7
        for o in orgs:
            sheet1.row(1).write(col, orepresent(o), styleHeader)
            col += 1

        # Data
        styleSection = xlwt.XFStyle()
        styleSection.font.bold = True
        styleSection.pattern.pattern = styleSection.pattern.SOLID_PATTERN
        styleSection.pattern.pattern_fore_colour = 0x2F # tan
        row = 3
        section = None
        max_width = 0
        for i in indicators:
            if i.section != section:
                section = i.section
                sheet1.row(row).write(0, section, styleSection)
                if len(section) > max_width:
                    max_width = len(section)
                row += 1
            sheet1.row(row).write(0, "%s. %s" % (i.number, i.name))
            indicator_id = i.id
            values = consolidated[indicator_id]
            col = 1
            for v in ("A", "B", "C", "D", "E", "F"):
                sheet1.row(row).write(col, values[v])
                col += 1
            for o in orgs:
                rating = orgs[o].get(indicator_id, "")
                sheet1.row(row).write(col, rating)
                col += 1
            row += 1

        # Set the width of 1st column to max section length
        COL_WIDTH_MULTIPLIER = 310
        width = max(max_width * COL_WIDTH_MULTIPLIER, 2000)
        width = min(width, 65535) # USHRT_MAX
        sheet1.col(0).width = width

        # Create the file
        output = StringIO()
        book.save(output)

        # Response headers
        from gluon.contenttype import contenttype
        filename = "%s.xls" % title
        disposition = "attachment; filename=\"%s\"" % filename
        response = current.response
        response.headers["Content-Type"] = contenttype(".xls")
        response.headers["Content-disposition"] = disposition

        output.seek(0)
        return output.read()

# =============================================================================
def org_logo_represent(org = None,
                       fallback_org = None,
                       width = 60,
                       ):
    """
        Produce an Org Logo DIV

        @param org: the name of the Org to use (or None to lookup root_org)
        @param fallback_org: the name of the fallback Org to use (if root_org lookup fails)
        @param width: the width of the image
    """

    logo = None

    if not org:
        # Lookup Root Organisation name
        org = current.auth.root_org_name()

    if org:
        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation
        query = (otable.name == org)
        fields = [otable.logo,
                  ]

        language = current.session.s3.language
        if language == current.deployment_settings.get_L10n_default_language():
            left = None
        else:
            ltable = s3db.org_organisation_name
            left = ltable.on((ltable.organisation_id == otable.id) & \
                             (ltable.language == language))
            fields += [ltable.name_l10n,
                       #ltable.acronym_l10n,
                       ]

        record = db(query).select(left = left,
                                  limitby = (0, 1),
                                  cache = s3db.cache,
                                  *fields).first()

        if record:
            if left:
                org = record["org_organisation_name.name_l10n"] or org
                logo = record["org_organisation.logo"]
            else:
                logo = record.logo

            if logo:
                # Select resized version if-available
                size = (width, None)
                image = s3db.pr_image_library_represent(logo, size=size)
                url_small = URL(c="default", f="download", args=image)
                alt = "%s logo" % org
                logo = IMG(_src=url_small, _alt=alt, _width=width)

    if not logo and fallback_org:
        # Default to fallback org
        logo = org_logo_represent(org=fallback_org, width=width)

    if not logo:
        # Placeholder
        logo = IMG(_src="", _alt="logo", _width=width)

    return (org, logo)

# =============================================================================
def org_customise_org_resource_fields(method):
    """
        Customize org_resource fields for Profile widgets and 'more' popups
    """

    s3db = current.s3db

    table = s3db.org_resource
    table.location_id.represent = s3db.gis_LocationRepresent(sep=" | ")

    list_fields = ["organisation_id",
                   "location_id",
                   "parameter_id",
                   "value",
                   "comments",
                   ]

    if method in ("datalist", "profile"):
        table.modified_by.represent = s3_auth_user_represent_name
        table.modified_on.represent = lambda dt: \
                                S3DateTime.datetime_represent(dt, utc=True)
        list_fields += ["modified_by",
                        "modified_on",
                        "organisation_id$logo",
                        ]

    s3db.configure("org_resource",
                   list_fields = list_fields,
                   )

# =============================================================================
def org_organisation_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Organisations on the Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["org_organisation.id"]
    item_class = "thumbnail" # span6 for 2 cols

    raw = record._row
    name = record["org_organisation.name"]
    logo = raw["org_organisation.logo"]
    phone = raw["org_organisation.phone"] or ""
    website = raw["org_organisation.website"] or ""
    if website:
        website = A(website, _href=website)

    org_url = URL(c="org", f="organisation", args=[record_id, "profile"])
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        logo = DIV(IMG(_class="media-object"),
                   _class="pull-left")

    db = current.db
    permit = current.auth.s3_has_permission
    table = db.org_organisation
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="org", f="organisation",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal dl-item-edit",
                     _title=current.response.s3.crud_strings.org_organisation.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"), _class="dl-item-delete")
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )
    # Render the item
    item = DIV(DIV(logo,
                   DIV(SPAN(A(name,
                              _href=org_url,
                              _class="media-heading"
                              ),
                            ),
                       edit_bar,
                       _class="card-header-select",
                       ),
                   DIV(P(ICON("phone"),
                         " ",
                         phone,
                         _class="card_1_line",
                         ),
                       P(ICON("link"),
                         " ",
                         website,
                         _class="card_1_line",
                         ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def org_resource_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Resources on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["org_resource.id"]
    item_class = "thumbnail"

    raw = record._row
    author = record["org_resource.modified_by"]
    date = record["org_resource.modified_on"]
    quantity = record["org_resource.value"]
    resource_type = record["org_resource.parameter_id"]
    comments = raw["org_resource.comments"]
    organisation = record["org_resource.organisation_id"]
    organisation_id = raw["org_resource.organisation_id"]
    location = record["org_resource.location_id"]
    location_id = raw["org_resource.location_id"]
    location_url = URL(c="gis", f="location",
                       args=[location_id, "profile"])

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    logo = raw["org_organisation.logo"]
    if logo:
        logo = A(IMG(_src=URL(c="default", f="download", args=[logo]),
                     _class="media-object",
                     ),
                 _href=org_url,
                 _class="pull-left",
                 )
    else:
        # @ToDo: use a dummy logo image
        logo = A(IMG(_class="media-object"),
                 _href=org_url,
                 _class="pull-left",
                 )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.org_resource
    if permit("update", table, record_id=record_id):
        link_vars = {"refresh": list_id,
                     "record": record_id,
                     }
        f = current.request.function
        if f == "organisation" and organisation_id:
            link_vars["(organisation)"] = organisation_id
        elif f == "location" and location_id:
            link_vars["(location)"] = location_id
        edit_btn = A(ICON("edit"),
                     _href = URL(c = "org",
                                 f = "resource",
                                 args = [record_id, "update.popup"],
                                 vars = link_vars,
                                 ),
                     _class = "s3_modal",
                     _title = current.response.s3.crud_strings.org_resource.title_update,
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    avatar = logo

    item = DIV(DIV(SPAN("%s %s" % (quantity, current.T(resource_type)), _class="card-title"),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(comments,
                           DIV(author or "" ,
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# END =========================================================================
