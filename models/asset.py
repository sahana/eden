# -*- coding: utf-8 -*-

"""
    Asset

    Asset Management Functionality

    http://eden.sahanafoundation.org/wiki/BluePrint/Assets
"""

# -----------------------------------------------------------------------------
# Defined in the Model for use from Multiple Controllers for unified menus
#
def asset_controller():
    """ RESTful CRUD controller """

    # Pre-process
    def prep(r):
        if r.interactive:
            address_hide(r.table)
        if r.component_name == "log":
            s3db.asset_log_prep(r)
            #if r.method == "update":
                # We don't want to exclude fields in update forms
                #pass
            #elif r.method != "read":
                # Don't want to see in Create forms
                # inc list_create (list_fields over-rides)
                #table = r.component.table
                #table.returned.readable = table.returned.writable = False
                #table.returned_status.readable = table.returned_status.writable = False
                # Process Base Site
                #s3mgr.configure(table._tablename,
                #                onaccept=asset_transfer_onaccept)
        #else:
            # @ToDo: Add Virtual Fields to the List view for 'Currently assigned to' & 'Current Location'

        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.method != "import":
            s3_action_buttons(r, deletable=False)
            #if not r.component:
                #response.s3.actions.append({"url" : URL(c="asset", f="asset",
                #                                            args = ["[id]", "log", "create"],
                #                                            vars = {"status" : eden.asset.asset_log_status["ASSIGN"],
                #                                                    "type" : "person"}),
                #                            "_class" : "action-btn",
                #                            "label" : str(T("Assign"))})
        return output
    response.s3.postp = postp

    output = s3_rest_controller("asset", "asset",
                                rheader=eden.asset.asset_rheader,
                                interactive_report=True)
    return output

# END =========================================================================
