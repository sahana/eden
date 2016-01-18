# -*- coding: utf-8 -*-

""" Sahana Eden Incident Reporting Model

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("S3IRSModel",
           "S3IRSResponseModel",
           "irs_rheader"
           )

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3IRSModel(S3Model):

    names = ("irs_icategory",
             "irs_ireport",
             "irs_ireport_person",
             "irs_ireport_id"
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        # Shortcuts
        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # List of Incident Categories
        # The keys are based on the Canadian ems.incident hierarchy, with a few extra general versions added to 'other'
        # The values are meant for end-users, so can be customised as-required
        # NB It is important that the meaning of these entries is not changed as otherwise this hurts our ability to do synchronisation
        # Entries can be hidden from user view in the controller.
        # Additional sets of 'translations' can be added to the tuples.
        irs_incident_type_opts = {
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

        # This Table defines which Categories are visible to end-users
        tablename = "irs_icategory"
        define_table(tablename,
                     Field("code",
                           label = T("Category"),
                           requires = IS_IN_SET_LAZY(lambda: \
                                      sort_dict_by_values(irs_incident_type_opts)),
                           represent = lambda opt: \
                                       irs_incident_type_opts.get(opt, opt)),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["code"],
                  onvalidation = self.irs_icategory_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # Reports
        # This is a report of an Incident
        #
        # Incident Reports can be linked to Incidents through the event_incident_report table
        #
        # @ToDo: If not using the Events module, we could have a 'lead incident' to track duplicates?
        #

        # Porto codes
        #irs_incident_type_opts = {
        #    1100:T("Fire"),
        #    6102:T("Hazmat"),
        #    8201:T("Rescue")
        #}
        tablename = "irs_ireport"
        define_table(tablename,
                     super_link("sit_id", "sit_situation"),
                     super_link("doc_id", "doc_entity"),
                     Field("name",
                           label = T("Short Description"),
                           requires = IS_NOT_EMPTY()),
                     Field("message", "text",
                           label = T("Message"),
                           represent = lambda text: \
                                       s3_truncate(text, length=48, nice=True)),
                     Field("category",
                           label = T("Category"),
                           # The full set available to Admins & Imports/Exports
                           # (users use the subset by over-riding this in the Controller)
                           requires = IS_EMPTY_OR(IS_IN_SET_LAZY(lambda: \
                                      sort_dict_by_values(irs_incident_type_opts))),
                           # Use this instead if a simpler set of Options required
                           #requires = IS_EMPTY_OR(IS_IN_SET(irs_incident_type_opts)),
                           represent = lambda opt: \
                                       irs_incident_type_opts.get(opt, opt)),
                     self.hrm_human_resource_id(
                          #readable=False,
                          #writable=False,
                          label = T("Reported By (Staff)")
                          ),
                     # Plain text field in case non-staff & don't want to clutter the PR
                     Field("person",
                           #readable = False,
                           #writable = False,
                           label = T("Reported By (Not Staff)"),
                           #comment = (T("At/Visited Location (not virtual)"))
                           ),
                     Field("contact",
                           readable = False,
                           writable = False,
                           label = T("Contact Details")),
                     s3_datetime("datetime",
                                 label = T("Date/Time of Alert"),
                                 empty=False,
                                 default="now",
                                 future=0,
                                 ),
                     s3_datetime("expiry",
                                 label = T("Expiry Date/Time"),
                                 past=0,
                                 ),
                     self.gis_location_id(),
                     # Very basic Impact Assessment
                     # @ToDo: Use Stats_Impact component instead
                     Field("affected", "integer",
                           label=T("Number of People Affected"),
                           represent = lambda val: val or T("unknown"),
                           ),
                     Field("dead", "integer",
                           label=T("Number of People Dead"),
                           represent = lambda val: val or T("unknown"),
                           ),
                     Field("injured", "integer",
                           label=T("Number of People Injured"),
                           represent = lambda val: val or T("unknown"),
                           ),
                     # Probably too much to try & capture
                     #Field("missing", "integer",
                     #      label=T("Number of People Missing")),
                     #Field("displaced", "integer",
                     #      label=T("Number of People Displaced")),
                     Field("verified", "boolean",    # Ushahidi-compatibility
                           # We don't want these visible in Create forms
                           # (we override in Update forms in controller)
                           readable = False,
                           writable = False,
                           label = T("Verified?"),
                           represent = lambda verified: \
                                       (T("No"),
                                       T("Yes"))[verified == True]
                           ),
                     # @ToDo: Move this to Events?
                     # Then add component to list_fields
                     s3_datetime("dispatch",
                                 label = T("Date/Time of Dispatch"),
                                 future=0,
                                 # We don't want these visible in Create forms
                                 # (we override in Update forms in controller)
                                 readable = False,
                                 writable = False,
                                 ),
                     Field("closed", "boolean",
                           # We don't want these visible in Create forms
                           # (we override in Update forms in controller)
                           default = False,
                           readable = False,
                           writable = False,
                           label = T("Closed?"),
                           represent = lambda closed: \
                                       (T("No"),
                                       T("Yes"))[closed == True]
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_INC_REPORT = T("Create Incident Report")
        crud_strings[tablename] = Storage(
            label_create = ADD_INC_REPORT,
            title_display = T("Incident Report Details"),
            title_list = T("Incident Reports"),
            title_update = T("Edit Incident Report"),
            title_upload = T("Import Incident Reports"),
            title_map = T("Map of Incident Reports"),
            label_list_button = T("List Incident Reports"),
            label_delete_button = T("Delete Incident Report"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report deleted"),
            msg_list_empty = T("No Incident Reports currently registered"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [
            S3TextFilter(["name",
                          "message",
                          "comments",
                          ],
                         label=T("Description"),
                         comment = T("You can search by description. You may use % as wildcard. Press 'Search' without input to list all incidents."),
                        _class="filter-search",
                         ),
            S3LocationFilter("location_id",
                             levels = levels,
                             #hidden = True,
                             ),
            S3OptionsFilter("category",
                            #hidden = True,
                            ),
            S3DateFilter("datetime",
                         label = T("Date"),
                         hide_time = True,
                         #hidden = True,
                         ),
            ]

        report_fields = ["category",
                         "datetime",
                         ]

        for level in levels:
            report_fields.append("location_id$%s" % level)

        # Resource Configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = ["id",
                                 "name",
                                 "category",
                                 "datetime",
                                 "location_id",
                                 #"organisation_id",
                                 "affected",
                                 "dead",
                                 "injured",
                                 "verified",
                                 "message",
                                 ],
                 report_options = Storage(rows = report_fields,
                                          cols = report_fields,
                                          fact = [(T("Number of Incidents"), "count(id)"),
                                                  (T("Total Affected"), "sum(affected)"),
                                                  (T("Total Dead"), "sum(dead)"),
                                                  (T("Total Injured"), "sum(injured)"),
                                                  ],
                                          defaults = dict(rows = "location_id$%s" % levels[0], # Highest-level of hierarchy
                                                          cols = "category",
                                                          fact = "count(id)",
                                                          totals = True,
                                                          )
                                          ),
                 super_entity = ("sit_situation", "doc_entity"),
                 )

        # Components
        if settings.get_irs_vehicle():
            # @ToDo: This workflow requires more work
            hr_link_table = "irs_ireport_vehicle_human_resource"
        else:
            hr_link_table = "irs_ireport_human_resource"
        add_components(tablename,
                       # Tasks
                       project_task={"link": "project_task_ireport",
                                     "joinby": "ireport_id",
                                     "key": "task_id",
                                     "actuate": "replace",
                                     "autocomplete": "name",
                                     "autodelete": False,
                                    },
                       # Vehicles
                       asset_asset={"link": "irs_ireport_vehicle",
                                    "joinby": "ireport_id",
                                    "key": "asset_id",
                                    "name": "vehicle",
                                    # Dispatcher doesn't need to Add/Edit records, just Link
                                    "actuate": "link",
                                    "autocomplete": "name",
                                    "autodelete": False,
                                   },
                       # Human Resources
                       hrm_human_resource={"link": hr_link_table,
                                           "joinby": "ireport_id",
                                           "key": "human_resource_id",
                                           # Dispatcher doesn't need to Add/Edit HRs, just Link
                                           "actuate": "hide",
                                           "autocomplete": "name",
                                           "autodelete": False,
                                          },
                       # Affected Persons
                       pr_person={"link": "irs_ireport_person",
                                  "joinby": "ireport_id",
                                  "key": "person_id",
                                  "actuate": "link",
                                  #"actuate": "embed",
                                  #"widget": S3AddPersonWidget2(),
                                  "autodelete": False,
                                 },
                      )

        ireport_id = S3ReusableField("ireport_id", "reference %s" % tablename,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db,
                                                              "irs_ireport.id",
                                                              self.irs_ireport_represent)),
                                     represent = self.irs_ireport_represent,
                                     label = T("Incident"),
                                     ondelete = "CASCADE")

        # Custom Methods
        set_method("irs", "ireport",
                   method = "dispatch",
                   action=self.irs_dispatch)

        set_method("irs", "ireport",
                   method = "timeline",
                   action = self.irs_timeline)

        set_method("irs", "ireport",
                   method = "ushahidi",
                   action = self.irs_ushahidi_import)

        if settings.has_module("fire"):
            create_next = URL(args=["[id]", "human_resource"])
        else:
            create_next = URL(args=["[id]", "image"])

        configure("irs_ireport",
                  create_next = create_next,
                  create_onaccept = self.ireport_onaccept,
                  update_next = URL(args=["[id]", "update"])
                  )

        # -----------------------------------------------------------
        # Affected Persons
        tablename = "irs_ireport_person"
        define_table(tablename,
                     ireport_id(),
                     self.pr_person_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return dict(irs_ireport_id = ireport_id,
                    irs_incident_type_opts = irs_incident_type_opts,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
            - used by events module
                    & legacy assess & impact modules
        """
        ireport_id = S3ReusableField("ireport_id", "integer",
                                     readable=False, writable=False)
        return Storage(irs_ireport_id = ireport_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_icategory_onvalidation(form):
        """
            Incident Category Validation:
                Prevent Duplicates

            Done here rather than in .requires to maintain the dropdown.
        """

        db = current.db
        table = db.irs_icategory

        category, error = IS_NOT_ONE_OF(db, "irs_icategory.code")(form.vars.code)
        if error:
            form.errors.code = error

        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_ireport_represent(id, row=None):
        """
            Represent an Incident Report via it's name
        """

        if row:
            return row.name
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.irs_ireport
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def ireport_onaccept(form):
        """
            Assign the appropriate vehicle & on-shift team to the incident
            @ToDo: Specialist teams
            @ToDo: Make more generic (currently Porto-specific)
        """

        settings = current.deployment_settings

        if settings.has_module("fire") and settings.has_module("vehicle"):
            pass
        else:
            # Not supported!
            return

        db = current.db
        s3db = current.s3db
        vars = form.vars
        ireport = vars.id
        category = vars.category
        if category == "1100":
            # Fire
            types = ["VUCI", "ABSC"]
        elif category == "6102":
            # Hazmat
            types = ["VUCI", "VCOT"]
        elif category == "8201":
            # Rescue
            types = ["VLCI", "ABSC"]
        else:
            types = ["VLCI"]

        # 1st unassigned vehicle of the matching type
        # @ToDo: Filter by Org/Base
        # @ToDo: Filter by those which are under repair (asset_log)
        table = s3db.irs_ireport_vehicle
        stable = s3db.org_site
        atable = s3db.asset_asset
        vtable = s3db.vehicle_vehicle
        ftable = s3db.fire_station
        fvtable = s3db.fire_station_vehicle
        for type in types:
            query = (atable.type == s3db.asset_types["VEHICLE"]) & \
                    (vtable.type == type) & \
                    (vtable.asset_id == atable.id) & \
                    (atable.deleted == False) & \
                    ((table.id == None) | \
                     (table.closed == True) | \
                     (table.deleted == True))
            left = table.on(atable.id == table.asset_id)
            vehicle = db(query).select(atable.id,
                                       left=left,
                                       limitby=(0, 1)).first()
            if vehicle:
                vehicle = vehicle.id
                query = (vtable.asset_id == vehicle) & \
                        (fvtable.vehicle_id == vtable.id) & \
                        (ftable.id == fvtable.station_id) & \
                        (stable.id == ftable.site_id)
                site = db(query).select(stable.id,
                                        limitby=(0, 1)).first()
                if site:
                    site = site.id
                table.insert(ireport_id=ireport,
                             asset_id=vehicle,
                             site_id=site)
                if settings.has_module("hrm"):
                    # Assign 1st 5 human resources on-shift
                    # @ToDo: We shouldn't assign people to vehicles automatically - this is done as people are ready
                    #        - instead we should simply assign people to the incident & then use a drag'n'drop interface to link people to vehicles
                    # @ToDo: Filter by Base
                    table = s3db.irs_ireport_vehicle_human_resource
                    htable = s3db.hrm_human_resource
                    on_shift = s3db.fire_staff_on_duty()
                    query = on_shift & \
                            ((table.id == None) | \
                             (table.closed == True) | \
                             (table.deleted == True))
                    left = table.on(htable.id == table.human_resource_id)
                    people = db(query).select(htable.id,
                                              left=left,
                                              limitby=(0, 5))
                    # @ToDo: Find Ranking person to be incident commander
                    leader = people.first()
                    if leader:
                        leader = leader.id
                    for person in people:
                        if person.id == leader.id:
                            table.insert(ireport_id=ireport,
                                         asset_id=vehicle,
                                         human_resource_id=person.id,
                                         incident_commander=True)
                        else:
                            table.insert(ireport_id=ireport,
                                         asset_id=vehicle,
                                         human_resource_id=person.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_dispatch(r, **attr):
        """
            Send a Dispatch notice from an Incident Report
            - this will be formatted as an OpenGeoSMS
        """

        if r.representation == "html" and \
           r.name == "ireport" and r.id and not r.component:

            T = current.T
            msg = current.msg

            record = r.record
            id = record.id

            contact = ""
            if record.contact:
                contact = "\n%s: %s" (T("Contact"),
                                      record.contact)
            message = ""
            if record.message:
                message = "\n%s" % record.message
            text = "SI#%s\n%s%s%s" % (id,
                                   record.name,
                                   contact,
                                   message)
            text += "\nSend help to see how to respond!"

            # Encode the message as an OpenGeoSMS
            message = msg.prepare_opengeosms(record.location_id,
                                             code="ST",
                                             map="google",
                                             text=text)

            # URL to redirect to after message sent
            url = URL(c="irs",
                      f="ireport",
                      args=r.id)

            # Create the form
            opts = dict(
                    type="SMS",
                    # @ToDo: deployment_setting
                    subject = T("Deployment Request"),
                    message = message,
                    url = url,
                    #formid = r.id
                )
            # Pre-populate the recipients list if we can
            # @ToDo: Check that we have valid contact details
            #        - slower, but useful to fail early if we need to
            s3db = current.s3db
            if current.deployment_settings.get_irs_vehicle():
                # @ToDo: This workflow requires more work
                #        - no ic defined yet in this case
                table = s3db.irs_ireport_vehicle_human_resource
            else:
                table = s3db.irs_ireport_human_resource
            htable = s3db.hrm_human_resource
            ptable = s3db.pr_person
            query = (table.ireport_id == id) & \
                    (table.deleted == False) & \
                    (table.human_resource_id == htable.id) & \
                    (htable.person_id == ptable.id)
            recipients = current.db(query).select(table.incident_commander,
                                                  ptable.pe_id)
            if not recipients:
                # Provide an Autocomplete the select the person to send the notice to
                opts["recipient_type"] = "pr_person"
            elif len(recipients) == 1:
                # Send to this person
                opts["recipient"] = recipients.first()["pr_person"].pe_id
            else:
                # Send to the Incident Commander
                ic = False
                for row in recipients:
                    if row["irs_ireport_human_resource"].incident_commander == True:
                        opts["recipient"] = row["pr_person"].pe_id
                        ic = True
                        break
                if not ic:
                    # Provide an Autocomplete the select the person to send the notice to
                    opts["recipient_type"] = "pr_person"
            output = msg.compose(**opts)

            # Maintain RHeader for consistency
            if attr.get("rheader"):
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = T("Send Dispatch Update")
            current.response.view = "msg/compose.html"
            return output

        else:
            raise HTTP(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_timeline(r, **attr):
        """
            Display the Incidents on a Simile Timeline

            http://www.simile-widgets.org/wiki/Reference_Documentation_for_Timeline

            @ToDo: Play button
            http://www.simile-widgets.org/wiki/Timeline_Moving_the_Timeline_via_Javascript
        """

        if r.representation == "html" and r.name == "ireport":

            T = current.T
            db = current.db
            s3db = current.s3db
            request = current.request
            response = current.response
            s3 = response.s3

            itable = s3db.doc_image
            dtable = s3db.doc_document

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % request.application)

            # Add our control script
            if s3.debug:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.js" % request.application)
            else:
                s3.scripts.append("/%s/static/scripts/S3/s3.timeline.min.js" % request.application)

            # Add our data
            # @ToDo: Make this the initial data & then collect extra via REST with a stylesheet
            # add in JS using S3.timeline.eventSource.addMany(events) where events is a []
            if r.record:
                # Single record
                rows = [r.record]
            else:
                # Multiple records
                # @ToDo: Load all records & sort to closest in time
                # http://stackoverflow.com/questions/7327689/how-to-generate-a-sequence-of-future-datetimes-in-python-and-determine-nearest-d
                r.resource.load(limit=2000)
                rows = r.resource._rows

            data = {"dateTimeFormat": "iso8601",
                    }

            now = request.utcnow
            tl_start = tl_end = now
            events = []
            for row in rows:
                # Dates
                start = row.datetime or ""
                if start:
                    if start < tl_start:
                        tl_start = start
                    if start > tl_end:
                        tl_end = start
                    start = start.isoformat()
                end = row.expiry or ""
                if end:
                    if end > tl_end:
                        tl_end = end
                    end = end.isoformat()
                # Image
                # Just grab the first one for now
                query = (itable.deleted == False) & \
                        (itable.doc_id == row.doc_id)
                image = db(query).select(itable.url,
                                         limitby=(0, 1)).first()
                if image:
                    image = image.url or ""
                # URL
                link = URL(args=[row.id])
                events.append({"start": start,
                               "end": end,
                               "title": row.name,
                               "caption": row.message or "",
                               "description": row.message or "",
                               "image": image or "",
                               "link": link or "",
                               # @ToDo: Colour based on Category (More generically: Resource or Resource Type)
                               #"color" : "blue',
                            })
            data["events"] = events
            data = json.dumps(data, separators=SEPARATORS)

            code = "".join((
'''S3.timeline.data=''', data, '''
S3.timeline.tl_start="''', tl_start.isoformat(), '''"
S3.timeline.tl_end="''', tl_end.isoformat(), '''"
S3.timeline.now="''', now.isoformat(), '''"
'''))

            # Control our code in static/scripts/S3/s3.timeline.js
            s3.js_global.append(code)

            # Create the DIV
            item = DIV(_id="s3timeline", _class="s3-timeline")

            output = dict(item = item)

            # Maintain RHeader for consistency
            if attr.get("rheader"):
                rheader = attr["rheader"](r)
                if rheader:
                    output["rheader"] = rheader

            output["title"] = T("Incident Timeline")
            response.view = "timeline.html"
            return output

        else:
            raise HTTP(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_ushahidi_import(r, **attr):
        """
            Import Incident Reports from Ushahidi

            @ToDo: Deployment setting for Ushahidi instance URL
        """

        T = current.T
        auth = current.auth
        request = current.request
        response = current.response
        session = current.session

        # Method is only available to Admins
        system_roles = session.s3.system_roles
        ADMIN = system_roles.ADMIN
        if not auth.s3_has_role(ADMIN):
            auth.permission.fail()

        if r.representation == "html" and \
           r.name == "ireport" and not r.component and not r.id:

            url = r.get_vars.get("url", "http://")

            title = T("Import Incident Reports from Ushahidi")

            form = FORM(
                    TABLE(
                        TR(
                            TH(B("%s: " % T("URL"))),
                            INPUT(_type="text", _name="url", _size="100",
                                  _value=url,
                                  requires=[IS_URL(), IS_NOT_EMPTY()]),
                            TH(DIV(SPAN("*", _class="req",
                                        _style="padding-right: 5px;")))
                            ),
                        TR(
                            TD(B("%s: " % T("Ignore Errors?"))),
                            TD(INPUT(_type="checkbox", _name="ignore_errors",
                                     _id="ignore_errors"))
                            ),
                        TR("", INPUT(_type="submit", _value=T("Import")))
                        ))

            rheader = DIV(P("%s: http://wiki.ushahidi.com/doku.php?id=ushahidi_api" % \
                                T("API is documented here")),
                          P("%s URL: http://ushahidi.my.domain/api?task=incidents&by=all&resp=xml&limit=1000" % \
                                T("Example")))

            output = dict(title=title,
                          form=form,
                          rheader=rheader)

            if form.accepts(request.vars, session):

                # "Exploit" the de-duplicator hook to count import items
                import_count = [0]
                def count_items(job, import_count=import_count):
                    if job.tablename == "irs_ireport":
                        import_count[0] += 1
                current.s3db.configure("irs_report", deduplicate=count_items)

                vars = form.vars
                ushahidi_url = vars.url

                import os
                stylesheet = os.path.join(request.folder, "static", "formats",
                                          "ushahidi", "import.xsl")

                if os.path.exists(stylesheet) and ushahidi_url:
                    ignore_errors = vars.get("ignore_errors", None)
                    try:
                        success = r.resource.import_xml(ushahidi_url,
                                                        stylesheet=stylesheet,
                                                        ignore_errors=ignore_errors)
                    except:
                        import sys
                        e = sys.exc_info()[1]
                        response.error = e
                    else:
                        if success:
                            count = import_count[0]
                            if count:
                                response.confirmation = "%s %s" % \
                                    (import_count[0],
                                     T("reports successfully imported."))
                            else:
                                response.information = T("No reports available.")
                        else:
                            response.error = self.error


            response.view = "create.html"
            return output

        else:
            raise HTTP(405, current.ERROR.BAD_METHOD)

# =============================================================================
class S3IRSResponseModel(S3Model):
    """
        Tables used when responding to Incident Reports
        - with HRMs &/or Vehicles

        Currently this has code specific to Porto Firefighters

        @ToDo: Replace with Deployment module
    """

    names = ("irs_ireport_human_resource",
             "irs_ireport_vehicle",
             "irs_ireport_vehicle_human_resource"
             )

    def model(self):

        T = current.T
        db = current.db

        human_resource_id = self.hrm_human_resource_id
        ireport_id = self.irs_ireport_id

        define_table = self.define_table
        configure = self.configure

        settings = current.deployment_settings
        hrm = settings.get_hrm_show_staff()
        vol = settings.has_module("vol")
        if hrm and not vol:
            hrm_label = T("Staff")
        elif vol and not hrm:
            hrm_label = T("Volunteer")
        else:
            hrm_label = T("Staff/Volunteer")

        def response_represent(opt):
            if opt is None:
                return current.messages["NONE"]
            elif opt:
                return T("Yes")
            else:
                return T("No")

        # ---------------------------------------------------------------------
        # Staff assigned to an Incident
        #
        msg_enabled = settings.has_module("msg")
        tablename = "irs_ireport_human_resource"
        define_table(tablename,
                     ireport_id(),
                     # @ToDo: Limit Staff to those which are not already assigned to an Incident
                     human_resource_id(label = hrm_label,
                                       # Simple dropdown is faster for a small team
                                       #widget=None,
                                       #comment=None,
                                       ),
                     Field("incident_commander", "boolean",
                           default = False,
                           label = T("Incident Commander"),
                           represent = lambda incident_commander: \
                                       (T("No"),
                                       T("Yes"))[incident_commander == True]),
                     Field("response", "boolean",
                           default = None,
                           label = T("Able to Respond?"),
                           writable = msg_enabled,
                           readable = msg_enabled,
                           represent = response_represent,
                           ),
                     s3_comments("reply",
                                 label = T("Reply Message"),
                                 writable = msg_enabled,
                                 readable = msg_enabled
                                 ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields=["id",
                               "human_resource_id",
                               "incident_commander",
                               "response",
                               "reply",
                              ])

        if not settings.has_module("vehicle"):
            return Storage()

        # ---------------------------------------------------------------------
        # Vehicles assigned to an Incident
        #
        asset_id = self.asset_asset_id
        tablename = "irs_ireport_vehicle"
        define_table(tablename,
                     ireport_id(),
                     asset_id(label = T("Vehicle"),
                              # Limit Vehicles to those which are not already assigned to an Incident
                              requires = self.irs_vehicle_requires,
                              comment = S3PopupLink(c = "vehicle",
                                                    f = "vehicle",
                                                    label = T("Add Vehicle"),
                                                    tooltip = T("If you don't see the vehicle in the list, you can add a new one by clicking link 'Add Vehicle'."),
                                                    ),
                              ),
                     s3_datetime("datetime",
                                 default = "now",
                                 future = 0,
                                 label = T("Dispatch Time"),
                                 ),
                     self.super_link("site_id", "org_site",
                                     label = T("Fire Station"),
                                     readable = True,
                                     # Populated from fire_station_vehicle
                                     #writable = True
                                     ),
                     self.gis_location_id(label = T("Destination"),
                                          ),
                     Field("closed",
                           # @ToDo: Close all assignments when Incident closed
                           readable=False,
                           writable=False),
                     Field.Method("minutes",
                                  self.irs_ireport_vehicle_minutes),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename, extra_fields = ["datetime"])

        # ---------------------------------------------------------------------
        # Which Staff are assigned to which Vehicle?
        #
        tablename = "irs_ireport_vehicle_human_resource"
        define_table(tablename,
                     ireport_id(),
                     # @ToDo: Limit Staff to those which are not already assigned to an Incident
                     human_resource_id(label = hrm_label,
                                       # Simple dropdown is faster for a small team
                                       widget=None,
                                       comment=None,
                                       ),
                     asset_id(label=T("Vehicle"),
                              # @ToDo: Limit to Vehicles which are assigned to this Incident
                              requires = IS_EMPTY_OR(
                                            IS_ONE_OF(db, "asset_asset.id",
                                                      self.asset_represent,
                                                      filterby="type",
                                                      filter_opts=(1,),
                                                      sort=True)),
                              comment = S3PopupLink(c = "vehicle",
                                                    f = "vehicle",
                                                    label = T("Add Vehicle"),
                                                    tooltip = T("If you don't see the vehicle in the list, you can add a new one by clicking link 'Add Vehicle'."),
                                                    ),
                              ),
                     Field("closed",
                           # @ToDo: Close all assignments when Incident closed
                           readable=False,
                           writable=False),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage(
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_vehicle_requires():
        """
            Populate the dropdown widget for responding to an Incident Report
            based on those vehicles which aren't already on-call
        """

        # Vehicles are a type of Asset
        s3db = current.s3db
        table = s3db.asset_asset
        ltable = s3db.irs_ireport_vehicle
        asset_represent = s3db.asset_asset_id.represent

        # Filter to Vehicles which aren't already on a call
        # @ToDo: Filter by Org/Base
        # @ToDo: Filter out those which are under repair
        query = (table.type == s3db.asset_types["VEHICLE"]) & \
                (table.deleted == False) & \
                ((ltable.id == None) | \
                 (ltable.closed == True) | \
                 (ltable.deleted == True))
        left = ltable.on(table.id == ltable.asset_id)
        requires = IS_EMPTY_OR(IS_ONE_OF(current.db(query),
                                         "asset_asset.id",
                                         asset_represent,
                                         left=left,
                                         sort=True))
        return requires

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_ireport_vehicle_minutes(row):

        if hasattr(row, "irs_ireport_vehicle"):
            row = "irs_ireport_vehicle"
        if hasattr(row, "datetime") and row.datetime:
            return int((current.request.utcnow - row.datetime) / 60)
        else:
            return 0

# =============================================================================
def irs_rheader(r, tabs=[]):
    """ Resource component page header """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings
        hrm_label = T("Responder(s)")

        tabs = [(T("Report Details"), None),
                (T("Photos"), "image"),
                (T("Documents"), "document"),
                (T("Affected Persons"), "person"),
                ]
        if settings.get_irs_vehicle():
            tabs.append((T("Vehicles"), "vehicle"))
        tabs.append((hrm_label, "human_resource"))
        tabs.append((T("Tasks"), "task"))
        if settings.has_module("msg"):
            tabs.append((T("Dispatch"), "dispatch"))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if r.name == "ireport":
            report = r.record

            table = r.table

            datetime = table.datetime.represent(report.datetime)
            expiry = table.datetime.represent(report.expiry)
            location = table.location_id.represent(report.location_id)
            category = table.category.represent(report.category) or ""
            contact = ""
            if report.person:
                if report.contact:
                    contact = "%s (%s)" % (report.person, report.contact)
                else:
                    contact = report.person
            elif report.contact:
                contact = report.contact
            if contact:
                contact = DIV(TH("%s: " % T("Contact")), TD(contact))

            #create_request = A(T("Create Request"),
            #                   _class="action-btn s3_add_resource_link",
            #                   _href=URL(c="req", f="req",
            #                             args="create",
            #                             vars={"format":"popup",
            #                                   "caller":"irs_ireport"}),
            #                  _title=T("Add Request"))
            #create_task = A(T("Create Task"),
            #                _class="action-btn s3_add_resource_link",
            #                _href=URL(c="project", f="task",
            #                          args="create",
            #                          vars={"format":"popup",
            #                                "caller":"irs_ireport"}),
            #                _title=T("Create Task"))
            rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label), report.name,
                                TH("%s: " % table.datetime.label), datetime,
                                ),
                            TR(
                                TH("%s: " % table.category.label), category,
                                TH("%s: " % table.expiry.label), expiry,
                                ),
                            TR(
                                TH("%s: " % table.location_id.label), location,
                                contact,
                                ),
                            TR(
                                TH("%s: " % table.message.label), TD(report.message or "",
                                                                     _colspan=3),
                                )
                            ),
                          #DIV(P(), create_request, " ", create_task, P()),
                          rheader_tabs)

        return rheader

    else:
        return None

# END =========================================================================
