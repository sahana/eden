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

    settings.ui.menu_logo = "/%s/static/themes/SAFIRE/BT/DDM.png" % current.request.application

    modules = settings.modules
    modules["br"] = {"name_nice": T("Case Management"), "module_type": 10}
    modules["dc"] = {"name_nice": T("Assessments"), "module_type": 10}
    modules["disease"] = {"name_nice": T("Disease"), "module_type": 10}
    modules["edu"] = {"name_nice": T("Schools"), "module_type": 10}
    modules["stats"] = {"name_nice": T("Statistics"), "module_type": 10}
    modules["transport"] = {"name_nice": T("Transport"), "module_type": 10}
    modules["water"] = {"name_nice": T("Water"), "module_type": 10}

    settings.supply.catalog_multi = False

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        # Configuration for Suppliers

        list_fields = [(T("Supplier Name"), "name"),
                       (T("Supplier Address"), "donor.organisation_id"),
                       (T("Supplier License Number"), "comments"),
                       (T("Contact No"), "phone"),
                       (T("Email ID"), "contact"),
                       ]

        current.s3db.configure(tablename,
                               list_fields = list_fields,
                               )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

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

    # -------------------------------------------------------------------------
    def customise_supply_catalog_item_resource(r, tablename):

        from s3 import S3Represent

        s3db = current.s3db

        represent = S3Represent(lookup = "supply_item_category")
        s3db.supply_catalog_item.item_category_id.represent = represent
        s3db.supply_item_category.parent_item_category_id.represent = represent

        list_fields = [(T("Item Name"), "item_id$name"),
                       (T("Item Category"), "item_category_id$parent_item_category_id"),
                       (T("Item Sub-category"), "item_category_id"),
                       (T("Base UoM"), "item_id$um"),
                       (T("Brand"), "item_id$brand_id"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_supply_catalog_item_resource = customise_supply_catalog_item_resource

# END =========================================================================
