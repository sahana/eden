# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

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

__all__ = ["HospitalDataModel",
           "CholeraTreatmentCapabilityModel",
           "HospitalActivityReportModel",
           "hms_hospital_rheader"
           ]

from gluon import *
from gluon.storage import Storage
from gluon.dal import Row
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class HospitalDataModel(S3Model):

    names = ["hms_hospital",
             "hms_contact",
             "hms_bed_capacity",
             "hms_services",
             "hms_image",
             "hms_resources",
             "hms_hospital_id"
             ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        human_resource_id = self.hrm_human_resource_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Hospitals
        #

        # Use government-assigned UUIDs instead of internal UUIDs
        HMS_HOSPITAL_USE_GOVUUID = True

        hms_facility_type_opts = {
            1: T("Hospital"),
            2: T("Field Hospital"),
            3: T("Specialized Hospital"),
            11: T("Health center"),
            12: T("Health center with beds"),
            13: T("Health center without beds"),
            21: T("Dispensary"),
            98: T("Other"),
            99: T("Unknown type of facility"),
        } #: Facility Type Options

        tablename = "hms_hospital"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             super_link("pe_id", "pr_pentity"),
                             super_link("site_id", "org_site"),
                             Field("paho_uuid",
                                   unique=True,
                                   length=128,
                                   requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                "%s.paho_uuid" % tablename)),
                                   label = T("PAHO UID")),

                             # UID assigned by Local Government
                             Field("gov_uuid",
                                   unique=True,
                                   length=128,
                                   requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                "%s.gov_uuid" % tablename)),
                                   label = T("Government UID")),

                             # Alternate ids found in data feeds
                             Field("other_ids",
                                   length=128),

                             # Mayon compatibility
                             #Field("code",
                             #      length=10,
                             #      notnull=True,
                             #      unique=True, label=T("Code")),

                             # Name of the facility
                             Field("name",
                                   notnull=True,
                                   length=64, # Mayon compatibility
                                   label = T("Name")),

                             # Alternate name, or name in local language
                             Field("aka1", label = T("Other Name")),

                             # Alternate name, or name in local language
                             Field("aka2",label = T("Other Name")),

                             Field("facility_type", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                hms_facility_type_opts)),
                                   default = 1,
                                   label = T("Facility Type"),
                                   represent = lambda opt: \
                                               hms_facility_type_opts.get(opt,
                                                        T("not specified"))),
                             organisation_id(),
                             location_id(),

                             # Address fields:
                             # @todo: Deprecate these & use location_id in HAVE export
                             Field("address",
                                   label = T("Address")),
                             Field("postcode",
                                   label = settings.get_ui_label_postcode()),
                             Field("city"),

                             Field("phone_exchange",
                                   label = T("Phone/Exchange (Switchboard)"),
                                   requires = IS_NULL_OR(s3_phone_requires)),

                             Field("phone_business",
                                   label = T("Phone/Business"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             Field("phone_emergency",
                                   label = T("Phone/Emergency"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             Field("website",
                                   label=T("Website"),
                                   requires = IS_NULL_OR(IS_URL()),
                                   represent = s3_url_represent),
                             Field("email",
                                   label = T("Email"),
                                   requires = IS_NULL_OR(IS_EMAIL())),
                             Field("fax",
                                   label = T("Fax"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             Field("total_beds", "integer",
                                   readable = False,
                                   writable = False,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Total Beds")),
                             Field("available_beds", "integer",
                                   readable = False,
                                   writable = False,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Available Beds")),
                             Field("doctors", "integer",
                                   label = T("Number of doctors"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 9999)),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("nurses", "integer",
                                   label = T("Number of nurses"),
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 9999)),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("non_medical_staff", "integer",
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Number of non-medical staff"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("obsolete", "boolean",
                                   label = T("Obsolete"),
                                   represent = lambda bool: \
                                     (bool and [T("Obsolete")] or [messages.NONE])[0],
                                   default = False,
                                   readable = False,
                                   writable = False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_HOSPITAL = T("Add Hospital")
        crud_strings[tablename] = Storage(
            title_create = ADD_HOSPITAL,
            title_display = T("Hospital Details"),
            title_list = T("Hospitals"),
            title_update = T("Edit Hospital"),
            title_search = T("Find Hospital"),
            title_map = T("Map of Hospitals"),
            subtitle_create = T("Add New Hospital"),
            label_list_button = T("List Hospitals"),
            label_create_button = ADD_HOSPITAL,
            label_delete_button = T("Delete Hospital"),
            msg_record_created = T("Hospital information added"),
            msg_record_modified = T("Hospital information updated"),
            msg_record_deleted = T("Hospital information deleted"),
            msg_list_empty = T("No Hospitals currently registered"))

        # Search method
        hms_hospital_search = S3Search(
            #name="hospital_search_simple",
            #label=T("Name and/or ID"),
            #comment=T("To search for a hospital, enter any of the names or IDs of the hospital, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
            #field=["gov_uuid", "name", "aka1", "aka2"],
            advanced=(S3SearchSimpleWidget(
                        name="hospital_search_advanced",
                        label=T("Name, Org and/or ID"),
                        comment=T("To search for a hospital, enter any of the names or IDs of the hospital, or the organisation name or acronym, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all hospitals."),
                        field=["gov_uuid", "name", "aka1", "aka2",
                            "organisation_id$name", "organisation_id$acronym"]
                      ),
                      # for testing:
                      S3SearchOptionsWidget(
                        name="hospital_facility_type",
                        label=T("Facility Type"),
                        field="facility_type"
                      ),
                      # for testing:
                      S3SearchMinMaxWidget(
                        name="hospital_search_bedcount",
                        method="range",
                        label=T("Total Beds"),
                        comment=T("Select a range for the number of total beds"),
                        field="total_beds"
                      ),
                    ))

        # Resource configuration
        configure(tablename,
                  super_entity=("org_site", "doc_entity", "pr_pentity"),
                  search_method=hms_hospital_search,
                  list_fields=["id",
                               "gov_uuid",
                               "name",
                               "facility_type",
                               "organisation_id",
                               "location_id",
                               "phone_exchange",
                               "total_beds",
                               "available_beds"])

        # Reusable field
        hms_hospital_id_comment = S3AddResourceLink(c="hms",
                                                    f="hospital",
                                                    label=ADD_HOSPITAL,
                                                    title=T("Hospital"),
                                                    tooltip=T("If you don't see the Hospital in the list, you can add a new one by clicking link 'Add Hospital'."))

        hospital_id = S3ReusableField("hospital_id", table,
                                      sortby="name",
                                      requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "hms_hospital.id",
                                                              self.hms_hospital_represent
                                                              )),
                                      represent = self.hms_hospital_represent,
                                      label = T("Hospital"),
                                      comment = hms_hospital_id_comment,
                                      ondelete = "RESTRICT")

        # Components
        single = dict(joinby="hospital_id", multiple=False)
        multiple = "hospital_id"

        add_component("hms_status", hms_hospital=single)
        add_component("hms_contact", hms_hospital=multiple)
        add_component("hms_bed_capacity", hms_hospital=multiple)
        add_component("hms_services", hms_hospital=single)
        add_component("hms_resources", hms_hospital=multiple)

        # Optional components
        if settings.get_hms_track_ctc():
            add_component("hms_ctc", hms_hospital=single)

        if settings.get_hms_activity_reports():
            add_component("hms_activity", hms_hospital=multiple)

        # ---------------------------------------------------------------------
        # Hospital status
        #
        hms_resource_status_opts = {
            1: T("Adequate"),
            2: T("Insufficient")
        } #: Resource Status Options

        hms_facility_status_opts = {
            1: T("Normal"),
            2: T("Compromised"),
            3: T("Evacuating"),
            4: T("Closed")
        } #: Facility Status Options

        hms_clinical_status_opts = {
            1: T("Normal"),
            2: T("Full"),
            3: T("Closed")
        } #: Clinical Status Options

        hms_security_status_opts = {
            1: T("Normal"),
            2: T("Elevated"),
            3: T("Restricted Access"),
            4: T("Lockdown"),
            5: T("Quarantine"),
            6: T("Closed")
        } #: Security Status Options

        hms_ems_traffic_opts = {
            1: T("Normal"),
            2: T("Advisory"),
            3: T("Closed"),
            4: T("Not Applicable")
        } #: EMS Traffic Options

        hms_or_status_opts = {
            1: T("Normal"),
            #2: T("Advisory"),
            3: T("Closed"),
            4: T("Not Applicable")
        } #: Operating Room Status Options

        hms_morgue_status_opts = {
            1: T("Open"),
            2: T("Full"),
            3: T("Exceeded"),
            4: T("Closed")
        } #: Morgue Status Options

        tablename = "hms_status"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),

                             # Status of the facility and facility operations
                             Field("facility_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_facility_status_opts)),
                                   label = T("Facility Status"),
                                   represent = lambda opt: \
                                               hms_facility_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("facility_operations", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_resource_status_opts)),
                                   label = T("Facility Operations"),
                                   represent = lambda opt: \
                                               hms_resource_status_opts.get(opt,
                                                                UNKNOWN_OPT)),

                             # Clinical status and clinical operations
                             Field("clinical_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_clinical_status_opts)),
                                   label = T("Clinical Status"),
                                   represent = lambda opt: \
                                               hms_clinical_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("clinical_operations", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_resource_status_opts)),
                                   label = T("Clinical Operations"),
                                   represent = lambda opt: \
                                               hms_resource_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("security_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_security_status_opts)),
                                   label = T("Security Status"),
                                   represent = lambda opt: \
                                               hms_security_status_opts.get(opt,
                                                                UNKNOWN_OPT)),

                             # Staffing status
                             Field("staffing", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_resource_status_opts)),
                                   label = T("Staffing Level"),
                                   represent = lambda opt: \
                                               hms_resource_status_opts.get(opt,
                                                                UNKNOWN_OPT)),

                             # Emergency Room Status
                             Field("ems_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_ems_traffic_opts)),
                                   label = T("ER Status"),
                                   represent = lambda opt: \
                                               hms_ems_traffic_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("ems_reason",
                                   length=128,
                                   label = T("ER Status Reason")),

                             # Operating Room Status
                             Field("or_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                        hms_or_status_opts)),
                                   label = T("OR Status"),
                                   represent = lambda opt: \
                                               hms_or_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("or_reason",
                                   length=128,
                                   label = T("OR Status Reason")),

                             # Morgue status and capacity
                             Field("morgue_status", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(
                                                    hms_morgue_status_opts)),
                                   label = T("Morgue Status"),
                                   represent = lambda opt: \
                                               hms_clinical_status_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             Field("morgue_units", "integer",
                                   requires = IS_NULL_OR(
                                                IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Morgue Units Available"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),

                             Field("access_status", "text",
                                   label = T("Road Conditions")),

                              *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Status Report"),
            title_display = T("Status Report"),
            title_list = T("Status Report"),
            title_update = T("Edit Status Report"),
            title_search = T("Search Status Reports"),
            subtitle_create = T("New Status Report"),
            label_list_button = T("List Status Reports"),
            label_create_button = T("Add Status Report"),
            msg_record_created = T("Status Report added"),
            msg_record_modified = T("Status Report updated"),
            msg_record_deleted = T("Status Report deleted"),
            msg_list_empty = T("No status information currently available"))

        # ---------------------------------------------------------------------
        # Contacts
        #
        tablename = "hms_contact"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             person_id(label = T("Contact"),
                                       requires = IS_ONE_OF(db, "pr_person.id",
                                                            self.pr_person_represent,
                                                            orderby="pr_person.first_name",
                                                            sort=True)),
                              Field("title", label = T("Job Title")),
                              Field("phone", label = T("Phone"),
                                    requires = IS_NULL_OR(s3_phone_requires)),
                              Field("mobile", label = T("Mobile"),
                                    requires = IS_NULL_OR(s3_phone_requires)),
                              Field("email", label = T("Email"),
                                    requires = IS_NULL_OR(IS_EMAIL())),
                              Field("fax", label = T("Fax"),
                                    requires = IS_NULL_OR(s3_phone_requires)),
                              Field("skype", label = T("Skype ID")),
                              Field("website", label=T("Website")),
                              *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact"),
            title_search = T("Search Contacts"),
            subtitle_create = T("Add New Contact"),
            label_list_button = T("List Contacts"),
            label_create_button = T("Add Contact"),
            msg_record_created = T("Contact information added"),
            msg_record_modified = T("Contact information updated"),
            msg_record_deleted = T("Contact information deleted"),
            msg_list_empty = T("No contacts currently registered"))

        # Resource configuration
        configure(tablename,
                  mark_required = ["person_id"],
                  list_fields=["id",
                               "person_id",
                               "title",
                               "phone",
                               "mobile",
                               "email",
                               "fax",
                               "skype"],
                  main="person_id",
                  extra="title")

        # ---------------------------------------------------------------------
        # Bed Capacity
        #
        hms_bed_type_opts = {
            1: T("Adult ICU"),
            2: T("Pediatric ICU"),
            3: T("Neonatal ICU"),
            4: T("Emergency Department"),
            5: T("Nursery Beds"),
            6: T("General Medical/Surgical"),
            7: T("Rehabilitation/Long Term Care"),
            8: T("Burn ICU"),
            9: T("Pediatrics"),
            10: T("Adult Psychiatric"),
            11: T("Pediatric Psychiatric"),
            12: T("Negative Flow Isolation"),
            13: T("Other Isolation"),
            14: T("Operating Rooms"),
            15: T("Cholera Treatment"),
            99: T("Other")
        }

        tablename = "hms_bed_capacity"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             Field("unit_id", length=128, unique=True,
                                   readable=False,
                                   writable=False),
                             Field("bed_type", "integer",
                                   requires = IS_IN_SET(hms_bed_type_opts,
                                                        zero=None),
                                   default = 6,
                                   label = T("Bed Type"),
                                   represent = lambda opt: \
                                               hms_bed_type_opts.get(opt,
                                                                UNKNOWN_OPT)),
                             s3_datetime(label = T("Date of Report"),
                                         empty=False,
                                         future=0,
                                         ),
                             Field("beds_baseline", "integer",
                                   default = 0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Baseline Number of Beds"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("beds_available", "integer",
                                   default = 0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Available Beds"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("beds_add24", "integer",
                                   default = 0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999)),
                                   label = T("Additional Beds / 24hrs"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             s3_comments(),
                             *s3_meta_fields())

        # Field configuration
        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Bed Type"),
            title_display = T("Bed Capacity"),
            title_list = T("Bed Capacity"),
            title_update = T("Update Unit"),
            title_search = T("Search Units"),
            subtitle_create = T("Add Unit"),
            label_list_button = T("List Units"),
            label_create_button = T("Add Unit"),
            label_delete_button = T("Delete Unit"),
            msg_record_created = T("Unit added"),
            msg_record_modified = T("Unit updated"),
            msg_record_deleted = T("Unit deleted"),
            msg_list_empty = T("No units currently registered"))

        # Resource configuration
        configure(tablename,
                  onvalidation = self.hms_bed_capacity_onvalidation,
                  onaccept = self.hms_bed_capacity_onaccept,
                  ondelete = self.hms_bed_capacity_onaccept,
                  list_fields=["id",
                               "unit_name",
                               "bed_type",
                               "date",
                               "beds_baseline",
                               "beds_available",
                               "beds_add24"],
                  main="hospital_id",
                  extra="id")

        # ---------------------------------------------------------------------
        # Services
        #
        tablename = "hms_services"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             Field("burn", "boolean", default=False,
                                   label = T("Burn")),
                             Field("card", "boolean", default=False,
                                   label = T("Cardiology")),
                             Field("dial", "boolean", default=False,
                                   label = T("Dialysis")),
                             Field("emsd", "boolean", default=False,
                                   label = T("Emergency Department")),
                             Field("infd", "boolean", default=False,
                                   label = T("Infectious Diseases")),
                             Field("neon", "boolean", default=False,
                                   label = T("Neonatology")),
                             Field("neur", "boolean", default=False,
                                   label = T("Neurology")),
                             Field("pedi", "boolean", default=False,
                                   label = T("Pediatrics")),
                             Field("surg", "boolean", default=False,
                                   label = T("Surgery")),
                             Field("labs", "boolean", default=False,
                                   label = T("Clinical Laboratory")),
                             Field("tran", "boolean", default=False,
                                   label = T("Ambulance Service")),
                             Field("tair", "boolean", default=False,
                                   label = T("Air Transport Service")),
                             Field("trac", "boolean", default=False,
                                   label = T("Trauma Center")),
                             Field("psya", "boolean", default=False,
                                   label = T("Psychiatrics/Adult")),
                             Field("psyp", "boolean", default=False,
                                   label = T("Psychiatrics/Pediatric")),
                             Field("obgy", "boolean", default=False,
                                   label = T("Obstetrics/Gynecology")),
                             *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Service Profile"),
            title_display = T("Services Available"),
            title_list = T("Services Available"),
            title_update = T("Update Service Profile"),
            title_search = T("Search Service Profiles"),
            subtitle_create = T("Add Service Profile"),
            label_list_button = T("List Service Profiles"),
            label_create_button = T("Add Service Profile"),
            label_delete_button = T("Delete Service Profile"),
            msg_record_created = T("Service profile added"),
            msg_record_modified = T("Service profile updated"),
            msg_record_deleted = T("Service profile deleted"),
            msg_list_empty = T("No service profile available"))

        # Resource configuration
        configure(tablename,
                  list_fields = ["id"],
                  main="hospital_id",
                  extra="id")

        # ---------------------------------------------------------------------
        # Resources (multiple) - @todo: to be completed!
        #
        tablename = "hms_resources"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             Field("type"),
                             Field("description"),
                             Field("quantity"),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Report Resource"),
            title_display = T("Resource Details"),
            title_list = T("Resources"),
            title_update = T("Edit Resource"),
            title_search = T("Search Resources"),
            subtitle_create = T("Add New Resource"),
            label_list_button = T("List Resources"),
            label_create_button = T("Add Resource"),
            label_delete_button = T("Delete Resource"),
            msg_record_created = T("Resource added"),
            msg_record_modified = T("Resource updated"),
            msg_record_deleted = T("Resource deleted"),
            msg_list_empty = T("No resources currently reported"))

        # Resource configuration
        configure(tablename,
                  list_fields=["id"],
                  main="hospital_id",
                  extra="id")

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return Storage(hms_hospital_id=hospital_id)

    # -------------------------------------------------------------------------
    def defaults(self):

        hospital_id = S3ReusableField("hospital_id", "integer",
                                      readable=False,
                                      writable=False)

        return Storage(hms_hospital_id=hospital_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_hospital_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.hms_hospital
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_bed_capacity_onvalidation(form):
        """ Bed Capacity Validation """

        db = current.db
        htable = db.hms_hospital
        ctable = db.hms_bed_capacity
        hospital_id = ctable.hospital_id.update
        bed_type = form.vars.bed_type
        query = (ctable.hospital_id == hospital_id) & \
                (ctable.bed_type == bed_type)
        row = db(query).select(ctable.id,
                               limitby=(0, 1)).first()
        if row and str(row.id) != current.request.post_vars.id:
            form.errors["bed_type"] = current.T("Bed type already registered")
        elif "unit_id" not in form.vars:
            query = htable.id == hospital_id
            hospital = db(query).select(htable.uuid,
                                        limitby=(0, 1)).first()
            if hospital:
                form.vars.unit_id = "%s-%s" % (hospital.uuid, bed_type)

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_bed_capacity_onaccept(form):
        """ Updates the number of total/available beds of a hospital """

        if isinstance(form, Row):
            formvars = form
        else:
            formvars = form.vars

        db = current.db
        ctable = db.hms_bed_capacity
        htable = db.hms_hospital
        query = ((ctable.id == formvars.id) &
                 (htable.id == ctable.hospital_id))
        hospital = db(query).select(htable.id,
                                    limitby=(0, 1))

        if hospital:
            hospital = hospital.first()
            a_beds = ctable.beds_available.sum()
            t_beds = ctable.beds_baseline.sum()
            query = (ctable.hospital_id == hospital.id) & \
                    (ctable.deleted == False)
            count = db(query).select(a_beds, t_beds)
            if count:
                a_beds = count[0]._extra[a_beds]
                t_beds = count[0]._extra[t_beds]

            db(htable.id == hospital.id).update(total_beds=t_beds,
                                                available_beds=a_beds)

# =============================================================================
class CholeraTreatmentCapabilityModel(S3Model):

    names = ["hms_ctc"]

    def model(self):

        T = current.T
        hospital_id = self.hms_hospital_id

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Cholera Treatment Capability
        #
        hms_problem_types = {
            1: T("Security problems"),
            2: T("Hygiene problems"),
            3: T("Sanitation problems"),
            4: T("Improper handling of dead bodies"),
            5: T("Improper decontamination"),
            6: T("Understaffed"),
            7: T("Lack of material"),
            8: T("Communication problems"),
            9: T("Information gaps")
        }

        tablename = "hms_ctc"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             Field("ctc", "boolean", default=False,
                                   represent = lambda opt: \
                                               opt and T("yes") or T("no"),
                                   label = T("Cholera-Treatment-Center")),
                             Field("number_of_patients", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                   label = T("Current number of patients"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("cases_24", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                   label = T("New cases in the past 24h"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("deaths_24", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999)),
                                   label = T("Deaths in the past 24h"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             #Field("staff_total", "integer", default=0),
                             Field("icaths_available", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Infusion catheters available"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("icaths_needed_24", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Infusion catheters needed per 24h"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("infusions_available", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Infusions available"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("infusions_needed_24", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Infusions needed per 24h"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             #Field("infset_available", "integer", default=0),
                             #Field("infset_needed_24", "integer", default=0),
                             Field("antibiotics_available", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Antibiotics available"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("antibiotics_needed_24", "integer", default=0,
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999999)),
                                   label = T("Antibiotics needed per 24h"),
                                   represent = lambda v, row=None: IS_INT_AMOUNT.represent(v)),
                             Field("problem_types", "list:integer",
                                   requires = IS_EMPTY_OR(IS_IN_SET(hms_problem_types,
                                                                    zero=None,
                                                                    multiple=True)),
                                   represent = lambda optlist: \
                                               optlist and ", ".join(map(str,optlist)) or T("N/A"),
                                   label = T("Current problems, categories")),
                             Field("problem_details", "text",
                                   label = T("Current problems, details")),
                             s3_comments(),
                             *s3_meta_fields())

        # Field configuration
        table.modified_on.label = T("Last updated on")
        table.modified_on.readable = True
        table.modified_by.label = T("Last updated by")
        table.modified_by.readable = True

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Cholera Treatment Capability Information"),
            title_display = T("Cholera Treatment Capability"),
            title_list = T("Cholera Treatment Capability"),
            title_update = T("Update Cholera Treatment Capability Information"),
            title_search = T("Search Status"),
            subtitle_create = T("Add Status"),
            label_list_button = T("List Statuses"),
            label_create_button = T("Add Status"),
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status added"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No status information available"))

        # Resource configuration
        configure(tablename,
                  list_fields = ["id"],
                  subheadings = {
                        "Activities": "ctc",
                        "Medical Supplies Availability": "icaths_available",
                        "Current Problems": "problem_types",
                        "Comments": "comments"
                  })

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return Storage()

    # -------------------------------------------------------------------------
    def defaults(self):

        return Storage()

# =============================================================================
class HospitalActivityReportModel(S3Model):

    names = ["hms_activity"]

    def model(self):

        T = current.T

        hospital_id = self.hms_hospital_id
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Activity
        #
        is_number_of_patients = IS_NULL_OR(IS_INT_IN_RANGE(0, 9999))
        represent_int_amount = lambda v, row=None: IS_INT_AMOUNT.represent(v)
        tablename = "hms_activity"
        table = define_table(tablename,
                             hospital_id(ondelete="CASCADE"),
                             s3_datetime(label = T("Date & Time"),
                                         empty=False,
                                         future=0),
                             # Current Number of Patients
                             Field("patients", "integer",
                                   requires = is_number_of_patients,
                                   default = 0,
                                   label = T("Number of Patients"),
                                   represent = represent_int_amount),
                             # Admissions in the past 24 hours
                             Field("admissions24", "integer",
                                   requires = is_number_of_patients,
                                   default = 0,
                                   label = T("Admissions/24hrs"),
                                   represent = represent_int_amount),
                             # Discharges in the past 24 hours
                             Field("discharges24", "integer",
                                   requires = is_number_of_patients,
                                   default = 0,
                                   label = T("Discharges/24hrs"),
                                   represent = represent_int_amount),
                             # Deaths in the past 24 hours
                             Field("deaths24", "integer",
                                   requires = is_number_of_patients,
                                   default = 0,
                                   label = T("Deaths/24hrs"),
                                   represent = represent_int_amount),
                             Field("comment", length=128),
                             *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Activity Report"),
            title_display = T("Activity Report"),
            title_list = T("Activity Reports"),
            title_update = T("Update Activity Report"),
            title_search = T("Search Activity Report"),
            subtitle_create = T("Add Activity Report"),
            label_list_button = T("List Activity Reports"),
            label_create_button = T("Add Report"),
            label_delete_button = T("Delete Report"),
            msg_record_created = T("Report added"),
            msg_record_modified = T("Report updated"),
            msg_record_deleted = T("Report deleted"),
            msg_list_empty = T("No reports currently available"))

        # Resource configuration
        configure(tablename,
                  onaccept = self.hms_activity_onaccept,
                  list_fields=["id",
                               "date",
                               "patients",
                               "admissions24",
                               "discharges24",
                               "deaths24",
                               "comment"],
                  main="hospital_id",
                  extra="id")

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return Storage()

    # -------------------------------------------------------------------------
    def defaults(self):

        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_activity_onaccept(form):

        db = current.db
        atable = db.hms_activity
        htable = db.hms_hospital
        query = ((atable.id == form.vars.id) & \
                 (htable.id == atable.hospital_id))
        hospital = db(query).select(htable.id,
                                    htable.modified_on,
                                    limitby=(0, 1)).first()
        timestmp = form.vars.date
        if hospital and hospital.modified_on < timestmp:
            hospital.update_record(modified_on=timestmp)

# =============================================================================
def hms_hospital_rheader(r, tabs=[]):
    """ Page header for component resources """

    rheader = None
    if r.representation == "html":
        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings
        tablename, record = s3_rheader_resource(r)
        if tablename == "hms_hospital" and record:

            if not tabs:
                tabs = [(T("Details"), ""),
                        (T("Status"), "status"),
                        (T("Contacts"), "contact"),
                        (T("Images"), "image"),
                        (T("Services"), "services"),
                        (T("Bed Capacity"), "bed_capacity"),
                       ]

                if settings.get_hms_activity_reports():
                    tabs.append((T("Activity Report"), "activity"))

                if settings.get_hms_track_ctc():
                    tabs.append((T("Cholera Treatment Capability"), "ctc"))

                tabs += [
                        (T("Staff"), "human_resource"),
                        (T("Assign Staff"), "human_resource_site"),
                        ]
                try:
                    tabs = tabs + s3db.req_tabs(r)
                except:
                    pass
                try:
                    tabs = tabs + s3db.inv_tabs(r)
                except:
                    pass

                tabs.append((T("User Roles"), "roles"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            hospital = record

            table = s3db.hms_hospital
            ltable = s3db.gis_location
            stable = s3db.hms_status

            query = (stable.hospital_id == hospital.id)
            s = current.db(query).select(limitby=(0, 1)).first()

            status = lambda k: (s is not None and
                                [stable[k].represent(s[k])] or
                                [T("n/a")])[0]

            rheader = DIV(TABLE(

                TR(TH("%s: " % T("Name")),
                    hospital.name,
                    TH("%s: " % T("EMS Status")),
                    status("ems_status")),

                TR(TH("%s: " % T("Location")),
                    ltable[hospital.location_id] and \
                        ltable[hospital.location_id].name or "unknown",
                    TH("%s: " % T("Facility Status")),
                    status("facility_status")),

                TR(TH("%s: " % T("Total Beds")),
                    hospital.total_beds,
                    TH("%s: " % T("Clinical Status")),
                    status("clinical_status")),

                TR(TH("%s: " % T("Available Beds")),
                    hospital.available_beds,
                    TH("%s: " % T("Security Status")),
                    status("security_status"))

                    ), rheader_tabs)

        if rheader and r.component and r.component.name == "req":
            rheader.append(s3db.req_helptext_script)

    return rheader

# END =========================================================================
