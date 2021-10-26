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
    settings.base.prepopulate.append("BRCMS/Evac")
    #settings.base.prepopulate_demo.append("BRCMS/Evac/Demo")

    # Enable password-retrieval feature
    settings.auth.password_retrieval = True

    settings.auth.registration_organisation_required = True
    settings.auth.realm_entity_types = ("org_organisation",
                                        "pr_forum",  # Realms
                                        "pr_person", # Case Managers, Case Supervisors, Handlers
                                        # Not needed, as hidden?
                                        #"pr_realm",  # Cases, Resources
                                        )

    modules = settings.modules
    modules["asset"] = {"name_nice": T("Assets"), "module_type": 10}
    #modules["fin"] = {"name_nice": T("Finances"), "module_type": 10}
    modules["hms"] = {"name_nice": T("Hospitals"), "module_type": 10}
    #modules["security"] = {"name_nice": T("Security"), "module_type": 10}
    modules["supply"] = {"name_nice": T("Supply"), "module_type": None}
    modules["transport"] = {"name_nice": T("Transport"), "module_type": 10}

    # -------------------------------------------------------------------------
    # BR Settings
    #
    #settings.org.default_organisation = "The Collective"
    #settings.br.case_global_default_org = True
    settings.br.case_activity_need_details = True
    settings.br.case_activity_updates = True
    settings.br.case_activity_documents = True
    settings.br.case_address = True
    settings.br.case_id_tab = True
    settings.br.case_language_details = False
    settings.br.case_notes_tab = True
    settings.br.id_card_export_roles = None
    settings.br.manage_assistance = False
    settings.br.needs_org_specific = False

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

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        if tablename == "org_organisation":
            # Realm is own PE ID
            # => use Default Rules
            pass
        elif tablename in ("transport_airport",
                           "transport_airplane",
                           ):
            # No Realm 
            return None
        elif tablename == "pr_person":
            # Staff?
            # Case?
            # Doctor?
            # Case & Doctor?
            pass
        elif tablename == "br_case":
            # Has a unique pr_realm with appropriate multiple inheritance
            pass
        elif tablename == "gis_route":
            # Inherits realm from the Case
            pass
        elif tablename == "br_activity":
            # Has a unique pr_realm with appropriate multiple inheritance
            pass
        elif tablename in ("event_incident_report",
                           "hms_contact",
                           "hms_hospital",
                           "hms_pharmacy",
                           "inv_inv_item",
                           "org_facility",
                           "security_zone",
                           "transport_flight",
                           "vehicle_vehicle",
                           ):
            # Has a unique pr_realm with appropriate multiple inheritance
            pass

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
            affiliate = record["pe_id"]

            # Have the WG inherit from the top-level
            pr_add_affiliation(master_ro, affiliate, role="Realm Hierarchy")

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
            affiliate = record["pe_id"]

            # Have the WG inherit from the top-level
            pr_add_affiliation(master_rw, affiliate, role="Realm Hierarchy")

    # =========================================================================
    def customise_org_organisation_resource(r, tablename):

        current.s3db.add_custom_callback(tablename,
                                         "create_onaccept",
                                         org_organisation_create_onaccept,
                                         )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # =========================================================================
    def br_case_onaccept(form):
        """
            Have a Realm for the Case
            Ensure the correct Inheritance
        """

        from s3db.pr import pr_add_affiliation

        db = current.db
        s3db = current.s3db

        case_id = form.vars.id

        # @ToDo: complete

    # =========================================================================
    def customise_br_case_resource(r, tablename):

        current.s3db.add_custom_callback(tablename,
                                         "onaccept",
                                         br_case_onaccept,
                                         )

    settings.customise_br_case_resource = customise_br_case_resource

# END =========================================================================
