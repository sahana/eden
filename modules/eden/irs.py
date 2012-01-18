# -*- coding: utf-8 -*-

""" Sahana Eden IRS Model

    @author: Fran Boon <fran[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3IRSModel",
           "S3IRSResponseModel",
           "irs_rheader"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3IRSModel(S3Model):

    names = ["irs_icategory",
             "irs_ireport",
             "irs_ireport_id"]

    def model(self):

        db = current.db
        T = current.T
        request = current.request
        s3 = current.response.s3
        settings = current.deployment_settings

        location_id = self.gis_location_id

        datetime_represent = S3DateTime.datetime_represent

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
        table = self.define_table(tablename,
                                  Field("code", label = T("Category"),
                                        requires = IS_IN_SET_LAZY(lambda: \
                                            sort_dict_by_values(irs_incident_type_opts)),
                                        represent = lambda opt: \
                                            irs_incident_type_opts.get(opt, opt)),
                                  *s3.meta_fields())

        self.configure(tablename,
                       onvalidation=self.irs_icategory_onvalidation,
                       list_fields=[ "code" ])

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
        table = self.define_table(tablename,
                                  self.super_link("sit_id", "sit_situation"),
                                  self.super_link("doc_id", "doc_entity"),
                                  Field("name", label = T("Short Description"),
                                        requires = IS_NOT_EMPTY()),
                                  Field("message", "text", label = T("Message"),
                                        represent = lambda text: \
                                            s3_truncate(text, length=48, nice=True)),
                                  Field("category", label = T("Category"),
                                        # The full set available to Admins & Imports/Exports
                                        # (users use the subset by over-riding this in the Controller)
                                        requires = IS_NULL_OR(IS_IN_SET_LAZY(lambda: \
                                            sort_dict_by_values(irs_incident_type_opts))),
                                        # Use this instead if a simpler set of Options required
                                        #requires = IS_NULL_OR(IS_IN_SET(irs_incident_type_opts)),
                                        represent = lambda opt: \
                                            irs_incident_type_opts.get(opt, opt)),
                                  # Better to use a plain text field than to clutter the PR
                                  Field("person",
                                        readable = False,
                                        writable = False,
                                        label = T("Reporter Name"),
                                        comment = (T("At/Visited Location (not virtual)"))),
                                  Field("contact",
                                        readable = False,
                                        writable = False,
                                        label = T("Contact Details")),
                                  Field("datetime", "datetime",
                                        default = request.utcnow,
                                        label = T("Date/Time of Alert"),
                                        widget = S3DateTimeWidget(future=0),
                                        represent = lambda val: datetime_represent(val, utc=True),
                                        requires = [IS_NOT_EMPTY(),
                                                    IS_UTC_DATETIME(allow_future=False)]),
                                  Field("expiry", "datetime",
                                        #readable = False,
                                        #writable = False,
                                        label = T("Expiry Date/Time"),
                                        widget = S3DateTimeWidget(past=0),
                                        represent = lambda val: datetime_represent(val, utc=True),
                                        requires = IS_NULL_OR(IS_UTC_DATETIME())
                                       ),
                                  location_id(),
                                  Field("verified", "boolean",    # Ushahidi-compatibility
                                        # We don't want these visible in Create forms
                                        # (we override in Update forms in controller)
                                        readable = False,
                                        writable = False,
                                        label = T("Verified?"),
                                        represent = lambda verified: \
                                              (T("No"),
                                               T("Yes"))[verified == True]),
                                  # @ToDo: Move this to Events?
                                  # Then display here as a Virtual Field
                                  Field("dispatch", "datetime",
                                        # We don't want these visible in Create forms
                                        # (we override in Update forms in controller)
                                        readable = False,
                                        writable = False,
                                        label = T("Date/Time of Dispatch"),
                                        widget = S3DateTimeWidget(future=0),
                                        requires = IS_EMPTY_OR(IS_UTC_DATETIME(allow_future=False))),
                                  Field("closed", "boolean",
                                        # We don't want these visible in Create forms
                                        # (we override in Update forms in controller)
                                        default = False,
                                        readable = False,
                                        writable = False,
                                        label = T("Closed?"),
                                        represent = lambda closed: \
                                              (T("No"),
                                               T("Yes"))[closed == True]),
                                  s3.comments(),
                                  *s3.meta_fields())

        # CRUD strings
        ADD_INC_REPORT = T("Add Incident Report")
        LIST_INC_REPORTS = T("List Incident Reports")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_INC_REPORT,
            title_display = T("Incident Report Details"),
            title_list = LIST_INC_REPORTS,
            title_update = T("Edit Incident Report"),
            title_search = T("Search Incident Reports"),
            subtitle_create = T("Add New Incident Report"),
            subtitle_list = T("Incident Reports"),
            label_list_button = LIST_INC_REPORTS,
            label_create_button = ADD_INC_REPORT,
            label_delete_button = T("Delete Incident Report"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report deleted"),
            msg_list_empty = T("No Incident Reports currently registered"))

        self.configure(tablename,
                       super_entity = ("sit_situation", "doc_entity"),
                       # Open tabs after creation
                       create_next = URL(args=["[id]", "update"]),
                       update_next = URL(args=["[id]", "update"]),
                       list_fields = ["id",
                                      "name",
                                      "category",
                                      "datetime",
                                      "location_id",
                                      #"organisation_id",
                                      "verified",
                                      "message",
                                    ])

        # Components
        # Tasks
        self.add_component("project_task",
                           irs_ireport=Storage(link="project_task_ireport",
                                               joinby="ireport_id",
                                               key="task_id",
                                               actuate="replace",
                                               autocomplete="name",
                                               autodelete=False))

        # Vehicles
        self.add_component("asset_asset",
                           irs_ireport=Storage(
                                link="irs_ireport_vehicle",
                                joinby="ireport_id",
                                key="asset_id",
                                name="vehicle",
                                # Dispatcher doesn't need to Add/Edit records, just Link
                                actuate="link",
                                autocomplete="name",
                                autodelete=False))

        if settings.has_module("vehicle"):
            link_table = "irs_ireport_vehicle_human_resource"
        else:
            link_table = "irs_ireport_human_resource"
        self.add_component("hrm_human_resource",
                           irs_ireport=Storage(
                                    link=link_table,
                                    joinby="ireport_id",
                                    key="human_resource_id",
                                    # Dispatcher doesn't need to Add/Edit records, just Link
                                    actuate="link",
                                    autocomplete="name",
                                    autodelete=False
                                )
                            )

        ireport_id = S3ReusableField("ireport_id", table,
                                     requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                     "irs_ireport.id",
                                                                     "%(name)s")),
                                     represent = lambda id: \
                                        (id and [db.irs_ireport[id].name] or [NONE])[0],
                                     label = T("Incident"),
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Custom Methods
        self.set_method("irs_ireport",
                        method="dispatch",
                        action=self.irs_dispatch)

        self.set_method("irs_ireport",
                        method="timeline",
                        action=self.irs_timeline)

        self.set_method("irs_ireport",
                        method="ushahidi",
                        action=self.irs_ushahidi_import)

        self.configure("irs_ireport",
                       # Porto-specific currently
                       #create_onaccept=self.ireport_onaccept,
                       #create_next=URL(args=["[id]", "human_resource"]),
                       update_next=URL(args=["[id]", "update"])
                       )

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            irs_ireport_id = ireport_id,
            irs_incident_type_opts = irs_incident_type_opts
            )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
            - used by events module
                    & legacy assess & impact modules
        """
        dummy = S3ReusableField("ireport_id", "integer",
                                readable=False, writable=False)
        return Storage(irs_ireport_id = dummy)

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
    def ireport_onaccept(form):
        """
            Assign the appropriate vehicle & on-shift team to the incident
            @ToDo: Specialist teams
            @ToDo: Make more generic (currently Porto-specific)
        """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        settings = current.deployment_settings

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
        current.manager.load("fire_station_vehicle")
        table = s3db.irs_ireport_vehicle
        atable = s3db.asset_asset
        vtable = s3db.vehicle_vehicle
        for type in types:
            query = (atable.type == s3.asset.ASSET_TYPE_VEHICLE) & \
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
                current.manager.load("vehicle_vehicle")
                vehicle = vehicle.id
                query = (vtable.asset_id == vehicle) & \
                        (db.fire_station_vehicle.vehicle_id == vtable.id) & \
                        (db.fire_station.id == db.fire_station_vehicle.station_id) & \
                        (db.org_site.id == db.fire_station.site_id)
                site = db(query).select(db.org_site.id,
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
                    on_shift = response.s3.fire_staff_on_duty()
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

        T = current.T
        msg = current.msg
        response = current.response

        if r.representation == "html" and \
           r.name == "ireport" and r.id and not r.component:

            record = r.record
            text = "%s %s:%s; %s" % (record.name,
                                     T("Contact"),
                                     record.contact,
                                     record.message)

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
            output = msg.compose(type="SMS",
                                 recipient_type = "pr_person",
                                 message = message,
                                 url = url)

            # Maintain RHeader for consistency
            if "rheader" in attr:
                output["rheader"] = attr["rheader"](r)

            output["title"] = T("Send Dispatch Update")
            response.view = "msg/compose.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

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

            import gluon.contrib.simplejson as json

            T = current.T
            db = current.db
            s3db = current.s3db
            request = current.request
            response = current.response
            session = current.session
            s3 = response.s3
            now = request.utcnow

            itable = s3db.doc_image
            dtable = s3db.doc_document

            # Create the DIV
            item = DIV(_id="s3timeline", _style="height: 400px; border: 1px solid #aaa; font-family: Trebuchet MS, sans-serif; font-size: 85%;")

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

            data = {'dateTimeFormat': 'iso8601',
                    'events': []
                    }

            tl_start = now
            tl_end = now
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
                events.append({'start': start,
                                       'end': end,
                                       'title': row.name,
                                       'caption': row.message or "",
                                       'description': row.message or "",
                                       'image': image or "",
                                       'link': link or ""
                                       # @ToDo: Colour based on Category (More generically: Resource or Resource Type)
                                       #'color' : 'blue'
                                    })
            data["events"] = events
            data = json.dumps(data)

            data = """
S3.timeline = Object();
S3.timeline.data = %s;""" % data
            s3.js_global.append(data)

            # Add core Simile Code
            s3.scripts.append("/%s/static/scripts/simile/timeline/timeline-api.js" % request.application)

            # Add our code to instantiate Simile
            # //theme.autoWidth = true;
            code = "".join(("""
S3.timeline.onLoad = function() {
    var tl_el = document.getElementById("s3timeline");
    S3.timeline.eventSource = new Timeline.DefaultEventSource();
    var theme = Timeline.ClassicTheme.create();
    theme.timeline_start = new Date('""", tl_start.isoformat(), """');
    theme.timeline_stop  = new Date('""", tl_end.isoformat(), """');
    theme.event.bubble.width = 320;
    theme.event.bubble.height = 180;
    var now = Timeline.DateTime.parseIso8601DateTime('""", now.isoformat(), """')
    var bandInfos = [
        Timeline.createBandInfo({
            width:          '90%',
            intervalUnit:   Timeline.DateTime.MONTH,
            intervalPixels: 140,
            eventSource:    S3.timeline.eventSource,
            date:           now,
            theme:          theme
        }),
        Timeline.createBandInfo({
            overview:       true,
            width:          '10%',
            intervalUnit:   Timeline.DateTime.YEAR,
            intervalPixels: 200,
            eventSource:    S3.timeline.eventSource,
            date:           now
        })
    ];
    bandInfos[1].syncWith = 0;
    bandInfos[1].highlight = true;
    S3.timeline.tl = Timeline.create(tl_el, bandInfos, Timeline.HORIZONTAL);
    var url = '.';
    S3.timeline.eventSource.loadJSON(S3.timeline.data, url);
    S3.timeline.tl.layout();
}
S3.timeline.resizeTimerID = null;
S3.timeline.onResize = function() {
    if (S3.timeline.resizeTimerID == null) {
        S3.timeline.resizeTimerID = window.setTimeout(function() {
            S3.timeline.resizeTimerID = null;
            S3.timeline.tl.layout();
        }, 500);
    }
}"""))
            s3.js_global.append(code)
            s3.jquery_ready.append("""
$(window).load(function() {
    SimileAjax.History.enabled = false;
    S3.timeline.onLoad();
});
$(window).resize(function() {
    S3.timeline.onResize();
});""")

            output = dict(item = item)

            # Maintain RHeader for consistency
            if "rheader" in attr:
                output["rheader"] = attr["rheader"](r)

            title = T("Incident Timeline")
            output["title"] = title
            response.view = "timeline.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

    # -------------------------------------------------------------------------
    @staticmethod
    def irs_ushahidi_import(r, **attr):
        """
            Import Incident Reports from Ushahidi

            @ToDo: Deployment setting for Ushahidi instance URL
        """

        import os

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

            title = T("Incident Reports")
            subtitle = T("Import from Ushahidi Instance")

            form = FORM(TABLE(TR(
                        TH("URL: "),
                        INPUT(_type="text", _name="url", _size="100", _value=url,
                              requires=[IS_URL(), IS_NOT_EMPTY()]),
                        TH(DIV(SPAN("*", _class="req", _style="padding-right: 5px;")))),
                        TR(TD("Ignore Errors?: "),
                        TD(INPUT(_type="checkbox", _name="ignore_errors", _id="ignore_errors"))),
                        TR("", INPUT(_type="submit", _value=T("Import")))))

            label_list_btn = s3base.S3CRUD.crud_string(r.tablename, "title_list")
            list_btn = A(label_list_btn,
                         _href=r.url(method="", vars=None),
                         _class="action-btn")

            rheader = DIV(P("%s: http://wiki.ushahidi.com/doku.php?id=ushahidi_api" % T("API is documented here")),
                          P("%s URL: http://ushahidi.my.domain/api?task=incidents&by=all&resp=xml&limit=1000" % T("Example")))

            output = dict(title=title,
                          form=form,
                          subtitle=subtitle,
                          list_btn=list_btn,
                          rheader=rheader)

            if form.accepts(request.vars, session):

                # "Exploit" the de-duplicator hook to count import items
                import_count = [0]
                def count_items(job, import_count = import_count):
                    if job.tablename == "irs_ireport":
                        import_count[0] += 1
                self.configure("irs_report", deduplicate=count_items)

                ireports = r.resource
                ushahidi = form.vars.url

                ignore_errors = form.vars.get("ignore_errors", None)

                stylesheet = os.path.join(request.folder, "static", "formats",
                                          "ushahidi", "import.xsl")

                if os.path.exists(stylesheet) and ushahidi:
                    try:
                        success = ireports.import_xml(ushahidi,
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
                                response.flash = "%s %s" % (import_count[0],
                                                            T("reports successfully imported."))
                            else:
                                response.flash = T("No reports available.")
                        else:
                            response.error = self.error


            response.view = "create.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

# =============================================================================
class S3IRSResponseModel(S3Model):
    """
        Tables used when responding to Incident Reports
        - with HRMs &/or Vehicles

        Currently this has code specific to Porto Firefighters

        @ToDo: Move these to Events module?
               - the response shouldn't live within the reporting system?
    """

    names = ["irs_ireport_human_resource",
             "irs_ireport_vehicle",
             "irs_ireport_vehicle_human_resource"]

    def model(self):

        db = current.db
        T = current.T
        request = current.request
        s3 = current.response.s3
        settings = current.deployment_settings

        human_resource_id = self.hrm_human_resource_id
        location_id = self.gis_location_id
        ireport_id = self.irs_ireport_id

        # ---------------------------------------------------------------------
        # Staff assigned to an Incident
        #
        if settings.has_module("hrm"):
            tablename = "irs_ireport_human_resource"
            table = self.define_table(tablename,
                                      ireport_id(),
                                      # Simple dropdown is faster for a small team
                                      human_resource_id(widget=None),
                                      Field("incident_commander", "boolean",
                                            default = False,
                                            label = T("Incident Commander"),
                                            represent = lambda incident_commander: \
                                                    (T("No"),
                                                     T("Yes"))[incident_commander == True]),
                                     *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Vehicles assigned to an Incident
        #
        if settings.has_module("vehicle"):
            table = self.asset_asset
            asset_id = s3.asset_id
            asset_represent = s3.asset_represent
            tablename = "irs_ireport_vehicle"
            table = self.define_table(tablename,
                                      ireport_id(),
                                      asset_id(
                                            label = T("Vehicle"),
                                            requires=self.irs_vehicle_requires
                                        ),
                                      Field("datetime", "datetime",
                                            label=T("Dispatch Time"),
                                            widget = S3DateTimeWidget(future=0),
                                            requires = IS_EMPTY_OR(IS_UTC_DATETIME(allow_future=False)),
                                            default = request.utcnow),
                                      self.super_link("site_id", "org_site"),
                                      location_id(label=T("Destination")),
                                      Field("closed",
                                            # @ToDo: Close all assignments when Incident closed
                                            readable=False,
                                            writable=False),
                                      s3.comments(),
                                      *s3.meta_fields())

            # Field options
            table.site_id.label = T("Fire Station")
            table.site_id.readable = True
            # Populated from fire_station_vehicle
            #table.site_id.writable = True

            # ---------------------------------------------------------------------
            # Which Staff are assigned to which Vehicle?
            #
            if settings.has_module("hrm"):
                hr_represent = self.hrm_hr_represent
                tablename = "irs_ireport_vehicle_human_resource"
                table = self.define_table(tablename,
                                          ireport_id(),
                                          # Simple dropdown is faster for a small team
                                          human_resource_id(represent=hr_represent,
                                                            requires = IS_ONE_OF(db,
                                                                                 "hrm_human_resource.id",
                                                                                 hr_represent,
                                                                                 #orderby="pr_person.first_name"
                                                                                 ),
                                                            widget=None),
                                          asset_id(label = T("Vehicle")),
                                          Field("closed",
                                                # @ToDo: Close all assignments when Incident closed
                                                readable=False,
                                                writable=False),
                                          *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
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

        db = current.db
        s3db = current.s3db
        s3 = response = current.response.s3

        # Vehicles are a type of Asset
        table = s3db.asset_asset
        ltable = s3db.irs_ireport_vehicle

        # Filter to Vehicles which aren't already on a call
        # @ToDo: Filter by Org/Base
        # @ToDo: Filter out those which are under repair
        query = (table.type == s3.asset.ASSET_TYPE_VEHICLE) & \
                (table.deleted == False) & \
                ((ltable.id == None) | \
                 (ltable.closed == True) | \
                 (ltable.deleted == True))
        left = ltable.on(table.id == ltable.asset_id)
        requires = IS_NULL_OR(IS_ONE_OF(db(query),
                                        "asset_asset.id",
                                        asset_represent,
                                        left=left,
                                        sort=True))
        return requires

# =============================================================================
def irs_rheader(r, tabs=[]):
    """ Resource component page header """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        T = current.T
        s3db = current.s3db
        #s3 = current.response.s3
        settings = current.deployment_settings

        tabs = [(T("Report Details"), None),
                (T("Photos"), "image"),
                (T("Documents"), "document"),
                (T("Vehicles"), "vehicle"),
                (T("Staff"), "human_resource"),
                (T("Tasks"), "task"),
                (T("Dispatch"), "dispatch"),
               ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if r.name == "ireport":
            report = r.record

            table = r.table

            datetime = table.datetime.represent(report.datetime)
            expiry = table.datetime.represent(report.expiry)
            location = table.location_id.represent(report.location_id)
            category = table.category.represent(report.category)
            contact = ""
            if report.person:
                if report.contact:
                    contact = "%s (%s)" % (report.person, report.contact)
                else:
                    contact = report.person
            elif report.contact:
                contact = report.contact

            #create_request = A(T("Create Request"),
            #                   _class="action-btn colorbox",
            #                   _href=URL(c="req", f="req",
            #                             args="create",
            #                             vars={"format":"popup",
            #                                   "caller":"irs_ireport"}),
            #                  _title=T("Add Request"))
            #create_task = A(T("Create Task"),
            #                _class="action-btn colorbox",
            #                _href=URL(c="project", f="task",
            #                          args="create",
            #                          vars={"format":"popup",
            #                                "caller":"irs_ireport"}),
            #                _title=T("Add Task"))
            rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label), report.name,
                                TH("%s: " % table.datetime.label), datetime,
                            TR(
                                TH("%s: " % table.category.label), category,
                                TH("%s: " % table.expiry.label), expiry,
                                ),
                            TR(
                                TH("%s: " % table.location_id.label), location,
                                TH("%s: " % T("Contact")), contact),
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
