# -*- coding: utf-8 -*-

""" Sahana Eden Common Alerting Protocol (CAP) Model

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("get_cap_options",
           "S3CAPModel",
           "S3CAPHistoryModel",
           "S3CAPAlertingAuthorityModel",
           "S3CAPAreaNameModel",
           "S3CAPMessageModel",
           "cap_alert_is_template",
           "cap_rheader",
           "cap_history_rheader",
           "cap_alert_list_layout",
           "add_area_from_template",
           "cap_expirydate",
           "cap_ImportAlert",
           "cap_AssignArea",
           "cap_AreaRepresent",
           "cap_CloneAlert",
           "cap_AlertProfileWidget",
           #"cap_gis_location_xml_post_parse",
           #"cap_gis_location_xml_post_render",
           )

import os
import datetime
import urllib2 # Needed for quoting & error handling on fetch

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

OIDPATTERN = r"^[^,<&\s]+$"

# =============================================================================
def get_cap_options():

    # List of Incident Categories -- copied from irs module <--
    # @ToDo: Switch to using event_incident_type
    #
    # The keys are based on the Canadian ems.incident hierarchy, with a
    # few extra general versions added to 'other'
    # The values are meant for end-users, so can be customised as-required
    # NB It is important that the meaning of these entries is not changed
    # as otherwise this hurts our ability to do synchronisation
    # Entries can be hidden from user view in the controller.
    # Additional sets of 'translations' can be added to the tuples.
    T = current.T
    cap_options = {}
    cap_options["cap_incident_type_opts"] = {
        "accident": T("Accident"),
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
        "health.disease": T("Disease"),
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
        # http://en.wikipedia.org/wiki/Amber_Alert
        "missingPerson.amberAlert": T("Child Abduction Emergency"),
        "missingPerson.missingVulnerablePerson": T("Missing Vulnerable Person"),
        # http://en.wikipedia.org/wiki/Silver_Alert
        "missingPerson.silver": T("Missing Senior Citizen"),
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

    # CAP alert Status Code (status)
    cap_options["cap_alert_status_code_opts"] = OrderedDict([
        ("Actual", T("Actual - actionable by all targeted recipients")),
        ("Exercise", T("Exercise - only for designated participants (decribed in note)")),
        ("System", T("System - for internal functions")),
        ("Test", T("Test - testing, all recipients disregard")),
        ("Draft", T("Draft - not actionable in its current form")),
    ])

    # CAP alert message type (msgType)
    # NB AllClear is not in msgType as of CAP 1.2, but they target to move it to
    # msgType instead of responseType in CAP 2.0
    cap_options["cap_alert_msg_type_code_opts"] = OrderedDict([
        ("Alert", T("Alert: Initial information requiring attention by targeted recipients")),
        ("Update", T("Update: Update and supercede earlier message(s)")),
        ("Cancel", T("Cancel: Cancel earlier message(s)")),
        ("Ack", T("Ack: Acknowledge receipt and acceptance of the message(s)")),
        ("Error", T("Error: Indicate rejection of the message(s)")),
        #("AllClear", T("AllClear - The subject event no longer poses a threat")),
    ])

    # CAP alert scope
    cap_options["cap_alert_scope_code_opts"] = OrderedDict([
        ("Public", T("Public - unrestricted audiences")),
        ("Restricted", T("Restricted - to users with a known operational requirement (described in restriction)")),
        ("Private", T("Private - only to specified addresses (mentioned as recipients)"))
    ])

    # CAP info categories
    cap_options["cap_info_category_opts"] = OrderedDict([
        ("Geo", T("Geo - Geophysical (inc. landslide)")),
        ("Met", T("Met - Meteorological (inc. flood)")),
        ("Safety", T("Safety - General emergency and public safety")),
        ("Security", T("Security - Law enforcement, military, homeland and local/private security")),
        ("Rescue", T("Rescue - Rescue and recovery")),
        ("Fire", T("Fire - Fire suppression and rescue")),
        ("Health", T("Health - Medical and public health")),
        ("Env", T("Env - Pollution and other environmental")),
        ("Transport", T("Transport - Public and private transportation")),
        ("Infra", T("Infra - Utility, telecommunication, other non-transport infrastructure")),
        ("CBRNE", T("CBRNE - Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack")),
        ("Other", T("Other - Other events")),
    ])

    # CAP info response type
    cap_options["cap_info_response_type_opts"] = OrderedDict([
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
    cap_options["cap_info_urgency_opts"] = OrderedDict([
        ("Immediate", T("Immediate - Response action should be taken immediately")),
        ("Expected", T("Expected - Response action should be taken soon (within next hour)")),
        ("Future", T("Future - Responsive action should be taken in the near future")),
        ("Past", T("Past - Responsive action is no longer required")),
        ("Unknown", T("Unknown")),
    ])

    # CAP info severity
    cap_options["cap_info_severity_opts"] = OrderedDict([
        ("Extreme", T("Extreme - Extraordinary threat to life or property")),
        ("Severe", T("Severe - Significant threat to life or property")),
        ("Moderate", T("Moderate - Possible threat to life or property")),
        ("Minor", T("Minor - Minimal to no known threat to life or property")),
        ("Unknown", T("Severity unknown")),
    ])

    # CAP info certainty
    cap_options["cap_info_certainty_opts"] = OrderedDict([
        ("Observed", T("Observed: determined to have occurred or to be ongoing")),
        ("Likely", T("Likely (p > ~50%)")),
        ("Possible", T("Possible but not likely (p <= ~50%)")),
        ("Unlikely", T("Unlikely - Not expected to occur (p ~ 0)")),
        ("Unknown", T("Certainty unknown")),
    ])

    return cap_options

# =============================================================================
class S3CAPModel(S3Model):
    """
        CAP: Common Alerting Protocol
        - this module is a non-functional stub

        http://eden.sahanafoundation.org/wiki/BluePrint/Messaging#CAP
    """

    names = ("cap_alert",
             "cap_alert_id",
             "cap_alert_represent",
             "cap_alert_approve",
             "cap_warning_priority",
             "cap_info",
             "cap_info_represent",
             "cap_info_parameter",
             "cap_resource",
             "cap_area",
             "cap_area_id",
             "cap_area_represent",
             "cap_area_location",
             "cap_area_tag",
             "cap_info_category_opts",
             "cap_expiry_date",
             "cap_sender_name",
             "cap_template_represent",
             "cap_alert_ack",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        cap_options = get_cap_options()
        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        #UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        tablename = "cap_alert"
        define_table(tablename,
                     Field("is_template", "boolean",
                           readable = False,
                           writable = True,
                           ),
                     self.event_type_id(#empty = False,
                                        ondelete = "SET NULL",
                                        label = T("Event Type"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Event Type of the alert message"),
                                                                        T("Event Type is classification of event."))),
                                        script = '''
$.filterOptionsS3({
    'trigger':'event_type_id',
    'target':'template_id',
    'lookupPrefix': 'cap',
    'lookupResource':'template',
    'fncRepresent': function(record,PrepResult){return record.template_title},
    'optional': true,
    'lookupURL': S3.Ap.concat('/cap/template.json?~.event_type_id=')
})'''
                     ),
                     Field("template_id", "reference cap_alert",
                           label = T("Template"),
                           ondelete = "SET NULL",
                           represent = self.cap_template_represent,
                           requires = IS_EMPTY_OR(
                                         IS_ONE_OF(db, "cap_alert.id",
                                                   self.cap_template_represent,
                                                   filterby="is_template",
                                                   filter_opts=(True,)
                                                   )),
                           comment = T("Apply a template"),
                           ),
                     Field("template_title",
                           label = T("Template Title"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Template Title"),
                                                           T("Title for the template, to indicate to which event this template is related to"))),
                           ),
                     Field("template_settings", "text",
                           default = "{}",
                           readable = False,
                           ),
                     Field("identifier", unique=True, length=255,
                           default = self.generate_identifier,
                           label = T("Identifier"),
                           requires = [IS_LENGTH(255),
                                       IS_MATCH(OIDPATTERN,
                                                error_message=T("Cannot be empty and Must not include spaces, commas, or restricted characters (< and &)."),
                                                ),
                                       ],
                           # Dont Allow to change the identifier
                           writable = False,
                           readable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A unique identifier of the alert message"),
                                                           T("A number or string uniquely identifying this message, assigned by the sender. Must not include spaces, commas or restricted characters (< and &)."))),
                           ),
                     # @ToDo: Switch to using event_incident_type_id
                     Field("incidents", "list:string",
                           label = T("Incidents"),
                           represent = S3Represent(options = cap_options["cap_incident_type_opts"],
                                                   multiple = True),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_incident_type_opts"],
                                                  multiple = True,
                                                  sort = True,
                                                  )),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A list of incident(s) referenced by the alert message"),
                                                           T("Used to collate multiple messages referring to different aspects of the same incident. If multiple incident identifiers are referenced, they SHALL be separated by whitespace.  Incident names including whitespace SHALL be surrounded by double-quotes."))),
                           ),
                     Field("sender",
                           label = T("Sender"),
                           default = self.generate_sender,
                           readable = False,
                           writable = False,
                           requires = IS_MATCH(OIDPATTERN,
                                               error_message=T("Cannot be empty and Must not include spaces, commas, or restricted characters (< and &).")),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the sender of the alert message"),
                                                           T("This is guaranteed by assigner to be unique globally; e.g., may be based on an Internet domain name. Must not include spaces, commas or restricted characters (< and &)."))),
                           ),
                     s3_datetime("sent",
                                 default = "now",
                                 writable = False,
                                 ),
                     Field("status",
                           default = "Draft",
                           label = T("Status"),
                           represent = S3Represent(options = cap_options["cap_alert_status_code_opts"],
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_alert_status_code_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the appropriate handling of the alert message"),
                                                           T("See options."))),
                           ),
                     Field("msg_type",
                           label = T("Message Type"),
                           default = "Alert",
                           #represent = S3Represent(options = cap_options["cap_alert_msg_type_code_opts"],
                           #                        ),
                           requires = IS_IN_SET(cap_options["cap_alert_msg_type_code_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The nature of the alert message"),
                                                           T("See options."))),
                           ),
                     Field("source",
                           label = T("Source"),
                           default = self.generate_source,
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text identifying the source of the alert message"),
                                                           T("The particular source of this alert; e.g., an operator or a specific device."))),
                           ),
                     Field("scope",
                           label = T("Scope"),
                           requires = IS_EMPTY_OR(IS_IN_SET(cap_options["cap_alert_scope_code_opts"])),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the intended distribution of the alert message"),
                                                           T("Who is this alert for?"))),
                           ),
                     # Text describing the restriction for scope=restricted
                     Field("restriction", "text",
                           label = T("Restriction"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text describing the rule for limiting distribution of the restricted alert message"),
                                                           T("Used when scope is 'Restricted'."))),
                           ),
                     Field("addresses", "list:string",
                           label = T("Recipients"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(get_cap_alert_addresses_opts(),
                                                  multiple = True,
                                                  sort = True,
                                                  )
                                        ),
                           #represent = S3Represent(lookup = "pr_group",
                           #                        fields = ["name"],
                           #                        multiple = True,
                           #                        ),
                           widget = S3MultiSelectWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The group listing of intended recipients of the alert message"),
                                                           T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address."))),
                           ),
                     Field("codes", "list:string",
                           default = settings.get_cap_codes(),
                           label = T("Codes"),
                           represent = self.list_string_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Codes for special handling of the message"),
                                                           T("Any user-defined flags or special codes used to flag the alert message for special handling."))),
                           ),
                     Field("note", "text",
                           label = T("Note"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text describing the purpose or significance of the alert message"),
                                                           T("The message note is primarily intended for use with status 'Exercise' and message type 'Error'"))),
                           ),
                     # text data type because as the number of referenced alert
                     # goes on increasing, it could very easily be more than 512 chars
                     Field("reference", "text",
                           label = T("Reference"),
                           writable = False,
                           readable = False,
                           #represent = S3Represent(lookup = tablename,
                           #                        fields = ["msg_type", "sent", "sender"],
                           #                        field_sep = " - ",
                           #                        multiple = True,
                           #                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The group listing identifying earlier message(s) referenced by the alert message"),
                                                           T("The extended message identifier(s) (in the form sender,identifier,sent) of an earlier CAP message or messages referenced by this one."))),
                           # @ToDo: This should not be manually entered,
                           #        needs a widget
                           #widget = S3ReferenceWidget(table,
                           #                           one_to_many=True,
                           #                           allow_create=False),
                           ),
                     # approved_on field for recording when the alert was approved
                     s3_datetime("approved_on",
                                 readable = False,
                                 writable = False,
                                 ),
                     # To separate the external CAP Alert
                     Field("external", "boolean",
                           # This is set to true if interactive in prep
                           default = True,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        list_fields = ["event_type_id",
                       "msg_type",
                       (T("Sent"), "sent"),
                       "info.headline",
                       "info.sender_name",
                       ]

        notify_fields = [(T("Identifier"), "identifier"),
                         (T("Date"), "sent"),
                         (T("Status"), "status"),
                         (T("Message Type"), "msg_type"),
                         (T("Source"), "source"),
                         (T("Scope"), "scope"),
                         (T("Restriction"), "restriction"),
                         (T("Category"), "info.category"),
                         (T("Event"), "info.event_type_id"),
                         (T("Response type"), "info.response_type"),
                         (T("Priority"), "info.priority"),
                         (T("Urgency"), "info.urgency"),
                         (T("Severity"), "info.severity"),
                         (T("Certainty"), "info.certainty"),
                         (T("Effective"), "info.effective"),
                         (T("Expires at"), "info.expires"),
                         (T("Sender's name"), "info.sender_name"),
                         (T("Headline"), "info.headline"),
                         (T("Description"), "info.description"),
                         (T("Instruction"), "info.instruction"),
                         (T("Contact information"), "info.contact"),
                         (T("URL"), "info.web"),
                         (T("Area Description"), "area.name"),
                         ]

        filter_widgets = [
            S3TextFilter(["identifier",
                          "sender",
                          "incidents",
                          "cap_info.headline",
                          "cap_info.event",
                          ],
                         label = T("Search"),
                         comment = T("Search for an Alert by sender, incident, headline or event."),
                         ),
            S3OptionsFilter("info.category",
                            label = T("Category"),
                            options = cap_options["cap_info_category_opts"],
                            hidden = True,
                            ),
            S3OptionsFilter("info.event_type_id",
                            hidden = True,
                            ),
            S3OptionsFilter("scope",
                            hidden = True,
                            ),
            S3OptionsFilter("info.priority",
                            hidden = True,
                            ),
            S3LocationFilter("location.location_id",
                             label = T("Location(s)"),
                             # options = gis.get_countries().keys(),
                             hidden = True,
                             ),
            S3OptionsFilter("info.language",
                            label = T("Language"),
                            hidden = True,
                            ),
            ]

        configure(tablename,
                  context = {"location": "location.location_id",
                             },
                  create_onaccept = self.cap_alert_create_onaccept,
                  deduplicate = S3Duplicate(primary = ("identifier", ),
                                            secondary = ("sender", ),
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = cap_alert_list_layout,
                  #list_orderby = "cap_alert.sent desc",
                  # Required Fields
                  mark_required = ("scope",),
                  notify_fields = notify_fields,
                  onapprove = self.cap_alert_approve,
                  onvalidation = self.cap_alert_onvalidation,
                  # Order with most recent Alert first
                  orderby = "cap_alert.sent desc",
                  )

        # Components
        add_components(tablename,
                       cap_area = "alert_id",
                       cap_area_location = {"name": "location",
                                            "joinby": "alert_id",
                                            },
                       cap_area_tag = {"name": "tag",
                                       "joinby": "alert_id",
                                       },
                       cap_info = "alert_id",
                       cap_info_parameter = "alert_id",
                       cap_resource = "alert_id",
                       )

        # Custom Methods
        set_method("cap", "alert",
                   method = "import_feed",
                   action = cap_ImportAlert())

        set_method("cap", "alert",
                   method = "assign",
                   action = self.cap_AssignArea())

        set_method("cap", "alert",
                   method = "clone",
                   action = self.cap_CloneAlert())

        if crud_strings["cap_template"]:
            crud_strings[tablename] = crud_strings["cap_template"]
        else:
            crud_strings[tablename] = Storage(
                label_create = T("Create Alert"),
                title_display = T("Alert Details"),
                title_list = T("Alerts"),
                # If already-published, this should create a new "Update"
                # alert instead of modifying the original
                title_update = T("Edit Alert"),
                title_upload = T("Import Alerts"),
                label_list_button = T("List Alerts"),
                label_delete_button = T("Delete Alert"),
                msg_record_created = T("Alert created"),
                msg_record_modified = T("Alert modified"),
                msg_record_deleted = T("Alert deleted"),
                msg_list_empty = T("No alerts to show"))

        alert_represent = S3Represent(lookup = tablename,
                                      fields = ["msg_type", "sent", "sender"],
                                      field_sep = " - ")

        alert_id = S3ReusableField("alert_id", "reference %s" % tablename,
                                   comment = T("The alert message containing this information"),
                                   label = T("Alert"),
                                   ondelete = "CASCADE",
                                   represent = alert_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_alert.id",
                                                          alert_represent)),
                                   )

        # ---------------------------------------------------------------------
        # Warning Priorities for CAP

        tablename = "cap_warning_priority"
        define_table(tablename,
                     Field("priority_rank", "integer",
                           label = T("Priority Sequence"),
                           length = 2,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Priority Rank"),
                                                           T("The Priority Rank is basically to give it a ranking 1, 2, ..., n. That way we know 1 is the most important of the chain and n is lowest element. For eg. (1, Signal 1), (2, Signal 2)..., (5, Signal 5) to enumerate the priority for cyclone."))),
                           ),
                     Field("event_code",
                           label = T("Event Code"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Event Code"),
                                                           T("Code (key) for the event like for eg. (2001, Typhoon), (2002, Flood)"))),
                           ),
                     Field("name", notnull=True, length=64, unique=True,
                           label = T("Name"),
                           requires = [IS_LENGTH(64),
                                       IS_NOT_ONE_OF(db, "%s.name" % tablename),
                                       IS_MATCH('^[^"\']+$',
                                               error_message=T('Name cannot be empty and Must not include " or (\')'),
                                               ),
                                       ],
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Name"),
                                                           T("The actual name for the warning priority, for eg. Typhoons in Philippines have five priority names (PSWS# 1, PSWS# 2, PSWS# 3, PSWS# 4 and PSWS# 5)"))),
                           ),
                     self.event_type_id(empty=False,
                                        ondelete = "SET NULL",
                                        label = T("Event Type"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Event Type"),
                                                                        T("The Event to which this priority is targeted for."))),
                           ),
                     Field("urgency",
                           label = T("Urgency"),
                           requires = IS_IN_SET(cap_options["cap_info_urgency_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the urgency of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Immediate' - Responsive action should be taken immediately" +
                                                             "'Expected' - Responsive action should be taken soon (within next hour)" +
                                                             "'Future' - Responsive action should be taken in the near future" +
                                                             "'Past' - Responsive action is no longer required" +
                                                             "'Unknown' - Urgency not known"))),
                           ),
                     Field("severity",
                           label = T("Severity"),
                           requires = IS_IN_SET(cap_options["cap_info_severity_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the severity of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Extreme' - Extraordinary threat to life or property" +
                                                             "'Severe' - Significant threat to life or property" +
                                                             "'Moderate' - Possible threat to life or property" +
                                                             "'Minor' - Minimal to no known threat to life or property" +
                                                             "'Unknown' - Severity unknown"))),
                           ),
                     Field("certainty",
                           label = T("Certainty"),
                           requires = IS_IN_SET(cap_options["cap_info_certainty_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the certainty of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Observed' - Determined to have occurred or to be ongoing" +
                                                             "'Likely' - Likely (p > ~50%)" +
                                                             "'Possible' - Possible but not likely (p <= ~50%)" +
                                                             "'Unlikely' - Not expected to occur (p ~ 0)" +
                                                             "'Unknown' - Certainty unknown"))),
                           ),
                     Field("color_code",
                           label = T("Color Code"),
                           represent = warning_priority_color,
                           widget = S3ColorPickerWidget(options = {
                                        "showPaletteOnly": False,
                                    }),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The color code for this priority"),
                                                           T("Pick from the color widget the color that is associated to this priority of the event. The color code is in hex format"))),
                           ),
                     # to record the last checked time for the table.
                     # used to sent notifications to subscribers about available options
                     s3_datetime("last_checked",
                                 readable = False,
                                 writable = False,
                                 ),
                     *s3_meta_fields())

        priority_represent = S3Represent(lookup=tablename, translate=True)

        crud_strings[tablename] = Storage(
            label_create = T("Create Warning Classification"),
            title_display = T("Warning Classification Details"),
            title_list = T("Warning Classifications"),
            title_update = T("Edit Warning Classification"),
            title_upload = T("Import Warning Classifications"),
            label_list_button = T("List Warning Classifications"),
            label_delete_button = T("Delete Warning Classification"),
            msg_record_created = T("Warning Classification added"),
            msg_record_modified = T("Warning Classification updated"),
            msg_record_deleted = T("Warning Classification removed"),
            msg_list_empty = T("No Warning Classifications currently registered")
            )

        list_fields = ["event_type_id",
                       (T("Color"), "color_code"),
                       "name",
                       (T("Rank"), "priority_rank"),
                       ]

        configure(tablename,
                  create_onaccept = self.cap_warning_priority_onaccept,
                  # Not needed since unique=True
                  #deduplicate = S3Duplicate(primary=("event_type_id", "name")),
                  list_fields = list_fields,
                  #onvalidation = self.cap_warning_priority_onvalidation,
                  orderby = "cap_warning_priority.event_type_id,cap_warning_priority.priority_rank desc",
                  )

        # ---------------------------------------------------------------------
        # CAP info segment
        settings.L10n.extra_codes = [("en-US", "English"),
                                     ("en-CA", "Canadian English"),
                                     ("fr-CA", "Canadian French"),
                                     ]
        tablename = "cap_info"
        define_table(tablename,
                     alert_id(),
                     Field("is_template", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("template_info_id", "reference cap_info",
                           ondelete = "SET NULL",
                           readable = False,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "cap_info.id",
                                                  self.cap_template_represent,
                                                  filterby="is_template",
                                                  filter_opts=(True,)
                                                  )),
                           widget = S3HiddenWidget(),
                           ),
                     Field("template_settings", "text",
                           readable = False,
                           ),
                     s3_language(default = "en-US",
                                 empty = False,
                                 ),
                     Field("category", "list:string", # 1 or more allowed
                           label = T("Category"),
                           required = IS_NOT_EMPTY(),
                           represent = S3Represent(options = cap_options["cap_info_category_opts"],
                                                   multiple = True,
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_category_opts"],
                                                multiple = True,
                                                ),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the category of the subject event of the alert message"),
                                                           T("You may select multiple categories by holding down control and then selecting the items."))),
                           ),
                     Field("event",
                           label = T("Event"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text denoting the type of the subject event of the alert message"),
                                                           T("If not specified, will the same as the Event Type."))),
                           ),
                     self.event_type_id(#empty = False,
                                        readable = False,
                                        ondelete = "SET NULL",
                                        label = T("Event Type"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Event Type of the alert message"),
                                                                        T("Event field above is more general. And this Event Type is classification of event. For eg. Event can be 'Terrorist Attack' and Event Type can be either 'Terrorist Bomb Explosion' or 'Terrorist Chemical Waefare Attack'. If not specified, will the same as the Event Type."))),
                                        script = '''
                            $.filterOptionsS3({
                             'trigger':'event_type_id',
                             'target':'priority',
                             'lookupPrefix': 'cap',
                             'lookupResource':'warning_priority',
                             'lookupKey': 'event_type_id',
                             'optional': true
                             })'''
                     ),
                     Field("response_type", "list:string", # 0 or more allowed
                           label = T("Response Type"),
                           represent = S3Represent(options = cap_options["cap_info_response_type_opts"],
                                                   multiple = True,
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_response_type_opts"],
                                                multiple = True),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the type of action recommended for the target audience"),
                                                           T("Multiple response types can be selected by holding down control and then selecting the items"))),
                           ),
                     Field("priority", "reference cap_warning_priority",
                           label = T("Priority"),
                           represent = priority_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "cap_warning_priority.id",
                                                  priority_represent
                                                  ),
                                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Priority of the alert message"),
                                                           T("Defines the priority of the alert message. Selection of the priority automatically sets the value for 'Urgency', 'Severity' and 'Certainty'"))),
                           ),
                     Field("urgency",
                           label = T("Urgency"),
                           represent = S3Represent(options = cap_options["cap_info_urgency_opts"],
                                                   ),
                           # Empty For Template, checked onvalidation hook
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_info_urgency_opts"])),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the urgency of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Immediate' - Responsive action should be taken immediately" +
                                                             "'Expected' - Responsive action should be taken soon (within next hour)" +
                                                             "'Future' - Responsive action should be taken in the near future" +
                                                             "'Past' - Responsive action is no longer required" +
                                                             "'Unknown' - Urgency not known"))),
                           ),
                     Field("severity",
                           label = T("Severity"),
                           represent = S3Represent(options = cap_options["cap_info_severity_opts"],
                                                   ),
                           # Empty For Template, checked onvalidation hook
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_info_severity_opts"])),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the severity of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Extreme' - Extraordinary threat to life or property" +
                                                             "'Severe' - Significant threat to life or property" +
                                                             "'Moderate' - Possible threat to life or property" +
                                                             "'Minor' - Minimal to no known threat to life or property" +
                                                             "'Unknown' - Severity unknown"))),
                           ),
                     Field("certainty",
                           label = T("Certainty"),
                           represent = S3Represent(options = cap_options["cap_info_certainty_opts"],
                                                   ),
                           # Empty For Template, checked onvalidation hook
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_info_certainty_opts"])),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the certainty of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Observed' - Determined to have occurred or to be ongoing" +
                                                             "'Likely' - Likely (p > ~50%)" +
                                                             "'Possible' - Possible but not likely (p <= ~50%)" +
                                                             "'Unlikely' - Not expected to occur (p ~ 0)" +
                                                             "'Unknown' - Certainty unknown"))),
                           ),
                     Field("audience", "text",
                           label = T("Audience"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Audience"),
                                                           T("The intended audience of the alert message"))),
                           ),
                     Field("event_code", "text",
                           label = T("Event Code"),
                           default = settings.get_cap_event_codes(),
                           represent = S3KeyValueWidget.represent,
                           widget = S3KeyValueWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A system-specific code identifying the event type of the alert message"),
                                                           T("Any system-specific code for events, in the form of key-value pairs. (e.g., SAME, FIPS, ZIP)."))),
                           ),
                     s3_datetime("effective",
                                 label = T("Effective"),
                                 default = "now",
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("The effective time of the information of the alert message"),
                                                                 T("If not specified, the effective time shall be assumed to be the same the time the alert was sent."))),
                                 ),
                     s3_datetime("onset",
                                 label = T("Onset"),
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Onset"),
                                                                 T("The expected time of the beginning of the subject event of the alert message"))),
                                 ),
                     s3_datetime("expires",
                                 label = T("Expires at"),
                                 #past = 0,
                                 default = cap_expirydate(),
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("The expiry time of the information of the alert message"),
                                                                 T("If this item is not provided, each recipient is free to enforce its own policy as to when the message is no longer in effect."))),
                                 ),
                     Field("sender_name",
                           label = T("Sender's name"),
                           default = self.cap_sendername,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text naming the originator of the alert message"),
                                                           T("The human-readable name of the agency or authority issuing this alert."))),
                           ),
                     Field("headline",
                           label = T("Headline"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text headline of the alert message"),
                                                           T("A brief human-readable headline.  Note that some displays (for example, short messaging service devices) may only present this headline; it should be made as direct and actionable as possible while remaining short.  160 characters may be a useful target limit for headline length."))),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The subject event of the alert message"),
                                                           T("An extended human readable description of the hazard or event that occasioned this message."))),
                           ),
                     Field("instruction", "text",
                           label = T("Instruction"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The recommended action to be taken by recipients of the alert message"),
                                                           T("An extended human readable instruction to targeted recipients.  If different instructions are intended for different recipients, they should be represented by use of multiple information blocks. You can use a different information block also to specify this information in a different language."))),
                           ),
                     Field("contact", "text",
                           label = T("Contact information"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Contact"),
                                                           T("The contact for follow-up and confirmation of the alert message"))),
                           ),
                     Field("web",
                           label = T("URL"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A URL associating additional information with the alert message"),
                                                           T("A full, absolute URI for an HTML page or other text resource with additional or reference information regarding this alert."))),
                           ),
                     #Field("parameter", "text",
                     #      default = settings.get_cap_parameters(),
                     #      label = T("Parameters"),
                     #      represent = S3KeyValueWidget.represent,
                     #      widget = S3KeyValueWidget(),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("A system-specific additional parameter associated with the alert message"),
                     #                                      T("Any system-specific datum, in the form of key-value pairs."))),
                     #      ),
                     *s3_meta_fields())

        if crud_strings["cap_template_info"]:
            crud_strings[tablename] = crud_strings["cap_template_info"]
        else:
            ADD_INFO = T("Add alert information")
            crud_strings[tablename] = Storage(
                label_create = ADD_INFO,
                title_display = T("Alert information"),
                title_list = T("Information entries"),
                title_update = T("Update alert information"), # this will create a new "Update" alert?
                title_upload = T("Import alert information"),
                subtitle_list = T("Listing of alert information items"),
                label_list_button = T("List information entries"),
                label_delete_button = T("Delete Information"),
                msg_record_created = T("Alert information created"),
                msg_record_modified = T("Alert information modified"),
                msg_record_deleted = T("Alert information deleted"),
                msg_list_empty = T("No alert information to show"))

        info_represent = S3Represent(lookup = tablename,
                                     fields = ["language", "headline"],
                                     field_sep = " - ")

        info_id = S3ReusableField("info_id", "reference %s" % tablename,
                                  label = T("Information Segment"),
                                  ondelete = "CASCADE",
                                  represent = info_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_info.id",
                                                          info_represent)
                                                ),
                                  #sortby = "identifier",
                                  )

        crud_form = S3SQLCustomForm("alert_id",
                                    "is_template",
                                    "template_info_id",
                                    # Not used
                                    #"template_settings",
                                    "language",
                                    "category",
                                    "event",
                                    "event_type_id",
                                    "response_type",
                                    "priority",
                                    "urgency",
                                    "severity",
                                    "certainty",
                                    "audience",
                                    "event_code",
                                    "effective",
                                    "onset",
                                    "expires",
                                    "sender_name",
                                    "headline",
                                    "description",
                                    "instruction",
                                    "contact",
                                    "web",
                                    S3SQLInlineComponent("info_parameter",
                                                         name = "info_parameter",
                                                         label = T("Parameter"),
                                                         fields = ["name",
                                                                   "value",
                                                                   "mobile",
                                                                   ],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("A system-specific additional parameter associated with the alert message"),
                                                                                         T("Any system-specific datum, in the form of key-value pairs."))),
                                                         ),
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  deduplicate = self.cap_info_duplicate,
                  # Required Fields
                  mark_required = ("urgency", "severity", "certainty",),
                  onaccept = self.cap_info_onaccept,
                  onvalidation = self.cap_info_onvalidation,
                  )

        # Components
        add_components(tablename,
                       cap_info_parameter = "info_id",
                       cap_resource = "info_id",
                       cap_area = "info_id",
                       )

        # ---------------------------------------------------------------------
        # CAP Info Parameters
        tablename = "cap_info_parameter"
        define_table(tablename,
                     alert_id(),
                     info_id(),
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     Field("mobile", "boolean",
                           default = False,
                           label = T("Mobile"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.cap_info_parameter_onaccept,
                  #onvalidation = self.cap_info_parameter_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # CAP Resource segments
        #
        # Resource elements sit inside the Info segment of the export XML
        # - however in most cases these would be common across all Infos, so in
        #   our internal UI we link these primarily to the Alert but still
        #   allow the option to differentiate by Info
        #
        tablename = "cap_resource"
        define_table(tablename,
                     alert_id(writable = False,
                              ),
                     # Only used for imports
                     # in CAP, resource are linked to alert
                     info_id(readable = False,
                             writable = False,
                             ),
                     Field("is_template", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     self.super_link("doc_id", "doc_entity"),
                     Field("resource_desc",
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The type and content of the resource file"),
                                                           T("The human-readable text describing the type and content, such as 'map' or 'photo', of the resource file."))),
                           ),
                     # Using image field instead of doc_id because the CropWidget doesn't work in inline forms
                     Field("image", "upload",
                           label = T("Image"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.doc_image_represent,
                           requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                           error_message=\
T("Upload an image file(bmp, gif, jpeg or png), max. 800x800 pixels!"))),
                           uploadfolder = os.path.join(current.request.folder,
                                                       "uploads", "images"),
                           widget = S3ImageCropWidget((800, 800)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Image"),
                                                           T("Attach an image that provides extra information about the event"))),
                           ),
                     Field("mime_type",
                           requires = IS_NOT_EMPTY(),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the MIME content type and sub-type describing the resource file"),
                                                           T("MIME content type and sub-type as described in [RFC 2046]. (As of this document, the current IANA registered MIME types are listed at http://www.iana.org/assignments/media-types/)"))),
                           ),
                     Field("size", "integer",
                           label = T("Size in Bytes"),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The integer indicating the size of the resource file"),
                                                           T("Approximate size of the resource file in bytes."))),
                           ),
                     Field("uri",
                           label = T("Link to any resources"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the hyperlink for the resource file"),
                                                           T("A full absolute URI, typically a Uniform Resource Locator that can be used to retrieve the resource over the Internet."))),
                           ),
                     #Field("file", "upload"),
                     Field("deref_uri", "text",
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Deref URI"),
                                                           T("The base-64 encoded data content of the resource file"))),
                           ),
                     Field("digest",
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The code representing the digital digest ('hash') computed from the resource file"),
                                                           T("Calculated using the Secure Hash Algorithm (SHA-1)."))),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
                    label_create = T("Add Resource"),
                    title_display = T("Alert Resource"),
                    title_list = T("Resources"),
                    title_update = T("Edit Resource"),
                    subtitle_list = T("List Resources"),
                    label_list_button = T("List Resources"),
                    label_delete_button = T("Delete Resource"),
                    msg_record_created = T("Resource added"),
                    msg_record_modified = T("Resource updated"),
                    msg_record_deleted = T("Resource deleted"),
                    msg_list_empty = T("No resources currently defined for this alert"))

        # @todo: complete custom form
        crud_form = S3SQLCustomForm("alert_id",
                                    "info_id",
                                    "is_template",
                                    "resource_desc",
                                    "uri",
                                    "image",
                                    "mime_type",
                                    "size",
                                    # The CropWidget doesn't work in inline forms
                                    #S3SQLInlineComponent("image",
                                    #                     label = T("Image"),
                                    #                     fields = [("", "file")],
                                    #                     comment = DIV(_class="tooltip",
                                    #                                   _title="%s|%s" % (T("Image"),
                                    #                                                     T("Attach an image that provides extra information about the event."))),
                                    #                     ),
                                    S3SQLInlineComponent("document",
                                                         label = T("Document"),
                                                         fields = [("", "file")],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("Document"),
                                                                                         T("Attach document that provides extra information about the event."))),
                                                         ),
                                    )

        list_fields = ["resource_desc",
                       "uri",
                       "image",
                       "document.file",
                       ]

        configure(tablename,
                  crud_form = crud_form,
                  list_fields = list_fields,
                  onaccept = self.cap_resource_onaccept,
                  onvalidation = self.cap_resource_onvalidation,
                  super_entity = "doc_entity",
                  )

        # ---------------------------------------------------------------------
        # CAP Area segments
        #
        # Area elements sit inside the Info segment of the export XML
        # - however in most cases these would be common across all Infos, so in
        #   our internal UI we link these primarily to the Alert but still
        #   allow the option to differentiate by Info
        #
        # Each <area> can have multiple elements which are one of <polygon>,
        # <circle>, or <geocode>.
        # <polygon> and <circle> are explicit geometry elements.
        # <geocode> is a key-value pair in which the key is a standard
        # geocoding system like SAME, FIPS, ZIP, and the value is a defined
        # value in that system. The region described by the <area> is the
        # union of the areas described by the individual elements, but the
        # CAP spec advises that, if geocodes are included, the concrete
        # geometry elements should outline the area specified by the geocodes,
        # as not all recipients will have access to the meanings of the
        # geocodes. However, since geocodes are a compact way to describe an
        # area, it may be that they will be used without accompanying geometry,
        # so we should not count on having <polygon> or <circle>.
        #
        # Geometry elements are each represented by a gis_location record, and
        # linked to the cap_area record via the cap_area_location link table.
        # For the moment, <circle> objects are stored with the center in the
        # gis_location's lat, lon, and radius (in km) as a tag "radius" and
        # value. ToDo: Later, we will add CIRCLESTRING WKT.
        #
        # Geocode elements are currently stored as key value pairs in the
        # cap_area record.
        #
        # <area> can also specify a minimum altitude and maximum altitude
        # ("ceiling"). These are stored in explicit fields for now, but could
        # be replaced by key value pairs, if it is found that they are rarely
        # used.
        #
        # (An alternative would be to have cap_area link to a gis_location_group
        # record. In that case, the geocode tags could be stored in the
        # gis_location_group's overall gis_location element's tags. The altitude
        # could be stored in the overall gis_location's elevation, with ceiling
        # stored in a tag. We could consider adding a maximum elevation field.)

        tablename = "cap_area"
        define_table(tablename,
                     alert_id(),
                     # Only used for imports
                     # in CAP, area are linked to alert
                     info_id(readable = False,
                             writable = False,
                             ),
                     # From which template area is the area assigned from
                     # Used for internationalisation
                     Field("template_area_id", "reference cap_area",
                           ondelete = "SET NULL",
                           readable = False,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "cap_area.id",
                                                  filterby="is_template",
                                                  filter_opts=(True,)
                                                  )),
                           widget = S3HiddenWidget(),
                           ),
                     Field("is_template", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("name", length=1024,
                           label = T("Area Description"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(1024),
                                       ],
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The affected area of the alert message"),
                                                           T("A text description of the affected area."))),
                           ),
                     Field("altitude", "integer", # Feet above Sea-level in WGS84 (Specific or Minimum is using a range)
                           label = T("Altitude"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The specific or minimum altitude of the affected area"),
                                                           T("If used with the ceiling element this value is the lower limit of a range. Otherwise, this value specifies a specific altitude. The altitude measure is in feet above mean sea level."))),
                           ),
                     Field("ceiling", "integer", # Feet above Sea-level in WGS84 (Maximum)
                           label = T("Ceiling"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The maximum altitude of the affected area"),
                                                           T("must not be used except in combination with the 'altitude' element. The ceiling measure is in feet above mean sea level."))),
                           ),
                     # Only used for Templates
                     self.event_type_id(ondelete = "SET NULL",
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Event Type of this predefined alert area"),
                                                                        T("Event Type relating to this predefined area."))),
                            #            script = '''
                            #$.filterOptionsS3({
                            # 'trigger':'event_type_id',
                            # 'target':'priority',
                            # 'lookupPrefix': 'cap',
                            # 'lookupResource': 'warning_priority',
                            # 'lookupKey': 'event_type_id'
                            # })'''
                     ),
                     # Only used for Templates
                     # Enable this when required
                     #Field("priority", "reference cap_warning_priority",
                     #      label = T("Priority"),
                     #      represent = priority_represent,
                     #      requires = IS_EMPTY_OR(
                     #                   IS_ONE_OF(
                     #                             db, "cap_warning_priority.id",
                     #                             priority_represent
                     #                             ),
                     #                  ),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("Priority of the Event Type"),
                     #                                      T("Defines the priority of the Event Type for this predefined area."))),
                     #      ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Area"),
            title_display = T("Alert Area"),
            title_list = T("Areas"),
            title_update = T("Edit Area"),
            subtitle_list = T("List Areas"),
            label_list_button = T("List Areas"),
            label_delete_button = T("Delete Area"),
            msg_record_created = T("Area added"),
            msg_record_modified = T("Area updated"),
            msg_record_deleted = T("Area deleted"),
            msg_list_empty = T("No areas currently defined for this alert"))


        crud_form = S3SQLCustomForm("alert_id",
                                    "info_id",
                                    "is_template",
                                    "event_type_id",
                                    #"priority",
                                    "name",
                                    S3SQLInlineComponent("location",
                                                         name = "location",
                                                         multiple = False,
                                                         fields = [("", "location_id")],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("Geolocation"),
                                                                                         T("The paired values of points defining a polygon that delineates the affected area of the alert message"))),
                                                         ),
                                    S3SQLInlineComponent("tag",
                                                         name = "tag",
                                                         fields = ["tag",
                                                                   "value",
                                                                   ],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("The geographic code delineating the affected area"),
                                                                                         T("Any geographically-based code to describe a message target area, in the form. The key is a user-assigned string designating the domain of the code, and the content of value is a string (which may represent a number) denoting the value itself (e.g., name='ZIP' and value='54321'). This should be used in concert with an equivalent description in the more universally understood polygon and circle forms whenever possible."))),
                                                         ),
                                    "altitude",
                                    "ceiling",
                                    )

        area_represent = cap_AreaRepresent(show_link=True)

        configure(tablename,
                  context = {"location": "location.location_id",
                             },
                  #create_next = URL(f="area", args=["[id]", "location"]),
                  crud_form = crud_form,
                  deduplicate = self.cap_area_duplicate,
                  mark_required = ("event_type_id",),
                  onaccept = self.cap_area_onaccept,
                  onvalidation = self.cap_area_onvalidation,
                  )

        # Components
        add_components(tablename,
                       cap_area_location = {"name": "location",
                                            "joinby": "area_id",
                                            },
                       cap_area_tag = {"name": "tag",
                                       "joinby": "area_id",
                                       },
                       # Names
                       cap_area_name = {"name": "name",
                                        "joinby": "area_id",
                                        },
                       )

        area_id = S3ReusableField("area_id", "reference %s" % tablename,
                                  label = T("Area"),
                                  ondelete = "CASCADE",
                                  represent = area_represent,
                                  requires = IS_ONE_OF(db, "cap_area.id",
                                                       area_represent),
                                  )

        # ToDo: Use a widget tailored to entering <polygon> and <circle>.
        # Want to be able to enter them by drawing on the map.
        # Also want to allow selecting existing locations that have
        # geometry, maybe with some filtering so the list isn't cluttered
        # with irrelevant locations.
        tablename = "cap_area_location"
        define_table(tablename,
                     alert_id(readable = False,
                              writable = False,
                              ),
                     area_id(),
                     self.gis_location_id(
                        widget = S3LocationSelector(points = False,
                                                    polygons = True,
                                                    circles = True,
                                                    show_map = True,
                                                    catalog_layers = True,
                                                    show_address = False,
                                                    show_postcode = False,
                                                    ),
                        ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Location"),
            title_display = T("Alert Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            subtitle_list = T("List Locations"),
            label_list_button = T("List Locations"),
            label_delete_button = T("Delete Location"),
            msg_record_created = T("Location added"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location deleted"),
            msg_list_empty = T("No locations currently defined for this alert"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("area_id", "location_id")),
                  onaccept = self.cap_area_location_onaccept
                  )

        # ---------------------------------------------------------------------
        # Area Tags
        # - Key-Value extensions
        # - Used to hold for geocodes: key is the geocode system name, and
        #   value is the specific value for this area.
        # - Could store other values here as well, to avoid dedicated fields
        #   in cap_area for rarely-used items like altitude and ceiling, but
        #   would have to distinguish those from geocodes.
        #
        # ToDo: Provide a mechanism for pre-loading geocodes that are not tied
        # to individual areas.
        # ToDo: Allow sharing the key-value pairs. Cf. Ruby on Rails tagging
        # systems such as acts-as-taggable-on, which has a single table of tags
        # used by all classes. Each tag record has the class and field that the
        # tag belongs to, as well as the tag string. We'd want tag and value,
        # but the idea is the same: There would be a table with tag / value
        # pairs, and individual cap_area, event_event, org_whatever records
        # would link to records in the tag table. So we actually would not have
        # duplicate tag value records as we do now.

        tablename = "cap_area_tag"
        define_table(tablename,
                     alert_id(readable = False,
                              writable = False,
                              ),
                     area_id(),
                     # ToDo: Allow selecting from a dropdown list of pre-defined
                     # geocode system names.
                     Field("tag",
                           label = T("Geocode Name"),
                           ),
                     # ToDo: Once the geocode system is selected, fetch a list
                     # of current values for that geocode system. Allow adding
                     # new values, e.g. with combo box menu.
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("area_id", "tag", "value")),
                  onaccept = self.cap_area_tag_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Acknowledgement Table for CAP Alert

        tablename = "cap_alert_ack"
        define_table(tablename,
                     alert_id(readable = False,
                              writable = False,
                              ),
                     # use-this when location intersect filter is supported
                     self.gis_location_id(readable = False,
                                          writable = False,
                                          ),
                     s3_datetime("acknowlegded_on",
                                 label = T("Acknowledged On"),
                                 default = "now",
                                 requires = IS_NOT_EMPTY(),
                                 ),
                     Field("acknowledged_by",
                           label = T("Acknowledged By"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Acknowledgement"),
            title_display = T("Alert Acknowledgement"),
            title_list = T("Alert Acknowledgements"),
            title_update = T("Edit Acknowledgement"),
            subtitle_list = T("List Alert Acknowledgements"),
            label_list_button = T("List Alert Acknowledgements"),
            label_delete_button = T("Delete Acknowledgement"),
            msg_record_created = T("Acknowledgement added"),
            msg_record_modified = T("Acknowledgement updated"),
            msg_record_deleted = T("Acknowledgement deleted"),
            msg_list_empty = T("No Acknowledgements currently received for this alert"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(cap_alert_id = alert_id,
                    cap_alert_represent = alert_represent,
                    cap_alert_approve = self.cap_alert_approve,
                    cap_area_id = area_id,
                    cap_area_represent = area_represent,
                    cap_info_represent = info_represent,
                    cap_info_category_opts = cap_options["cap_info_category_opts"],
                    cap_expiry_date = self.cap_expirydate,
                    cap_sender_name = self.cap_sendername,
                    cap_template_represent = self.cap_template_represent,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        alert_id = S3ReusableField("alert_id", "integer",
                                   readable = False,
                                   writable = False)

        return dict(cap_alert_id = alert_id)

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

        _time = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y.%m.%d")
        if r:
            next_id = int(r.id) + 1
        else:
            next_id = 1

        # Format: prefix:oid.time.alert_id
        settings = current.deployment_settings
        prefix = "urn:oid"
        oid = settings.get_cap_identifier_oid()
        # In Organization ID, the organization is identified with a 0
        # but the 0 should be changed to 1 when it is used in an alert message
        # OID is normally of the form 2.49.0.1.104.xx.(yy)
        oid_split = oid.split(".")
        if len(oid_split) >= 6 and oid_split[5] == str(0):
            oid_split[5] = str(1)
        oid = ".".join(oid_split)

        return "%s:%s.%s.%03d" % (prefix, oid, _time, next_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def generate_sender():
        """
            Generate a sender for a new form
        """
        try:
            user_email = current.auth.user.email
        except AttributeError:
            return ""

        return "%s" % user_email

    # -------------------------------------------------------------------------
    @staticmethod
    def generate_source():
        """
            Generate a source for CAP alert
        """
        return "%s@%s" % (current.xml.domain,
                          current.deployment_settings.get_base_public_url())

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_sendername():
        """
            Default Sender name for the alert
            Sendername is the name of the organisation if user is associated
            else None
        """

        db = current.db
        utable = db.auth_user
        otable = current.s3db.org_organisation
        query = (utable.id == current.auth.user.id) & \
                (utable.organisation_id == otable.id) & \
                (otable.deleted != True)
        row = db(query).select(otable.name,
                               limitby=(0, 1)).first()
        if row:
            return row.name
        return current.auth.user.username

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_template_represent(alert_id, row=None):
        """
            Represent an alert template concisely
        """

        if row:
            alert_id = row.id
        elif not alert_id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.cap_alert
            row = db(table.id == alert_id).select(table.is_template,
                                                  table.template_title,
                                                  limitby=(0, 1),
                                                  ).first()

        # @ToDo: Should get headline from "info"?
        if row.is_template:
            return row.template_title
        else:
            return current.s3db.cap_alert_represent(alert_id)

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
    def cap_alert_create_onaccept(form):
        """
            Auto-approve Templates
        """

        db = current.db
        form_vars = form.vars
        table = current.s3db.cap_alert
        if form_vars.get("is_template"):
            user = current.auth.user
            if user:
                db(table.id == form_vars.id).update(approved_by = user.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_alert_onvalidation(form):
        """
            Custom Form Validation:
                multi-field level
        """

        form_vars_get = form.vars.get
        if not form_vars_get("is_template"):
            # For non templates
            if not form_vars_get("scope"):
                form.errors["scope"] = \
                    current.T("'Scope' field is mandatory for actual alerts!")

            if form_vars_get("scope") == "Private":
                # Check if this comes from cap_alert
                # Can also come from rss import
                request = current.request
                if request.controller == "cap" and request.function == "alert":
                    # Internal alerts
                    if not form_vars_get("addresses"):
                        form.errors["addresses"] = \
                            current.T("'Recipients' field mandatory in case of 'Private' scope")

            if form_vars_get("scope") == "Restricted" and not form_vars_get("restriction"):
                form.errors["restriction"] = \
                    current.T("'Restriction' field mandatory in case of 'Restricted' scope")

            if form_vars_get("addresses") and not form_vars_get("scope"):
                form.errors["scope"] = \
                    current.T("'Scope' field mandatory in case using 'Recipients' field")

            if form_vars_get("status") == "Draft":
                form.errors["status"] = \
                    current.T("Cannot issue 'Draft' alerts!")

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_warning_priority_onvalidation(form):
        """
            Custom Form Validation
        """

        form_vars = form.vars
        table = current.s3db.cap_warning_priority
        query = (table.event_type_id == form_vars.event_type_id) & \
                (table.urgency == form_vars.urgency) & \
                (table.severity == form_vars.severity) & \
                (table.certainty == form_vars.certainty) & \
                (table.deleted != True)
        row = current.db(query).select(table.id, limitby=(0, 1)).first()
        if row:
            form.errors["event_type_id"] = \
current.T("This combination of the 'Event Type', 'Urgency', 'Certainty' and 'Severity' is already available in database.")

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_info_onaccept(form):
        """
            After DB I/O
        """

        if "vars" in form:
            form_vars = form.vars
        elif "id" in form:
            form_vars = form
        elif hasattr(form, "vars"):
            form_vars = form.vars
        else:
            form_vars = form

        info_id = form_vars.id
        if not info_id:
            return

        db = current.db
        itable = db.cap_info

        info = db(itable.id == info_id).select(itable.id,
                                               itable.alert_id,
                                               itable.language,
                                               itable.web,
                                               itable.event,
                                               itable.event_type_id,
                                               itable.event_code,
                                               itable.audience,
                                               limitby = (0, 1),
                                               ).first()
        if info:
            alert_id = info.alert_id

            # Details to update in this info-record:
            update = {}

            if alert_id and cap_alert_is_template(alert_id):
                update["is_template"] = True

            if not info.event:
                update["event"] = itable.event_type_id.represent(info.event_type_id)

            # For prepopulating
            event_code = info.event_code
            if event_code and ("|{" in event_code or "||" in event_code):
                update["event_code"] = json_formatter(event_code)

            # Unused:
            #parameter = info.parameter
            #if parameter and ("|{" in parameter or "||" in parameter):
            #    update["parameter"] = json_formatter(parameter)

            audience = info.audience
            if not audience or audience == current.messages["NONE"]:
                update["audience"] = None

            if info.language == "en":
                update["language"] = "en-US"

            if not info.web:
                # Use the local alert URL for "web"
                atable = current.s3db.cap_alert
                row = db(atable.id == alert_id).select(atable.scope,
                                                       limitby = (0, 1),
                                                       ).first()
                if row and row.scope == "Public":
                    fn = "public"
                else:
                    fn = "alert"
                web = "%s%s" % (current.deployment_settings.get_base_public_url(),
                                URL(c="cap", f=fn, args=[alert_id]),
                                )
                update["web"] = web
            else:
                web = None

            form_vars_get = form_vars.get

            # Defaults for relevance date fields
            form_effective = form_vars_get("effective", current.request.utcnow)
            form_expires = form_vars_get("expires", cap_expirydate())
            form_onset = form_vars_get("onset", form_effective)

            update.update({"effective": form_effective,
                           "expires": form_expires,
                           "onset": form_onset,
                           })

            if update:
                info.update_record(**update)

            # Sync data in all other info-records of the same alert
            idata = {"category"       : form_vars_get("category"),
                     "certainty"      : form_vars_get("certainty"),
                     "effective"      : form_effective,
                     "event_type_id"  : form_vars_get("event_type_id"),
                     "expires"        : form_expires,
                     "onset"          : form_onset,
                     "priority"       : form_vars_get("priority"),
                     "response_type"  : form_vars_get("response_type"),
                     "severity"       : form_vars_get("severity"),
                     "urgency"        : form_vars_get("urgency"),
                     }
            if web:
                idata["web"] = web
            query = (itable.alert_id == alert_id) & \
                    (itable.id != info_id) & \
                    (itable.deleted == False)
            db(query).update(**idata)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_info_onvalidation(form):
        """
            Custom Form Validation:
                used for import from CSV
        """

        T = current.T
        itable = current.db.cap_info
        irow = current.db((itable.alert_id == form.request_vars.alert_id) & \
                          (itable.id != form.request_vars.id)).\
                                                select(itable.language,
                                                       limitby=(0, 1)).first()
        # Check if both info segments are for same language
        if irow and irow.language == form.vars.language:
            form.errors["language"] = \
               T("Please edit already created info segment with same language!")

        form_record = form.record
        if form_record and form_record.is_template == False:
            form_vars = form.vars
            #parameters = json.loads(form_vars.get("parameter"))
            #if parameters:
            #    for parameter in parameters:
            #        if (parameter["key"] and not parameter["value"]) or \
            #           (parameter["value"] and not parameter["key"]):
            #            form.errors["parameter"] = \
            #                current.T("Name-Value Pair is incomplete.")

            if not form_vars.get("urgency"):
                form.errors["urgency"] = T("'Urgency' field is mandatory")
            if not form_vars.get("severity"):
                form.errors["severity"] = T("'Severity' field is mandatory")
            if not form_vars.get("certainty"):
                form.errors["certainty"] = T("'Certainty' field is mandatory")

            if not form_vars.get("category"):
                form.errors["category"] = T("At least one category is required.")

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_alert_approve(record=None):
        """
            Update the approved_on field when alert gets approved
        """

        if not record:
            return

        alert_id = record["id"]

        # Update approved_on at the time the alert is approved
        # @ToDo: update approved_on when approval is not required
        # i.e. we allow editors to be self approver
        if alert_id:
            db = current.db
            table = db.cap_alert
            query = table.id == alert_id
            utcnow = current.request.utcnow
            db(query).update(approved_on=utcnow, sent=utcnow)

            # Notify the owner of the record about approval
            row = db(query).select(table.owned_by_user,
                                   limitby=(0, 1)).first()
            if row.owned_by_user:
                settings = current.deployment_settings
                pe_id = current.auth.s3_user_pe_id(int(row.owned_by_user))
                subject = "%s: Alert Approved" % settings.get_system_name_short()
                url = "%s%s" % (settings.get_base_public_url(),
                                URL(c="cap", f="alert", args=[alert_id]))
                message = current.T("This alert that you requested to review has been approved:\n\n%s") % url
                current.msg.send_by_pe_id(pe_id,
                                          subject,
                                          message,
                                          alert_id=alert_id,
                                          )

            # Record the approved alert in history table without external references
            clone(current.request, record)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_info_duplicate(item):

        data = item.data
        alert_id = data.get("alert_id")
        # Default Info Language
        language = data.get("language", "en-US")

        if alert_id and language:
            table = item.table
            query = (table.alert_id == alert_id) & (table.language == language)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_info_parameter_onaccept(form):
        """
            Link alert_id to cap_info_parameter table
        """

        form_vars = form.vars
        info_id = form_vars.get("info_id", None)
        if not info_id:
            return

        db = current.db
        itable = db.cap_info

        irow = db(itable.id == info_id).select(itable.alert_id,
                                               limitby=(0, 1)).first()
        alert_id = irow.alert_id
        if alert_id:
            db(db.cap_info_parameter.id == form_vars["id"]).update(alert_id = alert_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_info_parameter_onvalidation(form):
        """
            Custom Form Validation
        """

        form_vars = form.vars
        parameter_name = form_vars.get("name")
        parameter_value = form_vars.get("value")
        if (parameter_name and not parameter_value) or \
           (parameter_value and not parameter_name):
            form.errors["name"] = current.T("Name-Value Pair is incomplete.")

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_area_duplicate(item):

        data = item.data
        name = data.get("name")

        if name is not None:
            table = item.table
            event_type_id = data.get("event_type_id", None)
            if event_type_id is not None:
                # This is a template
                query = (table.name == name) & \
                        (table.event_type_id == event_type_id)
            else:
                alert_id = data.get("alert_id", None)
                info_id = data.get("info_id", None)
                query_ = (table.name == name)
                if alert_id is not None:
                    # Real Alert, not template
                    query = query_ & (table.alert_id == alert_id)
                elif info_id is not None:
                    # CAP XML Import
                    query = query_ & (table.info_id == info_id)
                else:
                    # Nothing we can use
                    return

                duplicate = current.db(query).select(table.id,
                                                     limitby=(0, 1)).first()
                if duplicate:
                    item.id = duplicate.id
                    item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_area_onaccept(form):
        """
            Link alert_id for CAP XML import
        """

        form_vars = form.vars

        if form_vars.get("event_type_id"):
            # Predefined Area
            return

        db = current.db
        alert_id = form_vars.get("alert_id", None)
        if not alert_id:
            info_id = form_vars.get("info_id", None)
            if info_id:
                # CAP XML
                # Add the alert_id to this component of component
                # to make it a direct component for UI purposes
                itable = db.cap_info
                item = db(itable.id == info_id).select(itable.alert_id,
                                                       limitby=(0, 1)).first()
                alert_id = item.alert_id or None

        if alert_id:
            db(db.cap_area.id == form_vars.id).update(alert_id = alert_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_area_onvalidation(form):

        form_vars = form.vars
        if form_vars.get("ceiling") and not form_vars.get("altitude"):
            form.errors["altitude"] = \
                current.T("'Altitude' field is mandatory if using 'Ceiling' field.")

        if "event_type_id" in form_vars and form_vars.get("event_type_id") is None:
            form.errors["event_type_id"] = \
                current.T("'Event Type' field is mandatory for Predefined Area.")

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_area_location_onaccept(form):
        """
            - Link alert_id for non-template area
            - for external alerts (from import feed or rss), make sure the
              locations are only imported if we set polygons to be imported
        """

        form_vars = form.vars

        area_id = form_vars.get("area_id", None)
        if not area_id:
            # comes from assign method
            return

        db = current.db
        alert_id = form_vars.get("alert_id", None)
        if not alert_id:
            atable = db.cap_area
            row = db(atable.id == area_id).select(atable.alert_id,
                                                  limitby=(0, 1)).first()
            alert_id = row.alert_id or None
        if alert_id:
            # This is not template area
            # NB Template area are not linked with alert_id
            location_default = current.deployment_settings.get_cap_area_default()
            if "polygon" not in location_default:
                # Use-case for PH
                table = current.s3db.cap_alert
                row = db(table.id == alert_id).select(table.external,
                                                      limitby=(0, 1)).first()
                if row.external:
                    # If "polygon" is not in deployment_settings (eg. in PH) and
                    # if it is a external alert (coming from RSS and import_feed),
                    # don't use this for displaying map in area
                    db(db.cap_area_location.id == form_vars["id"]).delete()
                    return
            # For alerts generated from SAMBRO, link area to the alert_id
            db(db.cap_area_location.id == form_vars["id"]).update(alert_id = alert_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_area_tag_onaccept(form):
        """
            Link location if area_tag has SAME code
            Link alert_id for non-template area
        """

        form_vars = form.vars

        area_id = form_vars.get("area_id", None)
        if not area_id:
            # comes from assign method
            return

        db = current.db
        atable = db.cap_area

        arow = db(atable.id == area_id).select(atable.alert_id,
                                               limitby=(0, 1)).first()
        alert_id = arow.alert_id

        if alert_id:
            # This is not template area
            db(db.cap_area_tag.id == form_vars.id).update(alert_id = alert_id)

            s3db = current.s3db
            tag = form_vars.get("tag")
            same_code = current.deployment_settings.get_cap_same_code()
            import_location = False
            if tag and same_code:
                # Check if tag and same_code exist. If neither one or none
                # exists, do not import location
                if tag == "SAME":
                    # If tag is "SAME" then check other conditions, otherwise
                    # do not import location
                    if "geocode" in current.deployment_settings.get_cap_area_default():
                        import_location = True
                    else:
                        # Check internal alert
                        table = s3db.cap_alert
                        row = db(table.id == alert_id).select(table.external,
                                                              limitby=(0, 1)).first()
                        if not row.external:
                            import_location = True

            if import_location:
                # SAME tag refers to some location_id in CAP
                ttable = s3db.gis_location_tag
                gtable = s3db.gis_location

                # It is possible for there to be two polygons for the same SAME
                # code since polygon change over time, even if the code remains
                # the same. Hence the historic polygon is excluded as (gtable.end_date == None)
                tquery = (ttable.tag == same_code) & \
                         (ttable.value == form_vars.get("value")) & \
                         (ttable.deleted != True) & \
                         (ttable.location_id == gtable.id) & \
                         (gtable.end_date == None) & \
                         (gtable.deleted != True)
                trow = db(tquery).select(ttable.location_id, limitby=(0, 1)).first()
                if trow and trow.location_id:
                    # Match
                    ltable = db.cap_area_location
                    ldata = {"area_id": area_id,
                             "alert_id": alert_id or None,
                             "location_id": trow.location_id,
                             }
                    lid = ltable.insert(**ldata)
                    current.auth.s3_set_record_owner(ltable, lid)
                    # Uncomment this when required
                    #ldata["id"] = lid
                    #s3db.onaccept(ltable, ldata)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_resource_onaccept(form):
        """
            Link alert_id for CAP XML import
        """

        form_vars = form.vars

        info_id = form_vars.get("info_id", None)
        if info_id:
            # CAP XML
            # Add the alert_id to this component of component
            # to make it a direct component for UI purposes
            db = current.db
            itable = db.cap_info
            item = db(itable.id == info_id).select(itable.alert_id,
                                                   limitby=(0, 1)).first()
            alert_id = item.alert_id

            if alert_id:
                db(db.cap_resource.id == form_vars.id).update(alert_id = alert_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_resource_onvalidation(form):
        """
            For Image Upload
             NB not using document_onvalidation here because we are extracting
             other values from the file like size and mime type
        """

        form_vars = form.vars
        image = form_vars.image
        if image is None:
            encoded_file = form_vars.get("imagecrop-data", None)
            if encoded_file:
                import base64
                import uuid
                import cStringIO
                metadata, encoded_file = encoded_file.split(",")
                #filename, datatype, enctype = metadata.split(";")
                filename, datatype = metadata.split(";")[:2]
                f = Storage()
                f.filename = uuid.uuid4().hex + filename
                f.file = cStringIO.StringIO(base64.decodestring(encoded_file))
                form_vars.image = image = f
                stream = image.file
                stream.seek(0, os.SEEK_END)
                file_size = stream.tell()
                stream.seek(0)

                # extract mime_type
                if image is not None:
                    #data, mime_type = datatype.split(":")
                    form_vars.size = file_size
                    form_vars.mime_type = datatype.split(":")[1]

        elif isinstance(image, str):
            # Image = String => Update not a create, so file not in form
            return

    # -------------------------------------------------------------------------
    @staticmethod
    def cap_warning_priority_onaccept(form):

        form_vars = form.vars
        color_code = form_vars.color_code
        if color_code:
            db = current.db
            s3db = current.s3db
            stable = s3db.gis_style
            ftable = s3db.gis_layer_feature
            query = (ftable.controller == "cap") & \
                    (ftable.layer_id == stable.layer_id)
            rows = db(query).select(stable.id, stable.style)
            if rows:
                name = form_vars.name
                for row in rows:
                    style = row.style
                    if style:
                        sdata = dict(prop = "priority",
                                     fill = color_code,
                                     fillOpacity = 0.4,
                                     cat = name,
                                     )
                        if sdata not in style:
                            style.append(sdata)
                            db(stable.id == row.id).update(style = style)

# =============================================================================
def cap_expirydate():
    """
        Default Expiry date based on the expire offset
    """

    return current.request.utcnow + \
           datetime.timedelta(days = current.deployment_settings.\
                              get_cap_expire_offset())

# =============================================================================
def warning_priority_color(color_code):
    """
        Shows actual color for hex color code

        @param color_code: hex color code
    """

    if not color_code:
        return current.messages["NONE"]

    return DIV(_style="width:%(size)s;height:%(size)s;background-color:#%(color)s;" % \
               dict(size="2em", color=color_code))

# =============================================================================
class S3CAPHistoryModel(S3Model):

    names = ("cap_alert_history",
             "cap_info_history",
             "cap_info_parameter_history",
             "cap_resource_history",
             "cap_area_history",
             "cap_area_location_history",
             "cap_area_tag_history",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        cap_options = get_cap_options()
        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        #UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Alert History Table
        # Stores Copy of approved alerts without any external references

        tablename = "cap_alert_history"
        define_table(tablename,
                     Field("event_type",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("identifier", unique=True, length=255,
                           label = T("Identifier"),
                           requires = [IS_LENGTH(255),
                                       IS_MATCH(OIDPATTERN,
                                                error_message=T("Cannot be empty and Must not include spaces, commas, or restricted characters (< and &)."),
                                                ),
                                       ],
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A unique identifier of the alert message"),
                                                           T("A number or string uniquely identifying this message, assigned by the sender. Must not include spaces, commas or restricted characters (< and &)."))),
                           ),
                     Field("incidents", "list:string",
                           label = T("Incidents"),
                           represent = S3Represent(options = cap_options["cap_incident_type_opts"],
                                                   multiple = True),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_incident_type_opts"],
                                                  multiple = True,
                                                  sort = True,
                                                  )),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A list of incident(s) referenced by the alert message"),
                                                           T("Used to collate multiple messages referring to different aspects of the same incident. If multiple incident identifiers are referenced, they SHALL be separated by whitespace.  Incident names including whitespace SHALL be surrounded by double-quotes."))),
                           ),
                     Field("sender",
                           label = T("Sender"),
                           requires = IS_MATCH(OIDPATTERN,
                                               error_message=T("Cannot be empty and Must not include spaces, commas, or restricted characters (< and &).")),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the sender of the alert message"),
                                                           T("This is guaranteed by assigner to be unique globally; e.g., may be based on an Internet domain name. Must not include spaces, commas or restricted characters (< and &)."))),
                           ),
                     s3_datetime("sent"),
                     Field("status",
                           label = T("Status"),
                           represent = S3Represent(options = cap_options["cap_alert_status_code_opts"],
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_alert_status_code_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the appropriate handling of the alert message"),
                                                           T("See options."))),
                           ),
                     Field("msg_type",
                           label = T("Message Type"),
                           represent = S3Represent(options = cap_options["cap_alert_msg_type_code_opts"],
                                                   ),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_alert_msg_type_code_opts"])
                                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The nature of the alert message"),
                                                           T("See options."))),
                           ),
                     Field("source",
                           label = T("Source"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text identifying the source of the alert message"),
                                                           T("The particular source of this alert; e.g., an operator or a specific device."))),
                           ),
                     Field("scope",
                           label = T("Scope"),
                           represent = S3Represent(options = cap_options["cap_alert_scope_code_opts"],
                                                   ),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_options["cap_alert_scope_code_opts"])
                                        ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the intended distribution of the alert message"),
                                                           T("Who is this alert for?"))),
                           ),
                     Field("restriction", "text",
                           label = T("Restriction"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text describing the rule for limiting distribution of the restricted alert message"),
                                                           T("Used when scope is 'Restricted'."))),
                           ),
                     Field("addresses", "list:string",
                           label = T("Recipients"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(get_cap_alert_addresses_opts(),
                                                  multiple = True,
                                                  sort = True,
                                                  )
                                        ),
                           represent = S3Represent(lookup = "pr_group",
                                                   fields = ["name"],
                                                   multiple = True,
                                                   ),
                           widget = S3MultiSelectWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The group listing of intended recipients of the alert message"),
                                                           T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address."))),
                           ),
                     Field("codes", "list:string",
                           label = T("Codes"),
                           represent = self.list_string_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Codes for special handling of the message"),
                                                           T("Any user-defined flags or special codes used to flag the alert message for special handling."))),
                           ),
                     Field("note", "text",
                           label = T("Note"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text describing the purpose or significance of the alert message"),
                                                           T("The message note is primarily intended for use with status 'Exercise' and message type 'Error'"))),
                           ),
                     Field("reference", "text",
                           label = T("Reference"),
                           readable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The group listing identifying earlier message(s) referenced by the alert message"),
                                                           T("The extended message identifier(s) (in the form sender,identifier,sent) of an earlier CAP message or messages referenced by this one."))),
                           ),
                     s3_datetime("approved_on",
                                 readable = False,
                                 ),
                     *s3_meta_fields())

        list_fields = [(T("Event Type"), "info_history.event"),
                       "msg_type",
                       (T("Sent"), "sent"),
                       "info_history.headline",
                       "info_history.sender_name",
                       "created_by",
                       "approved_by",
                       (T("Approved On"), "approved_on"),
                       ]

        filter_widgets = [
            S3TextFilter(["identifier",
                          "sender",
                          "incidents",
                          "cap_info_history.headline",
                          "cap_info_history.event",
                          ],
                         label = T("Search"),
                         comment = T("Search for an Alert by sender, incident, headline or event."),
                         ),
            S3OptionsFilter("info_history.category",
                            label = T("Category"),
                            options = cap_options["cap_info_category_opts"],
                            hidden = True,
                            ),
            S3OptionsFilter("info_history.event",
                            hidden = True,
                            ),
            S3OptionsFilter("scope",
                            hidden = True,
                            ),
            S3OptionsFilter("info_history.priority",
                            hidden = True,
                            ),
            S3OptionsFilter("info_history.language",
                            label = T("Language"),
                            hidden = True,
                            ),
            ]

        configure(tablename,
                  deletable = False,
                  editable = False,
                  filter_widgets = filter_widgets,
                  insertable = False,
                  list_fields = list_fields,
                  orderby = "cap_info_history.expires desc",
                  )

        # Components
        add_components(tablename,
                       cap_area_history = "alert_history_id",
                       cap_area_location_history = {"name": "location_history",
                                                    "joinby": "alert_history_id",
                                                    },
                       cap_area_tag_history = {"name": "tag_history",
                                               "joinby": "alert_history_id",
                                               },
                       cap_info_history = "alert_history_id",
                       cap_info_parameter_history = "alert_history_id",
                       cap_resource_history = "alert_history_id",
                       )

        crud_strings[tablename] = Storage(
            title_display = T("Alert History Details"),
            title_list = T("Alerts History"),
            label_list_button = T("List Alerts History"),
            msg_list_empty = T("No alerts to show"))

        alert_history_represent = S3Represent(lookup = tablename,
                                              fields = ["msg_type", "sent", "sender"],
                                              field_sep = " - ")

        alert_history_id = S3ReusableField("alert_history_id", "reference %s" % tablename,
                                   comment = T("The alert message containing this information"),
                                   label = T("Alert History"),
                                   ondelete = "CASCADE",
                                   represent = alert_history_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_alert_history.id",
                                                          alert_history_represent)),
                                   )

        # ---------------------------------------------------------------------
        # CAP Info History Table
        settings.L10n.extra_codes = [("en-US", "English"),
                                     ]
        tablename = "cap_info_history"
        define_table(tablename,
                     alert_history_id(readable = False,
                                      writable = False,
                                      ),
                     s3_language(empty = False,
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Denotes the language of the information"),
                                                                 T("Code Values: Natural language identifier per [RFC 3066]. If not present, an implicit default value of 'en-US' will be assumed. Edit settings.cap.languages in 000_config.py to add more languages. See <a href=\"%s\">here</a> for a full list.") % "http://www.i18nguy.com/unicode/language-identifiers.html")),
                                 ),
                     Field("category", "list:string",
                           label = T("Category"),
                           represent = S3Represent(options = cap_options["cap_info_category_opts"],
                                                   multiple = True,
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_category_opts"],
                                                multiple = True,
                                                ),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the category of the subject event of the alert message"),
                                                           T("You may select multiple categories by holding down control and then selecting the items."))),
                           ),
                     Field("event",
                           label = T("Event"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text denoting the type of the subject event of the alert message"),
                                                           T("If not specified, will the same as the Event Type."))),
                           ),
                     Field("response_type", "list:string",
                           label = T("Response Type"),
                           represent = S3Represent(options = cap_options["cap_info_response_type_opts"],
                                                   multiple = True,
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_response_type_opts"],
                                                multiple = True),
                           widget = S3MultiSelectWidget(selectedList = 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the type of action recommended for the target audience"),
                                                           T("Multiple response types can be selected by holding down control and then selecting the items"))),
                           ),
                     Field("priority",
                           label = T("Priority"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Priority of the alert message"),
                                                           T("Defines the priority of the alert message. Selection of the priority automatically sets the value for 'Urgency', 'Severity' and 'Certainty'"))),
                           ),
                     Field("urgency",
                           label = T("Urgency"),
                           represent = S3Represent(options = cap_options["cap_info_urgency_opts"],
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_urgency_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the urgency of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Immediate' - Responsive action should be taken immediately" +
                                                             "'Expected' - Responsive action should be taken soon (within next hour)" +
                                                             "'Future' - Responsive action should be taken in the near future" +
                                                             "'Past' - Responsive action is no longer required" +
                                                             "'Unknown' - Urgency not known"))),
                           ),
                     Field("severity",
                           label = T("Severity"),
                           represent = S3Represent(options = cap_options["cap_info_severity_opts"],
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_severity_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the severity of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Extreme' - Extraordinary threat to life or property" +
                                                             "'Severe' - Significant threat to life or property" +
                                                             "'Moderate' - Possible threat to life or property" +
                                                             "'Minor' - Minimal to no known threat to life or property" +
                                                             "'Unknown' - Severity unknown"))),
                           ),
                     Field("certainty",
                           label = T("Certainty"),
                           represent = S3Represent(options = cap_options["cap_info_certainty_opts"],
                                                   ),
                           requires = IS_IN_SET(cap_options["cap_info_certainty_opts"]),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Denotes the certainty of the subject event of the alert message"),
                                                           T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                                                             "'Observed' - Determined to have occurred or to be ongoing" +
                                                             "'Likely' - Likely (p > ~50%)" +
                                                             "'Possible' - Possible but not likely (p <= ~50%)" +
                                                             "'Unlikely' - Not expected to occur (p ~ 0)" +
                                                             "'Unknown' - Certainty unknown"))),
                           ),
                     Field("audience", "text",
                           label = T("Audience"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Audience"),
                                                           T("The intended audience of the alert message"))),
                           ),
                     Field("event_code", "text",
                           label = T("Event Code"),
                           represent = S3KeyValueWidget.represent,
                           widget = S3KeyValueWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A system-specific code identifying the event type of the alert message"),
                                                           T("Any system-specific code for events, in the form of key-value pairs. (e.g., SAME, FIPS, ZIP)."))),
                           ),
                     s3_datetime("effective",
                                 label = T("Effective"),
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("The effective time of the information of the alert message"),
                                                                 T("If not specified, the effective time shall be assumed to be the same the time the alert was sent."))),
                                 ),
                     s3_datetime("onset",
                                 label = T("Onset"),
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Onset"),
                                                                 T("The expected time of the beginning of the subject event of the alert message"))),
                                 ),
                     s3_datetime("expires",
                                 label = T("Expires at"),
                                 #past = 0,
                                 comment = DIV(_class="tooltip",
                                               _title="%s|%s" % (T("The expiry time of the information of the alert message"),
                                                                 T("If this item is not provided, each recipient is free to enforce its own policy as to when the message is no longer in effect."))),
                                 ),
                     Field("sender_name",
                           label = T("Sender's name"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text naming the originator of the alert message"),
                                                           T("The human-readable name of the agency or authority issuing this alert."))),
                           ),
                     Field("headline",
                           label = T("Headline"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The text headline of the alert message"),
                                                           T("A brief human-readable headline.  Note that some displays (for example, short messaging service devices) may only present this headline; it should be made as direct and actionable as possible while remaining short.  160 characters may be a useful target limit for headline length."))),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The subject event of the alert message"),
                                                           T("An extended human readable description of the hazard or event that occasioned this message."))),
                           ),
                     Field("instruction", "text",
                           label = T("Instruction"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The recommended action to be taken by recipients of the alert message"),
                                                           T("An extended human readable instruction to targeted recipients.  If different instructions are intended for different recipients, they should be represented by use of multiple information blocks. You can use a different information block also to specify this information in a different language."))),
                           ),
                     Field("contact", "text",
                           label = T("Contact information"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Contact"),
                                                           T("The contact for follow-up and confirmation of the alert message"))),
                           ),
                     Field("web",
                           label = T("URL"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("A URL associating additional information with the alert message"),
                                                           T("A full, absolute URI for an HTML page or other text resource with additional or reference information regarding this alert."))),
                           ),
                     #Field("parameter", "text",
                     #      label = T("Parameters"),
                     #      represent = S3KeyValueWidget.represent,
                     #      widget = S3KeyValueWidget(key_label = T("Name")),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("A system-specific additional parameter associated with the alert message"),
                     #                                      T("Any system-specific datum, in the form of key-value pairs."))),
                     #      ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_display = T("Alert information History"),
            title_list = T("Information History entries"),
            subtitle_list = T("Listing of alert information History items"),
            label_list_button = T("List information History entries"),
            msg_list_empty = T("No alert information to show"))

        list_fields = ["language",
                       "category",
                       (T("Event Type"), "event"),
                       "response_type",
                       "priority",
                       "urgency",
                       "severity",
                       "certainty",
                       "sender_name",
                       ]

        info_history_represent = S3Represent(lookup = tablename,
                                             fields = ["language", "headline"],
                                             field_sep = " - ")

        info_history_id = S3ReusableField("info_history_id", "reference %s" % tablename,
                                          label = T("Information History Segment"),
                                          ondelete = "CASCADE",
                                          represent = info_history_represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "cap_info_history.id",
                                                                  info_history_represent)
                                                                 ),
                                          )

        crud_form = S3SQLCustomForm("alert_history_id",
                                    "language",
                                    "category",
                                    "event",
                                    "response_type",
                                    "priority",
                                    "urgency",
                                    "severity",
                                    "certainty",
                                    "audience",
                                    "event_code",
                                    "effective",
                                    "onset",
                                    "expires",
                                    "sender_name",
                                    "headline",
                                    "description",
                                    "instruction",
                                    "contact",
                                    "web",
                                    S3SQLInlineComponent("info_parameter_history",
                                                         name = "info_parameter_history",
                                                         label = T("Parameter"),
                                                         fields = ["name",
                                                                   "value",
                                                                   "mobile",
                                                                   ],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("A system-specific additional parameter associated with the alert message"),
                                                                                         T("Any system-specific datum, in the form of key-value pairs."))),
                                                         ),
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  list_fields = list_fields,
                  )

        # Components
        add_components(tablename,
                       cap_info_parameter_history = "info_history_id",
                       )

        # ---------------------------------------------------------------------
        # CAP Info Parameters History
        tablename = "cap_info_parameter_history"
        define_table(tablename,
                     alert_history_id(),
                     info_history_id(),
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     Field("mobile", "boolean",
                           default = False,
                           label = T("Mobile"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        # ---------------------------------------------------------------------
        # CAP Area segments history table
        tablename = "cap_area_history"
        define_table(tablename,
                     alert_history_id(readable = False,
                                      writable = False,
                                      ),
                     Field("name",
                           label = T("Area Description"),
                           required = True,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The affected area of the alert message"),
                                                           T("A text description of the affected area."))),
                           ),
                     Field("altitude", "integer",
                           label = T("Altitude"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The specific or minimum altitude of the affected area"),
                                                           T("If used with the ceiling element this value is the lower limit of a range. Otherwise, this value specifies a specific altitude. The altitude measure is in feet above mean sea level."))),
                           ),
                     Field("ceiling", "integer",
                           label = T("Ceiling"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The maximum altitude of the affected area"),
                                                           T("must not be used except in combination with the 'altitude' element. The ceiling measure is in feet above mean sea level."))),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_display = T("Alert Area History"),
            title_list = T("Areas History"),
            subtitle_list = T("List Areas History"),
            label_list_button = T("List Areas History"),
            msg_list_empty = T("No areas currently defined for this alert"))


        crud_form = S3SQLCustomForm("alert_history_id",
                                    "name",
                                    S3SQLInlineComponent("location_history",
                                                         name = "location",
                                                         multiple = False,
                                                         fields = [("", "location")],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("Geolocation"),
                                                                                         T("The paired values of points defining a polygon that delineates the affected area of the alert message"))),
                                                         ),
                                    S3SQLInlineComponent("tag_history",
                                                         name = "tag",
                                                         fields = ["tag",
                                                                   "value",
                                                                   ],
                                                         comment = DIV(_class="tooltip",
                                                                       _title="%s|%s" % (T("The geographic code delineating the affected area"),
                                                                                         T("Any geographically-based code to describe a message target area, in the form. The key is a user-assigned string designating the domain of the code, and the content of value is a string (which may represent a number) denoting the value itself (e.g., name='ZIP' and value='54321'). This should be used in concert with an equivalent description in the more universally understood polygon and circle forms whenever possible."))),
                                                         ),
                                    "altitude",
                                    "ceiling",
                                    )

        area_history_represent = cap_AreaRepresent(show_link=True)

        list_fields = ["name",
                       "altitude",
                       "ceiling",
                       ]
        configure(tablename,
                  crud_form = crud_form,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  list_fields = list_fields,
                  )

        # Components
        add_components(tablename,
                       cap_area_location_history = {"name": "location_history",
                                                    "joinby": "area_history_id",
                                                    },
                       cap_area_tag_history = {"name": "tag_history",
                                               "joinby": "area_history_id",
                                               },
                       )

        area_history_id = S3ReusableField("area_history_id", "reference %s" % tablename,
                                          label = T("Area"),
                                          ondelete = "CASCADE",
                                          represent = area_history_represent,
                                          requires = IS_ONE_OF(db, "cap_area_history.id",
                                                               area_history_represent),
                                          )

        # ---------------------------------------------------------------------
        # CAP Area Locations history table
        tablename = "cap_area_location_history"
        define_table(tablename,
                     alert_history_id(readable = False,
                                      writable = False,
                                      ),
                     area_history_id(),
                     Field("location_wkt", "text"),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_display = T("Alert Location History"),
            title_list = T("Locations History"),
            subtitle_list = T("List Locations History"),
            label_list_button = T("List Locations History"),
            msg_list_empty = T("No locations currently defined for this alert"))

        configure(tablename,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        # ---------------------------------------------------------------------
        # CAP Area Tags history table
        tablename = "cap_area_tag_history"
        define_table(tablename,
                     alert_history_id(readable = False,
                                      writable = False,
                                      ),
                     area_history_id(),
                     Field("tag",
                           label = T("Geocode Name"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  )

        # ---------------------------------------------------------------------
        # CAP Resource History segments
        tablename = "cap_resource_history"
        define_table(tablename,
                     alert_history_id(readable = False,
                                      writable = False,
                                      ),
                     Field("resource_desc",
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The type and content of the resource file"),
                                                           T("The human-readable text describing the type and content, such as 'map' or 'photo', of the resource file."))),
                           ),
                     Field("image", "upload",
                           label = T("Image"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = self.doc_image_represent,
                           requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                           error_message=\
T("Upload an image file(bmp, gif, jpeg or png), max. 800x800 pixels!"))),
                           uploadfolder = os.path.join(current.request.folder,
                                                       "uploads", "images"),
                           widget = S3ImageCropWidget((800, 800)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Image"),
                                                           T("Attach an image that provides extra information about the event"))),
                           ),
                     Field("mime_type",
                           requires = IS_NOT_EMPTY(),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the MIME content type and sub-type describing the resource file"),
                                                           T("MIME content type and sub-type as described in [RFC 2046]. (As of this document, the current IANA registered MIME types are listed at http://www.iana.org/assignments/media-types/)"))),
                           ),
                     Field("size", "integer",
                           label = T("Size in Bytes"),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The integer indicating the size of the resource file"),
                                                           T("Approximate size of the resource file in bytes."))),
                           ),
                     Field("uri",
                           label = T("Link to any resources"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The identifier of the hyperlink for the resource file"),
                                                           T("A full absolute URI, typically a Uniform Resource Locator that can be used to retrieve the resource over the Internet."))),
                           ),
                     Field("deref_uri", "text",
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Deref URI"),
                                                           T("The base-64 encoded data content of the resource file"))),
                           ),
                     Field("digest",
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("The code representing the digital digest ('hash') computed from the resource file"),
                                                           T("Calculated using the Secure Hash Algorithm (SHA-1)."))),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
                    title_display = T("Alert Resource History"),
                    title_list = T("Resources History"),
                    subtitle_list = T("List Resources History"),
                    label_list_button = T("List Resources History"),
                    msg_list_empty = T("No resources currently defined for this alert"))

        crud_form = S3SQLCustomForm("alert_history_id",
                                    "resource_desc",
                                    "uri",
                                    "image",
                                    "mime_type",
                                    "size",
                                    )

        list_fields = ["resource_desc",
                       "image",
                       ]

        configure(tablename,
                  crud_form = crud_form,
                  deletable = False,
                  editable = False,
                  insertable = False,
                  list_fields = list_fields,
                  )

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

# =============================================================================
class S3CAPAlertingAuthorityModel(S3Model):

    names = ("cap_alerting_authority",
             "cap_authority_feed_url",
             "cap_authority_forecast_url"
             )

    def model(self):

        T = current.T
        define_table = self.define_table
        messages = current.messages

        # ---------------------------------------------------------------------
        # The data model resembles the data extracted from here http://alerting.worldweather.org/
        #
        tablename = "cap_alerting_authority"
        define_table(tablename,
                     Field("oid", unique=True, length=255,
                           label = T("CAP OID"),
                           requires = [IS_LENGTH(255),
                                       IS_MATCH(OIDPATTERN,
                                                error_message=T("Cannot be empty and Must not include spaces, commas, or restricted characters (< and &).")),
                                       ],
                           ),
                     self.org_organisation_id(
                           requires = self.org_organisation_requires(
                                                required=True,
                                                ),
                           widget = None,
                           comment = S3PopupLink(c = "org",
                                                 f = "organisation",
                                                 label = T("Create Organization"),
                                                 title = messages.ORGANISATION,
                                                 ),
                          ),
                     Field("country", length=2,
                           label = T("Country"),
                           represent = self.gis_country_code_represent,
                           requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                                    lambda: current.gis.get_countries(key_type="code"),
                                                    zero=messages.SELECT_LOCATION)),
                           ),
                     Field("authorisation", "text",
                           label = T("Authorization Basis"),
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        self.crud_strings[tablename] = Storage(
                    label_create = T("Add Alerting Authority"),
                    title_display = T("Alerting Authority"),
                    title_list = T("Alerting Authorities"),
                    title_update = T("Edit Alerting Authority"),
                    subtitle_list = T("List Alerting Authorities"),
                    label_list_button = T("List Alerting Authorities"),
                    label_delete_button = T("Delete Alerting Authority"),
                    msg_record_created = T("Alerting Authority added"),
                    msg_record_modified = T("Alerting Authority updated"),
                    msg_record_deleted = T("Alerting Authority deleted"),
                    msg_list_empty = T("No Alerting Authority available"))

        list_fields = ["oid",
                       "organisation_id",
                       "country",
                       "feed_url.url",
                       "forecast_url.url",
                       ]

        alerting_authority_represent = S3Represent(lookup = tablename,
                                                   fields = ["organisation_id", "oid"],
                                                   field_sep = " - ")

        alerting_authority_id = S3ReusableField("alerting_authority_id", "reference %s" % tablename,
                                                label = T("CAP Alerting Authority"),
                                                ondelete = "CASCADE",
                                                represent = alerting_authority_represent,
                                                requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(current.db,
                                                              "cap_alerting_authority.id",
                                                              alerting_authority_represent)
                                                ))

        crud_form = S3SQLCustomForm("oid",
                                    "organisation_id",
                                    "country",
                                    "authorisation",
                                    S3SQLInlineComponent("feed_url",
                                                         name = "feed_url",
                                                         label = T("CAP Feed URL"),
                                                         fields = [("", "url")],
                                                         ),
                                    S3SQLInlineComponent("forecast_url",
                                                         name = "forecast_url",
                                                         label = T("Forecast URL"),
                                                         fields = [("", "url")],
                                                         )
                                    )

        self.configure(tablename,
                       crud_form = crud_form,
                       list_fields = list_fields,
                       )

        # Components
        self.add_components(tablename,
                            cap_authority_feed_url = {"name": "feed_url",
                                                      "joinby": "alerting_authority_id",
                                                      },
                            cap_authority_forecast_url = {"name": "forecast_url",
                                                          "joinby": "alerting_authority_id",
                                                          },
                            )

        # ---------------------------------------------------------------------
        # Feed URL for CAP Alerting Authority
        tablename = "cap_authority_feed_url"
        define_table(tablename,
                     alerting_authority_id(),
                     # @ToDo: Add username and pwd for url
                     Field("url",
                           label = T("CAP Feed URL"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Forecasts URL for CAP Alerting Authority
        tablename = "cap_authority_forecast_url"
        define_table(tablename,
                     alerting_authority_id(),
                     Field("url",
                           label = T("Forecast URL"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3CAPAreaNameModel(S3Model):
    """
        CAP Name Model:
            -local names for CAP Area
    """

    names = ("cap_area_name",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "cap_area_name"
        self.define_table(tablename,
                          self.cap_area_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          s3_language(empty = False,
                                      select = current.deployment_settings.get_cap_languages(),
                                      ),
                          Field("name_l10n",
                                label = T("Local Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary=("area_id", "language")),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3CAPMessageModel(S3Model):
    """
        Link Alert to Message
    """

    names = ("cap_alert_message",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Alert <> Messages link table
        #
        tablename = "cap_alert_message"
        self.define_table(tablename,
                          self.cap_alert_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          self.msg_message_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def json_formatter(fstring):
    """
        Properly format the Key-Value import string to json
    """

    if fstring == "||":
        fstring = "[]"
    else:
        fstring = fstring.replace(" ", "") # Remove space
        fstring = fstring.replace("|", "")
        fstring = fstring.replace("}{", "},{")
        fstring = fstring.replace("{u'", "{'")
        fstring = fstring.replace(":u'", ":'")
        fstring = fstring.replace(",u'", ",'")
        fstring = fstring.replace("'", '"')
        fstring = "[%s]" % fstring

    return fstring

# =============================================================================
def get_cap_alert_addresses_opts():
    """ Get the pr_group.id required for cap_alert.addresses field"""

    T = current.T
    gtable = current.s3db.pr_group
    rows = current.db(gtable.deleted != True).select(gtable.id,
                                                     gtable.name)
    return [(row.id, s3_str(T(row.name))) for row in rows]

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
def cap_rheader(r):
    """ Resource Header for CAP module """

    rheader = None
    if r.representation == "html":
        record = r.record
        if record:
            T = current.T
            db = current.db
            s3db = current.s3db
            tablename = r.tablename
            if tablename == "cap_alert":
                alert_id = record.id
                itable = s3db.cap_info
                row = db(itable.alert_id == alert_id).select(itable.id,
                                                             limitby=(0, 1)).first()
                if record.is_template:
                    if not row:
                        error = DIV(T("An alert needs to contain at least one info item."),
                                    _class="error")
                    else:
                        error = ""

                    # Copy button is not working as create?from_record only works
                    # with default form and not implemented for custom forms.
                    # cap_info uses a custom form
                    #if r.component_name == "info" and r.component_id:
                        # Display "Copy" Button to copy record from the opened info
                    #    copy_btn = A(T("Copy Info Segment"),
                    #                 _href = URL(f = "template",
                    #                             args = [r.id, "info", "create",],
                    #                             vars = {"from_record": r.component_id,
                    #                                     },
                    #                             ),
                    #                 _class = "action-btn"
                    #                 )
                    #else:
                    #    copy_btn = None

                    tabs = [(T("Alert Details"), None),
                            (T("Information"), "info"),
                            #(T("Area"), "area"),
                            (T("Resource Files"), "resource"),
                            ]

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    rheader = DIV(TABLE(TR(TH("%s: " % T("Template Title")),
                                           TD(A(s3db.cap_template_represent(alert_id, record),
                                                _href=URL(c="cap", f="template",
                                                          args=[alert_id, "update"]))),
                                           ),
                                        TR(TH("%s: " % T("Event Type")),
                                           TD(r.table.event_type_id.represent(record.event_type_id))
                                           ),
                                        ),
                                  rheader_tabs,
                                  error
                                  )
                    #if copy_btn is not None:
                    #    rheader.insert(1, TR(TD(copy_btn)))
                else:
                    action_btn = None
                    msg_type_buttons = None
                    if not row:
                        error = DIV(T("You need to create at least one alert information item in order to be able to broadcast this alert!"),
                                    _class="error")
                        #export_btn = ""
                    else:
                        error = ""
                        #export_btn = A(DIV(_class="export_cap_large"),
                        #               _href=URL(c="cap", f="alert", args=["%s.cap" % alert_id]),
                        #               _target="_blank",
                        #               )

                        has_permission = current.auth.s3_has_permission
                        # Display 'Submit for Approval', 'Publish Alert' or
                        # 'Review Alert' based on permission and deployment settings
                        if not current.request.get_vars.get("_next") and \
                           current.deployment_settings.get_cap_authorisation() and \
                           record.approved_by is None:
                            # Show these buttons only if there is atleast one area segment
                            area_table = s3db.cap_area
                            area_row = db(area_table.alert_id == alert_id).\
                                                select(area_table.id,
                                                       limitby=(0, 1)).first()
                            if area_row and has_permission("update", "cap_alert",
                                                           record_id=alert_id):
                                action_btn = A(T("Submit for Approval"),
                                               _href = URL(f = "notify_approver",
                                                           vars = {"cap_alert.id": alert_id,
                                                                   },
                                                           ),
                                               _class = "action-btn confirm-btn button tiny"
                                               )
                                current.response.s3.jquery_ready.append(
'''S3.confirmClick('.confirm-btn','%s')''' % T("Do you want to submit the alert for approval?"))

                                # For Alert Approver
                                if has_permission("approve", "cap_alert"):
                                    action_btn = A(T("Review Alert"),
                                                   _href = URL(args = [alert_id,
                                                                       "review"
                                                                       ],
                                                               ),
                                                   _class = "action-btn button tiny",
                                                   )

                        if record.approved_by is not None:
                            if has_permission("create", "cap_alert"):
                                relay_alert = A(T("Relay Alert"),
                                                _data = "%s/%s" % (record.msg_type, r.id),
                                                _class = "action-btn cap-clone-update button tiny",
                                                )
                                if record.external:
                                    msg_type_buttons = relay_alert
                                else:
                                    if record.created_by:
                                        utable = db.auth_user
                                        row = db(utable.id == record.created_by).select(\
                                                                utable.organisation_id,
                                                                limitby=(0, 1)).first()
                                        row_ = db(utable.id == current.auth.user.id).select(\
                                                                utable.organisation_id,
                                                                limitby=(0, 1)).first()
                                        if row.organisation_id == row_.organisation_id:
                                            # Same organisation
                                            msg_type = record.msg_type
                                            if msg_type == "Alert" or msg_type == "Update":
                                                msg_type_buttons = TAG[""](
                                                        TR(TD(A(T("Update Alert"),
                                                                _data = "Update/%s" % r.id,
                                                                _class = "action-btn cap-clone-update button tiny",
                                                                ))),
                                                        TR(TD(A(T("Cancel Alert"),
                                                                _data = "Cancel/%s" % r.id,
                                                                _class = "action-btn cap-clone-update button tiny",
                                                                ))),
                                                        TR(TD(A(T("Error Alert"),
                                                                _data = "Error/%s" % r.id,
                                                                _class = "action-btn cap-clone-update button tiny",
                                                                ))),
                                                        #TR(TD(A(T("All Clear"),
                                                        #        _data = "AllClear/%s" % r.id,
                                                        #        _class = "action-btn cap-clone-update button tiny",
                                                        #        ))),
                                                        )
                                            elif msg_type == "Error":
                                                msg_type_buttons = TAG[""](
                                                        TR(TD(A(T("Update Alert"),
                                                                _data = "Update/%s" % r.id,
                                                                _class = "action-btn cap-clone-update button tiny",
                                                                ))),
                                                        #TR(TD(A(T("All Clear"),
                                                        #        _data = "AllClear/%s" % r.id,
                                                        #        _class = "action-btn cap-clone-update button tiny",
                                                        #        ))),
                                                        )
                                            else:
                                                msg_type_buttons = None
                                        else:
                                            # Different organisation
                                            msg_type_buttons = relay_alert
                                    else:
                                        msg_type_buttons = relay_alert

                    tabs = [(T("Alert Details"), None),
                            (T("Information"), "info"),
                            (T("Area"), "area"),
                            (T("Resource Files"), "resource"),
                            ]

                    if r.representation == "html" and \
                       current.auth.s3_has_permission("update", "cap_alert",
                                                      record_id=alert_id) and \
                       r.record.approved_by is None:
                        # Show predefined areas tab if we have some defined for this event_type
                        row_ = db(itable.alert_id == alert_id).select(itable.event_type_id,
                                                                      limitby=(0, 1)).first()
                        if row_ is not None:
                            artable = s3db.cap_area
                            query = (artable.deleted != True) & \
                                    (artable.is_template == True) & \
                                    (artable.event_type_id == row_.event_type_id)
                            template_area_row = db(query).select(artable.id,
                                                                 limitby=(0, 1)).first()
                            if template_area_row:
                                tabs.insert(2, (T("Predefined Areas"), "assign"))

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                           TD(A("%s - %s" % (record.identifier, record.sender),
                                                _href=URL(c="cap", f="alert",
                                                          args=[alert_id, "update"]))),
                                           ),
                                        #TR(export_btn)
                                        ),
                                  rheader_tabs,
                                  error
                                  )

                    if action_btn:
                        rheader.insert(1, TR(TD(action_btn)))

                    if msg_type_buttons is not None:
                        rheader.insert(1, msg_type_buttons)

            elif tablename == "cap_area":
                # Used only for Area Templates
                tabs = [(T("Area"), None),
                        ]

                if current.deployment_settings.get_L10n_translate_cap_area():
                    tabs.insert(1, (T("Local Names"), "name"))

                rheader_tabs = s3_rheader_tabs(r, tabs)
                rheader = DIV(TABLE(TR(TH("%s: " % T("Area")),
                                       TD(A(s3db.cap_area_represent(record.id, record),
                                            _href=URL(c="cap", f="area",
                                                      args=[record.id, "update"]))),
                                       ),
                                    ),
                              rheader_tabs
                              )

            elif tablename == "cap_info":
                # Shouldn't ever be called
                tabs = [(T("Information"), None),
                        (T("Resource Files"), "resource"),
                        ]

                if cap_alert_is_template(record.alert_id):
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                    rheader = DIV(TABLE(TR(TH("%s: " % T("Template")),
                                           TD(A(s3db.cap_template_represent(record.alert_id),
                                                _href=URL(c="cap", f="template",
                                                          args=[record.alert_id, "update"]))),
                                            ),
                                        TR(TH("%s: " % T("Info template")),
                                           TD(A(s3db.cap_info_represent(record.id, record),
                                                _href=URL(c="cap", f="info",
                                                          args=[record.id, "update"]))),
                                           )
                                        ),
                                  rheader_tabs,
                                  _class="cap_info_template_form"
                                  )
                    current.response.s3.js_global.append('''i18n.cap_locked="%s"''' % T("Locked"))
                else:
                    tabs.insert(1, (T("Areas"), "area"))
                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                           TD(A(s3db.cap_alert_represent(record.alert_id),
                                                _href=URL(c="cap", f="alert",
                                                          args=[record.alert_id, "update"]))),
                                           ),
                                        TR(TH("%s: " % T("Information")),
                                           TD(A(s3db.cap_info_represent(record.id, record),
                                                _href=URL(c="cap", f="info",
                                                          args=[record.id, "update"]))),
                                           )
                                        ),
                                  rheader_tabs
                                  )

    return rheader

# =============================================================================
def cap_history_rheader(r):
    """ Resource Header for CAP history tables """

    rheader = None
    if r.representation == "html":
        record = r.record
        if record:
            T = current.T
            #db = current.db
            s3db = current.s3db
            if r.tablename == "cap_alert_history":
                alert_id = record.id
                #itable = s3db.cap_info_history
                #row = db(itable.alert_history_id == alert_id).select(itable.id,
                #                                                     limitby=(0, 1)).first()

                tabs = [(T("Alert Details"), None),
                        (T("Information"), "info_history"),
                        (T("Area"), "area_history"),
                        (T("Resource Files"), "resource_history"),
                        ]

                rheader_tabs = s3_rheader_tabs(r, tabs)

                rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                       TD(A(s3db.cap_alert_represent(alert_id, record),
                                            _href=URL(c="cap", f="alert",
                                                      args=[alert_id, "update"]))),
                                       )),
                              rheader_tabs
                              )

    return rheader

# =============================================================================
def cap_gis_location_xml_post_parse(element, record):
    """
        UNUSED - done in XSLT

        Convert CAP polygon representation to WKT; extract circle lat lon.
        Latitude and longitude in CAP are expressed as signed decimal values in
        coordinate pairs:
            latitude,longitude
        The circle text consists of:
            latitude,longitude radius
        where the radius is in km.
        Polygon text consists of a space separated sequence of at least 4
        coordinate pairs where the first and last are the same.
            lat1,lon1 lat2,lon2 lat3,lon3 ... lat1,lon1
    """

    # @ToDo: Extract altitude and ceiling from the enclosing <area>, and
    # compute an elevation value to apply to all enclosed gis_locations.

    cap_polygons = element.xpath("cap_polygon")
    if cap_polygons:
        cap_polygon_text = cap_polygons[0].text
        # CAP polygons and WKT have opposite separator conventions:
        # CAP has spaces between coordinate pairs and within pairs the
        # coordinates are separated by comma, and vice versa for WKT.
        # Unfortunately, CAP and WKT (as we use it) also have opposite
        # orders of lat and lon. CAP has lat lon, WKT has lon lat.
        # Both close the polygon by repeating the first point.
        cap_points_text = cap_polygon_text.split()
        cap_points = [cpoint.split(",") for cpoint in cap_points_text]
        # @ToDo: Should we try interpreting all the points as decimal numbers,
        # and failing validation if they're wrong?
        wkt_points = ["%s %s" % (cpoint[1], cpoint[0]) for cpoint in cap_points]
        wkt_polygon_text = "POLYGON ((%s))" % ", ".join(wkt_points)
        record.wkt = wkt_polygon_text
        return

    cap_circle_values = element.xpath("resource[@name='gis_location_tag']/data[@field='tag' and text()='cap_circle']/../data[@field='value']")
    if cap_circle_values:
        cap_circle_text = cap_circle_values[0].text
        coords, radius = cap_circle_text.split()
        lat, lon = coords.split(",")
        try:
            # If any of these fail to interpret as numbers, the circle was
            # badly formatted. For now, we don't try to fail validation,
            # but just don't set the lat, lon.
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
        except ValueError:
            return
        record.lat = lat
        record.lon = lon
        # Add a bounding box for the given radius, if it is not zero.
        if radius > 0.0:
            bbox = current.gis.get_bounds_from_radius(lat, lon, radius)
            record.lat_min = bbox["lat_min"]
            record.lon_min = bbox["lon_min"]
            record.lat_max = bbox["lat_max"]
            record.lon_max = bbox["lon_max"]

# =============================================================================
def cap_gis_location_xml_post_render(element, record):
    """
        UNUSED - done in XSLT

        Convert Eden WKT polygon (and eventually circle) representation to
        CAP format and provide them in the rendered s3xml.

        Not all internal formats have a parallel in CAP, but an effort is made
        to provide a resonable substitute:
        Polygons are supported.
        Circles that were read in from CAP (and thus carry the original CAP
            circle data) are supported.
        Multipolygons are currently rendered as their bounding box.
        Points are rendered as zero radius circles.

        Latitude and longitude in CAP are expressed as signed decimal values in
        coordinate pairs:
            latitude,longitude
        The circle text consists of:
            latitude,longitude radius
        where the radius is in km.
        Polygon text consists of a space separated sequence of at least 4
        coordinate pairs where the first and last are the same.
            lat1,lon1 lat2,lon2 lat3,lon3 ... lat1,lon1
    """

    # @ToDo: Can we rely on gis_feature_type == 3 to tell if the location is a
    # polygon, or is it better to look for POLYGON in the wkt? For now, check
    # both.
    # @ToDo: CAP does not support multipolygons.  Do we want to extract their
    # outer polygon if passed MULTIPOLYGON wkt? For now, these are exported
    # with their bounding box as the polygon.
    # @ToDo: What if a point (gis_feature_type == 1) that is not a CAP circle
    # has a non-point bounding box? Should it be rendered as a polygon for
    # the bounding box?

    try:
        from lxml import etree
    except ImportError:
        # This won't fail, since we're in the middle of processing xml.
        return

    SubElement = etree.SubElement

    s3xml = current.xml
    TAG = s3xml.TAG
    RESOURCE = TAG["resource"]
    DATA = TAG["data"]
    ATTRIBUTE = s3xml.ATTRIBUTE
    NAME = ATTRIBUTE["name"]
    FIELD = ATTRIBUTE["field"]
    #VALUE = ATTRIBUTE["value"]

    #loc_tablename = "gis_location"
    tag_tablename = "gis_location_tag"
    tag_fieldname = "tag"
    val_fieldname = "value"
    polygon_tag = "cap_polygon"
    circle_tag = "cap_circle"
    fallback_polygon_tag = "cap_polygon_fallback"
    fallback_circle_tag = "cap_circle_fallback"

    def __cap_gis_location_add_polygon(element, cap_polygon_text, fallback=False):
        """
            Helper for cap_gis_location_xml_post_render that adds the CAP polygon
            data to the current element in a gis_location_tag element.
        """
        # Make a gis_location_tag.
        tag_resource = SubElement(element, RESOURCE)
        tag_resource.set(NAME, tag_tablename)
        tag_field = SubElement(tag_resource, DATA)
        # Add tag and value children.
        tag_field.set(FIELD, tag_fieldname)
        if fallback:
            tag_field.text = fallback_polygon_tag
        else:
            tag_field.text = polygon_tag
        val_field = SubElement(tag_resource, DATA)
        val_field.set(FIELD, val_fieldname)
        val_field.text = cap_polygon_text

    def __cap_gis_location_add_circle(element, lat, lon, radius, fallback=False):
        """
            Helper for cap_gis_location_xml_post_render that adds CAP circle
            data to the current element in a gis_location_tag element.
        """
        # Make a gis_location_tag.
        tag_resource = SubElement(element, RESOURCE)
        tag_resource.set(NAME, tag_tablename)
        tag_field = SubElement(tag_resource, DATA)
        # Add tag and value children.
        tag_field.set(FIELD, tag_fieldname)
        if fallback:
            tag_field.text = fallback_circle_tag
        else:
            tag_field.text = circle_tag
        val_field = SubElement(tag_resource, DATA)
        val_field.set(FIELD, val_fieldname)
        # Construct a CAP circle string: latitude,longitude radius
        cap_circle_text = "%s,%s %s" % (lat, lon, radius)
        val_field.text = cap_circle_text

    # Sort out the geometry case by wkt, CAP tags, gis_feature_type, bounds,...
    # Check the two cases for CAP-specific locations first, as those will have
    # definite export values. For others, we'll attempt to produce either a
    # circle or polygon: Locations with a bounding box will get a box polygon,
    # points will get a zero-radius circle.

    # Currently wkt is stripped out of gis_location records right here:
    # https://github.com/flavour/eden/blob/master/modules/s3/s3resource.py#L1332
    # https://github.com/flavour/eden/blob/master/modules/s3/s3resource.py#L1426
    # https://github.com/flavour/eden/blob/master/modules/s3/s3resource.py#L3152
    # Until we provide a way to configure that choice, this will not work for
    # polygons.
    wkt = record.get("wkt", None)

    # WKT POLYGON: Although there is no WKT spec, according to every reference
    # that deals with nested polygons, the outer, enclosing, polygon must be
    # listed first. Hence, we extract only the first polygon, as CAP has no
    # provision for nesting.
    if wkt and wkt.startswith("POLYGON"):
        # ToDo: Is it sufficient to test for adjacent (( to find the start of
        # the polygon, or might there be whitespace between them?
        start = wkt.find("((")
        end = wkt.find(")")
        if start >=0 and end >=0:
            polygon_text = wkt[start + 2 : end]
            points_text = polygon_text.split(",")
            points = [p.split() for p in points_text]
            cap_points_text = ["%s,%s" % (point[1], point[0]) for point in points]
            cap_polygon_text = " ".join(cap_points_text)
            __cap_gis_location_add_polygon(element, cap_polygon_text)
            return
        # Fall through if the wkt string was mal-formed.

    # CAP circle stored in a gis_location_tag with tag = cap_circle.
    # If there is a cap_circle tag, we don't need to do anything further, as
    # export.xsl will use it. However, we don't know if there is a cap_circle
    # tag...
    #
    # @ToDo: The export calls xml_post_render after processing a resource's
    # fields, but before its components are added as children in the xml tree.
    # If this were delayed til after the components were added, we could look
    # there for the cap_circle gis_location_tag record. Since xml_post_parse
    # isn't in use yet (except for this), maybe we could look at moving it til
    # after the components?
    #
    # For now, with the xml_post_render before components: We could do a db
    # query to check for a real cap_circle tag record, and not bother with
    # creating fallbacks from bounding box or point...but we don't have to.
    # Instead, just go ahead and add the fallbacks under different tag names,
    # and let the export.xsl sort them out. This only wastes a little time
    # compared to a db query.

    # ToDo: MULTIPOLYGON -- Can stitch together the outer polygons in the
    # multipolygon, but would need to assure all were the same handedness.

    # The remaining cases are for locations that don't have either polygon wkt
    # or a cap_circle tag.

    # Bounding box: Make a four-vertex polygon from the bounding box.
    # This is a fallback, as if there is a circle tag, we'll use that.
    lon_min = record.get("lon_min", None)
    lon_max = record.get("lon_max", None)
    lat_min = record.get("lat_min", None)
    lat_max = record.get("lat_max", None)
    if lon_min and lon_max and lat_min and lat_max and \
       (lon_min != lon_max) and (lat_min != lat_max):
        # Although there is no WKT requirement, arrange the points in
        # counterclockwise order. Recall format is:
        # lat1,lon1 lat2,lon2 ... latN,lonN, lat1,lon1
        cap_polygon_text = \
            "%(lat_min)s,%(lon_min)s %(lat_min)s,%(lon_max)s %(lat_max)s,%(lon_max)s %(lat_max)s,%(lon_min)s %(lat_min)s,%(lon_min)s" \
            % {"lon_min": lon_min,
               "lon_max": lon_max,
               "lat_min": lat_min,
               "lat_max": lat_max}
        __cap_gis_location_add_polygon(element, cap_polygon_text, fallback=True)
        return

    # WKT POINT or location with lat, lon: This can be rendered as a
    # zero-radius circle.
    # Q: Do we put bounding boxes around POINT locations, and are they
    # meaningful?
    lat = record.get("lat", None)
    lon = record.get("lon", None)
    if not lat or not lon:
        # Look for POINT.
        if wkt and wkt.startswith("POINT"):
            start = wkt.find("(")
            end = wkt.find(")")
            if start >=0 and end >=0:
                point_text = wkt[start + 2 : end]
                point = point_text.split()
                try:
                    lon = float(point[0])
                    lat = float(point[1])
                except ValueError:
                    pass
    if lat and lon:
        # Add a (fallback) circle with zero radius.
        __cap_gis_location_add_circle(element, lat, lon, 0, True)
        return

    # ToDo: Other WKT.

    # Did not find anything to use. Presumably the area has a text description.
    return

# =============================================================================
def cap_alert_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for CAP Alerts on the Home page.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["cap_alert.id"]
    item_class = "thumbnail"

    T = current.T
    #raw = record._row
    # @ToDo: handle the case where we have multiple info segments &/or areas
    headline = record["cap_info.headline"]
    location = s3_str(record["cap_area.name"])
    priority = record["cap_info.priority"]
    status = record["cap_alert.status"]
    scope = record["cap_alert.scope"]
    event = record["cap_info.event_type_id"]
    msg_type = s3_str(record["cap_alert.msg_type"])

    if current.auth.s3_logged_in():
        _href = URL(c="cap", f="alert", args=[record_id, "profile"])
    else:
        _href = URL(c="cap", f="public", args=[record_id, "profile"])

    priority_row = None
    if priority and priority != "-":
        # Give the priority color to headline
        db = current.db
        wptable = db.cap_warning_priority
        priority_row = db(wptable.name == priority).select(wptable.color_code,
                                                           limitby=(0, 1)).first()

    more = A(T("Full Alert"),
             _href = _href,
             _target = "_blank",
             )

    if list_id == "map_popup":
        itable = current.s3db.cap_info
        # Map popup
        event = itable.event_type_id.represent(event)
        if priority is None:
            priority = ""
        else:
            priority = itable.priority.represent(priority)
        description = record["cap_info.description"]
        response_type = record["cap_info.response_type"]
        sender = record["cap_info.sender_name"]
        last = TAG[""](BR(),
                       description,
                       BR(),
                       ", ".join(response_type) if response_type is not None else None,
                       BR(),
                       sender,
                       BR(),
                       )

        details = "%s %s %s" % (priority, status, scope)

        headline_ = A(headline,
                      _href = _href,
                      _target = "_blank",
                      )

        if priority_row:
            headline_["_style"] = "color: #%s" % (priority_row.color_code)

        item = DIV(headline_,
                   BR(),
                   location,
                   BR(),
                   details,
                   BR(),
                   event,
                   last,
                   more,
                   _class=item_class,
                   _id=item_id,
                   )
    else:
        if priority == current.messages["NONE"]:
            priority = ""
        sender_name = record["cap_info.sender_name"]
        sent = record["cap_alert.sent"]

        headline = "%s" % (headline)

        sub_heading = "%s %s %s" % (priority, event, msg_type)

        sub_headline = A(sub_heading,
                         _href = _href,
                         _target = "_blank",
                         )

        if priority_row:
            sub_headline["_style"] = "color: #%s" % (priority_row.color_code)

        para = T("%(status)s alert for %(area_description)s.") \
                % dict(status=status, area_description=location)

        issuer = "%s: %s" % (T("Issued by"), sender_name)
        issue_date = "%s: %s" % (T("Issued on"), sent)

        item = DIV(headline,
                   BR(),
                   para,
                   BR(),
                   sub_headline,
                   BR(),
                   issuer,
                   BR(),
                   issue_date,
                   BR(),
                   more,
                   _class=item_class,
                   _id=item_id,
                   )

    return item

# =============================================================================
def add_area_from_template(area_id, alert_id):
    """
        Add an area from a Template along with its components Location and Tag
    """

    afieldnames = ("name",
                   "altitude",
                   "ceiling",
                  )
    lfieldnames = ("location_id",
                   )
    tfieldnames = ("tag",
                   "value",
                   "comments",
                   )

    db = current.db
    s3db = current.s3db
    set_record_owner = current.auth.s3_set_record_owner
    onaccept = s3db.onaccept
    atable = s3db.cap_area
    #itable = s3db.cap_info
    ltable = s3db.cap_area_location
    ttable = s3db.cap_area_tag

    # Create Area Record from Template
    atemplate = db(atable.id == area_id).select(*afieldnames,
                                                limitby=(0, 1)).first()

    # @ToDo set_record_owner, update_super and/or onaccept
    # Currently not required by SAMBRO template
    adata = {"is_template": False,
             "alert_id": alert_id,
             "template_area_id": area_id,
             }
    for field in afieldnames:
        adata[field] = atemplate[field]

    aid = atable.insert(**adata)
    set_record_owner(atable, aid)
    onaccept(atable, dict(id=aid))

    # Add Area Location Components of Template
    ltemplate = db(ltable.area_id == area_id).select(*lfieldnames)
    for lrow in ltemplate:
        ldata = {"area_id": aid,
                 "alert_id": alert_id,
                 }
        for field in lfieldnames:
            ldata[field] = lrow[field]
        lid = ltable.insert(**ldata)
        set_record_owner(ltable, lid)
        onaccept(ltable, dict(id=lid))

    # Add Area Tag Components of Template
    ttemplate = db(ttable.area_id == area_id).select(*tfieldnames)
    for trow in ttemplate:
        tdata = {"area_id": aid,
                 "alert_id": alert_id,
                 }
        for field in tfieldnames:
            tdata[field] = trow[field]
        ttable.insert(**tdata)

    return aid

# =============================================================================
class cap_ImportAlert(S3Method):
    """
        Simple interactive CAP-XML Alert importer
        - designed as REST method for the cap_alert resource
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        # Requires permission to create alerts
        authorised = current.auth.s3_has_permission("create", "cap_alert")
        if not authorised:
            r.unauthorised()

        if r.representation == "html":

            T = current.T
            response = current.response

            fields = [Field("url",
                            label=T("URL"),
                            requires=[IS_NOT_EMPTY(),
                                      IS_URL(mode="generic"),
                                      ],
                            comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("URL of the alert"),
                                                           T("The URL from which the alert should be imported!"))),
                            ),
                      Field("user",
                            label=T("Username"),
                            comment = DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Username"),
                                                            T("Optional username for HTTP Authentication."))),
                            ),
                      Field("password",
                            label=T("Password"),
                            widget = S3PasswordWidget(),
                            comment = DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Password"),
                                                            T("Optional password for HTTP Authentication."))),
                            ),
                      # TODO This is pointless:
                      #Field("ignore_errors", "boolean",
                      #      label=T("Ignore Errors?"),
                      #      represent = s3_yes_no_represent,
                      #      comment = DIV(_class="tooltip",
                      #                    _title="%s|%s" % (T("Ignore Errors"),
                      #                                      T("skip invalid record silently?"))),
                      #      ),
                      ]
            labels, required = s3_mark_required(fields)
            response.s3.has_required = required

            response.form_label_separator = ""
            form = SQLFORM.factory(formstyle = current.deployment_settings.get_ui_formstyle(),
                                   submit_button = T("Import"),
                                   labels = labels,
                                   separator = "",
                                   table_name = "import_alert", # Dummy table name
                                   _id = "importform",
                                   *fields
                                   )

            response.view = "create.html"
            output = {"title": T("Import from Feed URL"),
                      "form": form,
                      }

            if form.accepts(r.post_vars,
                            current.session,
                            formname = "import_form",
                            ):

                resource = r.resource
                error, msg = self.accept(resource, form)

                if error:
                    response.error = error
                else:
                    if msg:
                        response.confirmation = msg

                        # Get the ID of the newly created/updated cap_alert
                        if resource.import_created:
                            alert_id = resource.import_created[0]
                        elif resource.import_updated:
                            alert_id = resource.import_updated[0]
                        else:
                            alert_id = None

                        # Forward to a view of the alert
                        if alert_id:
                            self.next = URL(c="cap", f="alert", args=[alert_id])
                        else:
                            self.next = URL(c="cap", f="alert")
                    else:
                        response.warning = T("No CAP alerts found at URL")

            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def accept(self, resource, form):
        """
            Accept the import-form

            @param resource: the target import resource
            @param form: the FORM
            @returns: tuple (error, msg)
                      error - error message (if an error occured)
                      msg - confirmation message of the import
        """

        formvars_get = form.vars.get

        url = formvars_get("url")
        opener = self.opener(url,
                             username = formvars_get("user"),
                             password = formvars_get("password"),
                             )

        tree = version = error = None
        try:
            content = opener.open(url)
        except urllib2.HTTPError, e:
            # HTTP status
            error = "HTTP %s: %s" % (e.code, e.read())
        except urllib2.URLError, e:
            # URL Error (network error)
            error = "CAP source unavailable (%s)" % e.reason
        except Exception:
            # Other error (local error)
            import sys
            error = sys.exc_info()[1]
        else:
            # Try parse
            tree, version, error = self.parse_cap(content)

        if tree:
            error, msg = self.import_cap(tree,
                                         version = version,
                                         resource = resource,
                                         url = url,
                                         # TODO Pointless:
                                         #ignore_errors = formvars_get("ignore_errors", False),
                                         )
        else:
            msg = None

        return error, msg

    # -------------------------------------------------------------------------
    @staticmethod
    def import_cap(tree, version=None, resource=None, url=None, ignore_errors=False):
        """
            Import a CAP-XML element tree into a cap_alert resource

            @param tree: the ElementTree
            @param version: the detected CAP version (see parse_cap)
            @param resource: the cap_alert resource to import to,
                             will be instantiated if not passed in
            @param url: the CAP-XML source URL
            @param ignore_errors: skip invalid cap_alert records

            TODO ignore_errors gives no benefit because it means to
                 skip invalid master records, but a CAP-XML source
                 can only contain one master record anyway - so the
                 outcome would be the same
        """

        msg = None
        s3db = current.s3db

        # Version-specific import transformation stylesheet?
        if version == "cap11":
            filename = "import11.xsl"
        else:
            # Default CAP-1.2
            filename = "import.xsl"
        stylesheet = os.path.join(current.request.folder,
                                  "static", "formats", "cap", filename,
                                  )

        # Set default for cap_info.web
        itable = s3db.table("cap_info")
        field = itable.web
        field.default = url or None

        # Import the CAP-XML
        if resource is None:
            resource = s3db.resource("cap_alert")
        try:
            resource.import_xml(tree,
                                stylesheet = stylesheet,
                                ignore_errors = ignore_errors,
                                )
        except (IOError, SyntaxError):
            import sys
            error = "CAP import error: %s" % sys.exc_info()[1]
        else:
            if resource.error:
                # Import validation error
                errors = current.xml.collect_errors(resource.error_tree)
                error = "%s\n%s" % (resource.error, "\n".join(errors))
            else:
                error = None

            if resource.import_count == 0:
                if not error:
                    # No error, but nothing imported either
                    error = "No CAP alerts found in source"
            else:
                # Success
                error = None
                msg = "%s new CAP alerts imported, %s alerts updated" % (
                        len(resource.import_created),
                        len(resource.import_updated))

        return error, msg

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_cap(source):
        """
            Parse a CAP-XML source and detect the CAP version

            @param source: the CAP-XML source

            @returns: tuple (tree, version, error)
                      - tree    = ElementTree of the CAP source
                      - version = the detected CAP version
                      - error   = error message if parsing failed, else None
        """

        version = error = None

        xml = current.xml

        # Attempt to parse the source
        tree = xml.parse(source)

        if not tree:
            # Capture parser error
            error = xml.error or "XML parsing failed"

        else:
            # All supported CAP versions and their namespace URIs
            namespaces = (("cap11", "urn:oasis:names:tc:emergency:cap:1.1"),
                          ("cap12", "urn:oasis:names:tc:emergency:cap:1.2"),
                          )

            # Default
            version = "cap12"

            root = tree.getroot()
            for ns, uri in namespaces:
                if root.xpath("/%s:alert[1]" % ns, namespaces = {ns: uri}):
                    version = ns
                    break

        return tree, version, error

    # -------------------------------------------------------------------------
    @staticmethod
    def opener(url,
               headers=None,
               username=None,
               password=None,
               preemptive_auth=False,
               proxy=None,
               ):
        """
            Configure a HTTP opener to fetch CAP messages

            @param url: the target URL
            @param headers: HTTP request headers, list of tuples (header, value)
            @param username: user name for auth
            @param password: password for auth
            @param preemptive_auth: send credentials without waiting for a
                                    HTTP401 challenge
            @param proxy: proxy URL (if required)

            @returns: an OpenerDirector instance with proxy and
                      auth handlers installed

            @example:
                url = "http://example.com/capfile.xml"
                opener = self._opener(url, username="user", password="password")
                content = opener.open(url)
        """

        # Configure opener headers
        addheaders = []
        if headers:
            addheaders.extend(headers)

        # Configure opener handlers
        handlers = []

        # Proxy handling
        if proxy:
            # Figure out the protocol from the URL
            url_split = url.split("://", 1)
            if len(url_split) == 2:
                protocol = url_split[0]
            else:
                protocol = "http"
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
            handlers.append(proxy_handler)

        # Authentication handling
        if username and password:
            # Add a 401 handler
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm = None,
                                        uri = url,
                                        user = username,
                                        passwd = password,
                                        )
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Create the opener
        opener = urllib2.build_opener(*handlers)

        # Pre-emptive basic auth
        if preemptive_auth and username and password:
            import base64
            base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
            addheaders.append(("Authorization", "Basic %s" % base64string))

        if addheaders:
            opener.addheaders = addheaders

        return opener

