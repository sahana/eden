# -*- coding: utf-8 -*-

"""
    Work Items Management - Controllers
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    # Redirect to job list
    s3_redirect_default(URL(f="job", args=["datalist"]))

# -----------------------------------------------------------------------------
def context():
    """ Work Context - RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def job_type():
    """ Job Types - RESTful controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def job():
    """ Jobs - RESTful controller """

    def prep(r):
        # @todo: for assigments, filter person_id to persons not
        #        currently assigned to this job

        # @todo: for assigments, set default to current user if
        #        not assigned to this job yet

        if r.representation == "html" and r.method == "datalist":
            # Filter to open jobs by default
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.status", "OPEN",
                                  tablename = "work_job",
                                  )
            # Set default formstyle for side filter form
            # (=labels above fields)
            filter_formstyle = settings.get_ui_formstyle()
            s3db.configure("work_job",
                           filter_formstyle = filter_formstyle,
                           )

        if not r.component:
            r.resource.configure(create_next = r.url(method=""),
                                 update_next = r.url(method=""),
                                 )
        return True
    s3.prep = prep

    def postp(r, output):
        if r.representation == "html" and r.method == "datalist":
            # View template and script for job list
            response.view = "work/joblist.html"
            script = "/%s/static/scripts/S3/s3.work.js" % r.application
            if script not in s3.scripts:
                s3.scripts.append(script)
            # Hide options menu
            current.menu.options = None

        return output
    s3.postp = postp

    return s3_rest_controller(rheader = s3db.work_rheader)

# -----------------------------------------------------------------------------
def assignment():
    """ Job Assignments - RESTful controller """

    return s3_rest_controller()

# END =========================================================================
