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
    query = s3base.S3FieldSelector("evr_case.id") != None

    def prep(r):
        resource = r.resource
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

    return s3_rest_controller("pr", "person",
                              rheader = s3db.evr_rheader)
    
# -----------------------------------------------------------------------------
def group():
    """
        REST controller to register families
    """

    # @todo: filter groups to families where at least one member
    #        is an EVR case (this can be hard-coded here)
    # @todo: set group type default to family and hide field in form

    return s3_rest_controller("pr", "group")
    
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
