# -*- coding: utf-8 -*-

from os import path

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

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
def update_transferability():
    """
        Update transferability status of all cases, to be called either
        from scheduler task or manually through custom controller.

        @todo: complete criteria
        @todo: make a function of that custom controller class
        @todo: call from org_site_check task
    """

    # @todo: check that we have admin permissions

    db = current.db
    s3db = current.s3db

    now = current.request.utcnow

    ptable = s3db.pr_person
    ctable = s3db.dvr_case
    stable = s3db.dvr_case_status
    utable = s3db.cr_shelter_unit
    rtable = s3db.cr_shelter_registration
    ttable = s3db.dvr_case_appointment_type
    atable = s3db.dvr_case_appointment

    # Set transferable=False for all cases
    query = (ctable.deleted != True)
    db(query).update(transferable = False)

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

    for age_group in age_groups:

        min_age, max_age, appointment_flag, maximum_absence = age_groups[age_group]

        # Translate Age Group => Date of Birth
        dob_query = (ptable.date_of_birth != None)
        from dateutil.relativedelta import relativedelta
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

        # Case must not have a non-transferable status
        case_query &= (stable.is_not_transferable == False) | \
                      (stable.is_not_transferable == None)

        # Person must be assigned to a non-transitory housing unit
        case_query &= (utable.id != None) & \
                      ((utable.transitory == False) | \
                       (utable.transitory == None))

        # Add date-of-birth query
        case_query &= dob_query

        # @todo: check that we do not yet have a "reported transferable date"

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
        cases = db(case_query).select(ctable.id,
                                      left = left,
                                      )
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

                TODAY = now.date()
                ONE_YEAR_AGO = (now - relativedelta(years=1)).date()

                # Appointment statuses which do not count as valid dates
                MISSED = 5
                CANCELLED = 6

                # Appointment statuses which override the requirement
                NOT_REQUIRED = 7

                # Join the valid appointment dates
                for appointment_type_id in mandatory_appointments:

                    alias = "appointments_%s" % appointment_type_id
                    atable_ = atable.with_alias(alias)

                    join = atable_.on((atable_.person_id == ctable.person_id) & \
                                      (atable_.type_id == appointment_type_id) & \
                                      (atable_.deleted != True) & \
                                      (((atable_.status != MISSED) & \
                                        (atable_.status != CANCELLED) & \
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
            db(ctable.id.belongs(case_ids)).update(transferable=True)

# END =========================================================================
