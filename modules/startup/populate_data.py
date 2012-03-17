# -*- coding: utf-8 -*-

from gluon import *
request = current.request
reponse = current.response
session = current.session
db = current.db
T = current.T
deployment_settings = current.deployment_settings
manager = current.manager
gis = current.gis
auth = current.auth

from gluon.storage import Storage
import s3 as s3base
from s3.s3utils import *
import os

# 1st-run initialisation
# designed to be called from Crontab's @reboot
# however this isn't reliable (doesn't work on Win32 Service)
# so still in models for now...

# Deployments can change settings live via appadmin
populate = deployment_settings.get_base_prepopulate()
sysroles = auth.S3_SYSTEM_ROLES
if populate > 0:
    if populate & 1:

        # Load all Models to ensure all DB tables present
        manager.model.load_all_models()

        # Organization Registry
        table = db.org_sector
        if db(table).isempty():
            table.insert(
                abrv = T("Agriculture"),
                name = T("Agriculture")
            )
            table.insert(
                abrv = T("Camp"),
                name = T("Camp Coordination/Management")
            )
            table.insert(
                abrv = T("Recovery"),
                name = T("Early Recovery")
            )
            table.insert(
                abrv = T("Education"),
                name = T("Education")
            )
            cluster_shelter = table.insert(
                abrv = T("Shelter"),
                name = T("Emergency Shelter")
            )
            table.insert(
                abrv = T("Telecommunications"),
                name = T("Emergency Telecommunications")
            )
            table.insert(
                abrv = T("Health"),
                name = T("Health")
            )
            table.insert(
                abrv = T("Logistics"),
                name = T("Logistics")
            )
            cluster_nutrition = table.insert(
                abrv = T("Nutrition"),
                name = T("Nutrition")
            )
            table.insert(
                abrv = T("Protection"),
                name = T("Protection")
            )
            cluster_wash = table.insert(
                abrv = T("WASH"),
                name = T("Water Sanitation Hygiene")
            )
        table = db.org_subsector
        # Ensure that the sectors we defined are in the DB ready to be used as a FK
        db.commit()
        if db(table).isempty():
            table.insert(
                sector_id = cluster_shelter,
                abrv = T("Clothing")
            )
            table.insert(
                sector_id = cluster_shelter,
                abrv = T("Shelter")
            )
            table.insert(
                sector_id = cluster_nutrition,
                abrv = T("Cooking NFIs")
            )
            table.insert(
                sector_id = cluster_nutrition,
                abrv = T("Food Supply")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Aggravating factors")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Disease vectors")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Drainage")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Excreta disposal")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Hygiene NFIs")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Hygiene practice")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Solid waste")
            )
            table.insert(
                sector_id = cluster_wash,
                abrv = T("Water supply")
            )

        # Person Registry
        tablename = "pr_person"
        table = db[tablename]
        # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
        field = "first_name"
        db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
        field = "middle_name"
        db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
        field = "last_name"
        db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

        # Synchronisation
        table = db.sync_setting
        if db(table).isempty():
           table.insert(proxy="")

        # Incident Reporting System
        if deployment_settings.has_module("irs"):
            # Categories visible to ends-users by default
            table = db.irs_icategory
            if db(table).isempty():
                table.insert(code = "flood")
                table.insert(code = "geophysical.landslide")
                table.insert(code = "roadway.bridgeClosure")
                table.insert(code = "roadway.roadwayClosure")
                table.insert(code = "other.buildingCollapsed")
                table.insert(code = "other.peopleTrapped")
                table.insert(code = "other.powerFailure")

        # Messaging Module
        if deployment_settings.has_module("msg"):
            table = db.msg_email_settings
            if db(table).isempty():
                table.insert(
                    inbound_mail_server = "imap.gmail.com",
                    inbound_mail_type = "imap",
                    inbound_mail_ssl = True,
                    inbound_mail_port = 993,
                    inbound_mail_username = "username",
                    inbound_mail_password = "password",
                    inbound_mail_delete = False,
                    #outbound_mail_server = "mail:25",
                    #outbound_mail_from = "demo@sahanafoundation.org",
                )
            # Need entries for the Settings/1/Update URLs to work
            table = db.msg_setting
            if db(table).isempty():
                table.insert( outgoing_sms_handler = "WEB_API" )
            table = db.msg_modem_settings
            if db(table).isempty():
                table.insert( modem_baud = 115200 )
            table = db.msg_api_settings
            if db(table).isempty():
                table.insert( to_variable = "to" )
            table = db.msg_smtp_to_sms_settings
            if db(table).isempty():
                table.insert( address="changeme" )
            table = db.msg_tropo_settings
            if db(table).isempty():
                table.insert( token_messaging = "" )
            table = db.msg_twitter_settings
            if db(table).isempty():
                table.insert( pin = "" )

        # Human Resources
        if deployment_settings.has_module("hrm"):
            table = db.hrm_certificate
            if db(table).isempty():
                table.insert( name = "CPA - Certified Public Accountant")
                table.insert( name = "CSW - Certified Social Worker")
                table.insert( name = "DR1 - Driver's License - Car")
                table.insert( name = "DR2 - Driver's License - Lt truck")
                table.insert( name = "DR3 - Driver's License Heavy truck")
                table.insert( name = "DR4 - Driver's License Bus")
                table.insert( name = "DR5 - Driver's License Commercial")
                table.insert( name = "DR6 - Driver's License Motorcycle")
                table.insert( name = "EMT - Emergency Medical Technician")
                table.insert( name = "HRO - Ham Radio Operator")
                table.insert( name = "LPC - Licensed Professional Counselor")
                table.insert( name = "LPN - Licensed Practical Nurse")
                table.insert( name = "LSW - Licensed Social Worker")
                table.insert( name = "LVN - Licensed Vocational Nurse")
                table.insert( name = "MD - Medical Doctor")
                table.insert( name = "MFT - Marriage and Family Therapist")
                table.insert( name = "MT - Medical Technician")
                table.insert( name = "PA - Physician Assistant")
                table.insert( name = "PSY - Psychologist")
                table.insert( name = "RN - Registered Nurse")

        # Assessment
        if deployment_settings.has_module("assess"):
            table = db.assess_baseline_type
            if db(table).isempty():
                table.insert( name = "# of population")
                table.insert( name = "# of households" )
                table.insert( name = "# of children under 5" )
                table.insert( name = "# of children" )
                table.insert( name = "# of cattle" )
                table.insert( name = "Ha. of fields" )

        # Impacts
        if deployment_settings.has_module("irs") or deployment_settings.has_module("assess"):
            table = db.impact_type
            if db(table).isempty():
                def sector_id(look_up):
                    s3_get_db_field_value(tablename = "org_sector",
                                          fieldname = "id",
                                          look_up_value = look_up,
                                          look_up_field = "abrv")
                table.insert( name = "# of People Affected" )
                table.insert( name = "# People Needing Food",
                              sector_id = sector_id('Food'))
                table.insert( name = "# People at Risk From Vector-Borne Diseases",
                              sector_id = sector_id('Health'))
                table.insert( name = "# People without Access to Safe Drinking-Water",
                              sector_id = sector_id('WASH'))
                table.insert( name = "# Houses Damaged",
                              sector_id = sector_id('Shelter'))
                table.insert( name = "# Houses Flooded",
                              sector_id = sector_id('Shelter'))
                table.insert( name = "Water Level still high?",
                              sector_id = sector_id('Shelter'))
                table.insert( name = "Ha. Fields Flooded",
                              sector_id = sector_id('Agriculture'))
        # Project Module
        if deployment_settings.has_module("project"):
            table = db.project_need_type
            if db(table).isempty():
                table.insert( name = T("People Needing Food") )
                table.insert( name = T("People Needing Water") )
                table.insert( name = T("People Needing Shelter") )

        # Budget Module
        if deployment_settings.has_module("budget") and \
                deployment_settings.has_module("project"):
            table = db.budget_parameter
            if db(table).isempty():
                table.insert() # Only defaults are fine

        # Ticketing System
        if deployment_settings.has_module("ticket"):
            table = db.ticket_category
            if db(table).isempty():
                table.insert( name = "Report Missing Person" )
                table.insert( name = "Report Security Incident" )
                table.insert( name = "Report Information" )
                table.insert( name = "Request for Assistance" )
                table.insert( name = "Offer of Help" )

        # GIS Module
        table = db.gis_marker
        # Can't do sub-folders :/
        # need a script to read in the list of default markers from the filesystem, copy/rename & populate the DB 1 by 1
        if db(table).isempty():
            # We want to start at ID 1, but postgres won't let us truncate() & not needed anyway this is only run on 1st_run.
            #table.truncate()
            # "marker_red" is the default marker. If you remove it or change its
            # name, also change S3Config.get_gis_default_marker().
            marker_red = table.insert(
                name = "marker_red",
                height = 34,
                width = 20,
                image = "gis_marker.image.marker_red.png"
            )
            marker_yellow = table.insert(
                name = "marker_yellow",
                height = 34,
                width = 20,
                image = "gis_marker.image.marker_yellow.png"
            )
            marker_amber = table.insert(
                name = "marker_amber",
                height = 34,
                width = 20,
                image = "gis_marker.image.marker_amber.png"
            )
            marker_green = table.insert(
                name = "marker_green",
                height = 34,
                width = 20,
                image = "gis_marker.image.marker_green.png"
            )
            person = table.insert(
                name = "person",
                height = 50,
                width = 50,
                image = "gis_marker.image.Civil_Disturbance_Theme.png"
            )
            school = table.insert(
                name = "school",
                height = 33,
                width = 44,
                image = "gis_marker.image.Edu_Schools_S1.png"
            )
            food = table.insert(
                name = "food",
                height = 40,
                width = 40,
                image = "gis_marker.image.Emergency_Food_Distribution_Centers_S1.png"
            )
            office = table.insert(
                name = "office",
                height = 40,
                width = 40,
                image = "gis_marker.image.Emergency_Operations_Center_S1.png"
            )
            shelter = table.insert(
                name = "shelter",
                height = 40,
                width = 40,
                image = "gis_marker.image.Emergency_Shelters_S1.png"
            )
            activity = table.insert(
                name = "activity",
                height = 40,
                width = 40,
                image = "gis_marker.image.Emergency_Teams_S1.png"
            )
            hospital = table.insert(
                name = "hospital",
                height = 40,
                width = 40,
                image = "gis_marker.image.E_Med_Hospital_S1.png"
            )
            table.insert(
                name = "earthquake",
                height = 50,
                width = 50,
                image = "gis_marker.image.Geo_Earth_Quake_Epicenter.png"
            )
            table.insert(
                name = "volcano",
                height = 50,
                width = 50,
                image = "gis_marker.image.Geo_Volcanic_Threat.png"
            )
            table.insert(
                name = "flood",
                height = 50,
                width = 50,
                image = "gis_marker.image.Hydro_Meteor_Flood.png"
            )
            table.insert(
                name = "tsunami",
                height = 50,
                width = 50,
                image = "gis_marker.image.Hydro_Meteor_Tsunami_ch.png"
            )
            church = table.insert(
                name = "church",
                height = 33,
                width = 44,
                image = "gis_marker.image.Public_Venue_Church_S1.png"
            )
            table.insert(
                name = "mosque",
                height = 33,
                width = 44,
                image = "gis_marker.image.Public_Venue_Mosque_S1.png"
            )
            table.insert(
                name = "temple",
                height = 33,
                width = 44,
                image = "gis_marker.image.Public_Venue_Temple_S1.png"
            )
            phone = table.insert(
                name = "phone",
                height = 10,
                width = 5,
                image = "gis_marker.image.SMS_Message_Phone.png"
            )
            table.insert(
                name = "orphanage",
                height = 33,
                width = 44,
                image = "gis_marker.image.Special_Needs_Child_Day_Care_S1.png"
            )
            airport = table.insert(
                name = "airport",
                height = 33,
                width = 44,
                image = "gis_marker.image.Trans_Airport_S1.png"
            )
            bridge = table.insert(
                name = "bridge",
                height = 33,
                width = 44,
                image = "gis_marker.image.Trans_Bridge_S1.png"
            )
            table.insert(
                name = "helicopter",
                height = 33,
                width = 44,
                image = "gis_marker.image.Trans_Helicopter_Landing_Site_S1.png"
            )
            port = table.insert(
                name = "port",
                height = 33,
                width = 44,
                image = "gis_marker.image.Trans_Port_S1.png"
            )
            table.insert(
                name = "rail_station",
                height = 33,
                width = 44,
                image = "gis_marker.image.Trans_Rail_Station_S1.png"
            )
            vehicle = table.insert(
                name = "vehicle",
                height = 50,
                width = 50,
                image = "gis_marker.image.Transport_Vehicle_Theme.png"
            )
            water = table.insert(
                name = "water",
                height = 33,
                width = 44,
                image = "gis_marker.image.Water_Supply_Infrastructure_Theme_S1.png"
            )
            volunteer = table.insert(
                name = "volunteer",
                height = 40,
                width = 39,
                image = "gis_marker.image.Volunteer.png"
            )
        table = db.gis_symbology
        if db(table).isempty():
            table.insert(
                name = "Australasia"
            )
            table.insert(
                name = "Canada"
            )
            # "US" is the default symbology. If you remove it or change its name,
            # also change S3Config.get_gis_default_symbology().
            table.insert(
                name = "US"
            )
        table = db.gis_projection
        if db(table).isempty():
            # We want to start at ID 1, but postgres won't let us truncate() & not needed anyway this is only run on 1st_run.
            #table.truncate()
            # "Spherical Mercator" is the default projection. If you remove it or
            # change its name, also change S3Config.get_gis_default_projection().
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-PROJECTION-900913",
                name = "Spherical Mercator",
                epsg = 900913,
                maxExtent = "-20037508, -20037508, 20037508, 20037508.34",
                maxResolution = 156543.0339,
                units = "m"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-PROJECTION-4326",
                name = "WGS84",
                epsg = 4326,
                maxExtent = "-180,-90,180,90",
                maxResolution = 1.40625,
                units = "degrees"
                # OSM use these:
                #maxResolution = 156543.0339,
                #units = "m"
            )

        table = db.gis_config
        # Ensure that the projection/marker we defined
        # are in the DB ready to be
        # used as FKs
        db.commit()
        query = db.gis_symbology.name == \
            deployment_settings.get_gis_default_symbology()
        site_symbology = db(query).select(db.gis_symbology.id,
                                          limitby=(0, 1)).first().id
        if db(table).isempty():
            # We want to start at ID 1,
            # but postgres won't let us truncate() & not
            # needed anyway as this is only run on 1st_run.
            #table.truncate()
            default_gis_config_values = Storage()
            default_gis_config_values.update(
                deployment_settings.get_gis_default_config_values())
            if not default_gis_config_values.symbology_id:
                default_gis_config_values.symbology_id = site_symbology
            if not default_gis_config_values.projection_id:
                query = db.gis_projection.name == \
                    deployment_settings.get_gis_default_projection()
                projection_id = db(query).select(db.gis_symbology.id,
                                                 limitby=(0, 1)).first().id
                if projection_id:
                    default_gis_config_values.projection_id = projection_id
            if not default_gis_config_values.marker_id:
                query = db.gis_marker.name == \
                    deployment_settings.get_gis_default_marker()
                marker_id = db(query).select(db.gis_marker.id,
                                             limitby=(0, 1)).first().id
                if marker_id:
                    default_gis_config_values.marker_id = marker_id
            default_gis_config_values.update(
                gis.get_location_hierarchy_settings())
            # Since the values from deployment_settings have not been validated,
            # check them.
            errors = Storage()
            gis.config_onvalidation(default_gis_config_values, errors)
            # Do a minimal fixup of any errors.
            # If there's an error in region settings,
            # don't show it in the menu.
            if errors.region_location_id or errors.name:
                default_gis_config_values.show_in_menu = False
            # If there are missing level names, default them to Ln.
            for error in errors:
                if len(error) == 2 and error[0] == "L":
                    default_gis_config_values[error] = error
            # @ToDo: Log the errors.

            table.insert(**default_gis_config_values)

        # Feature Classes
        # - used to provide Markers for Feed Exports, like KML
        table = db.gis_feature_class
        if db(table).isempty():
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-TRACK",
                name = "Track",
                gps_marker = "TracBack Point",
                resource = "gis_track"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L0",
                name = "Country",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L1",
                name = "Province",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L2",
                name = "District",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L3",
                name = "Town",
                gps_marker = "City (Medium)",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L4",
                name = "Village",
                gps_marker = "City (Small)",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-AIRPORT",
                name = "Airport",
                symbology_id = site_symbology,
                marker_id = airport,
                gps_marker = "Airport",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-BRIDGE",
                name = "Bridge",
                symbology_id = site_symbology,
                marker_id = bridge,
                gps_marker = "Bridge",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-CHURCH",
                name = "Church",
                symbology_id = site_symbology,
                marker_id = church,
                gps_marker = "Church",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-FOOD",
                name = "Food",
                symbology_id = site_symbology,
                marker_id = food,
                gps_marker = "Restaurant",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-HOSPITAL",
                name = "Hospital",
                symbology_id = site_symbology,
                marker_id = hospital,
                gps_marker = "Medical Facility",
                resource = "hms_hospital"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-INCIDENT",
                name = "Incident",
                gps_marker = "Danger Area",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-OFFICE",
                name = "Office",
                symbology_id = site_symbology,
                marker_id = office,
                gps_marker = "Building",
                resource = "org_office"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PERSON",
                name = "Person",
                symbology_id = site_symbology,
                marker_id = person,
                gps_marker = "Contact, Dreadlocks",
                resource = "pr_person"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PORT",
                name = "Port",
                symbology_id = site_symbology,
                marker_id = port,
                gps_marker = "Marina",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PROJECT",
                name = "Project",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SCHOOL",
                name = "School",
                marker_id = school,
                gps_marker = "School",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SHELTER",
                name = "Shelter",
                symbology_id = site_symbology,
                marker_id = shelter,
                gps_marker = "Campground",
                resource = "cr_shelter"
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SMS",
                name = "SMS",
                marker_id = phone,
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-STAFF",
                name = "Staff",
                symbology_id = site_symbology,
                marker_id = person,
                gps_marker = "Contact, Dreadlocks",
                resource = "hrm_human_resource",
                filter_field = "type",
                filter_value = 1,
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VEHICLE",
                name = "Vehicle",
                symbology_id = site_symbology,
                marker_id = vehicle,
                gps_marker = "Car",
                resource = "asset_asset",
                filter_field = "type",
                filter_value = 1,
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VOLUNTEER",
                name = "Volunteer",
                symbology_id = site_symbology,
                marker_id = volunteer,
                gps_marker = "Contact, Dreadlocks",
                resource = "hrm_human_resource",
                filter_field = "type",
                filter_value = 2,
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WAREHOUSE",
                name = "Warehouse",
                symbology_id = site_symbology,
                marker_id = office,
                gps_marker = "Building",
            )
            table.insert(
                uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WATER",
                name = "Water",
                symbology_id = site_symbology,
                marker_id = water,
                gps_marker = "Drinking Water",
            )
        table = db.gis_layer_feature
        if db(table).isempty():
            table.insert(
                name = "Incident Reports",
                module = "irs",
                resource = "ireport",
                popup_label = "Incident",
                popup_fields = "name/category",
                # Default (but still better to define here as otherwise each feature needs to check it's feature_class)
                marker_id = marker_red
            )
            table.insert(
                name = "Hospitals",
                module = "hms",
                resource = "hospital",
                popup_label = "Hospital",
                marker_id = hospital
            )
            table.insert(
                name = "Shelters",
                module = "cr",
                resource = "shelter",
                popup_label = "Shelter",
                popup_fields = "name/organisation_id/capacity",
                marker_id = shelter
            )
            table.insert(
                name = "Offices",
                module = "org",
                resource = "office",
                comments = "All Active Offices",
                filter = "office.type=None,1,2,3,4&office.obsolete=False",
                popup_label = "Office",
                popup_fields = "name/organisation_id",
                marker_id = office
            )
            #table.insert(
            #    name = "Requests",
            #    module = "rms",
            #    resource = "req",
            #    popup_label = "Request",
            #    marker_id = marker_yellow
            #)
            table.insert(
                name = "Assessments",
                module = "assess",
                resource = "rat",
                popup_label = "Assessment",
                popup_fields = "date/staff_id",
                marker_id = marker_green
            )
            table.insert(
                name = "Activities",
                module = "project",
                resource = "activity",
                popup_label = "Activity",
                popup_fields = "name/organisation_id/sector_id",
                marker_id = activity
            )
            #table.insert(
            #    name = "People",
            #    module = "pr",
            #    resource = "person",
            #    popup_label = "Person",
            #    marker_id = person
            #)
            table.insert(
                name = "Staff",
                module = "hrm",
                resource = "human_resource",
                comments = "All Active Staff",
                filter = "human_resource.type=1&human_resource.status=1",
                popup_label = "Staff",
                popup_fields = "person_id/job_title/organisation_id",
                marker_id = person
            )
            table.insert(
                name = "Volunteers",
                module = "hrm",
                resource = "human_resource",
                comments = "All Active Volunteers",
                filter = "human_resource.type=2&human_resource.status=1",
                popup_label = "Volunteer",
                popup_fields = "person_id/job_title/organisation_id",
                marker_id = volunteer
            )
            table.insert(
                name = "Warehouses",
                module = "org",
                resource = "office",
                comments = "All Active Warehouses",
                filter = "office.type=5&office.obsolete=False",
                popup_label = "Warehouse",
                popup_fields = "name/organisation_id",
                marker_id = office
            )
            table.insert(
                name = "Assets",
                module = "asset",
                resource = "asset",
                popup_label = "Asset",
                popup_fields = "item_id/number", # Would like Status & Condition here, but currently they're a Join away
            )
            table.insert(
                name = "Vehicles",
                module = "asset",
                resource = "asset",
                filter = "asset.type=1",
                popup_label = "Vehicle",
                popup_fields = "item_id/number", # Would like Status & Condition here, but currently they're a Join away
                marker_id = vehicle
            )
        table = db.gis_layer_bing
        if db(table).isempty():
            # Populate table with single default Record
            table.insert(
                name = "Bing",
                apikey = "", # Insert API Key here
                enabled = False
            )
        table = db.gis_layer_coordinate
        if db(table).isempty():
            # Populate table with single default Record
            table.insert(
                    name = "Coordinate Grid",
                    enabled = False,
                    visible = False
                )
        table = db.gis_layer_openstreetmap
        if db(table).isempty():
            # Populate table
            table.insert(
                    name = "OpenStreetMap (Mapnik)",
                    url1 = "http://a.tile.openstreetmap.org/",
                    url2 = "http://b.tile.openstreetmap.org/",
                    url3 = "http://c.tile.openstreetmap.org/",
                    attribution = '<a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>',
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (CycleMap)",
                    url1 = "http://a.tile.opencyclemap.org/cycle/",
                    url2 = "http://b.tile.opencyclemap.org/cycle/",
                    url3 = "http://c.tile.opencyclemap.org/cycle/",
                    attribution = '<a href="http://www.opencyclemap.org/" target="_blank">OpenCycleMap</a>',
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (Labels)",
                    url1 = "http://tiler1.censusprofiler.org/labelsonly/",
                    attribution = 'Labels overlay CC-by-SA by <a href="http://oobrien.com/oom/" target="_blank">OpenOrienteeringMap</a>/<a href="http://www.openstreetmap.org/">OpenStreetMap</a> data',
                    base = False,
                    visible = False,
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (Relief)",
                    url1 = "http://toolserver.org/~cmarqu/hill/",
                    attribution = 'Relief by <a href="http://hikebikemap.de/" target="_blank">Hike &amp; Bike Map</a>',
                    base = False,
                    visible = False,
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (MapQuest)",
                    url1 = "http://otile1.mqcdn.com/tiles/1.0.0/osm/",
                    url2 = "http://otile2.mqcdn.com/tiles/1.0.0/osm/",
                    url3 = "http://otile3.mqcdn.com/tiles/1.0.0/osm/",
                    attribution = 'Tiles Courtesy of <a href="http://open.mapquest.co.uk/" target="_blank">MapQuest</a> <img src="http://developer.mapquest.com/content/osm/mq_logo.png" border="0">',
                    enabled = True
                )
            table.insert(
                    name = "OpenStreetMap (Osmarender)",
                    url1 = "http://a.tah.openstreetmap.org/Tiles/tile/",
                    url2 = "http://b.tah.openstreetmap.org/Tiles/tile/",
                    url3 = "http://c.tah.openstreetmap.org/Tiles/tile/",
                    attribution = '<a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>',
                    zoom_levels = 18,
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (Taiwan)",
                    url1 = "http://tile.openstreetmap.tw/tiles/",
                    enabled = False
                )
            table.insert(
                    name = "OpenStreetMap (Sahana)",
                    url1 = "http://geo.eden.sahanafoundation.org/tiles/",
                    enabled = False
                )
            #table.insert(
            #        name = "OpenAerialMap",
            #        url1 = "http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/",
            #        enabled = False
            #    )
        table = db.gis_layer_google
        if db(table).isempty():
           # Populate table with single default Record
            table.insert(
                name = "Google",
                apikey = "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRTpH3CbXHjuCVmaTc5MkkU4wO1RRhQWqp1VGwrG8yPE2KhLCPYhD7itFw", # http://127.0.0.1:8000
                enabled = True
            )
        table = db.gis_layer_yahoo
        if db(table).isempty():
            # Populate table with single default Record
            table.insert(
                name = "Yahoo",
                apikey = "euzuro-openlayers", # Trial - replace for Production use
                enabled = False
            )
        table = db.gis_layer_mgrs
        if db(table).isempty():
            # Populate table
            table.insert(
                    name = "MGRS Atlas PDFs",
                    description = "http://en.wikipedia.org/wiki/Military_grid_reference_system",
                    url = "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps",
                    enabled = False
                )
        table = db.gis_layer_tms
        if db(table).isempty():
            # Populate table
            table.insert(
                    name = "Blue Marble Topography & Bathymetry (January)",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "blue-marble-topo-bathy-jan",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Blue Marble Topography & Bathymetry (July)",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "blue-marble-topo-bathy-jul",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Blue Marble Topography (January)",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "blue-marble-topo-jan",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Blue Marble Topography (July)",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "blue-marble-topo-jul",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Control Room",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "control-room",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Geography Class",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "geography-class",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 9,
                    enabled = False
                )
            table.insert(
                    name = "Natural Earth Hypsometric",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "natural-earth-hypso",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 7,
                    enabled = False
                )
            table.insert(
                    name = "Natural Earth Hypsometric & Bathymetry",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "natural-earth-hypso-bathy",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 7,
                    enabled = False
                )
            table.insert(
                    name = "Natural Earth I",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "natural-earth-1",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 7,
                    enabled = False
                )
            table.insert(
                    name = "Natural Earth II",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "natural-earth-2",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 7,
                    enabled = False
                )
            table.insert(
                    name = "World Dark",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "world-dark",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 12,
                    enabled = False
                )
            table.insert(
                    name = "World Light",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "world-light",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 12,
                    enabled = False
                )
            table.insert(
                    name = "World Glass",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "world-glass",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 11,
                    enabled = False
                )
            table.insert(
                    name = "World Print",
                    description = "MapBox",
                    url = "http://a.tiles.mapbox.com/mapbox/",
                    url2 = "http://b.tiles.mapbox.com/mapbox/",
                    url3 = "http://c.tiles.mapbox.com/mapbox/",
                    layername = "world-print",
                    attribution = '<a href="http://mapbox.com" target="_blank">MapBox</a>',
                    zoom_levels = 10,
                    enabled = False
                )
        table = db.gis_layer_wms
        if db(table).isempty():
            # Populate table
            table.insert(
                    name = "VMap0",
                    description = "A Free low-resolution Vector Map of the whole world",
                    url = "http://vmap0.tiles.osgeo.org/wms/vmap0",
                    map = "",
                    layers = "basic",
                    enabled = False,
                    base = True,
                    transparent = True
                )
            table.insert(
                    name = "Blue Marble",
                    description = "A composite of four months of MODIS observations with a spatial resolution (level of detail) of 1 square kilometer per pixel.",
                    url = "http://maps.opengeo.org/geowebcache/service/wms",
                    map = "",
                    layers = "bluemarble",
                    enabled = False,
                    base = True,
                    transparent = True
                )
            table.insert(
                    name = "LandSat",
                    description = "Global 15m satellite imagery from 2003.",
                    url = "http://hyperquad.telascience.org/cgi-bin/onearth?",
                    map = "",
                    layers = "OnEarth_PAN_321_20030801",
                    img_format="image/jpeg",
                    enabled = False,
                    base = True,
                    transparent = True
                )
            table.insert(
                    name = "Topography",
                    description = "SRTMv4",
                    url = "http://skapes.org/geoserver/gwc/service/wms",
                    map = "",
                    layers = "sahana:SRTMv4",
                    enabled = False,
                    visible = False,
                    base = False,
                    transparent=True,
                    img_format="image/png",
                    opacity = 0.8
                )
            table.insert(
                    name="GADMv1",
                    description="GADM Base Layer: L0-L2 Boundaries, Polygon fill, Labels",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_base",
                    base=True,
                    # Set in geowebcache.xml as doesn't pass through
                    #bgcolor="CCCCFF",
                    img_format="image/jpeg"
                )
            table.insert(
                    name="Admin Boundaries",
                    description="GADM Overlay: L0-L2 Boundaries, Labels, No Polygon fill",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_overlays",
                    base=False,
                    transparent=True,
                    # Metatiling is done by GWC
                    tiled=False,
                    img_format="image/png"
                )
            table.insert(
                    name="L2 Boundaries",
                    description="GADM L2 Overlay: Boundaries, Labels, No Polygon fill",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_lev2",
                    base=False,
                    transparent=True,
                    # Metatiling is done by GWC
                    tiled=False,
                    img_format="image/png"
                )
            table.insert(
                    name="L1 Boundaries",
                    description="GADM L1 Overlay: Boundaries, Labels, No Polygon fill",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_lev1",
                    base=False,
                    transparent=True,
                    # Metatiling is done by GWC
                    tiled=False,
                    img_format="image/png"
                )
            table.insert(
                    name="Country Boundaries",
                    description="GADM L0 Overlay: Boundaries, Labels, No Polygon fill",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_lev0",
                    base=False,
                    transparent=True,
                    # Metatiling is done by GWC
                    tiled=False,
                    img_format="image/png"
                )
            table.insert(
                    name="Country Boundaries",
                    description="GADM L0 Base Layer: Boundaries, Polygon fill, No Labels",
                    enabled=False,
                    visible=False,
                    url="http://skapes.org/geoserver/gwc/service/wms",
                    layers="sahana:gadm1_lev0_base",
                    base=True,
                    # Set in geowebcache.xml as doesn't pass through
                    #bgcolor="CCCCFF",
                    img_format="image/jpeg"
                )

        table = db.gis_layer_georss
        if db(table).isempty():
            # Populate table
            table.insert(
                    name = "Earthquakes",
                    description = "USGS: Global 7-day",
                    url = "http://earthquake.usgs.gov/eqcenter/catalogs/eqs7day-M2.5.xml",
                    marker_id = db(db.gis_marker.name == "earthquake").select(db.gis_marker.id,
                                                                              limitby=(0, 1)).first().id,
                    enabled = False
                )
            table.insert(
                    name = "Floods",
                    description = "Dartmouth Flood Observatory",
                    url = "http://www.gdacs.org/xml/rssfl.xml",
                    image = "gdas:gfds_image",
                    marker_id = db(db.gis_marker.name == "flood").select(db.gis_marker.id,
                                                                              limitby=(0, 1)).first().id,
                    enabled = False
                )
            table.insert(
                    name = "Volcanoes",
                    description = "USGS: US recent",
                    url = "http://volcano.wr.usgs.gov/rss/vhpcaprss.xml",
                    marker_id = db(db.gis_marker.name == "volcano").select(db.gis_marker.id,
                                                                           limitby=(0, 1)).first().id,
                    enabled = False
                )

        tablename = "gis_location"
        table = db[tablename]
        if db(table).isempty():
            # L0 Countries
            import_file = os.path.join(request.folder,
                                       "private", "import",
                                       "countries.csv")
            table.import_from_csv_file(open(import_file, "r"))
            map_admin = db(db.auth_group.uuid==sysroles.MAP_ADMIN).select().first().id
            db(table.level=="L0").update(owned_by_role=map_admin)
        # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
        field = "name"
        db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

        # Ensure DB population committed when running through shell
        db.commit()

    if populate > 0: # Prepopulate import

        # Override authorization
        auth.override = True

        # Disable table protection
        protected = manager.PROTECTED
        manager.PROTECTED = []

        # Additional settings for user table imports:
        manager.configure("auth_user",
                        onaccept = lambda form: auth.s3_link_to_person(user=form.vars))
        manager.model.add_component("auth_membership", auth_user="user_id")

        # Create the bulk Importer object
        bi = s3base.S3BulkImporter()

        # Allow population via shell scripts
        if not request.env.request_method:
            request.env.request_method = "GET"

    if populate & 1: # Populate with the default data
        path = os.path.join(request.folder,
                            "private",
                            "prepopulate",
                            "default")
        bi.perform_tasks(path)

    if populate & 2: # Populate data for the regression tests
        path = os.path.join(request.folder,
                            "private",
                            "prepopulate",
                            "regression")
        bi.perform_tasks(path)

    if populate & 4: # Populate data for scalability testing
        # This is different from the repeatable imports that use csv files
        # This will generate millions of records of data for selected tables.

        # Code needs to go here to generate a large volume of test data
        pass

    if populate & 8: # Populate data for user specific data
        path = os.path.join(request.folder,
                            "private",
                            "prepopulate",
                            "user")
        bi.perform_tasks(path)

    if populate & 16: # Populate data for a deployment default demo
        path = os.path.join(request.folder,
                            "private",
                            "prepopulate",
                            "demo",
                            "default")
        bi.perform_tasks(path)

    demoFlag = populate
    demoFlag = demoFlag >> 4
    demoFolderIndex = 0
    if demoFlag > 0:
        """
            Read the demo_folders file and extract the folder for the specific demo
        """
        file = os.path.join(request.folder,
                            "private",
                            "prepopulate",
                            "demo",
                            "demo_folders.txt")
        source = open(file, "r")
        values = source.readlines()
        source.close()
        demoDir = {}
        for demos in values:
            # strip out the new line
            demos = demos.strip()
            if demos == "":
                continue
            # split at the comma
            details = demos.split(",")
            if len(details) == 2:
                 # remove any spaces and enclosing double quote
                index = details[0].strip('" ')
                directory = details[1].strip('" ')
                path = os.path.join(request.folder,
                                    "private",
                                    "prepopulate",
                                    "demo",
                                    directory)
                if os.path.exists(path):
                    demoDir[index] = path

    while demoFlag > 0: # Other deployment demos
        demoFolderIndex += 1
        if demoFlag & 1:
            if str(demoFolderIndex) in demoDir:
                bi.perform_tasks(demoDir[str(demoFolderIndex)])
            else:
                print >> sys.stderr, "Unable to install demo %s no demo directory found" % demoFolderIndex
        demoFlag = demoFlag >> 1

    if populate > 0: # Prepopulate import
        for errorLine in bi.errorList:
            print >> sys.stderr, errorLine
        # Restore table protection
        manager.PROTECTED = protected

        # Restore view
        response.view = "default/index.html"

    auth.override = False