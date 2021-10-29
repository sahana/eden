# -*- coding: utf-8 -*-

"""
    Application Template for supporting Evacuations of Personnel
    - e.g. from Afghanistan
"""

from gluon import current
from gluon.storage import Storage

# =============================================================================
def config(settings):

    T = current.T

    #settings.base.system_name = "Evacuation Management System"
    #settings.base.system_name_short =  "EMS"
    settings.base.system_name = "Afghans Extraction"
    settings.base.system_name_short =  "AFGEx"

    # PrePopulate data
    settings.base.prepopulate = ["default/base",
                                 "BRCMS/Evac",
                                 ]
    #settings.base.prepopulate_demo.append("BRCMS/Evac/Demo")

    # Custom Models
    settings.base.custom_models = {"dissemination": "BRCMS.Evac",
                                   }

    # Enable password-retrieval feature
    settings.auth.password_retrieval = True

    settings.auth.registration_organisation_required = True
    settings.auth.realm_entity_types = ("org_organisation",
                                        "pr_forum",  # Realms
                                        "pr_person", # Case Managers, Case Supervisors, Handlers
                                        # Not needed, as hidden?
                                        #"pr_realm",  # Cases, Resources
                                        )

    # Enable extra Modules
    modules = settings.modules
    modules["asset"] = {"name_nice": T("Assets"), "module_type": None}
    modules["dissemination"] = {"name_nice": T("Dissemination"), "module_type": None}
    modules["fin"] = {"name_nice": T("Finances"), "module_type": None}
    modules["inv"] = {"name_nice": T("Inventory"), "module_type": None}
    modules["med"] = {"name_nice": T("Hospitals"), "module_type": None}
    modules["security"] = {"name_nice": T("Security"), "module_type": None}
    modules["supply"] = {"name_nice": T("Supply"), "module_type": None}
    modules["transport"] = {"name_nice": T("Transport"), "module_type": None}

    # -------------------------------------------------------------------------
    # BR Settings
    #
    settings.br.case_activity_need_details = True
    settings.br.case_activity_updates = True
    settings.br.case_activity_documents = True
    settings.br.case_activity_urgent_option = True
    settings.br.case_address = True
    settings.br.case_id_tab = True
    settings.br.case_language_details = False
    settings.br.case_notes_tab = True
    settings.br.id_card_export_roles = None
    settings.br.manage_assistance = False
    settings.br.needs_org_specific = False

    settings.L10n.ethnicity = {"Achakzai": "Achakzai",
                               "Afshar": "Afshar",
                               "Aimaq": "Aimaq (Jamshidi, Taimuri, Firozkohi, Taimani)",
                               "Arab": "Arab",
                               "Baloch": "Baloch",
                               "Brahui": "Brahu'i/Brahvi",
                               "Gujjar": "Gujjar",
                               "Hazara": "Hazara",
                               "Kazakh": "Kazakh (Karakalpak)",
                               "Kyrgyz": "Kyrgyz",
                               "Mongol": "Moghol/Mongol",
                               "Nuristani": "Nuristani",
                               "Pamiri": "Pamiri (Vakti, Munjani, Yidgha, Ishkashim, Shugni, Sangleji, Sarikuli)",
                               "Parsiwan": "Parsiwan",
                               "Pashai": "Pasha'i",
                               "Pashtun": "Pashtun",
                               "Qizilbash": "Qizilbash",
                               "Sadat": "Sadat",
                               "Sayyid": "Sayyid",
                               "Tajik": "Tajik",
                               "Turkmen": "Turkmen",
                               "Uzbek": "Uzbek",
                               }

    # -------------------------------------------------------------------------
    # CR Settings
    #
    settings.cr.people_registration = True

    # -------------------------------------------------------------------------
    # HRM Settings
    #
    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.teams = False # Working Groups use Forums
    settings.hrm.use_address = False
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    # INV Settings
    #
    settings.inv.direct_stock_edits = True

    # -------------------------------------------------------------------------
    # Organisations Module Settings
    #
    settings.org.sector = False
    settings.org.branches = False
    settings.org.offices_tab = False
    settings.org.country = False

    WORKING_GROUPS = ("FLIGHTS",
                      "LEGAL",
                      "LOGISTICS",
                      "MEDICAL",
                      "SECURITY",
                      )

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def evac_realm_entity(table, row):
        """
            Assign a Realm Entity to records
            
            Cases all have a unique Realm
            Resources all have a unique Realm
            - other than:
                * Orgs
                * Staff

            Special Cases for Doctors (both a Case & a Resource!)
        """

        from s3dal import original_tablename

        tablename = original_tablename(table)

        if tablename == "br_case":
            # Has a unique pr_realm with appropriate multiple inheritance
            # - handled by crud_form.postprocess
            return None
        elif tablename == "br_case_activity":
            # Has a unique pr_realm with appropriate multiple inheritance
            # - handled by onaccept
            return None
        elif tablename == "pr_person":
            # Is this a Case or Staff?
            db = current.db
            s3db = current.s3db
            person_id = row.id

            # Try Case 1st (we expect more of these)
            ctable = s3db.br_case
            case = db(ctable.person_id == person_id).select(ctable.realm_entity,
                                                            limitby = (0, 1),
                                                            ).first()
            if case:
                # => Inherit from Case
                return case.realm_entity

            # Try Staff 2nd (we expect less of these)
            htable = s3db.hrm_human_resource
            otable = s3db.org_organisation
            query = (htable.person_id == person_id) & \
                    (htable.organisation_id == otable.id)
            org = db(query).select(otable.pe_id,
                                   limitby = (0, 1),
                                   ).first()
            if org:
                # => Inherit from Org
                return org.pe_id

            # Hmm, what kind of person could this be?
            current.log.warning("Person %s is neither Case nor Staff...using default rules" % person_id)
            # => use Default Rules
            return 0
        elif tablename == "gis_route":
            # Inherits realm from the Case
            # @ToDo
            pass
        elif tablename in ("fin_bank",
                           "med_hospital",
                           "med_pharmacy",
                           "transport_airport",
                           "transport_airplane",
                           ):
            # No Realm 
            return None
        elif tablename in ("cr_shelter",
                           "event_incident_report",
                           "fin_broker",
                           "med_contact",
                           "inv_inv_item",
                           "inv_warehouse",
                           "security_checkpoint",
                           "security_zone",
                           "transport_flight",
                           ):
            # Has a unique pr_realm with appropriate multiple inheritance
            # => Leave this to disseminate (called from crud_form.postprocess)
            return None
        elif tablename == "transport_flight_manifest":
            # Inherit from passenger
            ptable = current.s3db.pr_person
            person = current.db(ptable.id == row.person_id).select(ptable.realm_entity,
                                                                   limitby = (0, 1),
                                                                   ).first()
            return person.realm_entity
        elif tablename == "org_organisation":
            # Realm is own PE ID
            # => use Default Rules
            return 0

        # Use default rules
        realm_entity = 0

        return realm_entity

    settings.auth.realm_entity = evac_realm_entity

    # -------------------------------------------------------------------------
    def auth_add_role(user_id, group_id, for_pe=None):
        """
            Automatically add subsidiary roles & set to appropriate entities
        """

        auth = current.auth
        add_membership = auth.add_membership
        system_roles = auth.get_system_roles()

        # Is this the Admin role?
        if group_id == system_roles.ADMIN:
            # Add the main Role
            add_membership(group_id = group_id,
                           user_id = user_id,
                           )
            # No Subsidiary Roles to add
            return

        db = current.db
        s3db = current.s3db
        gtable = db.auth_group

        # Is this the OrgAdmin role?
        if group_id == system_roles.ORG_ADMIN:
            # Lookup the User Organisation
            utable = db.auth_user
            otable = s3db.org_organisation
            query = (utable.id == user_id) & \
                    (otable.id == utable.organisation_id)
            org = db(query).select(otable.id,
                                   otable.pe_id,
                                   limitby = (0, 1),
                                   ).first()

            # Lookup the Entity for the main role
            if for_pe:
                entity = for_pe
            else:
                entity = org.pe_id

            # Add the main Role for the correct entity
            add_membership(group_id = group_id,
                           user_id = user_id,
                           entity = entity,
                           )

            # Lookup the Groups for the subsidiary roles
            groups = db(gtable.uuid.belongs(("ORG_ADMIN_RO",
                                             "ORG_ADMIN_RW",
                                             ))).select(gtable.id,
                                                        gtable.uuid,
                                                        limitby = (0, 2),
                                                        )
            groups = {row.uuid: row.id for row in groups}
            # Lookup the Entities for the subsidiary roles
            organisation_id = org.id
            ftable = s3db.pr_forum
            forums = db(ftable.uuid.belongs(("ORG_ADMIN_RO_%s" % organisation_id,
                                             "ORG_ADMIN_RW_%s" % organisation_id,
                                             ))).select(ftable.pe_id,
                                                        ftable.uuid,
                                                        limitby = (0, 2),
                                                        )
            forums = {row.uuid: row.pe_id for row in forums}
            # Add User to the subsidiary roles for the subsidiary entities
            for uuid in groups:
                add_membership(group_id = groups[uuid],
                               user_id = user_id,
                               entity = forums["%s_%s" % (uuid,
                                                          organisation_id,
                                                          )],
                               )
            return

        # Need to lookup the role
        group = db(gtable.id == group_id).select(gtable.uuid,
                                                 limitby = (0, 1),
                                                 ).first()
        role = group.uuid
        if role == "ORG_MEMBER":
            # Lookup the Entity for the main role
            if for_pe:
                entity = for_pe
            else:
                utable = db.auth_user
                otable = s3db.org_organisation
                query = (utable.id == user_id) & \
                        (otable.id == utable.organisation_id)
                org = db(query).select(otable.pe_id,
                                       limitby = (0, 1),
                                       ).first()
                entity = org.pe_id

            # Add the main Role for the correct entity
            add_membership(group_id = group_id,
                           user_id = user_id,
                           entity = entity,
                           )
            # No Subsidiary Roles to add
            return

        # Lookup the Entity for the main role
        if for_pe:
            entity = for_pe
        else:
            ltable = s3db.pr_person_user
            person = db(ltable.user_id == user_id).select(ltable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            entity = person.pe_id

        # Add the main Role for the correct entity
        add_membership(group_id = group_id,
                       user_id = user_id,
                       entity = entity,
                       )

        # Lookup the Group for the Org Member role
        group = db(gtable.uuid == "ORG_MEMBER").select(gtable.id,
                                                       limitby = (0, 1),
                                                       ).first()
        # Lookup the Entity for the Org Member role
        utable = db.auth_user
        otable = s3db.org_organisation
        query = (utable.id == user_id) & \
                (otable.id == utable.organisation_id)
        org = db(query).select(otable.pe_id,
                               limitby = (0, 1),
                               ).first()
        # Add User to the Org Member role for the Org entity
        add_membership(group_id = group.id,
                       user_id = user_id,
                       entity = org.pe_id,
                       )

        if role in ("CASE_MANAGER",
                    "CASE_SUPERVISOR",
                    ):
            # No extra subsidiary role
            return

        # Resource role

        # Lookup the Groups for the subsidiary roles
        groups = db(gtable.uuid.belongs(("%s_RO" % role,
                                         "%s_RW" % role,
                                         ))).select(gtable.id,
                                                    gtable.uuid,
                                                    limitby = (0, 2),
                                                    )
        groups = {row.uuid: row.id for row in groups}
        # Lookup the Entities for the subsidiary roles
        organisation_id = org.id
        ftable = s3db.pr_forum
        forums = db(ftable.uuid.belongs(("%s_RO_%s" % (role,
                                                       organisation_id,
                                                       ),
                                         "%s_RW_%s" % (role,
                                                       organisation_id,
                                                       ),
                                         ))).select(ftable.pe_id,
                                                    ftable.uuid,
                                                    limitby = (0, 2),
                                                    )
        forums = {row.uuid: row.pe_id for row in forums}
        # Add User to the subsidiary roles for the subsidiary entities
        for uuid in groups:
            add_membership(group_id = groups[uuid],
                           user_id = user_id,
                           entity = forums["%s_%s" % (uuid,
                                                      organisation_id,
                                                      )],
                           )

    settings.auth.add_role = auth_add_role

    # -------------------------------------------------------------------------
    def auth_remove_role(user_id, group_id, for_pe=None):
        """
            Automatically remove subsidiary roles
        """

        auth = current.auth
        withdraw_role = auth.s3_withdraw_role

        auth = current.auth
        add_membership = auth.add_membership
        system_roles = auth.get_system_roles()

        # Is this the Admin role?
        if group_id == system_roles.ADMIN:
            # Remove the main Role
            withdraw_role(user_id, group_id)
            # No Subsidiary Roles to remove
            return

        db = current.db
        s3db = current.s3db
        gtable = db.auth_group

        # Is this the OrgAdmin role?
        if group_id == system_roles.ORG_ADMIN:
            # Lookup the User Organisation
            utable = db.auth_user
            otable = s3db.org_organisation
            query = (utable.id == user_id) & \
                    (otable.id == utable.organisation_id)
            org = db(query).select(otable.id,
                                   otable.pe_id,
                                   limitby = (0, 1),
                                   ).first()

            # Lookup the Entity for the main role
            if for_pe:
                entity = for_pe
            else:
                entity = org.pe_id

            # Remove the main Role for the correct entity
            withdraw_role(user_id, group_id, entity)

            # Lookup the Groups for the subsidiary roles
            groups = db(gtable.uuid.belongs(("ORG_ADMIN_RO",
                                             "ORG_ADMIN_RW",
                                             ))).select(gtable.id,
                                                        gtable.uuid,
                                                        limitby = (0, 2),
                                                        )
            groups = {row.uuid: row.id for row in groups}
            # Lookup the Entities for the subsidiary roles
            organisation_id = org.id
            ftable = s3db.pr_forum
            forums = db(ftable.uuid.belongs(("ORG_ADMIN_RO_%s" % organisation_id,
                                             "ORG_ADMIN_RW_%s" % organisation_id,
                                             ))).select(ftable.pe_id,
                                                        ftable.uuid,
                                                        limitby = (0, 2),
                                                        )
            forums = {row.uuid: row.pe_id for row in forums}
            # Remove User from the subsidiary roles for the subsidiary entities
            for uuid in groups:
                withdraw_role(user_id,
                              groups[uuid],
                              forums["%s_%s" % (uuid,
                                                organisation_id,
                                                )],
                              )
            return

        # Need to lookup the role
        group = db(gtable.id == group_id).select(gtable.uuid,
                                                 limitby = (0, 1),
                                                 ).first()
        role = group.uuid
        if role == "ORG_MEMBER":
            # Lookup the Entity for the main role
            if for_pe:
                entity = for_pe
            else:
                utable = db.auth_user
                otable = s3db.org_organisation
                query = (utable.id == user_id) & \
                        (otable.id == utable.organisation_id)
                org = db(query).select(otable.pe_id,
                                       limitby = (0, 1),
                                       ).first()
                entity = org.pe_id

            # Remove the main Role for the correct entity
            withdraw_role(user_id, group_id, entity)
            # No Subsidiary Roles to remove
            return

        # Lookup the Entity for the main role
        if for_pe:
            entity = for_pe
        else:
            ltable = s3db.pr_person_user
            person = db(ltable.user_id == user_id).select(ltable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            entity = person.pe_id

        # Remove the main Role for the correct entity
        withdraw_role(user_id, group_id, entity)

        if role in ("CASE_MANAGER",
                    "CASE_SUPERVISOR",
                    ):
            # No extra subsidiary role
            return

        # Resource role

        # Lookup the Groups for the subsidiary roles
        groups = db(gtable.uuid.belongs(("%s_RO" % role,
                                         "%s_RW" % role,
                                         ))).select(gtable.id,
                                                    gtable.uuid,
                                                    limitby = (0, 2),
                                                    )
        groups = {row.uuid: row.id for row in groups}
        # Lookup the Entities for the subsidiary roles
        organisation_id = org.id
        ftable = s3db.pr_forum
        forums = db(ftable.uuid.belongs(("%s_RO_%s" % (role,
                                                       organisation_id,
                                                       ),
                                         "%s_RW_%s" % (role,
                                                       organisation_id,
                                                       ),
                                         ))).select(ftable.pe_id,
                                                    ftable.uuid,
                                                    limitby = (0, 2),
                                                    )
        forums = {row.uuid: row.pe_id for row in forums}
        # Add User to the subsidiary roles for the subsidiary entities
        for uuid in groups:
            withdraw_role(user_id,
                          groups[uuid],
                          forums["%s_%s" % (uuid,
                                            organisation_id,
                                            )],
                          )

    settings.auth.remove_role = auth_remove_role

    # =========================================================================
    def br_case_activity_create_onaccept(form):
        """
            * Have a Realm for the Activity
              - ensure the correct Inheritance
            * Create a Task for the Assignment
        """

        db = current.db
        s3db = current.s3db

        form_vars = form.vars
        activity_id = form_vars.id

        # Create a pr_realm record
        rtable = s3db.pr_realm
        realm_id = rtable.insert(name = "%s_%s" % ("br_case_activity",
                                                   activity_id,
                                                   ))
        realm = Storage(id = realm_id)
        s3db.update_super(rtable, realm)
        realm_entity = realm["pe_id"]
        # Set this record to use this for it's realm
        catable = s3db.br_case_activity
        activity = db(catable.id == activity_id).select(catable.id,
                                                        catable.person_id,
                                                        limitby = (0, 1),
                                                        ).first()
        activity.update_record(realm_entity = realm_entity)

        # Set appropriate affiliations
        from s3db.pr import pr_add_affiliation

        # Activity affiliated to the Case
        # Person in a case has the same Realm
        ptable = s3db.pr_person
        person = db(ptable.id == activity.person_id).select(ptable.realm_entity,
                                                            limitby = (0, 1),
                                                            ).first()

        pr_add_affiliation(person.realm_entity, realm_entity, role="Realm Hierarchy")

        human_resource_id = form_vars.human_resource_id
        if human_resource_id:
            # Assignee already done, so add affiliation to this Handler
            htable = s3db.hrm_human_resource
            query = (htable.id == human_resource_id) & \
                    (htable.person_id == ptable.id)
            person = db(query).select(ptable.pe_id,
                                      limitby = (0, 1),
                                      ).first()
            pr_add_affiliation(person.pe_id, realm_entity, role="Realm Hierarchy")
        else:
            # Create a Task to look for someone to assign themselves to the Activity
            ntable = s3db.br_need
            need = db(ntable.id == form_vars.need_id).select(ntable.name,
                                                             ntable.uuid,
                                                             limitby = (0, 1),
                                                             ).first()

            ttable = s3db.project_task
            task_id = ttable.insert(name = need.name,
                                    description = form_vars.need_details,
                                    )
            # Link the Task to the Activity
            s3db.dissemination_case_activity_task.insert(case_activity_id = activity_id,
                                                         task_id = task_id,
                                                         )
            # Set the Task to appropriate Realm Entity
            # => top-level WG Forum
            ftable = s3db.pr_forum
            forum = db(ftable.uuid == need.uuid).select(ftable.pe_id,
                                                        limitby = (0, 1),
                                                        ).first()

            db(ttable.id == task_id).update(realm_entity = forum.pe_id)

    # =========================================================================
    def br_case_activity_update_onaccept(form):
        """
            * Ensure the correct Inheritances for the Realm
        """

        form_vars = form.vars
        human_resource_id = form_vars.human_resource_id
        if human_resource_id == form.record.human_resource_id:
            # Handler unchanged
            return

        db = current.db
        s3db = current.s3db

        activity_id = form_vars.id

        # Read the realm_entity
        catable = s3db.br_case_activity
        activity = db(catable.id == activity_id).select(catable.person_id,
                                                        catable.realm_entity,
                                                        limitby = (0, 1),
                                                        ).first()
        realm_entity = activity.realm_entity

        # Remove all current affiliations
        from s3db.pr import pr_remove_affiliation
        pr_remove_affiliation(None, realm_entity)

        # Set appropriate affiliations
        from s3db.pr import pr_add_affiliation

        # Activity affiliated to the Case
        # Person in a case has the same Realm
        ptable = s3db.pr_person
        person = db(ptable.id == activity.person_id).select(ptable.realm_entity,
                                                            limitby = (0, 1),
                                                            ).first()

        pr_add_affiliation(person.realm_entity, realm_entity, role="Realm Hierarchy")

        if human_resource_id:
            # Assignee already done, so add affiliation to this Handler
            htable = s3db.hrm_human_resource
            query = (htable.id == human_resource_id) & \
                    (htable.person_id == ptable.id)
            person = db(query).select(ptable.pe_id,
                                      limitby = (0, 1),
                                      ).first()
            pr_add_affiliation(person.pe_id, realm_entity, role="Realm Hierarchy")

    # =========================================================================
    def customise_br_case_activity_resource(r, tablename):

        from gluon import IS_NOT_EMPTY
        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLVerticalSubFormLayout

        s3db = current.s3db

        s3db.add_custom_callback(tablename,
                                 "create_onaccept",
                                 br_case_activity_create_onaccept,
                                 )

        s3db.add_custom_callback(tablename,
                                 "update_onaccept",
                                 br_case_activity_update_onaccept,
                                 )

        table = s3db.br_case_activity
        table.human_resource_id.label = T("Handler")

        if r.method in (None, "create"):
            # Need is required
            requires = table.need_id.requires 
            if hasattr(requires, "other"):
                table.need_id.requires = requires.other
            table.need_details.requires = IS_NOT_EMPTY()
            table.need_details.comment = T("If no Handler is assigned, then these Details will be copied to the Task created to request someone to take on this Activity")
            table.human_resource_id.comment = T("If no Handler is assigned, then when a Handler accepts the Task then they will be Assigned to the Activity")
        elif r.method == "update":
            # Don't allow Need to be changed
            table.need_id.writable = False
            table.human_resource_id.comment = None

        crud_form = S3SQLCustomForm("person_id",
                                    "need_id",
                                    "need_details",
                                    "human_resource_id",
                                    "priority",
                                    "date",
                                    "activity_details",
                                    "status_id",
                                    S3SQLInlineComponent("case_activity_update",
                                                         label = T("Progress"),
                                                         fields = ["date",
                                                                   "update_type_id",
                                                                   "human_resource_id",
                                                                   "comments",
                                                                   ],
                                                         layout = S3SQLVerticalSubFormLayout,
                                                         explicit_add = T("Add Entry"),
                                                         ),
                                    "end_date",
                                    "outcome",
                                    S3SQLInlineComponent("document",
                                                         name = "file",
                                                         label = T("Attachments"),
                                                         fields = ["file", "comments"],
                                                         filterby = {"field": "file",
                                                                     "options": "",
                                                                     "invert": True,
                                                                     },
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_br_case_activity_resource = customise_br_case_activity_resource

    # =========================================================================
    # Use pr_person_controller prep
    #def customise_br_case_resource(r, tablename):
    #settings.customise_br_case_resource = customise_br_case_resource

    # =========================================================================
    def customise_cr_shelter_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_org_site = {"name": "dissemination",
                                                      "joinby": "site_id",
                                                      "multiple": False,
                                                      },
                            )

        from s3 import S3SQLCustomForm
        crud_fields = ("dissemination.dissemination",
                       "name",
                       "organisation_id",
                       "shelter_type_id",
                       "location_id",
                       "person_id",
                       "contact_name",
                       "phone",
                       "email",
                       "website",
                       "shelter_details.population",
                       "shelter_details.capacity_day",
                       "shelter_details.capacity_night",
                       "shelter_details.available_capacity_day",
                       "shelter_details.population_day",
                       "shelter_details.population_night",
                       "shelter_details.status",
                       "comments",
                       "obsolete",
                       )

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       # Do NOT update standard affiliations
                       onaccept = None,
                       )

    settings.customise_cr_shelter_resource = customise_cr_shelter_resource

    # =========================================================================
    def customise_event_incident_report_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_incident_report = {"name": "dissemination",
                                                             "joinby": "incident_report_id",
                                                             "multiple": False,
                                                             },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.event_incident_report
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_event_incident_report_resource = customise_event_incident_report_resource

    # =========================================================================
    def customise_fin_broker_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_fin_broker = {"name": "dissemination",
                                                        "joinby": "broker_id",
                                                        "multiple": False,
                                                        },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.fin_broker
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_fin_broker_resource = customise_fin_broker_resource

    # =========================================================================
    def customise_hrm_human_resource_resource(r, tablename):

        current.s3db.configure(tablename,
                               # Always create via User Account
                               insertable = False,
                               )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # =========================================================================
    def customise_inv_inv_item_resource(r, tablename):

        from s3 import IS_ONE_OF, S3Represent, S3SQLCustomForm, S3SQLInlineComponent
        from s3layouts import S3PopupLink

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_inv_item = {"name": "dissemination",
                                                      "joinby": "inv_item_id",
                                                      "multiple": False,
                                                      },
                            )

        table = s3db.inv_inv_item
        table.site_id.requires = IS_ONE_OF(current.db, "org_site.site_id",
                                           S3Represent(lookup = "org_site"),
                                           orderby = "org_site.name",
                                           sort = True,
                                           instance_types = ("inv_warehouse",),
                                           updateable = True,
                                           )
        # @ToDo: get this working with a site_id
        table.site_id.comment = S3PopupLink(c = "inv",
                                            f = "warehouse",
                                            label = T("Create Warehouse"),
                                            vars = {"parent": "inv_item",
                                                    "child": "site_id",
                                                    }
                                            )

        crud_fields = ("dissemination.dissemination",
                       "site_id",
                       "item_id",
                       "item_pack_id",
                       "quantity",
                       S3SQLInlineComponent("bin",
                                            label = T("Bins"),
                                            fields = ["layout_id",
                                                      "quantity",
                                                      ],
                                            ),
                       "status",
                       "purchase_date",
                       "expiry_date",
                       "pack_value",
                       "currency",
                       "item_source_no",
                       "owner_org_id",
                       "supply_org_id",
                       "source_type",
                       "comments",
                       )

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # =========================================================================
    def customise_inv_warehouse_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_org_site = {"name": "dissemination",
                                                      "joinby": "site_id",
                                                      "multiple": False,
                                                      },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.inv_warehouse
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       # Do NOT update standard affiliations
                       onaccept = None,
                       )

    settings.customise_inv_warehouse_resource = customise_inv_warehouse_resource

    # =========================================================================
    def customise_med_contact_resource(r, tablename):

        from gluon import A, URL

        s3db = current.s3db

        f = s3db.med_contact.person_id
        f.label = T("Person Record")
        f.represent = lambda v: A(v,
                                  _href = URL(c="br", f="person",
                                              args = v,
                                              )) if v else current.messages["NONE"]
        f.comment = None
        f.writable = False

        s3db.add_components(tablename,
                            dissemination_med_contact = {"name": "dissemination",
                                                         "joinby": "contact_id",
                                                         "multiple": False,
                                                         },
                            )

        from s3 import S3SQLCustomForm, S3SQLInlineLink
        crud_fields = ["dissemination.dissemination",
                       "name",
                       "operational",
                       S3SQLInlineLink("skill",
                                       label = T("Qualifications"),
                                       field = "skill_id",
                                       ),
                       "location_id",
                       "phone",
                       "email",
                       "person_id",
                       "comments",
                       ]
        if r.function != "hospital":
            crud_fields.insert(-2, S3SQLInlineLink("hospital",
                                                   label = T("Hospital"),
                                                   field = "hospital_id",
                                                   ))

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_med_contact_resource = customise_med_contact_resource

    # =========================================================================
    def org_organisation_create_onaccept(form):
        """
            Create an RO & RW Forum for the Org Admin to be granted permissions to
            Create a RO & RW Forum for each Working Group for the Working Group members of this Organisation to be granted permission to
            Have the WG Forums inherit from the Org-level Forums
        """

        from s3db.pr import pr_add_affiliation

        db = current.db
        s3db = current.s3db

        organisation_id = form.vars.id

        ftable = s3db.pr_forum
        update_super = s3db.update_super

        # Create the top-level RO Forum
        uuid = "ORG_ADMIN_RO_%s" % organisation_id
        forum_id = ftable.insert(name = uuid,
                                 uuid = uuid,
                                 organisation_id = organisation_id,
                                 forum_type = 2,
                                 )
        record = Storage(id = forum_id)
        update_super(ftable, record)
        master_ro = record["pe_id"]

        # Create the top-level RW Forum
        uuid = "ORG_ADMIN_RW_%s" % organisation_id
        forum_id = ftable.insert(name = uuid,
                                 uuid = uuid,
                                 organisation_id = organisation_id,
                                 forum_type = 2,
                                 )
        record = Storage(id = forum_id)
        update_super(ftable, record)
        master_rw = record["pe_id"]

        # Read all the top-level WG Forums
        forums = db(ftable.uuid.belongs(WORKING_GROUPS)).select(ftable.uuid,
                                                                ftable.pe_id,
                                                                )
        forums = {row.uuid: row.pe_id for row in forums}

        for WG in WORKING_GROUPS:
            # Create the WG RO Forum
            uuid = "%s_RO_%s" % (WG,
                                 organisation_id,
                                 )
            forum_id = ftable.insert(name = uuid,
                                     uuid = uuid,
                                     organisation_id = organisation_id,
                                     forum_type = 2,
                                     )
            record = Storage(id = forum_id)
            update_super(ftable, record)
            org_wg_ro = record["pe_id"]

            # Have the WG inherit from the top-level Org
            pr_add_affiliation(master_ro, org_wg_ro, role="Realm Hierarchy")

            # Have the top-level WG inherit from this
            pr_add_affiliation(org_wg_ro, forums[WG], role="Realm Hierarchy")

            # Create the WG RW Forum
            uuid = "%s_RW_%s" % (WG,
                                 organisation_id,
                                 )
            forum_id = ftable.insert(name = uuid,
                                     uuid = uuid,
                                     organisation_id = organisation_id,
                                     forum_type = 2,
                                     )
            record = Storage(id = forum_id)
            update_super(ftable, record)
            org_wg_rw = record["pe_id"]

            # Have the WG inherit from the top-level
            pr_add_affiliation(master_rw, org_wg_rw, role="Realm Hierarchy")

    # =========================================================================
    def customise_org_organisation_resource(r, tablename):

        current.s3db.add_custom_callback(tablename,
                                         "create_onaccept",
                                         org_organisation_create_onaccept,
                                         )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # =========================================================================
    def customise_org_organisation_controller(**attr):

        attr["rheader"] = None

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # =========================================================================
    def pr_person_postprocess(form):
        """
            Set the Correct Realm for the Case and then the Person
        """

        form_vars = form.vars
        human_resource_id = form_vars.sub_case_human_resource_id
        organisation_id = form_vars.sub_case_organisation_id

        record = form.record
        if record:
            # Update form

            # Have either the Case Manager or Organisation changed?
            if human_resource_id == record.sub_case_human_resource_id and \
               organisation_id == record.sub_case_organisation_id:
                # No change
                return

            db = current.db
            s3db = current.s3db

            # Lookup Case
            person_id = form_vars.id
            ctable = s3db.br_case
            case = db(ctable.person_id == person_id).select(ctable.id,
                                                            ctable.realm_entity,
                                                            limitby = (0, 1),
                                                            ).first()

            # Read current realm_entity
            realm_entity = case.realm_entity

            if realm_entity:
                # Check it's a pr_realm record
                petable = s3db.pr_pentity
                pe = db(petable.pe_id == realm_entity).select(petable.instance_type,
                                                              limitby = (0, 1)
                                                              ).first()
                if pe.instance_type == "pr_realm":
                    # Set the person to use this for it's realm
                    ptable = s3db.pr_person
                    db(ptable.id == person_id).update(realm_entity = realm_entity)
                else:
                    current.log.debug("Disseminate: record %s in %s had a realm of type %s" % (record_id,
                                                                                               tablename,
                                                                                               pe.instance_type,
                                                                                               ))
                    realm_entity = None

        else:
            # Create form
            db = current.db
            s3db = current.s3db

            # Lookup Case
            person_id = form_vars.id
            ctable = s3db.br_case
            case = db(ctable.person_id == person_id).select(ctable.id,
                                                            limitby = (0, 1),
                                                            ).first()

            realm_entity = None

        if realm_entity:
            # Delete all current affiliations
            from s3db.pr import pr_remove_affiliation
            pr_remove_affiliation(None, realm_entity)
        else:
            # Create a pr_realm record
            rtable = s3db.pr_realm
            realm_id = rtable.insert(name = "%s_%s" % ("br_case",
                                                       case.id,
                                                       ))
            realm = Storage(id = realm_id)
            s3db.update_super(rtable, realm)
            realm_entity = realm["pe_id"]
            # Set this Case to use this for it's realm
            case.update_record(realm_entity = realm_entity)
            # Set the person to use this for it's realm
            ptable = s3db.pr_person
            db(ptable.id == person_id).update(realm_entity = realm_entity)

        # Set appropriate affiliations
        from s3db.pr import pr_add_affiliation

        # Org
        otable = s3db.org_organisation
        org = db(otable.id == organisation_id).select(otable.pe_id,
                                                      limitby = (0, 1),
                                                      ).first()
        pr_add_affiliation(org.pe_id, realm_entity, role="Realm Hierarchy")

        if human_resource_id:
            # Case Manager
            htable = s3db.hrm_human_resource
            query = (htable.id == human_resource_id) & \
                    (htable.person_id == ptable.id)
            person = db(query).select(ptable.pe_id,
                                      limitby = (0, 1),
                                      ).first()
            pr_add_affiliation(person.pe_id, realm_entity, role="Realm Hierarchy")

    # =========================================================================
    def customise_pr_person_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component or r.controller == "hrm":
                return result

            from gluon import IS_EMPTY_OR
            from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineComponent

            db = current.db
            s3db = current.s3db

            s3db.add_components("pr_person",
                                pr_occupation_type_person = {"joinby": "person_id",
                                                             "multiple": False,
                                                             },
                                )

            table = s3db.br_case

            #table.br_case.household_size.label = T("Group Size")

            # Filter to Case Managers
            gtable = db.auth_group
            mtable = db.auth_membership
            ltable = s3db.pr_person_user
            ptable = s3db.pr_person
            query = (gtable.uuid.belongs(("CASE_MANAGER",
                                          "CASE_SUPER",
                                          "ORG_ADMIN",
                                          ))) & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == ltable.user_id) & \
                    (ltable.pe_id == ptable.pe_id)
            persons = db(query).select(ptable.id)
            filter_opts = [p.id for p in persons]
            f = table.human_resource_id
            f.label = T("Case Manager")
            f.requires = IS_EMPTY_OR(
                            IS_ONE_OF(db, "hrm_human_resource.id",
                                      f.represent,
                                      filterby = "person_id",
                                      filter_opts = filter_opts,
                                      sort = True,
                                      ))

            crud_form = S3SQLCustomForm("case.date",
                                        "case.organisation_id",
                                        "case.human_resource_id",
                                        "case.priority",
                                        "case.status_id",
                                        "pe_label",
                                        "first_name",
                                        "middle_name",
                                        "last_name",
                                        "gender",
                                        "date_of_birth",
                                        #"person_details.nationality",
                                        "physical_description.ethnicity",
                                        (T("Occupation"), "occupation_type_person.occupation_type_id"),
                                        "person_details.marital_status",
                                        "case.household_size",
                                        S3SQLInlineComponent("address",
                                                             label = T("Current Address"),
                                                             fields = [("", "location_id")],
                                                             filterby = {"field": "type",
                                                                         "options": "1",
                                                                         },
                                                             link = False,
                                                             multiple = False,
                                                             ),
                                        S3SQLInlineComponent("contact",
                                                             fields = [("", "value")],
                                                             filterby = {"field": "contact_method",
                                                                         "options": "SMS",
                                                                         },
                                                             label = T("Mobile Phone"),
                                                             multiple = False,
                                                             name = "phone",
                                                             ),
                                        "case.comments",
                                        "case.invalid",
                                        postprocess = pr_person_postprocess,
                                        )

            list_fields = ["case.priority",
                           "pe_label",
                           "first_name",
                           "middle_name",
                           "last_name",
                           "gender",
                           "date_of_birth",
                           "case.status_id",
                           "case.human_resource_id",
                           "case.organisation_id",
                           ]

            s3db.configure(r.tablename,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )

            return result
        s3.prep = prep

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    def project_task_update_onaccept(form):
        """
            Update the Activity inheritances when Task is Assigned
        """

        form_vars = form.vars
        pe_id = form_vars.pe_id

        if pe_id == form.record.pe_id:
            # No change
            return

        db = current.db
        s3db = current.s3db

        task_id = form_vars.id

        # Lookup the linked Case Activity
        catable = s3db.br_case_activity
        ltable = s3db.dissemination_case_activity_task
        query = (ltable.task_id == task_id) & \
                (ltable.case_activity_id == catable.id)
        activity = db(query).select(catable.id,
                                    catable.realm_entity,
                                    limitby = (0, 1),
                                    ).first()

        if activity:
            # Affiliate the Activity to the Assignee
            from s3db.pr import pr_add_affiliation

            pr_add_affiliation(pe_id, activity.realm_entity, role="Realm Hierarchy")

            # Assign the Handler to the Activity
            ptable = s3db.pr_person
            htable = s3db.hrm_human_resource
            query = (ptable.pe_id == pe_id) & \
                    (ptable.id == htable.person_id)
            hr = db(query).select(htable.id,
                                  limitby = (0, 1),
                                  ).first()
            activity.update_record(human_resource_id = hr.id)

    # =========================================================================
    def customise_project_task_resource(r, tablename):

        from gluon import IS_EMPTY_OR
        from s3 import IS_ONE_OF

        db = current.db
        s3db = current.s3db

        # Just People for Assignees
        task_id = r.id
        if task_id and tablename == r.tablename:
            # Are we linked to a Case Activity?
            catable = s3db.br_case_activity
            ltable = s3db.dissemination_case_activity_task
            query = (ltable.task_id == task_id) & \
                    (ltable.case_activity_id == catable.id)
            activity = db(query).select(catable.need_id,
                                        catable.realm_entity,
                                        limitby = (0, 1),
                                        ).first()
        else:
            activity = None

        f = s3db.project_task.pe_id

        if activity:
            # Filter to Handlers of that Type
            f.label = T("Handler")
            ntable = s3db.br_need
            need = db(ntable.id == activity.need_id).select(ntable.uuid,
                                                            limitby = (0, 1),
                                                            ).first()
            gtable = db.auth_group
            mtable = db.auth_membership
            ltable = s3db.pr_person_user
            query = (gtable.uuid.belongs((need.uuid,
                                          "ORG_ADMIN",
                                          "ADMIN",
                                          ))) & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == ltable.user_id)
            persons = db(query).select(ltable.pe_id)
            filter_opts = [p.pe_id for p in persons]
        else:
            # Filtered to Staff
            htable = s3db.hrm_human_resource
            ptable = s3db.pr_person
            query = (htable.deleted == False) & \
                    (htable.person_id == ptable.id)
            persons = db(query).select(ptable.pe_id)
            filter_opts = [p.pe_id for p in persons]

        from s3db.pr import pr_PersonEntityRepresent
        represent = pr_PersonEntityRepresent(show_label = False,
                                             show_type = False,
                                             )

        f.requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "pr_pentity.pe_id",
                                  represent,
                                  filterby = "pe_id",
                                  filter_opts = filter_opts,
                                  sort = True,
                                  ))

        s3db.add_custom_callback(tablename,
                                 "update_onaccept",
                                 project_task_update_onaccept,
                                 )

    settings.customise_project_task_resource = customise_project_task_resource

    # =========================================================================
    def customise_security_checkpoint_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_security_checkpoint = {"name": "dissemination",
                                                                 "joinby": "checkpoint_id",
                                                                 "multiple": False,
                                                                 },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.security_checkpoint
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_security_checkpoint_resource = customise_security_checkpoint_resource

    # =========================================================================
    def customise_security_zone_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_security_zone = {"name": "dissemination",
                                                           "joinby": "zone_id",
                                                           "multiple": False,
                                                           },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.security_zone
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_security_zone_resource = customise_security_zone_resource

    # =========================================================================
    def customise_transport_flight_resource(r, tablename):

        s3db = current.s3db

        s3db.add_components(tablename,
                            dissemination_transport_flight = {"name": "dissemination",
                                                              "joinby": "flight_id",
                                                              "multiple": False,
                                                              },
                            )

        from s3 import S3SQLCustomForm
        table = s3db.transport_flight
        crud_fields = [f.name for f in table if (f.writable or f.readable) and not f.compute]
        crud_fields.insert(0, "dissemination.dissemination")

        from .dissemination import disseminate
        crud_form = S3SQLCustomForm(postprocess = disseminate,
                                    *crud_fields)

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_transport_flight_resource = customise_transport_flight_resource

# END =========================================================================
