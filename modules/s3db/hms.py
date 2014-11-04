# -*- coding: utf-8 -*-

""" Sahana Eden Hospital Management System Model

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

__all__ = ("HospitalDataModel",
           "CholeraTreatmentCapabilityModel",
           "HospitalActivityReportModel",
           "hms_hospital_rheader"
           )

from gluon import *
from gluon.storage import Storage
try:
    from gluon.dal.objects import Row
except ImportError:
    # old web2py
    from gluon.dal import Row

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class HospitalDataModel(S3Model):

    names = ("hms_hospital",
             "hms_hospital_tag",
             "hms_contact",
             "hms_bed_capacity",
             "hms_services",
             "hms_image",
             "hms_resources",
             "hms_hospital_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        add_components = self.add_components
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
            31: T("Long-term care"),
            41: T("Emergency Treatment Centre"),
            42: T("Triage"),
            43: T("Holding Center"),
            44: T("Transit Center"),
            98: T("Other"),
            99: T("Unknown"),
        } #: Facility Type Options

        # Status opts defined here for use in Search widgets
        hms_facility_status_opts = {
            1: T("Normal"),
            2: T("Compromised"),
            3: T("Evacuating"),
            4: T("Closed"),
            5: T("Pending"),
            99: T("No Response")
        } #: Facility Status Options

        hms_power_supply_type_opts = {
            1: T("Grid"),
            2: T("Generator"),
            98: T("Other"),
            99: T("None"),
        } #: Power Supply Type Options

        tablename = "hms_hospital"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),

                     # UID assigned by Local Government
                     # required for EDXL-HAVE
                     # @ToDo: Move to a KV in hms_hospital_tag table?
                     Field("gov_uuid", unique=True, length=128,
                           label = T("Government UID"),
                           requires = IS_EMPTY_OR(
                                       IS_NOT_ONE_OF(db,
                                           "%s.gov_uuid" % tablename)
                                       ),
                           readable = False,
                           writable = False,
                           ),

                     # Name of the facility
                     Field("name", notnull=True,
                           length=64, # Mayon compatibility
                           label = T("Name"),
                           ),

                     # Alternate name, or name in local language
                     Field("aka1",
                           label = T("Other Name"),
                           ),

                     # Alternate name, or name in local language
                     Field("aka2",
                           label = T("Other Name"),
                           readable = False,
                           writable = False,
                           ),

                     # Mayon compatibility
                     Field("code", length=10,
                           #notnull=True, unique=True,
                           label = T("Code"),
                           ),

                     Field("facility_type", "integer",
                           default = 1,
                           label = T("Facility Type"),
                           represent = lambda opt: \
                                       hms_facility_type_opts.get(opt, NONE),
                           requires = IS_EMPTY_OR(
                                       IS_IN_SET(hms_facility_type_opts)
                                       ),
                           ),
                     self.org_organisation_id(
                        requires = self.org_organisation_requires(updateable=True),
                        ),
                     self.gis_location_id(),

                     # Address fields:
                     # @todo: Deprecate these & use location_id in HAVE export
                     Field("address",
                           label = T("Address"),
                           ),
                     Field("postcode",
                           label = settings.get_ui_label_postcode(),
                           ),
                     Field("city"),

                     Field("phone_exchange",
                           label = T("Phone/Exchange (Switchboard)"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),

                     Field("phone_business",
                           label = T("Phone/Business"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("phone_emergency",
                           label = T("Phone/Emergency"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("website",
                           label = T("Website"),
                           represent = s3_url_represent,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("email",
                           label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     Field("fax",
                           label = T("Fax"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("total_beds", "integer",
                           label = T("Total Beds"),
                           #readable = False,
                           writable = False,
                           represent = lambda v: NONE if v is None else v,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("available_beds", "integer",
                           label = T("Available Beds"),
                           #readable = False,
                           writable = False,
                           represent = lambda v: NONE if v is None else v,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("doctors", "integer",
                           label = T("Number of doctors"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("nurses", "integer",
                           label = T("Number of nurses"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("non_medical_staff", "integer",
                           label = T("Number of non-medical staff"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: \
                                       (opt and [T("Obsolete")] or [NONE])[0],
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_HOSPITAL = T("Create Hospital")
        crud_strings[tablename] = Storage(
            label_create = ADD_HOSPITAL,
            title_display = T("Hospital Details"),
            title_list = T("Hospitals"),
            title_update = T("Edit Hospital"),
            title_map = T("Map of Hospitals"),
            label_list_button = T("List Hospitals"),
            label_delete_button = T("Delete Hospital"),
            msg_record_created = T("Hospital information added"),
            msg_record_modified = T("Hospital information updated"),
            msg_record_deleted = T("Hospital information deleted"),
            msg_list_empty = T("No Hospitals currently registered"))

        filter_widgets = [
                S3TextFilter(["name",
                              "code",
                              "comments",
                              "organisation_id$name",
                              "organisation_id$acronym",
                              "location_id$name",
                              "location_id$L1",
                              "location_id$L2",
                              ],
                             label=T("Name"),
                             _class="filter-search",
                             ),
                S3OptionsFilter("facility_type",
                                label = T("Type"),
                                represent = "%(name)s",
                                #hidden=True,
                                ),
                S3LocationFilter("location_id",
                                 label = T("Location"),
                                 levels = ("L0", "L1", "L2"),
                                 #hidden=True,
                                 ),
                S3OptionsFilter("status.facility_status",
                                label = T("Status"),
                                options = hms_facility_status_opts,
                                #represent="%(name)s",
                                #hidden=True,
                                ),
                S3OptionsFilter("status.power_supply_type",
                                label = T("Power"),
                                options = hms_power_supply_type_opts,
                                #represent = "%(name)s",
                                #hidden=True,
                                ),
                S3RangeFilter("total_beds",
                              label = T("Total Beds"),
                              #represent = "%(name)s",
                              #hidden = True,
                              ),
                ]

        report_fields = ["name",
                         (T("Type"), "facility_type"),
                         #"organisation_id",
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         (T("Status"), "status.facility_status"),
                         "status.power_supply_type",
                         "total_beds",
                         "available_beds",
                         ]

        # Resource configuration
        configure(tablename,
                  deduplicate = self.hms_hospital_duplicate,
                  filter_widgets = filter_widgets,
                  list_fields = ["id",
                                 #"gov_uuid",
                                 "name",
                                 "facility_type",
                                 "status.facility_status",
                                 "status.power_supply_type",
                                 #"organisation_id",
                                 "location_id$L1",
                                 "location_id$L2",
                                 "location_id$L3",
                                 #"phone_exchange",
                                 "total_beds",
                                 "available_beds",
                                 ],
                  onaccept = self.hms_hospital_onaccept,
                  report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows="location_id$L2",
                                         cols="status.facility_status",
                                         fact="count(name)",
                                         totals=True)
                        ),
                  super_entity = ("org_site", "doc_entity", "pr_pentity"),
                  )

        # Reusable field
        hms_hospital_id_comment = S3AddResourceLink(c="hms",
                                                    f="hospital",
                                                    label=ADD_HOSPITAL,
                                                    title=T("Hospital"),
                                                    tooltip=T("If you don't see the Hospital in the list, you can add a new one by clicking link 'Create Hospital'."))

        represent = S3Represent(lookup=tablename)
        hospital_id = S3ReusableField("hospital_id", "reference %s" % tablename,
                                      comment = hms_hospital_id_comment,
                                      label = T("Hospital"),
                                      ondelete = "RESTRICT",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "hms_hospital.id",
                                                              represent
                                                              )),
                                      sortby = "name",
                                      )

        # Components
        single = dict(joinby="hospital_id", multiple=False)
        multiple = "hospital_id"
        add_components(tablename,
                       hms_status=single,
                       hms_contact=multiple,
                       hms_bed_capacity=multiple,
                       hms_services=single,
                       hms_resources=multiple,
                       )

        # Optional components
        if settings.get_hms_track_ctc():
            add_components(tablename, hms_ctc=single)
        if settings.get_hms_activity_reports():
            add_components(tablename, hms_activity=multiple)

        # Custom Method to Assign HRs
        self.set_method("hms", "hospital",
                        method = "assign",
                        action = self.hrm_AssignMethod(component="human_resource_site"))

        # ---------------------------------------------------------------------
        # Hosptial Tags
        # - Key-Value extensions
        # - can be used to identify a Source (GPS, Imagery, Wikipedia, etc)
        # - can link Hospitals to other Systems, such as:
        #   * Government IDs
        #   * PAHO
        #   * OpenStreetMap (although their IDs can change over time)
        #   * WHO
        #   * Wikipedia URL
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "hms_hospital_tag"
        self.define_table(tablename,
                          hospital_id(empty = False,
                                      ondelete = "CASCADE",
                                      ),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        configure(tablename,
                  deduplicate = self.hms_hospital_tag_deduplicate,
                  )

        # ---------------------------------------------------------------------
        # Hospital status
        #
        hms_resource_status_opts = {
            1: T("Adequate"),
            2: T("Insufficient")
        } #: Resource Status Options

        hms_clinical_status_opts = {
            1: T("Normal"),
            2: T("Full"),
            3: T("Closed")
        } #: Clinical Status Options

        hms_facility_damage_opts = {
            1: T("Flooding"),
            2: T("Power Outage"),
        } #: Facility Damage Options

        hms_gas_supply_type_opts = {
            98: T("Other"),
            99: T("None"),
        } #: Gas Supply Type Options

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

        def hms_facility_damage_multirepresent(opt):
            """ Multi Represent """
            set = hms_facility_damage_opts
            if isinstance(opt, (list, tuple)):
                opts = opt
                try:
                    vals = [str(set.get(o)) for o in opts]
                except:
                    return None
            elif isinstance(opt, int):
                opts = [opt]
                vals = str(set.get(opt))
            else:
                return NONE

            if len(opts) > 1:
                vals = ", ".join(vals)
            else:
                vals = len(vals) and vals[0] or ""
            return vals

        tablename = "hms_status"
        define_table(tablename,
                     hospital_id(ondelete = "CASCADE"),

                     # Status of the facility and facility operations
                     Field("facility_status", "integer",
                           label = T("Facility Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_facility_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_facility_status_opts)),
                           ),
                     s3_date("date_reopening",
                             label = T("Estimated Reopening Date"),
                             ),
                     Field("facility_operations", "integer",
                           label = T("Facility Operations"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_resource_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_resource_status_opts)),
                           ),

                     # Facility Status Details
                     Field("damage", "list:integer",
                           label = T("Damage sustained"),
                           represent = hms_facility_damage_multirepresent,
                           requires = IS_EMPTY_OR(
                                      IS_IN_SET(hms_facility_damage_opts,
                                                multiple=True)),
                           widget = CheckboxesWidgetS3.widget,
                           ),
                     Field("power_supply_type", "integer",
                           label = T("Power Supply Type"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_power_supply_type_opts.get(opt,
                                                                      UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                      IS_IN_SET(hms_power_supply_type_opts,
                                                zero=None)),
                           ),
                     Field("gas_supply_type", "integer",
                           label = T("Gas Supply Type"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_gas_supply_type_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_gas_supply_type_opts,
                                                  zero=None)),
                           ),
                     Field("gas_supply_capacity", "integer",
                           label = T("Gas Supply Left (in hours)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999)),
                           ),

                     # Clinical status and clinical operations
                     Field("clinical_status", "integer",
                           label = T("Clinical Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_clinical_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_clinical_status_opts)),
                           ),
                     Field("clinical_operations", "integer",
                           label = T("Clinical Operations"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_resource_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_resource_status_opts)),
                           ),
                     Field("security_status", "integer",
                           label = T("Security Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_security_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_security_status_opts)),
                           ),

                     # Staffing status
                     Field("staffing", "integer",
                           label = T("Staffing Level"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_resource_status_opts.get(opt,
                                                                    UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_resource_status_opts)),
                           ),

                     # Emergency Room Status
                     Field("ems_status", "integer",
                           label = T("ER Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_ems_traffic_opts.get(opt,
                                                                UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_ems_traffic_opts)),
                           ),
                     Field("ems_reason", length=128,
                           label = T("ER Status Reason"),
                           ),

                     # Operating Room Status
                     Field("or_status", "integer",
                           label = T("OR Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_or_status_opts.get(opt,
                                                              UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_or_status_opts)),
                           ),
                     Field("or_reason", length=128,
                           label = T("OR Status Reason"),
                           ),

                     # Morgue status and capacity
                     Field("morgue_status", "integer",
                           label = T("Morgue Status"),
                           represent = lambda opt: \
                                       NONE if opt is None else \
                                       hms_morgue_status_opts.get(opt,
                                                                  UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_morgue_status_opts)),
                           ),
                     Field("morgue_units", "integer",
                           label = T("Morgue Units Available"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),

                     Field("access_status", "text",
                           label = T("Road Conditions")),

                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Status Report"),
            title_display = T("Status Report"),
            title_list = T("Status Report"),
            title_update = T("Edit Status Report"),
            label_list_button = T("List Status Reports"),
            msg_record_created = T("Status Report added"),
            msg_record_modified = T("Status Report updated"),
            msg_record_deleted = T("Status Report deleted"),
            msg_list_empty = T("No status information currently available"))

        # ---------------------------------------------------------------------
        # Contacts
        #
        tablename = "hms_contact"
        define_table(tablename,
                     hospital_id(ondelete = "CASCADE"),
                     self.pr_person_id(empty = False,
                                       label = T("Contact"),
                                       ),
                     Field("title",
                           label = T("Job Title"),
                           ),
                     Field("phone",
                           label = T("Phone"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("mobile",
                           label = settings.get_ui_label_mobile_phone(),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("email",
                           label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     Field("fax",
                           label = T("Fax"),
                           requires = IS_EMPTY_OR(s3_phone_requires),
                           ),
                     Field("skype",
                           label = T("Skype ID"),
                           ),
                     Field("website",
                           label = T("Website"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact"),
            label_list_button = T("List Contacts"),
            msg_record_created = T("Contact information added"),
            msg_record_modified = T("Contact information updated"),
            msg_record_deleted = T("Contact information deleted"),
            msg_list_empty = T("No contacts currently registered"))

        # Resource configuration
        configure(tablename,
                  extra = "title",
                  list_fields = ["id",
                                 "person_id",
                                 "title",
                                 "phone",
                                 "mobile",
                                 "email",
                                 "fax",
                                 "skype"
                                 ],
                  main = "person_id",
                  mark_required = ("person_id",),
                  )

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
            16: T("Ebola Treatment"),
            99: T("Other")
        }

        tablename = "hms_bed_capacity"
        define_table(tablename,
                     hospital_id(ondelete = "CASCADE"),
                     Field("unit_id", length=128, unique=True,
                           readable = False,
                           writable = False),
                     Field("bed_type", "integer",
                           default = 6,
                           label = T("Bed Type"),
                           represent = lambda opt: \
                                       hms_bed_type_opts.get(opt,
                                                             UNKNOWN_OPT),
                           requires = IS_IN_SET(hms_bed_type_opts,
                                                zero=None),
                           ),
                     s3_datetime(empty = False,
                                 label = T("Date of Report"),
                                 future = 0,
                                 ),
                     Field("beds_baseline", "integer",
                           default = 0,
                           label = T("Baseline Number of Beds"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("beds_available", "integer",
                           default = 0,
                           label = T("Available Beds"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),
                     Field("beds_add24", "integer",
                           default = 0,
                           label = T("Additional Beds / 24hrs"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999)),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Field configuration
        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Bed Type"),
            title_display = T("Bed Capacity"),
            title_list = T("Bed Capacity"),
            title_update = T("Update Unit"),
            label_list_button = T("List Units"),
            label_delete_button = T("Delete Unit"),
            msg_record_created = T("Unit added"),
            msg_record_modified = T("Unit updated"),
            msg_record_deleted = T("Unit deleted"),
            msg_list_empty = T("No units currently registered"))

        # Resource configuration
        configure(tablename,
                  extra = "id",
                  list_fields = ["id",
                                 "unit_name",
                                 "bed_type",
                                 "date",
                                 "beds_baseline",
                                 "beds_available",
                                 "beds_add24"
                                 ],
                  main = "hospital_id",
                  onaccept = self.hms_bed_capacity_onaccept,
                  ondelete = self.hms_bed_capacity_onaccept,
                  onvalidation = self.hms_bed_capacity_onvalidation,
                  )

        # ---------------------------------------------------------------------
        # Services
        #
        tablename = "hms_services"
        define_table(tablename,
                     hospital_id(ondelete = "CASCADE"),
                     Field("burn", "boolean",
                           default = False,
                           label = T("Burn"),
                           ),
                     Field("card", "boolean",
                           default = False,
                           label = T("Cardiology"),
                           ),
                     Field("dial", "boolean",
                           default = False,
                           label = T("Dialysis"),
                           ),
                     Field("emsd", "boolean",
                           default = False,
                           label = T("Emergency Department"),
                           ),
                     Field("infd", "boolean",
                           default = False,
                           label = T("Infectious Diseases"),
                           ),
                     Field("neon", "boolean",
                           default = False,
                           label = T("Neonatology"),
                           ),
                     Field("neur", "boolean",
                           default = False,
                           label = T("Neurology"),
                           ),
                     Field("pedi", "boolean",
                           default = False,
                           label = T("Pediatrics"),
                           ),
                     Field("surg", "boolean",
                           default = False,
                           label = T("Surgery"),
                           ),
                     Field("labs", "boolean",
                           default = False,
                           label = T("Clinical Laboratory"),
                           ),
                     Field("tran", "boolean",
                           default = False,
                           label = T("Ambulance Service"),
                           ),
                     Field("tair", "boolean",
                           default = False,
                           label = T("Air Transport Service"),
                           ),
                     Field("trac", "boolean",
                           default = False,
                           label = T("Trauma Center"),
                           ),
                     Field("psya", "boolean",
                           default = False,
                           label = T("Psychiatrics/Adult"),
                           ),
                     Field("psyp", "boolean",
                           default = False,
                           label = T("Psychiatrics/Pediatric"),
                           ),
                     Field("obgy", "boolean",
                           default = False,
                           label = T("Obstetrics/Gynecology"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Service Profile"),
            title_display = T("Services Available"),
            title_list = T("Services Available"),
            title_update = T("Update Service Profile"),
            label_list_button = T("List Service Profiles"),
            label_delete_button = T("Delete Service Profile"),
            msg_record_created = T("Service profile added"),
            msg_record_modified = T("Service profile updated"),
            msg_record_deleted = T("Service profile deleted"),
            msg_list_empty = T("No service profile available"))

        # Resource configuration
        configure(tablename,
                  extra = "id",
                  list_fields = ["id"],
                  main = "hospital_id",
                  )

        # ---------------------------------------------------------------------
        # Resources (multiple) - @todo: to be completed!
        #
        tablename = "hms_resources"
        define_table(tablename,
                     hospital_id(ondelete = "CASCADE"),
                     Field("type"),
                     Field("description"),
                     Field("quantity"),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Report Resource"),
            title_display = T("Resource Details"),
            title_list = T("Resources"),
            title_update = T("Edit Resource"),
            label_list_button = T("List Resources"),
            label_delete_button = T("Delete Resource"),
            msg_record_created = T("Resource added"),
            msg_record_modified = T("Resource updated"),
            msg_record_deleted = T("Resource deleted"),
            msg_list_empty = T("No resources currently reported"))

        # Resource configuration
        configure(tablename,
                  extra = "id",
                  list_fields = ["id"],
                  main = "hospital_id",
                  )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return dict(hms_hospital_id = hospital_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(hms_hospital_id = lambda **attr: dummy("hospital_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_hospital_duplicate(item):
        """
            Hospital record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        data = item.data
        #org = data.get("organisation_id")
        address = data.get("address")

        table = item.table
        query = (table.name == data.name)
        #if org:
        #    query = query & (table.organisation_id == org)
        if address:
            query = query & (table.address == address)
        row = current.db(query).select(table.id,
                                       limitby=(0, 1)).first()
        if row:
            item.id = row.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_hospital_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("hms_hospital", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def hms_hospital_tag_deduplicate(item):
        """
           If the record is a duplicate then it will set the item method to update
        """

        data = item.data
        tag = data.get("tag", None)
        hospital_id = data.get("hospital_id", None)

        if not tag or not hospital_id:
            return

        table = item.table
        query = (table.tag.lower() == tag.lower()) & \
                (table.hospital_id == hospital_id)

        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

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

    names = ("hms_ctc",)

    def model(self):

        T = current.T

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
        define_table(tablename,
                     self.hms_hospital_id(ondelete = "CASCADE"),
                     Field("ctc", "boolean", default=False,
                           label = T("Cholera-Treatment-Center"),
                           represent = lambda opt: \
                                       opt and T("yes") or T("no"),
                           ),
                     Field("number_of_patients", "integer",
                           default = 0,
                           label = T("Current number of patients"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999)),
                           ),
                     Field("cases_24", "integer",
                           default = 0,
                           label = T("New cases in the past 24h"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999)),
                           ),
                     Field("deaths_24", "integer",
                           default = 0,
                           label = T("Deaths in the past 24h"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999)),
                           ),
                     #Field("staff_total", "integer", default = 0),
                     Field("icaths_available", "integer",
                           default = 0,
                           label = T("Infusion catheters available"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     Field("icaths_needed_24", "integer",
                           default = 0,
                           label = T("Infusion catheters needed per 24h"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     Field("infusions_available", "integer",
                           default = 0,
                           label = T("Infusions available"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     Field("infusions_needed_24", "integer",
                           default = 0,
                           label = T("Infusions needed per 24h"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     #Field("infset_available", "integer", default = 0),
                     #Field("infset_needed_24", "integer", default = 0),
                     Field("antibiotics_available", "integer",
                           default = 0,
                           label = T("Antibiotics available"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     Field("antibiotics_needed_24", "integer",
                           default = 0,
                           label = T("Antibiotics needed per 24h"),
                           represent = lambda v: IS_INT_AMOUNT.represent(v),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 99999999)),
                           ),
                     Field("problem_types", "list:integer",
                           label = T("Current problems, categories"),
                           represent = lambda optlist: \
                                       optlist and ", ".join(map(str,optlist)) or T("N/A"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(hms_problem_types,
                                                  zero=None,
                                                  multiple=True)),
                           ),
                     Field("problem_details", "text",
                           label = T("Current problems, details"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Field configuration
        # @todo: make lazy table
        table = current.db[tablename]
        table.modified_on.label = T("Last updated on")
        table.modified_on.readable = True
        table.modified_by.label = T("Last updated by")
        table.modified_by.readable = True

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Cholera Treatment Capability Information"),
            title_display = T("Cholera Treatment Capability"),
            title_list = T("Cholera Treatment Capability"),
            title_update = T("Update Cholera Treatment Capability Information"),
            label_list_button = T("List Statuses"),
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status added"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No status information available"))

        # Resource configuration
        self.configure(tablename,
                       list_fields = ["id"],
                       subheadings = {
                        "Activities": "ctc",
                        "Medical Supplies Availability": "icaths_available",
                        "Current Problems": "problem_types",
                        "Comments": "comments"
                        },
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return dict()

    # -------------------------------------------------------------------------
    def defaults(self):

        return dict()

# =============================================================================
class HospitalActivityReportModel(S3Model):

    names = ("hms_activity",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Activity
        #
        is_number_of_patients = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 9999))
        represent_int_amount = lambda v, row=None: IS_INT_AMOUNT.represent(v)
        tablename = "hms_activity"
        self.define_table(tablename,
                          self.hms_hospital_id(ondelete = "CASCADE"),
                          s3_datetime(label = T("Date & Time"),
                                      empty = False,
                                      future = 0,
                                      ),
                          # Current Number of Patients
                          Field("patients", "integer",
                                default = 0,
                                label = T("Number of Patients"),
                                represent = represent_int_amount,
                                requires = is_number_of_patients,
                                ),
                          # Admissions in the past 24 hours
                          Field("admissions24", "integer",
                                default = 0,
                                label = T("Admissions/24hrs"),
                                represent = represent_int_amount,
                                requires = is_number_of_patients,
                                ),
                          # Discharges in the past 24 hours
                          Field("discharges24", "integer",
                                default = 0,
                                label = T("Discharges/24hrs"),
                                represent = represent_int_amount,
                                requires = is_number_of_patients,
                                ),
                          # Deaths in the past 24 hours
                          Field("deaths24", "integer",
                                default = 0,
                                label = T("Deaths/24hrs"),
                                represent = represent_int_amount,
                                requires = is_number_of_patients,
                                ),
                          Field("comment", length=128),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Activity Report"),
            title_display = T("Activity Report"),
            title_list = T("Activity Reports"),
            title_update = T("Update Activity Report"),
            label_list_button = T("List Activity Reports"),
            label_delete_button = T("Delete Report"),
            msg_record_created = T("Report added"),
            msg_record_modified = T("Report updated"),
            msg_record_deleted = T("Report deleted"),
            msg_list_empty = T("No reports currently available"))

        # Resource configuration
        self.configure(tablename,
                       extra = "id",
                       list_fields = ["id",
                                      "date",
                                      "patients",
                                      "admissions24",
                                      "discharges24",
                                      "deaths24",
                                      "comment",
                                      ],
                       main = "hospital_id",
                       onaccept = self.hms_activity_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return dict()

    # -------------------------------------------------------------------------
    def defaults(self):

        return dict()

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

                if settings.has_module("hrm"):
                    STAFF = settings.get_hrm_staff_label()
                    tabs.append((STAFF, "human_resource"))
                    permit = current.auth.s3_has_permission
                    if permit("update", tablename, r.id) and \
                       permit("create", "hrm_human_resource_site"):
                        tabs.append((T("Assign %(staff)s") % dict(staff=STAFF), "assign"))

                try:
                    tabs = tabs + s3db.req_tabs(r, match=False)
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
            NONE = current.messages["NONE"]
            total_beds = hospital.total_beds
            if total_beds is None:
                total_beds = NONE
            available_beds = hospital.available_beds
            if available_beds is None:
                available_beds = NONE
            rheader = DIV(TABLE(
                TR(TH("%s: " % T("Name")),
                      hospital.name,
                   TH("%s: " % T("Facility Status")),
                      status("facility_status")
                   ),
                TR(TH("%s: " % T("Location")),
                      ltable[hospital.location_id] and \
                      ltable[hospital.location_id].name or "unknown",
                   TH("%s: " % T("Estimated Reopening Date")),
                      status("date_reopening")
                   #TH("%s: " % T("EMS Status")),
                   #   status("ems_status")
                   ),
                TR(TH("%s: " % T("Total Beds")),
                      total_beds,
                   #TH("%s: " % T("Clinical Status")),
                   #   status("clinical_status")
                   ),
                TR(TH("%s: " % T("Available Beds")),
                      available_beds,
                   #TH("%s: " % T("Security Status")),
                   #   status("security_status")
                   )
                ), rheader_tabs)

    return rheader

# END =========================================================================