# -----------------------------------------------------------------------------
class cap_AssignArea(S3Method):
    """
        Assign CAP area to an alert, allows (multi-)selection of Predefined areas
    """

    def apply_method(self, r, **attr):
        """
            Apply method.
            @param r: the S3Request
            @param attr: controller options for this request
        """

        if not r.record:
            # Must be called for a particular alert
            r.error(404, current.ERROR.BAD_RECORD)

        # The record ID of the alert the method is called for
        alert_id = r.id

        # Requires permission to update this alert
        authorised = current.auth.s3_has_permission("update", "cap_alert",
                                                    record_id=alert_id)
        if not authorised:
            r.unauthorised()

        T = current.T
        s3db = current.s3db
        response = current.response

        # Get the event_type_id to filter by
        itable = s3db.cap_info
        row = current.db(itable.alert_id == alert_id).\
                    select(itable.event_type_id, limitby=(0, 1)).first()

        # Filter to limit the selection of areas
        area_filter = (FS("is_template") == True) & (FS("event_type_id") == row.event_type_id)

        if r.http == "POST":
            # Template areas have been selected

            added = 0
            post_vars = r.post_vars

            if all([n in post_vars for n in ("assign", "selected", "mode")]):

                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":

                    # URL filters
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.ajaxURL)
                    else:
                        filters = None

                    query = area_filter & (~(FS("id").belongs(selected)))
                    aresource = s3db.resource("cap_area",
                                              filter = query,
                                              vars = filters)
                    rows = aresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                for area_id in selected:
                    area_id = int(area_id.strip())
                    add_area_from_template(area_id, alert_id)
                    added += 1
            if added == 1:
                confirm_text = T("1 area assigned")
            elif added > 1:
                confirm_text = T("%(number)s areas assigned") % {"number": added}
            current.session.confirmation = confirm_text
            if added > 0:
                # Redirect to the list of areas of this alert
                redirect(URL(args=[r.id, "area"], vars={}))
            else:
                # Return to the "assign" page
                redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            # Filter widgets (@todo: lookup from cap_area resource config?)
            filter_widgets = []

            # List fields
            list_fields = ["id",
                           "name",
                           "event_type_id",
                           #"priority",
                           ]

            # Data table
            aresource = s3db.resource("cap_area", filter=area_filter)
            totalrows = aresource.count()
            get_vars = r.get_vars
            if "pageLength" in get_vars:
                display_length = get_vars["pageLength"]
                if display_length == "None":
                    display_length = None
                else:
                    display_length = int(display_length)
            else:
                display_length = 25
            if display_length:
                limit = 4 * display_length
            else:
                limit = None

            # Datatable filter and sorting
            query, orderby, left = aresource.datatable_filter(list_fields,
                                                              get_vars,
                                                              )
            aresource.add_filter(query)

            # Extract the data
            data = aresource.select(list_fields,
                                    start = 0,
                                    limit = limit,
                                    orderby = orderby,
                                    left = left,
                                    count = True,
                                    represent = True,
                                    )
            filteredrows = data.numrows

            # Instantiate the datatable
            dt = S3DataTable(data.rfields, data.rows)
            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Assign"), "assign")]

            if r.representation == "html":
                # Page load

                # Disallow deletion from this table, and link all open-buttons
                # to the respective area read page
                aresource.configure(deletable = False)
                profile_url = URL(c = "cap",
                                  f = "area",
                                  args = ["[id]", "read"],
                                  )
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = profile_url,
                                      update_url = profile_url,
                                      )
                # Hide export icons
                response.s3.no_formats = True

                # Render the datatable (will be "items" in the output dict)
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url = URL(args = r.args,
                                                  extension="aadata",
                                                  vars={},
                                                  ),
                                dt_bulk_actions = dt_bulk_actions,
                                dt_pageLength = display_length,
                                dt_pagination = "true",
                                dt_searching = "false",
                                )

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    get_vars = aresource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=get_vars)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f="cap_area",
                                          args=["filter.options"],
                                          vars={},
                                          )

                    get_config = aresource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear = filter_clear,
                                               formstyle = filter_formstyle,
                                               submit = filter_submit,
                                               ajax = True,
                                               url = filter_submit_url,
                                               ajaxurl = filter_ajax_url,
                                               _class = "filter-form",
                                               _id = "datatable-filter-form",
                                               )
                    fresource = s3db.resource("cap_area")
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target = "datatable",
                                          )
                else:
                    ff = ""

                output = {"items": items, # the datatable
                          "title": T("Add Areas"),
                          "list_filter_form": ff,
                          }
                response.view = "list_filter.html"
                return output

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions,
                                )
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# -----------------------------------------------------------------------------
class cap_CloneAlert(S3Method):
    """
        Clone the cap_alert
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply method
            @param r: the S3Request
            @param attr: controller options for this request
        """

        output = {}
        if r.http == "POST":
            if r.method == "clone":
                output = clone(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

# -----------------------------------------------------------------------------
def clone(r, record=None, **attr):
    """
        Clone the cap_alert

        @param r: the S3Request instance
        @param record: the record row
        @param attr: controller attributes
    """

    if record and not r.env.request_method == "POST":
        current.log.error(current.ERROR.BAD_METHOD)
        return

    # Get the alert ID
    alert_id = r.id
    if not alert_id and record:
        alert_id = record.id

    if not alert_id:
        # Must be called for a particular alert
        if record:
            current.log.error(current.ERROR.BAD_RECORD)
        else:
            r.error(404, current.ERROR.BAD_RECORD)

    s3db = current.s3db
    alert_table = s3db.cap_alert
    # Get the person ID
    auth = current.auth
    person_id = auth.s3_logged_in_person()
    if not person_id or not auth.s3_has_permission("create", alert_table):
        auth.permission.fail()

    msg_type_options = ["Alert", "Update", "Cancel", "Error", "AllClear"]
    msg_type = current.request._get_vars["msg_type"]

    if msg_type and msg_type not in msg_type_options:
        r.error(400, current.ERROR.BAD_REQUEST)

    # Start of clone
    db = current.db
    alert_history_table = s3db.cap_alert_history
    info_table = s3db.cap_info
    area_table = s3db.cap_area
    location_table = s3db.cap_area_location
    tag_table = s3db.cap_area_tag
    resource_table = s3db.cap_resource
    unwanted_fields = ["id", "doc_id"]
    unwanted_fields.extend(s3_all_meta_field_names())
    if record:
        unwanted_fields = ["id", "alert_id", "info_id", "is_template", "doc_id"]
    unwanted_fields = set(unwanted_fields)
    accessible_query = auth.s3_accessible_query
    has_permission = auth.s3_has_permission
    audit = current.audit
    set_record_owner = auth.s3_set_record_owner
    onaccept = s3db.onaccept

    # Copy the alert segment
    alert_fields = [alert_table[f] for f in alert_table.fields
                    if f not in unwanted_fields]
    alert_query = (alert_table.id == alert_id) & \
                   accessible_query("read", alert_table)
    alert_row = db(alert_query).select(*alert_fields, limitby=(0, 1)).first()
    alert_row_clone = alert_row.as_dict()
    if record:
        # Alert History use-case
        alert_row_clone["event_type"] = alert_table.event_type_id.represent(alert_row_clone["event_type_id"])
        del alert_row_clone["event_type_id"]
        del alert_row_clone["template_id"]
        del alert_row_clone["template_title"]
        del alert_row_clone["template_settings"]
        del alert_row_clone["external"]

        new_alert_id = alert_history_table.insert(**alert_row_clone)
        # Post-process create
        alert_row_clone["id"] = new_alert_id
        audit("create", "cap", "alert_history", record=new_alert_id)
        set_record_owner(alert_history_table, new_alert_id)
    else:
        # Change of msg_type use-case or relay alert
        referenced_reference = alert_row.reference
        references = []
        if referenced_reference:
            reference_splits = referenced_reference.split(",")
            reference_query_ = (alert_table.deleted != True) & \
                               (alert_table.is_template != True) & \
                               (alert_table.external != True)
            for split in reference_splits:
                reference_query = reference_query_ & (alert_table.identifier == split)
                reference_row = db(reference_query).select(alert_table.sender,
                                                           alert_table.sent,
                                                           limitby=(0, 1)).first()
                if reference_row:
                    references.append(("%s,%s,%s") % (reference_row.sender,
                                                      split,
                              s3_str(s3_utc(reference_row.sent)).replace(" ", "T")))

        references.append(("%s,%s,%s") % (alert_row.sender,
                                          alert_row.identifier,
                                s3_str(s3_utc(alert_row.sent)).replace(" ", "T")))
        del alert_row_clone["identifier"]
        alert_row_clone["msg_type"] = msg_type
        alert_row_clone["sent"] = current.request.utcnow
        alert_row_clone["external"] = False
        alert_row_clone["approved_on"] = None
        alert_row_clone["reference"] = " ".join(references)
        try:
            user_email = auth.user.email
        except AttributeError:
            user_email = ""
        alert_row_clone["sender"] = "%s" % user_email

        new_alert_id = alert_table.insert(**alert_row_clone)
        # Post-process create
        alert_row_clone["id"] = new_alert_id
        audit("create", "cap", "alert", record=new_alert_id)
        set_record_owner(alert_table, new_alert_id)
        onaccept(alert_table, alert_row_clone)

    if has_permission("create", info_table):
        # Copy the info segment
        info_history_table = s3db.cap_info_history
        unwanted_fields_ = list(unwanted_fields)
        unwanted_fields_.remove("id")
        info_fields = [info_table[f] for f in info_table.fields
                       if f not in unwanted_fields_]
        info_query = (info_table.alert_id == alert_id) &\
                      accessible_query("read", info_table)
        info_rows = db(info_query).select(*info_fields)
        if len(info_rows):
            info_parameter_table = s3db.cap_info_parameter
            info_parameter_history_table = s3db.cap_info_parameter_history
            info_parameter_table_insert = info_parameter_table.insert
            info_parameter_history_table_insert = info_parameter_history_table.insert
            info_parameter_accessible = accessible_query("read", info_parameter_table)
            info_parameter_fields = [info_parameter_table[f] for f in info_parameter_table.fields
                                     if f not in unwanted_fields]
            info_parameter_query_ = (info_parameter_table.alert_id == alert_id)
            for info_row in info_rows:
                info_id = info_row.id
                info_row_clone = info_row.as_dict()
                del info_row_clone["id"]
                if msg_type and msg_type == "AllClear":
                    info_row_clone["response_type"] = "AllClear"
                if record:
                    # Info History use-case
                    del info_row_clone["template_info_id"]
                    del info_row_clone["template_settings"]
                    del info_row_clone["event_type_id"]
                    info_row_clone["priority"] = info_table.priority.represent(info_row_clone["priority"])
                    info_row_clone["alert_history_id"] = new_alert_id
                    new_info_id = info_history_table.insert(**info_row_clone)
                    # Post-process create
                    info_row_clone["id"] = new_info_id
                    audit("create", "cap", "info_history", record=new_info_id)
                    set_record_owner(info_history_table, new_info_id)
                else:
                    # Change of msg_type use-case
                    info_row_clone["alert_id"] = new_alert_id
                    new_info_id = info_table.insert(**info_row_clone)
                    # Post-process create
                    info_row_clone["id"] = new_info_id
                    audit("create", "cap", "info", record=new_info_id)
                    set_record_owner(info_table, new_info_id)
                    onaccept(info_table, info_row_clone)

                # Copy the info parameters
                info_parameter_query = info_parameter_query_ & \
                                       (info_parameter_table.info_id == info_id) & \
                                       info_parameter_accessible
                info_parameter_rows = db(info_parameter_query).select(*info_parameter_fields)
                for info_parameter_row in info_parameter_rows:
                    info_parameter_row_clone = info_parameter_row.as_dict()
                    if record:
                        # History table use-case
                        info_parameter_row_clone["alert_history_id"] = new_alert_id
                        info_parameter_row_clone["info_history_id"] = new_info_id
                        new_info_parameter_id = info_parameter_history_table_insert(**info_parameter_row_clone)
                        # Post-process create
                        info_parameter_row_clone["id"] = new_info_parameter_id
                        audit("create", "cap", "info_parameter_history",
                              record=new_info_parameter_id)
                        set_record_owner(info_parameter_history_table, new_info_parameter_id)
                    else:
                        # Change of msg_type use-case
                        info_parameter_row_clone.update(alert_id = new_alert_id,
                                                        info_id = new_info_id)
                        new_info_parameter_id = info_parameter_table_insert(**info_parameter_row_clone)
                        # Post-process create
                        info_parameter_row_clone["id"] = new_info_parameter_id
                        audit("create", "cap", "info_parameter",
                              record=new_info_parameter_id)
                        set_record_owner(info_parameter_table, new_info_parameter_id)
                        onaccept(info_parameter_table, info_parameter_row_clone)

    if has_permission("create", area_table):
        # Copy the area segment
        area_fields = [area_table[f] for f in area_table.fields
                       if f not in unwanted_fields_]
        area_query = (area_table.alert_id == alert_id) & \
                     accessible_query("read", area_table)
        area_rows = db(area_query).select(*area_fields)
        if len(area_rows):
            gtable = s3db.gis_location
            area_history_table = s3db.cap_area_history
            location_history_table = s3db.cap_area_location_history
            tag_history_table = s3db.cap_area_tag_history
            onvalidation = s3db.onvalidation
            area_table_insert = area_table.insert

            location_table_insert = location_table.insert
            location_accessible = accessible_query("read", location_table)
            location_fields = [location_table[f] for f in location_table.fields
                               if f not in unwanted_fields]

            tag_table_insert = tag_table.insert
            tag_accessible = accessible_query("read", tag_table)
            tag_fields = [tag_table[f] for f in tag_table.fields
                          if f not in unwanted_fields]

            for area_row in area_rows:
                area_id = area_row.id
                area_row_clone = area_row.as_dict()
                del area_row_clone["id"]
                if record:
                    # History table use-case
                    del area_row_clone["template_area_id"]
                    del area_row_clone["event_type_id"]
                    #del area_row_clone["priority"]
                    area_row_clone["alert_history_id"] = new_alert_id
                    new_area_id = area_history_table.insert(**area_row_clone)
                    # Post-process create
                    area_row_clone["id"] = new_area_id
                    audit("create", "cap", "area_history", record=new_area_id)
                    set_record_owner(area_history_table, new_area_id)
                else:
                    # Update/Error/Relay/All Clear use-case
                    area_row_clone["alert_id"] = new_alert_id

                    new_area_id = area_table_insert(**area_row_clone)
                    # Post-process create
                    area_row_clone["id"] = new_area_id
                    audit("create", "cap", "area", record=new_area_id)
                    set_record_owner(area_table, new_area_id)
                    onaccept(area_table, area_row_clone)

                # Copy the area_location
                location_query = (location_table.area_id == area_id) &\
                                 location_accessible
                location_rows = db(location_query).\
                                    select(*location_fields)
                for location_row in location_rows:
                    location_row_clone = location_row.as_dict()
                    if record:
                        # History table use-case
                        del location_row_clone["area_id"]
                        location_row_clone["alert_history_id"] = new_alert_id
                        location_row_clone["area_history_id"] = new_area_id
                        grow = db(gtable.id == location_row_clone["location_id"]).\
                                select(gtable.wkt, limitby=(0, 1)).first()
                        if grow:
                            location_row_clone["location_wkt"] = grow.wkt
                        del location_row_clone["location_id"]
                        new_location_id = location_history_table.insert(**location_row_clone)
                        # Post-process create
                        location_row_clone["id"] = new_location_id
                        audit("create", "cap", "area_location_history",
                              record=new_location_id)
                        set_record_owner(location_history_table, new_location_id)
                    else:
                        # Update/Error/Relay/All Clear use-case
                        location_row_clone.update(alert_id = new_alert_id,
                                                  area_id = new_area_id)
                        onvalidation(gtable, location_row_clone)
                        new_location_id = location_table_insert(**location_row_clone)
                        # Post-process create
                        location_row_clone["id"] = new_location_id
                        audit("create", "cap", "area_location",
                              record=new_location_id)
                        set_record_owner(location_table, new_location_id)
                        onaccept(location_table, location_row_clone)

                # Copy the area_tag
                tag_query = (tag_table.area_id == area_id) &\
                            tag_accessible
                tag_rows = db(tag_query).select(*tag_fields)
                for tag_row in tag_rows:
                    tag_row_clone = tag_row.as_dict()
                    if record:
                        # History table use-case
                        del tag_row_clone["area_id"]
                        tag_row_clone["alert_history_id"] = new_alert_id
                        tag_row_clone["area_history_id"] = new_area_id

                        new_tag_id = tag_history_table.insert(**tag_row_clone)
                        # Post-process create
                        tag_row_clone["id"] = new_tag_id
                        audit("create", "cap", "area_tag_history", record=new_tag_id)
                        set_record_owner(tag_history_table, new_tag_id)
                    else:
                        # Update/Error/Relay/All Clear use-case
                        tag_row_clone.update(alert_id = new_alert_id,
                                             area_id = new_area_id)

                        new_tag_id = tag_table_insert(**tag_row_clone)
                        # Post-process create
                        tag_row_clone["id"] = new_tag_id
                        audit("create", "cap", "area_tag", record=new_tag_id)
                        set_record_owner(tag_table, new_tag_id)
                        # Don't do onaccept as geocodes may create locations, so duplicates
                        # as Locations are cloned anyway
                        #onaccept(tag_table, tag_row_clone)
    if has_permission("create", resource_table):
        # Copy the resource segment
        resource_fields = [resource_table[f] for f in resource_table.fields
                           if f not in unwanted_fields]
        resource_query = (resource_table.alert_id == alert_id) &\
                         accessible_query("read", resource_table)
        resource_rows = db(resource_query).select(*resource_fields)
        if len(resource_rows):
            resource_history_table = s3db.cap_resource_history
            resource_table_insert = resource_table.insert
            update_super = s3db.update_super
            for resource_row in resource_rows:
                resource_row_clone = resource_row.as_dict()
                mime_type = resource_row_clone["mime_type"]
                if record:
                    # History Table use-case
                    resource_row_clone["alert_history_id"] = new_alert_id
                    rid = resource_history_table.insert(**resource_row_clone)
                    resource_row_clone["id"] = rid
                    # Post-process create
                    audit("create", "cap", "resource_history", record=rid)
                    set_record_owner(resource_history_table, rid)
                elif mime_type and mime_type != "cap":
                    # Update/Error/Relay/All Clear use-case
                    resource_row_clone["alert_id"] = new_alert_id
                    rid = resource_table_insert(**resource_row_clone)
                    resource_row_clone["id"] = rid
                    # Post-process create
                    audit("create", "cap", "resource", record=rid)
                    update_super(resource_table, resource_row_clone)
                    set_record_owner(resource_table, rid)
                    onaccept(resource_table, resource_row_clone)


    if not record:
        output = current.xml.json_message(message=new_alert_id)
        current.response.headers["Content-Type"] = "application/json"
        return output
    return

# -----------------------------------------------------------------------------
class cap_AreaRepresent(S3Represent):
    """ Representation of CAP Area """

    def __init__(self,
                 show_link=False,
                 multiple=False):

        settings = current.deployment_settings
        # Translation using cap_area_name & not T()
        translate = settings.get_L10n_translate_cap_area()
        if translate:
            language = current.session.s3.language
            if language == settings.get_L10n_default_language():
                translate = False

        super(cap_AreaRepresent,
              self).__init__(lookup="cap_area",
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple
                             )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for Area(CAP) rows.Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the cap_area IDs
        """

        s3db = current.s3db
        artable = s3db.cap_area

        count = len(values)
        if count == 1:
            query = (artable.id == values[0])
        else:
            query = (artable.id.belongs(values))

        fields = [artable.id,
                  artable.name,
                  ]

        if self.translate:
            ltable = s3db.cap_area_name
            fields += [ltable.name_l10n,
                       ]
            left = [ltable.on((ltable.area_id == artable.id) & \
                              (ltable.language == current.session.s3.language)),
                        ]

        else:
            left = None

        rows = current.db(query).select(left = left,
                                        limitby = (0, count),
                                        *fields)
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the cap_area Row
        """

        if self.translate:
            name = row["cap_area_name.name_l10n"] or row["cap_area.name"]
        else:
            name = row["cap_area.name"]

        if not name:
            return self.default

        return s3_str(name)

# -----------------------------------------------------------------------------
class cap_AlertProfileWidget(object):
    """ Custom profile widget builder """

    def __init__(self, title, label=None, value=None):

        self.title = title
        self.label = label
        self.value = value

    # -------------------------------------------------------------------------
    def __call__(self, f):
        """
            Widget builder
            @param f: the calling function
        """

        def widget(r, **attr):
            components = f(r, **attr)
            components = [c for c in components if c is not None]
            title = self.title
            if title:
                label = self.label
                value = self.value
                T = current.T
                if label and value:
                    title_ = DIV(SPAN("%s " % T(title),
                                      _class="cap-value upper"
                                      ),
                                 SPAN("%s :: " % T(label),
                                      _class="cap-label upper"
                                      ),
                                 SPAN(value,
                                      _class="cap-strong"
                                      ),
                                 )
                else:
                    title_ = DIV(SPAN(T(title),
                                      _class="cap-value upper"),
                                 )

                header = TAG[""](title_,
                                 DIV(_class="underline"),
                                 )
                output = DIV(header, *components)
            else:
                output = DIV(components)
            return output

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def component(label, value,
                  represent = None,
                  uppercase = False,
                  strong = False,
                  hide_empty = True,
                  headline = False,
                  resource_segment = False,
                  ):
        """
            Component builder
            @param label: name for the component label
            @param value: value for the component
            @param represent: representation used for the value
            @param uppercase: whether to display label in upper case
            @param strong: whether to display with strong color
            @param hide_empty: whether to hide empty records
            @param headline: is headline?
            @param resource_segment: belongs to resource segment?
        """

        if not value and hide_empty:
            return None
        else:
            if isinstance(value, list):
                nvalue = []
                for value_ in value:
                    if value_:
                        if resource_segment and represent:
                            nvalue.append(represent(value_))
                        elif not resource_segment:
                            if represent:
                                nvalue.append(s3_str(represent(value_)))
                            else:
                                nvalue.append(s3_str(value_))
                if not resource_segment:
                    if len(nvalue):
                        nvalue = ", ".join(nvalue)
                    else:
                        return None
            else:
                if represent:
                    nvalue = represent(value)
                else:
                    nvalue = value

            label_class = "cap-label"
            if uppercase:
                label_class = "%s upper" % label_class
            value_class = "cap-value"
            if strong:
                value_class = "cap-strong"
            elif headline:
                value_class = "%s cap-headline" % value_class

            output = DIV(SPAN("%s :: " % current.T(label), _class=label_class),
                         SPAN(nvalue, _class=value_class),
                         )

            return output

# END =========================================================================
