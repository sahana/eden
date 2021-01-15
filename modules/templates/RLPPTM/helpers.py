# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLPPTM template

    @license: MIT
"""

from gluon import current

from s3 import S3Method

# =============================================================================
class rlpptm_InviteUserOrg(S3Method):
    """ Custom Method Handler to invite User Organisations """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            output = self.invite(r, **attr)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def invite(self, r, **attr):

        T = current.T

        output = {"title": T("Invite Organisation"),
                  }

        # TODO Implement this

        current.response.view = self._view(r, "update.html")

        return output

# END =========================================================================
