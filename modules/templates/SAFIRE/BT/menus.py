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

        settings = current.deployment_settings
        if settings.get_event_label(): # == "Disaster"
            EVENTS = "Disasters"
        else:
            EVENTS = "Events"

        if settings.get_incident_label(): # == "Ticket"
            INCIDENTS = "Tickets"
        else:
            INCIDENTS = "Incidents"

        menu= [MM("Call Logs", c="event", f="incident_report"),
               MM(INCIDENTS, c="event", f="incident", m="summary"),
               MM("Scenarios", c="event", f="scenario"),
               MM("Map", c="gis", f="index"),
               MM("Current System", link=False)(
                MM(EVENTS, c="event", f="event"),
                MM("Disaster Assessments", c="dc", f="index"),
                MM("Human Resources", c="hrm", f="staff"),
                MM("Infrastructure", c="transport", f="index"),
                MM("Population", c="stats", f="demographic_data"),
                MM("Stores Management", c="inv", f="index"),
                ),
               MM("DRR", link=False)(
                MM("Projects", c="project", f="project", m="summary"),
                MM("Trainings", c="hrm", f="training_event", m="summary"),
                ),
               MM("Other", link=False)(
                MM("Cases", c="br", f="person", vars={"closed": 0}),
                MM("Disease", c="disease", f="disease"),
                MM("Shelters", c="cr", f="shelter"),
                ),
               ]

        return menu

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    @staticmethod
    def event():
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

    # -------------------------------------------------------------------------
    @staticmethod
    def dc():
        """ Assessments menu """

        return M()(M("Initial Disaster Assessment (IDA)", c="dc", f="target",
<<<<<<< HEAD
                     vars = {"template_id$name": "Initial Disaster Assessment (IDA)"})(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Preliminary Damage and Needs Assessment (PDNA)", c="dc", f="target",
                     vars = {"template_id$name": "Preliminary Damage and Needs Assessment (PDNA)"})(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Detailed Damage Assessment", c="dc", f="target",
                     vars = {"template_id$name": "Detailed Damage Assessment"})(
                       M("Create", m="create"),
=======
                     vars = {"~.template_id$name": "Initial Disaster Assessment (IDA)"})(
                       M("Create", m="create",
                         vars = {"~.template_id$name": "Initial Disaster Assessment (IDA)"}),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Preliminary Damage and Needs Assessment (PDNA)", c="dc", f="target",
                     vars = {"~.template_id$name": "Preliminary Damage and Needs Assessment (PDNA)"})(
                       M("Create", m="create",
                         vars = {"~.template_id$name": "Preliminary Damage and Needs Assessment (PDNA)"}),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Detailed Damage Assessment", c="dc", f="target",
                     vars = {"~.template_id$name": "Detailed Damage Assessment"})(
                       M("Create", m="create",
                         vars = {"~.template_id$name": "Detailed Damage Assessment"}),
>>>>>>> 5ab908603 (DC: Update XSL/CSV)
                       #M("Import", m="import", p="create"),
                       ),
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ Projects menu """

        return M()(M("Projects", c="project", f="project", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Trainings", c="hrm", f="training_event", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   )

    # -------------------------------------------------------------------------
    def hrm(self):
        """ Human Resources menu """

        if current.request.function == "training_event":
            return self.project()
        else:
            return super(S3OptionsMenu, self).hrm()

    # -------------------------------------------------------------------------
    @staticmethod
    def inv():
        """ Inventory menu """

        return M()(M("Inventory Report", c="inv", f="inv_item", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Receive Item", c="inv", f="recv", m="create"),
                   M("Transfer Item", c="inv", f="send", m="create"),
                   M("Assign Item", c="asset", f="asset"),
                   M("Return Item", c="asset", f="asset"),
                   M("Stores", c="inv", f="warehouse", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Suppliers", c="inv", f="supplier", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Item Catalog", c="supply", f="catalog_item")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   )

    # -------------------------------------------------------------------------
    def asset(self):
        """ Assets menu """

        return self.inv()

    # -------------------------------------------------------------------------
    @staticmethod
    def transport():
        """ Infrastructure menu """

        return M()(M("Water Sources", c="water", f="reservoir", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Bridges", c="transport", f="bridge", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Sanitation Facilities", c="org", f="facility", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Health Facilities", c="hms", f="hospital", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Education Facilities", c="edu", f="school", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   M("Cultural Sites", c="org", f="facility", m="summary")(
                       M("Create", m="create"),
                       #M("Import", m="import", p="create"),
                       ),
                   )

    # -------------------------------------------------------------------------
    def edu(self):
        """ Education menu """

        return self.transport()

    # -------------------------------------------------------------------------
    def hms(self):
        """ Hospitals menu """

        return self.transport()

    # -------------------------------------------------------------------------
    def org(self):
        """ Organisations menu """

        return self.transport()

    # -------------------------------------------------------------------------
    def water(self):
        """ Water menu """

        return self.transport()

# END =========================================================================
