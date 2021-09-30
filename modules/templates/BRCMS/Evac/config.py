# -*- coding: utf-8 -*-

"""
    Application Template for supporting Evacuations of Personnel
    - e.g. from Afghanistan
"""

from gluon import current

# =============================================================================
def config(settings):

    T = current.T

    settings.base.system_name = "Evacuation Management System"
    settings.base.system_name_short =  "EMS"

    # PrePopulate data
    settings.base.prepopulate.append("BRCMS/Evac")
    #settings.base.prepopulate_demo.append("BRCMS/Evac/Demo")

    modules = settings.modules
    modules["asset"] = {"name_nice": T("Assets"), "module_type": 10}
    modules["fin"] = {"name_nice": T("Finances"), "module_type": 10}
    modules["hms"] = {"name_nice": T("Hospitals"), "module_type": 10}
    modules["security"] = {"name_nice": T("Security"), "module_type": 10}
    modules["supply"] = {"name_nice": T("Supply"), "module_type": None}
    modules["vehicle"] = {"name_nice": T("Vehicle"), "module_type": 10}

    # -------------------------------------------------------------------------
    # BR Settings
    #
    settings.org.default_organisation = "The Collective"
    settings.br.case_global_default_org = True
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
    settings.hrm.teams = False
    settings.hrm.use_address = False
    settings.hrm.use_id = False
    settings.hrm.use_skills = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def evac_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        realm_entity = 0

        return realm_entity

    #settings.auth.realm_entity = evac_realm_entity

# END =========================================================================
