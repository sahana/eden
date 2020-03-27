# -*- coding: utf-8 -*-

from collections import OrderedDict

#from gluon import current, URL
#from gluon.storage import Storage

def config(settings):
    """
        Settings for Ebola Demo for the Disease template.

        Normally configured as:
        settings.base.template = ("locations.GN", "locations.LR", "locations.ML", "locations.NG", "locations.SL", "locations.SN", "Disease", "Disease.Ebola")

        http://eden.sahanafoundation.org/wiki/Deployments/Ebola
    """

    #T = current.T

    # PrePopulate data
    settings.base.prepopulate.append("Disease/Ebola")

    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = False
    # Always notify the approver of a new (verified) user, even if the user is automatically approved
    settings.auth.always_notify_approver = False
    settings.security.policy = 1 # Simple Policy

    settings.L10n.languages = OrderedDict([
        ("en", "English"),
        ("fr", "French"),
    ])

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("GN", "LR", "ML", "NG", "SL", "SN")

    # Uncomment to show a default cancel button in standalone create/update forms
    settings.ui.default_cancel_button = True

    # Uncomment to open Location represent links in a Popup Window
    settings.gis.popup_location_link = True
    
# END =========================================================================
