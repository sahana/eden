# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL
from gluon.storage import Storage

def config(settings):
    """
        SHARE settings for Sri Lanka

        @ToDo: Setting for single set of Sectors / Sector Leads Nationally
    """

    T = current.T

    # PrePopulate data
    settings.base.prepopulate += ("SHARE/LK",)
    settings.base.prepopulate_demo += ("SHARE/Demo",)

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
        ("si", "Sinhala"),
        ("ta", "Tamil"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"

    # Finance settings
    settings.fin.currencies = {
        #"EUR" : "Euros",
        #"GBP" : "Great British Pounds",
        "LKR" : "Sri Lanka Rupees",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "USD"

    # -------------------------------------------------------------------------
    def customise_event_event_resource(r, tablename):

        s3db = current.s3db

        s3db.event_event.name.label = T("Disaster Title")

        # Custom Components
        s3db.add_components(tablename,
                            event_event_name = (# Sinhala
                                                {"name": "name_si",
                                                 "joinby": "event_id",
                                                 "filterby": {"language": "si",
                                                              },
                                                 "multiple": False,
                                                 },
                                                # Tamil
                                                {"name": "name_ta",
                                                 "joinby": "event_id",
                                                 "filterby": {"language": "ta",
                                                              },
                                                 "multiple": False,
                                                 },
                                                ),
                            need_need = {"link": "need_event",
                                         "joinby": "event_id",
                                         "key": "need_id",
                                         "actuate": "hide",
                                         "autodelete": False,
                                         },
                            )

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("name",
                                    S3SQLInlineComponent("name_si",
                                                         label = T("Title in Sinhala"),
                                                         multiple = False,
                                                         fields = [("", "name_l10n")],
                                                         ),
                                    S3SQLInlineComponent("name_ta",
                                                         label = T("Title in Tamil"),
                                                         multiple = False,
                                                         fields = [("", "name_l10n")],
                                                         ),
                                    "event_type_id",
                                    "start_date",
                                    "closed",
                                    "end_date",
                                    S3SQLInlineComponent("event_location",
                                                         label = T("Locations"),
                                                         multiple = False,
                                                         fields = [("", "location_id")],
                                                         ),
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_event_event_resource = customise_event_event_resource

# END =========================================================================
