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
           "cap_alert_rheader",
           "cap_alert_controller",
           "cap_info_rheader",
           "cap_info_controller"]

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
             "cap_alert"]

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
        cap_alert_status_code_opts = {
            "Actual":T("Actual - actionable by all targeted recipients"),
            "Exercise":T("Exercise - only for designated participants (decribed in note)"),
            "System":T("System - for internal functions"),
            "Test":T("Test - testing, all recipients disregard"),
            "Draft":T("Draft - not actionable in its current form"),
        }
        # CAP alert message type (msgType)
        cap_alert_msgType_code_opts = {
            "Alert":T("Alert: Initial information requiring attention by targeted recipients"),
            "Update":T("Update: Update and supercede earlier message(s)"),
            "Cancel":T("Cancel: Cancel earlier message(s)"),
            "Ack":T("Ack: Acknowledge receipt and acceptance of the message(s)"),
            "Error":T("Error: Indicate rejection of the message(s)"),
        }
        # CAP alert scope
        cap_alert_scope_code_opts = {
            "Public": "Public - unrestricted audiences",
            "Restricted": "Restricted - to users with a known operational requirement (described in restriction)",
            "Private": "Private - only to specified addresses (mentioned as recipients)"
        }

        # @ToDo: i18n: Need label=T("")
        tablename = "cap_alert"
        table = define_table(tablename,
                             # identifier string, as was recieved.
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
                             Field("codes", "list:string",
                                   widget = S3KeyValueWidget(),
                                   represent = lambda v: \
                                    self.list_string_represent(v, lambda i: \
                                            ": ".join(i.split("`", 1))),
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

        alert_id = S3ReusableField("alert_id", db.cap_alert,
                                   sortby = "identifier",
                                   requires = IS_NULL_OR(
                                    IS_ONE_OF(db, "cap_alert.id",
                                              label = self.alert_represent)),
                                   represent = self.alert_represent,
                                   label = T("Alert"),
                                   comment = T("The alert message containing this information"),
                                   ondelete = "RESTRICT")

        # CAP Informations as component of Alerts
        add_component("cap_info", cap_alert="alert_id")

        # @ToDo: Move these to the controller in a prep if r.interactive
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
        cap_info_category_opts = {
            "Geo":T("Geophysical (inc. landslide)"),
            "Met":T("Meteorological (inc. flood)"),
            "Safety":T("General emergency and public safety"),
            "Security":T("Law enforcement, military, homeland and local/private security"),
            "Rescue":T("Rescue and recovery"),
            "Fire":T("Fire suppression and rescue"),
            "Health":T("Medical and public health"),
            "Env":T("Pollution and other environmental"),
            "Transport":T("Public and private transportation"),
            "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
            "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
            "Other":T("Other events"),
        }
        # CAP info Response Type (responseType)
        cap_info_responseType_opts = {
            "Shelter":T("Shelter - Take shelter in place or per instruction"),
            "Evacuate":T("Evacuate - Relocate as instructed in the instruction"),
            "Prepare":T("Prepare - Make preparations per the instruction"),
            "Execute":T("Execute - Execute a pre-planned activity identified in instruction"),
            "Avoid":T("Avoid - Avoid the subject event as per the instruction"),
            "Monitor":T("Monitor - Attend to information sources as described in instruction"),
            "Assess":T("Assess - Evaluate the information in this message."),
            "AllClear":T("AllClear - The subject event no longer poses a threat"),
            "None":T("None - No action recommended"),
        }
        # CAP info urgency
        cap_info_urgency_opts = {
            "Immediate":T("Respone action should be taken immediately"),
            "Expected":T("Response action should be taken soon (within next hour)"),
            "Future":T("Responsive action should be taken in the near future"),
            "Past":T("Responsive action is no longer required"),
            "Unknown":T("Unknown"),
        }
        # CAP info severity
        cap_info_severity_opts = {
            "Extreme":T("Extraordinary threat to life or property"),
            "Severe":T("Significant threat to life or property"),
            "Moderate":T("Possible threat to life or property"),
            "Minor":T("Minimal to no known threat to life or property"),
            "Unknown":T("Severity unknown"),
        }
        # CAP info certainty
        cap_info_certainty_opts = {
            "Observed":T("Observed: determined to have occurred or to be ongoing"),
            "Likely":T("Likely (p > ~50%)"),
            "Possible":T("Possible but not likely (p <= ~50%)"),
            "Unlikely":T("Not expected to occur (p ~ 0)"),
            "Unknown":T("Certainty unknown"),
        }

        # @ToDo: i18n: Need label=T("")
        tablename = "cap_info"
        table = define_table(tablename,
                             alert_id(),
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
                             Field("urgency", notnull=True,
                                   requires=IS_IN_SET(cap_info_urgency_opts)),
                             Field("severity", notnull=True,
                                   requires=IS_IN_SET(cap_info_severity_opts)),
                             Field("certainty", notnull=True,
                                   requires=IS_IN_SET(cap_info_certainty_opts)),
                             Field("audience", "text"),
                             Field("event_code", "list:string",
                                   widget = S3KeyValueWidget(),
                                   represent = lambda v: \
                                    self.list_string_represent(v, lambda i: \
                                        ": ".join(i.split("`", 1)))
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
                             Field("parameter", "list:string",
                                   label = T("Parameters"),
                                   widget = S3KeyValueWidget(),
                                   represent = lambda v: \
                                    self.list_string_represent(v, lambda i: \
                                        ": ".join(i.split("`", 1)))),
                             *s3_meta_fields())

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

        info_id = S3ReusableField("info_id", db.cap_info,
                                  sortby="identifier",
                                  requires=IS_NULL_OR(
                                    IS_ONE_OF(db, "cap_info.id",
                                              label = self.info_represent)),
                                  represent = self.info_represent,
                                  label = T("Alert Information"),
                                  comment = T("The alert information"),
                                  ondelete = "RESTRICT")

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
                             Field("resource_desc", required=True),
                             Field("mime_type", notnull=True),
                             Field("size", "integer",
                                   writable = False),
                             Field("uri",
                                   writable = False), # needs a special validation
                             Field("file", "upload"),
                             # XXX: Should this be made per-info instead of per-file?
                             Field("base64encode", "boolean",
                                   label = T("Encode in message?")),
                             #Field("deref_uri", "text"), <-- base 64 encoded
                             Field("digest",
                                   writable=False),
                             *s3_meta_fields())

        # @ToDo: CRUD Strings

        # Resource as component of Information
        add_component("cap_info_resource", cap_info="info_id")

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


        #table.deref_uri.writable = False
        #table.deref_uri.readable = False

        table.base64encode.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Should this file be encoded into the CAP Message and sent?"),
                  T("Selecting this will encode the file in Base 64 encoding (which converts it into text) and sends it embedded in the CAP message. This is useful in one-way network where the sender cannot create URLs publicly accessible over the internet.")))

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
                                  Field("area_desc",
                                        label = T("Area description"),
                                        required=True),
                                  Field("polygon", "text"),
                                  Field("circle"),
                                  Field("geocode", "list:string",
                                        widget = S3KeyValueWidget()),
                                  Field("altitude", "integer"),
                                  Field("ceiling", "integer"),
                                  *s3_meta_fields())

        # @ToDo: CRUD Strings

        # Area as component of Information
        add_component("cap_info_area", cap_info="info_id")

        # @ToDo: Move these to the controller in a prep if r.interactive
        table.area_desc.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The affected area of the alert message"),
                  T("A text description of the affected area.")))

        table.polygon.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Points defining a polygon that delineates the affected area"),
                  T("")))

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

        table = current.s3db.cap_alert
        r = current.db().select(table.id,
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
        user_id = current.auth.user.id
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
                                     # left = table.on(table.id == table.parent_item_category_id), Doesn't work
                                     limitby=(0, 1)).first()

        #XXX: Should get headline from "info"?
        if r.msg_type:
            sent = r.sent or r.created_on
            return "%s - %s - %s" % (r.msg_type, sent, r.sender)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def list_string_represent(string, fmt=lambda v: v):
        try:
            if isinstance(string, list):
                return ", ".join([fmt(i) for i in string])
            else:
                return ", ".join([fmt(i) for i in string[1:-1].split("|")])
        except IndexError:
            return current.messages.NONE

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

        table = current.s3db.cap_info
        query = (table.id == id)
        r = current.db(query).select(table.headline,
                                     table.alert_id,
                                     table.language,
                                     limitby=(0, 1)).first()

        #XXX: Should get headline from "info"?
        return "%s - %s" % (r.language, r.headline)

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
                    (T("Edit Details"), None),
                    (T("Edit Information"), "info"),
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
def cap_info_rheader(r):
    """ Resource Header for Info segments """

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            tabs = [
                    (T("Edit Information"), None),
                    (T("Edit Area"), "info_area"),
                    (T("Resource Files"), "info_resource"),
                   ]

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
def add_submit_button(form, name, value, style="font-weight: bold"):
    """
    """

    form[0][-1][0].insert(1, TAG[""](" ",
                INPUT(_type="submit", _name=name, _style=style,
                      _value=value)))

# =============================================================================
def cap_alert_controller():
    """ RESTful CRUD controller """

    output = current.rest_controller("cap", "alert",
                                     rheader=current.s3db.cap_alert_rheader)

    if "form" in output:
        form = output["form"]

        tablename = form.table._tablename

        T = current.T

        if tablename == 'cap_alert':
            add_submit_button(form, "add_info", T("Save and add information..."))

        if tablename == 'cap_info':
            add_submit_button(form, "add_resource", T("Save and attach a file..."), "")
            add_submit_button(form, "add_area", T("Save and add area..."))
            add_submit_button(form, "add_language", T("Save and add another language..."))

    return output

# =============================================================================
def cap_info_controller():
    """ RESTful CRUD controller """

    output = current.rest_controller("cap", "info",
                                     rheader=current.s3db.cap_info_rheader)
    if "form" in output:
        add_submit_button(output["form"], "add_language",
                          current.T("Save and add another language..."))

    return output

# END =========================================================================
