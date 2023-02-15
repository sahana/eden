# -*- coding: utf-8 -*-

from gluon import current
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        if not current.auth.is_logged_in():
            return None

        settings = current.deployment_settings
        if settings.get_event_label(): # == "Disaster"
            EVENTS = "Disasters"
        else:
            EVENTS = "Events"

        if settings.get_incident_label(): # == "Ticket"
            INCIDENTS = "Tickets"
        else:
            INCIDENTS = "Incidents"

        menu= [#MM("Call Logs", c="event", f="incident_report"),
               #MM(INCIDENTS, c="event", f="incident", m="summary"),
               #MM("Scenarios", c="event", f="scenario"),
               #MM("more", link=False)(
                #MM(EVENTS, c="event", f="event"),
                #MM("Staff", c="hrm", f="staff"),
                #MM("Map", c="gis", f="index"),
                #MM("Volunteers", c="vol", f="volunteer"),
                #MM("Assets", c="asset", f="asset"),
                MM("Organizations", c="org", f="organisation"),
                MM("Facilities", c="org", f="facility"),
                MM("Hospitals", c="med", f="hospital", m="summary"),
                MM("Needs", c="req", f="need", m="summary"),
                #MM("Shelters", c="cr", f="shelter"),
                #MM("Warehouses", c="inv", f="warehouse"),
                #MM("Item Catalog", c="supply", f="catalog_item"),
                #),
               ]

        return menu

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    def event(self):
        """ Events menu """

        settings = current.deployment_settings
        if settings.get_event_label(): # == "Disaster"
            EVENTS = "Disasters"
            EVENT_TYPES = "Disaster Types"
        else:
            EVENTS = "Events"
            EVENT_TYPES = "Event Types"

        if settings.get_incident_label(): # == "Ticket"
            INCIDENTS = "Tickets"
            INCIDENT_TYPES = "Ticket Types"
        else:
            INCIDENTS = "Incidents"
            INCIDENT_TYPES = "Incident Types"

        return M()(M("Scenarios", c="event", f="scenario")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                   ),
                   M(EVENTS, c="event", f="event")(
                       M("Create", m="create"),
                   ),
                   M(EVENT_TYPES, c="event", f="event_type")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                   ),
                   M(INCIDENTS, c="event", f="incident")(
                       M("Create", m="create"),
                   ),
                   M("Incident Reports", c="event", f="incident_report", m="summary")(
                       M("Create", m="create"),
                   ),
                   M(INCIDENT_TYPES, c="event", f="incident_type")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                   ),
                   M("Positions", c="event", f="job_title")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                   ),
                   M("Situation Reports", c="event", f="sitrep")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                   ),
                )

    # -------------------------------------------------------------------------
    def scenario(self):
        """ Scenario menu """

        return self.event()

# END =========================================================================
