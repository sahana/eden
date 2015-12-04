# -*- coding: utf-8 -*-

#try:
#    # Python 2.7
#    from collections import OrderedDict
#except:
#    # Python 2.6
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, A, DIV, H3, TAG, SQLFORM, IS_NOT_EMPTY, IS_EMAIL
from gluon.storage import Storage

def config(settings):
    """
        Template settings for DRR Project Portal

        http://eden.sahanafoundation.org/wiki/Deployments/DRRProjectPortal
    """

    T = current.T

    # Base Settings

    # Pre-Populate
    settings.base.prepopulate += ("DRRPP", "default/users")

    settings.base.system_name = T("DRR Project Portal")
    settings.base.system_name_short = T("DRRPP")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "DRRPP"

    # =============================================================================
    # Auth Settings

    # Security Policy
    settings.security.policy = 6 # Realm
    settings.security.map = True

    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    # Uncomment this to request the Organisation when a user registers
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_pending = \
    """Registration awaiting approval from Administrator or Organisation Contact.
    A confirmation email will be sent to you once approved.
    For enquiries contact %s""" % settings.get_mail_approver()

    # Record Approval
    settings.auth.record_approval = True
    settings.auth.record_approval_required_for = ("org_organisation",
                                                  "project_project",
                                                  "project_framework",
                                                  )

    # =============================================================================
    # L10n Settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
    ])
    settings.L10n.default_language = "en-gb"
    # Default timezone for users
    settings.L10n.utc_offset = "+0700"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Unsortable 'pretty' date format
    #settings.L10n.date_format = "%d-%b-%Y"

    # =============================================================================
    # Finance Settings
    settings.fin.currencies = {
        "EUR" : "Euros",             # Needed for IFRC RMS interop
        "PHP" : "Philippine Pesos",  # Needed for IFRC RMS interop
        "CHF" : "Swiss Francs",      # Needed for IFRC RMS interop
        "USD" : "United States Dollars",
        "NZD" : "New Zealand Dollars",
    }

    # =============================================================================
    # GIS Settings
    # Theme
    settings.gis.map_height = 600
    settings.gis.map_width = 960 # container_12

    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True
    # Deployment only covers Asia-Pacific
    settings.gis.countries = [ "AF", "AU", "BD", "BN", "CK", "CN", "FJ", "FM", "HK", "ID", "IN", "JP", "KH", "KI", "KP", "KR", "LA", "MH", "MM", "MN", "MV", "MY", "NP", "NZ", "PG", "PH", "PK", "PW", "SB", "SG", "SL", "TH", "TL", "TO", "TV", "TW", "VN", "VU", "WS"]
    # Resources which can be directly added to the main map
    settings.gis.poi_create_resources = None

    # =============================================================================
    # Organisation Settings
    # Enable the use of Organisation Branches
    # RMS-compatibility
    settings.org.branches = True

    # =============================================================================
    # Project Settings
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to create a project_location for each country which is a project is implemented in
    # - done via Custom Form instead
    #settings.project.locations_from_countries = True
    # Uncomment this to use multiple Budgets per project
    #settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Uncomment this to disable Sectors in projects
    settings.project.sectors = False
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Lead Organization"),
        2: T("Partner Organization"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        #5: T("Supplier"),
        9: T("Partner Organization"), # Needed for IFRC RMS interop ("Partner National Society")
    }

    # =============================================================================
    # UI Settings
    # Enable this for a UN-style deployment
    settings.ui.cluster = True

    settings.ui.hide_report_options = False
    settings.ui.hide_report_filter_options = True

    # Uncomment to restrict the export formats available
    settings.ui.export_formats = ["xls", "xml"]

    # Uncomment to include an Interim Save button on CRUD forms
    settings.ui.interim_save = True

    # Uncomment to disable responsive behavior of datatables
    # - Disabled until tested
    settings.ui.datatables_responsive = False

    # -----------------------------------------------------------------------------
    # Formstyle
    def formstyle_row(id, label, widget, comment, hidden=False):
        if hidden:
            hide = "hide"
        else:
            hide = ""
        row = DIV(DIV(label,
                      _id=id + "_label",
                      _class="w2p_fl"),
                  DIV(widget,
                      _id=id + "_widget",
                      _class="w2p_fw"),
                  DIV(comment,
                      _id=id + "_comment",
                      _class="w2p_fc"),
                  _id=id,
                  _class = "w2p_r %s" % hide,
                  )
        return row

    # -----------------------------------------------------------------------------
    def formstyle(self, xfields):
        """
            Use new Web2Py formstyle to generate form using DIVs & CSS
            CSS can then be used to create MUCH more flexible form designs:
            - Labels above vs. labels to left
            - Multiple Columns
            @ToDo: Requires further changes to code to use
        """
        form = DIV()

        for id, a, b, c, in xfields:
            form.append(formstyle_row(id, a, b, c))

        return form

    settings.ui.formstyle_row = formstyle_row
    #settings.ui.formstyle = formstyle # Breaks e.g. org/organisation/create
    settings.ui.formstyle = formstyle_row

    # -----------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        tablename = "project_project"
        # Load normal model
        table = s3db[tablename]

        # Custom Components
        s3db.add_components(tablename,
                            project_drrpp={"joinby":"project_id",
                                           "multiple": False,
                                          },
                            project_output="project_id",
                            doc_document=(# Files
                                          {"name": "file",
                                           "joinby": "doc_id",
                                           "filterby": "url",
                                           "filterfor": ("", None),
                                          },
                                          # Links
                                          {"name": "url",
                                           "joinby": "doc_id",
                                           "filterby": "file",
                                           "filterfor": ("", None),
                                          },
                                         ),
                           )

        # Custom Fields
        table.name.label = T("Project Title")
        s3db.project_project.budget.label = T("Total Funding (USD)")
        location_id = s3db.project_location.location_id
        location_id.label = ""

        # Limit to just Countries
        location_id.requires = s3db.gis_country_requires
        # Use dropdown, not AC
        location_id.widget = None

        # In DRRPP this is a free field
        table = s3db.project_organisation
        table.comments.label = T("Role")
        table.comments.widget = SQLFORM.widgets.string.widget
        table.amount.label = T("Amount")
        table = s3db.doc_document
        table.file.widget = lambda field, value, download_url: \
            SQLFORM.widgets.upload.widget(field, value, download_url, _size = 15)
        table.comments.widget = SQLFORM.widgets.string.widget

        # If not logged in, contact person is required
        logged_in = current.auth.is_logged_in()
        if not logged_in:
            table = s3db.project_drrpp
            table.focal_person.required = True
            table.email.required = True
            table.email.requires = IS_EMAIL()

        # Custom dataTable
        s3["dataTable_dom"] = 'ripl<"dataTable_table"t>p'

        # Don't show export buttons for XLS/XML
        s3.formats = Storage(xls=None, xml=None)

        # Remove rheader
        attr["rheader"] = None

        # Only show 10 Project by default to improve load time
        attr["dt_lengthMenu"] = [[ 10, 50, -1], [ 10, 50, T("All")]]
        s3.dataTable_pageLength = 10

        # Custom PreP
        standard_prep = s3.prep
        def custom_prep(r):

            resource = r.resource

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            # Customise list_fields
            if r.method == "review":
                list_fields = ["id",
                               "created_on",
                               "modified_on",
                               "name",
                               "start_date",
                               (T("Countries"), "location.location_id"),
                               (T("Hazards"), "hazard.name"),
                               (T("Lead Organization"), "organisation_id"),
                               (T("Donors"), "donor.organisation_id"),
                              ]
            elif r.representation == "xls":
                # All readable Fields should be exported
                list_fields = ["id",
                               "name",
                               "code",
                               "description",
                               "status_id",
                               "start_date",
                               "end_date",
                               "drrpp.duration",
                               (T("Countries"), "location.location_id"),
                               "drrpp.L1",
                               (T("Hazards"), "hazard.name"),
                               (T("Themes"), "theme.name"),
                               "objectives",
                               "drrpp.activities",
                               "output.name",
                               "drr.hfa",
                               "drrpp.rfa",
                               "drrpp.pifacc",
                               "drrpp.jnap",
                               (T("Lead Organization"), "organisation_id"),
                               (T("Partners"), "partner.organisation_id"),
                               (T("Donors"), "donor.organisation_id"),
                               "budget",
                               "currency",
                               "drrpp.focal_person",
                               "drrpp.organisation_id",
                               "drrpp.email",
                               "url.url",
                               "drrpp.parent_project",
                               "comments",
                              ]
                if logged_in:
                     list_fields.extend(["created_by",
                                         "created_on",
                                         "modified_by",
                                         "modified_on",
                                         ])
            else:
                list_fields = ["id",
                               "name",
                               "start_date",
                               (T("Countries"), "location.location_id"),
                               (T("Hazards"), "hazard.name"),
                               (T("Lead Organization"), "organisation_id"),
                               (T("Donors"), "donor.organisation_id"),
                              ]

            resource.configure(list_fields = list_fields)

            # Customise report_options
            if r.method == "report":
                report_fields = ["name",
                                 (T("Countries"), "location.location_id"),
                                 (T("Hazards"), "hazard.name"),
                                 (T("Themes"), "theme.name"),
                                 (T("HFA Priorities"), "drr.hfa"),
                                 (T("RFA Priorities"), "drrpp.rfa"),
                                 (T("Lead Organization"), "organisation_id"),
                                 (T("Partner Organizations"), "partner.organisation_id"),
                                 (T("Donors"), "donor.organisation_id"),
                                ]

                # Report Settings for charts
                if "chart" in r.get_vars and r.representation != "json":
                    s3.crud_strings[tablename].title_report  = T("Project Graph")
                    report_fact_default = "count(id)"
                    report_facts = [(T("Number of Projects"), "count(id)")]
                    show_table = False
                else:
                    s3.crud_strings[tablename].title_report  = T("Project Matrix")
                    report_fact_default = "count(id)"
                    report_facts = [(T("Number of Projects"), "count(id)"),
                                    (T("Number of Countries"), "count(location.location_id)"),
                                    (T("Number of Hazards"), "count(hazard.id)"),
                                    (T("Number of Themes"), "count(theme.id)"),
                                    (T("Number of HFA Priorities"), "count(drr.hfa)"),
                                    (T("Number of RFA Priorities"), "count(drrpp.rfa)"),
                                    (T("Number of Lead Organizations"), "count(organisation_id)"),
                                    (T("Number of Partner Organizations"), "count(partner.organisation_id)"),
                                    (T("Number of Donors"), "count(donor.organisation_id)"),
                                   ]
                    show_table = True
                report_options = Storage(rows = report_fields,
                                         cols = report_fields,
                                         fact = report_facts,
                                         defaults = Storage(rows = "hazard.name",
                                                            cols = "location.location_id",
                                                            fact = report_fact_default,
                                                            totals = True,
                                                            table = show_table,
                                                           )
                                        )
                resource.configure(report_options = report_options)
                current.deployment_settings.ui.hide_report_options = True

            if r.interactive:

                # Don't show Update/Delete button on Search table
                if r.method is None and not r.id:
                    resource.configure(editable = False,
                                       deletable = False
                                      )

                # JS to show/hide Cook Island fields
                s3.scripts.append("/%s/static/themes/DRRPP/js/drrpp.js" % current.request.application)

                if r.method == "read":
                    table_pl = s3db.project_location
                    table_l = s3db.gis_location
                    countries = [row.name for row in
                                 db((table_pl.project_id == r.record.id) &
                                    (table_pl.location_id == table_l.id)
                                    ).select(table_l.name)
                                 ]
                    if not ("Cook Islands" in countries and len(countries) == 1):
                        s3db.project_drrpp.L1.readable = False
                        s3db.project_drrpp.pifacc.readable = False
                        s3db.project_drrpp.jnap.readable = False

                # Filter Options
                project_hfa_opts = s3db.project_hfa_opts()
                hfa_options = dict((key, "HFA %s" % key)
                                for key in project_hfa_opts)
                #hfa_options[None] = NONE # to search NO HFA
                project_rfa_opts = s3db.project_rfa_opts()
                rfa_options = dict((key, "RFA %s" % key)
                                for key in project_rfa_opts)
                #rfa_options[None] = NONE # to search NO RFA
                project_pifacc_opts = s3db.project_pifacc_opts()
                pifacc_options = dict((key, "PIFACC %s" % key)
                                    for key in project_pifacc_opts)
                #pifacc_options[None] = NONE # to search NO PIFACC
                project_jnap_opts = s3db.project_jnap_opts()
                jnap_options = dict((key, "JNAP %s" % key)
                                    for key in project_jnap_opts)
                #jnap_options[None] = NONE # to search NO JNAP

                # Filter widgets
                from s3 import S3TextFilter, S3OptionsFilter, s3_get_filter_opts
                filter_widgets = [
                    S3TextFilter(["name",
                                  "code",
                                  "description",
                                  "location.location_id",
                                  "hazard.name",
                                  "theme.name",
                                  ],
                                  label = T("Search Projects"),
                                  comment = T("Search for a Project by name, code, or description."),
                                  ),
                    S3OptionsFilter("status_id",
                                    label = T("Status"),
                                    cols = 4,
                                    ),
                    S3OptionsFilter("location.location_id",
                                    label = T("Country"),
                                    cols = 3,
                                    hidden = True,
                                    ),
                    #S3OptionsFilter("drrpp.L1",
                    #                label = T("Cook Islands"),
                    #                cols = 3,
                    #                hidden = True,
                    #                ),
                    S3OptionsFilter("hazard.id",
                                    label = T("Hazard"),
                                    options = lambda: \
                                        s3_get_filter_opts("project_hazard",
                                                           translate=True),
                                    help_field = s3db.project_hazard_help_fields,
                                    cols = 4,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("theme.id",
                                    label = T("Theme"),
                                    options = lambda: \
                                        s3_get_filter_opts("project_theme",
                                                           translate=True),
                                    help_field = s3db.project_theme_help_fields,
                                    cols = 4,
                                    # Don't group
                                    size = None,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("drr.hfa",
                                    label = T("HFA"),
                                    options = hfa_options,
                                    help_field = project_hfa_opts,
                                    cols = 5,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("drrpp.rfa",
                                    label = T("RFA"),
                                    options = rfa_options,
                                    help_field = project_rfa_opts,
                                    cols = 6,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("drrpp.pifacc",
                                    label = T("PIFACC"),
                                    options = pifacc_options,
                                    help_field = project_pifacc_opts,
                                    cols = 6,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("drrpp.jnap",
                                    label = T("JNAP"),
                                    options = jnap_options,
                                    help_field = project_jnap_opts,
                                    cols = 6,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("organisation_id",
                                    label = T("Lead Organization"),
                                    cols = 3,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("partner.organisation_id",
                                    label = T("Partners"),
                                    cols = 3,
                                    hidden = True,
                                    ),
                    S3OptionsFilter("donor.organisation_id",
                                    label = T("Donors"),
                                    cols = 3,
                                    hidden = True,
                                    )
                ]

                resource.configure(filter_widgets=filter_widgets)
            return True
        s3.prep = custom_prep

        # Custom Crud Form
        from s3.s3forms import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineComponentCheckbox
        crud_form = S3SQLCustomForm(
            "name",
            "code",
            "description",
            "status_id",
            "start_date",
            "end_date",
            "drrpp.duration",
            S3SQLInlineComponent(
                "location",
                label = T("Countries"),
                fields = ["location_id"],
                orderby = "location_id$name",
                render_list = True
            ),
            "drrpp.L1",
            S3SQLInlineComponentCheckbox(
                "hazard",
                label = T("Hazards"),
                field = "hazard_id",
                option_help = "comments",
                cols = 4,
            ),
            S3SQLInlineComponentCheckbox(
                "theme",
                label = T("Themes"),
                field = "theme_id",
                option_help = "comments",
                cols = 3,
            ),
            "objectives",
            "drrpp.activities",
            # Outputs
            S3SQLInlineComponent(
                "output",
                label = T("Outputs"),
                fields = ["name", "status"],
            ),
            "drr.hfa",
            "drrpp.rfa",
            "drrpp.pifacc",
            "drrpp.jnap",
            "organisation_id",
            # Partner Orgs
            S3SQLInlineComponent(
                "organisation",
                name = "partner",
                label = T("Partner Organizations"),
                fields = ["organisation_id",
                          "comments", # NB This is labelled 'Role' in DRRPP
                          ],
                filterby = dict(field = "role",
                                options = [2, 9]),
                default = {"role": 2}
            ),
            # Donors
            S3SQLInlineComponent(
                "organisation",
                name = "donor",
                label = T("Donor(s)"),
                fields = ["organisation_id",
                          "amount",
                          "currency",
                          ],
                filterby = dict(field = "role",
                                options = [3]),
                default = {"role": 3}
            ),
            "budget",
            "drrpp.local_budget",
            "drrpp.local_currency",
            "drrpp.focal_person",
            "drrpp.organisation_id",
            "drrpp.email",
            # Files
            S3SQLInlineComponent(
                "document",
                name = "file",
                label = T("Files"),
                fields = ["file", "comments"],
                filterby = dict(field = "file",
                                options = "",
                                invert = True,
                                )
            ),
            # Links
            S3SQLInlineComponent(
                "document",
                name = "url",
                label = T("Links"),
                fields = ["url", "comments"],
                filterby = dict(field = "url",
                                options = None,
                                invert = True,
                                )
            ),
            "drrpp.parent_project",
            "comments",
        )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       subheadings = {1: "hazard",
                                      2: "theme",
                                      3: "objectives",
                                      4: "drr_hfa",
                                      5: "drrpp_rfa",
                                      6: "drrpp_pifacc",
                                      7: "drrpp_jnap",
                                      8: "organisation_id",
                                     },
                       )

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -----------------------------------------------------------------------------
    def customise_project_framework_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Load normal model
        table = s3db.project_framework

        # Custom CRUD Strings
        s3.crud_strings.project_framework.title_list = \
            T("Policies & Strategies List")

        # Custom PreP
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                output = standard_prep(r)
            else:
                output = True
            if r.interactive:
                # Don't show Update/Delete button on List View
                if r.method is None:
                    s3db.configure("project_framework",
                                   deletable = False,
                                   editable = False,
                                   insertable = False,
                                   )
            return output
        s3.prep = custom_prep

        return attr

    settings.customise_project_framework_controller = customise_project_framework_controller

    # -----------------------------------------------------------------------------
    def customise_project_location_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Load normal model
        table = s3db.project_location

        # Custom Components
        s3db.add_components("project_project",
                            project_drrpp = {"joinby": "project_id",
                                             "multiple": False,
                                             },
                            )

        # Custom CRUD Strings
        s3.crud_strings.project_location.title_map = T("Project Map")

        # Custom Search Filters
        from s3.s3filter import S3TextFilter, S3OptionsFilter, S3LocationFilter
        filter_widgets = [
            S3TextFilter(["project_id$name",
                          "project_id$code",
                          "project_id$description",
                          #"location_id$name",
                          #"project_id$organisation.name",
                          #"project_id$organisation.acronym",
                          ],
                         label=T("Search Projects"),
                         _class="filter-search",
                         ),
            S3OptionsFilter("project_id$status_id",
                            label = T("Status"),
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 3,
                            #hidden=True,
                            ),
            S3LocationFilter("location_id",
                             label = T("Country"),
                             levels = ("L0",),
                             widget = "groupedpts",
                             #widget = "multiselect",
                             cols = 3,
                             hidden = True,
                             ),
            S3OptionsFilter("project_id$hazard_project.hazard_id",
                            label = T("Hazard"),
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 4,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$theme_project.theme_id",
                            label = T("Theme"),
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 4,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$drr.hfa",
                            label = T("HFA"),
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 5,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$drrpp.rfa",
                            label = T("RFA"),
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 6,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$organisation_id",
                            label = T("Lead Organization"),
                            represent = "%(name)s",
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 3,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$partner.organisation_id",
                            label = T("Partners"),
                            represent = "%(name)s",
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 3,
                            hidden = True,
                            ),
            S3OptionsFilter("project_id$donor.organisation_id",
                            label = T("Donors"),
                            represent = "%(name)s",
                            widget = "groupedpts",
                            #widget = "multiselect",
                            cols = 3,
                            hidden = True,
                            ),
            ]

        s3db.configure("project_location",
                       filter_widgets = filter_widgets,
                       # Add CSS to default class better than patching
                       #map_submit = (T("Search"), "search-button"),
                       map_advanced = (T("Advanced Search"), T("Simple Search")),
                       )

        return attr

    settings.customise_project_location_controller = customise_project_location_controller

    # -----------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):
        """
            Customise pr_person controller

            @todo: SavedSearch deprecated,
                   re-implement with saved filters / S3Notify
        """

        s3db = current.s3db
        # Load normal model
        table = s3db.pr_person

        # Custom CRUD Strings
        current.response.s3.crud_strings.pr_person.title_display = T("My Page")

        # Customise saved search
        #table = s3db.pr_saved_search
        #table.url.label = T("Display Search")
        #
        #def url_represent(url):
        #    return TAG[""](
        #            A(T("List"),
        #                _href = url,
        #                _class = "action-btn"
        #                ),
        #            A(T("Matrix"),
        #                # @ToDo: Fix for S3Search deprecation
        #                _href = url.replace("search", "report"),
        #                _class = "action-btn"
        #                ),
        #            A(T("Chart"),
        #                # @ToDo: Fix for S3Search deprecation
        #                _href = url.replace("search", "report?chart=breakdown%3Arows"),
        #                _class = "action-btn"
        #                ),
        #            A(T("Map"),
        #                # @ToDo: Fix for S3Search deprecation
        #                _href = url.replace("project/search", "location/map"),
        #                _class = "action-btn"
        #                )
        #            )
        #table.url.represent = url_represent
        #
        #s3db.configure("pr_saved_search",
        #               list_fields = ["name",
        #                              "url",
        #                              ]
        #               )
        #
        #attr["rheader"] = H3(T("Saved Searches"))

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -----------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):
        """
            Customise org_organisation controller to just show Name field
        """

        s3 = current.response.s3

        # Custom PreP
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                output = standard_prep(r)
            else:
                output = True
            if r.interactive and r.method == "create":
                table = current.s3db.org_organisation
                for field in table:
                    if field.name != "name":
                        field.readable = field.writable = False
            return output
        s3.prep = custom_prep

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # =============================================================================
    # Enabled Modules
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
                name_nice = T("Home"),
                restricted = False, # Use ACLs to control access to this module
                access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
                module_type = None  # This item is not shown in the menu
            )),
        ("admin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = "Needed for Breadcrumbs",
                restricted = False,
                module_type = None  # No Menu
            )),
        ("sync", Storage(
                name_nice = T("Synchronization"),
                #description = "Synchronization",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = "Situation Awareness & Geospatial Analysis",
                restricted = True,
                module_type = 3,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Person Registry"),
                #description = "Central point to record details on People",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                module_type = None
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
                restricted = True,
                module_type = 2
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                module_type = None,
            )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = "A library of digital resources, such as photos, documents and reports",
                restricted = True,
                module_type = None,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = "Sends & Receives Alerts via Email & SMS",
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                module_type = None,
            )),
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                module_type = 1
            )),
        # Stats required if using beneficiary model
        #("stats", Storage(
        #       name_nice = T("Statistics"),
        #       #description = "Manages statistics",
        #       restricted = True,
        #       module_type = None,
        #   )),
    ])

# END =========================================================================
