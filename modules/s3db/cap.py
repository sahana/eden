# -*- coding: utf-8 -*-

""" Sahana Eden Common Alerting Protocol (CAP) Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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
           "cap_rheader",
           ]

import datetime

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
             "cap_alert_represent",
             "cap_info",
             "cap_info_represent",
             "cap_resource",
             "cap_area",
             "cap_area_location",
             "cap_area_tag",
             ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
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
        define_table(tablename,
                     Field("is_template", "boolean",
                           readable = False,
                           writable = True,
                           ),
                     Field("template_id", "reference cap_alert",
                           label = T("Template"),
                           ondelete = "RESTRICT",
                           represent = self.template_represent,
                           requires = IS_EMPTY_OR(
                                         IS_ONE_OF(db, "cap_alert.id",
                                                   self.template_represent,
                                                   filterby="is_template",
                                                   filter_opts=(True,)
                                                   )),
                           comment = T("Apply a template"),
                           ),
                     Field("template_title",
                           label = T("Template Title"),
                           ),
                     Field("template_settings", "text",
                           default = "{}",
                           readable = False,
                           ),
                     Field("identifier", unique=True, length=128,
                           default = self.generate_identifier,
                           label = T("Identifier"),
                           ),
                     Field("sender",
                           label = T("Sender"),
                           default = self.generate_sender,
                           ),
                     s3_datetime("sent",
                                 default = "now",
                                 writable = False,
                                 ),
                     Field("status",
                           default = "Draft",
                           label = T("Status"),
                           requires = IS_IN_SET(cap_alert_status_code_opts),
                           ),
                     Field("msg_type",
                           label = T("Message Type"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_alert_msgType_code_opts)
                                        ),
                           ),
                     Field("source",
                           label = T("Source"),
                           ),
                     Field("scope",
                           label = T("Scope"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_alert_scope_code_opts)
                                        ),
                           ),
                     # Text describing the restriction for scope=restricted
                     Field("restriction", "text",
                           label = T("Restriction"),
                           ),
                     Field("addresses", "list:string",
                           label = T("Recipients"),
                           represent = self.list_string_represent,
                           #@ToDo: provide a better way to add multiple addresses,
                           #       do not ask the user to delimit it themselves
                           #       this should eventually use the CAP contacts
                           #widget = S3CAPAddressesWidget,
                           ),
                     Field("codes", "text",
                           default = settings.get_cap_codes(),
                           label = T("Codes"),
                           represent = S3KeyValueWidget.represent,
                           widget = S3KeyValueWidget(),
                           ),
                     Field("note", "text",
                           label = T("Note"),
                           ),
                     Field("reference", "list:reference cap_alert",
                           label = T("Reference"),
                           represent = S3Represent(lookup = tablename,
                                                   fields = ["msg_type", "sent", "sender"],
                                                   field_sep = " - ",
                                                   multiple = True,
                                                   ),
                           # @ToDo: This should not be manually entered,
                           #        needs a widget
                           #widget = S3ReferenceWidget(table,
                           #                           one_to_many=True,
                           #                           allow_create=False),
                           ),
                     # @ToDo: Switch to using event_incident_type_id
                     Field("incidents", "list:string",
                           label = T("Incidents"),
                           represent = S3Represent(options = cap_incident_type_opts,
                                                   multiple = True),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_incident_type_opts,
                                                  multiple = True,
                                                  sort = True,
                                                  )),
                           widget = S3MultiSelectWidget(),
                           ),
                     *s3_meta_fields())

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
            ]

        configure(tablename,
                  filter_widgets = filter_widgets,
                  onvalidation = self.cap_alert_form_validation,
                  )

        # Components
        add_components(tablename,
                       cap_info = "alert_id",
                       cap_area = "alert_id",
                       cap_resource = "alert_id",
                       )

        if crud_strings["cap_template"]:
            crud_strings[tablename] = crud_strings["cap_template"]
        else:
            ADD_ALERT = T("Create Alert")
            crud_strings[tablename] = Storage(
                label_create = ADD_ALERT,
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
                                   ondelete = "RESTRICT",
                                   represent = alert_represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_alert.id",
                                                          alert_represent)),
                                   )

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
            ("Immediate", T("Response action should be taken immediately")),
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
        define_table(tablename,
                     alert_id(),
                     Field("is_template", "boolean",
                           default = True,
                           readable = False,
                           writable = False,
                           ),
                     Field("template_info_id", "reference cap_info",
                           ondelete = "RESTRICT",
                           readable = False,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "cap_info.id",
                                                  self.template_represent,
                                                  filterby="is_template",
                                                  filter_opts=(True,)
                                                  )),
                           widget = S3HiddenWidget(),
                           ),
                     Field("template_settings", "text",
                           readable = False,
                           ),
                     Field("language",
                           default = "en",
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(settings.get_cap_languages())
                                        ),
                           ),
                     Field("category", "list:string",
                           represent = S3Represent(options = cap_info_category_opts,
                                                   multiple = True,
                                                   ),
                           required = True,
                           requires = IS_IN_SET(cap_info_category_opts,
                                                multiple = True,
                                                ),
                           widget = S3MultiSelectWidget(),
                           ), # 1 or more allowed
                     Field("event",
                           required = True,
                           ),
                     Field("response_type", "list:string",
                           represent = S3Represent(options = cap_info_responseType_opts,
                                                   multiple = True,
                                                   ),
                           requires = IS_IN_SET(cap_info_responseType_opts,
                                                multiple = True),
                           widget = S3MultiSelectWidget(),
                           ), # 0 or more allowed
                     Field("priority",
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(cap_info_priority_opts)
                                        ),
                           ),
                     Field("urgency",
                           required = True,
                           requires = IS_IN_SET(cap_info_urgency_opts),
                           ),
                     Field("severity",
                           required = True,
                           requires = IS_IN_SET(cap_info_severity_opts),
                           ),
                     Field("certainty",
                           required = True,
                           requires = IS_IN_SET(cap_info_certainty_opts),
                           ),
                     Field("audience", "text"),
                     Field("event_code", "text",
                           default = settings.get_cap_event_codes(),
                           represent = S3KeyValueWidget.represent,
                           widget = S3KeyValueWidget(),
                           ),
                     s3_datetime("effective"),
                     s3_datetime("onset"),
                     s3_datetime("expires",
                                 past = 0,
                                 ),
                     Field("sender_name"),
                     Field("headline"),
                     Field("description", "text"),
                     Field("instruction", "text"),
                     Field("contact", "text"),
                     Field("web",
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("parameter", "text",
                           default = settings.get_cap_parameters(),
                           label = T("Parameters"),
                           represent = S3KeyValueWidget.represent,
                           widget = S3KeyValueWidget(),
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
                                  ondelete = "RESTRICT",
                                  represent = info_represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cap_info.id",
                                                          info_represent)
                                                ),
                                  sortby = "identifier",
                                  )

        configure(tablename,
                  #create_next = URL(f="info", args=["[id]", "area"]),
                  onaccept = self.info_onaccept,
                  )

        # Components
        add_components(tablename,
                       cap_resource = "info_id",
                       cap_area = "info_id",
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
                     info_id(),
                     Field("resource_desc",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("mime_type",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("size", "integer",
                           writable = False,
                           ),
                     Field("uri",
                           # needs a special validation
                           writable = False,
                           ),
                     Field("file", "upload"),
                     Field("deref_uri", "text",
                           readable = False,
                           writable = False,
                           ),
                     Field("digest",
                           writable = False,
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

        configure(tablename,
                  onaccept = update_alert_id(tablename),
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
                     alert_id(writable = False,
                              ),
                     info_id(),
                     Field("name",
                           label = T("Area description"),
                           required = True,
                           ),
                     #Field("geocode", "text",
                     #      widget = S3KeyValueWidget(),
                     #      represent = S3KeyValueWidget.represent,
                     #      default = settings.get_cap_geocodes),
                     Field("altitude", "integer"),
                     Field("ceiling", "integer"),
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

        crud_form = S3SQLCustomForm("name",
                                    "info_id",
                                    # Not yet working with default formstyle or multiple=True
                                    #S3SQLInlineComponent("area_location",
                                    #                     name = "location",
                                    #                     label = "",
                                    #                     multiple = False,
                                    #                     fields = [("", "location_id")],
                                    #                     ),
                                    S3SQLInlineComponent("area_tag",
                                                         name = "tag",
                                                         label = "",
                                                         fields = ["tag",
                                                                   "value",
                                                                   ],
  
                                                         ),
                                    "altitude",
                                    "ceiling",
                                    )

        configure(tablename,
                  create_next = URL(f="area", args=["[id]", "area_location"]),
                  crud_form = crud_form,
                  onaccept = update_alert_id(tablename),
                  )

        # Components
        add_components(tablename,
                       cap_area_location = "area_id",
                       cap_area_tag = "area_id",
                       )

        # ToDo: Use a widget tailored to entering <polygon> and <circle>.
        # Want to be able to enter them by drawing on the map.
        # Also want to allow selecting existing locations that have
        # geometry, maybe with some filtering so the list isn't cluttered
        # with irrelevant locations.
        tablename = "cap_area_location"
        define_table(tablename,
                     Field("area_id", "reference cap_area"),
                     self.gis_location_id(
                         widget = S3LocationSelectorWidget2(polygons=True,
                                                            show_map=True,
                                                            show_address=False,
                                                            show_postcode=False,
                                                            ),
                         ),
                     )

        # ToDo: When importing, we'll construct the WKT for locations in
        # xml_post_parse. However, this is an action on the gis_location not
        # the cap_area_location, so we'll add the xml_post_parse to
        # gis_location in the cap_alert controller's prep, as it's not wanted
        # for anything but CAP.
        # ToDo: Right now, we have no support for CIRCULARSTRING, so will need
        # to handle adding circle info when the location is added in the form
        # as well.

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
                     Field("area_id", "reference cap_area"),
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

        #configure(tablename,
        #          deduplicate = self.cap_area_tag_deduplicate,
        #          )


        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(cap_alert_id = alert_id,
                    cap_alert_represent = alert_represent,
                    cap_info_represent = info_represent,
                    )

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

        _time = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y/%m/%dT%H:%M:%S")
        if r:
            next_id = int(r.id) + 1
        else:
            next_id = 1

        # Format: prefix-time+-timezone+sequence-suffix
        settings = current.deployment_settings
        prefix = settings.get_cap_identifier_prefix() or current.xml.domain
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

        return "%s/%d" % (current.xml.domain, user_id)

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
                return s3db.cap_alert_represent(id)
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
    def cap_alert_form_validation(form):
        """
            On Validation for CAP alert form
        """

        form_vars = form.vars
        if form_vars.get("scope") == "Private" and not form_vars.get("addresses"):
            form.errors["addresses"] = \
                current.T("'Recipients' field mandatory in case of 'Private' scope")
        return

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

    # -------------------------------------------------------------------------
    @staticmethod
    def area_represent(id, row=None):
        """
            Represent an alert information area
        """

        if row:
            pass
        elif not id:
            return current.messages["NONE"]
        else:
            db = current.db
            table = db.cap_area
            row = db(table.id == id).select(table.name,
                                            limitby=(0, 1)).first()

        return row.name

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
def cap_rheader(r):
    """ Resource Header for CAP module """

    rheader = None
    if r.representation == "html":
        record = r.record
        if record:
            T = current.T
            s3db = current.s3db
            tablename = r.tablename
            if tablename == "cap_alert":
                table = s3db.cap_info
                query = (table.alert_id == record.id)
                row = current.db(query).select(table.id,
                                               limitby=(0, 1)).first()
                if record.is_template:
                    if not (row and row.id):
                        error = DIV(T("An alert needs to contain at least one info item."),
                                    _class="error")
                    else:
                        error = ""

                    tabs = [(T("Template"), None),
                            (T("Information template"), "info"),
                            #(T("Area"), "area"),
                            #(T("Resource Files"), "resource"),
                            ]

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    rheader = DIV(TABLE(TR(TH("%s: " % T("Template")),
                                           TD(A(S3CAPModel.template_represent(record.id, record),
                                                _href=URL(c="cap", f="template",
                                                          args=[record.id, "update"]))),
                                           ),
                                        ),
                                  rheader_tabs,
                                  error
                                  )
                else:
                    if not (row and row.id):
                        error = DIV(T("You need to create at least one alert information item in order to be able to broadcast this alert!"),
                                    _class="error")
                    else:
                        error = ""

                    tabs = [(T("Alert Details"), None),
                            (T("Information"), "info"),
                            (T("Area"), "area"),
                            (T("Resource Files"), "resource"),
                            ]

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                           TD(A(s3db.cap_alert_represent(record.id, record),
                                                _href=URL(c="cap", f="alert",
                                                          args=[record.id, "update"]))),
                                           ),
                                        ),
                                  rheader_tabs,
                                  error
                                  )

            elif tablename == "cap_area":
                
                tabs = [(T("Area"), None),
                        (T("Locations"), "area_location"),
                        #(T("Geocodes"), "area_tag"),
                        ]
                rheader_tabs = s3_rheader_tabs(r, tabs)
                rheader = DIV(TABLE(TR(TH("%s: " % T("Alert")),
                                       TD(A(s3db.cap_alert_represent(record.alert_id),
                                            _href=URL(c="cap", f="alert",
                                                      args=[record.id, "update"])))
                                       ),
                                    TR(TH("%s: " % T("Information")),
                                       TD(A(s3db.cap_info_represent(record.info_id),
                                            _href=URL(c="cap", f="info",
                                                      args=[record.info_id, "update"]))),
                                       ),
                                    TR(TH("%s: " % T("Area")),
                                       TD(A(S3CAPModel.area_represent(record.id, record),
                                            _href=URL(c="cap", f="area",
                                                      args=[record.id, "update"]))),
                                       ),
                                    ),
                              rheader_tabs
                              )

            elif tablename == "cap_area_location":
                # Shouldn't ever be called
                # We need the rheader only for the link back to the area.
                rheader = DIV(TABLE(TR(TH("%s: " % T("Area")),
                                       TD(A(S3CAPModel.area_represent(record.area_id),
                                            _href=URL(c="cap", f="area",
                                                      args=[record.area_id, "update"]))),
                                       ),
                                    ))

            elif tablename == "cap_info":
                # Shouldn't ever be called
                tabs = [(T("Information"), None),
                        (T("Resource Files"), "resource"),
                        ]

                if cap_alert_is_template(record.alert_id):
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                    table = r.table
                    rheader = DIV(TABLE(TR(TH("%s: " % T("Template")),
                                           TD(A(S3CAPModel.template_represent(record.alert_id),
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
                    table = r.table

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
def update_alert_id(tablename):
    """ On-accept for area and resource records """

    def func(form):
        if "vars" in form:
            form_vars = form.vars
        elif "id" in form:
            form_vars = form
        elif hasattr(form, "vars"):
            form_vars = form.vars
        else:
            form_vars = form

        if form_vars.get("alert_id", None):
            # Nothing to do
            return

        # Look up from the info
        info_id = form_vars.get("info_id", None)
        if not info_id:
            # Get the full record
            _id = form_vars.id
            if not _id:
                return
    
            db = current.db
            table = db[tablename]
            item = db(table.id == _id).select(table.alert_id,
                                              table.info_id,
                                              limitby=(0, 1)).first()
            try:
                alert_id = item.alert_id
                info_id = item.info_id
            except:
                # Nothing we can do
                return
            if alert_id:
                # Nothing to do
                return

        itable = db.cap_info
        info = db(itable.id == info_id).select(itable.alert_id,
                                               limitby=(0, 1)).first()
        try:
            alert_id = info.alert_id
        except:
            # Nothing we can do
            return

        db(table.id == _id).update(alert_id = alert_id)

    return func

# END =========================================================================
