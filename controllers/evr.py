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
        
        table = resource.table
        
        # Disallow "unknown" gender and defaults to "male"
        evr_gender_opts = dict((k, v) for k, v in s3db.pr_gender_opts.items()
                                      if k in (2, 3))
        gender = table.gender
        gender.requires = IS_IN_SET(evr_gender_opts, zero=None)
        gender.default = 3
        
        # Disable unneeded physical details
        pdtable = s3db.pr_physical_description
        pdtable.race.writable = pdtable.race.readable = False
        pdtable.complexion.writable = pdtable.complexion.readable = False
        pdtable.height.writable = pdtable.height.readable = False
        pdtable.hair_length.writable = pdtable.hair_length.readable = False
        pdtable.hair_baldness.writable = pdtable.hair_baldness.readable = False
        pdtable.facial_hair_type.writable = pdtable.facial_hair_type.readable = False
        pdtable.facial_hair_color.writable = pdtable.facial_hair_color.readable = False
        pdtable.facial_hair_length.writable = pdtable.facial_hair_length.readable = False
        pdtable.hair_style.writable = pdtable.hair_style.readable = False
        pdtable.facial_hair_comment.writable = pdtable.facial_hair_comment.readable = False
        pdtable.body_hair.writable = pdtable.body_hair.readable = False
        pdtable.skin_marks.writable = pdtable.skin_marks.readable = False
        pdtable.medical_conditions.writable = pdtable.medical_conditions.readable = False
        
        # This set is suitable for Italy
        evr_ethnicity_opts = {1: T("Italian"),
                              2: T("Chinese"),
                              3: T("Albanese"),
                              4: T("Philippine"),
                              5: T("Pakistani"),
                              6: T("English"),
                              7: T("African"),
                              8: T("Other"),
                              9: T("Unknown")
                              }
        pdtable.ethnicity_opts.writable = pdtable.ethnicity_opts.readable = True
        pdtable.ethnicity_opts.requires = IS_EMPTY_OR(IS_IN_SET(evr_ethnicity_opts))
        pdtable.ethnicity_opts.represent = lambda opt: \
                                               evr_ethnicity_opts.get(
                                                    opt,
                                                    current.messages.UNKNOWN_OPT)
        pdtable.ethnicity.label = T("Ethnicity comments")
        
        if r.interactive and not r.component:

            # Filter widgets
            from s3 import S3TextFilter
            filter_widgets = [
                S3TextFilter(["first_name",
                              "middle_name",
                              "last_name",
                              "local_name",
                              "identity.value",
                              "case.fiscal_code"
                              ],
                              label=T("Name and/or ID"),
                              comment=T("To search for a person, enter any of the "
                                        "first, middle or last names and/or an ID "
                                        "number of a person, separated by spaces. "
                                        "You may use % as wildcard."),
                              ),
            ]

            # List fields
            list_fields = ["id",
                           "first_name",
                           #"middle_name",
                           "last_name",
                           "gender",
                           "date_of_birth",
                           (T("Age"), "age"),
                           ]

            # Custom Form for Persons
            from s3 import S3SQLCustomForm, S3SQLInlineComponent
            crud_form = S3SQLCustomForm("first_name",
                                        "middle_name",
                                        "last_name",
                                        "date_of_birth",
                                        "case.birthplace",
                                        "case.fiscal_code",
                                        S3SQLInlineComponent(
                                            "identity",
                                            label = T("Identity Documents"),
                                            fields = ["type",
                                                      "value",
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
            resource.configure(crud_form = crud_form,
                               list_fields = list_fields,
                               filter_widgets = filter_widgets)
            
        return True
    s3.prep = prep

    return s3_rest_controller("pr", "person",
                              rheader = s3db.evr_rheader)
    
# -----------------------------------------------------------------------------
def group():
    """
        REST controller to register families
    """

    # Special group types for EVR
    evr_group_types = {1 : T("Family"),
                       4 : T("other"),
                       6 : T("Society"),
                       7 : T("Company"),
                       8 : T("Orphanage"),
                       9 : T("Convent"),
                       10 : T("Hotel"),
                       11 : T("Hospital"),
                       }

    query = (s3base.S3FieldSelector("system") == False) & \
             (s3base.S3FieldSelector("group_type").belongs(evr_group_types.keys()))
    s3.filter = query

    s3db.configure("pr_group",
                   # Redirect to member list when a new group has been created
                   create_next = URL(f="group",
                                     args=["[id]", "group_membership"]),
                   list_fields = ["id",
                                  "name",
                                  "description",
                                  "group_type",
                                  "comments",
                                  ],
                   )
    
    # Custom method to get a list of available shelters
    s3db.set_method("pr", "group",
                    method="available_shelters",
                    action=s3db.evr_AvailableShelters
                    )
    
    # Pre-process
    def prep(r):
        if r.interactive:
            # Override the options for group_type,
            # only show evr_group_types
            r.resource.table.group_type.requires = IS_IN_SET(evr_group_types,
                                                             zero=None)
        return True
    s3.prep = prep
    
    # Post-process
    def postp(r, output):

        if r.interactive:
            if not r.component:
                update_url = URL(args=["[id]", "group_membership"])

        return output
    s3.postp = postp
    
    output = s3_rest_controller("pr", "group",
                                rheader = s3db.evr_rheader)
    
    return output
    
# END =========================================================================
