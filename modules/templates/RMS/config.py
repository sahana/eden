# -*- coding: utf-8 -*-

import datetime
import json
from collections import OrderedDict

from gluon import current, IS_IN_SET, URL
from gluon.storage import Storage

from s3 import S3Method, S3Represent, SEPARATORS#, NONE

from .controllers import deploy_index, inv_Dashboard

# Organisation Type
RED_CROSS = "Red Cross / Red Crescent"

# Names of Orgs with specific settings
HNRC = "Honduran Red Cross"
PARC = "Red Cross Society of Panama"
#PYRC = "Paraguayan Red Cross"

def config(settings):
    """
        Template settings for IFRC's Resource Management System

        http://eden.sahanafoundation.org/wiki/Deployments/IFRC

        This version was developed for the Americas Zone
        Hence Apellido Paterno (pr_person.middle_name) matches to auth_user.last_name
    """

    T = current.T

    # -------------------------------------------------------------------------
    # System Name
    #
    settings.base.system_name = T("Resource Management System")
    settings.base.system_name_short = T("RMS")

    # -------------------------------------------------------------------------
    # Custom Models
    #
    settings.base.custom_models = {"deploy": "RMS",
                                   }

    # -------------------------------------------------------------------------
    # Pre-Populate
    #
    settings.base.prepopulate.append("RMS")
    settings.base.prepopulate_demo.append("RMS/Demo")

    # -------------------------------------------------------------------------
    # Theme (folder to use for views/layout.html)
    #
    settings.base.theme = "RMS"

    # Uncomment to show a default cancel button in standalone create/update forms
    settings.ui.default_cancel_button = True
    settings.ui.update_label = "Modify"
    # Limit Export Formats
    settings.ui.export_formats = ("xls",
                                  "pdf",
                                  )

    def datatables_responsive(default):
        """ Responsive behavior of datatables (lazy setting) """

        table = current.s3db.s3dt_user_options
        options = current.db(table.user_id == current.auth.user.id).select(table.unresponsive_tables,
                                                                           limitby = (0, 1),
                                                                           ).first()
        if options:
            return not options.unresponsive_tables
        else:
            return default
    settings.ui.datatables_responsive = datatables_responsive

    # @todo: configure custom icons
    #settings.ui.custom_icons = {
    #    "male": "icon-male",
    #    "female": "icon-female",
    #    "medical": "icon-plus-sign-alt",
    #}

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Security Policy
    settings.security.policy = 7
    settings.security.map = True

    # Authorization Settings
    settings.auth.registration_requires_approval = True
    settings.auth.registration_requires_verification = True
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_organisation_required = True
    settings.auth.registration_requests_site = True

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               #"member": T("Member")
                                               }
    # This hides the options from the UI
    #settings.auth.registration_link_user_to_default = ["volunteer"]

    #settings.auth.record_approval = True

    # @ToDo: Should we fallback to organisation_id if site_id is None?
    settings.auth.registration_roles = {"site_id": ["reader",
                                                    ],
                                        }

    # Owner Entity
    settings.auth.person_realm_human_resource_site_then_org = True
    settings.auth.person_realm_member_org = True

    # Activate entity role manager tabs for OrgAdmins
    settings.auth.entity_role_manager = True

    # Use HRM for the /default/person Profile
    settings.auth.profile_controller = "hrm"

    # -------------------------------------------------------------------------
    def ifrc_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        tablename = table._tablename

        # Do not apply realms for Master Data
        # @ToDo: Restore Realms and add a role/functionality support for Master Data
        if tablename in ("hrm_certificate",
                         "hrm_department",
                         "hrm_job_title",
                         "hrm_course",
                         "hrm_programme",
                         "inv_package",
                         "member_membership_type",
                         "vol_award",
                         ):
            return None

        db = current.db
        s3db = current.s3db

        realm_entity = 0
        use_user_organisation = False
        use_user_root_organisation = False

        if tablename in ("inv_req",
                         "inv_req_item",
                         "inv_track_item",
                         #"inv_send", # Only need to have site_id, to_site_id will manage via Recv, if-necessary
                         #"inv_recv", # Only need to have site_id, from_site_id will manage via Send, if-necessary
                         ):
            if tablename == "inv_req":
                req_id = row["id"]
                req_site_id = row["site_id"]
                ritable = s3db.inv_req_item
                req_items = db(ritable.req_id == req_id).select(ritable.site_id)
                site_ids = set([ri.site_id for ri in req_items if ri.site_id != None] + [req_site_id])
                if len(site_ids) == 1:
                    # Can just use the Site's realm
                    from s3db.pr import pr_get_pe_id
                    return pr_get_pe_id("org_site", req_site_id)
                elif len(site_ids) == 2:
                    # Need a pr_realm with dual inheritance
                    # - this can be shared with all other records shared between these 2 sites
                    for site_id in site_ids:
                        if site_id != req_site_id:
                            ri_site_id = site_id
                            break
                    if req_site_id < ri_site_id:
                        realm_name = "2SITES_%s_%s" % (req_site_id, ri_site_id)
                    else:
                        realm_name = "2SITES_%s_%s" % (ri_site_id, req_site_id)
                else:
                    # Need a unique pr_realm with multiple inheritance
                    realm_name = "REQ_%s" % req_id

            elif tablename == "inv_req_item":
                req_id = row.get("req_id")
                if not req_id:
                    ritable = s3db.inv_req_item
                    req_item = db(ritable.id == row["id"]).select(ritable.req_id,
                                                                  limitby = (0, 1),
                                                                  ).first()
                    req_id = req_item.req_id
                rtable = s3db.inv_req
                req = db(rtable.id == req_id).select(rtable.site_id,
                                                     limitby = (0, 1),
                                                     ).first()
                req_site_id = req.site_id
                ri_site_id = row["site_id"]
                if not ri_site_id or (ri_site_id == req_site_id):
                    # Use the realm of the Req's site
                    from s3db.pr import pr_get_pe_id
                    return pr_get_pe_id("org_site", req_site_id)

                # Need a pr_realm with dual inheritance
                # - this can be shared with all other records shared between these 2 sites
                site_ids = (req_site_id, ri_site_id)
                if req_site_id < ri_site_id:
                    realm_name = "2SITES_%s_%s" % (req_site_id, ri_site_id)
                else:
                    realm_name = "2SITES_%s_%s" % (ri_site_id, req_site_id)

            elif tablename == "inv_track_item":
                # Inherit from inv_send &/or inv_recv
                record = db(table.id == row["id"]).select(table.send_id,
                                                          table.recv_id,
                                                          limitby = (0, 1),
                                                          ).first()
                send_id = record.send_id
                recv_id = record.recv_id
                if send_id and recv_id:
                    # Need a pr_realm with dual inheritance
                    # - this can be shared with all other records shared between these 2 sites
                    realm_name = "WB_%s" % send_id
                    send = db(stable.id == send_id).select(stable.site_id,
                                                           stable.to_site_id,
                                                           limitby = (0, 1),
                                                           ).first()
                    site_id = send.site_id
                    to_site_id = send.to_site_id
                    site_ids = (site_id, to_site_id)
                    if site_id < to_site_id:
                        realm_name = "2SITES_%s_%s" % (site_id, to_site_id)
                    else:
                        realm_name = "2SITES_%s_%s" % (to_site_id, site_id)
                elif send_id:
                    # Inherit from the Send
                    stable = s3db.inv_send
                    send = db(stable.id == send_id).select(stable.realm_entity,
                                                           limitby = (0, 1),
                                                           ).first()
                    return send.realm_entity
                elif recv_id:
                    # Inherit from the Recv
                    rtable = s3db.inv_recv
                    recv = db(rtable.id == recv_id).select(rtable.realm_entity,
                                                           limitby = (0, 1),
                                                           ).first()
                    return recv.realm_entity

            #elif tablename == "inv_send":
            #    record_id = row["id"]
            #    realm_name = "WB_%s" % record_id
            #    to_site_id = db(table.id == record_id).select(table.to_site_id,
            #                                                  limitby = (0, 1),
            #                                                  ).first().to_site_id
            #    site_ids = (row["site_id"],
            #                to_site_id,
            #                )
            #elif tablename == "inv_recv":
            #    record_id = row["id"]
            #    realm_name = "GRN_%s" % record_id
            #    from_site_id = db(table.id == record_id).select(table.from_site_id,
            #                                                    limitby = (0, 1),
            #                                                    ).first().from_site_id
            #    site_ids = (row["site_id"],
            #                from_site_id
            #                )

            # Find/create the Realm
            rtable = s3db.pr_realm
            realm = db(rtable.name == realm_name).select(rtable.pe_id,
                                                         limitby = (0, 1),
                                                         ).first()
            if not realm:
                realm_id = rtable.insert(name = realm_name)
                realm = Storage(id = realm_id)
                s3db.update_super(rtable, realm)
            else:
                realm_id = None

            realm_entity = realm.pe_id

            # Lookup the PE ID for Sites involved
            stable = s3db.org_site
            sites = db(stable.site_id.belongs(site_ids)).select(stable.site_id,
                                                                stable.instance_type,
                                                                )
            instance_types = {}
            for site in sites:
                instance_type = site.instance_type
                if instance_type in instance_types:
                    instance_types[instance_type].append(site.site_id)
                else:
                    instance_types[instance_type] = [site.site_id]

            entities = []
            for instance_type in instance_types:
                itable = s3db.table(instance_type)
                instances = db(itable.site_id.belongs(instance_types[instance_type])).select(itable.pe_id)
                entities += [i.pe_id for i in instances]

            if realm_id:
                # New realm doesn't need old affiliations removing
                from s3db.pr import OU, \
                                    pr_add_affiliation
            elif realm_name.startswith("2SITES"):
                # Existing 2 Sites Realm doesn't need affiliations modifying
                return realm_entity
            else:
                # Get all current affiliations
                rtable = s3db.pr_role
                atable = s3db.pr_affiliation
                query = (atable.deleted == False) & \
                        (atable.pe_id.belongs(entities)) & \
                        (rtable.deleted == False) & \
                        (rtable.id == atable.role_id)
                affiliations = db(query).select(rtable.pe_id,
                                                rtable.role,
                                                )

                # Remove affiliations which are no longer needed
                from s3db.pr import OU, \
                                    pr_add_affiliation, \
                                    pr_remove_affiliation
                for a in affiliations:
                    pe_id = a.pe_id
                    role = a.role
                    if pe_id not in entities:
                        pr_remove_affiliation(pe_id, realm_entity, role=role)
                    else:
                        entities.remove(pe_id)

            # Add new affiliations
            for pe_id in entities:
                pr_add_affiliation(pe_id, realm_entity, role="Parent", role_type=OU)

            return realm_entity

        elif tablename == "org_organisation":
            # Suppliers & Partners should be in the realm of the user's root organisation
            ottable = s3db.org_organisation_type
            ltable = db.org_organisation_organisation_type
            query = (ltable.organisation_id == row["id"]) & \
                    (ltable.organisation_type_id == ottable.id)
            otype = db(query).select(ottable.name,
                                     limitby = (0, 1),
                                     ).first()
            if not otype or otype.name != RED_CROSS:
                use_user_organisation = True
                use_user_root_organisation = True

        elif tablename in ("org_facility", "pr_forum", "pr_group"):
            # Facilities, Forums and Groups should be in the realm of the user's organisation
            use_user_organisation = True

        elif tablename == "hrm_training":
            # Inherit realm entity from the related HR record
            htable = s3db.hrm_human_resource
            query = (table.id == row["id"]) & \
                    (htable.person_id == table.person_id) & \
                    (htable.deleted != True)
            rows = db(query).select(htable.realm_entity,
                                    limitby = (0, 2),
                                    )
            if len(rows) == 1:
                realm_entity = rows.first().realm_entity
            else:
                # Ambiguous => try course organisation
                ctable = s3db.hrm_course
                otable = s3db.org_organisation
                query = (table.id == row["id"]) & \
                        (ctable.id == table.course_id) & \
                        (otable.id == ctable.organisation_id)
                org = db(query).select(otable.pe_id,
                                       limitby = (0, 1),
                                       ).first()
                if org:
                    return org.pe_id
                # otherwise: inherit from the person record
        else:
            # Entity reference fields
            EID = "pe_id"
            OID = "organisation_id"
            SID = "site_id"
            #GID = "group_id"
            PID = "person_id"

            # Owner Entity Foreign Key
            realm_entity_fks = {"pr_contact": [("org_organisation", EID),
                                               #("po_household", EID),
                                               ("pr_person", EID),
                                               ],
                                "pr_contact_emergency": EID,
                                "pr_physical_description": EID,
                                "pr_address": [("org_organisation", EID),
                                               ("pr_person", EID),
                                               ],
                                "pr_image": EID,
                                "pr_identity": PID,
                                "pr_education": PID,
                                #"pr_note": PID,
                                "hrm_human_resource": SID,
                                "hrm_training": PID,
                                "hrm_training_event": OID,
                                "inv_adj": SID,
                                "inv_adj_item": "adj_id",
                                "inv_inv_item": SID,
                                "inv_recv": SID,
                                "inv_send": SID,
                                #"inv_track_item": "track_org_id",
                                #"inv_req": "site_id",
                                #"inv_req_item": "req_id",
                                #"po_household": "area_id",
                                #"po_organisation_area": "area_id",
                                }

            # Default Foreign Keys (ordered by priority)
            default_fks = (#"household_id",
                           "catalog_id",
                           "project_id",
                           "project_location_id",
                           )

            # Link Tables
            #realm_entity_link_table = {
            #    "project_task": Storage(tablename = "project_task_project",
            #                            link_key = "task_id"
            #                            )
            #    }
            #if tablename in realm_entity_link_table:
            #    # Replace row with the record from the link table
            #    link_table = realm_entity_link_table[tablename]
            #    table = s3db[link_table.tablename]
            #    rows = db(table[link_table.link_key] == row.id).select(table.id,
            #                                                           limitby = (0, 1),
            #                                                           )
            #    if rows:
            #        # Update not Create
            #        row = rows.first()

            # Check if there is a FK to inherit the realm_entity
            fk = realm_entity_fks.get(tablename, None)
            fks = [fk] if not isinstance(fk, list) else list(fk)
            fks.extend(default_fks)
            for default_fk in fks:
                if isinstance(default_fk, tuple):
                    instance_type, fk = default_fk
                else:
                    instance_type, fk = None, default_fk
                if fk not in table.fields:
                    continue

                # Inherit realm_entity from parent record
                if fk == EID:
                    if instance_type:
                        ftable = s3db.table(instance_type)
                        if not ftable:
                            continue
                    else:
                        ftable = s3db.pr_person
                    query = (ftable[EID] == row[EID])
                elif fk == SID:
                    # Need to get the entity from the instance, not the super
                    from s3db.pr import pr_get_pe_id
                    realm_entity = pr_get_pe_id("org_site",
                                                row[SID])
                    break
                elif fk == OID:
                    ftable = s3db.org_organisation
                    query = (ftable.id == row[OID])
                else:
                    # PID & other FKs not in row, so need to load
                    ftablename = table[fk].type[10:] # reference tablename
                    ftable = s3db[ftablename]
                    query = (table.id == row["id"]) & \
                            (table[fk] == ftable.id)
                record = db(query).select(ftable.realm_entity,
                                          limitby = (0, 1),
                                          ).first()
                if record:
                    return record.realm_entity
                #else:
                # Continue to loop through the rest of the default_fks
                # Fall back to default get_realm_entity function

        if use_user_organisation:
            auth = current.auth
            user = auth.user
            if user:
                # @ToDo - this might cause issues if the user's org is different
                #         from the realm that gave them permissions to create the record
                if use_user_root_organisation:
                    organisation_id = auth.root_org()
                else:
                    organisation_id = user.organisation_id
                from s3db.pr import pr_get_pe_id
                realm_entity = pr_get_pe_id("org_organisation",
                                            organisation_id)
            else:
                # Prepop data - need to handle this separately
                if tablename == "org_organisation":
                    # Use org_organisation_organisation
                    ltable = s3db.org_organisation_organisation
                    otable = s3db.org_organisation
                    query = (ltable.organisation_id == row["id"]) & \
                            (ltable.parent_id == otable.id)
                    parent = db(query).select(otable.realm_entity,
                                              limitby = (0, 1),
                                              ).first()
                    if parent:
                        return parent.realm_entity

        return realm_entity

    settings.auth.realm_entity = ifrc_realm_entity

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    #
    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("fr", "French"),
        ("pt-br", "Portuguese (Brazil)"),
        ("es", "Spanish"),
        ])
    # Default Language
    settings.L10n.default_language = "en"
    # Default timezone for users
    settings.L10n.timezone = "America/Bogota"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Unsortable 'pretty' date format (for use in English)
    settings.L10n.date_format = "%d-%b-%Y"
    # Make last name in person/user records mandatory
    #settings.L10n.mandatory_lastname = True # mother's surname
    settings.L10n.mandatory_middlename = True # father's surname
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this for Alternate Location Names
    settings.L10n.name_alt_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True

    # -------------------------------------------------------------------------
    # Finance settings
    #
    def currencies(default):
        """ RMS- and NS-specific currencies (lazy setting) """

        # Currencies that are common for all NS
        currencies = {"EUR" : "Euros",
                      "CHF" : "Swiss Francs",
                      "USD" : "United States Dollars",
                      }

        # NS-specific currencies
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            currencies["HNL"] = "Honduran Lempira"
        return currencies

    settings.fin.currencies = currencies

    def currency_default(default):
        """ NS-specific default currencies (lazy setting) """

        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            default = "HNL"
        #else:
        #    default = "USD"
        return default

    settings.fin.currency_default = currency_default

    def currency_represent(currency):
        """ NS-specific currency represent """

        if currency == "HNL":
            root_org = current.auth.root_org_name()
            if root_org == HNRC:
                return "L"
        return currency

    # -------------------------------------------------------------------------
    # Map Settings

    # Display Resources recorded to Admin-Level Locations on the map
    # @ToDo: Move into gis_config?
    settings.gis.display_L0 = True

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"

    # GeoNames username
    settings.gis.geonames_username = "rms_dev"

    # @ToDo: Lazy fn once we have NS to enable this for
    # (off for HN & off by default)
    settings.gis.postcode_selector = False

    # -------------------------------------------------------------------------
    # Filter Manager
    #settings.search.filter_manager = False

    # Use the label 'Camp' instead of 'Shelter'
    settings.ui.camp = True

    # Requires enabling fancyZoom JS & CSS
    #settings.ui.thumbnail = (60,60)

    # -------------------------------------------------------------------------
    # Default Summary
    #
    settings.ui.summary = ({"common": True,
                            "name": "add",
                            "widgets": [{"method": "create"}],
                            },
                           {"name": "table",
                            "label": "Table",
                            "widgets": [{"method": "datatable"}],
                            },
                           {"name": "charts",
                            "label": "Report",
                            "widgets": [{"method": "report", "ajax_init": True}],
                            },
                           {"name": "map",
                            "label": "Map",
                            "widgets": [{"method": "map", "ajax_init": True}],
                            },
                           )

    # -------------------------------------------------------------------------
    # Content Management
    #
    #settings.cms.hide_index = True
    settings.cms.richtext = True

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    #settings.msg.parser = "IFRC"

    # =========================================================================
    # Module Settings

    # -------------------------------------------------------------------------
    # Members
    #
    settings.member.cv_tab = True

    # -------------------------------------------------------------------------
    # Organisations
    #
    # Enable the use of Organisation Branches
    settings.org.branches = True
    settings.org.branches_tree_view = True
    # Set the length of the auto-generated org/site code the default is 10
    #settings.org.site_code_len = 3
    # Set the label for Sites
    settings.org.site_label = "Office/Warehouse/Facility"

    # -------------------------------------------------------------------------
    # Human Resource Management
    #
    # Uncomment to allow Staff & Volunteers to be registered without an email address
    settings.hrm.email_required = True
    settings.hrm.mix_staff = True
    # Uncomment to show the Organisation name in HR represents
    settings.hrm.show_organisation = True
    # Uncomment to allow HRs to have multiple Job Titles
    #settings.hrm.multiple_job_titles = True
    # Uncomment to have each root Org use a different Job Title Catalog
    settings.hrm.org_dependent_job_titles = True
    settings.hrm.staff_departments = False
    settings.hrm.teams = False
    # Uncomment to disable the use of HR Credentials
    settings.hrm.use_credentials = False
    # Uncomment to disable the use of HR Certificates
    #settings.hrm.use_certificates = False
    # Uncomment to filter certificates by (root) Organisation & hence not allow Certificates from other orgs to be added to a profile (except by Admin)
    #settings.hrm.filter_certificates = True
    # Uncomment to auto-create certificates for courses
    settings.hrm.create_certificates_from_courses = "organisation_id"
    settings.hrm.use_code = True
    settings.hrm.use_description = None # Replaced by Medical Information
    # Uncomment to enable the use of HR Education
    settings.hrm.use_education = True
    # Uncomment to hide Job Titles
    settings.hrm.use_job_titles = False
    settings.hrm.use_medical = "Medical Information"
    settings.hrm.use_national_id = True
    settings.hrm.use_skills = True
    # Custom label for Organisations in HR module
    settings.hrm.organisation_label = "National Society / Branch"
    # Custom label for Top-level Organisations in HR module
    settings.hrm.root_organisation_label = "National Society"
    # Uncomment to consolidate tabs into a single CV
    settings.hrm.cv_tab = True
    settings.hrm.vol_experience = "programme"
    # Uncomment to consolidate tabs into Staff Record (set to False to hide the tab)
    settings.hrm.record_tab = "record"
    # Use Locations for Training Events, not Facilities
    settings.hrm.event_site = False
    # Training Instructors are Multiple
    settings.hrm.training_instructors = "multiple"
    # Training Filters are Contains
    settings.hrm.training_filter_and = True
    settings.hrm.record_label = "Information"
    # Pass marks are defined by Course
    settings.hrm.course_pass_marks = True
    # Work History & Missions
    settings.hrm.staff_experience = "both"

    # Uncomment to do a search for duplicates in the new AddPersonWidget2
    settings.pr.lookup_duplicates = True
    settings.pr.separate_name_fields = 3

    #def dob_required(default):
    #    """ NS-specific dob_required (lazy setting) """

    #    if current.auth.override is True:
    #        default = False
    #    else:
    #        root_org = current.auth.root_org_name()
    #        if root_org == HNRC:
    #            default = False
    #        else:
    #            # Human Talent module for zone
    #            default = True
    #    return default

    #settings.pr.dob_required = dob_required

    def hrm_course_grades(default):
        """ Course Grades """

        default = {0: T("No Show"),
                   1: T("Left Early"),
                   #2: T("Attendance"),
                   8: T("Pass"),
                   9: T("Fail"),
                   }

        return default

    settings.hrm.course_grades = hrm_course_grades

    # =========================================================================
    def vol_programme_active(person_id):
        """
            Whether a Volunteer counts as 'Active' based on the number of hours
            they've done (both Trainings & Programmes) per month, averaged over
            the last year.
            If nothing recorded for the last 3 months, don't penalise as assume
            that data entry hasn't yet been done.

            @ToDo: This should be based on the HRM record, not Person record
                   - could be active with Org1 but not with Org2
        """

        now = current.request.utcnow

        # Time spent on Programme work
        htable = current.s3db.hrm_programme_hours
        query = (htable.deleted == False) & \
                (htable.person_id == person_id) & \
                (htable.date != None)
        programmes = current.db(query).select(htable.hours,
                                              htable.date,
                                              orderby = htable.date,
                                              )
        if programmes:
            # Ignore up to 3 months of records
            three_months_prior = (now - datetime.timedelta(days = 92))
            end = max(programmes.last().date, three_months_prior.date())
            last_year = end - datetime.timedelta(days = 365)
            # Is this the Volunteer's first year?
            if programmes.first().date > last_year:
                # Only start counting from their first month
                start = programmes.first().date
            else:
                # Start from a year before the latest record
                start = last_year

            # Total hours between start and end
            programme_hours = 0
            for programme in programmes:
                if programme.date >= start and programme.date <= end and programme.hours:
                    programme_hours += programme.hours

            # Average hours per month
            months = max(1, (end - start).days / 30.5)
            average = programme_hours / months

            # Active?
            if average >= 8:
                return True

        return False

    def hrm_vol_active(default):
        """ Whether & How to track Volunteers as Active """

        #root_org = current.auth.root_org_name()
        #if root_org in (ARCS, IRCS):
        #    # Simple checkbox
        #    return True
        #elif root_org in (CVTL, PMI, PYRC):
        #    # Use formula based on hrm_programme
        #    return vol_programme_active
        #elif root_org in (CRMADA, ):
        #    # Use formula based on vol_activity
        #    return vol_activity_active
        #return False

        # Use formula based on hrm_programme
        return vol_programme_active

    settings.hrm.vol_active = hrm_vol_active
    settings.hrm.vol_active_tooltip = "A volunteer is defined as active if they've participated in an average of 8 or more hours of Program work or Trainings per month in the last year"

    # Roles which are permitted to export ID cards
    ID_CARD_EXPORT_ROLES = ("ORG_ADMIN", "hr_manager", "hr_assistant")

    # -------------------------------------------------------------------------
    # RIT
    settings.deploy.team_label = "RIT"
    settings.customise_deploy_home = deploy_index # Imported from controllers.py
    # Alerts get sent to all recipients
    settings.deploy.manual_recipients = False
    settings.deploy.post_to_twitter = True

    # -------------------------------------------------------------------------
    # Projects
    settings.project.assign_staff_tab = False
    # Uncomment this to use settings suitable for a global/regional organisation (e.g. DRR)
    settings.project.mode_3w = True
    # Uncomment this to use DRR (Disaster Risk Reduction) extensions
    settings.project.mode_drr = True
    # Uncomment this to use Activity Types for Activities & Projects
    #settings.project.activity_types = True
    # Uncomment this to use Codes for projects
    settings.project.codes = True
    # Uncomment this to call project locations 'Communities'
    #settings.project.community = True
    # Uncomment this to enable Demographics in 3W projects
    #settings.project.demographics = True
    # Uncomment this to enable Hazards in 3W projects
    settings.project.hazards = True
    # Uncomment this to enable Indicators in projects
    # Just HNRC
    #settings.project.indicators = True
    # Uncomment this to use multiple Budgets per project
    settings.project.multiple_budgets = True
    # Uncomment this to use multiple Organisations per project
    settings.project.multiple_organisations = True
    # Ondelete behaviour for ProjectPlanningModel
    settings.project.planning_ondelete = "RESTRICT"
    # Uncomment this to enable Programmes in projects
    settings.project.programmes = True
    # Uncomment this to enable Themes in 3W projects
    settings.project.themes = True
    # Uncomment this to customise
    # Links to Filtered Components for Donors & Partners
    settings.project.organisation_roles = {
        1: T("Host National Society"),
        2: T("Partner"),
        3: T("Donor"),
        #4: T("Customer"), # T("Beneficiary")?
        #5: T("Supplier"),
        9: T("Partner National Society"),
    }

    # -------------------------------------------------------------------------
    # Inventory Management
    settings.customise_inv_home = inv_Dashboard() # Imported from controllers.py

    # Hide Staff Management Tabs for Facilities in Inventory Module
    settings.inv.facility_manage_staff = False
    settings.inv.document_filing = True
    settings.inv.minimums = True
    settings.inv.send_gift_certificate = True
    settings.inv.send_packaging = True
    # Uncomment if you need a simpler (but less accountable) process for managing stock levels
    #settings.inv.direct_stock_edits = True
    settings.inv.stock_count = False
    settings.inv.item_status = {#0: NONE, # Not defined yet
                                0: T("Good"),
                                1: T("Damaged"),
                                #1: T("Dump"),
                                #2: T("Sale"),
                                #3: T("Reject"),
                                #4: T("Surplus")
                                }
    settings.inv.recv_types = {#0: NONE, In Shipment Types
                               #11: T("Internal Shipment"), In Shipment Types
                               32: T("Donation"),
                               34: T("Purchase"),
                               36: T("Loan"), # 'Consignment'?
                               37: T("In Transit"),  # Loaning warehouse space to another agency
                               }
    # Calculate Warehouse Free Capacity
    settings.inv.warehouse_free_capacity_calculated = True
    settings.inv.req_project = True
    settings.inv.req_reserve_items = True
    # Use structured Bins
    settings.inv.bin_site_layout = True
    settings.inv.recv_ref_writable = True
    settings.inv.send_ref_writable = True
    # Use Stock Cards
    settings.inv.stock_cards = True

    # Disable Alternate Items
    settings.supply.use_alt_name = False

    transport_opts = {"Air": T("Air"),
                      "Sea": T("Sea"),
                      "Road": T("Road"),
                      "Rail": T("Rail"),
                      "Hand": T("Hand"),
                      }

    # -------------------------------------------------------------------------
    # Requestions
    # Uncomment to disable Inline Forms
    settings.inv.req_inline_forms = False
    # No need to use Commits (default anyway)
    #settings.inv.req_use_commit = False
    # Should Requests ask whether Transportation is required?
    settings.inv.req_ask_transport = True
    # Request Numbers are entered manually
    settings.inv.generate_req_number = False
    settings.inv.req_pack_values = False
    # Don't Match Requests (they are assigned instead)
    settings.inv.req_match_tab = False
    # HNRC disable Request Matching as don't want users making requests to see what stock is available
    # PIRAC want this to be done by the Logistics Approver
    settings.inv.req_prompt_match = False
    # Uncomment to disable Recurring Request
    settings.inv.req_recurring = False
    # Use Order Items
    settings.inv.req_order_item = True
    # Requester doesn't need Update rights for the Site
    settings.inv.requester_site_updateable = False
    # Use Workflow
    settings.inv.req_workflow = True

    # =========================================================================
    # Template Modules
    #
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
                name_nice = "RMS",
                restricted = False, # Use ACLs to control access to this module
                access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
                #module_type = None  # This item is not shown in the menu
            )),
        ("admin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                #module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                #module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = "Needed for Breadcrumbs",
                restricted = False,
                #module_type = None  # No Menu
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
                #module_type = None  # This item is handled separately for the menu
            )),
        ("translate", Storage(
                name_nice = T("Translation Functionality"),
                #description = "Selective translation of strings based on module.",
                #module_type = None,
            )),
        # Uncomment to enable internal support requests
        ("support", Storage(
                name_nice = T("Support"),
                #description = "Support Requests",
                restricted = True,
                #module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = "Situation Awareness & Geospatial Analysis",
                restricted = True,
                #module_type = 6,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Person Registry"),
                #description = "Central point to record details on People",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                #module_type = 10
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
                restricted = True,
                #module_type = 1
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("vol", Storage(
                name_nice = T("Volunteers"),
                #description = "Human Resources Management",
                restricted = True,
                #module_type = 2,
            )),
        ("cms", Storage(
                name_nice = T("Content Management"),
                #description = "Content Management System",
                restricted = True,
                module_type = None,
            )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = "A library of digital resources, such as photos, documents and reports",
                restricted = True,
                #module_type = 10,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = "Sends & Receives Alerts via Email & SMS",
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                #module_type = None,
            )),
        ("supply", Storage(
                name_nice = T("Supply Chain Management"),
                #description = "Used within Inventory Management, Request Management and Asset Management",
                restricted = True,
                #module_type = None, # Not displayed
            )),
        ("inv", Storage(
                name_nice = T("Warehouses"),
                #description = "Receiving and Sending Items",
                restricted = True,
                #module_type = 4
            )),
        #("proc", Storage(
        #        name_nice = T("Procurement"),
        #        restricted = True,
        #        #module_type = None, # Not displayed
        #    )),
        #("asset", Storage(
        #        name_nice = T("Assets"),
        #        #description = "Recording and Assigning Assets",
        #        restricted = True,
        #        #module_type = 5,
        #    )),
        #("req", Storage(
        #        name_nice = T("Requests"),
        #        #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #        restricted = True,
        #        #module_type = 10,
        #    )),
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                #module_type = 2
            )),
        ("budget", Storage(
                name_nice = T("Budgets"),
                #description = "Tracking of Budgets",
                restricted = True,
                #module_type = None
            )),
        #("survey", Storage(
        #        name_nice = T("Assessments"),
        #        #description = "Create, enter, and manage surveys.",
        #        restricted = True,
        #        #module_type = 5,
        #    )),
        # Used by RIT
        ("event", Storage(
                name_nice = T("Events"),
                #description = "Events",
                restricted = True,
                #module_type = 10
            )),
        ("member", Storage(
               name_nice = T("Partners"),
               #description = "Membership Management System",
               restricted = True,
               #module_type = 10,
           )),
        ("deploy", Storage(
               name_nice = T("Regional Intervention Teams"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
               #module_type = 10,
           )),
        #("po", Storage(
        #       name_nice = T("Recovery Outreach"),
        #       #description = "Population Outreach",
        #       restricted = True,
        #       #module_type = 10,
        #   )),
        ("stats", Storage(
                name_nice = T("Statistics"),
                #description = "Manages statistics",
                restricted = True,
                #module_type = None,
            )),
        #("vulnerability", Storage(
        #        name_nice = T("Vulnerability"),
        #        #description = "Manages vulnerability indicators",
        #        restricted = True,
        #        #module_type = 10,
        #    )),
    ])

    # -------------------------------------------------------------------------
    # Functions which are local to this Template
    # -------------------------------------------------------------------------
    def ns_only(tablename,
                fieldname = "organisation_id",
                required = True,
                branches = True,
                updateable = True,
                limit_filter_opts = True
                ):
        """
            Function to configure an organisation_id field to be restricted to just
            NS/Branch

            Args:
                required: Field is mandatory
                branches: Include Branches
                updateable: Limit to Orgs which the user can update
                limit_filter_opts: Also limit the Filter options

            Note:
                If limit_filter_opts=True, apply in customise_xx_controller inside prep,
                after standard_prep is run
        """

        # Lookup organisation_type_id for Red Cross
        db = current.db
        s3db = current.s3db
        ttable = s3db.org_organisation_type
        try:
            type_id = db(ttable.name == RED_CROSS).select(ttable.id,
                                                          cache = s3db.cache,
                                                          limitby = (0, 1),
                                                          ).first().id
        except AttributeError:
            # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            return

        # Load standard model
        f = s3db[tablename][fieldname]

        if limit_filter_opts:
            # Find the relevant filter widget & limit it's options
            filter_widgets = s3db.get_config(tablename, "filter_widgets")
            filter_widget = None
            if filter_widgets:
                from s3 import FS, S3HierarchyFilter
                for w in filter_widgets:
                    if isinstance(w, S3HierarchyFilter) and \
                       w.field == "organisation_id":
                        filter_widget = w
                        break
            if filter_widget is not None:
                selector = FS("organisation_organisation_type.organisation_type_id")
                filter_widget.opts["filter"] = (selector == type_id)

        # Label
        if branches:
            f.label = T("National Society / Branch")
        else:
            f.label = T("National Society")

        # Requires

        # Filter by type
        ltable = db.org_organisation_organisation_type
        rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
        filter_opts = [row.organisation_id for row in rows]

        auth = current.auth
        s3_has_role = auth.s3_has_role
        Admin = s3_has_role("ADMIN")
        if branches:
            if Admin:
                parent = True
            else:
                # @ToDo: Set the represent according to whether the user can see resources of just a single NS or multiple
                # @ToDo: Consider porting this into core
                user = auth.user
                if user:
                    realms = user.realms
                    #delegations = user.delegations
                    if realms:
                        parent = True
                    else:
                        parent = False
                else:
                    parent = True

        else:
            # Keep the represent function as simple as possible
            parent = False
            # Exclude branches
            btable = s3db.org_organisation_branch
            rows = db((btable.deleted != True) &
                      (btable.branch_id.belongs(filter_opts))).select(btable.branch_id)
            filter_opts = list(set(filter_opts) - set(row.branch_id for row in rows))

        from s3db.org import org_OrganisationRepresent
        organisation_represent = org_OrganisationRepresent
        represent = organisation_represent(parent=parent)
        f.represent = represent

        from s3 import IS_ONE_OF
        requires = IS_ONE_OF(db, "org_organisation.id",
                             represent,
                             filterby = "id",
                             filter_opts = filter_opts,
                             updateable = updateable,
                             orderby = "org_organisation.name",
                             sort = True,
                             )
        if not required:
            from gluon import IS_EMPTY_OR
            requires = IS_EMPTY_OR(requires)
        f.requires = requires

        if parent:
            # Use hierarchy-widget
            from s3 import FS, S3HierarchyWidget
            # No need for parent in represent (it's a hierarchy view)
            node_represent = organisation_represent(parent = False)
            # Filter by type
            # (no need to exclude branches - we wouldn't be here if we didn't use branches)
            selector = FS("organisation_organisation_type.organisation_type_id")
            f.widget = S3HierarchyWidget(lookup = "org_organisation",
                                         filter = (selector == type_id),
                                         represent = node_represent,
                                         multiple = False,
                                         leafonly = False,
                                         )
        else:
            # Dropdown not Autocomplete
            f.widget = None

        # Comment
        if (Admin or s3_has_role("ORG_ADMIN")):
            # Need to do import after setting Theme
            from s3layouts import S3PopupLink
            from s3 import S3ScriptItem
            add_link = S3PopupLink(c = "org",
                                   f = "organisation",
                                   vars = {"organisation_type.name": RED_CROSS},
                                   label = T("Create National Society"),
                                   title = T("National Society"),
                                   )
            comment = f.comment
            if not comment or isinstance(comment, S3PopupLink):
                f.comment = add_link
            elif isinstance(comment[1], S3ScriptItem):
                # Don't overwrite scripts
                f.comment[0] = add_link
            else:
                f.comment = add_link
        else:
            # Not allowed to add NS/Branch
            f.comment = ""

    # -------------------------------------------------------------------------
    def user_org_default_filter(selector, tablename=None):
        """
            Default filter for organisation_id:
            * Use the user's organisation if logged-in and associated with an
              organisation.
        """

        auth = current.auth
        user_org_id = auth.is_logged_in() and auth.user.organisation_id
        if user_org_id:
            return user_org_id
        else:
            # no default
            return {}

    # -------------------------------------------------------------------------
    #def user_org_and_children_default_filter(selector, tablename=None):
    #    """
    #        Default filter for organisation_id:
    #        * Use the user's organisation if logged-in and associated with an
    #          organisation.
    #    """

    #    auth = current.auth
    #    user_org_id = auth.is_logged_in() and auth.user.organisation_id
    #    if user_org_id:
    #        db = current.db
    #        s3db = current.s3db
    #        otable = s3db.org_organisation
    #        org = db(otable.id == user_org_id).select(otable.pe_id,
    #                                                  limitby = (0, 1),
    #                                                  ).first()
    #        if org:
    #            from s3db.pr import pr_get_descendants
    #            pe_id = org.pe_id
    #            pe_ids = pr_get_descendants((pe_id,),
    #                                        entity_types=("org_organisation",))
    #            rows = db(otable.pe_id.belongs(pe_ids)).select(otable.id)
    #            ids = [row.id for row in rows]
    #            ids.append(user_org_id)
    #            return ids
    #        else:
    #            return user_org_id
    #    else:
    #        # no default
    #        return {}

    # -------------------------------------------------------------------------
    def auth_add_role(user_id,
                      group_id,
                      for_pe = None,
                      from_role_manager = True,
                      ):
        """
            Automatically add subsidiary roles & set to appropriate entities
        """

        auth = current.auth
        add_membership = auth.add_membership
        system_roles = auth.get_system_roles()

        if from_role_manager:
            # Add the main Role
            add_membership(group_id = group_id,
                           user_id = user_id,
                           )

        # Is this the Admin role?
        if group_id == system_roles.ADMIN:
            # No Subsidiary Roles to add
            return

        db = current.db
        gtable = db.auth_group

        # Lookup the role
        group = db(gtable.id == group_id).select(gtable.uuid,
                                                 limitby = (0, 1),
                                                 ).first()
        role = group.uuid
        if role in ("hn_user",
                    "rms_user",
                    "rc_logs_user",
                    "rc_user",
                    "logs_manager_national",
                    "wh_operator_national",
                    ):
            # This is a Hidden role, so coming in advanced mode
            # - don't do anything further
            return

        s3db = current.s3db

        # Lookup the User Organisation
        utable = db.auth_user
        otable = s3db.org_organisation
        query = (utable.id == user_id) & \
                (otable.id == utable.organisation_id)
        org = db(query).select(otable.id,
                               otable.name,
                               otable.pe_id,
                               otable.root_organisation,
                               limitby = (0, 1),
                               ).first()
        if not org:
            # Default ADMIN in prepop: bail
            return

        # Lookup the RC Org Group
        ogtable = s3db.org_group
        org_group = db(ogtable.name == "RC").select(ogtable.pe_id,
                                                    limitby = (0, 1),
                                                    ).first()
        rc_group_pe_id = org_group.pe_id

        # Lookup the root entity
        root_org = org.root_organisation
        if root_org == org.id:
            ns_level = True
            ns = org
        else:
            ns_level = False
            ns = db(otable.id == root_org).select(otable.name,
                                                  otable.pe_id,
                                                  limitby = (0, 1),
                                                  ).first()
        ns_entity = ns.pe_id

        # Add to relevant NS User role
        if ns.name == HNRC:
            user_role = "hn_user"
        else:
            user_role = "rms_user"
        roles = [user_role,
                 "rc_user",
                 ]

        # Add to additional roles for Logs Users
        if role == "logs_manager":
            if ns_level:
                roles.append("rc_logs_user")
            else:
                roles += ["rc_logs_user",
                          "logs_manager_national",
                          ]
        elif role == "wh_operator":
            roles += ["rc_logs_user",
                      "wh_operator_national",
                      ]

        if len(roles) == 1:
            query = (gtable.uuid == roles[0])
        else:
            query = (gtable.uuid.belongs(roles))

        groups = db(query).select(gtable.id,
                                  gtable.uuid,
                                  )
        for group in groups:
            if group.uuid in ("rc_logs_user",
                              "rc_user",
                              ):
                add_membership(group_id = group.id,
                               user_id = user_id,
                               entity = rc_group_pe_id,
                               )
            else:
                add_membership(group_id = group.id,
                               user_id = user_id,
                               entity = ns_entity,
                               )

    settings.auth.add_role = auth_add_role

    # -------------------------------------------------------------------------
    def auth_remove_role(user_id, group_id, for_pe=None):
        """
            Automatically remove subsidiary roles
        """

        auth = current.auth
        system_roles = auth.get_system_roles()
        withdraw_role = auth.s3_withdraw_role

        # Remove the main Role
        withdraw_role(user_id, group_id)

        # Is this the Admin role?
        if group_id == system_roles.ADMIN:
            # No Subsidiary Roles to remove
            return

        db = current.db
        gtable = db.auth_group

        logs_roles = ("logs_manager",
                      "wh_operator",
                      )

        # Lookup the role
        group = db(gtable.id == group_id).select(gtable.uuid,
                                                 limitby = (0, 1),
                                                 ).first()
        role = group.uuid
        if role not in logs_roles:
            # Not a Logs role
            # - don't do anything further
            return

        # Do they still have a Logs role?
        mtable = db.auth_membership
        query = (mtable.user_id == user_id) & \
                (gtable.id == mtable.group_id) & \
                (gtable.uuid.belongs(logs_roles))
        memberships = db(query).select(mtable.id,
                                       limitby = (0, 1),
                                       ).first()
        if not memberships:
            # Withdraw the Logs RC role
            group = db(gtable.uuid == "rc_logs_user").select(gtable.id,
                                                       limitby = (0, 1),
                                                       ).first()
            withdraw_role(user_id, group.id, for_pe=[])  

        # Lookup the User Organisation
        utable = db.auth_user
        otable = current.s3db.org_organisation
        query = (utable.id == user_id) & \
                (otable.id == utable.organisation_id)
        org = db(query).select(otable.id,
                               otable.pe_id,
                               otable.root_organisation,
                               limitby = (0, 1),
                               ).first()
        if not org:
            # Default ADMIN in prepop: bail
            return

        # Lookup the root entity
        root_org = org.root_organisation
        if root_org == org.id:
            if role == "logs_manager":
                # No more subsidiary roles
                return
            ns = org
        else:
            ns = db(otable.id == root_org).select(otable.pe_id,
                                                  limitby = (0, 1),
                                                  ).first()
        ns_entity = ns.pe_id

        if role == "logs_manager":
            ns_level = "logs_manager_national"
        else:
            # wh_operator
            ns_level = "wh_operator_national"

        group = db(gtable.uuid == ns_level).select(gtable.id,
                                                   limitby = (0, 1),
                                                   ).first()
        withdraw_role(user_id, group.id, for_pe=ns_entity)

    settings.auth.remove_role = auth_remove_role

    # =========================================================================
    def auth_membership_create_onaccept(form):
        """
            Automatically add subsidiary roles & set to appropriate entities
        """

        form_vars = form.vars

        auth_add_role(form_vars.user_id,
                      form_vars.group_id,
                      for_pe = form_vars.pe_id,
                      from_role_manager = False,
                      )

    # =========================================================================
    def customise_auth_user_resource(r, tablename):

        db = current.db
        configure = current.s3db.configure

        configure("auth_membership",
                  create_onaccept = auth_membership_create_onaccept,
                  )

        table = db.auth_user
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.append((T("Tables have Scrollbar"), "user_options.unresponsive_tables"))

        from s3 import S3SQLCustomForm
        crud_form = S3SQLCustomForm(*crud_fields)

        configure(tablename,
                  crud_form = crud_form,
                  dynamic_components = True,
                  )

    settings.customise_auth_user_resource = customise_auth_user_resource

    # -------------------------------------------------------------------------
    def customise_auth_user_controller(**attr):
        """
            Customise admin/user() and default/user() controllers
        """

        # Organisation needs to be an NS/Branch
        ns_only("auth_user",
                required = True,
                branches = True,
                updateable = False, # Need to see all Orgs in Registration screens
                )

        table = current.db.auth_user
        table.first_name.label = T("Forenames")
        table.last_name.label = T("Father's Surname")

        # What this does currently:
        #(A) If the User Account creating the new account is associated with
        #     the Panamanian RC then the Panama-specific mail is sent
        #(B) If the current interface of the User creating the new account is
        #    in Spanish then the Spanish mail is sent
        #(C) Otherwise the English mail is sent
        # What we really want (will require a little deeper customisation of Auth...pending budget):
        #(A) If the User being created is associated with the Panamanian RC
        #     then the Panama-specific mail is sent
        #(B) If the User being created has their account is in Spanish then
        #    the Spanish mail is sent
        #(C) Otherwise the English mail is sent
        auth = current.auth
        messages = auth.messages
        messages.lock_keys = False
        if auth.root_org_name() == PARC:
            messages.welcome_email = \
