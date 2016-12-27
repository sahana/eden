# -*- coding: utf-8 -*-

""" Sahana Eden Guided Tour Model

    @copyright: 2009-2016 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

    @todo: update for new template path modules/template
"""

__all__ = ("S3GuidedTourModel",
           "tour_rheader",
           "tour_builder",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3GuidedTourModel(S3Model):

    """ Details about which guided tours this Person has completed """

    names = ("tour_config",
             "tour_details",
             "tour_user",
             )

    def model(self):

        T = current.T
        db = current.db
        NONE = current.messages["NONE"]
        s3 = current.response.s3

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table

        person_id = self.pr_person_id

        # ---------------------------------------------------------------------
        # Guided tours that are available
        #
        tablename = "tour_config"
        define_table(tablename,
                     Field("name",
                           represent=lambda v: v or NONE,
                           label=T("Display name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("code",
                           length=255,
                           notnull=True,
                           unique=True,
                           represent=lambda v: v or NONE,
                           requires = IS_NOT_EMPTY(),
                           label=T("Unique code")),
                     Field("controller",
                           represent=lambda v: v or NONE,
                           label=T("Controller tour is activated")),
                     Field("function",
                           represent=lambda v: v or NONE,
                           label=T("Function tour is activated")),
                     Field("autostart", "boolean",
                           default=False,
                           represent=lambda v: \
                                     T("Yes") if v else T("No"),
                           label=T("Auto start")),
                     Field("role", "string",
                           represent=lambda v: v or NONE,
                           label=T("User's role")),
                     * s3_meta_fields()
                     )

        # CRUD strings
        ADD_TOUR = T("Create Tour")
        crud_strings[tablename] = Storage(
            label_create = ADD_TOUR,
            title_display = T("Tour Configuration"),
            title_list = T("Tours"),
            title_update = T("Edit Tour"),
            label_list_button = T("List Tours"),
            label_delete_button = T("Delete Tour"),
            msg_record_created = T("Tour added"),
            msg_record_modified = T("Tour updated"),
            msg_record_deleted = T("Tour deleted"),
            msg_list_empty = T("No Tours currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        tour_config_id = S3ReusableField("tour_config_id", "reference %s" % tablename,
                                         requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "tour_config.id",
                                                              represent,
                                                              sort=True)),
                                         represent=represent,
                                         label=T("Tour Name"),
                                         ondelete="SET NULL")

        # Components
        add_components(tablename,
                       # Details
                       tour_details="tour_config_id",
                       # Users
                       tour_user="tour_config_id",
                      )

        # ---------------------------------------------------------------------
        # Details of the tour.
        #
        tablename = "tour_details"
        define_table(tablename,
                     tour_config_id(empty = False),
                     Field("posn", "integer",
                           default=0,
                           label=T("Position in tour")),
                     Field("controller",
                           represent=lambda v: v or NONE,
                           label=T("Controller name")),
                     Field("function",
                           represent=lambda v: v or NONE,
                           label=T("Function name")),
                     Field("args",
                           represent=lambda v: v or NONE,
                           label=T("Arguments")),
                     Field("tip_title",
                           represent=lambda v: v or NONE,
                           label=T("Title")),
                     Field("tip_details",
                           represent=lambda v: v or NONE,
                           label=T("Details")),
                     Field("html_id",
                           represent=lambda v: v or NONE,
                           label=T("HTML ID")),
                     Field("html_class",
                           represent=lambda v: v or NONE,
                           label=T("HTML class")),
                     Field("button",
                           represent=lambda v: v or NONE,
                           label=T("Button name")),
                     Field("tip_location",
                           represent=lambda v: v or NONE,
                           label=T("Loctaion of tip")),
                     Field("datatable_id",
                           represent=lambda v: v or NONE,
                           label=T("DataTable ID")),
                     Field("datatable_row",
                           represent=lambda v: v or NONE,
                           label=T("DataTable row")),
                     Field("redirect",
                           represent=lambda v: v or NONE,
                           label=T("Redirect URL")),
                     )
        # CRUD strings
        ADD_DETAILS = T("Create Details")
        crud_strings[tablename] = Storage(
            label_create = ADD_DETAILS,
            title_display = T("Tour Details"),
            title_list = T("Details"),
            title_update = T("Edit Details"),
            label_list_button = T("List Details"),
            label_delete_button = T("Delete Detail"),
            msg_record_created = T("Detail added"),
            msg_record_modified = T("Detail updated"),
            msg_record_deleted = T("Detail deleted"),
            msg_list_empty = T("No Details currently registered"))

        configure(tablename,
                  orderby = "tour_details.tour_config_id,tour_details.posn"
                  )
        # ---------------------------------------------------------------------
        # Details of the tours that the user has taken.
        #
        tablename = "tour_user"
        define_table(tablename,
                     person_id(label = T("Person"),
                               ondelete="CASCADE",
                               empty = False,
                               ),
                     tour_config_id(),
                     Field("place",
                           represent=lambda v: v or NONE,
                           label=T("Where reached")),
                     Field("resume",
                           represent=lambda v: v or NONE,
                           label=T("URL to resume tour")),
                     Field("completed", "boolean",
                           default=False,
                           represent=lambda v: \
                                     T("Yes") if v else T("No"),
                           label=T("Completed tour?")),
                     Field("trip_counter", "integer",
                           default=0,
                           label=T("Times Completed")),
                     )

        # CRUD strings
        ADD_USER = T("Create User")
        crud_strings[tablename] = Storage(
            label_create = ADD_USER,
            title_display = T("Tour User"),
            title_list = T("Users"),
            title_update = T("Edit User"),
            label_list_button = T("List Users"),
            label_delete_button = T("Delete User"),
            msg_record_created = T("User added"),
            msg_record_modified = T("User updated"),
            msg_record_deleted = T("User deleted"),
            msg_list_empty = T("No users have taken a tour"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(tour_config_id = tour_config_id,
                    )

# =============================================================================
def tour_rheader(r):
    """ Resource Header for Guided Tour """

    if r.representation == "html":
        tour = r.record
        if tour:
            T = current.T
            tabs = [(T("Edit Details"), None),
                    (T("Details"), "details"),
                    (T("People"), "user"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   tour.name,
                                   ),
                                TR(TH("%s: " % table.code.label),
                                   tour.code,
                                   ),
                                ),
                          rheader_tabs
                          )
            return rheader
    return None

# =============================================================================
def tour_builder(output):
    """
         Helper function to attach a guided tour (if required) to the output
    """

    auth = current.auth
    db = current.db
    s3db = current.s3db
    request = current.request
    s3 = current.response.s3
    T = current.T

    req_vars = request.vars
    tour_id = req_vars.tour
    # Now see if the details are on the database for this user
    tour = None
    user_id = None
    if auth.is_logged_in():
        user_id = auth.s3_logged_in_person()
        # Find out if the user has done this tour before
        utable = s3db.tour_user
        uquery = (utable.person_id == user_id) & \
                (utable.tour_config_id == tour_id)
        tour = db(uquery).select(utable.id,
                                utable.completed,
                                utable.place,
                                utable.resume,
                                limitby=(0, 1)).first()
        # If the tour has just been started (from the menu) then
        # it may be necessary to redirect to a different controller
        # @todo: does place need to be changed to controller and function?
        if not req_vars.tour_running:
            if (tour and not tour.completed and tour.place != request.controller):
                redirect("%s?tour=%s" %(tour.resume, tour_id))

    # get the details from the database
    dtable = s3db.tour_details
    dquery = (dtable.tour_config_id == tour_id) &\
            (dtable.controller == request.controller) &\
            (dtable.function == request.function)
    details = db(dquery).select(dtable.args,
                               dtable.tip_title,
                               dtable.tip_details,
                               dtable.button,
                               dtable.tip_location,
                               dtable.html_id,
                               dtable.html_class,
                               dtable.datatable_id,
                               dtable.datatable_row,
                               dtable.redirect,
                               orderby=(dtable.posn)
                               )
#        tour_filename = os.path.join(request.folder,
#                                     "private",
#                                     "tour",
#                                     tour_name)
#        tour_file = open (tour_filename, "rb")
#        # now open the details of the guided_tour into a dictionary
#        import csv
#        tour_details = csv.DictReader(tour_file, skipinitialspace=True)
    # load the list of tour items in the html
    joyride_OL = OL(_id="joyrideID_1")
    pre_step_data = []
    post_step_data = []
    post_ride_data = []
    last_row = None
    last_used = None
    req_args = request.args
    cnt = -1
    for row in details:
        if row.args:
            args = row.args.split(",")
        else:
            args = []
        # if the page has a nested login form then "login" will be added to
        # the req_args list so it needs to be added to the args list as well
        if "login" in req_args:
            if "login" not in args:
                args.append("login")
        # The following will capture the actual id used for the req_arg
        # Example org/organisation/10, where 10 is the id from the database
        posn = 0
        for arg in args:
            if arg == "dt_id":
                args[posn] = req_args[posn]
            posn += 1
        # Now check that the tour url matches the current url
        if (args == req_args):
            cnt += 1 # number of records used in this part of the tour
            if row.datatable_id:
                dt_id = row.datatable_id
#                    cols = []
#                    if "DataTable_columns" in row:
#                        cols = row["DataTable_columns"].split(",")
                row_num = 0
                if row.datatable_row:
                    row_num = row.datatable_row
                # Now set this up for the pre-processor hook in joyride
                pre_step_data.append([cnt, dt_id, row_num])
            if row.redirect:
                redirect_row = row.redirect.split(",")
                if len(redirect_row) >= 3:
                    url = URL(c=redirect_row[0],
                              f=redirect_row[1],
                              args=redirect_row[2:],
                              vars={"tour_running":True,
                                    "tour":tour_id}
                              )
                    if "dt_id" in redirect_row[2]:
                        post_step_data.append([cnt, url, dt_id, row_num])
                elif len(redirect_row) == 2:
                    url = URL(c=redirect_row[0],
                              f=redirect_row[1],
                              vars={"tour_running":True,
                                    "tour":tour_id}
                              )
                    post_step_data.append([cnt, url])
                else:
                    url = URL(c=redirect_row[0],vars={"tour_running":True,
                                                  "tour":tour_id})
                    post_step_data.append([cnt, url])
            extra = {}
            if row.html_id:
                extra["_data-id"] = row.html_id
            elif row.html_class:
                extra["_data-class"] = row.html_class
            if row.button:
                extra["_data-button"] = row.button
            else:
                extra["_data-button"] = "Next"
            if row.tip_location:
                extra["_data-options"] = "tipLocation:%s" % row.tip_location.lower()
            else:
                extra["_data-options"] = "tipLocation:right"
            joyride_OL.append(LI(H2(T(row.tip_title)),
                                 P(T(row.tip_details)),
                                    **extra
                                 )
                              )
            last_used = row
        last_row = row
    # The following redirect will be triggered if the user has moved away
    # from the tour, such as by clicking on a tab. However if a tab
    # is part of the tour we are unable to determine if they have moved
    # away or just visiting as part of the tour and so it will continue.
    if len(joyride_OL) == 0:
        del request.vars.tour
        redirect(URL(args=req_args,
                     vars=request.vars))
    if (user_id != None) and (last_row == last_used):
        # set up an AJAX call to record that the tour has been completed
        post_ride_data = [cnt, tour_id]
    joyride_div = DIV(joyride_OL,
                      _class="hidden")
    # Add the javascript configuration data
    from gluon.serializers import json as jsons
    if pre_step_data:
        joyride_div.append(INPUT(_type="hidden",
                                 _id="prestep_data",
                                 _name="prestep_data",
                                 _value=jsons(pre_step_data))
                           )
    if post_step_data:
        joyride_div.append(INPUT(_type="hidden",
                                 _id="poststep_data",
                                 _name="poststep_data",
                                 _value=jsons(post_step_data))
                           )
    if post_ride_data:
        joyride_div.append(INPUT(_type="hidden",
                                 _id="postride_data",
                                 _name="postride_data",
                                 _value=jsons(post_ride_data))
                           )
    # Now add the details to the tour_user table
    if user_id != None:
        if tour == None:
            # this user has never done this tour before so create a new record
            utable.insert(person_id = user_id,
                          tour_config_id = tour_id,
                          place = request.controller,
                          resume = request.url)
        else:
            # the user has done some of this tour so update the record
            db(uquery).update(place = request.controller,
                             resume = request.url,
                             completed = False)

    output["joyride_div"] = joyride_div
    if s3.debug:
        appname = request.application
        s3.scripts.append("/%s/static/scripts/jquery.joyride.js" % appname)
        s3.scripts.append("/%s/static/scripts/S3/s3.guidedtour.js" % appname)
        s3.stylesheets.append("plugins/joyride.min.css")
    else:
        s3.scripts.append("/%s/static/scripts/S3/s3.guidedtour.min.js" % request.application)
        s3.stylesheets.append("plugins/joyride.css")
    return output

# END =========================================================================
