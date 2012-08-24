# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from eden.layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import eden.menus as default

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customized separately,
        by simply overriding (re-defining) the default function. The
        options menu function must return an instance of the item layout.

        The standard menu uses the M item layout class, but you can of
        course also use any other layout class which you define in
        layouts.py (can also be mixed).

        Make sure additional helper functions in this class don't match
        any current or future controller prefix (e.g. by using an
        underscore prefix).
    """

    # -------------------------------------------------------------------------
    def hrm(self):
        """ HRM / Human Resources Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles
        settings = current.deployment_settings
        job_roles = lambda i: settings.get_hrm_job_roles()
        use_teams = lambda i: settings.get_hrm_use_teams()

        return M(c="hrm")(
                    M("Staff", f="staff",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"staff"}, p="create"),
                    ),
                    M("Teams", f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=[manager_mode, job_roles])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Title Catalog", f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Skill Catalog", f="skill",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Provisions", f="skill_provision"),
                    #),
                    #M("Training Events", f="training_event",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    M("Search", m="search"),
                    #    M("Search Training Participants", f="training",
                    #      m="search"),
                    #    M("Import Participant List", f="training", m="import"),
                    #),
                    #M("Training Course Catalog", f="course",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Course Certificates", f="course_certificate"),
                    #),
                    #M("Certificate Catalog", f="certificate",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Equivalence", f="certificate_skill"),
                    #),
                    M("Reports", f="staff", m="report",
                      check=manager_mode)(
                        M("Staff Report", m="report"),
                        M("Expiring Staff Contracts Report",
                          vars=dict(expiring=1)),
                    #    M("Training Report", f="training", m="report"),
                    ),
                    M("Personal Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    # This provides the link to switch to the manager mode:
                    M("Staff Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", f="person",
                    #  check=manager_mode, vars=dict(mode="personal"))
                )

    # -------------------------------------------------------------------------
    def vol(self):
        """ Volunteer Management """

        s3 = current.session.s3
        ADMIN = s3.system_roles.ADMIN

        # Custom conditions for the check-hook, as lambdas in order
        # to have them checked only immediately before rendering:
        manager_mode = lambda i: s3.hrm.mode is None
        personal_mode = lambda i: s3.hrm.mode is not None
        is_org_admin = lambda i: s3.hrm.orgs and True or \
                                 ADMIN in s3.roles

        settings = current.deployment_settings
        job_roles = lambda i: settings.get_hrm_job_roles()
        show_programmes = lambda i: settings.get_hrm_vol_experience() == "programme"
        show_tasks = lambda i: settings.has_module("project") and \
                               settings.get_project_mode_task()
        use_teams = lambda i: settings.get_hrm_use_teams()

        if job_roles(""):
            jt_catalog_label = "Job Title Catalog"
        else:
            jt_catalog_label = "Volunteer Role Catalog"

        return M(c="vol")(
                    M("Volunteers", f="volunteer",
                      check=[manager_mode])(
                        M("New", m="create"),
                        M("List All"),
                        M("Search", m="search"),
                        M("Import", f="person", m="import",
                          vars={"group":"volunteer"}, p="create"),
                    ),
                    M("Teams", f="group",
                      check=[manager_mode, use_teams])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M("Job Role Catalog", f="job_role",
                      check=[manager_mode, job_roles])(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    M(jt_catalog_label, f="job_title",
                      check=manager_mode)(
                        M("New", m="create"),
                        M("List All"),
                    ),
                    #M("Skill Catalog", f="skill",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Provisions", f="skill_provision"),
                    #),
                    #M("Training Events", f="training_event",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    M("Search", m="search"),
                    #    M("Search Training Participants", f="training",
                    #      m="search"),
                    #    M("Import Participant List", f="training", m="import"),
                    #),
                    #M("Training Course Catalog", f="course",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Course Certificates", f="course_certificate"),
                    #),
                    #M("Certificate Catalog", f="certificate",
                    #  check=manager_mode)(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    #M("Skill Equivalence", f="certificate_skill"),
                    #),
                    #M("Programmes", f="programme",
                    #  check=[manager_mode, show_programmes])(
                    #    M("New", m="create"),
                    #    M("List All"),
                    #    M("Import Hours", f="programme_hours", m="import"),
                    #),
                    M("Reports", f="volunteer", m="report",
                      check=manager_mode)(
                        M("Volunteer Report", m="report"),
                    #    M("Training Report", f="training", m="report"),
                    ),
                    M("My Profile", f="person",
                      check=personal_mode, vars=dict(mode="personal")),
                    M("My Tasks", f="task",
                      check=[personal_mode, show_tasks],
                      vars=dict(mode="personal",
                                mine=1)),
                    # This provides the link to switch to the manager mode:
                    M("Volunteer Management", f="index",
                      check=[personal_mode, is_org_admin]),
                    # This provides the link to switch to the personal mode:
                    #M("Personal Profile", f="person",
                    #  check=manager_mode, vars=dict(mode="personal"))
                )

# END =========================================================================