"""Estimado, estimada,
Le damos la más cordial bienvenida al Sistema de Gestión de Recursos (RMS).

Su nombre de usuarios es: su correo electrónico
Contraseña: cruzroja (puede ser cambiando por usted cuando lo desee)
Para acceder a la plataforma visite: https://rms.cruzroja.org

Si tiene algún problema para acceder a la plataforma póngase en contacto con:

Haylin Mosquera – Coordinadora de Voluntariado de la Cruz Roja Panameña – E: voluntariado@cruzroja.org.pa

Saludos Cordiales

EQUIPO DE SOPORTE
RMS – Sistema de Gestión de Recursos

Albrook, Calle Jorge Bolivar Alemán, Edifico 453
Ciudad de Panamá, Panamá
Tel: (507) 315-1388 / 315-1389
Email: rmssoporte@cruzroja.org.pa
www.cruzroja.org.pa / rms.cruzroja.org"""
        else:
            if current.session.s3.language == "es":
                messages.welcome_email = \
"""Estimado, estimada,
Le damos la más cordial bienvenida al Sistema de Gestión de Recursos (RMS).

Su nombre de usuarios es: su correo electrónico
Contraseña: cruzroja (puede ser cambiando por usted cuando lo desee)
Para acceder a la plataforma visite: https://rms.cruzroja.org

Saludos Cordiales,
Equipo de Soporte RMS"""
            else:
                # "en"
                messages.welcome_email = \
