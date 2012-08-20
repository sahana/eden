# -*- coding: utf-8 -*-

""" Sahana Eden Messaging Model

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
           "cap_info_labels",
           "cap_alert_is_template",
           "cap_alert_rheader",
           "cap_alert_controller",
           "cap_first_run",
           "cap_template_rheader",
           "cap_template_controller",
           "cap_info_rheader",
           "cap_info_controller"
           ]

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

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

    names = ["msg_report",
             "cap_info_resource",
             "cap_info_area",
             "cap_info",
             "cap_alert"
             ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        location_id = self.gis_location_id
        message_id = self.msg_message_id

        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # @ToDo: msg_ tables cannot exist in modules/eden/cap.py
        tablename = "msg_report"
        table = define_table(tablename,
                             message_id(),
                             location_id(),
                             Field("image", "upload", autodelete=True),
                             Field("url",
                                   requires=IS_NULL_OR(IS_URL())),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # List of Incident Categories -- copied from irs module <--
        # FIXME: Move to a pre-populated Table irs_incident_type
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

        # @ToDo: i18n: Need label=T("")
        tablename = "cap_alert"
        table = define_table(tablename,
                             Field("is_template", "boolean",
                                   readable=False,
                                   writable=True),
                             Field("template_id", "reference %s" % tablename,
                                      requires = IS_NULL_OR(
                                          IS_ONE_OF(db, "cap_alert.id",
                                                    filterby="is_template",
                                                    filter_opts=(True,),
                                                    label = self.template_represent)),
                                      represent = self.template_represent,
                                      label = T("Template"),
                                      comment = T("Apply a template"),
                                      ondelete = "RESTRICT"),
                             Field("template_title"),
                             Field("template_settings", "text", readable=False, default="{}"),
                             Field("identifier", unique=True,
                                   default = self.generate_identifier),
                             Field("sender",
                                   default = self.generate_sender),
                             Field("sent", "datetime",
                                   writable=False,
                                   readable=True),
                             Field("status",
                                   requires=IS_IN_SET(cap_alert_status_code_opts)),
                             Field("msg_type",
                                   label = T("Message Type"),
                                   requires=IS_IN_SET(cap_alert_msgType_code_opts)),
                             Field("source"),
                             Field("scope",
                                   requires=IS_IN_SET(cap_alert_scope_code_opts)),
                             Field("restriction", "text"), # text decribing the restriction for scope=restricted
                             Field("addresses", "list:string",
                                   label = T("Recipients"),
                                   #@ToDo: provide a better way to add multiple addresses, do not ask the user to delimit it themselves
                                   #       this should eventually use the CAP contacts
                                   #widget = S3CAPAddressesWidget,
                                   represent=self.list_string_represent),
                             Field("codes", "text",
                                   widget = S3KeyValueWidget(),
                                   represent = S3KeyValueWidget.represent,
                                   default = settings.get_cap_codes()
                                   ),
                             Field("note", "text"),
                             Field("reference", "list:reference cap_alert",
                                   # @ToDo: This should not be manually entered, needs a widget
                                   #widget = S3ReferenceWidget(table, one_to_many=True, allow_create=False),
                                   represent=self.alert_reference_represent),
                             Field("incidents",
                                   requires=IS_IN_SET(cap_incident_type_opts,
                                                      multiple=True),
                                   represent = self.list_string_represent),
                             *s3_meta_fields())

        # -----------------------------------------------------------------------------
        cap_search = S3CAPSearch(
                 simple = (S3SearchSimpleWidget(
                     name="org_search_text_simple",
                     label = T("Search"),
                     comment = T("Search for an Organization by name or acronym."),
                     field = [ "sender",
                               "incidents",
                               "cap_info$headline",
                               "cap_info$event"
                             ]
                     )
                 ),
            )

        utablename = current.auth.settings.table_user_name
        self.configure(tablename,
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
                                              label = self.alert_represent)),
                                   represent = self.alert_represent,
                                   label = T("Alert"),
                                   comment = T("The alert message containing this information"),
                                   ondelete = "RESTRICT")

        table.identifier.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A unique identifier of the alert message"),
                  T("A number or string uniquely identifying this message, assigned by the sender. Must notnclude spaces, commas or restricted characters (< and &).")))

        table.sender.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the sender of the alert message"),
                  T("This is guaranteed by assigner to be unique globally; e.g., may be based on an Internet domain name. Must not include spaces, commas or restricted characters (< and &).")))

        table.status.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the appropriate handling of the alert message"),
                  T("See options.")))

        table.msg_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The nature of the alert message"),
                  T("See options.")))

        table.source.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text identifying the source of the alert message"),
                  T("The particular source of this alert; e.g., an operator or a specific device.")))

        table.scope.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the intended distribution of the alert message"),
                  T("Who is this alert for?")))

        table.restriction.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text describing the rule for limiting distribution of the restricted alert message"),
                  T("Used when scope is 'Restricted'.")))

        table.addresses.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The group listing of intended recipients of the alert message"),
                  T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address.")))

        table.codes.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Codes for special handling of the message"),
                  T("Any user-defined flags or special codes used to flag the alert message for special handling.")))

        table.note.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text describing the purpose or significance of the alert message"),
                  T("The message note is primarily intended for use with status 'Exercise' and message type 'Error'")))

        table.reference.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The group listing identifying earlier message(s) referenced by the alert message"),
                  T("The extended message identifier(s) (in the form sender,identifier,sent) of an earlier CAP message or messages referenced by this one.")))

        table.incidents.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A list of incident(s) referenced by the alert message"),
                  T("Used to collate multiple messages referring to different aspects of the same incident. If multie incident identifiers are referenced, they SHALL be separated by whitespace.  Incident names including whitespace SHALL be surrounded by double-quotes.")))

        # ---------------------------------------------------------------------
        # CAP info segments
        #

        # CAP info Event Category (category)
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
        # CAP info Response Type (responseType)
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
        # CAP info urgency
        cap_info_urgency_opts = OrderedDict([
            ("Immediate", T("Respone action should be taken immediately")),
            ("Expected", T("Response action should be taken soon (within next hour)")),
            ("Future", T("Responsive action should be taken in the near future")),
            ("Past", T("Responsive action is no longer required")),
            ("Unknown", T("Unknown")),
        ])
        # CAP info severity
        cap_info_severity_opts = OrderedDict([
            ("Extreme", T("Extraordinary threat to life or property")),
            ("Severe", T("Significant threat to life or property")),
            ("Moderate", T("Possible threat to life or property")),
            ("Minor", T("Minimal to no known threat to life or property")),
            ("Unknown", T("Severity unknown")),
        ])
        # CAP info certainty
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
            raise ValueError("cap priorities setting is not structured properly")

        # @ToDo: i18n: Need label=T("")
        tablename = "cap_info"
        table = define_table(tablename,
                             alert_id(),
                             Field("is_template", "boolean",
                                   default=True,
                                   readable=False,
                                   writable=False),
                             Field("template_info_id", "reference %s" % tablename,
                                      requires = IS_NULL_OR(
                                          IS_ONE_OF(db, "%s.id" % tablename,
                                                    filterby="is_template",
                                                    filter_opts=(True,),
                                                    label = self.template_represent)),
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

        # CAP Informations as component of Alerts
        add_component("cap_info", cap_alert="alert_id")

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
                                              label = self.info_represent)),
                                  represent = self.info_represent,
                                  label = T("Alert Information"),
                                  comment = T("The alert information"),
                                  ondelete = "RESTRICT")

        self.configure(tablename, onaccept=info_onaccept)

        # @ToDo: Move these to the controller in a prep if r.interactive
        table.language.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the language of the information"),
                  T("Code Values: Natural language identifier per [RFC 3066]. If not present, an implicit default value of 'en-US' will be assumed. Edit settings.cap.languages in 000_config.py to add more languages. See <a href=\"%s\">here</a> for a full list.") % "http://www.i18nguy.com/unicode/language-identifiers.html"))

        table.category.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the category of the subject event of the alert message"),
                  T("You may select multiple categories by holding down control and then selecting the items.")))

        table.event.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text denoting the type of the subject event of the alert message"),
                  T("")))

        table.response_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the type of action recommended for the target audience"),
                  T("Multiple response types can be selected by holding down control and then selecting the items")))

        table.urgency.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the urgency of the subject event of the alert message"),
                  T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                    "'Immediate' - Responsive action should be taken immediately" +
                    "'Expected' - Responsive action should be taken soon (within next hour)" +
                    "'Future' - Responsive action should be taken in the near future" +
                    "'Past' - Responsive action is no longer required" +
                    "'Unknown' - Urgency not known")))

        table.severity.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the severity of the subject event of the alert message"),
                  T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                  "'Extreme' - Extraordinary threat to life or property" +
                  "'Severe' - Significant threat to life or property" +
                  "'Moderate' - Possible threat to life or property" +
                  "'Minor' - Minimal to no known threat to life or property" +
                  "'Unknown' - Severity unknown")))

        table.certainty.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the certainty of the subject event of the alert message"),
                  T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                  "'Observed' - Determined to have occurred or to be ongoing" +
                  "'Likely' - Likely (p > ~50%)" +
                  "'Possible' - Possible but not likely (p <= ~50%)" +
                  "'Unlikely' - Not expected to occur (p ~ 0)" +
                  "'Unknown' - Certainty unknown")))

        table.audience.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The intended audience of the alert message"),
                  T("")))

        table.event_code.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A system-specific code identifying the event type of the alert message"),
                  T("Any system-specific code for events, in the form of key-value pairs. (e.g., SAME, FIPS, ZIP).")))

        table.effective.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The effective time of the information of the alert message"),
                  T("If not specified, the effective time shall be assumed to be the same the time the alert was sent.")))

        table.onset.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The expected time of the beginning of the subject event of the alert message"),
                  T("")))

        table.expires.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The expiry time of the information of the alert message"),
                  T("If this item is not provided, each recipient is free to enforce its own policy as to when the message is no longer in effect.")))

        table.sender_name.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text naming the originator of the alert message"),
                  T("The human-readable name of the agency or authority issuing this alert.")))

        table.headline.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text headline of the alert message"),
                  T("A brief human-readable headline.  Note that some displays (for example, short messaging service devices) may only present this headline; it should be made as direct and actionable as possible while remaining short.  160 characters may be a useful target limit for headline length.")))

        table.description.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The subject event of the alert message"),
                  T("An extended human readable description of the hazard or event that occasioned this message.")))

        table.instruction.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The recommended action to be taken by recipients of the alert message"),
                  T("An extended human readable instruction to targeted recipients.  If different instructions are intended for different recipients, they should be represented by use of multiple information blocks. You can use a different information block also to specify this information in a different language.")))

        table.web.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A URL associating additional information with the alert message"),
                  T("A full, absolute URI for an HTML page or other text resource with additional or reference information regarding this alert.")))

        table.contact.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The contact for follow-up and confirmation of the alert message"),
                  T("")))

        table.parameter.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A system-specific additional parameter associated with the alert message"),
                  T("Any system-specific datum, in the form of key-value pairs.")))

        #table.resource.comment = DIV(
        #      _class="tooltip",
        #      _title="%s|%s" % (
        #          T("Additional files supplimenting the alert message."),
        #          T("")))
        #table.resource.widget = S3ReferenceWidget(current.db.cap_info_resource,
        #                                          one_to_many=True,
        #                                          use_iframe=True)

        #table.area.comment = DIV(
        #      _class="tooltip",
        #      _title="%s|%s" % (
        #          T("The affected area of the alert"),
        #          T("")))
        #table.area.widget = S3ReferenceWidget(current.db.cap_info_area, one_to_many=True)

        # ---------------------------------------------------------------------
        # CAP info resource segments
        #

        tablename = "cap_info_resource"
        table = define_table(tablename,
                             info_id(),
                             alert_id(),
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

        # Resource as component of <alert> and <info>
        add_component(tablename, cap_alert="alert_id")
        add_component(tablename, cap_info="info_id")

        self.configure(tablename,
                       onaccept=update_alert_id(table)
                      )

        table.alert_id.writable = False

        # @ToDo: Move these to the controller in a prep if r.interactive
        table.resource_desc.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The type and content of the resource file"),
                  T("The human-readable text describing the type and content, such as 'map' or 'photo', of the resource file.")))

        table.mime_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the MIME content type and sub-type describing the resource file"),
                  T("MIME content type and sub-type as described in [RFC 2046]. (As of this document, the current IANA registered MIME types are listed at http://www.iana.org/assignments/media-types/)")))

        table.size.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The integer indicating the size of the resource file"),
                  T("Approximate size of the resource file in bytes.")))

        # fixme: This should be handled under the hood
        table.uri.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the hyperlink for the resource file"),
                  T("A full absolute URI, typically a Uniform Resource Locator that can be used to retrieve the resource over the Internet.")))


        table.digest.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The code representing the digital digest ('hash') computed from the resource file"),
                  T("Calculated using the Secure Hash Algorithm (SHA-1).")))

        # ---------------------------------------------------------------------
        # CAP info area segments
        #
        # @ToDo: Use gis_location here and convert wkt to WGS84

        tablename = "cap_info_area"
        table = self.define_table(tablename,
                                  info_id(),
                                  alert_id(),
                                  Field("area_desc",
                                        label = T("Area description"),
                                        required=True),
                                  location_id(),
                                  Field("circle"),
                                  Field("geocode", "text",
                                        widget = S3KeyValueWidget(),
                                        represent = S3KeyValueWidget.represent,
                                        default = settings.get_cap_geocodes),
                                  Field("altitude", "integer"),
                                  Field("ceiling", "integer"),
                                  *s3_meta_fields())

        # @ToDo: CRUD Strings

        # Area as component of the Alert and Information
        add_component("cap_info_area", cap_alert="alert_id")
        add_component("cap_info_area", cap_info="info_id")

        self.configure(tablename,
                       onaccept=update_alert_id(table)
                      )

        table.alert_id.writable = False

        # @ToDo: Move these to the controller in a prep if r.interactive
        table.area_desc.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The affected area of the alert message"),
                  T("A text description of the affected area.")))

        #table.polygon.comment = DIV(
        #      _class="tooltip",
        #      _title="%s|%s" % (
        #          T("Points defining a polygon that delineates the affected area"),
        #          T("")))
        #table.polygon.widget = S3LocationPolygonWidget

        table.location_id.widget = S3LocationSelectorWidget(polygon=True)

        table.circle.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A point and radius delineating the affected area"),
                  T("The circular area is represented by a central point given as a coordinate pair followed by a radius value in kilometers.")))

        table.geocode.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The geographic code delineating the affected area"),
                  T("Any geographically-based code to describe a message target area, in the form. The key is a user-assigned string designating the domain of the code, and the content of value is a string (which may represent a number) denoting the value itself (e.g., name='ZIP' and value='54321'). This should be used in concert with an equivalent description in the more universally understood polygon and circle forms whenever possible.")))

        table.altitude.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The specific or minimum altitude of the affected area"),
                  T("If used with the ceiling element this value is the lower limit of a range. Otherwise, this value specifies a specific altitude. The altitude measure is in feet above mean sea level.")))

        table.ceiling.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The maximum altitude of the affected area"),
                  T("must not be used except in combination with the 'altitude' element. The ceiling measure is in feet above mean sea level.")))

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
    def alert_represent(id):
        """
            Represent an alert concisely
        """

        if not id:
            return current.messages.NONE
        table = current.s3db.cap_alert
        query = (table.id == id)
        r = current.db(query).select(table.msg_type,
                                     table.sent,
                                     table.created_on,
                                     table.sender,
                                     limitby=(0, 1)).first()

        #XXX: Should get headline from "info"?
        if r and r.msg_type:
            sent = r.sent or r.created_on
            return "%s - %s - %s" % (r.msg_type, sent, r.sender)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def template_represent(id):
        """
            Represent an alert template concisely
        """

        if not id:
            return current.messages.NONE

        table = current.s3db.cap_alert
        query = (table.id == id)
        r = current.db(query).select(table.is_template,
                                     table.template_title,
                                     # left = table.on(table.id == table.parent_item_category_id), Doesn't work
                                     limitby=(0, 1)).first()

        #XXX: Should get headline from "info"?
        if r and r.is_template:
            return r.template_title
        else:
            return S3CAPModel.alert_represent(id)

    # -------------------------------------------------------------------------
    @staticmethod
    def list_string_represent(string, fmt=lambda v: v):
        try:
            if isinstance(string, list):
                return ", ".join([fmt(i) for i in string])
            elif isinstance(string, str):
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
    def info_represent(id):
        """
            Represent an alert information concisely
        """

        if not id:
            return current.messages.NONE

        db = current.db
        table = db.cap_info
        r = db(table.id == id).select(table.headline,
                                      table.alert_id,
                                      table.language,
                                      limitby=(0, 1)).first()

        #XXX: Should get headline from "info"?
        return "%s - %s" % (r.language, r.headline)

# =============================================================================
def cap_info_labels():
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
            error = []
            if not (row and row.id):
                error.append(DIV(T("You need to create atleast one alert " +
                                   "information item in order to be able " +
                                   "to broadcast this alert!"), _class="error"))

            tabs = [
                    (T("Alert Qualifiers"), None),
                    (T("Information"), "info"),
                    #(T("Edit Area"), "info_area"),
                    #(T("Resource Files"), "info_resource"),
                   ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(TABLE(TR( TH("%s: " % T("Alert")),
                                    A(S3CAPModel.alert_represent(item.id),
                                      _href=URL(c="cap", f="alert", args=[item.id, "update"]))
                                  )
                               ),
                          rheader_tabs,
                          *error
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
                    #(T("Edit Area"), "info_area"),
                    #(T("Resource Files"), "info_resource"),
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
                    (T("Resource Files"), "info_resource"),
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
                current.response.s3.js_global \
                    .append("S3.i18n.cap_locked = '%s';" % T("Locked"))
            else:
                tabs.insert(1, (T("Edit Area"), "info_area"))
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
def add_submit_button(form, name, value):
    """
        Append a submit button to a form
    """

    form[0][-1][0].insert(1, TAG[""](" ",
                INPUT(_type="submit", _name=name,
                      _value=value)))

# =============================================================================
def alert_form_mods(form):
    """
        Alert form mods
    """
    #TODO:
    # rename save button as "Save and edit information"
    #
    #add_submit_button(form, "add_info", T("Save and add information..."))
    T = current.T

    fields = cap_info_labels()
    jsobj = []
    for f in fields:
        jsobj.append("'%s': '%s'" % (f, fields[f].replace("'", "\\'")))

    current.response.s3.js_global.append("S3.i18n.cap_info_labels = {%s};" % ", ".join(jsobj))

    form[0][-1][0][0].update(_value=T("Save and edit information"),
                             _name="edit_info")


# =============================================================================
def cap_alert_controller():
    """ RESTful CRUD controller """

    output = current.rest_controller("cap", "alert",
                                     rheader=current.s3db.cap_alert_rheader)

    if "form" in output:
        form = output["form"]

        if form and "table" in dir(form):
            tablename = form.table._tablename

            if tablename == 'cap_alert':
                alert_form_mods(form)
                form.update(_class="cap_alert_form")
            set_priority_js()
        else:
            return output

        #if tablename == 'cap_info':
        #    add_submit_button(form, "add_language", T("Save and add another language"))

    return output

# =============================================================================
def cap_template_controller():
    """ RESTful CRUD controller """

    T = current.T
    crud_strings = current.response.s3.crud_strings
    s3db = current.s3db

    # XXX: hack!
    tablename = "cap_template"
    ADD_ALERT_TPL = T("Create Template")
    crud_strings[tablename] = Storage(
        title_create = ADD_ALERT_TPL,
        title_display = T("Template"),
        title_list = T("Templates"),
        title_update = T("Edit Template"), # If already-published, this should create a new "Update" alert instead of modifying the original
        title_upload = T("Import Templates"),
        title_search = T("Search Templates"),
        subtitle_create = T("Create new Template"),
        label_list_button = T("List Templates"),
        label_create_button = ADD_ALERT_TPL,
        label_delete_button = T("Delete Template"),
        msg_record_created = T("Template created"),
        msg_record_modified = T("Template modified"),
        msg_record_deleted = T("Tempmate deleted"),
        msg_list_empty = T("No templates to show"))

    for f in ["identifier", "msg_type"]:
        s3db.cap_alert[f].writable = False
        s3db.cap_alert[f].readable = False
        s3db.cap_alert[f].requires = None

    for f in ["status", "scope"]:
        s3db.cap_alert[f].requires = None

    s3db.cap_alert.template_title.required = True

    for f in ["urgency", "certainty",
              "priority", "severity",
              "effective", "onset", "expires"]:
        s3db.cap_info[f].writable = False
        s3db.cap_info[f].readable = False
        s3db.cap_info[f].required = False

    for f in ["category", "event"]:
        s3db.cap_info[f].required = False

    output = current.rest_controller("cap", "alert",
                                     rheader=current.s3db.cap_template_rheader)

    if "form" in output:
        form = output["form"]

        current.response.s3.js_global.append("S3.i18n.cap_locked = '%s';" % T("Locked"))

        tablename = form.table._tablename

        if tablename == 'cap_alert':
            form.update(_class="cap_template_form")
        if tablename == 'cap_info':
            form.update(_class="cap_info_template_form")

    return output

# =============================================================================
def cap_info_controller():
    """ RESTful CRUD controller """

    s3db = current.s3db
    output = current.rest_controller("cap", "info",
                                     rheader=s3db.cap_info_rheader)


    if "form" in output:
        set_priority_js()
        add_submit_button(output["form"], "add_language",
                          current.T("Save and add another language..."))

    return output

def cap_first_run():
    """ Add the default template """

    db = current.db
    s3db = current.s3db
    atable = s3db.cap_alert

    s3db.configure("cap_alert")
    if not db(atable.id > 0).select(atable.id,
                                    limitby=(0, 1)):
        # @fixme: get this to work!
        s3db.cap_alert.insert(template_title="Default", is_template='T')

def set_priority_js():
    """ Output json for priority field """

    settings = current.deployment_settings
    js_global = current.response.s3.js_global

    p_settings = [f[0:1] + f[2:] for f in settings.get_cap_priorities()]

    priority_conf = "S3.cap_priorities = %s;" % json.dumps(p_settings)
    if not priority_conf in js_global:
        js_global.append(priority_conf)

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

        item = db(table.id == id).select(table.info_id, limitby=(0, 1)).first()
        info_id = item.info_id

        itable = db.cap_info
        info = db(itable.id == info_id).select(itable.alert_id, limitby=(0, 1)).first()
        alert_id = info.alert_id

        db(table.id == id).update(alert_id = alert_id)
        db.commit()

    return func

def info_onaccept(form):

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
    s3db = current.s3db

    atable, itable = db.cap_alert, db.cap_info

    info = itable(itable.id == info_id)
    alert_id = info.alert_id

    if alert_id and s3db.cap_alert_is_template(alert_id) and info:
        info.is_template = True
        info.update()

    return True
# END =========================================================================
