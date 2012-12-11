# -*- coding: utf-8 -*-

""" Sahana Eden Common Alerting Protocol (CAP) Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3CAPModel",
           "cap_first_run",
           "cap_info_labels",
           "cap_alert_is_template",
           "cap_alert_rheader",
           "cap_template_rheader",
           "cap_info_rheader",
           ]

import time

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3CAPModel(S3Model):
    """
        CAP: Common Alerting Protocol
        - this module is a non-functional stub

        http://eden.sahanafoundation.org/wiki/BluePrint/Messaging#CAP
    """

    names = ["cap_alert",
             "cap_info",
             "cap_resource",
             "cap_area",
             ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # List of Incident Categories -- copied from irs module <--
        # @ToDo: Switch to using event_incident_type
        #
        # The keys are based on the Canadian ems.incident hierarchy, with a few extra general versions added to 'other'
        # The values are meant for end-users, so can be customised as-required
        # NB It is important that the meaning of these entries is not changed as otherwise this hurts our ability to do synchronisation
        # Entries can be hidden from user view in the controller.
        # Additional sets of 'translations' can be added to the tuples.
        cap_incident_type_opts = {
            "animalHealth.animalDieOff": T("Animal Die Off"),
            "animalHealth.animalFeed": T("Animal Feed"),
            "aviation.aircraftCrash": T("Aircraft Crash"),
            "aviation.aircraftHijacking": T("Aircraft Hijacking"),
            "aviation.airportClosure": T("Airport Closure"),
            "aviation.airspaceClosure": T("Airspace Closure"),
            "aviation.noticeToAirmen": T("Notice to Airmen"),
            "aviation.spaceDebris": T("Space Debris"),
            "civil.demonstrations": T("Demonstrations"),
            "civil.dignitaryVisit": T("Dignitary Visit"),
            "civil.displacedPopulations": T("Displaced Populations"),
            "civil.emergency": T("Civil Emergency"),
            "civil.looting": T("Looting"),
            "civil.publicEvent": T("Public Event"),
            "civil.riot": T("Riot"),
            "civil.volunteerRequest": T("Volunteer Request"),
            "crime": T("Crime"),
            "crime.bomb": T("Bomb"),
            "crime.bombExplosion": T("Bomb Explosion"),
            "crime.bombThreat": T("Bomb Threat"),
            "crime.dangerousPerson": T("Dangerous Person"),
            "crime.drugs": T("Drugs"),
            "crime.homeCrime": T("Home Crime"),
            "crime.illegalImmigrant": T("Illegal Immigrant"),
            "crime.industrialCrime": T("Industrial Crime"),
            "crime.poisoning": T("Poisoning"),
            "crime.retailCrime": T("Retail Crime"),
            "crime.shooting": T("Shooting"),
            "crime.stowaway": T("Stowaway"),
            "crime.terrorism": T("Terrorism"),
            "crime.vehicleCrime": T("Vehicle Crime"),
            "fire": T("Fire"),
            "fire.forestFire": T("Forest Fire"),
            "fire.hotSpot": T("Hot Spot"),
            "fire.industryFire": T("Industry Fire"),
            "fire.smoke": T("Smoke"),
            "fire.urbanFire": T("Urban Fire"),
            "fire.wildFire": T("Wild Fire"),
            "flood": T("Flood"),
            "flood.damOverflow": T("Dam Overflow"),
            "flood.flashFlood": T("Flash Flood"),
            "flood.highWater": T("High Water"),
            "flood.overlandFlowFlood": T("Overland Flow Flood"),
            "flood.tsunami": T("Tsunami"),
            "geophysical.avalanche": T("Avalanche"),
            "geophysical.earthquake": T("Earthquake"),
            "geophysical.lahar": T("Lahar"),
            "geophysical.landslide": T("Landslide"),
            "geophysical.magneticStorm": T("Magnetic Storm"),
            "geophysical.meteorite": T("Meteorite"),
            "geophysical.pyroclasticFlow": T("Pyroclastic Flow"),
            "geophysical.pyroclasticSurge": T("Pyroclastic Surge"),
            "geophysical.volcanicAshCloud": T("Volcanic Ash Cloud"),
            "geophysical.volcanicEvent": T("Volcanic Event"),
            "hazardousMaterial": T("Hazardous Material"),
            "hazardousMaterial.biologicalHazard": T("Biological Hazard"),
            "hazardousMaterial.chemicalHazard": T("Chemical Hazard"),
            "hazardousMaterial.explosiveHazard": T("Explosive Hazard"),
            "hazardousMaterial.fallingObjectHazard": T("Falling Object Hazard"),
            "hazardousMaterial.infectiousDisease": T("Infectious Disease (Hazardous Material)"),
            "hazardousMaterial.poisonousGas": T("Poisonous Gas"),
            "hazardousMaterial.radiologicalHazard": T("Radiological Hazard"),
            "health.infectiousDisease": T("Infectious Disease"),
            "health.infestation": T("Infestation"),
            "ice.iceberg": T("Iceberg"),
            "ice.icePressure": T("Ice Pressure"),
            "ice.rapidCloseLead": T("Rapid Close Lead"),
            "ice.specialIce": T("Special Ice"),
            "marine.marineSecurity": T("Marine Security"),
            "marine.nauticalAccident": T("Nautical Accident"),
            "marine.nauticalHijacking": T("Nautical Hijacking"),
            "marine.portClosure": T("Port Closure"),
            "marine.specialMarine": T("Special Marine"),
            "meteorological.blizzard": T("Blizzard"),
            "meteorological.blowingSnow": T("Blowing Snow"),
            "meteorological.drought": T("Drought"),
            "meteorological.dustStorm": T("Dust Storm"),
            "meteorological.fog": T("Fog"),
            "meteorological.freezingDrizzle": T("Freezing Drizzle"),
            "meteorological.freezingRain": T("Freezing Rain"),
            "meteorological.freezingSpray": T("Freezing Spray"),
            "meteorological.hail": T("Hail"),
            "meteorological.hurricane": T("Hurricane"),
            "meteorological.rainFall": T("Rain Fall"),
            "meteorological.snowFall": T("Snow Fall"),
            "meteorological.snowSquall": T("Snow Squall"),
            "meteorological.squall": T("Squall"),
            "meteorological.stormSurge": T("Storm Surge"),
            "meteorological.thunderstorm": T("Thunderstorm"),
            "meteorological.tornado": T("Tornado"),
            "meteorological.tropicalStorm": T("Tropical Storm"),
            "meteorological.waterspout": T("Waterspout"),
            "meteorological.winterStorm": T("Winter Storm"),
            "missingPerson": T("Missing Person"),
            "missingPerson.amberAlert": T("Child Abduction Emergency"),   # http://en.wikipedia.org/wiki/Amber_Alert
            "missingPerson.missingVulnerablePerson": T("Missing Vulnerable Person"),
            "missingPerson.silver": T("Missing Senior Citizen"),          # http://en.wikipedia.org/wiki/Silver_Alert
            "publicService.emergencySupportFacility": T("Emergency Support Facility"),
            "publicService.emergencySupportService": T("Emergency Support Service"),
            "publicService.schoolClosure": T("School Closure"),
            "publicService.schoolLockdown": T("School Lockdown"),
            "publicService.serviceOrFacility": T("Service or Facility"),
            "publicService.transit": T("Transit"),
            "railway.railwayAccident": T("Railway Accident"),
            "railway.railwayHijacking": T("Railway Hijacking"),
            "roadway.bridgeClosure": T("Bridge Closed"),
            "roadway.hazardousRoadConditions": T("Hazardous Road Conditions"),
            "roadway.roadwayAccident": T("Road Accident"),
            "roadway.roadwayClosure": T("Road Closed"),
            "roadway.roadwayDelay": T("Road Delay"),
            "roadway.roadwayHijacking": T("Road Hijacking"),
            "roadway.roadwayUsageCondition": T("Road Usage Condition"),
            "roadway.trafficReport": T("Traffic Report"),
            "temperature.arcticOutflow": T("Arctic Outflow"),
            "temperature.coldWave": T("Cold Wave"),
            "temperature.flashFreeze": T("Flash Freeze"),
            "temperature.frost": T("Frost"),
            "temperature.heatAndHumidity": T("Heat and Humidity"),
            "temperature.heatWave": T("Heat Wave"),
            "temperature.windChill": T("Wind Chill"),
            "wind.galeWind": T("Gale Wind"),
            "wind.hurricaneForceWind": T("Hurricane Force Wind"),
            "wind.stormForceWind": T("Storm Force Wind"),
            "wind.strongWind": T("Strong Wind"),
            "other.buildingCollapsed": T("Building Collapsed"),
            "other.peopleTrapped": T("People Trapped"),
            "other.powerFailure": T("Power Failure"),
        }

        # ---------------------------------------------------------------------
        # CAP alerts
        #

        # CAP alert Status Code (status)
        cap_alert_status_code_opts = OrderedDict([
            ("Actual", T("Actual - actionable by all targeted recipients")),
            ("Exercise", T("Exercise - only for designated participants (decribed in note)")),
            ("System", T("System - for internal functions")),
            ("Test", T("Test - testing, all recipients disregard")),
            ("Draft", T("Draft - not actionable in its current form")),
        ])
        # CAP alert message type (msgType)
        cap_alert_msgType_code_opts = OrderedDict([
            ("Alert", T("Alert: Initial information requiring attention by targeted recipients")),
            ("Update", T("Update: Update and supercede earlier message(s)")),
            ("Cancel", T("Cancel: Cancel earlier message(s)")),
            ("Ack", T("Ack: Acknowledge receipt and acceptance of the message(s)")),
            ("Error", T("Error: Indicate rejection of the message(s)")),
        ])
        # CAP alert scope
        cap_alert_scope_code_opts = OrderedDict([
            ("Public", T("Public - unrestricted audiences")),
            ("Restricted", T("Restricted - to users with a known operational requirement (described in restriction)")),
            ("Private", T("Private - only to specified addresses (mentioned as recipients)"))
        ])

        tablename = "cap_alert"
        table = define_table(tablename,
                             Field("is_template", "boolean",
                                   readable=False,
                                   writable=True),
                             Field("template_id", "reference cap_alert",
                                      requires = IS_NULL_OR(
                                          IS_ONE_OF(db, "cap_alert.id",
                                                    self.template_represent,
                                                    filterby="is_template",
                                                    filter_opts=(True,)
                                                    )),
                                      represent = self.template_represent,
                                      label = T("Template"),
                                      comment = T("Apply a template"),
                                      ondelete = "RESTRICT"),
                             Field("template_title",
                                   label = T("Template Title")),
                             Field("template_settings", "text",
                                   readable=False,
                                   default="{}"),
                             Field("identifier", unique=True,
                                   label = T("Identifier"),
                                   default = self.generate_identifier),
                             Field("sender",
                                   label = T("Sender"),
                                   default = self.generate_sender),
                             Field("sent", "datetime",
                                   writable=False,
                                   readable=True),
                             Field("status",
                                   label = T("Status"),
                                   requires=IS_IN_SET(cap_alert_status_code_opts)),
                             Field("msg_type",
                                   label = T("Message Type"),
                                   requires=IS_IN_SET(cap_alert_msgType_code_opts)),
                             Field("source",
                                   label = T("Source")),
                             Field("scope",
                                   label = T("Scope"),
                                   requires=IS_IN_SET(cap_alert_scope_code_opts)),
                             # Text decribing the restriction for scope=restricted
                             Field("restriction", "text",
                                   label = T("Restriction")),
                             Field("addresses", "list:string",
                                   label = T("Recipients"),
                                   #@ToDo: provide a better way to add multiple addresses, do not ask the user to delimit it themselves
                                   #       this should eventually use the CAP contacts
                                   #widget = S3CAPAddressesWidget,
                                   represent=self.list_string_represent),
                             Field("codes", "text",
                                   label = T("Codes"),
                                   widget = S3KeyValueWidget(),
                                   represent = S3KeyValueWidget.represent,
                                   default = settings.get_cap_codes()
                                   ),
                             Field("note", "text",
                                   label = T("Note")),
                             Field("reference", "list:reference cap_alert",
                                   label = T("Reference"),
                                   # @ToDo: This should not be manually entered, needs a widget
                                   #widget = S3ReferenceWidget(table, one_to_many=True, allow_create=False),
                                   represent=self.alert_reference_represent),
                             # @ToDo: Switch to using event_incident_type_id
                             Field("incidents",
                                   label = T("Incidents"),
                                   requires=IS_IN_SET(cap_incident_type_opts,
                                                      multiple=True),
                                   represent = self.list_string_represent),
                             *s3_meta_fields())

        cap_search = S3Search(
                 simple = (S3SearchSimpleWidget(
                     name="org_search_text_simple",
                     label = T("Search"),
                     comment = T("Search for an Alert by sender, incident, headline or event."),
                     field = ["sender",
                              "incidents",
                              "cap_info$headline",
                              "cap_info$event"
                              ]
                     )
                 ),
            )

        configure(tablename,
                  search_method=cap_search)

        if crud_strings["cap_template"]:
            crud_strings[tablename] = crud_strings["cap_template"]
        else:
            ADD_ALERT = T("Create Alert")
            crud_strings[tablename] = Storage(
                title_create = ADD_ALERT,
                title_display = T("Alert Details"),
                title_list = T("Alerts"),
                title_update = T("Edit Alert"), # If already-published, this should create a new "Update" alert instead of modifying the original
                title_upload = T("Import Alerts"),
                title_search = T("Search Alerts"),
                subtitle_create = T("Create new Alert"),
                label_list_button = T("List Alerts"),
                label_create_button = ADD_ALERT,
                label_delete_button = T("Delete Alert"),
                msg_record_created = T("Alert created"),
                msg_record_modified = T("Alert modified"),
                msg_record_deleted = T("Alert deleted"),
                msg_list_empty = T("No alerts to show"))

        alert_id = S3ReusableField("alert_id", table,
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cap_alert.id",
                                                          self.alert_represent)),
                                   represent = self.alert_represent,
                                   label = T("Alert"),
                                   comment = T("The alert message containing this information"),
                                   ondelete = "RESTRICT")

        # CAP Informations as component of Alerts
        add_component("cap_info", cap_alert="alert_id")

        # CAP Resources as component of Alerts
        #add_component("cap_resource", cap_alert="alert_id")

        # CAP Areas as component of Alerts
        #add_component("cap_area", cap_alert="alert_id")

        # ---------------------------------------------------------------------
        # CAP info segments
        #
        cap_info_category_opts = OrderedDict([
            ("Geo", T("Geophysical (inc. landslide)")),
            ("Met", T("Meteorological (inc. flood)")),
            ("Safety", T("General emergency and public safety")),
            ("Security", T("Law enforcement, military, homeland and local/private security")),
            ("Rescue", T("Rescue and recovery")),
            ("Fire", T("Fire suppression and rescue")),
            ("Health", T("Medical and public health")),
            ("Env", T("Pollution and other environmental")),
            ("Transport", T("Public and private transportation")),
            ("Infra", T("Utility, telecommunication, other non-transport infrastructure")),
            ("CBRNE", T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack")),
            ("Other", T("Other events")),
        ])

        cap_info_responseType_opts = OrderedDict([
            ("Shelter", T("Shelter - Take shelter in place or per instruction")),
            ("Evacuate", T("Evacuate - Relocate as instructed in the instruction")),
            ("Prepare", T("Prepare - Make preparations per the instruction")),
            ("Execute", T("Execute - Execute a pre-planned activity identified in instruction")),
            ("Avoid", T("Avoid - Avoid the subject event as per the instruction")),
            ("Monitor", T("Monitor - Attend to information sources as described in instruction")),
            ("Assess", T("Assess - Evaluate the information in this message.")),
            ("AllClear", T("AllClear - The subject event no longer poses a threat")),
            ("None", T("None - No action recommended")),
        ])

        cap_info_urgency_opts = OrderedDict([
            ("Immediate", T("Respone action should be taken immediately")),
            ("Expected", T("Response action should be taken soon (within next hour)")),
            ("Future", T("Responsive action should be taken in the near future")),
            ("Past", T("Responsive action is no longer required")),
            ("Unknown", T("Unknown")),
        ])

        cap_info_severity_opts = OrderedDict([
            ("Extreme", T("Extraordinary threat to life or property")),
            ("Severe", T("Significant threat to life or property")),
            ("Moderate", T("Possible threat to life or property")),
            ("Minor", T("Minimal to no known threat to life or property")),
            ("Unknown", T("Severity unknown")),
        ])

        cap_info_certainty_opts = OrderedDict([
            ("Observed", T("Observed: determined to have occurred or to be ongoing")),
            ("Likely", T("Likely (p > ~50%)")),
            ("Possible", T("Possible but not likely (p <= ~50%)")),
            ("Unlikely", T("Not expected to occur (p ~ 0)")),
            ("Unknown", T("Certainty unknown")),
        ])

        # CAP info priority
        priorities = settings.get_cap_priorities()
        try:
            cap_info_priority_opts = OrderedDict([(f[0], f[1]) for f in priorities]
                    + [("Undefined", T("Undefined"))])
        except IndexError:
            raise ValueError("CAP priorities setting is not structured properly")

        # @ToDo: i18n: Need label=T("")
        tablename = "cap_info"
        table = define_table(tablename,
                             alert_id(),
                             Field("is_template", "boolean",
                                   default=True,
                                   readable=False,
                                   writable=False),
                             Field("template_info_id", "reference cap_info",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cap_info.id",
                                                          self.template_represent,
                                                          filterby="is_template",
                                                          filter_opts=(True,)
                                                          )),
                                   ondelete = "RESTRICT",
                                   widget = S3HiddenWidget(),
                                   readable=False),
                             Field("template_settings", "text", readable=False),
                             Field("language",
                                   requires=IS_IN_SET(settings.get_cap_languages()),
                                   default="en"),
                             Field("category",
                                   represent=self.list_string_represent,
                                   requires=IS_IN_SET(cap_info_category_opts,
                                                      multiple=True),
                                   required=True),# 1 or more allowed
                             Field("event", required=True),
                             Field("response_type",
                                   #widget = S3MultiSelectWidget(),
                                   requires=IS_IN_SET(cap_info_responseType_opts,
                                                      multiple=True),
                                   represent=self.list_string_represent), # 0 or more allowed
                             Field("priority",
                                    requires=IS_IN_SET(cap_info_priority_opts)),
                             Field("urgency", required=True,
                                   requires=IS_IN_SET(cap_info_urgency_opts)),
                             Field("severity", required=True,
                                   requires=IS_IN_SET(cap_info_severity_opts)),
                             Field("certainty", required=True,
                                   requires=IS_IN_SET(cap_info_certainty_opts)),
                             Field("audience", "text"),
                             Field("event_code", "text",
                                   widget = S3KeyValueWidget(),
                                   represent = S3KeyValueWidget.represent,
                                   default = settings.get_cap_event_codes()
                                   ),
                             Field("effective", "datetime",
                                   # @ToDo: format/represent for l10n options
                                   widget = S3DateTimeWidget()),
                             Field("onset", "datetime",
                                   widget = S3DateTimeWidget()),
                             Field("expires", "datetime",
                                   widget = S3DateTimeWidget(past=0)),
                             Field("sender_name"),
                             Field("headline"),
                             Field("description", "text"),
                             Field("instruction", "text"),
                             Field("contact", "text"),
                             Field("web",
                                   requires=IS_NULL_OR(IS_URL())),
                             Field("parameter", "text",
                                   label = T("Parameters"),
                                   widget = S3KeyValueWidget(),
                                   represent = S3KeyValueWidget.represent,
                                   default = settings.get_cap_parameters()
                                   ),
                             *s3_meta_fields())

        info_labels = cap_info_labels()
        for field in info_labels:
            db.cap_info[field].label = info_labels[field]

        if crud_strings["cap_template_info"]:
            crud_strings[tablename] = crud_strings["cap_template_info"]
        else:
            ADD_INFO = T("Add alert information")
            crud_strings[tablename] = Storage(
                title_create = ADD_INFO,
                title_display = T("Alert information"),
                title_list = T("Information entries"),
                title_update = T("Update alert information"), # this will create a new "Update" alert?
                title_upload = T("Import alert information"),
                title_search = T("Search alert information"),
                subtitle_create = T("Create an information entry"),
                subtitle_list = T("Listing of alert information items"),
                label_list_button = T("List information entries"),
                label_create_button = ADD_INFO,
                label_delete_button = T("Delete Alert"),
                msg_record_created = T("Alert information created"),
                msg_record_modified = T("Alert information modified"),
                msg_record_deleted = T("Alert information deleted"),
                msg_list_empty = T("No alert information to show"))

        info_id = S3ReusableField("info_id", table,
                                  sortby="identifier",
                                  requires=IS_NULL_OR(
                                            IS_ONE_OF(db, "cap_info.id",
                                                      self.info_represent)),
                                  represent = self.info_represent,
                                  label = T("Alert Information"),
                                  comment = T("The alert information"),
                                  ondelete = "RESTRICT")

        configure(tablename,
                  onaccept=self.info_onaccept)

        add_component("cap_resource", cap_info="info_id")
        add_component("cap_area", cap_info="info_id")

        # ---------------------------------------------------------------------
        # CAP Resource segments
        #
        tablename = "cap_resource"
        table = define_table(tablename,
                             info_id(),
                             alert_id(writable=False),
                             Field("resource_desc", required=True),
                             Field("mime_type", required=True),
                             Field("size", "integer",
                                   writable = False),
                             Field("uri",
                                   writable = False), # needs a special validation
                             Field("file", "upload"),
                             Field("deref_uri", "text",
                                    writable=False, readable=False),
                             Field("digest",
                                   writable=False),
                             *s3_meta_fields())

        # @ToDo: CRUD Strings

        configure(tablename,
                  onaccept=update_alert_id(table))

        # ---------------------------------------------------------------------
        # CAP info area segments
        #
        tablename = "cap_area"
        table = define_table(tablename,
                             info_id(),
                             alert_id(writable=False),
                             Field("area_desc",
                                   label = T("Area description"),
                                   required=True),
                             self.gis_location_id(
                                widget = S3LocationSelectorWidget(polygon=True)
                             ),
                             Field("circle"),
                             Field("geocode", "text",
                                   widget = S3KeyValueWidget(),
                                   represent = S3KeyValueWidget.represent,
                                   default = settings.get_cap_geocodes),
                             Field("altitude", "integer"),
                             Field("ceiling", "integer"),
                             *s3_meta_fields())

        # @ToDo: CRUD Strings

        configure(tablename,
                  onaccept=update_alert_id(table))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def generate_identifier():
        """
            Generate an identifier for a new form
        """

        db = current.db
        table = db.cap_alert
        r = db().select(table.id,
                        limitby=(0, 1),
                        orderby=~table.id).first()

        _time = time.strftime("%Y%m%dT%H:%M:%S%z")
        if r:
            next_id = int(r.id) + 1
        else:
            next_id = 1

        # Format: prefix-time+-timezone+sequence-suffix
        settings = current.deployment_settings
        prefix = settings.get_cap_identifier_prefix() \
                    or current.manager.domain
        suffix = settings.get_cap_identifier_suffix()

        return "%s-%s-%d%s%s" % \
                    (prefix, _time, next_id, ["", "-"][bool(suffix)], suffix)

    # -------------------------------------------------------------------------
    @staticmethod
    def generate_sender():
        """
            Generate a sender for a new form
        """
        try:
            user_id = current.auth.user.id
        except AttributeError:
            return ""

        return "%s/%d" % (current.manager.domain, user_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def alert_represent(id, row=None):
        """
            Represent an alert concisely
        """

        if row:
            pass
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.cap_alert
            row = db(table.id == id).select(table.msg_type,
                                            table.sent,
                                            table.created_on,
                                            table.sender,
                                            limitby=(0, 1)).first()

        if row:
            sent = row.sent or row.created_on
            if row.msg_type:
                return "%s - %s - %s" % (row.msg_type, sent, row.sender)
        return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def template_represent(id, row=None):
        """
            Represent an alert template concisely
        """

        if row:
            id = row.id
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.cap_alert
            row = db(table.id == id).select(table.is_template,
                                            table.template_title,
                                            # left = table.on(table.id == table.parent_item_category_id), Doesn't work
                                            limitby=(0, 1)).first()

        try:
            # @ToDo: Should get headline from "info"?
            if row.is_template:
                return row.template_title
            else:
                return S3CAPModel.alert_represent(id)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def list_string_represent(string, fmt=lambda v: v):
        try:
            if isinstance(string, list):
                return ", ".join([fmt(i) for i in string])
            elif isinstance(string, basestring):
                return ", ".join([fmt(i) for i in string[1:-1].split("|")])
        except IndexError:
            return current.messages.UNKNOWN_OPT
        return ""

    # -------------------------------------------------------------------------
    @staticmethod
    def alert_reference_represent(v):
        """
            Represent an alert concisely
        """

        return S3CAPModel.list_string_represent(v, S3CAPModel.alert_represent)

    # -------------------------------------------------------------------------
    @staticmethod
    def info_represent(id, row=None):
        """
            Represent an alert information concisely
        """

        if row:
            pass
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.cap_info
            row = db(table.id == id).select(table.headline,
                                            table.alert_id,
                                            table.language,
                                            limitby=(0, 1)).first()

        # @ToDo: Should get headline from "info"?
        return "%s - %s" % (row.language, row.headline)

    # -------------------------------------------------------------------------
    @staticmethod
    def info_onaccept(form):
        """
            After DB I/O
        """

        if "vars" in form:
            vars = form.vars
        elif "id" in form:
            vars = form
        elif hasattr(form, "vars"):
            vars = form.vars
        else:
            vars = form

        info_id = vars.id
        if not info_id:
            return

        db = current.db
        atable = db.cap_alert
        itable = db.cap_info

        info = db(itable.id == info_id).select(itable.alert_id,
                                               limitby=(0, 1)).first()
        if info:
            alert_id = info.alert_id
            if alert_id and cap_alert_is_template(alert_id):
                info.update(is_template = True)

        return True

# =============================================================================
def cap_info_labels():
    """
        Labels for CAP info segments
    """

    T = current.T
    return dict(
                language=T("Language"),
                category=T("Category"),
                event=T("Event"),
                response_type=T("Response type"),
                urgency=T("Urgency"),
                severity=T("Severity"),
                certainty=T("Certainty"),
                audience=T("Audience"),
                event_code=T("Event code"),
                effective=T("Effective"),
                onset=T("Onset"),
                expires=T("Expires at"),
                sender_name=T("Sender's name"),
                headline=T("Headline"),
                description=T("Description"),
                instruction=T("Instruction"),
                web=T("URL"),
                contact=T("Contact information"),
                parameter=T("Parameters")
                )

# =============================================================================
def cap_alert_is_template(alert_id):
    """
        Tell whether an alert entry is a template
    """

    if not alert_id:
        return False

    table = current.s3db.cap_alert
    query = (table.id == alert_id)
    r = current.db(query).select(table.is_template,
                                 limitby=(0, 1)).first()

    return r and r.is_template

# =============================================================================
def cap_alert_rheader(r):
    """ Resource Header for Alerts """

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            table = current.s3db.cap_info
            query = (table.alert_id == item.id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if not (row and row.id):
                error = DIV(T("You need to create at least one alert information item in order to be able to broadcast this alert!"),
                            _class="error")
            else:
                error = ""

            tabs = [
                    (T("Alert Qualifiers"), None),
                    (T("Information"), "info"),
                    #(T("Edit Area"), "area"),
                    #(T("Resource Files"), "resource"),
                   ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                   A(S3CAPModel.alert_represent(item.id),
                                     _href=URL(c="cap", f="alert",
                                               args=[item.id, "update"]))
                                  )
                                ),
                          rheader_tabs,
                          error
                         )
            return rheader
    return None

# =============================================================================
def cap_template_rheader(r):
    """ Resource Header for Alert templates"""

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            table = current.s3db.cap_info
            query = (table.alert_id == item.id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            error = []
            if not (row and row.id):
                error.append(DIV(T("An alert needs to contain at least one info item."),
                                   _class="error"))

            tabs = [
                    (T("Template"), None),
                    (T("Information template"), "info"),
                    #(T("Edit Area"), "area"),
                    #(T("Resource Files"), "resource"),
                   ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(TABLE(TR( TH("%s: " % T("Template")),
                                    A(S3CAPModel.template_represent(item.id),
                                      _href=URL(c="cap", f="template", args=[item.id, "update"]))
                                  )
                               ),
                          rheader_tabs,
                          *error
                         )
            return rheader
    return None

# =============================================================================
def cap_info_rheader(r):
    """ Resource Header for Info segments """

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            tabs = [
                    (T("Information"), None),
                    (T("Resource Files"), "resource"),
                   ]

            if cap_alert_is_template(item.alert_id):
                rheader_tabs = s3_rheader_tabs(r, tabs)
                table = r.table
                rheader = DIV(TABLE(TR(TH("%s: " % T("Template")),
                                       A(S3CAPModel.template_represent(item.alert_id),
                                         _href=URL(c="cap", f="template",
                                                   args=[item.alert_id, "update"])),
                                      ),
                                    TR(TH("%s: " % T("Info template")),
                                       A(S3CAPModel.info_represent(item.id),
                                         _href=URL(c="cap", f="info",
                                                   args=[item.id, "update"])),
                                      )
                                   ),
                              rheader_tabs,
                              _class="cap_info_template_form"
                             )
                current.response.s3.js_global.append('''i18n.cap_locked="%s"''' % T("Locked"))
            else:
                tabs.insert(1, (T("Edit Area"), "area"))
                rheader_tabs = s3_rheader_tabs(r, tabs)
                table = r.table

                rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                       A(S3CAPModel.alert_represent(item.alert_id),
                                         _href=URL(c="cap", f="alert",
                                                   args=[item.alert_id, "update"])),
                                      ),
                                    TR(TH("%s: " % T("Information")),
                                       A(S3CAPModel.info_represent(item.id),
                                         _href=URL(c="cap", f="info",
                                                   args=[item.id, "update"])),
                                      )
                                   ),
                              rheader_tabs
                             )
            return rheader
    return None

# =============================================================================
def cap_first_run():
    """ Add the default template """

    s3db = current.s3db
    atable = s3db.cap_alert

    if not current.db(atable.id > 0).select(atable.id,
                                            limitby=(0, 1)):
        s3db.cap_alert.insert(template_title="Default", is_template=True)

    return

# =============================================================================
def update_alert_id(table):
    """ On-accept for area and resource records """

    def func(form):
        if "vars" in form:
            vars = form.vars
        elif "id" in form:
            vars = form
        elif hasattr(form, "vars"):
            vars = form.vars
        else:
            vars = form

        # Get the full record
        id = vars.id
        if not id:
            return

        db = current.db
        item = db(table.id == id).select(table.info_id,
                                         limitby=(0, 1)).first()
        info_id = item.info_id

        itable = db.cap_info
        info = db(itable.id == info_id).select(itable.alert_id,
                                               limitby=(0, 1)).first()
        alert_id = info.alert_id

        db(table.id == id).update(alert_id = alert_id)
        db.commit()

    return func

# END =========================================================================
