# -*- coding: utf-8 -*-

"""
    Evacuees Registry
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Cases
    redirect(URL(f="person"))

# -----------------------------------------------------------------------------
def person():
    """
        REST controller to register evacuees
    """

    # @todo: this will not allow pre-existing person records
    #        to be added as EVR cases - need a filter+action
    #        solution instead
    s3.filter = s3base.S3FieldSelector("case.id") != None

    # Custom Method for Contacts
    s3db.set_method("pr", "person",
                    method="contacts",
                    action=s3db.pr_contacts)


    def prep(r):
        resource = r.resource
        
        if r.interactive and not r.component:


            # Custom Form for Persons
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            crud_form = S3SQLCustomForm("first_name",
                                        "local_name",
                                        "last_name",
                                        "date_of_birth",
                                        "case.fiscal_code",
                                        # @todo: split this into 3 different
                                        #        inline-fields (really? why?)
                                        S3SQLInlineComponent(
                                            "identity",
                                            label = T("Identity Documents"),
                                            fields = ["type",
                                                      "value",
                                                      # @todo: more fields available
                                                      # e.g. valid_until, country code
                                                      # for foreign documents etc.,
                                                      # see pr_identity
                                                      ],
                                        ),
                                        "gender",
                                        "person_details.marital_status",
                                        "person_details.nationality",
                                        "person_details.religion",
                                        "person_details.occupation",
                                        #"person_details.company",
                                        "comments",
                                        )
            resource.configure(crud_form=crud_form)
            
        # Extend pr_person_onaccept to auto-register an
        # evr_case record upon create ()
        key = "create_onaccept"
        onaccept = resource.get_config(key)
        if not onaccept:
            key = "onaccept"
            onaccept = resource.get_config(key)
        if not onaccept:
            resource.configure(create_onaccept=evr_person_onaccept)
        elif isinstance(onaccept, list):
            onaccept.append(evr_person_onaccept)
        else:
            resource.configure(**{key: [onaccept, evr_person_onaccept]})
            
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person",
                              rheader = s3db.evr_rheader)
    
# -----------------------------------------------------------------------------
def group():
    """
        REST controller to register families
    """

    # @todo: filter groups to families where at least one member
    #        is an EVR case (this can be hard-coded here)

    # not needed in controllers:
    #T = current.T
    #s3db = current.s3db
    #s3 = current.response.s3

    #tablename = "pr_group"
    #table = s3db[tablename]

    #_group_type = table.group_type

    ## Set Defaults
    #_group_type.default = 1  # 'Family'

    ## Only show Families
    ## Do not show system groups
    #s3.filter = (table.system == False) & \
                #(_group_type == 1 or
                 #_group_type == 4 or
                 #_group_type == 6 or
                 #_group_type == 7 or
                 #_group_type == 8 or
                 #_group_type == 9 or
                 #_group_type == 10 or
                 #_group_type == 11
                 #)

    query = (s3base.S3FieldSelector("system") == False) & \
            (s3base.S3FieldSelector("group_type").belongs((1,4,6,7,8,9,10,11)))
    s3.filter = query

    s3db.configure(tablename,
                   # Redirect to member list when a new group has been created
                   create_next = URL(f="group",
                                     args=["[id]", "group_membership"]),
                   list_fields = ["id",
                                  "name",
                                  "description",
                                  "comments",
                                  ],
                   )
    
    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "group_membership"])

        return output
    s3.postp = postp
    
    output = s3_rest_controller("pr", "group",
                                hide_filter = False,
                                rheader = lambda r: \
                                s3db.pr_rheader(r, tabs=tabs)
                                )
    
    return output
    
# -----------------------------------------------------------------------------
def evr_person_onaccept(form):
    """
        Auto-create a evr_case record for persons registered through
        the evr/person controller, so that they appear in the person
        list.

        @param form: the CRUD form
    """

    try:
        person_id = form.vars.id
    except:
        return
        
    table = s3db.evr_case

    row = db(table.person_id == person_id).select(table.id,
                                                  limitby=(0, 1)).first()
    if not row:
        table.insert(person_id=person_id)
    return

# END =========================================================================