"""Dear,
We welcome you to the Resource Management System (RMS).

Your user name is: your e-mail address
Password: redcross (can be changed by you at any time)
To access the platform visit: https://rms.cruzroja.org

Best regards,
RMS Support Team"""

        messages.lock_keys = True

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -------------------------------------------------------------------------
    def customise_deploy_alert_resource(r, tablename):

        s3db = current.s3db

        # Only send Alerts via Email
        # @ToDo: Also send via Twitter
        f = s3db[tablename].contact_method
        f.readable = f.writable = False

        #from s3 import S3SQLCustomForm

        #crud_form = S3SQLCustomForm("mission_id",
        #                            "subject",
        #                            "body",
        #                            "modified_on",
        #                            )

        #s3db.configure(tablename,
        #               crud_form = crud_form,
        #               list_fields = ["mission_id",
        #                              "subject",
        #                              "body",
        #                              ],
        #               )

    settings.customise_deploy_alert_resource = customise_deploy_alert_resource

    # -------------------------------------------------------------------------
    def deploy_application_onaccept(form):
        """
            RIT Members should be added to the RIT Role
        """

        db = current.db
        s3db = current.s3db
        htable = db.hrm_human_resource
        ptable = db.pr_person

        # Find the Person
        human_resource_id = form.vars.get("human_resource_id")
        if human_resource_id:
            query = (htable.id == human_resource_id)
        else:
            table = db.deploy_application
            query = (table.id == form.vars.get("id")) & \
                    (table.human_resource_id == htable.id)

        hr = db(query).select(htable.person_id,
                              limitby = (0, 1),
                              ).first()
        person_id = hr.person_id

        # Do they have a User Account?
        ltable = s3db.pr_person_user
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby = (0, 1),
                                ).first()
        if link:
            # Add them to the RIT role
            current.auth.s3_assign_role(link.user_id, "RIT_MEMBER")

    # -------------------------------------------------------------------------
    def customise_deploy_application_resource(r, tablename):

        current.s3db.configure(tablename,
                               create_onaccept = deploy_application_onaccept,
                               )

    settings.customise_deploy_application_resource = customise_deploy_application_resource

    # -------------------------------------------------------------------------
    def customise_deploy_mission_resource(r, tablename):

        s3db = current.s3db
        s3db[tablename].event_type_id.label = T("Disaster Type")
        COUNTRY = current.messages.COUNTRY

        from s3 import S3SQLCustomForm

        crud_form = S3SQLCustomForm("name",
                                    "date",
                                    "location_id",
                                    "event_type_id",
                                    )

        #from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3TextFilter
        #filter_widgets = [S3TextFilter(["name",
        #                                "event_type_id$name",
        #                                "location_id",
        #                                ],
        #                               label = T("Search"),
        #                               ),
        #                  S3LocationFilter("location_id",
        #                                   label = COUNTRY,
        #                                   widget = "multiselect",
        #                                   levels = ["L0"],
        #                                   hidden = True,
        #                                   ),
        #                  S3OptionsFilter("event_type_id",
        #                                  widget = "multiselect",
        #                                  hidden = True,
        #                                  ),
        #                  #S3OptionsFilter("status",
        #                  #                options = s3db.deploy_mission_status_opts,
        #                  #                hidden = True,
        #                  #                ),
        #                  S3DateFilter("date",
        #                               hide_time = True,
        #                               hidden = True,
        #                               ),
        #                  ]

        list_fields = ["name",
                       "date",
                       "event_type_id",
                       (COUNTRY, "location_id"),
                       (T("Responses"), "response_count"),
                       (T("Members Deployed"), "hrquantity"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_deploy_mission_resource = customise_deploy_mission_resource

    # -------------------------------------------------------------------------
    def customise_event_event_type_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Disaster Type"),
            title_display = T("Disaster Type Details"),
            title_list = T("Disaster Types"),
            title_update = T("Edit Disaster Type Details"),
            title_upload = T("Import Disaster Types"),
            label_list_button = T("List Disaster Types"),
            label_delete_button = T("Delete Disaster Type"),
            msg_record_created = T("Disaster Type added"),
            msg_record_modified = T("Disaster Type Details updated"),
            msg_record_deleted = T("Disaster Type deleted"),
            msg_list_empty = T("No Disaster Types currently defined"),
            )

    settings.customise_event_event_type_resource = customise_event_event_type_resource

    # -------------------------------------------------------------------------
    def customise_hrm_certificate_controller(**attr):

        table = current.s3db.hrm_course
        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            # See all Certificates
            pass
        elif auth.s3_has_roles(("training_coordinator",
                                "training_assistant",
                                )):
            # Only show this Center's Certificates
            organisation_id = auth.user.organisation_id
            current.response.s3.filter = (table.organisation_id == organisation_id) | \
                                         (table.organisation_id == None)
            # Default to this Training Center
            table.organisation_id.default = organisation_id
        else:
            # See NS Certificates
            organisation_id = auth.root_org()
            current.response.s3.filter = (table.organisation_id == organisation_id) | \
                                         (table.organisation_id == None)
            # Default to this NS
            table.organisation_id.default = organisation_id
        return attr

    settings.customise_hrm_certificate_controller = customise_hrm_certificate_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_controller(**attr):

        table = current.s3db.hrm_course
        auth = current.auth
        if auth.s3_has_role("ADMIN"):
            # See all Courses
            pass
        elif auth.s3_has_roles(("training_coordinator",
                                "training_assistant",
                                )):
            # Only show this Center's courses
            current.response.s3.filter = (table.organisation_id == auth.user.organisation_id) | (table.organisation_id == None)
        else:
            # See NS Courses
            current.response.s3.filter = (table.organisation_id == auth.root_org()) | (table.organisation_id == None)

        return attr

    settings.customise_hrm_course_controller = customise_hrm_course_controller

    # -------------------------------------------------------------------------
    def customise_hrm_course_resource(r, tablename):

        from gluon import IS_EMPTY_OR, IS_NOT_IN_DB
        from s3 import S3SQLCustomForm

        db = current.db
        auth = current.auth
        s3db = current.s3db
        table = s3db[tablename]

        # Code should be Unique
        f = table.code
        f.requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "hrm_course.code"))

        if auth.s3_has_roles(("training_coordinator",
                              "training_assistant",
                              )):
            f = table.organisation_id
            f.label = T("Training Center")
            f.comment = False # Don't create here
            from s3db.org import org_OrganisationRepresent
            org_represent = org_OrganisationRepresent(parent = False)
            f.represent = org_represent

        list_fields = ["code",
                       "name",
                       ]

        has_role = auth.s3_has_role
        if has_role("ADMIN"):
            table.organisation_id.label = T("National Society / Training Center")
            list_fields.insert(0, "organisation_id")
            #f.readable = f.writable = True
            #ttable = s3db.org_organisation_type
            #try:
            #    type_id = db(ttable.name == "Training Center").select(ttable.id,
            #                                                          limitby = (0, 1),
            #                                                          ).first().id
            #except:
            #    # No/incorrect prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            #    pass
            #else:
            #    ltable = s3db.org_organisation_organisation_type
            #    rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
            #    filter_opts = [row.organisation_id for row in rows]

            #    f.requires = IS_ONE_OF(db, "org_organisation.id",
            #                           org_represent,
            #                           orderby = "org_organisation.name",
            #                           sort = True,
            #                           filterby = "id",
            #                           filter_opts = filter_opts,
            #                           )

        elif has_role("training_coordinator"):
            f.default = auth.user.organisation_id

        crud_form = S3SQLCustomForm("organisation_id",
                                    "code",
                                    "name",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       orderby = "hrm_course.code",
                       )

    settings.customise_hrm_course_resource = customise_hrm_course_resource

    # -------------------------------------------------------------------------
    #def customise_hrm_department_controller(**attr):

    #    # Organisation needs to be an NS/Branch
    #    ns_only("hrm_department",
    #            required = False,
    #            branches = False,
    #            )

    #    return attr

    #settings.customise_hrm_department_controller = customise_hrm_department_controller

    # -------------------------------------------------------------------------
    #def emergency_contact_represent(row):
    #    """
    #        Representation of Emergency Contacts (S3Represent label renderer)

    #        Args:
    #           row: the row
    #    """

    #    items = [row["pr_contact_emergency.name"]]
    #    relationship = row["pr_contact_emergency.relationship"]
    #    if relationship:
    #        items.append(" (%s)" % relationship)
    #    phone_number = row["pr_contact_emergency.phone"]
    #    if phone_number:
    #        items.append(": %s" % phone_number)
    #    return "".join(items)

    # -------------------------------------------------------------------------
    def customise_hrm_home():

        #from gluon import URL
        from s3 import s3_redirect_default

        has_role = current.auth.s3_has_role
        len_roles = len(current.session.s3.roles)
        if (len_roles <= 2) or \
           (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
            # No specific Roles
            # Go to Personal Profile
            s3_redirect_default(URL(f="person"))
        else:
            # Bypass home page & go direct to searchable list of Staff
            s3_redirect_default(URL(f = "human_resource",
                                    args = "summary",
                                    ))

    settings.customise_hrm_home = customise_hrm_home

    # -------------------------------------------------------------------------
    def customise_hrm_experience_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Work History"),
            title_display = T("Work History Details"),
            title_list = T("Work History"),
            title_update = T("Edit Work History"),
            label_list_button = T("List Work History"),
            label_delete_button = T("Delete Work History"),
            msg_record_created = T("Work History added"),
            msg_record_modified = T("Work History updated"),
            msg_record_deleted = T("Work History deleted"),
            msg_list_empty = T("No entries currently registered"),
            )

    settings.customise_hrm_experience_resource = customise_hrm_experience_resource

    # -------------------------------------------------------------------------
    def hrm_human_resource_create_onaccept(form):
        """
            If the Staff/Volunteer is RC then create them a user account with a random password
            - only called when created by RIT_ADMIN through the web forms (not import)
            - only happens if an email has been set
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Call normal onaccept
        from s3db.hrm import hrm_human_resource_onaccept
        hrm_human_resource_onaccept(form)

        # Is the person RC?
        organisation_id = form_vars.get("organisation_id")
        if not organisation_id:
            hr_id = form_vars.get("id")
            if not hr_id:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR as no id in the form")
                return

            htable = s3db.hrm_human_resource
            hr = db(htable.id == hr_id).select(htable.id,
                                               htable.person_id,
                                               htable.type,
                                               htable.organisation_id,
                                               limitby = (0, 1),
                                               ).first()
            try:
                organisation_id = hr.organisation_id
            except AttributeError:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return
        else:
            hr = None

        ttable = s3db.org_organisation_type
        ltable = s3db.org_organisation_organisation_type
        query = (ttable.name == RED_CROSS) & \
                (ltable.organisation_type_id == ttable.id) & \
                (ltable.organisation_id == organisation_id)
        RC = db(query).select(ltable.id,
                              limitby = (0, 1),
                              ).first()
        if not RC:
            return

        # Collect the Details needed
        person_id = form_vars.get("person_id")
        if not person_id:
            if not hr:
                hr_id = form_vars.get("id")
                if not hr_id:
                    # Nothing we can do!
                    current.log.warning("Cannot create user for HR as no id in the form")
                    return

                htable = s3db.hrm_human_resource
                hr = db(htable.id == hr_id).select(htable.id,
                                                   htable.person_id,
                                                   htable.type,
                                                   limitby = (0, 1),
                                                   ).first()
            try:
                person_id = hr.person_id
            except AttributeError:
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return

        ptable = s3db.pr_person
        person = db(ptable.id == person_id).select(ptable.id,
                                                   ptable.first_name,
                                                   ptable.middle_name, # NB We use middle_name for User in RMS Americas!
                                                   ptable.pe_id,
                                                   limitby = (0, 1),
                                                   ).first()
        try:
            pe_id = person.pe_id
        except AttributeError:
            # Nothing we can do!
            return

        ctable = s3db.pr_contact
        query = (ctable.pe_id == pe_id) & \
                (ctable.contact_method == "EMAIL")
        contact = db(query).select(ctable.value,
                                   limitby = (0, 1),
                                   ).first()
        try:
            email = contact.value
        except AttributeError:
            # Nothing we can do!
            hr_id = form_vars.get("id")
            current.log.warning("Cannot create user for HR %s as cannot find Email" % hr_id)
            return

        hr_type = form_vars.get("type")
        if not hr_type:
            if not hr:
                hr_id = form_vars.get("id")
                if not hr_id:
                    # Nothing we can do!
                    current.log.warning("Cannot create user for HR as no id in the form")
                    return

                htable = s3db.hrm_human_resource
                hr = db(htable.id == hr_id).select(htable.id,
                                                   htable.type,
                                                   limitby = (0, 1),
                                                   ).first()
            try:
                hr_type = str(hr.type)
            except AttributeError:
                # Nothing we can do!
                current.log.warning("Cannot create user for HR %s as cannot find HR record" % hr_id)
                return

        if hr_type == "1":
            link_user_to = "staff"
        else:
            link_user_to = "volunteer"

        # This field has been manually added to the form
        language = current.request.post_vars.get("language")

        auth = current.auth

        # Generate a password
        password, crypted = auth.s3_password(8)

        # Create User
        user = Storage(organisation_id = organisation_id,
                       language = language,
                       first_name = person.first_name,
                       last_name = person.middle_name, # NB We use middle_name for User in RMS Americas!
                       email = email,
                       link_user_to = link_user_to,
                       password = str(crypted),
                       )

        #user = auth.get_or_create_user(user, login=False)
        user_id = db.auth_user.insert(**user)

        # Set the HR record to be owned by this user
        if hr:
            hr.update_record(owned_by_user = user_id)
        else:
            hr_id = form_vars.get("id")
            db(s3db.hrm_human_resource.id == hr_id).update(owned_by_user = user_id)

        # Set the Person record to be owned by this user
        person.update_record(owned_by_user = user_id)

        # Cascade down to components
        # pr_address
        atable = s3db.pr_address
        db(atable.pe_id == pe_id).update(owned_by_user = user_id)
        # pr_contact
        db(ctable.pe_id == pe_id).update(owned_by_user = user_id)

        # Link to Person so that we find this in the 'Link'
        ltable = s3db.pr_person_user
        ltable.insert(pe_id = pe_id,
                      user_id = user_id,
                      )

        # Approve User, link to Person & send them a Welcome email
        user.update(id = user_id)
        messages = auth.messages
        messages.lock_keys = False
        messages.welcome_email = \
"""Welcome to %(system_name)s
 - You can start using %(system_name)s at: %(url)s
 - Your password is: %(password)s
 - To edit your profile go to: %(url)s%(profile)s
