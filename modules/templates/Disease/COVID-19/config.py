# -*- coding: utf-8 -*-

from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for COVID-19 Demo for the Disease template.

        Normally configured as:
        settings.base.template = ("locations.XX", "Disease", "Disease.COVID-19")
    """

    #T = current.T

    # PrePopulate data
    settings.base.prepopulate.append("Disease/COVID-19")

    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = False
    # Always notify the approver of a new (verified) user, even if the user is automatically approved
    settings.auth.always_notify_approver = False
    settings.security.policy = 1 # Simple Policy

    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("es", "Spanish"),
        ("fr", "French"),
    ])
    
# END =========================================================================
