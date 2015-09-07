# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Settings for the SITAP deployhment in Turkey:
        http://sahana.org.tr
    """

    T = current.T

    #settings.base.system_name = T("Sahana Skeleton")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate = ("Turkey", "default/users", "Turkey/Demo")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "Turkey"

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    #settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("TR",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "العربية"),
        ("en", "English"),
        ("tr", "Türkçe"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "tr"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0200"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = ","
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = "."
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : T("Euros"),
        #"GBP" : T("Great British Pounds"),
        "TRY" : T("Turkish Lira"),
        "USD" : T("United States Dollars"),
    }
    settings.fin.currency_default = "TRY"

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
    settings.security.policy = 8 # Entity Realm + Hierarchy and Delegations

    # Uncomment to have Volunteers be hierarchical organisational units
    # (& hence HR realms propagate down to Address & Contacts)
    # NB Doesn't seem to make any difference
    #settings.hrm.vol_affiliation = 1

    # Uncomment to have Person records owned by the Org they are an HR for
    settings.auth.person_realm_human_resource_site_then_org = True

    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    settings.hrm.skill_types = True

    # -------------------------------------------------------------------------
    def pr_component_realm_entity(table, row):
        """
            Assign a Realm Entity to Person Address/Contact records
        """

        db = current.db
        s3db = current.s3db

        # Find the Person
        ptable = s3db.pr_person
        person = db(ptable.pe_id == row.pe_id).select(ptable.id,
                                                      limitby=(0, 1)
                                                      ).first()
        try:
            person_id = person.id
        except:
            # => Set to default of Person's
            return row.pe_id

        # Find the Organisation which this Person links to
        htable = s3db.hrm_human_resource
        query = (htable.person_id == person_id) & \
                (htable.deleted == False)
        hrs = db(query).select(htable.organisation_id)
        if len(hrs) != 1:
            # Either no HR record or multiple options
            # => Set to default of Person's
            return row.pe_id
        organisation_id = hrs.first().organisation_id

        # Find the Org's realm_entity
        otable = s3db.org_organisation
        org = db(otable.id == organisation_id).select(otable.realm_entity,
                                                      limitby=(0, 1)
                                                      ).first()
        try:
            # Set to the same realm_entity
            return org.realm_entity
        except:
            # => Set to default of Person's
            return row.pe_id

    # -------------------------------------------------------------------------
    def customise_pr_address_resource(r, tablename):

        current.s3db.configure("pr_address",
                               realm_entity = pr_component_realm_entity,
                               )

    settings.customise_pr_address_resource = customise_pr_address_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        current.s3db.configure("pr_contact",
                               realm_entity = pr_component_realm_entity,
                               )

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db
        table = s3db.pr_person_details
        table.place_of_birth.writable = True
        table.mother_name.readable = True
        table.father_name.readable = True
        #import s3db.tr
        s3db.add_components("pr_person",
                            tr_identity = "person_id",
                            )
        settings.org.dependent_fields = \
            {"pr_person_details.mother_name" : None, # Show for all
             "pr_person_details.father_name" : None, # Show for all
             }
        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm("first_name",
                                    "last_name",
                                    "date_of_birth",
                                    #"initials",
                                    #"preferred_name",
                                    #"local_name",
                                    "gender",
                                    "person_details.occupation",
                                    "person_details.marital_status",
                                    "person_details.number_children",
                                    #"person_details.nationality",
                                    #"person_details.religion",
                                    "person_details.mother_name",
                                    "person_details.father_name",
                                    #"person_details.company",
                                    #"person_details.affiliations",
                                    "person_details.criminal_record",
                                    "person_details.military_service",
                                    "comments",
                                    )

        s3db.configure("pr_person",
                       crud_form = crud_form,
                       )
        s3db.configure("pr_address",
                       realm_entity = pr_component_realm_entity,
                       )
        s3db.configure("pr_contact",
                       realm_entity = pr_component_realm_entity,
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def vol_rheader(r):
        if r.representation != "html":
            # RHeaders only used in interactive views
            return None
        record = r.record
        if record is None:
            # List or Create form: rheader makes no sense here
            return None
<<<<<<< HEAD

        #from gluon.html import DIV
        person_id = r.id
        s3db = current.s3db
        table = s3db.hrm_human_resource
        hr = current.db(table.person_id == person_id).select(table.organisation_id,
                                                             limitby=(0, 1)).first()
        if hr:
            if current.auth.user.organisation_id != hr.organisation_id:
                # Only show Org if not the same as user's
                rheader = table.organisation_id.represent(hr.organisation_id)
=======
    
        T = current.T
        table = r.table
        resourcename = r.name
    
        if resourcename == "person":
            settings = current.deployment_settings
            get_vars = r.get_vars
            hr = get_vars.get("human_resource.id", None)
            if hr:
                name = current.s3db.hrm_human_resource_represent(int(hr))
            else:
                name = s3_fullname(record)
            group = get_vars.get("group", None)
            if group is None:
                controller = r.controller
                if controller == "vol":
                    group = "volunteer"
                else:
                    group = "staff"
            use_cv = settings.get_hrm_cv_tab()
            record_tab = settings.get_hrm_record_tab()
            experience_tab = None
            service_record = ""
            tbl = TABLE(TR(TH(name,
                              # @ToDo: Move to CSS
                              _style="padding-top:15px")
                           ))
            experience_tab2 = None
            if settings.get_hrm_staff_experience() == "experience" and not use_cv:
                experience_tab = (T("Experience"), "experience")
    
            if settings.get_hrm_use_certificates():
                certificates_tab = (T("Certificates"), "certification")
            else:
                certificates_tab = None
    
            if settings.get_hrm_use_credentials():
                credentials_tab = (T("Credentials"), "credential")
            else:
                credentials_tab = None
    
            if settings.get_hrm_use_description():
                description_tab = (T("Description"), "physical_description")
            else:
                description_tab = None
    
            if settings.get_hrm_use_education() and not use_cv:
                education_tab = (T("Education"), "education")
            else:
                education_tab = None
    
            if settings.get_hrm_use_id():
                id_tab = (T("ID"), "identity")
            else:
                id_tab = None
    
            if settings.get_hrm_use_address():
                address_tab = (T("Address"), "address")
            else:
                address_tab = None
    
            if settings.get_hrm_salary():
                salary_tab = (T("Salary"), "salary")
            else:
                salary_tab = None
    
            if settings.get_hrm_use_skills() and not use_cv:
                skills_tab = (T("Skills"), "competency")
            else:
                skills_tab = None
    
            if record_tab != "record":
                teams = settings.get_hrm_teams()
                if teams:
                    teams_tab = (T(teams), "group_membership")
                else:
                    teams_tab = None
            else:
                teams_tab = None
    
            trainings_tab = instructor_tab = None
            if settings.get_hrm_use_trainings():
                if not use_cv:
                    trainings_tab = (T("Trainings"), "training")
                if settings.get_hrm_training_instructors() in ("internal", "both"):
                    instructor_tab = (T("Instructor"), "training_event")
    
            if use_cv:
                trainings_tab = (T("CV"), "cv")
    
            hr_tab = None
            if not record_tab:
                record_method = None
            elif record_tab == "record":
                record_method = "record"
            else:
                # Default
                record_method = "human_resource"
            if profile:
                # Configure for personal mode
                if record_method:
                    hr_tab = (T("Staff/Volunteer Record"), record_method)
                tabs = [(T("Person Details"), None),
                        (T("User Account"), "user"),
                        hr_tab,
                        id_tab,
                        description_tab,
                        address_tab,
                        ]
                contacts_tabs = settings.get_pr_contacts_tabs()
                if "all" in contacts_tabs:
                    tabs.append((T("Contacts"), "contacts"))
                if "public" in contacts_tabs:
                    tabs.append((T("Public Contacts"), "public_contacts"))
                if "private" in contacts_tabs:
                    tabs.append((T("Private Contacts"), "private_contacts"))
                tabs += [education_tab,
                         trainings_tab,
                         certificates_tab,
                         skills_tab,
                         credentials_tab,
                         experience_tab,
                         experience_tab2,
                         instructor_tab,
                         teams_tab,
                         #(T("Assets"), "asset"),
                         ]
            elif current.session.s3.hrm is not None and current.session.s3.hrm.mode is not None:
                # Configure for personal mode
                tabs = [(T("Person Details"), None),
                        id_tab,
                        description_tab,
                        address_tab,
                        ]
                contacts_tabs = settings.get_pr_contacts_tabs()
                if "all" in contacts_tabs:
                    tabs.append((T("Contacts"), "contacts"))
                if "public" in contacts_tabs:
                    tabs.append((T("Public Contacts"), "public_contacts"))
                if "private" in contacts_tabs:
                    tabs.append((T("Private Contacts"), "private_contacts"))
                if record_method is not None:
                    hr_tab = (T("Positions"), "human_resource")
                tabs += [trainings_tab,
                         certificates_tab,
                         skills_tab,
                         credentials_tab,
                         experience_tab,
                         experience_tab2,
                         hr_tab,
                         teams_tab,
                         (T("Assets"), "asset"),
                         ]
            else:
                # Configure for HR manager mode
                if group == "staff":
                    hr_record = T("Staff Record")
                    awards_tab = None
                elif group == "volunteer":
                    hr_record = T("Volunteer Record")
                    if settings.get_hrm_use_awards() and not use_cv:
                        awards_tab = (T("Awards"), "award")
                    else:
                        awards_tab = None
                if record_method:
                    hr_tab = (hr_record, record_method)
                tabs = [(T("Person Details"), None),
                        hr_tab,
                        id_tab,
                        description_tab,
                        address_tab,
                        ]
                contacts_tabs = settings.get_pr_contacts_tabs()
                if "all" in contacts_tabs:
                    tabs.append((T("Contacts"), "contacts"))
                if "public" in contacts_tabs:
                    tabs.append((T("Public Contacts"), "public_contacts"))
                if "private" in contacts_tabs:
                    tabs.append((T("Private Contacts"), "private_contacts"))
                tabs += [salary_tab,
                         education_tab,
                         trainings_tab,
                         certificates_tab,
                         skills_tab,
                         credentials_tab,
                         experience_tab,
                         experience_tab2,
                         instructor_tab,
                         awards_tab,
                         teams_tab,
                         (T("Assets"), "asset"),
                         ]
                # Add role manager tab if a user record exists
                user_id = current.auth.s3_get_user_id(record.id)
                if user_id:
                    tabs.append((T("Roles"), "roles"))
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV(service_record,
                          A(s3_avatar_represent(record.id,
                                                "pr_person",
                                                _class="rheader-avatar"),
                            _href=URL(f="person", args=[record.id, "image"],
                                      vars = get_vars),
                            ),
                          tbl,
                          rheader_tabs)
    
        elif resourcename == "training_event":
            # Tabs
            tabs = [(T("Training Event Details"), None),
                    (T("Participants"), "participant"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)
            if current.deployment_settings.has_module("msg") and \
                   current.auth.permission.has_permission("update", c="hrm", f="compose"):
                # @ToDo: Be able to see who has been messaged, whether messages bounced, receive confirmation responses, etc
                action = A(T("Message Participants"),
                           _href = URL(f = "compose",
                                       vars = {"training_event.id": record.id,
                                               "pe_id": record.pe_id,
                                               },
                                       ),
                           _class = "action-btn send"
                           )
>>>>>>> aad931e... Add organisation_id to dvr_case
            else:
                rheader = None
        else:
            # Something went wrong!
            rheader = None
        return rheader

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):
        # Custom RHeader
        attr["rheader"] = vol_rheader
        return attr

<<<<<<< HEAD
    #settings.customise_pr_person_controller = customise_pr_person_controller
=======
    settings.customise_pr_person_controller = customise_pr_person_controller
    
    # -------------------------------------------------------------------------    
    def dvr_case_onvalidation(form):

        try:
            form_vars = form.vars
            case_number = form_vars.get("reference") 
            org_id = form_vars.get("organisation_id")
            
            table = current.s3db.dvr_case
            query = (table.reference == case_number) & \
                    (table.organisation_id == org_id)
            record = current.db(query).select(limitby=(0, 1)).first()  
            if record:
                form.errors["reference"] = "Bu dosya numarası kullanılmıştır!"
        except AttributeError:
            return

        #if case_number :
        #    form.errors["reference"] = current.T("Test problem")
        return
        
    # -------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):
        """ Configure dvr_case_resource """  
        s3db = current.s3db        
        s3db.configure("dvr_case",
                  onvalidation = dvr_case_onvalidation,
                  )
    
    settings.customise_dvr_case_resource = customise_dvr_case_resource  
>>>>>>> aad931e... Add organisation_id to dvr_case

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
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
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
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
        #("cms", Storage(
        #    name_nice = T("Content Management"),
        #    #description = "Content Management System",
        #    restricted = True,
        #    module_type = 10,
        #)),
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
        ("cr", Storage(
            name_nice = T("Camps"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        ("hms", Storage(
            name_nice = T("Hospitals"),
            #description = "Helps to monitor status of hospitals",
            restricted = True,
            module_type = 10
        )),
        #("dvr", Storage(
        #   name_nice = T("Disaster Victim Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
        ("tr", Storage(
           name_nice = "Turkish Extensions",
           restricted = True,
           module_type = None,
        )),
        ("transport", Storage(
           name_nice = T("Transport"),
           restricted = True,
           module_type = 10,
        )),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================