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
    settings.base.prepopulate_demo = ("BRCMS/Evac/Demo",
                                      )

    # Custom Models
    settings.base.custom_models = {"dissemination": "BRCMS.Evac",
                                   }

    # Enable password-retrieval feature
    settings.auth.password_retrieval = True

    settings.auth.registration_organisation_required = True
    settings.auth.realm_entity_types = ("org_organisation",
                                        "pr_forum",  # Realms
                                        "pr_person", # Case Managers, Case Supervisors, Handlers
                                        )

    # Enable extra Modules
    modules = settings.modules
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
    settings.br.case_per_family_member = False
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

            # Try Case 1st (we expect more of these)
            ctable = s3db.br_case
            case = db(ctable.person_id == person_id).select(ctable.realm_entity,
                                                            limitby = (0, 1),
                                                            ).first()
            if case:
                # => Inherit from Case
                return case.realm_entity

            # Try Staff 3rd (we expect less of these)
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

            # Probably a new case...will be sorted in crud_form.preprocess
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

        elif tablename in ("pr_address",
                           "pr_contact",
                           "pr_contact_emergency",
                           "pr_image",
                           ):

            # Inherit from person via PE
            s3db = current.s3db
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.pe_id == table.pe_id)
            person = current.db(query).select(ptable.realm_entity,
                                              limitby = (0, 1),
                                              ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename == "org_organisation":
            # Realm is own PE ID
            # => use Default Rules
            return 0

        # Use default rules
        return 0

    settings.auth.realm_entity = evac_realm_entity

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

        # Is this the Admin role?
        if group_id == system_roles.ADMIN:
            if from_role_manager:
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
            if not org:
                # Default ADMIN in prepop: bail
                return

            # Lookup the Entity for the main role
            if for_pe:
                entity = for_pe
            else:
                entity = org.pe_id

            if from_role_manager:
                # Add the main Role for the correct entity
                add_membership(group_id = group_id,
                               user_id = user_id,
                               entity = entity,
                               )
            elif not for_pe:
                # Update the main Role to the correct entity
                mtable = db.auth_membership
                query = (mtable.group_id == group_id) & \
                        (mtable.user_id == user_id) & \
                        (mtable.pe_id == None)
                db(query).update(pe_id = entity)

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
                if not org:
                    # Default ADMIN in prepop: bail
                    return

                entity = org.pe_id

            if from_role_manager:
                # Add the main Role for the correct entity
                add_membership(group_id = group_id,
                               user_id = user_id,
                               entity = entity,
                               )
            elif not for_pe:
                # Update the main Role to the correct entity
                mtable = db.auth_membership
                query = (mtable.group_id == group_id) & \
                        (mtable.user_id == user_id) & \
                        (mtable.pe_id == None)
                db(query).update(pe_id = entity)

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

        if from_role_manager:
            # Add the main Role for the correct entity
            add_membership(group_id = group_id,
                           user_id = user_id,
                           entity = entity,
                           )
        elif not for_pe:
            # Update the main Role to the correct entity
            mtable = db.auth_membership
            query = (mtable.group_id == group_id) & \
                    (mtable.user_id == user_id) & \
                    (mtable.pe_id == None)
            db(query).update(pe_id = entity)

        # Lookup the Group for the Org Member role
        group = db(gtable.uuid == "ORG_MEMBER").select(gtable.id,
                                                       limitby = (0, 1),
                                                       ).first()
        # Lookup the Entity for the Org Member role
        utable = db.auth_user
        otable = s3db.org_organisation
        query = (utable.id == user_id) & \
                (otable.id == utable.organisation_id)
        org = db(query).select(otable.id,
                               otable.pe_id,
                               limitby = (0, 1),
                               ).first()
        if not org:
            # Default ADMIN in prepop: bail
            return
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
            if not org:
                # Default ADMIN in prepop: bail
                return

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
                if not org:
                    # Default ADMIN in prepop: bail
                    return
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

        # @ToDo: Call settings.auth.add_role via auth_membership_create_onaccept
        current.s3db.configure("auth_membership",
                               create_onaccept = auth_membership_create_onaccept,
                               )

    settings.customise_auth_user_resource = customise_auth_user_resource

    # =========================================================================
    def auth_user_update_onaccept(form):
        """
            Handle Users moved between Orgs
        """

        form_vars = form.vars
        organisation_id = int(form_vars.organisation_id)
        old_organisation_id = form.record.organisation_id
        if organisation_id == old_organisation_id:
            # Nothing to do
            return

        user_id = form_vars.id

        db = current.db
        s3db = current.s3db

        # Lookup the Org PE IDs
        otable = s3db.org_organisation
        orgs = db(otable.id.belongs((organisation_id,
                                     old_organisation_id,
                                     ))).select(otable.id,
                                                otable.pe_id,
                                                limitby = (0, 2),
                                                )
        orgs = {org.id: org.pe_id for org in orgs}
        organisation_pe_id = orgs[organisation_id]
        old_organisation_pe_id = orgs[old_organisation_id]

        # Read Memberships
        gtable = db.auth_group
        mtable = db.auth_membership
        query = (mtable.user_id == user_id) & \
                (mtable.group_id == gtable.id)
        rows = db(query).select(gtable.uuid,
                                mtable.pe_id,
                                )
        roles = {}
        for row in rows:
            role = row["auth_group.uuid"]
            if role in ("AUTHENTICATED",
                        "FLIGHTS",
                        "LEGAL",
                        "LOGISTICS",
                        "MEDICAL",
                        "SECURITY",
                        ):
                # Role applied at Personal Level
                # => no need to update
                continue
            if role in roles:
                roles[role].append(row["auth_membership.pe_id"])
            else:
                roles[role] = [row["auth_membership.pe_id"]]

        if "CASE_MANAGER" in roles or \
           "CASE_SUPER" in roles or \
           "ORG_ADMIN" in roles:
            # Can be assigned to Cases

            # Lookup Person PE ID
            ltable = s3db.pr_person_user
            person = db(ltable.user_id == user_id).select(ltable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            pe_id = person.pe_id
            
            # Remove assignment to all Cases in the old Org
            ptable = s3db.pr_person
            htable = s3db.hrm_human_resource
            ctable = s3db.br_case
            query = (ptable.pe_id == pe_id) & \
                    (ptable.id == htable.person_id) & \
                    (htable.id == ctable.human_resource_id) & \
                    (ctable.organisation_id == old_organisation_id)
            cases = db(query).select(ctable.id,
                                     ctable.realm_entity,
                                     )
            if cases:
                # Remove assignments
                db(ctable.id.belongs([c.id for c in cases])).update(human_resource_id = None)
                # Remove affiliations
                from s3db.pr import pr_remove_affiliation
                for case in cases:
                    pr_remove_affiliation(pe_id, case.realm_entity)

            if "CASE_MANAGER" in roles:
                del roles["CASE_MANAGER"]
            if "CASE_SUPER" in roles:
                del roles["CASE_SUPER"]

            if "ORG_ADMIN" in roles and \
               old_organisation_pe_id in roles["ORG_ADMIN"]:
                # Update Role to new Org's Realm
                # Role applied at Organization Level
                query = (mtable.user_id == user_id) & \
                        (mtable.group_id == gtable.id) & \
                        (gtable.uuid == "ORG_ADMIN") & \
                        (mtable.pe_id == old_organisation_pe_id)
                membership = db(query).select(mtable.id,
                                              limitby = (0, 1),
                                              ).first()
                membership.update_record(pe_id = organisation_pe_id)
                del roles["ORG_ADMIN"]

        if "ORG_MEMBER" in roles and \
           old_organisation_pe_id in roles["ORG_MEMBER"]:
            # Update Role to new Org's Realm
            # Role applied at Organization Level
            query = (mtable.user_id == user_id) & \
                    (mtable.group_id == gtable.id) & \
                    (gtable.uuid == "ORG_MEMBER") & \
                    (mtable.pe_id == old_organisation_pe_id)
            membership = db(query).select(mtable.id,
                                          limitby = (0, 1),
                                          ).first()
            membership.update_record(pe_id = organisation_pe_id)
            del roles["ORG_MEMBER"]
        
        # Lookup Forums
        forum_roles = ("_RW",
                       "_RO",
                       )
        forums = []
        for role in roles:
            if role[-3:] in (forum_roles):
                forums += ("%s_%s" % (role, organisation_id),
                           "%s_%s" % (role, old_organisation_id),
                           )

        if not forums:
            # Case Manager or Case Super
            return

        ftable = s3db.pr_forum
        forums = db(ftable.uuid.belongs(forums)).select(ftable.uuid,
                                                        ftable.pe_id,
                                                        )
        forums = {row.uuid: row.pe_id for row in forums}

        user_query = (mtable.user_id == user_id)
        for role in roles:
            old_forum_uuid = "%s_%s" % (role, old_organisation_id)
            if old_forum_uuid not in forums:
                # Unknown role
                continue
            # WG role applied at WG Forum Level
            old_forum_pe_id = forums[old_forum_uuid]
            if old_forum_pe_id not in roles[role]:
                # No role for the old Org's WG Forum realm
                continue
            forum_pe_id = forums["%s_%s" % (role, organisation_id)]
            query = user_query & \
                    (mtable.group_id == gtable.id) & \
                    (gtable.uuid == role) & \
                    (mtable.pe_id == old_forum_pe_id)
            membership = db(query).select(mtable.id,
                                          limitby = (0, 1),
                                          ).first()
            membership.update_record(pe_id = forum_pe_id)

    # =========================================================================
    def customise_auth_user_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.method == "roles":
                if current.auth.s3_has_role("ADMIN") and r.get_vars.get("advanced"):
                    # @ToDo: Show Hidden Roles
                    pass
                else:
                    # Show a very simplified interface
                    settings.auth.realm_entity_types = ("org_organisation",)
                    s3.scripts.append("/%s/static/themes/Evac/js/roles.js" % r.application)
                    # @ToDo: Add an Advanced button to trigger a page reload with the advanced get_var
            else:
                # Handle move of User between Orgs
                current.s3db.configure("auth_user",
                                       update_onaccept = auth_user_update_onaccept,
                                       )

            return result
        s3.prep = prep

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

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
        if human_resource_id == str(form.record.human_resource_id):
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

        db = current.db
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
        f = table.human_resource_id
        f.label = T("Handler")

        if r.method == "update":
            update = True
        else:
            if tablename == r.tablename:
                update = r.id
            else:
                update = r.component_id

        if update:
            # Don't allow Need to be changed
            table.need_id.writable = False
            f.comment = None
            # Filter to Handlers for this WG
            if tablename == r.tablename:
                need_id = r.record.need_id
            else:
                activity_id = r.component_id
                record = db(table.id == activity_id).select(table.need_id,
                                                            limitby = (0, 1),
                                                            ).first()
                need_id = record.need_id
            ntable = s3db.br_need
            need = db(ntable.id == need_id).select(ntable.uuid,
                                                   limitby = (0, 1),
                                                   ).first()
            gtable = db.auth_group
            mtable = db.auth_membership
            ltable = s3db.pr_person_user
            ptable = s3db.pr_person
            query = (gtable.uuid.belongs((need.uuid,
                                          "ORG_ADMIN",
                                          "ADMIN",
                                          ))) & \
                    (gtable.id == mtable.group_id) & \
                    (mtable.user_id == ltable.user_id) & \
                    (ltable.pe_id == ptable.pe_id)
            persons = db(query).select(ptable.id)
            filter_opts = [p.id for p in persons]
            from gluon import IS_EMPTY_OR
            from s3 import IS_ONE_OF
            f.requires = IS_EMPTY_OR(
                            IS_ONE_OF(db, "hrm_human_resource.id",
                                      f.represent,
                                      filterby = "person_id",
                                      filter_opts = filter_opts,
                                      sort = True,
                                      ))

        elif r.method in (None, "create"):
            # Need is required
            requires = table.need_id.requires 
            if hasattr(requires, "other"):
                table.need_id.requires = requires.other
            table.need_details.requires = IS_NOT_EMPTY()
            table.need_details.comment = T("If no Handler is assigned, then these Details will be copied to the Task created to request someone to take on this Activity")
            f.comment = T("If no Handler is assigned, then when a Handler accepts the Task then they will be Assigned to the Activity")
            # Activity Priority defaults to Case Priority
            if tablename == r.tablename:
                record = r.record
                if record:
                    ctable = s3db.br_case
                    case = db(ctable.person_id == r.record.person_id).select(ctable.priority,
                                                                             limitby = (0, 1),
                                                                             ).first()
                    table.priority.default = case.priority
            else:
                ctable = s3db.br_case
                case = db(ctable.person_id == r.id).select(ctable.priority,
                                                           limitby = (0, 1),
                                                           ).first()
                table.priority.default = case.priority
            # Filter to Handlers for the WG selected
            current.response.s3.scripts.append("/%s/static/themes/Evac/js/br_case_activity.js" % r.application)

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
    def customise_br_case_activity_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.get_vars.get("my_cases"):
                # Filter to Activities for Cases assigned to this person
                human_resource_id = current.auth.s3_logged_in_human_resource()
                if human_resource_id:
                    from s3 import FS
                    r.resource.add_filter(FS("person_id$case.human_resource_id") == human_resource_id)

            return result
        s3.prep = prep

        return attr

    settings.customise_br_case_activity_controller = customise_br_case_activity_controller

    # =========================================================================
    # Use pr_person_controller prep
    #def customise_br_case_resource(r, tablename):
    #settings.customise_br_case_resource = customise_br_case_resource

    # =========================================================================
    def handlers(r, **attr):
        """
            Return the Handlers for a Need when creating an Activity
            - called by br_case_activity.js
            - called via .json to reduce request overheads
        """

        import json

        from s3 import s3_fullname

        db = current.db
        s3db = current.s3db

        ntable = s3db.br_need
        need = db(ntable.id == r.id).select(ntable.uuid,
                                            limitby = (0, 1),
                                            ).first()
        gtable = db.auth_group
        mtable = db.auth_membership
        ltable = s3db.pr_person_user
        ptable = s3db.pr_person
        htable = s3db.hrm_human_resource
        query = (gtable.uuid.belongs((need.uuid,
                                      "ORG_ADMIN",
                                      "ADMIN",
                                      ))) & \
                (gtable.id == mtable.group_id) & \
                (mtable.user_id == ltable.user_id) & \
                (ltable.pe_id == ptable.pe_id) & \
                (ptable.id == htable.person_id)
        rows = db(query).select(htable.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name,
                                )

        # Simplify format
        handlers = [{"i": row["hrm_human_resource.id"],
                     "n": s3_fullname(row.pr_person),
                     } for row in rows]

        SEPARATORS = (",", ":")
        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(handlers, separators=SEPARATORS)
        
    # =========================================================================
    def customise_br_need_controller(**attr):

        current.s3db.set_method("br", "need",
                                method = "handlers",
                                action = handlers,
                                )

        return attr

    settings.customise_br_need_controller = customise_br_need_controller

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
            if WG == "SECURITY":
                security_wg_ro = org_wg_ro

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

        # Additionally have the top-level LOGISTICS inherit from ORG SECURITY RO
        pr_add_affiliation(security_wg_ro, forums["LOGISTICS"], role="Realm Hierarchy")

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
    def br_rheader(r):
        """
            BR Resource Headers
            - copied from modules/s3db/py
            - settings applied rather than looked-up & Family/Household labelled as Group
            - 'Share case with' added 
        """

        if r.representation != "html":
            # Resource headers only used in interactive views
            return None

        from s3 import s3_rheader_resource

        tablename, record = s3_rheader_resource(r)
        if not record:
            return None

        s3db = current.s3db

        if tablename != r.tablename:
            resource = s3db.resource(tablename,
                                     id = record.id,
                                     )
        else:
            resource = r.resource

        case = resource.select(["first_name",
                                "middle_name",
                                "last_name",
                                "case.status_id",
                                "case.invalid",
                                "case.household_size",
                                "case.organisation_id",
                                ],
                                represent = True,
                                raw_data = True,
                                ).rows

        if not case:
            # Target record exists, but doesn't match filters
            return None

        case = case[0]
        raw = case["_row"]

        from s3 import S3ResourceHeader, s3_avatar_represent, s3_fullname

        T = current.T

        record_id = record.id

        tabs = [(T("Basic Details"), None),
                (T("Contact Info"), "contacts"),
                (T("ID"), "identity"),
                (T("Group Members"), "group_membership/"),
                (T("Activities"), "case_activity"),
                (T("Notes"), "br_note"),
                (T("Documents"), "document/"),
                ]

        rheader_fields = [[(T("ID"), "pe_label"),
                           (T("Case Status"), lambda row: case["br_case.status_id"]),
                           (T("Organisation"), lambda row: case["br_case.organisation_id"]),
                           ],
                          ["date_of_birth",
                           (T("Size of Group"), lambda row: case["br_case.household_size"]),
                           ],
                          ]

        if current.auth.s3_has_role("ORG_ADMIN"):
            # Add option to share case with another Organisation
            otable = s3db.org_organisation
            query = (otable.deleted == False) & \
                    (otable.id != raw["br_case.organisation_id"])
            orgs = current.db(query).select(otable.id,
                                            otable.name,
                                            )
            from gluon import OPTION, SELECT
            opts = [OPTION(org.name,
                           _value = org.id,
                           ) for org in orgs]
            opts.insert(0, OPTION(""))
            orgs_dropdown = SELECT(_id = "share-case",
                                   *opts)
            orgs_dropdown["_data-person_id"] = record.id
            rheader_fields[1].append((T("Share Case with"), lambda row: orgs_dropdown))
            s3 = current.response.s3
            s3.scripts.append("/%s/static/themes/Evac/js/share_case.js" % r.application)
            s3.stylesheets.append("../themes/Evac/style.css")

        invalid = raw["br_case.invalid"]
        if invalid:
            # "Invalid Case" Hint
            hint = lambda row: SPAN(T("Invalid Case"),
                                    _class = "invalid-case",
                                    )
            rheader_fields.insert(0, [(None, hint)])

        # Generate rheader XML
        rheader = S3ResourceHeader(rheader_fields,
                                   tabs,
                                   title = s3_fullname,
                                   )(r,
                                     table = resource.table,
                                     record = record,
                                     )

        # Add profile picture
        from gluon import A, URL 
        rheader.insert(0, A(s3_avatar_represent(record_id,
                                                "pr_person",
                                                _class = "rheader-avatar",
                                                ),
                            _href = URL(f = "person",
                                        args = [record_id, "image", "create"],
                                        vars = r.get_vars,
                                        ),
                            )
                       )

        return rheader

    # =========================================================================
    def pr_person_postprocess(form):
        """
            Set the Correct Realm for the Case and then the Person
        """

        form_vars = form.vars
        human_resource_id = form_vars.sub_case_human_resource_id
        organisation_id = form_vars.sub_case_organisation_id or current.auth.user.organisation_id

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
    def share_case(r, **attr):
        """
            Share a case with another Organisation
            - i.e. affiliate to ORG RO forum for their ORG_ADMIN to have READ access

            - called via POST from inv_send_rheader
            - called via JSON method to reduce request overheads
        """

        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD,
                    next = URL(),
                    )

        person_id = r.id

        if not person_id:
            r.error(405, "Can only share a single case")

        try:
            organisation_id = r.args[2]
        except:
            r.error(405, "Missing Organisation to share to")

        s3db = current.s3db
        ptable = s3db.pr_person

        if not current.auth.s3_has_permission("update", ptable,
                                              record_id = person_id,
                                              ):
            r.unauthorised()

        ftable = s3db.pr_forum
        forum = current.db(ftable.uuid == "ORG_ADMIN_RW_%s" % organisation_id).select(ftable.pe_id,
                                                                                      limitby = (0, 1),
                                                                                      ).first()

        from s3db.pr import pr_add_affiliation
        pr_add_affiliation(forum.pe_id, r.record.realm_entity, role="Realm Hierarchy")

        from s3 import s3_str

        import json
        SEPARATORS = (",", ":")
        current.response.headers["Content-Type"] = "application/json"
        return json.dumps({"message": s3_str(current.T("Case Shared")),
                           }, separators=SEPARATORS)

    # =========================================================================
    def customise_pr_person_controller(**attr):

        if current.request.controller in ("default",
                                          "hrm",
                                          ):
            # Use defaults
            return attr

        # Cases

        s3db = current.s3db
        s3 = current.response.s3

        s3db.set_method("pr", "person", 
                        method = "share",
                        action = share_case,
                        )

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component:
                return result

            from gluon import IS_EMPTY_OR
            from s3 import IS_ONE_OF, S3SQLCustomForm, S3SQLInlineComponent

            db = current.db

            # Redefine as multiple=False for simpler Inline form
            s3db.add_components("pr_person",
                                pr_occupation_type_person = {"joinby": "person_id",
                                                             "multiple": False,
                                                             },
                                )
            # Occupation optional
            f = s3db.pr_occupation_type_person.occupation_type_id
            f.requires = IS_EMPTY_OR(f.requires)

            ptable = s3db.pr_person
            # Gender optional
            f = ptable.gender
            f.requires = IS_EMPTY_OR(f.requires)

            table = s3db.br_case

            #table.br_case.household_size.label = T("Group Size")

            # Filter to Case Managers
            gtable = db.auth_group
            mtable = db.auth_membership
            ltable = s3db.pr_person_user
            query = (gtable.uuid.belongs(("CASE_MANAGER",
                                          "CASE_SUPER",
                                          "ORG_ADMIN",
                                          "ADMIN",
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

            crud_fields = ["case.date",
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
                           #"case.household_size",
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
                           ]

            auth = current.auth
            has_role = auth.s3_has_role
            if has_role("ADMIN"):
                assign_cm = True
                multiple_orgs = True
            elif has_role("ORG_ADMIN"):
                assign_cm = True
                realms = auth.permission.permitted_realms("br_case", "create")
                otable = s3db.org_organisation
                query = (otable.pe_id.belongs(realms)) & \
                        (otable.deleted == False)
                rows = db(query).select(otable.id,
                                        limitby = (0, 2),
                                        )
                multiple_orgs = len(rows) > 1
            elif has_role("CASE_SUPER"):
                assign_cm = True
            else:
                assign_cm = False
                multiple_orgs = False

            if assign_cm:
                crud_fields.insert(1, "case.human_resource_id")
            if multiple_orgs:
                crud_fields.insert(1, "case.organisation_id")

            crud_form = S3SQLCustomForm(*crud_fields,
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
                           ]
            if multiple_orgs:
                list_fields.append("case.organisation_id")

            s3db.configure(r.tablename,
                           crud_form = crud_form,
                           list_fields = list_fields,
                           )

            return result
        s3.prep = prep

        attr["rheader"] = br_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # =========================================================================
    def customise_pr_group_membership_controller(**attr):

        #s3db = current.s3db
        s3 = current.response.s3

        # @ToDo:
        #s3db.set_method("pr", "group_membership", 
        #                method = "split",
        #                action = split_case,
        #                )

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            # Adjust CRUD strings for this perspective
            s3.crud_strings["pr_group_membership"] = Storage(
                label_create = T("Add Group Member"),
                title_display = T("Group Member Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Group Member"),
                label_list_button = T("List Group Members"),
                label_delete_button = T("Remove Group Member"),
                msg_record_created = T("Group Member added"),
                msg_record_modified = T("Group Member updated"),
                msg_record_deleted = T("Group Member removed"),
                msg_list_empty = T("No Group Members currently registered"),
                )

            current.s3db.pr_group_membership.group_head.label = T("Group Head")

            return result
        s3.prep = prep

        attr["rheader"] = br_rheader

        return attr

    settings.customise_pr_group_membership_controller = customise_pr_group_membership_controller

    # =========================================================================
    def project_task_update_onaccept(form):
        """
            Update the Activity inheritances when Task is Assigned
        """

        form_vars = form.vars
        pe_id = form_vars.pe_id

        if pe_id == str(form.record.pe_id):
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
