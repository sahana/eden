# -*- coding: utf-8 -*-

"""
    Messaging module
"""

if deployment_settings.has_module("msg"):

    # =============================================================================
    # Tasks to be callable async
    # =============================================================================
    def process_outbox(contact_method, user_id=None):
        """
            Process Outbox
                - will normally be done Asynchronously if there is a worker alive

            @param contact_method: one from s3msg.MSG_CONTACT_OPTS
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task
        result = msg.process_outbox(contact_method)
        return result

    tasks["process_outbox"] = process_outbox

# END =========================================================================
