# -*- coding: utf-8 -*-

from gluon import *
from s3 import S3CustomController

THEME = "CumbriaEAC"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        auth = current.auth

        if auth.s3_has_role("POLICE", include_admin=False):
            # Police don't manage Shelters, they are interested in Clients
            redirect(URL(c="pr", f="person", args="summary"))

        output = {}

        T = current.T
        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        roles = current.session.s3.roles
        settings = current.deployment_settings
        system_roles = auth.get_system_roles()

        # Allow editing of page content from browser using CMS module
        if settings.has_module("cms"):
            ADMIN = system_roles.ADMIN in roles
            table = s3db.cms_post
            ltable = s3db.cms_post_module
            module = "default"
            resource = "index"
            query = (ltable.module == module) & \
                    ((ltable.resource == None) | \
                     (ltable.resource == resource)) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            item = db(query).select(table.body,
                                    table.id,
                                    limitby = (0, 1)
                                    ).first()
            if item:
                if ADMIN:
                    item = DIV(XML(item.body),
                               BR(),
                               A(T("Edit"),
                                 _href = URL(c="cms", f="post",
                                             args = [item.id, "update"]),
                                 _class = "action-btn",
                                 ))
                else:
                    item = DIV(XML(item.body))
            elif ADMIN:
                if s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = A(T("Edit"),
                         _href = URL(c="cms", f="post", args="create",
                                     vars = {"module": module,
                                             "resource": resource
                                             }),
                         _class = "%s cms-edit" % _class,
                         )
            else:
                item = ""
        else:
            item = ""
        output["item"] = item

        # Different content depending on whether logged-in or not
        if system_roles.AUTHENTICATED in roles:
            # Provide a way to select the default Shelter (from those which are Open)
            stable = s3db.cr_shelter
            query = (stable.deleted == False) & \
                    (stable.status.belongs(3,4,5))
            shelters = db(query).select(stable.id,
                                        stable.name,
                                        )
            if len(shelters) > 0:
                facility_list = [(row.id, row.name) for row in shelters]
                facility_list = sorted(facility_list, key=lambda fac: fac[1])
                facility_opts = [OPTION(fac[1], _value=fac[0])
                                 for fac in facility_list]
                shelter_id = facility_list[0][0]
                manage_facility_box = DIV(H3(T("Manage your Shelter")),
                                          SELECT(_id = "manage-facility-select",
                                                 *facility_opts
                                                 ),
                                          A(T("Go"),
                                            _href = URL(c="cr", f="shelter",
                                                        args = [shelter_id, "manage"],
                                                        ),
                                            _id = "manage-facility-btn",
                                            _class = "action-btn"
                                            ),
                                          _id = "manage-facility-box",
                                          _class = "menu-box row",
                                          )
            else:
                manage_facility_box = DIV(T("No Open Shelters"),
                                          _class = "menu-box row",
                                          )
            output["manage_facility_box"] = manage_facility_box
            output["find_shelter"] = DIV(A(T("Find a Shelter to Open"),
                                           _href = URL(c="cr", f="shelter",
                                                       args = ["summary"],
                                                       vars = {"~.status__belongs": "1,3,4,5,6",
                                                               },
                                                       )
                                           ),
                                         _class = "menu-box row",
                                         )

            s3.jquery_ready.append('''$('#manage-facility-select').change(function(){
 $('#manage-facility-btn').attr('href',S3.Ap.concat('/cr/shelter/',$('#manage-facility-select').val(),'/manage'))})
$('#manage-facility-btn').click(function(){
if (($('#manage-facility-btn').attr('href').toString())===S3.Ap.concat('/cr/shelter/None'))
{$("#manage-facility-box").append("<div class='alert alert-error'>%s</div>")
return false}})''' % (T("Please Select a Shelter")))
        else:
            # Provide a login box on front page
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system") % \
                                  {"login": B(T("login"))})))
            output["login_div"] = login_div
            output["login_form"] = login_form

        self._view(THEME, "index.html")
        return output

# =============================================================================
def cr_shelter_import_prep(data):
    """
        Called when Shelters are imported from CSV

        Lookups Pseudo-reference fields from Names

        Defined in controllers to be able to import from post-pop as well as config
    """

    db = current.db
    s3db = current.s3db
    update_super = s3db.update_super
    ctable = s3db.cms_post

    tree = data[1]

    def add_plan(name):
        """ Helper to add a New Plan """
        plan_id = ctable.insert(name = name,
                                body = "", # notnull=True
                                )
        record = Storage(id = plan_id)
        update_super(ctable, record)
        # @ToDo: Call set_record_owner?
        # @ToDo: Call onaccept?
        return plan_id

    def plan_lookup(name):
        """ Helper to lookup a Plan """

        query = (ctable.name.lower() == name.lower()) & \
                (ctable.deleted != True)

        records = db(query).select(ctable.id,
                                   limitby = (0, 1)
                                   )
        if len(records):
            record = records.first()
            plan_id = record.id
        else:
            # Add a new record
            plan_id = add_plan(name)

        return plan_id

    # Plans
    # This works for plans, but then other tags don't get imported on 2nd pass! (1st pass OK)
    #elements = tree.getroot().xpath("/s3xml//resource[@alias='plan']/data[@field='value']")
    elements = tree.getroot().xpath("/s3xml//data[@field='tag']")
    looked_up = {}
    #for value_element in elements:
    for tag_element in elements:
        #value = value_element.text
        tag = tag_element.text

        if tag == "plan":
            value_element = tag_element.getnext()
            value = value_element.text
            if value:
                if value in looked_up:
                    # Replace string with plan_id
                    value_element.text = looked_up[value]
                    # Don't check again
                    continue

                # This is a non-integer, so must be 1st or only phase
                plan_id = plan_lookup(value)

                new_value = str(plan_id)
                # Replace string with plan_id
                value_element.text = new_value
                # Store in case we get called again with same value
                looked_up[value] = new_value

# END =========================================================================
