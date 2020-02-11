# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for the Default template
        - default settings suitable for a small organisation managing it's own resources
    """

    T = current.T

    # Pre-Populate
    # http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/PrePopulate
    # Configure/disable pre-population of the database.
    # To pre-populate the database On 1st run should specify directory(s) in
    # /modules/templates/
    # eg:
    # ["default"] (1 is a shortcut for this)
    # ["default", "default/users"]
    # Unless doing a manual DB migration, where prepopulate = 0
    # In Production, prepopulate = 0 (to save 1x DAL hit every page)
    settings.base.prepopulate.append("default")

    # Uncomment this to prefer scalability-optimized strategies globally
    #settings.base.bigtable = True

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "default"

    # Enable Guided Tours
    # - defaults to module enabled or not
    #settings.base.guided_tour = True

    # Authentication settings
    # These settings should be changed _after_ the 1st (admin) user is
    # registered in order to secure the deployment
    # Should users be allowed to register themselves?
    #settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    # Disable welcome-emails to newly registered users
    #settings.auth.registration_welcome_email = False

    # Allow a new user to be linked to a record (and a new record will be created if it doesn't already exist)
    #settings.auth.registration_link_user_to = {"staff": T("Staff"),
    #                                           "volunteer": T("Volunteer"),
    #                                           "member": T("Member"),
    #                                           }

    # Always notify the approver of a new (verified) user, even if the user is automatically approved
    #settings.auth.always_notify_approver = False

    # The name of the teams that users are added to when they opt-in to receive alerts
    #settings.auth.opt_in_team_list = ["Updates"]
    # Uncomment this to set the opt in default to True
    #settings.auth.opt_in_default = True
    # Uncomment this to request the Home Phone when a user registers
    #settings.auth.registration_requests_home_phone = True
    # Uncomment this to request the Mobile Phone when a user registers
    #settings.auth.registration_requests_mobile_phone = True
    # Uncomment this to have the Mobile Phone selection during registration be mandatory
    #settings.auth.registration_mobile_phone_mandatory = True
    # Uncomment this to request the Organisation when a user registers
    #settings.auth.registration_requests_organisation = True
    # Uncomment this to have the Organisation selection during registration be mandatory
    #settings.auth.registration_organisation_required = True
    # Uncomment this to hide the Create-Organisation link in registration forms
    #settings.auth.registration_organisation_link_create = False
    # Uncomment this to have the Organisation input hidden unless the user enters a non-whitelisted domain
    #settings.auth.registration_organisation_hidden = True
    # Uncomment this to default the Organisation during registration
    #settings.auth.registration_organisation_default = "My Organisation"
    # Uncomment this to request the Organisation Group when a user registers
    #settings.auth.registration_requests_organisation_group = True
    # Uncomment this to have the Organisation Group selection during registration be mandatory
    #settings.auth.registration_organisation_group_required = True
    # Uncomment this to request the Site when a user registers
    #settings.auth.registration_requests_site = True
    # Uncomment this to allow Admin to see Organisations in User Admin even if the Registration doesn't request this
    #settings.auth.admin_sees_organisation = True
    # Uncomment to set the default role UUIDs assigned to newly-registered users
    # This is a dictionary of lists, where the key is the realm that the list of roles applies to
    # The key 0 implies not realm restricted
    # The keys "organisation_id" and "site_id" can be used to indicate the user's "organisation_id" and "site_id"
    #settings.auth.registration_roles = { 0: ["STAFF", "PROJECT_EDIT"]}
    # Whether the first user to register for an Org should get the ORG_ADMIN role for that Org
    #settings.auth.org_admin_to_first = True
    # Define which entity types to use as realm entities in role manager
    #settings.auth.realm_entity_types = ("org_organisation",)
    # Uncomment to activate entity role manager tabs for OrgAdmins
    #settings.auth.entity_role_manager = True
    # Define modules for entity role manager
    #settings.auth.role_modules = OrderedDict([])
    # Define access levels for entity role manager
    #settings.auth.access_levels = OrderedDict([])
    # Uncomment this to enable record approval
    #settings.auth.record_approval = True
    # Uncomment this and specify a list of tablenames for which record approval is required
    #settings.auth.record_approval_required_for = ("org_organisation",)
    # Uncomment this to request an image when users register
    #settings.auth.registration_requests_image = True
    # Uncomment this to direct newly-registered users to their volunteer page to be able to add extra details
    # NB This requires Verification/Approval to be Off
    # @ToDo: Extend to all optional Profile settings: Homepage, Twitter, Facebook, Mobile Phone, Image
    #settings.auth.registration_volunteer = True
    # Terms of Service to be able to Register on the system
    # https://termsfeed.com/terms-conditions/generator/
    # uses <template>/views/tos.html
    #settings.auth.terms_of_service = True
    # Enable options for tracking user consent
    #settings.auth.consent_tracking = True
    # Uncomment this to allow users to Login using Gmail's SMTP
    #settings.auth.gmail_domains = ["gmail.com"]
    # Uncomment this to allow users to Login using Office365's SMTP
    #settings.auth.office365_domains = ["microsoft.com"]
    # Uncomment this to allow users to Login using OpenID
    #settings.auth.openid = True
    # Uncomment this to allow users to login using master key
    #settings.auth.masterkey = True
    # Uncomment this to block password changes since managed externally (OpenID / SMTP / LDAP)
    #settings.auth.password_changes = False
    # Uncomment this to disable password retrieval (e.g. if impractical or unsafe)
    #settings.auth.password_retrieval = False
    # Uncomment this to enable presence records on login based on HTML5 geolocations
    #settings.auth.set_presence_on_login = True
    # Uncomment this and specify a list of location levels to be ignored by presence records
    #settings.auth.ignore_levels_for_presence = ("L0", "L1", "L2", "L3")
    # Uncomment this to enable the creation of new locations if a user logs in from an unknown location. Warning: This may lead to many useless location entries
    #settings.auth.create_unknown_locations = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "Arabic"),
        ("bs", "Bosnian"),
        #("crs", "Seychellois Creole"),
        #("dv", "Divehi"), # Maldives
        #("dz", "Dzongkha"), # Bhutan
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
        ("el", "Greek"),
        ("es", "Spanish"),
        #("id", "Bahasa Indonesia"),
        ("it", "Italian"),
        ("ja", "Japanese"),
        ("km", "Khmer"), # Cambodia
        ("ko", "Korean"),
        #("lo", "Lao"),
        #("lt", "Lithuanian"),
        #("mg", "Malagasy"),
        ("mn", "Mongolian"),
        #("ms", "Malaysian"),
        ("my", "Burmese"), # Myanmar
        ("ne", "Nepali"),
        ("prs", "Dari"), # Afghan Persian
        ("ps", "Pashto"), # Afghanistan, Pakistan
        ("pt", "Portuguese"),
        ("pt-br", "Portuguese (Brazil)"),
        ("ru", "Russian"),
        ("tet", "Tetum"),
        #("si", "Sinhala"), # Sri Lanka
        #("so", "Somali"),
        #("ta", "Tamil"), # India, Sri Lanka
        ("th", "Thai"),
        ("tl", "Tagalog"), # Philippines
        ("tr", "Turkish"),
        ("ur", "Urdu"), # Pakistan
        ("vi", "Vietnamese"),
        ("zh-cn", "Chinese (Simplified)"), # Mainland China
        ("zh-tw", "Chinese (Taiwan)"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    #settings.L10n.default_language = "en"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    #settings.L10n.timezone = "US/Eastern"
    # Uncomment these to use US-style dates in English
    #settings.L10n.date_format = "%m-%d-%Y"
    #settings.L10n.time_format = "%H:%M:%S"
    # Start week on Sunday
    #settings.L10n.firstDOW = 0
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    #settings.L10n.thousands_separator = ","
    # Default Country Code for telephone numbers
    #settings.L10n.default_country_code = 1
    # Make last name in person/user records mandatory
    #settings.L10n.mandatory_lastname = True
    # Configure the list of Religions
    #settings.L10n.religions = {"none": T("none"),
                            #"christian": T("Christian"),
                            #"muslim": T("Muslim"),
                            #"jewish": T("Jewish"),
                            #"buddhist": T("Buddhist"),
                            #"hindu": T("Hindu"),
                            #"bahai": T("Bahai"),
                            #"other": T("other")
                            #}
    # Uncomment this to Translate CMS Series Names
    #settings.L10n.translate_cms_series = True
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    #settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Uncomment this to Translate Site Names
    #settings.L10n.translate_org_site = True

    # Finance settings
    #settings.fin.currencies = {
    #    "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    #}
    #settings.fin.currency_default = "USD"
    #settings.fin.currency_writable = False # False currently breaks things

    # PDF settings
    # Default page size (defaults to A4)
    #settings.base.pdf_size = "Letter"
    # Default page orientation (defaults to "Auto" to auto-adapt for wide tables)
    #settings.base.pdf_orientation = "Landscape"
    # Location of Logo used in pdfs headers
    #settings.ui.pdf_logo = "static/img/mylogo.png"
    # Maximum number of records in PDF exports (None for unlimited)
    #settings.base.pdf_max_rows = 1000

    #Uncomment to add a title row to XLS exports
    #settings.base.xls_title_row = True

    # GIS (Map) settings
    # Size of the Embedded Map
    # Change this if-required for your theme
    # NB API can override this in specific modules
    #settings.gis.map_height = 600
    #settings.gis.map_width = 1000
    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("US",)
    # Uncomment to pass Addresses imported from CSV to a Geocoder to try and automate Lat/Lon
    #settings.gis.geocode_imported_addresses = "google"
    # Hide the Map-based selection tool in the Location Selector
    #settings.gis.map_selector = False
    # Show LatLon boxes in the Location Selector
    #settings.gis.latlon_selector = True
    # Use Building Names as a separate field in Street Addresses?
    #settings.gis.building_name = False
    # Use a non-default fillColor for Clustered points
    #settings.gis.cluster_fill = "8087ff"
    # Disable the label for clustered points
    #settings.gis.cluster_label = False
    # Use a non-default strokeColor for Clustered points
    #settings.gis.cluster_stroke = "2b2f76"
    # Use a non-default fillColor for Selected points
    #settings.gis.select_fill = "ffdc33"
    # Use a non-default strokeColor for Selected points
    #settings.gis.select_stroke = "ff9933"
    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    # Uncomment to fall back to country LatLon to show resources, if nothing better available
    #settings.gis.display_L0 = True
    # Currently unused
    #settings.gis.display_L1 = False
    # Uncomment this to do deduplicate lookups on Imports via PCode (as alternative to Name)
    #settings.gis.lookup_code = "PCode"
    # Set this if there will be multiple areas in which work is being done,
    # and a menu to select among them is wanted.
    #settings.gis.menu = "Maps"
    # Maximum Marker Size
    # (takes effect only on display)
    #settings.gis.marker_max_height = 35
    #settings.gis.marker_max_width = 30
    # Duplicate Features so that they show wrapped across the Date Line?
    # Points only for now
    # lon<0 have a duplicate at lon+360
    # lon>0 have a duplicate at lon-360
    #settings.gis.duplicate_features = True
    # Uncomment to use CMS to provide Metadata on Map Layers
    #settings.gis.layer_metadata = True
    # Uncomment to show Clear Layers tool
    #settings.gis.clear_layers = True
    # Uncomment to hide the Geolocation control
    #settings.gis.geolocate_control = False
    # Uncomment to hide the WMS GetFeatureInfo control
    #settings.gis.getfeature_control = False
    # Uncomment to hide Layer Properties tool
    #settings.gis.layer_properties = False
    # Uncomment to hide the Base Layers folder in the LayerTree
    #settings.gis.layer_tree_base = False
    # Uncomment to hide the Overlays folder in the LayerTree
    #settings.gis.layer_tree_overlays = False
    # Uncomment to change the label of the Overlays folder in the LayerTree
    #settings.gis.label_overlays = "Overlays"
    # Uncomment to not expand the folders in the LayerTree by default
    #settings.gis.layer_tree_expanded = False
    # Uncomment to have custom folders in the LayerTree use Radio Buttons
    #settings.gis.layer_tree_radio = True
    # Uncomment to display the Map Legend as a floating DIV
    #settings.gis.legend = "float"
    # Uncomment to use scalability-optimized options lookups in location filters
    #settings.gis.location_filter_bigtable_lookups = True
    # Uncomment to prevent showing LatLon in Location Represents
    #settings.gis.location_represent_address_only = True
    # Mouse Position: 'normal', 'mgrs' or None
    #settings.gis.mouse_position = "mgrs"
    # Uncomment to show the Navigation controls on the toolbar
    #settings.gis.nav_controls = True
    # Uncomment to hide the Overview map
    #settings.gis.overview = False
    # Uncomment to hide the permalink control
    #settings.gis.permalink = False
    # Resources which can be directly added to the main map
    #settings.gis.poi_create_resources = None
    #settings.gis.poi_create_resources = [{"c":"event", "f":"incident_report", "table": "gis_poi", "label": T("Add Incident Report") ,"tooltip": T("Add Incident Report"), "layer":"Incident Reports", "location": "popup"}]
    # PoIs to export in KML/OSM feeds from Admin locations
    #settings.gis.poi_export_resources = ["cr_shelter", "hms_hospital", "org_office"]
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True
    # Uncomment to save a screenshot whenever a saved map is saved
    #settings.gis.config_screenshot = (820, 410)
    # Uncomment to hide the Save control, or set to "float"
    #settings.gis.save = False
    # Uncomment to hide the ScaleLine control
    #settings.gis.scaleline = False
    # Uncomment to hide the GeoNames search box
    #settings.gis.search_geonames = False
    # Uncomment to modify the Simplify Tolerance
    #settings.gis.simplify_tolerance = 0.001
    # Uncomment this for highly-zoomed maps showing buildings
    #settings.gis.precision = 5
    # Uncomment to Hide the Toolbar from the main Map
    #settings.gis.toolbar = False
    # Uncomment to show Catalogue Layers in Map Widgets (e.g. Profile & Summary pages)
    #settings.gis.widget_catalogue_layers = True
    # Uncomment to show WMS Browser in Map Widgets (e.g. Profile & Summary pages)
    # - NB This also requires the active gis_config to have one configured
    #settings.gis.widget_wms_browser = True
    # Uncomment to hide the Zoom control
    #settings.gis.zoomcontrol = False
    # Uncomment to open Location represent links in a Popup Window
    #settings.gis.popup_location_link = True
    # Uncomment to include WKT in XML exports
    #settings.gis.xml_wkt = True
    # GeoNames username
    settings.gis.geonames_username = "eden_test"

    # Messaging Settings
    # If you wish to use a parser.py in another folder than "default"
    #settings.msg.parser = "mytemplatefolder"
    # Uncomment to turn off enforcement of E.123 international phone number notation
    #settings.msg.require_international_phone_numbers = False
    # Uncomment to make basestation codes unique
    #settings.msg.basestation_code_unique = True

    # Use 'soft' deletes
    #settings.security.archive_not_delete = False

    # AAA Settings

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    #settings.security.policy = 7 # Organisation-ACLs

    # Ownership-rule for records without owner:
    # True = not owned by any user (strict ownership, default)
    # False = owned by any authenticated user
    #settings.security.strict_ownership = False

    # Audit
    # - can be a callable for custom hooks (return True to also perform normal logging, or False otherwise)
    # NB Auditing (especially Reads) slows system down & consumes diskspace
    #settings.security.audit_read = True
    #settings.security.audit_write = True

    # Lock-down access to Map Editing
    #settings.security.map = True
    # Allow non-MapAdmins to edit hierarchy locations? Defaults to True if not set.
    # (Permissions can be set per-country within a gis_config)
    #settings.gis.edit_Lx = False
    # Allow non-MapAdmins to edit group locations? Defaults to False if not set.
    #settings.gis.edit_GR = True
    # Note that editing of locations used as regions for the Regions menu is always
    # restricted to MapAdmins.
    # Uncomment to disable that LatLons are within boundaries of their parent
    #settings.gis.check_within_parent_boundaries = False
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False

    # Increase these if having scalability issues or slow connections
    #settings.ui.autocomplete_delay = 800
    #settings.ui.autocomplete_min_chars = 2
    #settings.ui.filter_auto_submit = 800
    #settings.ui.report_auto_submit = 800
    # Enable this for a UN-style deployment
    #settings.ui.cluster = True
    # Enable this to use the label 'Camp' instead of 'Shelter'
    #settings.ui.camp = True
    # Enable this to have Open links in IFrames open a full page in a new tab
    #settings.ui.iframe_opens_full = True
    # Enable this to change the label for 'Attachments' tabs
    #settings.ui.label_attachments = "Attachments"
    # Uncomment to configure the LocationSelector labels for the Map button with Points
    #settings.label_locationselector_map_point_add = "Find on Map"
    #settings.label_locationselector_map_point_view = "Find on Map"
    # Enable this to change the label for 'Mobile Phone'
    #settings.ui.label_mobile_phone = "Cell Phone"
    # Enable this to change the label for 'Postcode'
    #settings.ui.label_postcode = "ZIP Code"
    # Enable Social Media share buttons
    #settings.ui.social_buttons = True
    # Enable this to show pivot table options form by default
    #settings.ui.hide_report_options = False
    # Uncomment to show created_by/modified_by using Names not Emails
    #settings.ui.auth_user_represent = "name"
    # Uncomment to control the dataTables layout: https://datatables.net/reference/option/dom
    # Default:
    #settings.ui.datatables_dom = "fril<'dataTable_table't>pi"
    # dataTables.Foundation.js would set to this:
    #settings.ui.datatables_dom = "<'row'<'large-6 columns'l><'large-6 columns'f>r>t<'row'<'large-6 columns'i><'large-6 columns'p>>"
    # Move the export_formats after the pagination control
    #settings.ui.datatables_initComplete = '''$('.dataTables_paginate').after($('.dt-export-options'))'''
    # Uncomment for dataTables to use a different paging style:
    #settings.ui.datatables_pagingType = "bootstrap"
    # Uncomment to restrict the export formats available
    #settings.ui.export_formats = ("kml", "pdf", "rss", "xls", "xml")
    # Uncomment to change the label/class of FilterForm clear buttons
    #settings.ui.filter_clear = "Clear"
    # Uncomment to include an Interim Save button on CRUD forms
    #settings.ui.interim_save = True
    # Uncomment to enable icons on action buttons (requires corresponding CSS)
    #settings.ui.use_button_icons = True
    # Uncomment to use S3MultiSelectWidget on all dropdowns (currently the Auth Registration page & LocationSelectorWidget2 listen to this)
    #settings.ui.multiselect_widget = True
    # Theme for the S3HierarchyWidget
    #settings.ui.hierarchy_theme = dict(css = "../themes/MYTHEME",
    #                                   icons = True,
    #                                   stripes = False,
    #                                   )
    # Uncomment to show a default cancel button in standalone create/update forms
    #settings.ui.default_cancel_button = True
    # Uncomment to disable responsive behavior of datatables
    #settings.ui.datatables_responsive = False
    # Uncomment to enable double scroll bars on non-responsive datatables
    #settings.ui.datatables_double_scroll = True
    # Uncomment to modify the label of the Permalink
    #settings.ui.label_permalink = "Permalink"
    # Uncomment to modify the main menu logo
    #settings.ui.menu_logo = URL(c="static", f="img", args=["S3menulogo.png"])
    # Configure business hours to indicate in organizer (can be a list)
    #settings.ui.organizer_business_hours = {"dow": [1,2,3,4,5], "start": "08:00", "end": "18:00"}
    # Configure a time format for organizer events to override locale default
    #settings.ui.organizer_time_format = "H:mm"
    # Configure the snap raster width in organizer (hh:mm:ss)
    #settings.ui.organizer_snap_duration = "00:15:00"

    # -------------------------------------------------------------------------
    # Sync
    # Uncomment if this deployment exposes public data sets
    #settings.sync.data_repository = True

    # -------------------------------------------------------------------------
    # Asset
    # Uncomment to have a specific asset type for Telephones
    #settings.asset.telephones = True

    # -------------------------------------------------------------------------
    # Beneficiary Registry

    # --- Terminology ---
    # Terminology to use when referring to cases (Beneficiary|Client|Case)
    #settings.br.case_terminology = "Beneficiary"
    # Terminology to use when referring to measures of assistance (Counseling|Assistance)
    #settings.br.assistance_terminology = "Counseling"

    # --- Need Categories ---
    # Use hierarchical need categories
    #settings.br.needs_hierarchical = True
    # Let all orgs use a common set of need categories
    #settings.br.needs_org_specific = False

    # --- Basic Case Options ---
    # Show the case organisation even if only one option
    #settings.br.case_hide_default_org = False
    # Disable assignment of cases to staff
    #settings.br.case_manager = False
    # Expose fields to track home address in case file
    #settings.br.case_address = True
    # Disable documentation of language details in case file
    #settings.br.case_language_details = False
    # Control household size tracking in case files: False, True or "auto" (=default)
    #settings.br.household_size = "auto"
    # Layout class for beneficiary ID cards
    #settings.br.id_card_layout = IDCardLayout
    # User roles with permission to export beneficiary ID cards
    #settings.br.id_card_export_roles = ["ORG_ADMIN", "CASE_MANAGEMENT"]

    # --- Case File Tabs ---
    # Hide the contact info tab in case files
    #settings.br.case_contacts_tab = False
    # Show the ID-tab in case files
    #settings.br.case_id_tab = True
    # Hide the family members tab in case files
    #settings.br.case_family_tab = False
    # Enable case file tab to track service contacts
    #settings.br.service_contacts = True
    # Show tab with notes journal
    #settings.br.case_notes_tab = True
    # Show the photos-tab in case files
    #settings.br.case_photos_tab = True
    # Hide the documents-tab in case files
    #settings.br.case_documents_tab = False

    # --- Attachments ---
    # Hide activity attachments from case documents-tab
    #settings.br.case_include_activity_docs = False
    # Hide case group attachments from case documents-tab
    #settings.br.case_include_group_docs = False

    # --- Case Activities ---
    # Disable tracking of case activities
    #settings.br.case_activities = False
    # Disable assignment of case activities to staff
    #settings.br.case_activity_manager = False
    # Expose "urgent" priority for case activities (=emergencies)
    #settings.br.case_activity_urgent_option = True
    # Disable need categories in case activities
    #settings.br.case_activity_need = False
    # Use a free-text subject line in case activities
    #settings.br.case_activity_subject = True
    # Use a free-text field to document need details in case activities
    #settings.br.case_activity_need_details = True
    # Disable status and end-date for case activities
    #settings.br.case_activity_status = False
    # Show end-date of case activites (True=show, "writable"=allow manual edit)
    #settings.br.case_activity_end_date = True
    # Enable inline-updates of case activities
    #settings.br.case_activity_updates = True
    # Disable fields for outcome documentation
    #settings.br.case_activity_outcome = False
    # Allow documents to be attached to case activities
    #settings.br.case_activity_documents = True

    # --- Assistance Measures ---
    # Disable tracking of individual assistance measures
    #settings.br.manage_assistance = False
    # Use separate tab to track assistance measures
    #settings.br.assistance_tab = True
    # Hide inline assistance measures on case activity tab
    #settings.br.assistance_inline = False
    # Document date+time (rather than only date) for assistance measures
    #settings.br.assistance_measures_use_time = True
    # Set default status of assistance measures to closed
    #settings.br.assistance_measure_default_closed = True
    # Disable assignment of assistance measures to staff
    #settings.br.assistance_manager = False
    # Disable types of assistance (e.g. if there is only one type)
    #settings.br.assistance_types = False

    # --- Assistance Themes ---
    # Enable assistance themes
    #settings.br.assistance_themes = True
    # Use a common set of assistance themes rather than org-specific
    #settings.br.assistance_themes_org_specific = False
    # Organize assistance themes by org sector
    #settings.br.assistance_themes_sectors = True
    # Organize assistance themes by need type
    #settings.br.assistance_themes_needs = True
    # Document assistance details per theme
    #settings.br.assistance_details_per_theme = True
    # Enable auto-linking of assistance measure details to case activities
    #settings.br.assistance_activity_autolink = True
    # Disable tracking of effort (=hours spent) for assistance measures
    #settings.br.assistance_track_effort = False

    # -------------------------------------------------------------------------
    # CMS
    # Uncomment this to hide CMS from module index pages
    #settings.cms.hide_index = True
    # Uncomment to use Bookmarks in Newsfeed
    #settings.cms.bookmarks = True
    # Uncomment to use have Filter form in Newsfeed be open by default
    #settings.cms.filter_open = True
    # Uncomment to adjust filters in Newsfeed when clicking on locations instead of opening the profile page
    #settings.cms.location_click_filters = True
    # Uncomment to use Rich Text editor in Newsfeed
    #settings.cms.richtext = True
    # Uncomment to show Events in Newsfeed
    #settings.cms.show_events = True
    # Uncomment to hide Attachments in Newsfeed
    #settings.cms.show_attachments = False
    # Uncomment to show Links in Newsfeed
    #settings.cms.show_links = True
    # Uncomment to show Tags in Newsfeed
    #settings.cms.show_tags = True
    # Uncomment to show post Titles in Newsfeed
    #settings.cms.show_titles = True
    # Uncomment to use organisation_id instead of created_by in Newsfeed
    #settings.cms.organisation = "post_organisation.organisation_id"
    # Uncomment to use org_group_id in Newsfeed
    #settings.cms.organisation_group = "created_by$org_group_id"
    #settings.cms.organisation_group = "post_organisation_group.group_id"
    # Uncomment to use person_id instead of created_by in Newsfeed
    #settings.cms.person = "person_id"

    # -------------------------------------------------------------------------
    # Shelters
    # Uncomment to use a dynamic population estimation by calculations based on registrations
    #settings.cr.shelter_population_dynamic = True
    # Uncomment to disable people registration in shelters
    #settings.cr.people_registration = False
    # Uncomment to use Tags for Shelters
    #settings.cr.tags = True
    # Uncomment to generate tasks from shelter inspections (requires project module)
    #settings.cr.shelter_inspection_tasks = True
    # Configure active statuses for shelter inspection tasks (subset of project.task_status_opts)
    #settings.cr.shelter_inspection_task_active_statuses = (2, 3, 6)

    # -------------------------------------------------------------------------
    # Disaster Victim Registry / Case Management

    # Uncomment to use the term Beneficiary instead of Case
    #settings.dvr.label = "Beneficiary"

    # Uncomment this to enable tracking of transfer origin/destination sites
    #settings.dvr.track_transfer_sites = True
    # Uncomment this to enable features to manage transferability of cases
    #settings.dvr.manage_transferability = True

    # Uncomment this to enable household size in cases, set to "auto" for automatic counting
    #settings.dvr.household_size = True

    # Uncomment this to expose flags to mark appointment types as mandatory
    #settings.dvr.mandatory_appointments = True
    # Uncomment this to have appointments with personal presence update last_seen_on
    #settings.dvr.appointments_update_last_seen_on = True
    # Uncomment this to automatically update the case status when appointments are completed
    #settings.dvr.appointments_update_case_status = True
    # Uncomment this to automatically close appointments when registering certain case events
    #settings.dvr.case_events_close_appointments = True

    # Uncomment this to have allowance payments update last_seen_on
    #settings.dvr.payments_update_last_seen_on = True

    # Uncomment this to use service types for group/case activites
    #settings.dvr.activity_use_service_type = True
    # Uncomment this to use sectors in group/case activities
    #settings.dvr.activity_sectors = True
    # Uncomment this to use case activity types
    #settings.dvr.activity_types = True
    # Uncomment this to use hierarchical case activity types
    #settings.dvr.activity_types_hierarchical = True
    # Uncomment this to use status field in case activities
    #settings.dvr.case_activity_use_status = True
    # Uncomment this to disable follow-up fields in case activities
    #settings.dvr.case_activity_follow_up = False

    # Uncomment this to include case activity docs on beneficiary documents-tab
    #settings.dvr.case_include_activity_docs = True
    # Uncomment this to include case group docs on beneficiary documents-tab
    #settings.dvr.case_include_group_docs = True

    # Uncomment this if Case activities use multiple Needs
    #settings.dvr.case_activity_needs_multiple = True
    # Uncomment this to use service types for needs
    #settings.dvr_needs_use_service_type = True
    # Uncomment this to use hierarchical need types
    #settings.dvr.needs_hierarchical = True
    # Uncomment this to use hierarchical vulnerability types
    #settings.dvr.vulnerability_types_hierarchical = True

    # Uncomment this to manage individual response actions in case activities
    #settings.dvr.manage_response_actions = True
    # Uncomment this to not use response action types
    #settings.dvr.response_types = False
    # Uncomment this to use response themes
    #settings.dvr.response_themes = True
    # Uncomment this to not use org-specific response themes
    #settings.dvr.response_themes_org_specific = False
    # Uncomment this to link response themes to org sectors
    #settings.dvr.response_themes_sectors = True
    # Uncomment this to link response themes to needs
    #settings.dvr.response_themes_needs = True
    # Uncomment this to automatically link responses to case activities
    #settings.dvr.response_activity_autolink = True
    # Uncomment this to activate features for response planning
    #settings.dvr.response_planning = True
    # Uncomment this to use a separate due-date for responses
    #settings.dvr.response_due_date = True
    # Uncomment this to use date+time for responses (instead of just date)
    #settings.dvr.response_use_time = True

    # Configure a regular expression pattern for ID Codes (QR Codes)
    #settings.dvr.id_code_pattern = "(?P<label>[^,]*),(?P<first_name>[^,]*),(?P<last_name>[^,]*),(?P<date_of_birth>[^,]*)"
    # Uncomment this to show a warning during event registration if the person is not currently checked-in
    #settings.dvr.event_registration_checkin_warning = True
    # Uncomment this to show profile pictures in event registration UI only on demand
    #settings.dvr.event_registration_show_picture = False

    # -------------------------------------------------------------------------
    # Events
    # Uncomment to use the term Disaster instead of Event
    #settings.event.label = "Disaster"
    # Uncomment to not use Incidents under Events
    #settings.event.incident = False
    # Uncomment to preserve linked Incidents when an Event is deleted
    # NB Changing this setting requires a DB migration
    #settings.event.cascade_delete_incidents = False
    # Make Event Types Hierarchical
    #settings.event.types_hierarchical = True
    # Make Incident Types Hierarchical
    #settings.event.incident_types_hierarchical = True
    # Uncomment to allow the use of Exercise Events
    #settings.event.exercise = True
    # Show tab for Event Dispatch
    #settings.event.dispatch_tab = False
    # Hide tab for Event Impacts
    #settings.event.impact_tab = False
    # Hide tab for Event Collection Targets
    #settings.event.target_tab = False
    # Hide tab for Event Collections
    #settings.event.collection_tab = False
    # Hide tab for Incident Dispatch
    #settings.event.incident_dispatch_tab = False
    # Show tab for Incident Impacts
    #settings.event.incident_impact_tab = True
    # Show tab for Incident Teams
    #settings.event.incident_teams_tab = True

    # -------------------------------------------------------------------------
    # Members
    # Hide Membership Types
    #settings.member.membership_types = False
    # Show a CV tab for Members
    #settings.member.cv_tab = True

    # -------------------------------------------------------------------------
    # Persons
    # Uncomment to allow person imports to match even without email addresses
    #settings.pr.import_update_requires_email = False
    # Uncomment this to enable support for third gender
    #settings.pr.hide_third_gender = False
    # Uncomment to a fuzzy search for duplicates in the new AddPersonWidget2
    #settings.pr.lookup_duplicates = True
    # Uncomment to hide fields in S3AddPersonWidget[2]
    #settings.pr.request_dob = False
    #settings.pr.request_email = False
    #settings.pr.request_gender = False
    # Uncomment to show field in S3AddPersonWidget
    #settings.pr.request_home_phone = True
    # Uncomment to modify the order of Names
    #settings.pr.name_format = "%(last_name)s, %(first_name)s %(middle_name)s"
    # Uncomment to prevent selecting existing users in the old S3AddPersonWidget
    #settings.pr.select_existing = False
    # Uncomment to prevent showing HR details in S3PersonAutocompleteWidget results
    #settings.pr.search_shows_hr_details = False
    # Uncomment to hide Emergency Contacts in Person Contacts page
    #settings.pr.show_emergency_contacts = False
    # Uncomment to hide the Address tab in person details
    #settings.pr.use_address = False
    # Show separate Public and Private Contacts Tabs
    #settings.pr.contacts_tabs = ("public", "private")
    # Uncomment this to allow persons to belong to multiple case groups ("households")
    #settings.pr.multiple_case_groups = True

    # -------------------------------------------------------------------------
    # Organisations
    # Uncomment to use an Autocomplete for Organisation lookup fields
    #settings.org.autocomplete = True
    # Enable the Organisation Sector field
    #settings.org.sector = True
    # But hide it from the rheader
    #settings.org.sector_rheader = False
    # Enable the use of Organisation Branches
    #settings.org.branches = True
    # Show branches as tree rather than as table
    #settings.org.branches_tree_view = True
    # Make Facility Types Hierarchical
    #settings.org.facility_types_hierarchical = True
    # Enable the use of Organisation Groups & what their name is
    #settings.org.groups = "Coalition"
    #settings.org.groups = "Network"
    # Organisation Location context
    #settings.org.organisation_location_context = "organisation_location.location_id"
    # Make Organisation Types Hierarchical
    #settings.org.organisation_types_hierarchical = True
    # Make Organisation Types Multiple
    #settings.org.organisation_types_multiple = True
    # Show Organisation Types in the rheader
    #settings.org.organisation_type_rheader = True
    # Enable the use of Organisation Regions
    #settings.org.regions = True
    # Make Organisation Regions Hierarchical
    #settings.org.regions_hierarchical = True
    # Enable the use of Organisation Region Countries
    #settings.org.region_countries = True
    # Uncomment to show a Tab for Organisation Resources
    #settings.org.resources_tab = True
    # Make Services Hierarchical
    #settings.org.services_hierarchical = True
    # Set the length of the auto-generated org/site code the default is 10
    #settings.org.site_code_len = 3
    # Set the label for Sites
    #settings.org.site_label = "Facility"
    # Uncomment to show the date when a Site (Facilities-only for now) was last contacted
    #settings.org.site_last_contacted = True
    # Uncomment to use an Autocomplete for Site lookup fields
    #settings.org.site_autocomplete = True
    # Extra fields to search in Autocompletes & display in Representations
    #settings.org.site_autocomplete_fields = ("instance_type", "location_id$L1", "location_id$addr_street", "organisation_id$name")
    # Uncomment to hide inv & req tabs from Sites
    #settings.org.site_inv_req_tabs = False
    # Uncomment to allow Sites to be staffed by Volunteers
    #settings.org.site_volunteers = True
    # Enable certain fields just for specific Organisations
    # Requires a call to settings.set_org_dependent_field(field)
    # empty list => disabled for all (including Admin)
    #settings.org.dependent_fields = \
    #    {#"<table name>.<field name>"  : ["<Organisation Name>"],
    #     "pr_person_details.mother_name"             : [],
    #     "pr_person_details.father_name"             : [],
    #     "pr_person_details.company"                 : [],
    #     "pr_person_details.affiliations"            : [],
    #     "vol_volunteer.active"                      : [],
    #     "vol_volunteer_cluster.vol_cluster_type_id"      : [],
    #     "vol_volunteer_cluster.vol_cluster_id"          : [],
    #     "vol_volunteer_cluster.vol_cluster_position_id" : [],
    #     }
    # Uncomment to make Office codes unique
    #settings.org.office_code_unique = True
    # Uncomment to make Facility codes unique
    #settings.org.facility_code_unique = True
    # Uncomment to use Tags for Organisations, Offices & Facilities
    #settings.org.tags = True

    # -------------------------------------------------------------------------
    # Human Resource Management
    # Uncomment to change the label for 'Staff'
    #settings.hrm.staff_label = "Contacts"
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    #settings.hrm.email_required = False
    # Uncomment to allow Staff & Volunteers to be registered without an Organisation
    #settings.hrm.org_required = False
    # Uncomment if their are only Staff & Volunteers from a single Organisation with no Branches
    #settings.hrm.multiple_orgs = False
    # Uncomment to disable the 'Send Message' action button
    #settings.hrm.compose_button = False
    # Uncomment to allow HR records to be deletable rather than just marking them as obsolete
    #settings.hrm.deletable = True
    # Uncomment to hide Job Titles
    #settings.hrm.use_job_titles = False
    # Uncomment to allow HRs to have multiple Job Titles
    #settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    #settings.hrm.org_dependent_job_titles = True
    # Uncomment to display & search by National ID
    #settings.hrm.use_national_id = True
    # Uncomment to hide the Staff resource
    #settings.hrm.show_staff = False
    # Uncomment to have Staff use their Home Address as fallback if they have no Site defined
    #settings.hrm.location_staff = ("site_id", "person_id")
    # Uncomment to have Volunteers use their Site Address as fallback if they have no Home Address defined
    #settings.hrm.location_vol = ("person_id", "site_id")
    # Uncomment this to allow multiple site contacts per site (e.g. if needing a separate contact per sector)
    #settings.hrm.site_contact_unique = False
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    #settings.hrm.skill_types = True
    # Uncomment to disable Staff experience
    #settings.hrm.staff_experience = False
    # Uncomment to enable Volunteer 'active' field
    # - can also be made a function which is called to calculate the status based on recorded hours
    # Custom label for Organisations in HR module
    #settings.hrm.organisation_label = "Organization / Branch"
    # Custom label for Top-level Organisations in HR module
    #settings.hrm.root_organisation_label = "Organization"
    #settings.hrm.vol_active = True
    # Uncomment to define a Tooltip to show when viewing the Volunteer 'active' field
    #settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"
    # Uncomment to disable Volunteer experience
    #settings.hrm.vol_experience = False
    # Uncomment to show the Organisation name in HR represents
    #settings.hrm.show_organisation = True
    # Uncomment to consolidate tabs into a single CV
    #settings.hrm.cv_tab = True
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    #settings.hrm.record_tab = "record"
    # Uncomment to disable the use of Volunteer Awards
    #settings.hrm.use_awards = False
    # Uncomment to disable the use of HR Certificates
    #settings.hrm.use_certificates = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    #settings.hrm.filter_certificates = True
    # Uncomment to auto-create certificates for courses
    #settings.hrm.create_certificates_from_courses = True
    # Uncomment to enable the use of Staff/Volunteer IDs
    #settings.hrm.use_code = True
    # Uncomment to disable the use of HR Credentials
    #settings.hrm.use_credentials = False
    # Uncomment to disable the use of HR Description
    #settings.hrm.use_description = None
    # Uncomment to enable the use of HR Education
    #settings.hrm.use_education = True
    # Uncomment to disable the use of HR ID Tab
    #settings.hrm.use_id = False
    # Uncomment to disable the use of HR Address Tab
    #settings.hrm.use_address = False
    # Uncomment to disable the use of HR Skills
    #settings.hrm.use_skills = False
    # Uncomment to enable tracking of staff salaries
    #settings.hrm.salary = True
    # Uncomment to disable the use of HR Teams
    #settings.hrm.teams = False
    # Uncomment to disable the use of HR Trainings
    #settings.hrm.use_trainings = False
    # Uncomment this to configure tracking of internal/external training instructors
    #settings.hrm.training_instructors = "external"
    # Uncomment this to modify the training filter to be AND not OR
    #settings.hrm.training_filter_and = True
    # Uncomment this to have Pass marks defined by Course
    #settings.hrm.course_pass_marks = True
    # Uncomment to use activity types in experience record, specify as {"code":"label", ...}
    #settings.hrm.activity_types = {"rdrt": "RDRT Mission"}

    # -------------------------------------------------------------------------
    # Inventory Management
    #settings.inv.collapse_tabs = False
    # Uncomment to customise the label for Facilities in Inventory Management
    #settings.inv.facility_label = "Facility"
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    #settings.inv.direct_stock_edits = True
    # Uncomment to have Warehouse Types be Organisation-dependent
    #settings.inv.org_dependent_warehouse_types = True
    # Uncomment to call Stock Adjustments, 'Stock Counts'
    #settings.inv.stock_count = True
    # Use the term 'Order' instead of 'Shipment'
    #settings.inv.shipment_name = "order"
    # Uncomment to validate for Unique Warehouse Codes
    #settings.inv.warehouse_code_unique = True
    # Uncomment to not track pack values
    #settings.inv.track_pack_values = False
    #settings.inv.show_mode_of_transport = True
    #settings.inv.send_show_org = False
    #settings.inv.send_show_time_in = True
    #settings.inv.send_form_name = "Tally Out Sheet"
    #settings.inv.send_short_name = "TO"
    #settings.inv.send_ref_field_name = "Tally Out Number"
    #settings.inv.recv_form_name = "Acknowledgement Receipt for Donations Received Form"
    #settings.inv.recv_shortname = "ARDR"
    # Types common to both Send and Receive
    #settings.inv.shipment_types = {
    #         0: T("-"),
    #         1: T("Other Warehouse"),
    #         2: T("Donation"),
    #         3: T("Foreign Donation"),
    #         4: T("Local Purchases"),
    #         5: T("Confiscated Goods from Bureau Of Customs")
    #    }
    #settings.inv.send_types = {
    #        21: T("Distribution")
    #    }
    #settings.inv.send_type_default = 1
    #settings.inv.recv_types = {
    #        32: T("Donation"),
    #        34: T("Purchase"),
    #    }
    #settings.inv.item_status = {
    #        0: "-",
    #        1: T("Dump"),
    #        2: T("Sale"),
    #        3: T("Reject"),
    #        4: T("Surplus")
    #   }

    # -------------------------------------------------------------------------
    # Requests Management
    # Uncomment to disable Inline Forms in Requests module
    #settings.req.inline_forms = False
    # Label for Inventory Requests
    #settings.req.type_inv_label = "Donations"
    # Label for People Requests
    #settings.req.type_hrm_label = "Volunteers"
    # Label for Requester
    #settings.req.requester_label = "Site Contact"
    # Uncomment to disable Recurring Request
    #settings.req.recurring = False
    #settings.req.requester_optional = True
    # Uncomment if the User Account logging the Request is NOT normally the Requester
    #settings.req.requester_is_author = False
    # Filter Requester as being from the Site
    #settings.req.requester_from_site = True
    # Set the Requester as being an HR for the Site if no HR record yet & as Site contact if none yet exists
    #settings.req.requester_to_site = True
    #settings.req.date_writable = False
    # Allow the status for requests to be set manually,
    # rather than just automatically from commitments and shipments
    #settings.req.status_writable = False
    #settings.req.item_quantities_writable = True
    #settings.req.skill_quantities_writable = True
    #settings.req.show_quantity_transit = False
    #settings.req.multiple_req_items = False
    #settings.req.prompt_match = False
    #settings.req.items_ask_purpose = False
    # Uncomment to disable the Commit step in the workflow & simply move direct to Ship
    #settings.req.use_commit = False
    # Uncomment to have Donations include a 'Value' field
    #settings.req.commit_value = True
    # Uncomment to allow Donations to be made without a matching Request
    #settings.req.commit_without_request = True
    # Uncomment to Commit Named People rather than simply Anonymous Skills
    #settings.req.commit_people = True
    # Uncomment if the User Account logging the Commitment is NOT normally the Committer
    #settings.req.comittter_is_author = False
    # Should Requests ask whether Security is required?
    #settings.req.ask_security = True
    # Should Requests ask whether Transportation is required?
    #settings.req.ask_transport = True
    #settings.req.use_req_number = False
    #settings.req.generate_req_number = False
    #settings.req.req_form_name = "Request Issue Form"
    #settings.req.req_shortname = "RIS"
    # Restrict the type of requests that can be made, valid values in the
    # list are ("Stock", "People", "Other"). If this is commented out then
    # all types will be valid.
    #settings.req.req_type = ("Stock",)
    # Uncomment to enable Summary 'Site Needs' tab for Offices/Facilities
    #settings.req.summary = True
    # Uncomment to restrict adding new commits to Completed commits
    #settings.req.req_restrict_on_complete = True

    # Custom Crud Strings for specific req_req types
    #settings.req.req_crud_strings = dict()
    #ADD_ITEM_REQUEST = T("Make a Request for Donations")
    # req_req Crud Strings for Item Request (type=1)
    #settings.req.req_crud_strings[1] = Storage(
    #    label_create = ADD_ITEM_REQUEST,
    #    title_display = T("Request for Donations Details"),
    #    title_list = T("Requests for Donations"),
    #    title_update = T("Edit Request for Donations"),
    #    label_list_button = T("List Requests for Donations"),
    #    label_delete_button = T("Delete Request for Donations"),
    #    msg_record_created = T("Request for Donations Added"),
    #    msg_record_modified = T("Request for Donations Updated"),
    #    msg_record_deleted = T("Request for Donations Canceled"),
    #    msg_list_empty = T("No Requests for Donations"))
    #ADD_PEOPLE_REQUEST = T("Make a Request for Volunteers")
    # req_req Crud Strings for People Request (type=3)
    #settings.req.req_crud_strings[3] = Storage(
    #    label_create = ADD_PEOPLE_REQUEST,
    #    title_display = T("Request for Volunteers Details"),
    #    title_list = T("Requests for Volunteers"),
    #    title_update = T("Edit Request for Volunteers"),
    #    label_list_button = T("List Requests for Volunteers"),
    #    label_delete_button = T("Delete Request for Volunteers"),
    #    msg_record_created = T("Request for Volunteers Added"),
    #    msg_record_modified = T("Request for Volunteers Updated"),
    #    msg_record_deleted = T("Request for Volunteers Canceled"),
    #    msg_list_empty = T("No Requests for Volunteers"))

    # -------------------------------------------------------------------------
    # Supply
    # Name of the Default Item Catalog. Do not edit after deployment
    #settings.supply.catalog_default = "Default"
    # Disable the use of Multiple Item Catalogs
    #settings.supply.catalog_multi = False
    # Disable the use of Alternative Items
    #settings.supply.use_alt_name = False

    # -------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    #settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    #settings.project.mode_drr = True
    # Uncomment this to use settings suitable for detailed Task management
    #settings.project.mode_task = True
    # Uncomment this to use link Projects to Events
    #settings.project.event_projects = True
    # Uncomment this to use Activities for Projects & Tasks
    #settings.project.activities = True
    # Uncomment this to use link Activities to Events
    #settings.project.event_activities = True
    # Uncomment this to use Activity Types for Activities & Projects
    #settings.project.activity_types = True
    # Uncomment this to filter dates in Activities
    #settings.project.activity_filter_year = True
    # Uncomment this to not use Beneficiaries for Activities
    #settings.project.get_project_activity_beneficiaries = False
    # Uncomment this to not use Item Catalog for Distributions
    #settings.project.activity_items = False
    # Uncomment this to use Codes for projects
    #settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Demographics in 3W projects
    #settings.project.demographics = True
    # Uncomment this to enable Hazards in 3W projects
    #settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    #settings.project.indicators = True
    # Uncomment this to enable Milestones in projects
    #settings.project.milestones = True
    # Uncomment this to use Projects for Activities & Tasks
    #settings.project.projects = True
    # Uncomment this to disable Sectors in projects
    #settings.project.sectors = False
    # Uncomment this to enable Programmes in projects
    #settings.project.programmes = True
    # Uncomment this to enable Budgets in Programmes
    #settings.project.programme_budget = True
    # Uncomment this to enable Themes in 3W projects
    #settings.project.themes = True
    # Uncomment this to use Theme Percentages for projects
    #settings.project.theme_percentages = True
    # Uncomment this to use multiple Budgets per project
    #settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    #settings.project.multiple_organisations = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    #settings.project.organisation_roles = {
    #    1: T("Lead Implementer"), # T("Host National Society")
    #    2: T("Partner"), # T("Partner National Society")
    #    3: T("Donor"),
    #    4: T("Customer"), # T("Beneficiary")?
    #    5: T("Super"), # T("Beneficiary")?
    #}
    #settings.project.organisation_lead_role = 1
    # Uncomment to customise the list of options for the Priority of a Task.
    # NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
    #settings.project.task_priority_opts =
    # Uncomment to customise the list of options for the Status of a Task.
    # NB Be very cautious about doing this (see docstring in modules/s3cfg.py)
    #settings.project.task_status_opts =

    # -------------------------------------------------------------------------
    # Incidents
    # Uncomment this to use vehicles when responding to Incident Reports
    #settings.irs.vehicle = True

    # -------------------------------------------------------------------------
    # Transport
    # Uncomment to make Airport codes unique
    #settings.transport.airport_code_unique = True
    # Uncomment to make Seaport codes unique
    #settings.transport.seaport_code_unique = True
    # Uncomment to make Heliport codes unique
    #settings.transport.heliport_code_unique = True

    # -------------------------------------------------------------------------
    # Filter Manager
    #settings.search.filter_manager = False

    # if you want to have videos appearing in /default/video
    #settings.base.youtube_id = [dict(id = "introduction",
    #                                 title = T("Introduction"),
    #                                 video_id = "HR-FtR2XkBU"),]

    # -----------------------------------------------------------------------------
    # Mobile Forms
    # Configure mobile forms (example), see modules/s3cfg.py for details
    #settings.mobile.forms = [
    #    ("Beneficiaries", "pr_person", {"c": "dvr", "f": "person"}),
    #]
    # Disable mobile forms for dynamic tables:
    #settings.mobile.dynamic_tables = False

    # -----------------------------------------------------------------------------
    # XForms
    # Configure xform resources (example)
    #settings.xforms.resources = [("Request", "req_req")]

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # @ToDo: Have the system automatically enable migrate if a module is enabled
    # Modules menu is defined in modules/eden/menu.py
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
        ("setup", Storage(
            name_nice = T("Setup"),
            #description = "WebSetup",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
             module_type = None  # No Menu
        )),
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("cms", Storage(
            name_nice = T("Content Management"),
            #description = "Content Management System",
            restricted = True,
            module_type = 10,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("supply", Storage(
            name_nice = T("Supply Chain Management"),
            #description = "Used within Inventory Management, Request Management and Asset Management",
            restricted = True,
            module_type = None, # Not displayed
        )),
        ("inv", Storage(
            name_nice = T("Warehouses"),
            #description = "Receiving and Sending Items",
            restricted = True,
            module_type = 4
        )),
        #("proc", Storage(
        #        name_nice = T("Procurement"),
        #        #description = "Ordering & Purchasing of Goods & Services",
        #        restricted = True,
        #        module_type = 10
        #    )),
        ("asset", Storage(
            name_nice = T("Assets"),
            #description = "Recording and Assigning Assets",
            restricted = True,
            module_type = 5,
        )),
        # Vehicle depends on Assets
        ("vehicle", Storage(
            name_nice = T("Vehicles"),
            #description = "Manage Vehicles",
            restricted = True,
            module_type = 10,
        )),
        ("req", Storage(
            name_nice = T("Requests"),
            #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
            restricted = True,
            module_type = 10,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 2
        )),
        #("survey", Storage(
        #    name_nice = T("Surveys"),
        #    #description = "Create, enter, and manage surveys.",
        #    restricted = True,
        #    module_type = 5,
        #)),
        #("dc", Storage(
        #   name_nice = T("Assessments"),
        #   #description = "Data collection tool",
        #   restricted = True,
        #   module_type = 5
        #)),
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("disease", Storage(
        #    name_nice = T("Disease Tracking"),
        #    #description = "Helps to track cases and trace contacts in disease outbreaks",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("br", Storage(
        #    name_nice = T("Beneficiary Registry"),
        #    #description = "Beneficiary Registry and Case Management",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("br", Storage(
        #    name_nice = T("Benficiary Registry"),
        #    #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("transport", Storage(
        #    name_nice = T("Transport"),
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
        #("member", Storage(
        #    name_nice = T("Members"),
        #    #description = "Membership Management System",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("budget", Storage(
        #    name_nice = T("Budgeting Module"),
        #    #description = "Allows a Budget to be drawn up",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("deploy", Storage(
        #    name_nice = T("Deployments"),
        #    #description = "Manage Deployments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Deprecated: Replaced by event
        #("irs", Storage(
        #    name_nice = T("Incidents"),
        #    #description = "Incident Reporting System",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("dvi", Storage(
        #   name_nice = T("Disaster Victim Identification"),
        #   #description = "Disaster Victim Identification",
        #   restricted = True,
        #   module_type = 10,
        #   #access = "|DVI|",      # Only users with the DVI role can see this module in the default menu & access the controller
        #)),
        #("edu", Storage(
        #    name_nice = T("Schools"),
        #    #description = "Helps to monitor status of schools",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("mpr", Storage(
        #   name_nice = T("Missing Person Registry"),
        #   #description = "Helps to report and search for missing persons",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("vulnerability", Storage(
        #    name_nice = T("Vulnerability"),
        #    #description = "Manages vulnerability indicators",
        #    restricted = True,
        #    module_type = 10,
        # )),
        #("fire", Storage(
        #   name_nice = T("Fire Stations"),
        #   #description = "Fire Station Management",
        #   restricted = True,
        #   module_type = 1,
        #)),
        #("water", Storage(
        #    name_nice = T("Water"),
        #    #description = "Flood Gauges show water levels in various parts of the country",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("patient", Storage(
        #    name_nice = T("Patient Tracking"),
        #    #description = "Tracking of Patients",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("po", Storage(
        #    name_nice = T("Population Outreach"),
        #    #description = "Population Outreach",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("security", Storage(
        #   name_nice = T("Security"),
        #   #description = "Security Management System",
        #   restricted = True,
        #   module_type = 10,
        #)),
        # These are specialist modules
        #("cap", Storage(
        #    name_nice = T("CAP"),
        #    #description = "Create & broadcast CAP alerts",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Requires RPy2 & PostgreSQL
        #("climate", Storage(
        #    name_nice = T("Climate"),
        #    #description = "Climate data portal",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("delphi", Storage(
        #    name_nice = T("Delphi Decision Maker"),
        #    #description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
        #    restricted = False,
        #    module_type = 10,
        #)),
        # @ToDo: Port these Assessments to the Survey module
        #("building", Storage(
        #    name_nice = T("Building Assessments"),
        #    #description = "Building Safety Assessments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        # Deprecated by Surveys module
        # - depends on CR, IRS & Impact
        #("assess", Storage(
        #    name_nice = T("Assessments"),
        #    #description = "Rapid Assessments & Flexible Impact Assessments",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("impact", Storage(
        #    name_nice = T("Impacts"),
        #    #description = "Used by Assess",
        #    restricted = True,
        #    module_type = None,
        #)),
        #("ocr", Storage(
        #   name_nice = T("Optical Character Recognition"),
        #   #description = "Optical Character Recognition for reading the scanned handwritten paper forms.",
        #   restricted = False,
        #   module_type = None,
        #)),
        #("work", Storage(
        #   name_nice = T("Jobs"),
        #   #description = "Simple Volunteer Jobs Management",
        #   restricted = False,
        #   module_type = None,
        #)),
    ])

# END =========================================================================
