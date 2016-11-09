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

        due_followups = current.s3db.dvr_due_followups() or "0"
        follow_up_label = "%s (%s)" % (current.T("Due Follow-ups"),
                                       due_followups,
                                       )

        ADMIN = current.session.s3.system_roles.ADMIN

        return M(c=("dvr", "project"))(
                    M("Current Cases", c=("dvr", "pr"), f="person",
                      vars = {"closed": "0"})(
                        M("Create", m="create"),
                        M("All Cases", vars = {}),
                        ),
                    M("Activities", f="case_activity")(
                       #M("Create", m="create"),
                        M(follow_up_label, f="due_followups"),
                    ),
                    #M("Need Types", f="need")(
                    #   M("Create", m="create"),
                    #),
                    M("Archive", link=False)(
                        M("Closed Cases", f="person",
                          vars={"closed": "1"},
                          ),
                        M("Invalid Cases", f="person",
                          vars={"archived": "1"},
                          ),
                        ),
                    M("Administration", c="project", link=False,
                      restrict = [ADMIN])(
                        M("Projects", c="project", f="project"),
                        M("Service Types", c="org", f="service"),
                        SEP(),
                        M("Beneficiary Types", c="dvr", f="beneficiary_type"),
                        M("Housing Types", c="dvr", f="housing_type"),
                        M("Income Sources", c="dvr", f="income_source"),
                        M("SNF Justifications", c="dvr", f="case_funding_reason"),
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
