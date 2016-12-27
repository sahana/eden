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

        if r.method == "datalist":
            # Filter to open jobs by default
            from s3 import s3_set_default_filter
            s3_set_default_filter("~.status", "OPEN",
                                  tablename = "work_job",
                                  )
            if r.representation == "html":
                # Set default formstyle for side filter form
                # (=labels above fields)
                filter_formstyle = settings.get_ui_formstyle()
                s3db.configure("work_job",
                               filter_formstyle = filter_formstyle,
                               )

        if not r.component:
            # Return to list after create/update
            r.resource.configure(create_next = r.url(method=""),
                                 update_next = r.url(method=""),
                                 )

        elif r.component_name == "assignment":
            ctable = r.component.table
            field = ctable.person_id

            # Set default to current user if not assigned yet
            logged_in_person = auth.s3_logged_in_person()
            if logged_in_person:
                query = (ctable.job_id == r.id) & \
                        (ctable.person_id == logged_in_person) & \
                        (ctable.deleted != True)
                existing = db(query).select(ctable.id, limitby=(0, 1)).first()
                if not existing:
                    field.default = logged_in_person
                else:
                    field.default = None

        return True
    s3.prep = prep

    def postp(r, output):
        if r.representation == "html" and r.method == "datalist":
            # View template and script for job list
            response.view = "work/joblist.html"
            script = "s3.work.js" if s3.debug else "s3.work.min.js"
            path = "/%s/static/scripts/S3/%s" % (appname, script)
            if path not in s3.scripts:
                s3.scripts.append(path)

            # Hide options menu
            current.menu.options = None

        return output
    s3.postp = postp

    return s3_rest_controller(rheader=s3db.work_rheader)

# -----------------------------------------------------------------------------
def assignment():
    """ Job Assignments - RESTful controller """

    return s3_rest_controller()

# END =========================================================================
