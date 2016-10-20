# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        #sysname = current.deployment_settings.get_system_name_short()
        return [
            #homepage(),
            MM("Case Management", c=("dvr", "pr")),
            #homepage("gis"),
            homepage("org"),
            #homepage("hrm"),
            MM("Staff", c="hrm", f="staff"),
            #homepage("cr"),
        ]
    # -------------------------------------------------------------------------
    @classmethod
    def menu_help(cls, **attr):
        """ Help Menu """

        menu_help = MM("Help", c="default", f="help", **attr)(
            MM("Contact us", f="contact"),
            MM("About Us", f="about"),
        )
        return menu_help

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def dvr():
        """ DVR / Disaster Victim Registry """

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c=("dvr", "project"))(
                    M("Cases", c=("dvr", "pr"), f="person")(
                        M("Create", m="create"),
                        #M("Archived Cases", vars={"archived": "1"}),
                    ),
                    #M("Case Types", f="case_type")(
                    #    M("Create", m="create"),
                    #),
                    #M("Need Types", f="need")(
                    #   M("Create", m="create"),
                    #),
                    #M("Housing Types", f="housing_type")(
                    #   M("Create", m="create"),
                    #),
                    #M("Income Sources", f="income_source")(
                    #  M("Create", m="create"),
                    #),
                    #M("Beneficiary Types", f="beneficiary_type")(
                    #   M("Create", m="create"),
                    #),
                    M("Administration", c="project", link=False,
                      restrict = [ADMIN])(
                        M("Projects", c="project", f="project"),
                    ),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def project(cls):
        """ PROJECT - use DVR menu """

        return cls.dvr()

    # -------------------------------------------------------------------------
    @staticmethod
    def org():
        """ ORG / Organization Registry """

        settings = current.deployment_settings
        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c="org")(
                    M("Organizations", f="organisation")(
                        M("Create", m="create"),
                        M("Import", m="import")
                    ),
                    #M("Offices", f="office")(
                    #    M("Create", m="create"),
                    #    M("Map", m="map"),
                    #    M("Import", m="import")
                    #),
                    #M("Facilities", f="facility")(
                    #    M("Create", m="create"),
                    #    M("Import", m="import"),
                    #),
                    M("Organization Types", f="organisation_type",
                      restrict = [ADMIN])(
                        M("Create", m="create"),
                    ),
                    #M("Office Types", f="office_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                    #M("Facility Types", f="facility_type",
                    #  restrict=[ADMIN])(
                    #    M("Create", m="create"),
                    #),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def hrm():
        """ HRM / Human Resources Management """

        settings = current.deployment_settings

        session_s3 = current.session.s3
        ADMIN = session_s3.system_roles.ADMIN

        manager_mode = lambda i: session_s3.hrm.mode is None
        #personal_mode = lambda i: session_s3.hrm.mode is not None

        return M(c="hrm")(
                    M(settings.get_hrm_staff_label(), f="staff", #m="summary",
                      check = manager_mode)(
                        M("Create", m="create"),
                        M("Import", f="person", m="import", p="create",
                          vars = {"group": "staff"},
                          ),
                      ),
                    M("Job Title Catalog", f="job_title",
                      check = manager_mode,
                      restrict = [ADMIN])(
                        M("Create", m="create"),
                      ),
                    )

# END =========================================================================
