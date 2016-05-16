# -*- coding: utf-8 -*-

import json

from os import path

from gluon import current
from gluon.html import *
from gluon.storage import Storage
from gluon.http import redirect

from s3 import FS, S3CustomController
from s3theme import formstyle_foundation_inline

THEME = "DRK"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T
        request = current.request
        response = current.response
        s3 = response.s3

        # Check logged in and permissions
        auth = current.auth
        settings = current.deployment_settings
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        # Login/Registration forms
        self_registration = current.deployment_settings.get_security_registration_visible()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None

        # Contact Form
        request_email = settings.get_frontpage("request_email")
        if request_email:
            from s3dal import Field
            from gluon.validators import IS_NOT_EMPTY
            from gluon.sqlhtml import SQLFORM
            fields = [Field("name",
                            label="Your name",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("address",
                            label="Your e-mail address",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("subject",
                            label="Subject",
                            requires=IS_NOT_EMPTY(),
                            ),
                      Field("message", "text",
                            label="Message",
                            requires=IS_NOT_EMPTY(),
                            ),
                      ]
            from s3 import s3_mark_required
            labels, required = s3_mark_required(fields)
            s3.has_required = required

            response.form_label_separator = ""
            contact_form = SQLFORM.factory(formstyle = settings.get_ui_formstyle(),
                                           submit_button = T("Submit"),
                                           labels = labels,
                                           separator = "",
                                           table_name = "contact", # Dummy table name
                                           _id="mailform",
                                           *fields
                                           )

            if contact_form.accepts(request.post_vars,
                                    current.session,
                                    formname="contact_form",
                                    keepvalues=False,
                                    hideerror=False):
                # Processs Contact Form
                form_vars = contact_form.vars
                sender = "%s <%s>" % (form_vars.name, form_vars.address)
                result = current.msg.send_email(to=request_email,
                                                sender=sender,
                                                subject=form_vars.subject,
                                                message=form_vars.message,
                                                reply_to=form_vars.address,
                                                )
                if result:
                    response.confirmation = "Thank you for your message - we'll be in touch shortly"
            if s3.cdn:
                if s3.debug:
                    s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.js")
                else:
                    s3.scripts.append("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.9/jquery.validate.min.js")
            else:
                if s3.debug:
                    s3.scripts.append("/%s/static/scripts/jquery.validate.js" % request.application)
                else:
                    s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % request.application)
            validation_script = '''
$('#mailform').validate({
 errorClass:'req',
 rules:{
  name:{
   required:true
  },
  address: {
   required:true,
   email:true
  },
  subject:{
   required:true
  },
  message:{
   required:true
  }
 },
 messages:{
  name:"Enter your name",
  subject:"Enter a subject",
  message:"Enter a message",
  address:{
   required:"Please enter a valid email address",
   email:"Please enter a valid email address"
  }
 },
 errorPlacement:function(error,element){
  error.appendTo(element.parents('div.controls'))
 },
 submitHandler:function(form){
  form.submit()
 }
})'''
            s3.jquery_ready.append(validation_script)

        else:
            contact_form = ""

        if AUTHENTICATED not in roles:

            login_buttons = DIV(A(T("Login"),
                                  _id="show-login",
                                  _class="tiny secondary button"),
                                _id="login-buttons"
                                )
            script = '''
$('#show-mailform').click(function(e){
 e.preventDefault()
 $('#intro').slideDown(400, function() {
   $('#login_box').hide()
 });
})
$('#show-login').click(function(e){
 e.preventDefault()
 $('#login_form').show()
 $('#register_form').hide()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
            s3.jquery_ready.append(script)

            # This user isn't yet logged-in
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration is True:
                # Provide a Registration box on front page
                login_buttons.append(A(T("Register"),
                                       _id="show-register",
                                       _class="tiny secondary button",
                                       _style="margin-left:5px"))
                script = '''
$('#show-register').click(function(e){
 e.preventDefault()
 $('#login_form').hide()
 $('#register_form').show()
 $('#login_box').show()
 $('#intro').slideUp()
})'''
                s3.jquery_ready.append(script)

                register_form = auth.register()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you would like to help, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                register_script = '''
$('#register-btn').click(function(e){
 e.preventDefault()
 $('#register_form').show()
 $('#login_form').hide()
})
$('#login-btn').click(function(e){
 e.preventDefault()
 $('#register_form').hide()
 $('#login_form').show()
})'''
                s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  dict(login=B(T("login"))))))

        else:
            login_buttons = ""

        output["login_buttons"] = login_buttons
        output["self_registration"] = self_registration
        output["registered"] = registered
        output["login_div"] = login_div
        output["login_form"] = login_form
        output["register_div"] = register_div
        output["register_form"] = register_form
        output["contact_form"] = contact_form

        # Slick slider
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/slick.js" % request.application)
        else:
            s3.scripts.append("/%s/static/scripts/slick.min.js" % request.application)
        script = '''
$(document).ready(function(){
 $('#title-image').slick({
  autoplay:true,
  autoplaySpeed:5000,
  speed:1000,
  fade:true,
  cssEase:'linear'
 });
});'''
        s3.jquery_ready.append(script)

        s3.stylesheets.append("../themes/%s/homepage.css" % THEME)
        self._view(THEME, "index.html")

        return output

# =============================================================================
class transferability(S3CustomController):
    """ Custom controller to update transferability status """

    def __call__(self):

        auth = current.auth
        ADMIN = auth.get_system_roles().ADMIN

        if auth.s3_has_role(ADMIN):

            T = current.T

            form = FORM(H3(T("Check transferability for all current cases")),
                        INPUT(_type="submit", _value=T("Update now"), _class="tiny primary button"),
                        P("(%s)" % T("This process can take a couple of minutes")),
                        )

            if form.accepts(current.request.post_vars, current.session):

                # Get default site
                default_site = current.deployment_settings.get_org_default_site()

                # Update transferability
                result = update_transferability(site_id=default_site)
                if result:
                    msg = current.T("%(number)s transferable cases found") % {"number": result}
                    current.session.confirmation = msg
                else:
                    msg = current.T("No transferable cases found")
                    current.session.warning = msg

                # Forward to list of transferable cases
                redirect(URL(c = "dvr",
                            f = "person",
                            vars = {"closed": "0",
                                    "dvr_case.transferable__belongs": "True",
                                    "show_family_transferable": "1",
                                    },
                            ))

            self._view(THEME, "transferability.html")
            return {"form": form}

        else:
            auth.permission.fail()

# =============================================================================
def update_transferability(site_id=None):
    """
        Update transferability status of all cases, to be called either
        from scheduler task or manually through custom controller.

        @todo: call from org_site_check task
        @todo: check household transferability
    """

    db = current.db
    s3db = current.s3db

    now = current.request.utcnow

    from dateutil.relativedelta import relativedelta
    TODAY = now.date()
    ONE_YEAR_AGO = (now - relativedelta(years=1)).date()

    ptable = s3db.pr_person
    ctable = s3db.dvr_case
    stable = s3db.dvr_case_status
    ftable = s3db.dvr_case_flag
    cftable = s3db.dvr_case_flag_case
    utable = s3db.cr_shelter_unit
    rtable = s3db.cr_shelter_registration
    ttable = s3db.dvr_case_appointment_type
    atable = s3db.dvr_case_appointment

    # Appointment status "completed"
    COMPLETED = 4

    # Appointment statuses which override the requirement
    NOT_REQUIRED = 7

    # Set transferable=False for all cases
    query = (ctable.deleted != True)
    db(query).update(transferable = False,
                     household_transferable = False,
                     )

    # Get IDs of "Reported Transferable" and "Transfer" appointment types
    query = ((ttable.name == "Reported Transferable") | \
             (ttable.name == "Transfer")) & \
            (ttable.deleted != True)
    rows = db(query).select(ttable.id, limitby = (0, 2))
    if rows:
        transferability_complete = set(row.id for row in rows)
    else:
        transferability_complete = None

    # Get IDs of open case statuses
    query = ((stable.is_closed == False) | \
             (stable.is_closed == None)) & \
            (stable.deleted != True)
    rows = db(query).select(stable.id)
    if rows:
        OPEN = set(row.id for row in rows)
    else:
        OPEN = None

    # Get IDs of non-transferable case flags
    query = (ftable.is_not_transferable == True) & \
            (ftable.deleted != True)
    rows = db(query).select(ftable.id)
    if rows:
        NOT_TRANSFERABLE = set(row.id for row in rows)
    else:
        NOT_TRANSFERABLE = None

    # Define age groups (minimum age, maximum age, appointments, maximum absence)
    age_groups = {"children": (None, 15, "mandatory_children", None),
                  "adolescents": (15, 18, "mandatory_adolescents", None),
                  "adults": (18, None, "mandatory_adults", 4),
                  }

    # Define left joins for base criteria
    left = [stable.on(stable.id == ctable.status_id),
            ptable.on(ptable.id == ctable.person_id),
            rtable.on((rtable.person_id == ptable.id) &
                      (rtable.deleted != True)),
            utable.on(utable.id == rtable.shelter_unit_id),
            ]

    # Add left join for "reported transferable" date
    if transferability_complete:
        tctable = atable.with_alias("transferability_complete")
        tcjoin = tctable.on((tctable.person_id == ctable.person_id) & \
                            (tctable.type_id.belongs(transferability_complete)) & \
                            (tctable.deleted != True) & \
                            (tctable.date != None) & \
                            (tctable.date >= ONE_YEAR_AGO) & \
                            (tctable.date <= TODAY) & \
                            (tctable.status == COMPLETED))
        left.append(tcjoin)

    # Add left join for non-transferable case flags
    if NOT_TRANSFERABLE:
        cfjoin = cftable.on((cftable.person_id == ctable.person_id) & \
                            (cftable.flag_id.belongs(NOT_TRANSFERABLE)) & \
                            (cftable.deleted != True))
        left.append(cfjoin)

    result = 0
    for age_group in age_groups:

        min_age, max_age, appointment_flag, maximum_absence = age_groups[age_group]

        # Translate Age Group => Date of Birth
        dob_query = (ptable.date_of_birth != None)
        if max_age:
            dob_min = now - relativedelta(years=max_age)
            dob_query &= (ptable.date_of_birth > dob_min)
        if min_age:
            dob_max = now - relativedelta(years=min_age)
            dob_query &= (ptable.date_of_birth <= dob_max)

        # Case must be valid
        case_query = (ctable.deleted != True) & \
                     ((ctable.archived == False) | \
                      (ctable.archived == None))
        if OPEN:
            # Check only open cases
            case_query &= ctable.status_id.belongs(OPEN)

        # Check for site
        if site_id:
            case_query &= (ctable.site_id == site_id)

        # Case must not have a non-transferable status
        case_query &= (stable.is_not_transferable == False) | \
                      (stable.is_not_transferable == None)

        # Case must not have a non-transferable case flag
        if NOT_TRANSFERABLE:
            case_query &= (cftable.id == None)

        # Person must be assigned to a non-transitory housing unit
        case_query &= (utable.id != None) & \
                      ((utable.transitory == False) | \
                       (utable.transitory == None))

        # Add date-of-birth query
        case_query &= dob_query

        # Check that transferability management is not complete
        # (=no completed appointment for "Reported Transferable" or "Transfer")
        if transferability_complete:
            case_query &= (tctable.id == None)

        # Filter by presence if required
        if maximum_absence is not None:
            if maximum_absence:
                # Must be checked-in or checked-out for less
                # than maximum_absence days
                earliest_check_out_date = now - \
                                          relativedelta(days = maximum_absence)
                presence_query = (rtable.registration_status == 2) | \
                                 ((rtable.registration_status == 3) & \
                                  (rtable.check_out_date > earliest_check_out_date))
            else:
                # Must be checked-in or checked-out
                presence_query = (rtable.registration_status.belongs(2, 3))
            case_query &= presence_query

        # Select all cases for this age group:
        cases = db(case_query).select(ctable.id, left = left)
        case_ids = set(case.id for case in cases)

        if case_ids:

            # Check for mandatory appointments
            query = ctable.id.belongs(case_ids)
            aleft = []

            # Get all mandatory appointment types for this age groups:
            if appointment_flag:
                tquery = (ttable[appointment_flag] == True) & \
                         (ttable.deleted != True)
                rows = db(tquery).select(ttable.id)
                mandatory_appointments = [row.id for row in rows]
            else:
                mandatory_appointments = None

            if mandatory_appointments:

                # Join the valid appointment dates
                for appointment_type_id in mandatory_appointments:

                    alias = "appointments_%s" % appointment_type_id
                    atable_ = atable.with_alias(alias)

                    join = atable_.on((atable_.person_id == ctable.person_id) & \
                                      (atable_.type_id == appointment_type_id) & \
                                      (atable_.deleted != True) & \
                                      (((atable_.status == COMPLETED) & \
                                        (atable_.date != None) & \
                                        (atable_.date >= ONE_YEAR_AGO) & \
                                        (atable_.date <= TODAY)) | \
                                        (atable_.status == NOT_REQUIRED)))
                    aleft.append(join)
                    query &= (atable_.id != None)

                # Select all cases that have the required appointment dates
                cases = db(query).select(ctable.id, left=aleft)
                case_ids = set(case.id for case in cases)

            # Set the matching cases transferable=True
            success = db(ctable.id.belongs(case_ids)).update(transferable=True)
            if success:
                result += success

    # Check transferability of families
    gtable = s3db.pr_group
    mtable = s3db.pr_group_membership
    # Family = Case Group (group type 7)
    query = (gtable.group_type == 7) & \
            (gtable.deleted != True) & \
            (ctable.id != None)

    # Find all case groups which have no currently transferable member
    left = [mtable.on((mtable.group_id == gtable.id) & \
                      (mtable.deleted != True)),
            ctable.on((ctable.person_id == mtable.person_id) &
                      (ctable.transferable == True)),
            ]
    members = ctable.id.count()
    rows = db(query).select(gtable.id,
                            groupby = gtable.id,
                            having = (members == 0),
                            left = left,
                            )
    group_ids = set(row.id for row in rows)

    # Add all case groups which have at least one non-transferable member
    open_case = (ctable.archived != True) & \
                (ctable.deleted != True)
    if OPEN:
        open_case = (ctable.status_id.belongs(OPEN)) & open_case

    if group_ids:
        query &= (~(gtable.id.belongs(group_ids)))
    left = [mtable.on((mtable.group_id == gtable.id) & \
                      (mtable.deleted != True)),
            ctable.on((ctable.person_id == mtable.person_id) & \
                      open_case & \
                      ((ctable.transferable == False) | \
                       (ctable.transferable == None))),
            ]
    if transferability_complete:
        left.append(tcjoin)
        query &= (tctable.id == None)

    rows = db(query).select(gtable.id,
                            groupby = gtable.id,
                            left = left,
                            )
    group_ids |= set(row.id for row in rows)

    # Find all cases which do not belong to any of these
    # non-transferable case groups, but either belong to
    # another case group or are transferable themselves
    ftable = mtable.with_alias("family")
    left = [mtable.on((mtable.person_id == ctable.person_id) & \
                      (mtable.group_id.belongs(group_ids)) & \
                      (mtable.deleted != True)),
            gtable.on((ftable.person_id == ctable.person_id) & \
                      (ftable.deleted != True) & \
                      (gtable.id == ftable.group_id) & \
                      (gtable.group_type == 7)),
            ]
    query = (mtable.id == None) & (ctable.deleted != True)
    families = gtable.id.count()
    required = ((families > 0) | (ctable.transferable == True))
    rows = db(query).select(ctable.id,
                            groupby = ctable.id,
                            having = required,
                            left = left,
                            )

    # ...and set them household_transferable=True:
    case_ids = set(row.id for row in rows)
    if case_ids:
        db(ctable.id.belongs(case_ids)).update(household_transferable=True)

    return result

# END =========================================================================