Thank you"""
        messages.lock_keys = True
        auth.s3_approve_user(user, password=password)

    # -------------------------------------------------------------------------
    def hrm_human_resource_onvalidation(form):
        """
            Check that the Organization ID is unique per NS
        """

        # Read Code
        form_vars_get = form.vars.get
        code = form_vars_get("code")

        if code is None:
            return

        db = current.db
        s3db = current.s3db

        # Lookup Root Org
        organisation_id = form_vars_get("organisation_id")
        otable = s3db.org_organisation
        root_org = db(otable.id == organisation_id).select(otable.root_organisation,
                                                           limitby = (0, 1),
                                                           ).first()
        root_organisation = root_org.root_organisation

        # Check for another HR in the same NS with same code
        htable = s3db.hrm_human_resource
        query = (htable.code == code) & \
                (htable.organisation_id == otable.id) & \
                (otable.root_organisation == root_organisation)
        human_resource_id = form_vars_get("id")
        if human_resource_id:
            # Update Form: Skip our own record
            query &= (htable.id != human_resource_id)
        match = db(query).select(htable.id,
                                 limitby = (0, 1),
                                 ).first()
        if match:
            # Error
            form.errors["code"] = current.T("Organization ID already in use")

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        # Organization ID needs to be unique per NS
        current.s3db.configure(tablename,
                               onvalidation = hrm_human_resource_onvalidation,
                               )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        #controller = current.request.controller
        #if controller != "deploy":
        #    # Default Filter
        #    from s3 import s3_set_default_filter
        #    s3_set_default_filter("~.organisation_id",
        #                          user_org_and_children_default_filter,
        #                          tablename = "hrm_human_resource")

        s3 = current.response.s3
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        if current.request.function == "trainee":
            EXTERNAL = True
        else:
            EXTERNAL = False

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            from s3 import FS

            db = current.db
            s3db = current.s3db
            auth = current.auth
            resource = r.resource
            table = r.table

            has_role = auth.s3_has_role
            has_roles = auth.s3_has_roles

            if EXTERNAL:
                f = table.organisation_id
                f.label = T("Organization")

                # Organisation cannot be an NS/Branch
                # Lookup organisation_type_id for Red Cross
                ttable = s3db.org_organisation_type
                type_ids = db(ttable.name.belongs((RED_CROSS, "Training Center"))).select(ttable.id,
                                                                                          cache = s3db.cache,
                                                                                          limitby = (0, 2),
                                                                                          )
                if type_ids:
                    from s3 import IS_ONE_OF
                    ltable = db.org_organisation_organisation_type
                    type_ids = [t.id for t in type_ids]
                    rows = db(ltable.organisation_type_id.belongs(type_ids)).select(ltable.organisation_id)
                    not_filter_opts = [row.organisation_id for row in rows]
                    f.requires = IS_ONE_OF(db, "org_organisation.id",
                                           f.represent,
                                           not_filterby = "id",
                                           not_filter_opts = not_filter_opts,
                                           updateable = True,
                                           orderby = "org_organisation.name",
                                           sort = True,
                                           )

                    resource.add_filter(~FS("organisation_id").belongs(not_filter_opts))

                    # Find the relevant filter widget & limit it's options
                    filter_widgets = s3db.get_config("hrm_human_resource", "filter_widgets")
                    filter_widget = None
                    if filter_widgets:
                        from s3 import S3HierarchyFilter
                        for w in filter_widgets:
                            if isinstance(w, S3HierarchyFilter) and \
                               w.field == "organisation_id":
                                filter_widget = w
                                break
                    if filter_widget is not None:
                        filter_widget.opts["filter"] = (~FS("id").belongs(not_filter_opts))

            else:
                otable = s3db.org_organisation
                otable.root_organisation.label = T("National Society")

                # Organisation needs to be an NS/Branch
                ns_only("hrm_human_resource",
                        required = True,
                        branches = True,
                        # default
                        #limit_filter_opts = True,
                        )

                export_formats = list(settings.get_ui_export_formats())

                if r.method in ("create", "summary", None):
                    # Provide a default Organization ID
                    organisation_id = auth.user.organisation_id
                    if organisation_id:
                        org = db(otable.id == organisation_id).select(otable.root_organisation,
                                                                      limitby = (0, 1),
                                                                      ).first()
                        root_organisation_id = org.root_organisation
                        f = table.code
                        query = (otable.root_organisation == root_organisation_id) & \
                                (otable.id == table.organisation_id)
                        last_code = db(query).select(f,
                                                     limitby = (0, 1),
                                                     orderby = ~f,
                                                     ).first()
                        last_code = last_code.code
                        if last_code:
                            f.default = int(last_code) + 1
                        else:
                            f.default = 1

                if not r.id:
                    # Filter to just RC people
                    resource.add_filter(FS("organisation_id$organisation_type.name") == RED_CROSS)

                    if has_role("RIT_ADMIN", include_admin=False):
                        # Create a User Account for the HR to manage their own profile
                        def add_language(form):
                            from gluon import LABEL, OPTION, SELECT
                            from s3 import s3_addrow
                            formstyle = settings.get_ui_formstyle()
                            language_opts = [OPTION(T("Spanish"),
                                                    _value = "es",
                                                    _selected = "selected",
                                                    ),
                                             OPTION(T("French"),
                                                    _value = "fr",
                                                    ),
                                             OPTION(T("English"),
                                                    _value = "en",
                                                    ),
                                             ]
                            s3_addrow(form,
                                      LABEL("%s:" % T("Language"),
                                            _id = "auth_user_language__label",
                                            _for = "auth_user_language",
                                            ),
                                      SELECT(_id = "auth_user_language",
                                             _name = "language",
                                             *language_opts
                                             ),
                                      "",
                                      formstyle,
                                      "auth_user_language__row",
                                      position = 3,
                                      )
                        resource.configure(create_onaccept = hrm_human_resource_create_onaccept,
                                           form_postp = add_language,
                                           )

                    # Custom list_fields
                    list_fields = [(T("Full Name"), "person_id"),
                                   "organisation_id",
                                   (T("Program"), "person_id$hours.programme_id"),
                                   (T("National ID"), "person_id$national_id.value"),
                                   "code",
                                   (T("Email"), "email.value"),
                                   (settings.get_ui_label_mobile_phone(), "phone.value"),
                                   ]
                    r.resource.configure(list_fields = list_fields)

                    # Bind method for signature list export + add export icon
                    from .siglist import HRSignatureList
                    s3db.set_method("hrm", "human_resource",
                                    method = "siglist",
                                    action = HRSignatureList,
                                    )
                    export_formats.append(("siglist.pdf", "fa fa-list", T("Export Signature List")))
                    s3.formats["siglist.pdf"] = r.url(method = "siglist")

                if has_roles(ID_CARD_EXPORT_ROLES):
                    if r.representation == "card":
                        # Configure ID card layout
                        from .idcards import IDCardLayout
                        resource.configure(pdf_card_layout = IDCardLayout)

                    if not r.id and not r.component:
                        # Add export-icon for ID cards
                        export_formats.append(("card", "fa fa-id-card", T("Export ID Cards")))
                        s3.formats["card"] = r.url(method = "")

                settings.ui.export_formats = export_formats


            if not has_role("ADMIN") and \
                   has_roles(("training_coordinator", "training_assistant")):
                # Filter People to just those trained by this Reference Center
                resource.add_filter(FS("training.training_event_id$organisation_id") == auth.user.organisation_id)

            # Default to Volunteers
            table.type.default = 2

            # Hide Venues from the list of Offices
            from gluon import IS_EMPTY_OR

            ttable = s3db.org_facility_type
            ltable = s3db.org_site_facility_type
            query = (ltable.facility_type_id == ttable.id) & \
                    (ttable.name == "Venue")
            venues = db(query).select(ltable.site_id)
            venues = [v.site_id for v in venues]
            stable = s3db.org_site
            dbset = db(~stable.site_id.belongs(venues))

            f = table.site_id
            new_requires = f.requires.other
            new_requires.dbset = dbset
            f.requires = IS_EMPTY_OR(new_requires)

            table = s3db.pr_person
            table.first_name.label = T("Forenames")
            table.middle_name.label = T("Father's Surname")
            table.last_name.label = T("Mother's Surname")

            # For the filter
            s3db.hrm_competency.skill_id.label = T("Language")

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_insurance_resource(r, tablename):

        table = current.s3db.hrm_insurance

        table.type.default = "HEALTH"
        table.insurance_number.label = T("Affiliate Number")
        table.phone.label = T("Emergency Number")
        table.insurer.label = "%s / %s" % (T("Insurance Company"),
                                           T("Social Work or Prepaid"),
                                           )

    settings.customise_hrm_insurance_resource = customise_hrm_insurance_resource

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_resource(r, tablename):

        s3db = current.s3db

        f = s3db.hrm_job_title.type
        f.default = 3 # Both
        #f.readable  = f.writable = False

        label = T("Position")
        label_create = T("Create Position")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Position Details"),
            title_list = T("Position Catalog"),
            title_update = T("Edit Position"),
            title_upload = T("Import Positions"),
            label_list_button = T("List Positions"),
            label_delete_button = T("Delete Position"),
            msg_record_created = T("Position added"),
            msg_record_modified = T("Position updated"),
            msg_record_deleted = T("Position deleted"),
            msg_list_empty = T("Currently no entries in the catalog"),
            )

        from s3layouts import S3PopupLink
        f = s3db.hrm_job_title_id.attr
        f.label = label
        f.comment = S3PopupLink(c = "hrm",
                                f = "job_title",
                                label = label_create,
                                title = label,
                                )

    settings.customise_hrm_job_title_resource = customise_hrm_job_title_resource

    # -------------------------------------------------------------------------
    def customise_hrm_job_title_controller(**attr):

        s3 = current.response.s3

        # Organisation needs to be an NS
        ns_only("hrm_job_title",
                required = False,
                branches = False,
                )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if current.auth.s3_has_role("ADMIN"):
                from s3 import S3OptionsFilter, S3TextFilter
                filter_widgets = [S3TextFilter(["name",
                                                ],
                                               label=T("Search")
                                               ),
                                  S3OptionsFilter("organisation_id",
                                                  ),
                                  ]
                current.s3db.configure("hrm_job_title",
                                       filter_widgets = filter_widgets,
                                       )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_job_title_controller = customise_hrm_job_title_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_controller(**attr):

        table = current.s3db.hrm_programme

        # Organisation needs to be an NS/Branch
        ns_only("hrm_programme",
                required = False,
                branches = False,
                )

        # non-Admins should only see programmes for their NS
        auth = current.auth
        if not auth.s3_has_role("ADMIN"):
            current.response.s3.filter = (table.organisation_id == auth.root_org())

        f = table.name_long
        f.readable = f.writable = False

        return attr

    settings.customise_hrm_programme_controller = customise_hrm_programme_controller

    # -------------------------------------------------------------------------
    def customise_hrm_programme_hours_controller(**attr):

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.person_id$human_resource.organisation_id",
                              user_org_default_filter,
                              tablename = "hrm_programme_hours")

        attr["csv_template"] = ("../../themes/RMS/formats", "hrm_programme_hours")
        return attr

    settings.customise_hrm_programme_hours_controller = customise_hrm_programme_hours_controller

    # -------------------------------------------------------------------------
    def skip_create(deduplicate):
        """ Decorator for deduplicators to prevent creation of new records """
        def wrapped(item):
            if callable(deduplicate):
                deduplicate(item)
            item.strategy = [item.METHOD.UPDATE]
        return wrapped

    def customise_hrm_programme_hours_resource(r, tablename):

        from s3 import S3SQLCustomForm

        s3db = current.s3db
        phtable = s3db.hrm_programme_hours

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Hours of Service"),
            title_display = T("Hours Details"),
            title_list = T("Hours of Service"),
            title_update = T("Edit Hours"),
            label_list_button = T("List Hours"),
            label_delete_button = T("Delete Hours"),
            msg_record_created = T("Hours added"),
            msg_record_modified = T("Hours updated"),
            msg_record_deleted = T("Hours deleted"),
            msg_list_empty = T("Currently no hours recorded"),
            )

        # Show new custom fields
        phtable.event.readable = phtable.event.writable = True
        phtable.place.readable = phtable.place.writable = True
        # Hide old fields so they don't appear in list_fields in hrm_Record
        #phtable.programme_id.readable = phtable.programme_id.writable = False
        phtable.job_title_id.readable = phtable.job_title_id.writable = False

        crud_form = S3SQLCustomForm("date",
                                    "programme_id",
                                    "place",
                                    "event",
                                    "hours",
                                    )

        # Only visible in hrm_Record which controls list_fields itself
        #list_fields = ["date",
        #               "programme_id",
        #               "place",
        #               "event",
        #               "training_id$training_event_id$location_id",
        #               "training_id$training_event_id$course_id",
        #               "hours",
        #               ]

        configure = s3db.configure
        configure("hrm_programme_hours",
                  crud_form = crud_form,
                  #list_fields = list_fields,
                  )

        # Prevent create during imports
        get_config = s3db.get_config
        configure("pr_person",
                  deduplicate = skip_create(get_config("pr_person", "deduplicate")),
                  )
        configure("org_organisation",
                  deduplicate = skip_create(get_config("org_organisation", "deduplicate")),
                  )
        configure("hrm_programme",
                  deduplicate = skip_create(get_config("hrm_programme", "deduplicate")),
                  )

    settings.customise_hrm_programme_hours_resource = customise_hrm_programme_hours_resource

    # -------------------------------------------------------------------------
    def customise_hrm_skill_resource(r, tablename):

        #label = T("Language")
        label_create = T("Create Language")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = label_create,
            title_display = T("Language Details"),
            title_list = T("Language Catalog"),
            title_update = T("Edit Language"),
            label_list_button = T("List Languages"),
            label_delete_button = T("Delete Language"),
            msg_record_created = T("Language added"),
            msg_record_modified = T("Language updated"),
            msg_record_deleted = T("Language deleted"),
            msg_list_empty = T("Currently no entries in the catalog"),
            )

        # No use since cannot be sure this runs before hrm_competency table is loaded
        #from s3layouts import S3PopupLink
        #f = current.s3db.hrm_skill_id.attr
        #f.label = label
        #f.comment = S3PopupLink(c = "hrm",
        #                        f = "skill",
        #                        label = label_create,
        #                        title = label,
        #                        )

    settings.customise_hrm_skill_resource = customise_hrm_skill_resource

    # -------------------------------------------------------------------------
    def customise_hrm_competency_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Language"),
            title_display = T("Language Details"),
            title_list = T("Languages"),
            title_update = T("Edit Language"),
            label_list_button = T("List Languages"),
            label_delete_button = T("Delete Language"),
            msg_record_created = T("Language added"),
            msg_record_modified = T("Language updated"),
            msg_record_deleted = T("Language deleted"),
            msg_list_empty = T("No entries currently registered"),
            )

        label = T("Language")
        from s3layouts import S3PopupLink
        f = current.s3db.hrm_competency.skill_id
        f.label = label
        f.comment = S3PopupLink(c = "hrm",
                                f = "skill",
                                label = T("Create Language"),
                                title = label,
                                )

    settings.customise_hrm_competency_resource = customise_hrm_competency_resource

    # -------------------------------------------------------------------------
    def hrm_training_onaccept(form):
        """
            Add People to the RIT Alert List if they have passed the RIT course
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars

        # Lookup full record
        table = db.hrm_training
        record = db(table.id == form_vars.id).select(table.id,
                                                     table.person_id,
                                                     table.course_id,
                                                     table.grade,
                                                     limitby = (0, 1),
                                                     ).first()
        try:
            course_id = record.course_id
        except AttributeError:
            current.log.error("Cannot find Training record")
            return

        # Lookup the RIT Course ID
        ctable = db.hrm_course
        row = db(ctable.name == "Regional Intervention Teams").select(ctable.id,
                                                                      cache = s3db.cache,
                                                                      limitby = (0, 1),
                                                                      ).first()
        try:
            rit_course_id = row.id
        except AttributeError:
            current.log.error("Cannot find RIT Course: Prepop not done?")
            return

        if course_id != rit_course_id:
            # Nothing to do
            return

        if record.grade != 8:
            # Not passed: Nothing to do
            return

        # Is person already a RIT Member?
        person_id = record.person_id
        htable = s3db.hrm_human_resource
        hr = db(htable.person_id == person_id).select(htable.id,
                                                      limitby = (0, 1),
                                                      ).first()
        try:
            human_resource_id = hr.id
        except AttributeError:
            current.log.error("Cannot find Human Resource record")
            return

        dtable = s3db.deploy_application
        exists = db(dtable.human_resource_id == human_resource_id).select(dtable.id,
                                                                          limitby = (0, 1),
                                                                          ).first()
        if not exists:
            # Add them to the list
            dtable.insert(human_resource_id = human_resource_id)

        # Add them to the RIT role
        ltable = s3db.pr_person_user
        ptable = db.pr_person
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id)
        link = db(query).select(ltable.user_id,
                                limitby = (0, 1),
                                ).first()
        if link:
            current.auth.s3_assign_role(link.user_id, "RIT_MEMBER")

    # -------------------------------------------------------------------------
    def hrm_training_onimport(import_info):
        """
            Create Users for Persons created
        """

        training_ids = import_info["created"]
        if not training_ids:
            # No new people created
            return

        db = current.db
        s3db = current.s3db

        # Find all the Persons
        ttable = s3db.hrm_training
        ptable = s3db.pr_person
        query = (ttable.id.belongs(training_ids)) & \
                (ttable.person_id == ptable.id)
        trainings = db(query).select(ptable.pe_id)
        person_pe_ids = {p.pe_id for p in trainings}

        if not person_pe_ids:
            # No people?
            return

        # Remove those with a User Account
        ltable = s3db.pr_person_user
        users = db(ltable.pe_id.belongs(person_pe_ids)).select(ltable.pe_id)
        user_pe_ids = [u.pe_id for u in users]
        discard = person_pe_ids.discard
        for pe_id in user_pe_ids:
            discard(pe_id)

        if not person_pe_ids:
            # Nobody without a User Account already
            return

        # Read Person Details
        ctable = s3db.pr_contact
        dtable = s3db.pr_person_details
        htable = s3db.hrm_human_resource
        left = [ctable.on((ctable.pe_id == ptable.pe_id) & \
                          (ctable.contact_method == "EMAIL")
                          ),
                dtable.on(dtable.person_id == ptable.id),
                htable.on(htable.person_id == ptable.id),
                ]
        persons = db(ptable.pe_id.belongs(person_pe_ids)).select(ptable.id,
                                                                 ptable.first_name,
                                                                 # Americas use Apellido Paterno for Last Name
                                                                 ptable.middle_name,
                                                                 #ptable.last_name,
                                                                 ctable.value,
                                                                 dtable.language,
                                                                 htable.type,
                                                                 htable.organisation_id,
                                                                 left = left,
                                                                 )
        auth = current.auth
        utable = db.auth_user
        create_user = utable.insert
        approve_user = auth.s3_approve_user
        cert_table = s3db.hrm_certification
        # For each Person
        for p in persons:
            person = p["pr_person"]
            hr = p["hrm_human_resource"]

            if hr.type == 1:
                link_user_to = "staff"
            else:
                link_user_to = "volunteer"

            # Set random password
            password, crypted = auth.s3_password(8)

            # Create a User Account
            user = Storage(first_name = person.first_name,
                           last_name = person.middle_name,
                           #last_name = person.last_name,
                           email = p["pr_contact.value"],
                           language = p["pr_person_details.language"],
                           password = crypted,
                           organisation_id = hr.organisation_id,
                           link_user_to = link_user_to,
                           )
            user_id = create_user(**user)

            # Standard Approval (inc Link to Person/HR and Send out Welcome Email with password)
            user["id"] = user_id
            approve_user(user, password)

            # Fixup permissions
            person_id = person.id
            db(htable.person_id == person_id).update(owned_by_user = user_id)
            db(ttable.person_id == person_id).update(owned_by_user = user_id)
            db(cert_table.person_id == person_id).update(owned_by_user = user_id)

    # -------------------------------------------------------------------------
    def customise_hrm_training_controller(**attr):

        s3 = current.response.s3

        # Default Filter
        #from s3 import s3_set_default_filter
        #s3_set_default_filter("~.person_id$human_resource.organisation_id",
        #                      user_org_default_filter,
        #                      tablename = "hrm_training")

        auth = current.auth
        if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("training_coordinator", "training_assistant")):
            TC = True
            # Filter Trainings to just those done by this Reference Center
            from s3 import FS
            query = FS("~.training_event_id$organisation_id") == auth.user.organisation_id
            s3.filter = query
        else:
            TC = False

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if r.method == "import":
                # HR records may be created via importing them as participants
                s3db = current.s3db
                # Default to Volunteers
                s3db.hrm_human_resource.type.default = 2
                if TC:
                    # Doesn't work as email created after human_resource
                    #s3db.configure("hrm_human_resource",
                    #               create_onaccept = hrm_human_resource_create_onaccept,
                    #               )
                    # Create User Accounts for those Persons without them
                    s3db.configure("hrm_training",
                                   onimport = hrm_training_onimport,
                                   )

            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_training_controller = customise_hrm_training_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_resource(r, tablename):

        s3db = current.s3db
        table = s3db.hrm_training
        f = table.grade
        f.readable = f.writable = True
        f = table.qualitative_feedback
        f.readable = f.writable = True

        s3db.hrm_certification.number.label = T("Registration Number")

        from s3 import S3SQLCustomForm, S3TextFilter, S3OptionsFilter, S3DateFilter

        if r.function == "person":
            crud_form = S3SQLCustomForm("course_id",
                                        "end_date",
                                        "grade",
                                        "grade_details",
                                        "qualitative_feedback",
                                        "certification_from_training.number",
                                        )
        else:
            crud_form = S3SQLCustomForm("person_id",
                                        "end_date",
                                        "grade",
                                        "grade_details",
                                        "qualitative_feedback",
                                        "certification_from_training.number",
                                        )

        from s3db.org import org_SiteRepresent
        filter_widgets = [
            S3TextFilter(["person_id$first_name",
                          "person_id$last_name",
                          "course_id$name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("You can search by trainee name, course name or comments. You may use % as wildcard. Press 'Search' without input to list all trainees."),
                         _class = "filter-search",
                         ),
            S3OptionsFilter("training_event_id$site_id",
                            label = T("Country"),
                            represent = org_SiteRepresent(show_type = False),
                            ),
            S3OptionsFilter("person_id$human_resource.organisation_id",
                            label = T("Organization"),
                            ),
            S3OptionsFilter("course_id",
                            ),
            S3OptionsFilter("grade",
                            ),
            S3DateFilter("date",
                         hide_time=True,
                         ),
            ]

        s3db.add_custom_callback(tablename,
                                 "onaccept",
                                 hrm_training_onaccept,
                                 )

        s3db.configure(tablename,
                      crud_form = crud_form,
                      filter_widgets = filter_widgets,
                      )

    settings.customise_hrm_training_resource = customise_hrm_training_resource

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineComponent
        from s3db.org import org_OrganisationRepresent

        db = current.db
        auth = current.auth
        s3db = current.s3db
        table = s3db.hrm_training_event

        org_represent = org_OrganisationRepresent(parent = False)

        f = table.organisation_id
        f.label = T("Training Center")
        f.comment = False # Don't create here
        f.represent = org_represent

        list_fields = ["organisation_id",
                       "course_id",
                       #"site_id",
                       "location_id",
                       "start_date",
                       "training_event_instructor.person_id",
                       "comments",
                       ]

        if auth.s3_has_role("ADMIN"):
            #f.readable = f.writable = True
            ttable = s3db.org_organisation_type
            try:
                type_id = db(ttable.name == "Training Center").select(ttable.id,
                                                                      limitby = (0, 1),
                                                                      ).first().id
            except AttributeError:
                # No/incorrect prepop done - skip (e.g. testing impacts of CSS changes in this theme)
                pass
            else:
                ltable = s3db.org_organisation_organisation_type
                rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
                filter_opts = [row.organisation_id for row in rows]

                f.requires = IS_ONE_OF(db, "org_organisation.id",
                                       org_represent,
                                       orderby = "org_organisation.name",
                                       sort = True,
                                       filterby = "id",
                                       filter_opts = filter_opts,
                                       )

        elif auth.s3_has_roles(("training_coordinator", "training_assistant")):
            organisation_id = auth.user.organisation_id
            f.default = organisation_id
            f.writable = False
            list_fields.pop(0) # organisation_id
            table.course_id.requires.set_filter(filterby = "organisation_id",
                                                filter_opts = [organisation_id],
                                                )

        # Hours are Optional
        from gluon import IS_EMPTY_OR
        table.hours.requires = IS_EMPTY_OR(table.hours)

        #site_represent = S3Represent(lookup = "org_site")

        # Filter list of Venues
        #f = table.site_id
        #f.default = None
        #f.label = T("Country")
        #f.represent = site_represent

        #ftable = s3db.org_facility
        #ltable = s3db.org_site_facility_type
        #ttable = s3db.org_facility_type
        #query = (ftable.deleted == False) & \
        #        (ftable.site_id == ltable.site_id) & \
        #        (ltable.facility_type_id == ttable.id) & \
        #        (ttable.name == "Venue")
        #rows = db(query).select(ftable.site_id)
        #filter_opts = [row.site_id for row in rows]
        #f.requires = IS_ONE_OF(db, "org_site.site_id",
        #                       site_represent,
        #                       filterby = "site_id",
        #                       filter_opts = filter_opts,
        #                       )

        # Multiple Instructors
        crud_form = S3SQLCustomForm("organisation_id",
                                    # @ToDo: Filter Courses by Training Center
                                    "course_id",
                                    #"site_id",
                                    "location_id",
                                    "start_date",
                                    "end_date",
                                    S3SQLInlineComponent("training_event_instructor",
                                                         label = T("Instructor"),
                                                         fields = [("", "person_id")],
                                                         # @ToDo: Filter to HRMs (this should be done through AC?)
                                                         #filterby = ({"field": "type",
                                                         #             "options": 3,
                                                         #             },),
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -------------------------------------------------------------------------
    def hrm_training_event_report_pdf_export(r, **attr):
        """
            Generate a PDF Export of a training Event Report
        """

        from s3 import s3_fullname, s3_str

        record = r.record

        T = current.T
        db = current.db
        s3db = current.s3db

        current_language = T.accepted_language
        if current_language == "es":
            # Reach different translation
            title = s3_str(T("Training Event Report"))
        else:
            title = s3_str(T("Training Report"))

        if record.course_id:
            course_name = s3db.hrm_training_event.course_id.represent(record.course_id)
            title = "%s: %s" % (title, course_name)

        def callback(r):

            from gluon.html import DIV, TABLE, TD, TH, TR
            from s3db.org import org_OrganisationRepresent, \
                                 org_organisation_logo

            rtable = s3db.hrm_training_event_report

            date_represent = rtable.date.represent
            org_represent = org_OrganisationRepresent(parent = False,
                                                      acronym = False,
                                                      )

            # Logo
            logo = org_organisation_logo(record.organisation_id)

            # Read the report
            report = db(rtable.training_event_id == r.id).select(rtable.person_id,
                                                                 rtable.job_title_id,
                                                                 rtable.organisation_id,
                                                                 rtable.date,
                                                                 rtable.purpose,
                                                                 rtable.objectives,
                                                                 rtable.methodology,
                                                                 rtable.actions,
                                                                 rtable.participants,
                                                                 rtable.results,
                                                                 rtable.followup,
                                                                 rtable.additional,
                                                                 rtable.comments,
                                                                 limitby = (0, 1),
                                                                 ).first()

            # Header
            header = TABLE(TR(TH("%s:" % T("Name")),
                              TD(s3_fullname(report.person_id)),
                              TH("%s:" % T("Training Date")),
                              TD(date_represent(record.start_date)),
                              ),
                           TR(TH("%s:" % T("Position")),
                              TD(rtable.job_title_id.represent(report.job_title_id)),
                              TH("%s:" % T("Finance Codes")),
                              TD(report.code),
                              ),
                           TR(TH("%s:" % T("National Society Visited")),
                              TD(org_represent(report.organisation_id)),
                              TH("%s:" % T("Report Date")),
                              TD(date_represent(report.date)),
                              ),
                           TR(TH("%s:" % T("Training Purpose")),
                              TD(report.purpose,
                                 _colspan = 3,
                                 ),
                              ),
                           )

            # Main
            main = TABLE(TR(TH("1. %s" % T("Objectives"))),
                         TR(TD(report.objectives)),
                         TR(TH("2. %s" % T("Methodology"))),
                         TR(TD(report.methodology)),
                         TR(TH("3. %s" % T("Implemented Actions"))),
                         TR(TD(report.actions)),
                         TR(TH("4. %s" % T("About the participants"))),
                         TR(TD(report.participants)),
                         TR(TH("5. %s" % T("Results and Lessons Learned"))),
                         TR(TD(report.results)),
                         TR(TH("6. %s" % T("Follow-up Required"))),
                         TR(TD(report.followup)),
                         TR(TH("7. %s" % T("Additional relevant information"))),
                         TR(TD(report.additional)),
                         TR(TH("8. %s" % T("General Comments"))),
                         TR(TD(report.comments)),
                         )

            output = DIV(TABLE(TR(TD(logo),
                                  #TD(org_name), # This isn't rtl-proof, check vol_service_record for how to handle that if-required
                                  )),
                         TABLE(TR(TD(title))),
                         TABLE(header),
                         TABLE(main),
                         )

            return output

        attr["rheader"] = None

        from s3.s3export import S3Exporter

        exporter = S3Exporter().pdf
        pdf_title = title
        return exporter(r.resource,
                        request = r,
                        method = "list",
                        pdf_title = pdf_title,
                        pdf_table_autogrow = "B",
                        pdf_callback = callback,
                        **attr
                        )

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_controller(**attr):

        T = current.T
        auth = current.auth
        s3db = current.s3db
        s3 = current.response.s3

        if not auth.s3_has_role("ADMIN") and \
               auth.s3_has_roles(("training_coordinator", "training_assistant")):
            # Filter People to just those trained by this Reference Center
            from s3 import FS
            query = FS("~.organisation_id") == auth.user.organisation_id
            s3.filter = query

        s3db.set_method("hrm", "training_event",
                        method = "report_pdf_export",
                        action = hrm_training_event_report_pdf_export,
                        )

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "training_event_report" and r.component_id:
                from gluon.html import A, DIV#, URL
                from s3 import ICON
                s3.rfooter = DIV(A(ICON("print"),
                                 " ",
                                 T("PDF Report"),
                                   _href = URL(args = [r.id, "report_pdf_export"]),#, extension="pdf"),
                                   _class = "action-btn",
                                   ),
                                 )

            return result
        s3.prep = custom_prep

        from s3db.hrm import hrm_rheader
        attr["rheader"] = lambda r: \
            hrm_rheader(r, tabs=[(T("Training Event Details"), None),
                                 (T("Participants"), "participant"),
                                 (T("Report"), "training_event_report"),
                                 ])
        return attr

    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_report_resource(r, tablename):

        s3db = current.s3db
        table = s3db.hrm_training_event_report
        table.person_id.default = current.auth.s3_logged_in_person()
        table.person_id.label = T("Name")
        ns_only("hrm_training_event_report",
                required = False,
                branches = False,
                updateable = False,
                )
        table.organisation_id.label = T("National Society Visited")
        table.code.label = T("Finance Codes")

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("person_id",
                                    "job_title_id",
                                    "organisation_id",
                                    "purpose",
                                    "code",
                                    "date",
                                    (("1. %s" % table.objectives.label), "objectives"),
                                    (("2. %s" % table.methodology.label), "methodology"),
                                    (("3. %s" % table.actions.label), "actions"),
                                    (("4. %s" % table.participants.label), "participants"),
                                    (("5. %s" % table.results.label), "results"),
                                    (("6. %s" % table.followup.label), "followup"),
                                    (("7. %s" % table.additional.label), "additional"),
                                    (("8. %s" % table.comments.label), "comments"),
                                    S3SQLInlineComponent("document",
                                                         label = "9. %s" % T("Supporting Documentation"),
                                                         link = False,
                                                         fields = ["file"],
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_hrm_training_event_report_resource = customise_hrm_training_event_report_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_resource(r, tablename):

        from s3layouts import S3PopupLink

        ADD_MEMBERSHIP_TYPE = T("Create Partner Type")

        s3db = current.s3db
        table = s3db.member_membership
        table.code.label = T("Partner ID")
        table.membership_type_id.comment = S3PopupLink(f = "membership_type",
                                                       label = ADD_MEMBERSHIP_TYPE,
                                                       title = ADD_MEMBERSHIP_TYPE,
                                                       tooltip = T("Add a new partner type to the catalog."),
                                                       )
        list_fields = [(T("Full Name"), "person_id"),
                       "organisation_id",
                       "membership_type_id",
                       "code",
                       (T("National ID"), "person_id$national_id.value"),
                       (T("Email"), "email.value"),
                       (T("Mobile Phone"), "phone.value"),
                       "membership_fee",
                       (T("Paid"), "paid"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Partner"),
            title_display = T("Partner Details"),
            title_list = T("Partners"),
            title_update = T("Edit Partner Details"),
            title_upload = T("Import Partners"),
            label_list_button = T("List Partners"),
            label_delete_button = T("Delete Partner"),
            msg_record_created = T("Partner added"),
            msg_record_modified = T("Partner updated"),
            msg_record_deleted = T("Partner deleted"),
            msg_list_empty = T("No Partners currently defined"),
            )

    settings.customise_member_membership_resource = customise_member_membership_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_controller(**attr):

        ns_only("member_membership",
                required = True,
                branches = True,
                updateable = True,
                )

        return attr

    settings.customise_member_membership_controller = customise_member_membership_controller

    # -------------------------------------------------------------------------
    def customise_member_membership_type_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Partner Type"),
            title_display = T("Partner Type Details"),
            title_list = T("Partner Types"),
            title_update = T("Edit Partner Type Details"),
            title_upload = T("Import Partner Types"),
            label_list_button = T("List Partner Types"),
            label_delete_button = T("Delete Partner Type"),
            msg_record_created = T("Partner Type added"),
            msg_record_modified = T("Partner Type updated"),
            msg_record_deleted = T("Partner Type deleted"),
            msg_list_empty = T("No Partner Types currently defined"),
            )

    settings.customise_member_membership_type_resource = customise_member_membership_type_resource

    # -------------------------------------------------------------------------
    def customise_member_membership_type_controller(**attr):

        ns_only("member_membership_type",
                required = False,
                branches = False,
                updateable = True,
                )

        return attr

    settings.customise_member_membership_type_controller = customise_member_membership_type_controller

    # -------------------------------------------------------------------------
    #def on_inv_adj_close():
    #    """
    #        Nothing needed here currently
    #    """

    #    return

    # -------------------------------------------------------------------------
    #def customise_inv_adj_resource(r, tablename):

    #    current.s3db.configure(tablename,
    #                           on_inv_adj_close = on_inv_adj_close,
    #                           )

    #settings.customise_inv_adj_resource = customise_inv_adj_resource

    # -------------------------------------------------------------------------
    def customise_inv_kitting_resource(r, tablename):

        s3db = current.s3db

        def inv_kitting_onaccept(form):
            # Trigger Stock Limit Alert creation/cancellation
            site_id = int(form.vars.site_id)
            wtable = s3db.inv_warehouse
            warehouse = current.db(wtable.site_id == site_id).select(wtable.id,
                                                                     wtable.name,
                                                                     limitby = (0, 1),
                                                                     ).first()
            warehouse.site_id = site_id
            stock_limit_alerts(warehouse)

        s3db.add_custom_callback(tablename,
                                 "onaccept",
                                 inv_kitting_onaccept,
                                 )

    settings.customise_inv_kitting_resource = customise_inv_kitting_resource

    # -------------------------------------------------------------------------
    def inv_pdf_header(r, title=None):
        """
            PDF header for Stock Reports

            Args:
                r: the S3Request
                title: the report title
        """

        # Get organisation name and logo
        from .layouts import OM
        name, logo = OM().render()

        from gluon.html import DIV, H2, H4, P, TABLE, TR, TD

        # Report title and subtitle
        title = H2(title) if title else ""
        subtitle = ""

        get_vars = r.get_vars
        report = get_vars.get("report")
        if report == "movements":
            from s3 import S3TypeConverter, S3DateTime
            # Get earliest/latest date from filter
            convert = S3TypeConverter.convert
            dtstr = get_vars.get("_transaction.date__ge")
            earliest = convert(datetime.datetime, dtstr) if dtstr else ""
            dtstr = get_vars.get("_transaction.date__le")
            latest = convert(datetime.datetime, dtstr) if dtstr else ""
            # Convert into local calendar/format
            if earliest:
                earliest = S3DateTime.date_represent(earliest, utc=True)
            if latest:
                latest = S3DateTime.date_represent(latest, utc=True)
            # Add as subtitle
            if earliest or latest:
                subtitle = P(" - ".join((earliest, latest)))

        output = TABLE(TR(TD(DIV(logo,
                                 H4(name),
                                 ),
                             ),
                          TD(DIV(title,
                                 subtitle,
                                 ),
                             ),
                          ),
                       )

        return output

    # -------------------------------------------------------------------------
    def customise_inv_inv_item_resource(r, tablename):

        from s3db.inv import inv_item_total_weight, \
                             inv_item_total_volume, \
                             inv_stock_movements

        s3db = current.s3db

        # Add field methods for total weight and volume
        from gluon import Field
        table = s3db.inv_inv_item
        table.total_weight = Field.Method("total_weight",
                                          inv_item_total_weight,
                                          )
        table.total_volume = Field.Method("total_volume",
                                          inv_item_total_volume,
                                          )

        resource = r.resource
        if resource.tablename == "inv_inv_item" and r.method == "grouped":
            report = r.get_vars.get("report")
            if report == "movements":
                # Inject a date filter for transactions
                filter_widgets = resource.get_config("filter_widgets")
                from s3 import S3DateFilter
                date_filter = S3DateFilter("transaction_date",
                                           label = T("Date"),
                                           fieldtype = "date",
                                           selector = "_transaction.date",
                                           )
                filter_widgets.insert(1, date_filter)

        # Stock Reports
        stock_reports = {"default": {
                            "title": T("Stock Position Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin.layout_id",
                                       "item_id$name",
                                       "quantity",
                                       "pack_value",
                                       "total_value",
                                       ],
                            "groupby": ["site_id",
                                        #"supply_org_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "quantity"),
                                          ("sum", "total_value"),
                                          ],
                            "pdf_header": inv_pdf_header,
                            },
                         "weight_and_volume": {
                            "title": T("Weight and Volume Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin.layout_id",
                                       "item_id$name",
                                       "quantity",
                                       "item_id$weight",
                                       "item_id$volume",
                                       "total_weight",
                                       "total_volume",
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "quantity"),
                                          ("sum", "total_weight"),
                                          ("sum", "total_volume"),
                                          ],
                            "pdf_header": inv_pdf_header,
                            },
                         "movements": {
                            "title": T("Stock Movements Report"),
                            "fields": [(T("Warehouse"), "site_id$name"),
                                       "item_id$item_category_id",
                                       "bin.layout_id",
                                       "item_id$name",
                                       (T("Origin/Destination"), "sites"),
                                       (T("Documents"), "documents"),
                                       (T("Initial Quantity"), "original_quantity"),
                                       (T("Incoming"), "quantity_in"),
                                       (T("Outgoing"), "quantity_out"),
                                       (T("Final Quantity"), "quantity"),
                                       ],
                            "groupby": ["site_id",
                                        ],
                            "orderby": ["site_id$name",
                                        "item_id$name",
                                        ],
                            "aggregate": [("sum", "original_quantity"),
                                          ("sum", "quantity_in"),
                                          ("sum", "quantity_out"),
                                          ("sum", "quantity"),
                                          ],
                            "extract": inv_stock_movements,
                            "pdf_header": inv_pdf_header,
                            },
                         }

        list_fields = [(T("Description"), "item_id"),
                       (T("Reference"), "item_id$code"),
                       (T("Owner"), "owner_org_id"),
                       (T("Donor"), "supply_org_id"),
                       (T("Stock Location"), "site_id"),
                       (T("Physical Balance"), "quantity"),
                       (T("Unit Weight"), "item_id$weight"),
                       (T("Total Weight"), "total_weight"),
                       (T("Unit Volume"), "item_id$volume"),
                       (T("Total Volume"), "total_volume"),
                       (T("Unit Price"), "pack_value"),
                       (T("Total Price"), "total_value"),
                       (T("Comments"), "comments"),
                       ]

        filter_widgets = resource.get_config("filter_widgets")
        if filter_widgets is not None:
            from s3 import S3OptionsFilter
            filter_widgets.insert(2, S3OptionsFilter("item_id",
                                                     #label = T("Status"),
                                                     hidden = True,
                                                     ))

        report_options = s3db.get_config(tablename, "report_options")
        report_options["fact"] += [(T("Total Weight"), "total_weight"),
                                   (T("Total Volume"), "total_volume"),
                                   ]
        report_options["precision"] = {"total_value": 3,
                                       "total_weight": 3,
                                       "total_volume": 3,
                                       }

        s3db.configure("inv_inv_item",
                       grouped = stock_reports,
                       # Needed for Field.Methods
                       extra_fields = ["quantity",
                                       "pack_value",
                                       "item_id$weight",
                                       "item_id$volume",
                                       "item_pack_id$quantity",
                                       ],
                       list_fields = list_fields,
                       )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # -------------------------------------------------------------------------
    def customise_inv_inv_item_controller(**attr):

        ADMIN = current.auth.s3_has_role("ADMIN")
        if ADMIN:
            # ADMIN is allowed to Edit Inventory bypassing the need to use Adjustments
            # - seems wrong to me as Adjustments aren't that heavy, but has been requested
            settings.inv.direct_stock_edits = True

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            if not ADMIN and \
               r.method == "import":
                # Only ADMIN is allowed to Import Inventory
                return False

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_inv_inv_item_controller = customise_inv_inv_item_controller

    # -------------------------------------------------------------------------
    def on_inv_recv_process(row):
        """
            Update any inv_order_item records
        """

        db = current.db
        s3db = current.s3db

        recv_id = row.id

        # Lookup the PO for this receive
        rtable = s3db.inv_recv
        record = db(rtable.id == recv_id).select(rtable.purchase_ref,
                                                 limitby = (0, 1),
                                                 ).first()

        purchase_ref = record.purchase_ref
        if not purchase_ref:
            return

        # Lookup the REQs for this receive
        rrtable = s3db.inv_recv_req
        reqs = db(rrtable.recv_id == recv_id).select(rrtable.req_id)
        req_ids = [row.req_id for row in reqs]

        # Lookup the Order Items which match these REQs and PO
        otable = s3db.inv_order_item
        if len(req_ids) > 1:
            query = (otable.req_id.belongs(req_ids))
        else:
            query = (otable.req_id == req_ids[0])
        query &= (otable.purchase_ref == purchase_ref)
        orders = db(query).select(otable.id,
                                  otable.item_id,
                                  )
        if not orders:
            return

        # Lookup the Matching Items in the Shipment
        order_items = [row.item_id for row in orders]
        ttable = s3db.inv_track_item
        query = (ttable.recv_id == recv_id) & \
                (ttable.item_id.belongs(order_items))
        recv_items = db(query).select(ttable.item_id)
        if not recv_items:
            return
        recv_items = [row.item_id for row in recv_items]
        orders_to_update = []
        for row in orders:
            if row.item_id in recv_items:
                orders_to_update.append(row.id)

        if orders_to_update:
            if len(orders_to_update) > 1:
                query = (otable.id.belongs(orders_to_update))
            else:
                query = (otable.id == orders_to_update[0])
            db(query).update(recv_id = recv_id)

    # -------------------------------------------------------------------------
    def customise_inv_recv_resource(r, tablename):

        if not r.interactive and r.representation != "aadata":
            return

        db = current.db
        s3db = current.s3db
        table = s3db.inv_recv

        # Use Custom Represent for Sites to send to
        from .controllers import org_SiteRepresent
        table.from_site_id.requires.other.label = org_SiteRepresent()

        # Filter list of Orgs
        # - all root NS
        # - our Branches
        # - our Donors/Suppliers (& their branches, if-any)
        ttable = s3db.org_organisation_type
        try:
            type_id = db(ttable.name == RED_CROSS).select(ttable.id,
                                                          cache = s3db.cache,
                                                          limitby = (0, 1),
                                                          ).first().id
        except AttributeError:
            # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            pass
        else:
            root_org_id = current.auth.root_org()
            otable = s3db.org_organisation
            root_org = db(otable.id == root_org_id).select(otable.pe_id,
                                                           limitby = (0, 1),
                                                           ).first()
            ltable = db.org_organisation_organisation_type
            try:
                query = ((ltable.organisation_type_id == type_id) & (ltable.organisation_id == otable.id) & (otable.id == otable.root_organisation)) | \
                        (otable.root_organisation == root_org_id) | \
                        ((ltable.organisation_type_id != type_id) & (ltable.organisation_id == otable.id) & (otable.realm_entity == root_org.pe_id))
            except:
                # No root_org: we must be testing as Admin
                query = (ltable.organisation_type_id == type_id) & \
                        (ltable.organisation_id == otable.id) & \
                        (otable.id == otable.root_organisation)
            orgs = db(query).select(otable.id)
            org_ids = [row.id for row in orgs]
            table.organisation_id.requires.other.set_filter(filterby = "id",
                                                            filter_opts = org_ids,
                                                            )

        f = table.transport_type
        requires = f.requires
        if hasattr(requires, "other"):
            f.requires = requires.other

        from s3 import S3SQLCustomForm, S3SQLInlineLink#, IS_ONE_OF

        crud_form = S3SQLCustomForm(S3SQLInlineLink("req",
                                                    field = "req_id",
                                                    label = T("Request Number"),
                                                    # @ToDo: Filter appropriately
                                                    #requires = IS_ONE_OF()
                                                    ),
                                    "recv_ref",
                                    "site_id",
                                    "type",
                                    "organisation_id",
                                    "from_site_id",
                                    "eta",
                                    "date",
                                    "send_ref",
                                    "purchase_ref",
                                    "sender_id",
                                    "recipient_id",
                                    "transport_type",
                                    "transported_by",
                                    "transport_ref",
                                    "registration_no",
                                    "status",
                                    "grn_status",
                                    "cert_status",
                                    "filing_status",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = ["recv_ref",
                                      (T("Request Number"), "recv_req.req_id"),
                                      "send_ref",
                                      "purchase_ref",
                                      "recipient_id",
                                      "organisation_id",
                                      "from_site_id",
                                      "site_id",
                                      "date",
                                      "type",
                                      "status",
                                      ],
                       on_inv_recv_process = on_inv_recv_process,
                       )

        # Custom GRN
        from .forms import inv_recv_form
        s3db.set_method("inv", "recv",
                        method = "form",
                        action = inv_recv_form,
                        )

    settings.customise_inv_recv_resource = customise_inv_recv_resource

    # -------------------------------------------------------------------------
    def customise_inv_recv_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.get_vars.get("incoming"):
                s3.crud_strings.inv_recv.title_list = T("Incoming Shipments")
                # Filter to just Shipments able to be Received
                #    SHIP_STATUS_IN_PROCESS = 0
                #    SHIP_STATUS_SENT = 2
                from s3 import s3_set_default_filter
                s3_set_default_filter("~.status",
                                      [0, 2],
                                      tablename = "inv_recv")

            return result
        s3.prep = custom_prep

        return attr

    #settings.customise_inv_recv_controller = customise_inv_recv_controller

    # -------------------------------------------------------------------------
    def on_inv_send_process(record):
        """
            Remove req_fulfil Dashboard Alert if completed
        """

        from s3db.inv import REQ_STATUS_COMPLETE, \
                             REQ_STATUS_PARTIAL

        db = current.db
        s3db = current.s3db

        # Which Requests did we act on & what is their Status?
        srtable = s3db.inv_send_req
        rtable = s3db.inv_req
        query = (srtable.send_id == record.id) & \
                (srtable.req_id == rtable.id)
        reqs = db(query).select(rtable.id,
                                rtable.transit_status,
                                )
        req_ids_to_delete = []
        req_ids_to_check = []
        for row in reqs:
            transit_status = row.transit_status
            if transit_status == REQ_STATUS_COMPLETE:
                req_ids_to_delete.append(row.id)
            elif transit_status == REQ_STATUS_PARTIAL:
                req_ids_to_check.append(row.id)

        if req_ids_to_check:
            ritable = s3db.inv_req_item
            query = (ritable.req_id.belongs(req_ids_to_check)) & \
                    (ritable.site_id == record.site_id)
            req_items = db(query).select(ritable.req_id,
                                         ritable.quantity,
                                         ritable.quantity_transit,
                                         )
            reqs = {}
            for row in req_items:
                if row.quantity_transit >=  row.quantity:
                    item_complete = True
                else:
                    item_complete = False
                req_id = row.req_id
                if req_id in reqs:
                    if reqs[req_id]:
                        if not item_complete:
                            # Any single Incomplete Item makes the Request Incomplete
                            reqs[req_id] = False
                else:
                    reqs[req_id] = item_complete

            for req_id in reqs:
                if reqs[req_id]:
                    req_ids_to_delete.append(req_id)

        if req_ids_to_delete:
            auth = current.auth
            override_default = auth.override
            auth.override = True
            ntable = s3db.auth_user_notification
            query = (ntable.type == "req_fulfil") & \
                    (ntable.record_id.belongs(req_ids_to_delete))
            resource = s3db.resource("auth_user_notification", filter = query)
            resource.delete()
            auth.override = override_default

    # -------------------------------------------------------------------------
    def customise_inv_send_resource(r, tablename):

        #from gluon import IS_IN_SET

        s3db = current.s3db
        table = s3db.inv_send

        # Use Custom Represent for Sites to send to
        from .controllers import org_SiteRepresent
        table.to_site_id.requires.other.label = org_SiteRepresent()

        from s3 import S3SQLCustomForm, S3SQLInlineLink

        f = table.transport_type
        requires = f.requires
        if hasattr(requires, "other"):
            f.requires = requires.other

        from s3db.inv import inv_send_postprocess
        crud_form = S3SQLCustomForm(S3SQLInlineLink("req",
                                                    field = "req_id",
                                                    label = T("Request Number"),
                                                    ),
                                    "send_ref",
                                    "site_id",
                                    "type",
                                    "to_site_id",
                                    "organisation_id",
                                    "sender_id",
                                    "recipient_id",
                                    "transport_type",
                                    "transported_by",
                                    "transport_ref",
                                    "vehicle",
                                    "registration_no",
                                    #"driver_name",
                                    #"driver_phone",
                                    # Will only appear in Update forms:
                                    "date",
                                    "delivery_date", # Appears on Create form too
                                    "status",
                                    "filing_status",
                                    "comments",
                                    postprocess = inv_send_postprocess,
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       list_fields = ["send_ref",
                                      #"req_ref",
                                      (T("Request Number"), "send_req.req_id"),
                                      #"sender_id",
                                      "site_id",
                                      "date",
                                      "recipient_id",
                                      "delivery_date",
                                      "to_site_id",
                                      "status",
                                      #"driver_name",
                                      #"driver_phone",
                                      #"registration_no",
                                      #"time_out",
                                      #"comments",
                                      ],
                       on_inv_send_process = on_inv_send_process,
                       )

        # Custom Waybill
        from .forms import inv_send_form
        s3db.set_method("inv", "send",
                        method = "form",
                        action = inv_send_form,
                        )

    settings.customise_inv_send_resource = customise_inv_send_resource

    # -------------------------------------------------------------------------
    def customise_inv_send_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            #if r.get_vars.get("draft"):
            #    s3.crud_strings.inv_recv.title_list = T("Outbound Shipments")
            #    # Filter to just Shipments able to be Received
            #    #    SHIP_STATUS_IN_PROCESS = 0
            #    from s3 import s3_set_default_filter
            #    s3_set_default_filter("~.status",
            #                          [0],
            #                          tablename = "inv_send")

            return result
        s3.prep = custom_prep

        return attr

    #settings.customise_inv_send_controller = customise_inv_send_controller

    # -------------------------------------------------------------------------
    def stock_limit_alerts(warehouse):
        """
            Generate an Alert if Stock Level falls below Minimum
            Cancel Alerts if Stock Level is above Minimum
        """

        db = current.db
        s3db = current.s3db

        site_id = warehouse.site_id

        # Read Minimums
        mtable = s3db.inv_minimum
        query = (mtable.site_id == site_id) &\
                (mtable.deleted == False)

        minimums = db(query).select(mtable.id,
                                    mtable.item_id,
                                    mtable.quantity,
                                    )
        item_ids = [row.item_id for row in minimums]

        # Read current stock for each
        itable = s3db.inv_inv_item
        ptable = s3db.supply_item_pack
        query = (itable.site_id == site_id) &\
                (itable.item_id.belongs(item_ids)) &\
                (itable.item_pack_id == ptable.id) &\
                (itable.deleted == False)
        inventory = db(query).select(itable.item_id,
                                     itable.quantity,
                                     ptable.quantity,
                                     )

        ntable = s3db.auth_user_notification
        nquery = (ntable.tablename == "inv_minimum")

        alerts = []

        for row in minimums:
            # What is the Stock for this Item?
            item_id = row.item_id
            minimum = row.quantity
            minimum_id = row.id
            stock = 0
            for row in inventory:
                if row["inv_inv_item.item_id"] == item_id:
                    stock += (row["inv_inv_item.quantity"] * row["supply_item_pack.quantity"])
            query = nquery & (ntable.record_id == minimum_id)
            if stock < minimum:
                # Add Alert, if there is not one already present
                query &= (ntable.deleted == False)
                exists = current.db(query).select(ntable.id,
                                                  limitby = (0, 1),
                                                  ).first()
                if not exists:
                    alerts.append((item_id, stock, minimum_id))
            else:
                # Remove any Minimum Alerts for this Item/Warehouse
                auth = current.auth
                override_default = auth.override
                auth.override = True
                resource = s3db.resource("auth_user_notification",
                                         filter = query,
                                         )
                resource.delete()
                auth.override = override_default

        if alerts:
            # Generate Alerts
            warehouse_name = warehouse.name

            from .controllers import inv_operators_for_sites
            operators = inv_operators_for_sites([site_id])[site_id]["operators"]
            languages = {}
            for row in operators:
                language = row["auth_user.language"]
                if language not in languages:
                    languages[language] = []
                languages[language].append((row["pr_person_user.pe_id"], row["pr_person_user.user_id"]))

            # Bulk Lookup Item Represents
            # - assumes that we are not using translate = True!
            item_ids = [alert[0] for alert in alerts]
            items = itable.item_id.represent.bulk(item_ids, show_link=False)

            #from gluon import URL
            from s3 import s3_str

            url = "%s%s" % (settings.get_base_public_url(),
                            URL(c="inv", f="warehouse",
                                args = [warehouse.id, "inv_item"],
                                ),
                            )
            send_email = current.msg.send_by_pe_id
            insert = ntable.insert

            T = current.T
            session = current.session
            #session_s3 = session.s3
            ui_language = session.s3.language

            subject_T = T("%(item)s replenishment needed in %(site)s Warehouse")
            message_T = T("%(item)s replenishment needed in %(site)s Warehouse. %(quantity)s remaining. Please review at: %(url)s")
            alert_T = T("%(item)s replenishment needed in %(site)s Warehouse. %(quantity)s remaining")

            warnings = 0

            for alert in alerts:
                item_id = alert[0]
                item = items.get(item_id)
                quantity = int(alert[1])
                minimum_id = alert[2]
                for language in languages:
                    T.force(language)
                    #session_s3.language = language # for date_represent
                    subject = s3_str(subject_T) % {"item": item[:30],
                                                   "site": warehouse_name
                                                   }
                    message = s3_str(message_T) % {"item": item,
                                                   "site": warehouse_name,
                                                   "quantity": quantity,
                                                   "url": url,
                                                   }
                    alert = s3_str(alert_T) % {"item": item,
                                               "site": warehouse_name,
                                               "quantity": quantity,
                                               }
                    users = languages[language]
                    for user in users:
                        send_email(user[0],
                                   subject = subject,
                                   message = message,
                                   )
                        # Add Alert to Dashboard
                        insert(user_id = user[1],
                               name = alert,
                               url = url,
                               tablename = "inv_minimum",
                               record_id = minimum_id,
                               )

                # Restore language for UI
                #session_s3.language = ui_language
                T.force(ui_language)

                # Interactive Notification
                #alert = {"item": item,
                #         "site": warehouse_name,
                #         "quantity": quantity,
                #         }
                #warnings.append(alert)
                warnings += 1

            if warnings == 1:
                session.warning = s3_str(alert_T) % {"item": item,
                                                     "site": warehouse_name,
                                                     "quantity": quantity,
                                                     }
            else:
                session.warning = s3_str(T("Replenishment of multiple items needed in %(site)s Warehouse. Check the Dashboard for details.")) % \
                                            {"site": warehouse_name,
                                             }

    # -------------------------------------------------------------------------
    def on_free_capacity_update(warehouse):
        """
            Generate an Alert if Free Capacity < 10% of Capacity
            Cancel Alerts if Free capacity is above this
            Trigger Stock Limit Alert creation/cancellation
        """

        s3db = current.s3db

        warehouse_id = warehouse.id

        ntable = s3db.auth_user_notification
        query = (ntable.tablename == "inv_warehouse") & \
                (ntable.record_id == warehouse_id) & \
                (ntable.type == "capacity")

        free_capacity = warehouse.free_capacity
        threshold = warehouse.capacity * 0.1
        if free_capacity < threshold:
            # Generate Capacity Alert, if there is not one already present
            query = query & (ntable.deleted == False)
            exists = current.db(query).select(ntable.id,
                                              limitby = (0, 1),
                                              ).first()
            if not exists:
                #from gluon import URL
                from s3 import s3_str
                site_id = warehouse.site_id
                warehouse_name = warehouse.name
                url = "%s%s" % (settings.get_base_public_url(),
                                URL(c="inv", f="warehouse",
                                    args = warehouse_id,
                                    ),
                                )
                send_email = current.msg.send_by_pe_id

                T = current.T
                session_s3 = current.session.s3
                ui_language = session_s3.language

                subject_T = T("Stockpile Capacity in %(site)s Warehouse is less than %(threshold)s m3")
                message_T = T("Stockpile Capacity in %(site)s Warehouse is less than %(threshold)s m3. Please review at: %(url)s")
                alert_T = T("Stockpile Capacity in %(site)s Warehouse is less than %(threshold)s m3")

                from .controllers import inv_operators_for_sites
                operators = inv_operators_for_sites([site_id])[site_id]["operators"]
                insert = ntable.insert
                languages = {}
                for row in operators:
                    language = row["auth_user.language"]
                    if language not in languages:
                        languages[language] = []
                    languages[language].append((row["pr_person_user.pe_id"], row["pr_person_user.user_id"]))
                for language in languages:
                    T.force(language)
                    #session_s3.language = language # for date_represent
                    subject = s3_str(subject_T) % {"site": warehouse_name,
                                                   "threshold": threshold,
                                                   }
                    message = s3_str(message_T) % {"site": warehouse_name,
                                                   "threshold": threshold,
                                                   "url": url,
                                                   }
                    alert = s3_str(alert_T) % {"site": warehouse_name,
                                               "threshold": threshold,
                                               }
                    users = languages[language]
                    for user in users:
                        send_email(user[0],
                                   subject = subject,
                                   message = message,
                                   )
                        # Add Alert to Dashboard
                        insert(user_id = user[1],
                               name = alert,
                               url = url,
                               type = "capacity",
                               tablename = "inv_warehouse",
                               record_id = warehouse_id,
                               )

                # Restore language for UI
                #session_s3.language = ui_language
                T.force(ui_language)
        else:
            # Remove any Capacity Alerts
            auth = current.auth
            override_default = auth.override
            auth.override = True
            resource = s3db.resource("auth_user_notification",
                                     filter = query,
                                     )
            resource.delete()
            auth.override = override_default

        # Trigger Stock Limit Alert creation/cancellation
        stock_limit_alerts(warehouse)

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_resource(r, tablename):

        s3db = current.s3db

        settings.inv.recv_tab_label = "Received/Incoming Shipments"
        settings.inv.send_tab_label = "Sent Shipments"

        s3db.configure("inv_warehouse",
                       on_free_capacity_update = on_free_capacity_update,
                       )

        # Only Nepal RC use Warehouse Types
        field = s3db.inv_warehouse.warehouse_type_id
        field.readable = field.writable = False
        list_fields = s3db.get_config("inv_warehouse", "list_fields")
        try:
            list_fields.remove("warehouse_type_id")
        except ValueError:
            # Already removed
            pass

    settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

    # -------------------------------------------------------------------------
    def customise_inv_warehouse_controller(**attr):

        if current.auth.s3_has_role("ADMIN"):
            # ADMIN is allowed to Edit Inventory bypassing the need to use Adjustments
            # - seems wrong to me as Adjustments aren't that heavy, but has been requested
            settings.inv.direct_stock_edits = True

        return attr

    settings.customise_inv_warehouse_controller = customise_inv_warehouse_controller

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        #root_org = current.auth.root_org_name()
        #if root_org != HNRC:
        #    return

        # Simplify Form
        s3db = current.s3db
        table = s3db.org_facility
        table.code.readable = table.code.writable = False
        table.opening_times.readable = table.opening_times.writable = False
        table.website.readable = table.website.writable = False
        field = s3db.org_site_facility_type.facility_type_id
        field.readable = field.writable = False
        # Simplify Search Fields
        from s3 import S3TextFilter, S3OptionsFilter, S3LocationFilter
        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()
        text_fields = ["name",
                       #"code",
                       "comments",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       ]
        for level in levels:
            lfield = "location_id$%s" % level
            text_fields.append(lfield)

        s3db.configure("org_facility",
                       filter_widgets = [
                            S3TextFilter(text_fields,
                                         label = T("Search"),
                                         ),
                            S3OptionsFilter("organisation_id"),
                            S3LocationFilter("location_id",
                                             levels = levels,
                                             ),
                            ]
                       )


    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_office_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Organisation needs to be an NS/Branch
            ns_only("org_office",
                    required = True,
                    branches = True,
                    # default
                    #limit_filter_opts = True,
                    )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_office_controller = customise_org_office_controller

    # -------------------------------------------------------------------------
    def org_organisation_organisation_type_onaccept(form):
        """
            * Update the realm entity
            * Ensure that all RC Orgs get added to RC org_group
        """

        # Get the link
        try:
            link_id = form.vars.id
        except AttributeError:
            return

        db = current.db
        s3db = current.s3db

        ttable = s3db.org_organisation_type
        ltable = s3db.org_organisation_organisation_type

        query = (ltable.id == link_id) & \
                (ltable.organisation_type_id == ttable.id)

        row = db(query).select(ltable.organisation_id,
                               ttable.name,
                               limitby = (0, 1),
                               ).first()

        if row:
            organisation_id = row["org_organisation_organisation_type.organisation_id"]

            # Update the realm entity
            current.auth.set_realm_entity("org_organisation",
                                          organisation_id,
                                          force_update = True,
                                          )

            if row["org_organisation_type.name"] == RED_CROSS:
                # RC Org: ensure a member of RC org_group
                gtable = s3db.org_group
                group = db(gtable.name == "RC").select(gtable.id,
                                                       limitby = (0, 1),
                                                       ).first()
                try:
                    group_id = group.id
                except:
                    # IFRC prepop not done: Bail
                    return
                mtable = s3db.org_group_membership
                query = (mtable.organisation_id == organisation_id) & \
                        (mtable.group_id == group_id)
                member = db(query).select(mtable.id,
                                          limitby = (0, 1),
                                          ).first()
                if not member:
                    membership_id = mtable.insert(group_id = group_id,
                                                  organisation_id = organisation_id,
                                                  )
                    onaccept = s3db.get_config("org_group_membership", "onaccept")
                    if onaccept:
                        mform = Storage(vars = Storage(id = membership_id))
                        onaccept(mform)

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # Ensure that realms get set properly
        # Ensure that all RC Orgs get added to RC org_group
        #from s3db.org import org_organisation_organisation_type_onaccept
        from s3db.org import org_organisation_organisation_type_ondelete
        s3db.configure("org_organisation_organisation_type",
                       onaccept = org_organisation_organisation_type_onaccept,
                       ondelete = org_organisation_organisation_type_ondelete,
                       )

        if current.auth.override:
            # Prepop
            # - ensure that realms get set properly
            from s3db.org import org_organisation_organisation_onaccept, \
                                 org_organisation_organisation_ondelete
            s3db.configure("org_organisation_organisation",
                           onaccept = org_organisation_organisation_onaccept,
                           ondelete = org_organisation_organisation_ondelete,
                           )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        type_filter = current.request.get_vars.get("organisation_type.name")

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.interactive or r.representation == "aadata":

                if not r.component or r.component_name == "branch":

                    resource = r.resource
                    table = resource.table

                    if r.function == "training_center":
                        auth = current.auth
                        if not auth.s3_has_role("ADMIN"):
                            # See NS Training Centers only
                            resource.add_filter(table.root_organisation == auth.root_org())

                            if not auth.s3_has_role("ORG_ADMIN"):
                                resource.configure(insertable = False)

                    type_label = T("Type")

                    if r.get_vars.get("caller") == "org_facility_organisation_id":
                        # Simplify
                        from s3 import S3SQLCustomForm
                        crud_form = S3SQLCustomForm("name",
                                                    "acronym",
                                                    "phone",
                                                    "comments",
                                                    )
                        resource.configure(crud_form = crud_form,
                                           )

                    else:
                        list_fields = ["name",
                                       "acronym",
                                       "organisation_organisation_type.organisation_type_id",
                                       "country",
                                       "website",
                                       ]
                        if type_filter:
                            type_names = type_filter.split(",")
                            if len(type_names) == 1:
                                # Strip Type from list_fields
                                try:
                                    list_fields.remove("organisation_organisation_type.organisation_type_id")
                                except ValueError:
                                    # Already removed
                                    pass
                                type_label = ""

                            if type_filter == RED_CROSS:
                                # Modify filter_widgets
                                filter_widgets = resource.get_config("filter_widgets")
                                # Remove type (always 'RC')
                                filter_widgets.pop(1)

                                # Modify CRUD Strings
                                s3.crud_strings.org_organisation = Storage(
                                    label_create = T("Create National Society"),
                                    title_display = T("National Society Details"),
                                    title_list = T("Red Cross & Red Crescent National Societies"),
                                    title_update = T("Edit National Society"),
                                    title_upload = T("Import Red Cross & Red Crescent National Societies"),
                                    label_list_button = T("List Red Cross & Red Crescent National Societies"),
                                    label_delete_button = T("Delete National Society"),
                                    msg_record_created = T("National Society added"),
                                    msg_record_modified = T("National Society updated"),
                                    msg_record_deleted = T("National Society deleted"),
                                    msg_list_empty = T("No Red Cross & Red Crescent National Societies currently registered"),
                                    )
                                # Add Region to list_fields
                                list_fields.insert(-1, "organisation_region.region_id")

                            if type_filter == "Supplier":
                                # Show simple free-text contact field
                                contact_field = table.contact
                                contact_field.readable = True
                                contact_field.writable = True

                                # Include contact information in list_fields
                                list_fields = ["name",
                                               "acronym",
                                               "country",
                                               "contact",
                                               "phone",
                                               "website",
                                               ]

                        resource.configure(list_fields = list_fields)

                        if r.interactive:
                            table.country.label = T("Country")
                            from s3 import S3SQLCustomForm, S3SQLInlineLink

                            crud_fields = ["name",
                                           "acronym",
                                           S3SQLInlineLink("organisation_type",
                                                           field = "organisation_type_id",
                                                           label = type_label,
                                                           multiple = False,
                                                           ),
                                           "country",
                                           "contact",
                                           "phone",
                                           "website",
                                           "logo",
                                           "comments",
                                           ]
                            if type_filter == RED_CROSS:
                                crud_fields.insert(3, "organisation_region.region_id")
                            crud_form = S3SQLCustomForm(*crud_fields)
                            resource.configure(crud_form = crud_form)

            return result
        s3.prep = custom_prep

        if type_filter == "Supplier":
            # Suppliers have simpler Tabs (hide Offices, Warehouses and Contacts)
            tabs = [(T("Basic Details"), None, {"native": 1}),
                    ]
            if settings.get_L10n_translate_org_organisation():
                tabs.append((T("Local Names"), "name"))
            from s3db.org import org_rheader
            attr["rheader"] = lambda r: org_rheader(r, tabs=tabs)

        elif type_filter == "Academic,Bilateral,Government,Intergovernmental,NGO,UN agency":
            # Partners have simpler Tabs (hide Offices, Warehouses and Contacts)
            tabs = [(T("Basic Details"), None, {"native": 1}),
                    (T("Projects"), "project"),
                    ]
            if settings.get_L10n_translate_org_organisation():
                tabs.insert(1, (T("Local Names"), "name"))
            from s3db.org import org_rheader
            attr["rheader"] = lambda r: org_rheader(r, tabs=tabs)

        else:
            # Enable tab for PDF card configurations
            settings.org.pdf_card_configs = True

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_site_layout_resource(r, tablename):

        current.response.s3.crud_strings[tablename] = Storage(
           label_create = T("Create Warehouse Location"),
           title_display = T("Warehouse Location Details"),
           title_list = T("Warehouse Locations"),
           title_update = T("Edit Warehouse Location"),
           label_list_button = T("List Warehouse Locations"),
           label_delete_button = T("Delete Warehouse Location"),
           msg_record_created = T("Warehouse Location added"),
           msg_record_modified = T("Warehouse Location updated"),
           msg_record_deleted = T("Warehouse Location deleted"),
           msg_list_empty = T("No Warehouse Locations currently registered"),
           )

    settings.customise_org_site_layout_resource = customise_org_site_layout_resource

    # -------------------------------------------------------------------------
    def customise_pr_address_resource(r, tablename):

        #if current.auth.root_org_name() in (HNRC,
        #                                    PYRC,
        #                                    ):
            # Location Hierarchy loaded: Leave things as they are since we have the
        #   pass
        #else:
        s3db = current.s3db
        s3db.gis_location.addr_street.label = T("Address")
        s3db.configure("pr_address",
                       list_fields = ["type",
                                      (current.messages.COUNTRY, "location_id$L0"),
                                      (T("Address"), "location_id$addr_street"),
                                      #(settings.get_ui_label_postcode(),
                                      # "location_id$addr_postcode")
                                      ],
                       )

    settings.customise_pr_address_resource = customise_pr_address_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        table = current.s3db[tablename]
        table.comments.readable = table.comments.writable = False
        table.contact_description.readable = table.contact_description.writable = False
        table.priority.readable = table.priority.writable = False

    settings.customise_pr_contact_resource = customise_pr_contact_resource

    # -------------------------------------------------------------------------
    def customise_pr_education_resource(r, tablename):

        s3db = current.s3db
        table = s3db[tablename]
        table.country.readable = table.country.writable = True
        table.grade.readable = table.grade.writable = False
        table.major.readable = table.major.writable = False
        s3db.configure(tablename,
                       list_fields = [# Normally accessed via component
                                      #"person_id",
                                      "year",
                                      "level_id",
                                      "award",
                                      #"major",
                                      #"grade",
                                      "institute",
                                      ],
                       )

    settings.customise_pr_education_resource = customise_pr_education_resource

    # -------------------------------------------------------------------------
    def customise_pr_forum_resource(r, tablename):

        table = current.s3db.pr_forum
        table.forum_type.readable = table.forum_type.writable = False

    settings.customise_pr_forum_resource = customise_pr_forum_resource

    # -------------------------------------------------------------------------
    def customise_pr_forum_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "assign":
                auth = current.auth
                has_role = auth.s3_has_role
                if not has_role("ADMIN") and has_role("training_coordinator"):
                    # Filter people to just those Trained by this Reference Center or Staff of this Reference Center
                    from s3 import FS
                    organisation_id = auth.user.organisation_id
                    query = (FS("training.training_event_id$organisation_id") == organisation_id) | \
                            (FS("user.organisation_id") == organisation_id)
                    s3.filter = query

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_pr_forum_controller = customise_pr_forum_controller

    # -------------------------------------------------------------------------
    #def customise_pr_group_controller(**attr):

    #    # Organisation needs to be an NS/Branch
    #    ns_only("org_organisation_team",
    #            required = False,
    #            branches = True,
    #            )

    #    return attr

    #settings.customise_pr_group_controller = customise_pr_group_controller

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        table = current.s3db[tablename]
        table.first_name.label = T("Forenames")
        table.middle_name.label = T("Father's Surname")
        table.last_name.label = T("Mother's Surname")

    settings.customise_pr_person_resource = customise_pr_person_resource

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3
        # Enable scalability-optimized strategies
        settings.base.bigtable = True

        EXTERNAL = False

        auth = current.auth
        has_role = auth.s3_has_role
        request = current.request

        if "profile" in request.get_vars:
            PROFILE = True
        else:
            len_roles = len(current.session.s3.roles)
            if (len_roles <= 2) or \
               (len_roles == 3 and has_role("RIT_MEMBER") and not has_role("ADMIN")):
                PROFILE = True
            else:
                PROFILE = False
                if request.function == "trainee_person":
                    EXTERNAL = True

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            if PROFILE:
                # Configure for personal mode
                s3.crud_strings["pr_person"].update(
                    title_display = T("Profile"),
                    title_update = T("Profile")
                    )
                # People can edit their own HR data
                configure = s3db.configure
                configure("hrm_human_resource",
                          deletable = False,
                          #editable = True,
                          insertable = False,
                          )
                if not has_role("RIT_MEMBER"):
                    #configure("hrm_certification",
                    #          deletable = True,
                    #          editable = True,
                    #          insertable = True,
                    #          )
                    configure("hrm_training",
                              deletable = False,
                              editable = False,
                              insertable = False,
                              )

            elif EXTERNAL:
                s3.crud_strings["pr_person"].update(
                    title_display = T("External Trainee Details"),
                    title_update = T("External Trainee Details")
                    )

            component_name = r.component_name
            method = r.method
            if method == "import":
                # HR records may be created via import
                # Default to Volunteers
                s3db.hrm_human_resource.type.default = 2
                # Doesn't work as email created after human_resource
                #s3db.configure("hrm_human_resource",
                #               create_onaccept = hrm_human_resource_create_onaccept,
                #               )

            elif method == "record" or component_name == "human_resource":
                table = s3db.hrm_human_resource
                if EXTERNAL:
                    db = current.db
                    f = table.organisation_id
                    f.label = T("Organization")
                    # Organisation cannot be an NS/Branch
                    # Lookup organisation_type_id for Red Cross
                    ttable = s3db.org_organisation_type
                    type_ids = db(ttable.name.belongs((RED_CROSS, "Training Center"))).select(ttable.id,
                                                                                              cache = s3db.cache,
                                                                                              limitby = (0, 2),
                                                                                              )
                    if type_ids:
                        from s3 import IS_ONE_OF
                        ltable = db.org_organisation_organisation_type
                        rows = db(ltable.organisation_type_id.belongs(type_ids)).select(ltable.organisation_id)
                        not_filter_opts = [row.organisation_id for row in rows]
                        f.requires = IS_ONE_OF(db, "org_organisation.id",
                                               f.represent,
                                               not_filterby = "id",
                                               not_filter_opts = not_filter_opts,
                                               updateable = True,
                                               orderby = "org_organisation.name",
                                               sort = True,
                                               )
                else:
                    # Organisation needs to be an NS/Branch
                    if auth.s3_has_roles(("surge_capacity_manager",
                                          "ns_training_manager",
                                          "ns_training_assistant",
                                          "training_coordinator",
                                          "training_assistant",
                                          )):
                        updateable = False
                    else:
                        updateable = True
                    ns_only("hrm_human_resource",
                            required = True,
                            branches = True,
                            updateable = updateable,
                            )
                f = table.essential
                f.readable = f.writable = False
                f = table.site_contact
                f.readable = f.writable = False
                if method == "record":
                    if not auth.s3_has_roles(("ORG_ADMIN",
                                              "hr_manager",
                                              "hr_assistant",
                                              )):
                        table.organisation_id.writable = False
                        # Hide the Site field as this data isn't loaded & we want to keep things simple
                        # @ToDo: Re-enable for specific NS as-required
                        f = table.site_id
                        f.readable = f.writable = False
                    # Use default form (legacy)
                    #s3db.clear_config("hrm_human_resource", "crud_form")

            elif not component_name:
                s3db.configure("pr_person",
                               listadd = True,
                               )

                # Basic Details tab
                f = s3db.pr_person.middle_name
                f.readable = f.writable = True
                f = s3db.pr_person_details.nationality2
                f.readable = f.writable = True
                from s3 import S3SQLCustomForm
                crud_form = S3SQLCustomForm("first_name",
                                            "middle_name",
                                            "last_name",
                                            "date_of_birth",
                                            "gender",
                                            "person_details.marital_status",
                                            "person_details.nationality",
                                            "person_details.nationality2",
                                            "comments",
                                            )
                s3db.configure("pr_person",
                               crud_form = crud_form,
                               )

            elif component_name == "appraisal":
                atable = r.component.table
                atable.organisation_id.readable = atable.organisation_id.writable = False
                # Organisation needs to be an NS
                #ns_only("hrm_appraisal",
                #        required = True,
                #        branches = False,
                #        )
                field = atable.supervisor_id
                field.readable = field.writable = False
                field = atable.job_title_id
                field.comment = None
                field.label = T("Sector") # RDRT-specific
                from s3 import IS_ONE_OF
                field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                           field.represent,
                                           filterby = "type",
                                           filter_opts = (4,),
                                           )

            elif component_name == "certification":
                ctable = r.component.table
                ctable.organisation_id.readable = False

            elif component_name == "competency":
                ctable = r.component.table
                ctable.skill_id.label = T("Language")
                ctable.organisation_id.readable = False

            elif component_name == "experience":
                # 2 options here: Work Experience & Missions
                # These have very different views
                # Work Experience
                etable = r.component.table
                etable.organisation_id.readable = etable.organisation_id.writable = False
                etable.job_title_id.readable = etable.job_title_id.writable = False
                etable.responsibilities.readable = etable.responsibilities.writable = False
                etable.hours.readable = etable.hours.writable = False
                etable.supervisor_id.readable = etable.supervisor_id.writable = False
                etable.organisation.readable = etable.organisation.writable = True
                etable.job_title.readable = etable.job_title.writable = True
                from s3 import S3LocationSelector
                etable.location_id.label = T("Country")
                etable.location_id.widget = S3LocationSelector(levels = ("L0",),
                                                               show_map = False,
                                                               show_postcode = False,
                                                               )

            elif component_name == "identity":
                #itable = r.component.table
                # Default
                #itable.country_code.readable = itable.country_code.writable = False
                #itable.ia_name.readable = itable.ia_name.writable = False
                f = r.component.table.ia_name
                f.readable = f.writable = False
                list_fields = ["type",
                               "value",
                               "valid_until",
                               ]
                s3db.configure("pr_identity",
                               list_fields = list_fields,
                               )

            # Moved to MedicalTab
            #elif component_name == "physical_description":
            #    from gluon import DIV
            #    dtable = r.component.table
            #    dtable.medical_conditions.comment = DIV(_class = "tooltip",
            #                                            _title = "%s|%s" % (T("Medical Conditions"),
            #                                                                T("Chronic Illness, Disabilities, Mental/Psychological Condition etc."),
            #                                                                ),
            #                                            )
            #    dtable.allergic.writable = dtable.allergic.readable = True
            #    dtable.allergies.writable = dtable.allergies.readable = True
            #    dtable.ethnicity.writable = dtable.ethnicity.readable = False
            #    dtable.other_details.writable = dtable.other_details.readable = False
            #    s3.jquery_ready.append('''S3.showHidden('%s',%s,'%s')''' % \
            #        ("allergic", json.dumps(["allergies"], separators=SEPARATORS), "pr_physical_description"))

            if not EXTERNAL and \
               auth.s3_has_roles(ID_CARD_EXPORT_ROLES):
                # Show button to export ID card
                settings.hrm.id_cards = True

            return True
        s3.prep = custom_prep

        if current.request.controller in ("default", "hrm", "vol"):
            attr["csv_template"] = ("../../themes/RMS/formats", "hrm_person")
            # Common rheader for all views
            from s3db.hrm import hrm_rheader
            attr["rheader"] = lambda r: hrm_rheader(r, profile=PROFILE)

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def customise_pr_physical_description_resource(r, tablename):

        from gluon import DIV
        from s3 import S3SQLCustomForm

        s3db = current.s3db

        #s3db.pr_physical_description.medical_conditions.comment = DIV(_class = "tooltip",
        #                                                              _title = "%s|%s" % (T("Medical Conditions"),
        #                                                                                  T("Chronic Illness, Disabilities, Mental/Psychological Condition etc."),
        #                                                                                  ),
        #                                                              )

        s3db.pr_physical_description.medical_conditions.comment = DIV(_class = "tooltip",
                                                                      _title = "%s|%s" % (T("Medical Conditions"),
                                                                                          T("It is important to include, if they exist: surgical history, medical restrictions, vaccines, etc."),
                                                                                          ),
                                                                      )

        s3db.configure(tablename,
                       crud_form = S3SQLCustomForm("blood_type",
                                                   "medical_conditions",
                                                   "medication",
                                                   "diseases",
                                                   "allergic",
                                                   "allergies",
                                                   ),
                       )

    settings.customise_pr_physical_description_resource = customise_pr_physical_description_resource

    # -------------------------------------------------------------------------
    def customise_project_window_resource(r, tablename):

        r.resource.configure(deletable = False,
                             insertable = False,
                             )

    settings.customise_project_window_resource = customise_project_window_resource

    # -------------------------------------------------------------------------
    def customise_project_activity_data_resource(r, tablename):

        if current.auth.s3_has_roles(("monitoring_evaluation", "ORG_ADMIN")):
            # Normal Access
            return

        # Project Manager
        if r.method == "update":

            table = current.s3db.project_activity_data

            if r.tablename == "project_activity_data":
                record_id = r.id
            else:
                record_id = r.component_id
            record = current.db(table.id == record_id).select(table.value,
                                                              limitby = (0, 1),
                                                              ).first()
            if record.value:
                # Redirect to Read-only mode
                from gluon import redirect
                redirect(r.url(method="read"))
            else:
                # Cannot edit anything
                for f in table.fields:
                    table[f].writable = False
                # Except add a Real value
                table.value.writable = True
                # Or Amend the Comments
                table.comments.writable = True
        else:
            s3db = current.s3db
            table = s3db.project_window
            record = current.db(table.deleted == False).select(table.start_date,
                                                               table.end_date,
                                                               limitby = (0, 1),
                                                               ).first()
            if record:
                if record.start_date <= r.utcnow.date() <= record.end_date:
                    # Inside the time window: Project Manager may update Actuals
                    return
            # Outside the time window: Project Manager cannot add the Actual value
            s3db.project_activity_data.value.writable = False
            s3db.configure("project_activity_data",
                           updateable = False,
                           )

    settings.customise_project_activity_data_resource = customise_project_activity_data_resource

    # -------------------------------------------------------------------------
    def customise_project_organisation_resource(r, tablename):

        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            #from gluon import IS_IN_SET
            currency_opts = {"EUR" : "EUR",
                             "CHF" : "CHF",
                             "HNL" : "L",
                             "USD" : "USD",
                             }
            f = current.s3db.project_organisation.currency
            f.represent = currency_represent
            f.requires = IS_IN_SET(currency_opts)

    settings.customise_project_organisation_resource = customise_project_organisation_resource

    # -------------------------------------------------------------------------
    def project_project_postprocess(form):
        """
            When using Budget Monitoring (i.e. HNRC) then create the entries
        """

        db = current.db
        s3db = current.s3db
        project_id = form.vars.id
        # Read Budget Entity ID, Start Date and End Date
        ptable = s3db.project_project
        project = db(ptable.id == project_id).select(ptable.budget_entity_id,
                                                     ptable.name,
                                                     ptable.start_date,
                                                     ptable.end_date,
                                                     limitby = (0, 1),
                                                     ).first()
        if not project:
            return

        # Copy Project Name to Budget Name
        budget_entity_id = project.budget_entity_id
        btable = s3db.budget_budget
        query = (btable.budget_entity_id == budget_entity_id)
        budget = db(query).select(btable.id, # Needed for update_record
                                  # If we want to provide smoothed default expected values
                                  #btable.total_budget,
                                  btable.currency,
                                  # Assume Monthly
                                  #btable.monitoring_frequency,
                                  limitby = (0, 1),
                                  ).first()
        if not budget:
            return

        # Build Budget Name from Project Name
        project_name = project.name

        # Check for duplicates
        query = (btable.name == project_name) & \
                (btable.id != budget.id)
        duplicate = db(query).select(btable.id,
                                     limitby = (0, 1),
                                     ).first()

        if not duplicate:
            budget_name = project_name[:128]
        else:
            # Need another Unique name
            import uuid
            budget_name = "%s %s" % (project_name[:91], uuid.uuid4())
        budget.update_record(name = budget_name)

        mtable = s3db.budget_monitoring
        exists = db(mtable.budget_entity_id == budget_entity_id).select(mtable.id,
                                                                        limitby = (0, 1),
                                                                        )
        if not exists:
            # Create Monitoring Data entries
            start_date = project.start_date
            end_date = project.end_date
            if not start_date or not end_date:
                return
            # Assume Monthly
            #monitoring_frequency = budget.monitoring_frequency
            #if not monitoring_frequency:
            #    return
            #total_budget = budget.total_budget
            currency = budget.currency
            # Create entries for the 1st of every month between start_date and end_date
            from dateutil import rrule
            dates = list(rrule.rrule(rrule.MONTHLY, bymonthday=1, dtstart=start_date, until=end_date))
            for d in dates:
                mtable.insert(budget_entity_id = budget_entity_id,
                              # @ToDo: This needs to be modified whenever entries are manually edited
                              # Set/update this in budget_monitoring_onaccept
                              # - also check here that we don't exceed overall budget
                              start_date = start_date,
                              end_date = d,
                              currency = currency,
                              )
                # Start date relates to previous entry
                start_date = d

    # -------------------------------------------------------------------------
    def customise_project_programme_controller(**attr):

        # Organisation needs to be an NS/Branch
        ns_only("project_programme",
                required = True,
                branches = False,
                updateable = True,
                )

        return attr

    settings.customise_project_programme_controller = customise_project_programme_controller

    # -------------------------------------------------------------------------
    def customise_project_project_controller(**attr):

        tablename = "project_project"

        if current.request.controller == "inv":
            # Very simple functionality all that is required
            from gluon import IS_NOT_EMPTY
            f = current.s3db.project_project.code
            f.label = T("Code")
            f.requires = IS_NOT_EMPTY()
            # Lead Organisation needs to be an NS (not a branch)
            ns_only(tablename,
                    required = True,
                    branches = False,
                    # default
                    #limit_filter_opts = True,
                    )
            return attr

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.organisation_id",
                              user_org_default_filter,
                              tablename = "project_project")

        # Load standard model
        s3db = current.s3db
        table = s3db[tablename]

        # Disable Map Tab on Summary View
        # - until we can support multiple Points per Record
        settings.ui.summary = ({"common": True,
                                "name": "add",
                                "widgets": [{"method": "create"}],
                                },
                               #{"common": True,
                               # "name": "cms",
                               # "widgets": [{"method": "cms"}]
                               # },
                               {"name": "table",
                                "label": "Table",
                                "widgets": [{"method": "datatable"}]
                                },
                               {"name": "charts",
                                "label": "Report",
                                "widgets": [{"method": "report",
                                             "ajax_init": True}]
                                },
                               #{"name": "map",
                               # "label": "Map",
                               # "widgets": [{"method": "map",
                               #              "ajax_init": True}],
                               # },
                               )

        # @ToDo: S3SQLInlineComponent for Project orgs
        # Get IDs for Partner NS/Partner Donor
        # db = current.db
        # ttable = db.org_organisation_type
        # rows = db(ttable.deleted != True).select(ttable.id,
        #                                          ttable.name,
        #                                          )
        # rc = []
        # not_rc = []
        # nappend = not_rc.append
        # for row in rows:
            # if row.name == RED_CROSS:
                # rc.append(row.id)
            # elif row.name == "Supplier":
                # pass
            # else:
                # nappend(row.id)

        # Custom Fields
        table.organisation_id.label = T("Host National Society")

        # Custom Crud Form
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        # Special cases for different NS
        root_org = current.auth.root_org_name()
        if root_org == HNRC:
            # @ToDo: Use Inter-American Framework instead (when extending to Zone office)
            # @ToDo: Add 'Business Line' (when extending to Zone office)
            project_settings = settings.project
            project_settings.details_tab = True
            #project_settings.community_volunteers = True
            # Done in a more structured way instead
            objectives = None
            outputs = None
            project_settings.goals = True
            project_settings.outcomes = True
            project_settings.outputs = True
            project_settings.indicators = True
            project_settings.indicator_criteria = True
            project_settings.status_from_activities = True
            table.human_resource_id.label = T("Coordinator")
            # Use Budget module instead of ProjectAnnualBudget
            project_settings.multiple_budgets = False
            project_settings.budget_monitoring = True
            # Require start/end dates
            table.start_date.requires = table.start_date.requires.other
            table.end_date.requires = table.end_date.requires.other
            budget = S3SQLInlineComponent("budget",
                                          label = T("Budget"),
                                          #link = False,
                                          multiple = False,
                                          fields = ["total_budget",
                                                    "currency",
                                                    #"monitoring_frequency",
                                                    ],
                                          )
            btable = s3db.budget_budget
            # Need to provide a name
            import random, string
            btable.name.default = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
            btable.monitoring_frequency.default = 3 # Monthly
            btable.currency.represent = currency_represent
            currency_opts = {"EUR" : "EUR",
                             "CHF" : "CHF",
                             "HNL" : "L",
                             "USD" : "USD",
                             }
            #from gluon import IS_IN_SET
            btable.currency.requires = IS_IN_SET(currency_opts)
            s3db.budget_monitoring.currency.represent = currency_represent
            postprocess = project_project_postprocess
            list_fields = s3db.get_config("project_project", "list_fields")
            list_fields += [(T("Actual Progress"), "actual_progress_by_activities"),
                            (T("Planned Progress"), "planned_progress_by_activities"),
                            ]
        else:
            objectives = "objectives"
            outputs = S3SQLInlineComponent(
                "output",
                label = T("Outputs"),
                fields = ["name", "status"],
            )
            budget = None
            postprocess = None

        if settings.get_project_programmes():
            # Inject inline link for programmes including S3PopupLink
            #from s3layouts import S3PopupLink
            comment = s3db.project_programme_id.attr.comment
            comment.vars = {"caller": "link_defaultprogramme",
                            "prefix": "project",
                            "parent": "programme_project",
                            }
            programme = S3SQLInlineLink("programme",
                                        field = "programme_id",
                                        label = T("Program"),
                                        multiple = False,
                                        comment = comment,
                                        )
        else:
            programme = None

        from s3db.project import project_hazard_help_fields, \
                                 project_theme_help_fields
        crud_form = S3SQLCustomForm(
            "organisation_id",
            programme,
            "name",
            "code",
            "description",
            "status_id",
            "start_date",
            "end_date",
            budget,
            #S3SQLInlineComponent(
            #    "location",
            #    label = T("Locations"),
            #    fields = ["location_id"],
            #),
            # Outputs
            outputs,
            S3SQLInlineLink(
                "hazard",
                label = T("Hazards"),
                field = "hazard_id",
                help_field = project_hazard_help_fields,
                cols = 4,
                translate = True,
            ),
            S3SQLInlineLink(
                "sector",
                label = T("Sectors"),
                field = "sector_id",
                cols = 4,
                translate = True,
            ),
            S3SQLInlineLink(
                "theme",
                label = T("Themes"),
                field = "theme_id",
                help_field = project_theme_help_fields,
                cols = 4,
                translate = True,
                # Filter Theme by Sector
               filterby = "theme_id:project_theme_sector.sector_id",
               match = "sector_project.sector_id",
               script = '''
    $.filterOptionsS3({
     'trigger':{'alias':'sector','name':'sector_id','inlineType':'link'},
     'target':{'alias':'theme','name':'theme_id','inlineType':'link'},
     'lookupPrefix':'project',
     'lookupResource':'theme',
     'lookupKey':'theme_id:project_theme_sector.sector_id',
     'showEmptyField':false,
     'tooltip':'project_theme_help_fields(id,name)'
    })'''
            ),
            objectives,
            "human_resource_id",
            # Disabled since we need organisation_id filtering to either organisation_type_id == RC or NOT
            # & also hiding Branches from RCs
            # & also rewriting for organisation_type_id via link table
            # Partner NS
            # S3SQLInlineComponent(
                # "organisation",
                # name = "partnerns",
                # label = T("Partner National Societies"),
                # fields = ["organisation_id",
                          # "comments",
                          # ],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [9])
            # ),
            # Partner Orgs
            # S3SQLInlineComponent(
                # "organisation",
                # name = "partner",
                # label = T("Partner Organizations"),
                # fields = ["organisation_id",
                          # "comments",
                          # ],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": not_rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [2])
            # ),
            # Donors
            # S3SQLInlineComponent(
                # "organisation",
                # name = "donor",
                # label = T("Donor(s)"),
                # fields = ["organisation_id",
                          # "amount",
                          # "currency"],
                # Filter Organisation by Type
                # filter = ["organisation_id": {"filterby": "organisation_type_id",
                                              # "filterfor": not_rc,
                                              # }],
                # filterby = dict(field = "role",
                                # options = [3])
            # ),
            #"budget",
            #"currency",
            "comments",
            postprocess = postprocess,
        )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "grouped":

                grouped = {"default":
                        {"title": T("Global Report of Projects Status"),
                         "fields": [(T("Project"), "name"),
                                    (T("Program"), "programme.name"),
                                    (T("Donor"), "donor.organisation_id"),
                                    (T("Budget"), "budget.total_budget"),
                                    (T("Location"), "location.location_id"),
                                    "start_date",
                                    "end_date",
                                    ],
                         "orderby": ["name",
                                     ],
                         "aggregate": [("sum", "budget.total_budget"),
                                       ],
                         },
                       }

                from s3 import S3DateFilter, S3OptionsFilter

                filter_widgets = [S3DateFilter("date",
                                               label = T("Time Period"),
                                               hide_time = True,
                                               ),
                                  S3OptionsFilter("programme_project.programme_id",
                                                  label = T("Programs"),
                                                  ),
                                  S3OptionsFilter("theme_project.theme_id",
                                                  label = T("Themes"),
                                                  ),
                                  S3OptionsFilter("sector_project.sector_id",
                                                  label = T("Sectors"),
                                                  ),
                                  S3OptionsFilter("beneficiary.parameter_id",
                                                  label = T("Beneficiaries"),
                                                  ),
                                  S3OptionsFilter("hazard_project.hazard_id",
                                                  label = T("Hazards"),
                                                  ),
                                  ]

                s3db.configure(tablename,
                               filter_widgets = filter_widgets,
                               grouped = grouped,
                               )

            elif r.component:
                if r.component_name == "organisation":
                    component_id = r.component_id
                    if component_id:
                        # No r.component.record :/
                        ctable = s3db.project_organisation
                        crecord = current.db(ctable.id == component_id).select(ctable.role,
                                                                               limitby = (0, 1),
                                                                               ).first()
                        if crecord.role == settings.get_project_organisation_lead_role():
                            ns_only("project_organisation",
                                    required = True,
                                    branches = False,
                                    updateable = True,
                                    )
                            #from s3db.org import org_organisation_requires
                            #ctable.organisation_id.requires = \
                            #    org_organisation_requires(required = True,
                            #                              # Only allowed to add Projects for Orgs
                            #                              # that the user has write access to
                            #                              updateable = True,
                            #                              )

            else:
                # Lead Organisation needs to be an NS (not a branch)
                ns_only(tablename,
                        required = True,
                        branches = False,
                        # default
                        #limit_filter_opts = True,
                        )

                # Set the Host NS filter as Visible so that the default filter works
                filter_widgets = s3db.get_config(tablename, "filter_widgets")
                for widget in filter_widgets:
                    if widget.field == "organisation_id":
                        widget.opts.hidden = False
                        break

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_project_project_controller = customise_project_project_controller

    # -------------------------------------------------------------------------
    #def customise_project_beneficiary_resource(r, tablename):
    #    """
    #        Link Project Beneficiaries to Activity Type
    #    """

    #    if r.interactive and r.component:
    #        if r.tablename == "project_project":
    #            # We are a component of the Project
    #            project_id = r.id
    #        elif r.tablename == "project_location":
    #            # We are a component of the Project Location
    #            project_id = r.record.project_id
    #        else:
    #            # Unknown!
    #            return

    #        db = current.db
    #        s3db = current.s3db

    #        # Filter Activity Type by Sector
    #        ltable = s3db.project_sector_project
    #        rows = db(ltable.project_id == project_id).select(ltable.sector_id)
    #        sectors = [row.sector_id for row in rows]
    #        ltable = s3db.project_activity_type_sector
    #        rows = db(ltable.sector_id.belongs(sectors)).select(ltable.activity_type_id)
    #        filteropts = [row.activity_type_id for row in rows]

    #        def postprocess(form):
    #            # Update project_location.activity_type
    #            beneficiary_id = form.vars.get("id", None)
    #            table = db.project_beneficiary
    #            row = db(table.id == beneficiary_id).select(table.project_location_id,
    #                                                        limitby = (0, 1),
    #                                                        ).first()
    #            if not row:
    #                return
    #            project_location_id = row.project_location_id
    #            if not project_location_id:
    #                return
    #            ltable = db.project_beneficiary_activity_type
    #            row = db(ltable.beneficiary_id == beneficiary_id).select(ltable.activity_type_id,
    #                                                                     limitby = (0, 1),
    #                                                                     ).first()
    #            if not row:
    #                return
    #            activity_type_id = row.activity_type_id
    #            ltable = s3db.project_activity_type_location
    #            query = (ltable.project_location_id == project_location_id) & \
    #                    (ltable.activity_type_id == activity_type_id)
    #            exists = db(query).select(ltable.id,
    #                                      limitby = (0, 1),
    #                                      ).first()
    #            if not exists:
    #                ltable.insert(project_location_id = project_location_id,
    #                              activity_type_id = activity_type_id,
    #                              )

    #        from s3 import S3SQLCustomForm, S3SQLInlineLink
    #        crud_form = S3SQLCustomForm(#"project_id",
    #                                    "project_location_id",
    #                                    S3SQLInlineLink("activity_type",
    #                                                    field = "activity_type_id",
    #                                                    filterby = "id",
    #                                                    options = filteropts,
    #                                                    label = T("Activity Type"),
    #                                                    multiple = False,
    #                                                    ),
    #                                    "parameter_id",
    #                                    "value",
    #                                    "target_value",
    #                                    "date",
    #                                    "end_date",
    #                                    "comments",
    #                                    postprocess = postprocess,
    #                                    )

    #        s3db.configure(tablename,
    #                       crud_form = crud_form,
    #                       )

    #    elif not r.component:
    #        # Report
    #        from s3 import S3OptionsFilter
    #        resource = r.resource
    #        filter_widgets = resource.get_config("filter_widgets")
    #        filter_widgets.insert(1,
    #            S3OptionsFilter("beneficiary_activity_type.activity_type_id",
    #                            label = T("Activity Type"),
    #                            ))
    #        report_options = resource.get_config("report_options")
    #        report_options["rows"].append("beneficiary_activity_type.activity_type_id")
    #        # Same object so would be added twice
    #        #report_options["cols"].append("beneficiary_activity_type.activity_type_id")

    # Only used for activity_types which aren't used by HNRC
    #settings.customise_project_beneficiary_resource = customise_project_beneficiary_resource

    # -------------------------------------------------------------------------
    #def customise_project_indicator_resource(r, tablename):

    #    table = current.s3db.project_indicator
    #    table.definition.label = T("Indicator Definition")
    #    table.measures.label = T("Indicator Criteria")

    #settings.customise_project_indicator_resource = customise_project_indicator_resource

    # -------------------------------------------------------------------------
    def customise_project_indicator_data_resource(r, tablename):

        table = current.s3db.project_indicator_data
        f = table.start_date
        f.readable = f.writable = True
        f.label = T("Start Date")
        table.end_date.label = T("End Date")

        if r.method == "update":
            has_role = current.auth.s3_has_role
            if has_role("monitoring_evaluation") or has_role("ORG_ADMIN"):
                # Normal Access
                return
            # Project Manager
            if r.tablename == "project_indicator_data":
                record_id = r.id
            else:
                record_id = r.component_id
            record = current.db(table.id == record_id).select(table.value,
                                                              limitby = (0, 1),
                                                              ).first()
            if record.value:
                # Redirect to Read-only mode
                # @ToDo: Remove 'Update' button from the read-only page
                from gluon import redirect
                redirect(r.url(method="read"))
            else:
                # Cannot edit anything
                for f in table.fields:
                    table[f].writable = False
                # Except add a Real value
                table.value.writable = True
                # Or Amend the Comments
                table.comments.writable = True

    settings.customise_project_indicator_data_resource = customise_project_indicator_data_resource

    # -------------------------------------------------------------------------
    def customise_project_location_resource(r, tablename):

        s3db = current.s3db
        table = s3db.project_location
        table.name.readable = False
        table.percentage.readable = table.percentage.writable = False
        #ist_fields = s3db.get_config(tablename, "list_fields")
        #try:
        #    list_fields.remove((T("Activity Types"), "activity_type.name"))
        #except:
        #    # Already removed
        #    pass

    settings.customise_project_location_resource = customise_project_location_resource

    # -------------------------------------------------------------------------
    def customise_project_location_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        #standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp (just does same thing but different)
            #if callable(standard_postp):
            #    output = standard_postp(r, output)

            if r.representation == "plain":
                # Map Popup
                from gluon import A, TABLE, TR, TD, B#, URL
                s3db = current.s3db
                table = s3db.project_project
                project_id = r.record.project_id
                resource = s3db.resource("project_project",
                                         id = project_id,
                                         )
                list_fields = ("name",
                               "status_id",
                               "start_date",
                               "end_date",
                               "budget.total_budget",
                               "budget.currency",
                               "hazard_project.hazard_id",
                               "sector_project.sector_id",
                               "theme_project.theme_id",
                               # Contact
                               "human_resource_id",
                               "overall_status_by_indicators",
                               )
                data = resource.select(list_fields, represent=True)
                record = data.rows[0]
                item = TABLE(TR(TD(B("%s:" % table.name.label)),
                                          TD(record["project_project.name"]),
                                          ),
                                       TR(TD(B("%s:" % table.status_id.label)),
                                          TD(record["project_project.status_id"]),
                                          ),
                                       TR(TD(B("%s:" % table.start_date.label)),
                                          TD(record["project_project.start_date"]),
                                          ),
                                       TR(TD(B("%s:" % table.end_date.label)),
                                          TD(record["project_project.end_date"]),
                                          ),
                                       TR(TD(B("%s:" % T("Budget"))),
                                          TD("%s %s" % (record["budget_budget.currency"],
                                                        record["budget_budget.total_budget"])),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_hazard_project.hazard_id.label)),
                                          TD(record["project_hazard_project.hazard_id"]),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_sector_project.sector_id.label)),
                                          TD(record["project_sector_project.sector_id"]),
                                          ),
                                       TR(TD(B("%s:" % s3db.project_theme_project.theme_id.label)),
                                          TD(record["project_theme_project.theme_id"]),
                                          ),
                                       TR(TD(B("%s:" % table.human_resource_id.label)),
                                          TD(record["project_project.human_resource_id"]),
                                          ),
                                       TR(TD(B("%s:" % T("Cumulative Status"))),
                                          TD(record["project_project.overall_status_by_indicators"]),
                                          ),
                                       )
                title = s3.crud_strings["project_project"].title_display
                # Assume authorised to see details
                popup_url = URL(f = "project",
                                args = [project_id],
                                )
                details_btn = A(T("Open"),
                                _href = popup_url,
                                _class = "btn",
                                _id = "details-btn",
                                _target = "_blank",
                                )

                output = {"item": item,
                          "title": title,
                          "details_btn": details_btn,
                          }

            return output

        s3.postp = custom_postp
        return attr

    settings.customise_project_location_controller = customise_project_location_controller

    # -------------------------------------------------------------------------
    def inv_req_approver_update_roles(person_id):
        """
            Update the req_approver role to have the right realms
            # see hrm_certification_onaccept
        """

        db = current.db
        s3db = current.s3db

        # Lookup User Account
        ltable = s3db.pr_person_user
        ptable = s3db.pr_person
        query = (ptable.id == person_id) & \
                (ptable.pe_id == ltable.pe_id)
        user = db(query).select(ltable.user_id,
                                limitby = (0, 1),
                                )
        if not user:
            return

        user_id = user.first().user_id

        # What realms should this user have the req_approver role for?
        table = s3db.inv_req_approver
        rows = db(table.person_id == person_id).select(table.pe_id)
        realms = [row.pe_id for row in rows]

        # Lookup the req_approver group_id
        gtable = db.auth_group
        role = db(gtable.uuid == "req_approver").select(gtable.id,
                                                        limitby = (0, 1),
                                                        ).first()
        group_id = role.id

        # Delete all req_approver roles for this user
        mtable = db.auth_membership
        query = (mtable.user_id == user_id) & \
                (mtable.group_id == group_id)
        db(query).delete()

        # Create required req_approver roles for this user
        for pe_id in realms:
            mtable.insert(user_id = user_id,
                          group_id = group_id,
                          pe_id = pe_id,
                          )

    # -------------------------------------------------------------------------
    def inv_req_approver_onaccept(form):
        """
            Ensure that the Approver has the req_approver role for the correct realms
        """

        person_id = form.vars.get("person_id")
        inv_req_approver_update_roles(person_id)

        if form.record:
            # Update form
            # - has the person changed?
            if form.record.person_id != person_id:
                # Also update the old person
                inv_req_approver_update_roles(form.record.person_id)

    # -------------------------------------------------------------------------
    def inv_req_approver_ondelete(row):

        # Update the req_approver roles for this person
        inv_req_approver_update_roles(row.person_id)

    # -------------------------------------------------------------------------
    def customise_inv_req_approver_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        auth = current.auth

        f = s3db.inv_req_approver.pe_id

        if auth.s3_has_role("ADMIN"):
            # Filter to Red Cross entities

            ttable = s3db.org_organisation_type
            try:
                type_id = db(ttable.name == RED_CROSS).select(ttable.id,
                                                              cache = s3db.cache,
                                                              limitby = (0, 1),
                                                              ).first().id
            except AttributeError:
                # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
                return

            otable = s3db.org_organisation
            btable = s3db.org_organisation_branch
            ltable = db.org_organisation_organisation_type

            rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
            all_rc_organisation_ids = [row.organisation_id for row in rows]
            query = (btable.deleted != True) & \
                    (btable.branch_id.belongs(all_rc_organisation_ids))
            branches = db(query).select(btable.branch_id)
            root_ns_organisation_ids = list(set(all_rc_organisation_ids) - set(row.branch_id for row in branches))
            root_ns = db(otable.id.belongs(root_ns_organisation_ids)).select(otable.pe_id)
            pe_ids = [row.pe_id for row in root_ns]

            # Find all child Orgs/Sites of these
            entity_types = ["org_organisation"] + list(auth.org_site_types.keys())
            from s3db.pr import pr_get_descendants
            child_pe_ids = pr_get_descendants(pe_ids, entity_types=entity_types)

            entities = pe_ids + child_pe_ids

        else:
            # Filter to entities the user has the ORG_ADMIN or logs_manager role for

            # Lookup which realms the user has the roles for
            gtable = db.auth_group
            mtable = db.auth_membership
            query = (mtable.user_id == auth.user.id) & \
                    (mtable.group_id == gtable.id) & \
                    (gtable.uuid.belongs(("ORG_ADMIN", "logs_manager")))

            memberships = db(query).select(mtable.pe_id)
            pe_ids = [m.pe_id for m in memberships]
            if None in pe_ids:
                # Default Realm(s)
                pe_ids.remove(None)
                from s3db.pr import pr_default_realms
                realms = pr_default_realms(auth.user["pe_id"])
                if realms:
                    pe_ids += realms

            # Find all child Orgs/Sites of these
            entity_types = ["org_organisation"] + list(auth.org_site_types.keys())
            from s3db.pr import pr_get_descendants
            child_pe_ids = pr_get_descendants(pe_ids, entity_types=entity_types)

            entities = pe_ids + child_pe_ids
            if len(entities) == 1:
                f.default = entities[0]
                f.readable = f.writable = False
                return

            # Default to NS (most-common use-case)
            otable = s3db.org_organisation
            org = db(otable.id == auth.root_org()).select(otable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            org_pe_id = org.pe_id
            if org_pe_id in entities:
                f.default = org_pe_id

        from s3 import IS_ONE_OF
        from s3db.pr import pr_PersonEntityRepresent
        f.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                               pr_PersonEntityRepresent(show_type = False),
                               filterby = "pe_id",
                               filter_opts = entities,
                               sort = True
                               )

        s3db.configure(tablename,
                       onaccept = inv_req_approver_onaccept,
                       ondelete = inv_req_approver_ondelete,
                       )

    settings.customise_inv_req_approver_resource = customise_inv_req_approver_resource

    # -------------------------------------------------------------------------
    def customise_inv_req_project_resource(r, tablename):
        """
            Customise reponse from options.s3json
        """

        from s3 import IS_ONE_OF#, S3Represent

        s3db = current.s3db
        ptable = s3db.project_project

        project_represent = S3Represent(lookup = "project_project",
                                        fields = ["code"],
                                        )
        query = ((ptable.end_date == None) | \
                 (ptable.end_date > r.utcnow)) & \
                (ptable.deleted == False)
        the_set = current.db(query)
        f = s3db.inv_req_project.project_id
        f.represent = project_represent
        f.requires = IS_ONE_OF(the_set, "project_project.id",
                               project_represent,
                               sort = True,
                               )

    settings.customise_inv_req_project_resource = customise_inv_req_project_resource

    # -------------------------------------------------------------------------
    def inv_req_onaccept(form):
        """
            Update realm if site_id changes
            - Lighter then using update_realm on every update (this is much rarer edge case))
            - Can hardcode the component handling
        """

        record = form.record
        if record:
            # Update form
            form_vars = form.vars
            req_id = form_vars.id
            db = current.db
            table = db.inv_req
            site_id = form_vars.get("site_id")
            if not site_id:
                req = db(table.id == req_id).select(table.site_id,
                                                    limitby = (0, 1),
                                                    ).first()
                site_id = req.site_id
            if site_id != record.site_id:
                get_realm_entity = current.auth.get_realm_entity
                req_realm_entity = get_realm_entity(table, record)
                db(table.id == req_id).update(realm_entity = req_realm_entity)
                # Update Request Items
                ritable = current.s3db.inv_req_item
                req_items = db(ritable.req_id == req_id).select(ritable.id,
                                                                ritable.site_id,
                                                                )
                site_ids = {}
                for row in req_items:
                    site_id = row.site_id
                    if site_id in site_ids:
                        site_ids[site_id].append(row.id)
                    else:
                        site_ids[site_id] = [row.id]
                req_site_id = record.site_id
                same_as_req = site_ids.get(None, []) + site_ids.get(req_site_id, [])
                same_as_req_len = len(same_as_req)
                if same_as_req_len:
                    if same_as_req_len == 1:
                        db(ritable.id == same_as_req[0]).update(realm_entity = req_realm_entity)
                    else:
                        db(ritable.id.belongs(same_as_req)).update(realm_entity = req_realm_entity)
                    if None in site_ids:
                        del site_ids[None]
                    if req_site_id in site_ids:
                        del site_ids[req_site_id]
                for site_id in site_ids:
                    req_item_ids = site_ids[site_id]
                    req_item_id = req_item_ids[0]
                    realm_entity = get_realm_entity(ritable, {"id": req_item_id,
                                                              "site_id": site_id,
                                                              "req_id": record.id,
                                                              })
                    if len(req_item_ids) == 1:
                        db(ritable.id == req_item_id).update(realm_entity = realm_entity)
                    else:
                        db(ritable.id.belongs(req_item_ids)).update(realm_entity = realm_entity)

    # -------------------------------------------------------------------------
    def on_req_approve(req_id):
        """
            Remove Dashboard Alert
        """

        s3db = current.s3db
        ntable = s3db.auth_user_notification
        query = (ntable.user_id == current.auth.user.id) & \
                (ntable.type == "req_approve") & \
                (ntable.record_id == req_id)

        auth = current.auth
        override_default = auth.override
        auth.override = True
        resource = s3db.resource("auth_user_notification", filter = query)
        resource.delete()
        auth.override = override_default

    # -------------------------------------------------------------------------
    def on_req_approved(req_id, record, site_ids):
        """
            Notify the Warehouse Operator(s)
            - Email
            - Dashboard Alert
        """

        #from gluon import URL
        from s3 import s3_str, S3DateTime
        from .controllers import inv_operators_for_sites

        T = current.T
        db = current.db
        s3db = current.s3db
        session_s3 = current.session.s3
        ui_language = session_s3.language

        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="inv", f="req",
                            args = [req_id, "req_item"],
                            ))
        req_ref = record.req_ref
        date_required = record.date_required
        date_represent = S3DateTime.date_represent # We want Dates not datetime which table.date_required uses
        send_email = current.msg.send_by_pe_id
        subject_T = T("Request Approved for Items from your Warehouse")
        message_T = T("A new Request, %(reference)s, has been Approved for shipment from %(site)s by %(date_required)s. Please review at: %(url)s")
        alert_T = T("Request %(reference)s for items from %(site)s by %(date_required)s")

        insert = s3db.auth_user_notification.insert
        sites = inv_operators_for_sites(site_ids)

        for site_id in sites:
            site = sites[site_id]
            site_name = site["name"]
            # Send Localised Alerts & Mail(s)
            languages = {}
            operators = site["operators"]
            for row in operators:
                language = row["auth_user.language"]
                if language not in languages:
                    languages[language] = []
                languages[language].append((row["pr_person_user.pe_id"], row["pr_person_user.user_id"]))
            for language in languages:
                T.force(language)
                session_s3.language = language # for date_represent
                date = date_represent(date_required)
                subject = "%s: %s" % (s3_str(subject_T), req_ref)
                message = s3_str(message_T) % {"date_required": date,
                                               "reference": req_ref,
                                               "site": site_name,
                                               "url": url,
                                               }
                alert = s3_str(alert_T) % {"date_required": date,
                                           "reference": req_ref,
                                           "site": site_name,
                                           }

                users = languages[language]
                for user in users:
                    send_email(user[0],
                               subject = subject,
                               message = message,
                               )
                    insert(user_id = user[1],
                           name = alert,
                           url = url,
                           type = "req_fulfil",
                           tablename = "inv_req",
                           record_id = req_id,
                           )

        # Restore language for UI
        session_s3.language = ui_language
        T.force(ui_language)

    # -------------------------------------------------------------------------
    def on_req_submit(req_id, record, site, approvers):
        """
            Notify the Approvers
            - Email
            - Dashboard Alert
        """

        #from gluon import URL
        from s3 import s3_fullname, s3_str, S3DateTime

        T = current.T
        db = current.db
        s3db = current.s3db
        session_s3 = current.session.s3
        ui_language = session_s3.language

        url = "%s%s" % (settings.get_base_public_url(),
                        URL(c="inv", f="req",
                            args = [req_id],
                            ))
        req_ref = record.req_ref
        date_required = record.date_required
        date_represent = S3DateTime.date_represent # We want Dates not datetime which table.date_required uses
        requester = s3_fullname(record.requester_id)
        site_name = site.name
        send_email = current.msg.send_by_pe_id
        subject_T = T("Request submitted for Approval")
        message_T = T("A new Request, %(reference)s, has been submitted for Approval by %(person)s for delivery to %(site)s by %(date_required)s. Please review at: %(url)s")
        alert_T = T("A new Request, %(reference)s, has been submitted for Approval by %(person)s for delivery to %(site)s by %(date_required)s")

        insert = s3db.auth_user_notification.insert

        # Send Localised Alerts & Mail(s)
        languages = {}
        for row in approvers:
            language = row["auth_user.language"]
            if language not in languages:
                languages[language] = []
            languages[language].append((row["pr_person_user.pe_id"], row["pr_person_user.user_id"]))
        for language in languages:
            T.force(language)
            session_s3.language = language # for date_represent
            date = date_represent(date_required)
            subject = "%s: %s" % (s3_str(subject_T), req_ref)
            message = s3_str(message_T) % {"date_required": date_represent(date_required),
                                           "reference": req_ref,
                                           "person": requester,
                                           "site": site_name,
                                           "url": url,
                                           }
            alert = s3_str(alert_T) % {"date_required": date,
                                       "reference": req_ref,
                                       "person": requester,
                                       "site": site_name,
                                       }

            users = languages[language]
            for user in users:
                send_email(user[0],
                           subject = subject,
                           message = message,
                           )
                insert(user_id = user[1],
                       name = alert,
                       url = url,
                       type = "req_approve",
                       tablename = "inv_req",
                       record_id = req_id,
                       )

        # Restore language for UI
        session_s3.language = ui_language
        T.force(ui_language)

    # -------------------------------------------------------------------------
    def customise_inv_req_resource(r, tablename):

        from gluon import IS_NOT_EMPTY
        from s3db.inv import inv_ReqRefRepresent

        auth = current.auth
        s3db = current.s3db

        table = s3db.inv_req

        # Use Custom Represent for Sites
        from .controllers import org_SiteRepresent
        table.site_id.requires.label = org_SiteRepresent()

        f = table.req_ref
        f.represent = inv_ReqRefRepresent(show_link = True,
                                          pdf = True,
                                          )
        f.requires = IS_NOT_EMPTY()
        f.widget = None
        table.priority.readable = table.priority.writable = False
        table.date.label = T("Date of Issue")
        table.date_required.label = T("Requested Delivery Date")
        table.site_id.label = T("Deliver To")

        LOGS_ADMIN = auth.s3_has_roles(("ORG_ADMIN",
                                        "wh_operator",
                                        "logs_manager",
                                        ))
        if not LOGS_ADMIN:
            table.requester_id.writable = False

        MINE = r.get_vars.get("mine")

        if r.tablename == tablename:
            if MINE:
                # Filter
                from s3 import FS
                r.resource.add_filter(FS("requester_id") == auth.s3_logged_in_person())

            from gluon import IS_EMPTY_OR#, IS_IN_SET
            from s3 import IS_ONE_OF, S3GroupedOptionsWidget, S3SQLCustomForm, S3SQLInlineComponent#, S3Represent
            from s3layouts import S3PopupLink

            db = current.db

            # Link to Projects
            # NB Whilst the requester can only select valid Project Codes for their NS, we do NOT use this as a filter for destination.
            ptable = s3db.project_project
            project_represent = S3Represent(lookup = "project_project",
                                            fields = ["code"],
                                            )
            query = ((ptable.end_date == None) | \
                     (ptable.end_date > r.utcnow)) & \
                    (ptable.deleted == False)
            the_set = db(query)
            f = s3db.inv_req_project.project_id
            f.label = T("Project Code")
            f.requires = IS_ONE_OF(the_set, "project_project.id",
                                   project_represent,
                                   sort = True,
                                   )
            f.comment = S3PopupLink(c = "inv",
                                    f = "project",
                                    label = T("Create Project"),
                                    tooltip = T("If you don't see the project in the list, you can add a new one by clicking link 'Create Project'."),
                                    vars = {"caller": "inv_req_sub_project_req_project_id",
                                            "parent": "req_project",
                                            },
                                    )

            crud_fields = [f for f in table.fields if table[f].readable]
            crud_fields.insert(0, "req_project.project_id")

            req_id = r.id
            if req_id:
                # Never opens in Component Tab, always breaks out
                atable = s3db.inv_req_approver_req
                approved = db(atable.req_id == req_id).select(atable.id,
                                                              limitby = (0, 1),
                                                              )
                if approved:
                    crud_fields.insert(-1, S3SQLInlineComponent("approver",
                                                                name = "approver",
                                                                label = T("Approved By"),
                                                                fields = [("", "person_id"),
                                                                          ("", "title"),
                                                                          ],
                                                                readonly = True,
                                                                ))
                if r.method == "read" or \
                   r.record.workflow_status in (3, 4, 5) or \
                   not auth.s3_has_permission("update",
                                              r.table,
                                              record_id = req_id,
                                              ):
                    # Read-only form
                    if r.record.transport_req:
                        transport_type = True
                    else:
                        transport_type = False
                else:
                    # Update form
                    transport_type = True
            else:
                # Create form
                transport_type = True

            if transport_type:
                # Filtered components
                s3db.add_components("inv_req",
                                    inv_req_tag = ({"name": "transport_type",
                                                    "joinby": "req_id",
                                                    "filterby": {"tag": "transport_type"},
                                                    "multiple": False,
                                                    },
                                                    ),
                                    )

                # Individual settings for specific tag components
                components_get = s3db.resource(tablename).components.get

                transport_type = components_get("transport_type")
                f = transport_type.table.value
                f.requires = IS_EMPTY_OR(IS_IN_SET(transport_opts))
                from s3 import s3_options_represent
                f.represent = s3_options_represent(transport_opts)
                f.widget = S3GroupedOptionsWidget(options = transport_opts,
                                                  multiple = False,
                                                  cols = 4,
                                                  sort = False,
                                                  )
                insert_index = crud_fields.index("transport_req") + 1
                crud_fields.insert(insert_index, ("", "transport_type.value"))

                s3 = current.response.s3
                s3.jquery_ready.append('''S3.showHidden('%s',%s,'%s')''' % \
                    ("transport_req", json.dumps(["sub_transport_type_value"], separators=SEPARATORS), "inv_req"))

            crud_form = S3SQLCustomForm(*crud_fields)
            s3db.configure(tablename,
                           crud_form = crud_form,
                           )

            # Custom Request Form
            from .forms import inv_req_form
            s3db.set_method("inv", "req",
                            method = "form",
                            action = inv_req_form,
                            )

        from s3 import S3OptionsFilter
        filter_widgets = [S3OptionsFilter("workflow_status",
                                          cols = 3,
                                          ),
                          ]

        list_fields = ["req_ref",
                       "req_project.project_id",
                       "date",
                       "site_id",
                       (T("Details"), "details"),
                       "workflow_status",
                       #"commit_status",
                       "transit_status",
                       "fulfil_status",
                       ]
        if LOGS_ADMIN and not MINE:
            list_fields.insert(2, "date_required")
            list_fields.insert(4, "requester_id")

            #filter_widgets += [
            #                   ]

        s3db.add_custom_callback(tablename,
                                 "onaccept",
                                 inv_req_onaccept,
                                 )

        s3db.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       on_req_approve = on_req_approve,
                       on_req_approved = on_req_approved,
                       on_req_submit = on_req_submit,
                       )

    settings.customise_inv_req_resource = customise_inv_req_resource

    # -------------------------------------------------------------------------
    def customise_inv_req_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
                if not result:
                    return False

            req_id = r.id
            if not req_id:
                current.s3db.inv_req_project.project_id.represent = S3Represent(lookup = "project_project",
                                                                                fields = ["code"],
                                                                                )
            elif not r.component:
                if r.record.workflow_status in (3, 4, 5): # Approved, Completed, Cancelled
                    # Lookup PE of Project Code
                    s3db = current.s3db
                    ltable = s3db.inv_req_project
                    ptable = s3db.project_project
                    otable = s3db.org_organisation
                    query = (ltable.req_id == req_id) & \
                            (ltable.project_id == ptable.id) & \
                            (ptable.organisation_id == otable.id)
                    org = current.db(query).select(otable.pe_id,
                                                   limitby = (0, 1),
                                                   ).first()
                    if current.auth.s3_has_roles(("logs_manager",
                                                  "logs_manager_national",
                                                  ),
                                                 for_pe = org.pe_id,
                                                 ):
                        # Allow editing of the Project Code
                        s3db.configure("inv_req",
                                       editable = True,
                                       )
                        table = s3db.inv_req
                        for fname in table.fields:
                            table[fname].writable = False

                        table.site_id.comment = None
                        table.requester_id.comment = None
                        table.recv_by_id.comment = None

            elif r.component_name == "req_item":
                s3db = current.s3db
                workflow_status = r.record.workflow_status
                if workflow_status == 2: # Submitted for Approval
                    show_site_and_po = True
                    # Are we a Logistics Approver?
                    from s3db.inv import inv_req_approvers
                    approvers = inv_req_approvers(r.record.site_id)
                    person_id = current.auth.s3_logged_in_person()
                    if person_id in approvers and approvers[person_id]["matcher"]:
                        # Have we already approved?
                        atable = s3db.inv_req_approver_req
                        query = (atable.req_id == req_id) & \
                                (atable.person_id == person_id)
                        approved = current.db(query).select(atable.id,
                                                            limitby = (0, 1),
                                                            )
                        if not approved:
                            # Allow User to Match
                            settings.inv.req_prompt_match = True
                elif workflow_status == 3: # Approved
                    show_site_and_po = True
                else:
                    show_site_and_po = False

                if show_site_and_po:
                    # Show in read-only form
                    r.component.table.site_id.readable = True

                    # Show in list_fields
                    oitable = s3db.inv_order_item
                    def inv_order_item_represent(record_id):
                        """
                            Probably few enough Request Items not to need an S3Represent sub-class
                        """
                        if record_id == None:
                            return T("Not being Purchased")
                        else:
                            order_item = current.db(oitable.id == record_id).select(oitable.purchase_ref,
                                                                                    limitby = (0, 1),
                                                                                    ).first()
                            return order_item.purchase_ref or T("Not yet entered")

                    oitable.id.represent = inv_order_item_represent
                    order_label = T("%(PO)s Number") % \
                                    {"PO": settings.get_proc_shortname()}

                    list_fields = ["item_id",
                                   "item_pack_id",
                                   "site_id",
                                   (order_label, "order_item.id"),
                                   "quantity",
                                   "quantity_reserved",
                                   "quantity_transit",
                                   "quantity_fulfil",
                                   ]
                    r.component.configure(list_fields = list_fields)

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_inv_req_controller = customise_inv_req_controller

    # -------------------------------------------------------------------------
    def inv_req_item_onaccept(form):
        """
            Update realm's affiliations if site_id changes
        """

        record = form.record
        if record:
            # Update form
            form_vars_get = form.vars.get
            site_id = form_vars_get("site_id")
            if site_id and site_id != record.site_id:
                # Item has been Requested from a specific site
                # Update the Request's Realm
                req_id = form_vars_get("req_id")
                db = current.db
                table = db.inv_req
                req = db(table.id == req_id).select(table.id,
                                                    table.site_id,
                                                    limitby = (0, 1),
                                                    ).first()
                get_realm_entity = current.auth.get_realm_entity
                req_realm_entity = get_realm_entity(table, record)
                db(table.id == req_id).update(realm_entity = req_realm_entity)
                # Update Realm of the Request Item
                if site_id == req.site_id:
                    db(current.s3db.inv_req_item.id == form_vars_get("id")).update(realm_entity = req_realm_entity)
                else:
                    req_item_id = form_vars_get("id")
                    ritable = current.s3db.inv_req_item
                    realm_entity = get_realm_entity(ritable, {"id": req_item_id,
                                                              "site_id": site_id,
                                                              "req_id": req_id,
                                                              })
                    db(ritable.id == req_item_id).update(realm_entity = realm_entity)

    # -------------------------------------------------------------------------
    def customise_inv_req_item_resource(r, tablename):

        current.s3db.add_custom_callback(tablename,
                                         "onaccept",
                                         inv_req_item_onaccept,
                                         )

    settings.customise_inv_req_item_resource = customise_inv_req_item_resource

    # -------------------------------------------------------------------------
    def customise_inv_stock_card_controller(**attr):

        s3 = current.response.s3

        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):

            if r.representation == "pdf":
                from .forms import stock_card
                output = stock_card(r, **attr)
            else:
                # Call standard postp
                if callable(standard_postp):
                    output = standard_postp(r, output)

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_inv_stock_card_controller = customise_inv_stock_card_controller

    # -------------------------------------------------------------------------
    def customise_supply_item_category_resource(r, tablename):

        from s3db.supply import supply_ItemCategoryRepresent

        s3db = current.s3db

        table = s3db.supply_item_category
        #root_org = current.auth.root_org_name()
        #if root_org == HNRC:
        # Not using Assets Module
        table.can_be_asset.readable = table.can_be_asset.writable = False
        table.parent_item_category_id.represent = supply_ItemCategoryRepresent(show_catalog = False,
                                                                               use_code = False,
                                                                               )

    settings.customise_supply_item_category_resource = customise_supply_item_category_resource

    # -------------------------------------------------------------------------
    def customise_supply_item_resource(r, tablename):

        from s3db.supply import supply_ItemCategoryRepresent

        s3db = current.s3db

        table = s3db.supply_item
        table.brand.readable = table.brand.writable = False
        table.model.readable = table.model.writable = False
        table.year.readable = table.year.writable = False
        table.length.readable = table.length.writable = False
        table.width.readable = table.width.writable = False
        table.height.readable = table.height.writable = False
        table.item_category_id.represent = supply_ItemCategoryRepresent(show_catalog = False,
                                                                        use_code = False,
                                                                        )

        if r.tablename == tablename:
            # Brand & Year not used
            r.resource.configure(filter_widgets = None)

    settings.customise_supply_item_resource = customise_supply_item_resource

# END =========================================================================