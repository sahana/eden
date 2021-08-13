# -*- coding: utf-8 -*-

#from collections import OrderedDict

from gluon import current#, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Bhutan's extensions to the core SaFiRe template.
    """

    T = current.T

    settings.base.system_name = T("Disaster Management Information System")
    settings.base.system_name_short = T("DMIS")

    # PrePopulate data
    #settings.base.prepopulate.append("SAFIRE/BT")
    settings.base.prepopulate_demo = ("default/users",
                                      "SAFIRE/BT/Demo",
                                      )

    settings.ui.menu_logo = "/%s/static/themes/SaFiRe/BT/DDM.png" % current.request.application

    settings.modules["dc"] = {"name_nice": T("Assessments"), "module_type": 10}
    settings.modules["disease"] = {"name_nice": T("Disease"), "module_type": 10}
    settings.modules["edu"] = {"name_nice": T("Schools"), "module_type": 10}
    settings.modules["stats"] = {"name_nice": T("Statistics"), "module_type": 10}
    settings.modules["transport"] = {"name_nice": T("Transport"), "module_type": 10}
    settings.modules["water"] = {"name_nice": T("Water"), "module_type": 10}

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        list_fields = [(T("Project Name"), "name"),
                       (T("Funding Source"), "donor.organisation_id"),
                       (T("Project Area"), "location.location_id"),
                       (T("Start Date"), "start_date"),
                       (T("End Date"), "end_date"),
                       (T("Budget(Nu in million)"), "budget"),
                       ]

        current.s3db.configure(tablename,
                               list_fields = list_fields,
                               )

    settings.customise_project_project_resource = customise_project_project_resource

# END =========================================================================
