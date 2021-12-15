# -*- coding: utf-8 -*-

""" Sahana Eden Medical Model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("HospitalModel",
           "HospitalActivityReportModel",
           "HospitalBedsModel",
           "HospitalCholeraModel",
           "HospitalServicesModel",
           "HospitalStatusModel",
           "MedicalContactsModel",
           "PharmacyModel",
           "med_hospital_rheader"
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3dal import Row
from s3layouts import S3PopupLink

# =============================================================================
class HospitalModel(S3Model):
    """
        Medical Facilities
    """

    names = ("med_hospital",
             "med_hospital_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        # HAVE compliance?
        have = settings.get_med_have()

        add_components = self.add_components
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Hospitals
        #
        med_facility_type_opts = {
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
        }

        tablename = "med_hospital"
        self.define_table(tablename,
                          super_link("doc_id", "doc_entity"),
                          super_link("pe_id", "pr_pentity"),
                          super_link("site_id", "org_site"),
                          # Name of the facility
                          Field("name", notnull=True,
                                length=64, # Mayon compatibility
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ]
                                ),
                          Field("code", length=10, # Mayon compatibility
                                #notnull=True, unique=True,
                                # @ToDo: code_requires
                                label = T("Code"),
                                requires = IS_LENGTH(120),
                                ),
                          Field("facility_type", "integer",
                                default = 1,
                                label = T("Facility Type"),
                                represent = s3_options_represent(med_facility_type_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_facility_type_opts)
                                            ),
                                ),
                          self.org_organisation_id(requires = self.org_organisation_requires(updateable = True),
                                                   ),
                          Field("town",
                                # Needed for HAVE & not easy to know which Lx to use for this!
                                readable = have,
                                writable = have,
                                ),
                          self.gis_location_id(),
 
                          Field("phone_exchange",
                                label = T("Phone/Exchange (Switchboard)"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          Field("phone_business",
                                label = T("Phone/Business"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          Field("phone_emergency",
                                label = T("Phone/Emergency"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
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
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          Field("total_beds", "integer",
                                label = T("Total Beds"),
                                #readable = False,
                                writable = False,
                                represent = lambda v: NONE if v is None else v,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("available_beds", "integer",
                                label = T("Available Beds"),
                                #readable = False,
                                writable = False,
                                represent = lambda v: NONE if v is None else v,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("doctors", "integer",
                                label = T("Number of doctors"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(
                                             IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("nurses", "integer",
                                label = T("Number of nurses"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(
                                             IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("non_medical_staff", "integer",
                                label = T("Number of non-medical staff"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(
                                             IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("obsolete", "boolean",
                                default = False,
                                label = T("Obsolete"),
                                represent = lambda opt: current.messages.OBSOLETE if opt else NONE,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        ADD_HOSPITAL = T("Create Hospital")
        current.response.s3.crud_strings[tablename] = Storage(
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
            msg_list_empty = T("No Hospitals currently registered"),
            )

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

        if have:
            # HAVE-compliant CRUD form
            crud_form = S3SQLCustomForm((T("Government UID"), "gov_uuid.value"),
                                        "name",
                                        "code",
                                        "facility_type",
                                        "organisation_id",
                                        "town",
                                        "location_id",
                                        "phone_exchange",
                                        "phone_business",
                                        "phone_emergency",
                                        "website",
                                        "email",
                                        "fax",
                                        "total_beds",
                                        "available_beds",
                                        "doctors",
                                        "nurses",
                                        "non_medical_staff",
                                        "obsolete",
                                        "comments",
                                        )
        else:
            crud_form = None

        # Resource configuration
        self.configure(tablename,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("name",),
                                                 ),
                       list_fields = [#"gov_uuid",
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
                       onaccept = self.med_hospital_onaccept,
                       report_options = {"rows": report_fields,
                                         "cols": report_fields,
                                         "fact": report_fields,
                                         "defaults": {"rows": "location_id$L2",
                                                      "cols": "status.facility_status",
                                                      "fact": "count(name)",
                                                      },
                                         },
                       super_entity = ("doc_entity",
                                       "org_site",
                                       "pr_pentity",
                                       ),
                       )

        # Reusable field
        med_hospital_id_comment = S3PopupLink(c = "med",
                                              f = "hospital",
                                              label = ADD_HOSPITAL,
                                              title = T("Hospital"),
                                              tooltip = T("If you don't see the Hospital in the list, you can add a new one by clicking link 'Create Hospital'."),
                                              )

        represent = S3Represent(lookup = tablename)
        hospital_id = S3ReusableField("hospital_id", "reference %s" % tablename,
                                      comment = med_hospital_id_comment,
                                      label = T("Hospital"),
                                      ondelete = "RESTRICT",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "med_hospital.id",
                                                              represent
                                                              )),
                                      sortby = "name",
                                      )

        # Components
        add_components(tablename,
                       med_hospital_status = {"name": "status",
                                              "joinby": "hospital_id",
                                              "multiple": False,
                                              },
                       med_contact = {"link": "med_contact_hospital",
                                      "joinby": "hospital_id",
                                      "key": "contact_id",
                                      "actuate": "replace",
                                      },
                       med_bed_capacity = "hospital_id",
                       med_hospital_services = {"name": "services",
                                                "joinby": "hospital_id",
                                                "multiple": False,
                                                },
                       med_hospital_resources = {"name": "resources",
                                                 "joinby": "hospital_id",
                                                 },
                       )

        # Optional components
        if settings.get_med_track_ctc():
            add_components(tablename,
                           med_ctc = {"joinby": "hospital_id",
                                      "multiple": False,
                                      },
                           )
        if settings.get_med_activity_reports():
            add_components(tablename,
                           med_hospital_activity = {"name": "activity",
                                                    "joinby": "hospital_id",
                                                    "multiple": True,
                                                    },
                           )
        if have:
            add_components(tablename,
                           # Filtered components
                           org_site_tag = {"name": "gov_uuid",
                                           "joinby": "site_id",
                                           "filterby": {"tag": "gov_uuid"},
                                           "multiple": False,
                                           },
                           )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return {"med_hospital_id": hospital_id,
                }

    # -------------------------------------------------------------------------
    def defaults(self):

        return {"med_hospital_id": S3ReusableField.dummy("hospital_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def med_hospital_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("med_hospital", form.vars)

# =============================================================================
class HospitalActivityReportModel(S3Model):

    names = ("med_hospital_activity",)

    def model(self):

        T = current.T

        is_number_of_patients = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None))
        represent_int_amount = lambda v, row=None: IS_INT_AMOUNT.represent(v)

        # ---------------------------------------------------------------------
        # Activity
        #
        tablename = "med_hospital_activity"
        self.define_table(tablename,
                          self.med_hospital_id(ondelete = "CASCADE"),
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
                          Field("comment", length=128,
                                requires = IS_LENGTH(128),
                                ),
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
            msg_list_empty = T("No reports currently available"),
            )

        # Resource configuration
        self.configure(tablename,
                       list_fields = ["date",
                                      "patients",
                                      "admissions24",
                                      "discharges24",
                                      "deaths24",
                                      "comment",
                                      ],
                       main = "hospital_id",
                       onaccept = self.med_activity_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def med_activity_onaccept(form):

        db = current.db
        atable = db.med_hospital_activity
        htable = db.med_hospital
        query = ((atable.id == form.vars.id) & \
                 (htable.id == atable.hospital_id))
        hospital = db(query).select(htable.id,
                                    htable.modified_on,
                                    limitby = (0, 1),
                                    ).first()
        timestmp = form.vars.date
        if hospital and hospital.modified_on < timestmp:
            hospital.update_record(modified_on = timestmp)

# =============================================================================
class HospitalBedsModel(S3Model):
    """
        Hospital Beds
    """

    names = ("med_bed_capacity",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Bed Capacity
        #

        med_bed_type_opts = {
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
            17: T("Respirator"),
            99: T("Other"),
        }

        tablename = "med_bed_capacity"
        self.define_table(tablename,
                          self.med_hospital_id(ondelete = "CASCADE"),
                          Field("unit_id", length=128, unique=True,
                                requires = IS_LENGTH(128),
                                readable = False,
                                writable = False,
                                ),
                          Field("bed_type", "integer",
                                default = 6,
                                label = T("Bed Type"),
                                # Can't migrate to s3_options_represent as we read the options in the controller for the Filter options
                                represent = S3Represent(options = med_bed_type_opts),
                                requires = IS_IN_SET(med_bed_type_opts,
                                                     zero = None),
                                ),
                          s3_datetime(empty = False,
                                      label = T("Date of Report"),
                                      future = 0,
                                      ),
                          Field("beds_baseline", "integer",
                                default = 0,
                                label = T("Baseline Number of Beds"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("beds_available", "integer",
                                default = 0,
                                label = T("Available Beds"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("beds_add24", "integer",
                                default = 0,
                                label = T("Additional Beds / 24hrs"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                               ),
                          s3_comments(),
                          *s3_meta_fields())

        # Field configuration
        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Bed Type"),
            title_display = T("Bed Capacity"),
            title_list = T("Bed Capacity"),
            title_update = T("Update Unit"),
            label_list_button = T("List Units"),
            label_delete_button = T("Delete Unit"),
            msg_record_created = T("Unit added"),
            msg_record_modified = T("Unit updated"),
            msg_record_deleted = T("Unit deleted"),
            msg_list_empty = T("No units currently registered"),
            )

        # Resource configuration
        self.configure(tablename,
                       list_fields = ["unit_name",
                                      "bed_type",
                                      "date",
                                      "beds_baseline",
                                      "beds_available",
                                      "beds_add24"
                                      ],
                       main = "hospital_id",
                       onaccept = self.med_bed_capacity_onaccept,
                       ondelete = self.med_bed_capacity_onaccept,
                       onvalidation = self.med_bed_capacity_onvalidation,
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def med_bed_capacity_onvalidation(form):
        """ Bed Capacity Validation """

        db = current.db
        htable = db.med_hospital
        ctable = db.med_bed_capacity
        hospital_id = ctable.hospital_id.update # ?
        bed_type = form.vars.bed_type
        query = (ctable.hospital_id == hospital_id) & \
                (ctable.bed_type == bed_type)
        row = db(query).select(ctable.id,
                               limitby = (0, 1),
                               ).first()
        if row and str(row.id) != current.request.post_vars.id:
            form.errors["bed_type"] = current.T("Bed type already registered")
        elif "unit_id" not in form.vars:
            hospital = db(htable.id == hospital_id).select(htable.uuid,
                                                           limitby = (0, 1),
                                                           ).first()
            if hospital:
                form.vars.unit_id = "%s-%s" % (hospital.uuid, bed_type)

    # -------------------------------------------------------------------------
    @staticmethod
    def med_bed_capacity_onaccept(form):
        """ Updates the number of total/available beds of a hospital """

        if isinstance(form, Row):
            form_vars = form
        else:
            form_vars = form.vars

        db = current.db
        ctable = db.med_bed_capacity
        htable = db.med_hospital
        query = ((ctable.id == form_vars.id) &
                 (htable.id == ctable.hospital_id))
        hospital = db(query).select(htable.id,
                                    limitby = (0, 1),
                                    ).first()

        if hospital:
            a_beds = ctable.beds_available.sum()
            t_beds = ctable.beds_baseline.sum()
            query = (ctable.hospital_id == hospital.id) & \
                    (ctable.deleted == False)
            count = db(query).select(a_beds, t_beds)
            if count:
                a_beds = count[0]._extra[a_beds]
                t_beds = count[0]._extra[t_beds]

            db(htable.id == hospital.id).update(total_beds = t_beds,
                                                available_beds = a_beds,
                                                )

# =============================================================================
class HospitalCholeraModel(S3Model):

    names = ("med_ctc",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Cholera Treatment Capability
        #
        med_problem_types = {
            1: T("Security problems"),
            2: T("Hygiene problems"),
            3: T("Sanitation problems"),
            4: T("Improper handling of dead bodies"),
            5: T("Improper decontamination"),
            6: T("Understaffed"),
            7: T("Lack of material"),
            8: T("Communication problems"),
            9: T("Information gaps"),
        }

        tablename = "med_ctc"
        self.define_table(tablename,
                          self.med_hospital_id(ondelete = "CASCADE"),
                          Field("ctc", "boolean",
                                default = False,
                                label = T("Cholera-Treatment-Center"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("number_of_patients", "integer",
                                default = 0,
                                label = T("Current number of patients"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("cases_24", "integer",
                                default = 0,
                                label = T("New cases in the past 24h"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("deaths_24", "integer",
                                default = 0,
                                label = T("Deaths in the past 24h"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          #Field("staff_total", "integer", default = 0),
                          Field("icaths_available", "integer",
                                default = 0,
                                label = T("Infusion catheters available"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("icaths_needed_24", "integer",
                                default = 0,
                                label = T("Infusion catheters needed per 24h"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("infusions_available", "integer",
                                default = 0,
                                label = T("Infusions available"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("infusions_needed_24", "integer",
                                default = 0,
                                label = T("Infusions needed per 24h"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          #Field("infset_available", "integer", default = 0),
                          #Field("infset_needed_24", "integer", default = 0),
                          Field("antibiotics_available", "integer",
                                default = 0,
                                label = T("Antibiotics available"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("antibiotics_needed_24", "integer",
                                default = 0,
                                label = T("Antibiotics needed per 24h"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),
                          Field("problem_types", "list:integer",
                                label = T("Current problems, categories"),
                                represent = lambda optlist: \
                                            optlist and ", ".join(str(o) for o in optlist) or T("N/A"),
                                requires = IS_EMPTY_OR(
                                             IS_IN_SET(med_problem_types,
                                                       zero = None,
                                                       multiple = True,
                                                       )),
                                ),
                          Field("problem_details", "text",
                                label = T("Current problems, details"),
                                ),
                          s3_comments(),
                          *s3_meta_fields(),
                          on_define = lambda table: \
                            [table.modified_on.set_attributes(label = T("Last updated on"),
                                                              readable = True
                                                              ),
                             table.modified_by.set_attributes(label = T("Last updated by"),
                                                              readable = True,
                                                              ),
                             ]
                          )

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
            msg_list_empty = T("No status information available"),
            )

        # Resource configuration
        self.configure(tablename,
                       subheadings = {"ctc": T("Activities"),
                                      "icaths_available": T("Medical Supplies Availability"),
                                      "problem_types": T("Current Problems"),
                                      "comments": T("Comments"),
                                      },
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

# =============================================================================
class HospitalServicesModel(S3Model):
    """
        Hospital Services & Resources
    """

    names = ("med_hospital_services",
             "med_hospital_resources",
             )

    def model(self):

        T = current.T

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        hospital_id = self.med_hospital_id

        # ---------------------------------------------------------------------
        # Services
        #
        tablename = "med_hospital_services"
        define_table(tablename,
                     hospital_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
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
            msg_list_empty = T("No service profile available"),
            )

        # ---------------------------------------------------------------------
        # Resources (multiple) - @todo: to be completed!
        #
        tablename = "med_hospital_resources"
        define_table(tablename,
                     hospital_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
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
            msg_list_empty = T("No resources currently reported"),
            )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

# =============================================================================
class HospitalStatusModel(S3Model):
    """
        Hospital Status
    """

    names = ("med_hospital_status",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Hospital status
        #
        med_facility_status_opts = {
            1: T("Normal"),
            2: T("Compromised"),
            3: T("Evacuating"),
            4: T("Closed"),
            5: T("Pending"),
            99: T("No Response"),
        }

        med_resource_status_opts = {
            1: T("Adequate"),
            2: T("Insufficient")
        }

        med_clinical_status_opts = {
            1: T("Normal"),
            2: T("Full"),
            3: T("Closed")
        }

        med_facility_damage_opts = {
            1: T("Flooding"),
            2: T("Power Outage"),
        }

        med_power_supply_type_opts = {
            1: T("Grid"),
            2: T("Generator"),
            98: T("Other"),
            99: T("None"),
        }

        med_gas_supply_type_opts = {
            98: T("Other"),
            99: T("None"),
        }

        med_security_status_opts = {
            1: T("Normal"),
            2: T("Elevated"),
            3: T("Restricted Access"),
            4: T("Lockdown"),
            5: T("Quarantine"),
            6: T("Closed")
        }

        med_ems_traffic_opts = {
            1: T("Normal"),
            2: T("Advisory"),
            3: T("Closed"),
            4: T("Not Applicable")
        }

        med_or_status_opts = {
            1: T("Normal"),
            #2: T("Advisory"),
            3: T("Closed"),
            4: T("Not Applicable")
        }

        med_morgue_status_opts = {
            1: T("Open"),
            2: T("Full"),
            3: T("Exceeded"),
            4: T("Closed")
        }

        def med_facility_damage_multirepresent(value):
            """ Multi Represent """
            if not value:
                return NONE
            if not isinstance(value, (list, tuple)):
                value = [value]
            labels = (med_facility_damage_opts.get(v) for v in value if v)
            return ", ".join(s3_str(l) for l in labels if l is not None)

        tablename = "med_hospital_status"
        self.define_table(tablename,
                          self.med_hospital_id(ondelete = "CASCADE"),

                          # Status of the facility and facility operations
                          Field("facility_status", "integer",
                                label = T("Facility Status"),
                                # Can't migrate to s3_options_represent as we read the options in the controller for the Filter options
                                represent = S3Represent(options = med_facility_status_opts),
                                requires = IS_EMPTY_OR(
                                             IS_IN_SET(med_facility_status_opts)),
                                ),
                          s3_date("date_reopening",
                                  label = T("Estimated Reopening Date"),
                                  ),
                          Field("facility_operations", "integer",
                                label = T("Facility Operations"),
                                represent = s3_options_represent(med_resource_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_resource_status_opts)),
                                ),

                          # Facility Status Details
                          Field("damage", "list:integer",
                                label = T("Damage sustained"),
                                represent = med_facility_damage_multirepresent,
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_facility_damage_opts,
                                                      multiple = True)),
                                widget = CheckboxesWidgetS3.widget,
                                ),
                          Field("power_supply_type", "integer",
                                label = T("Power Supply Type"),
                                # Can't migrate to s3_options_represent as we read the options in the controller for the Filter options
                                represent = S3Represent(options = med_power_supply_type_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_power_supply_type_opts,
                                                      zero = None)),
                                ),
                          Field("gas_supply_type", "integer",
                                label = T("Gas Supply Type"),
                                represent = s3_options_represent(med_gas_supply_type_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_gas_supply_type_opts,
                                                      zero = None)),
                                ),
                          Field("gas_supply_capacity", "integer",
                                label = T("Gas Supply Left (in hours)"),
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),

                          # Clinical status and clinical operations
                          Field("clinical_status", "integer",
                                label = T("Clinical Status"),
                                represent = s3_options_represent(med_clinical_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_clinical_status_opts)),
                                ),
                          Field("clinical_operations", "integer",
                                label = T("Clinical Operations"),
                                represent = s3_options_represent(med_resource_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_resource_status_opts)),
                                ),
                          Field("security_status", "integer",
                                label = T("Security Status"),
                                represent = s3_options_represent(med_security_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_security_status_opts)),
                                ),

                          # Staffing status
                          Field("staffing", "integer",
                                label = T("Staffing Level"),
                                represent = s3_options_represent(med_resource_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_resource_status_opts)),
                                ),

                          # Emergency Room Status
                          Field("ems_status", "integer",
                                label = T("ER Status"),
                                represent = s3_options_represent(med_ems_traffic_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_ems_traffic_opts)),
                                ),
                          Field("ems_reason", length=128,
                                label = T("ER Status Reason"),
                                requires = IS_LENGTH(128),
                                ),

                          # Operating Room Status
                          Field("or_status", "integer",
                                label = T("OR Status"),
                                represent = s3_options_represent(med_or_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_or_status_opts)),
                                ),
                          Field("or_reason", length=128,
                                label = T("OR Status Reason"),
                                requires = IS_LENGTH(128),
                                ),

                          # Morgue status and capacity
                          Field("morgue_status", "integer",
                                label = T("Morgue Status"),
                                represent = s3_options_represent(med_morgue_status_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(med_morgue_status_opts)),
                                ),
                          Field("morgue_units", "integer",
                                label = T("Morgue Units Available"),
                                represent = IS_INT_AMOUNT.represent,
                                requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                                ),

                          Field("access_status", "text",
                                label = T("Road Conditions"),
                                ),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Status Report"),
            title_display = T("Status Report"),
            title_list = T("Status Report"),
            title_update = T("Edit Status Report"),
            label_list_button = T("List Status Reports"),
            msg_record_created = T("Status Report added"),
            msg_record_modified = T("Status Report updated"),
            msg_record_deleted = T("Status Report deleted"),
            msg_list_empty = T("No status information currently available"),
            )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

# =============================================================================
class MedicalContactsModel(S3Model):
    """
        Medical Contacts
    """

    names = ("med_contact",
             "med_contact_id",
             "med_contact_hospital",
             "med_contact_skill",
             )

    def model(self):

        T = current.T

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Contacts
        #
        tablename = "med_contact"
        define_table(tablename,
                     Field("name", notnull=True,
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("operational", "boolean",
                           default = True,
                           label = T("Operational"),
                           represent = s3_yes_no_represent,
                           comment = T("e.g. Has Cash available"),
                           ),
                     self.gis_location_id(),
                     Field("phone",
                           label = T("Phone"),
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           ),
                     Field("email",
                           label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     # Optional link to a Person Record
                     # - automatic sync with Person Name/Contacts isn't done by default as the context & permissions can be different
                     self.pr_person_id(label = T("Person"),
                                       ondelete = "SET NULL",
                                       comment = None,
                                       ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Contact"),
            title_display = T("Contact Details"),
            title_list = T("Contacts"),
            title_update = T("Edit Contact"),
            label_list_button = T("List Contacts"),
            msg_record_created = T("Contact information added"),
            msg_record_modified = T("Contact information updated"),
            msg_record_deleted = T("Contact information deleted"),
            msg_list_empty = T("No contacts currently registered"),
            )

        crud_fields = ["name",
                       "operational",
                       S3SQLInlineLink("skill",
                                       label = T("Qualifications"),
                                       field = "skill_id",
                                       ),
                       "location_id",
                       "phone",
                       "email",
                       "person_id",
                       "comments",
                       ]
        if current.request.function != "hospital":
            crud_fields.insert(-2, S3SQLInlineLink("hospital",
                                                   label = T("Hospital"),
                                                   field = "hospital_id",
                                                   ))

        crud_form = S3SQLCustomForm(*crud_fields)

        # Resource configuration
        self.configure(tablename,
                       crud_form = crud_form,
                       )

        self.add_components(tablename,
                            hrm_skill = {"link": "med_contact_skill",
                                         "joinby": "contact_id",
                                         "key": "skill_id",
                                         "actuate": "hide",
                                         },
                            med_hospital = {"link": "med_contact_hospital",
                                            "joinby": "contact_id",
                                            "key": "hospital_id",
                                            "actuate": "hide",
                                            },
                            )

        # Reusable field
        contact_id = S3ReusableField("contact_id", "reference %s" % tablename,
                                     ondelete = "CASCADE",
                                     )

        # ---------------------------------------------------------------------
        # Med Contact <> Hospital link table
        #
        tablename = "med_contact_hospital"
        define_table(tablename,
                     contact_id(),
                     self.med_hospital_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Med Contact <> Skill table
        #
        tablename = "med_contact_skill"
        define_table(tablename,
                     contact_id(),
                     self.hrm_skill_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return {"med_contact_id": contact_id,
                }

# =============================================================================
class PharmacyModel(S3Model):

    names = ("med_pharmacy",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Pharmacies
        # - usually commercial
        # - usually have dispensing facilities
        # - don't have beds
        #
        tablename = "med_pharmacy"
        self.define_table(tablename,
                          #super_link("doc_id", "doc_entity"),
                          #super_link("pe_id", "pr_pentity"),
                          self.super_link("site_id", "org_site"),
                          Field("name", notnull=True,
                                length=64, # Mayon compatibility
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ]
                                ),
                          #Field("code", length=10, # Mayon compatibility
                          #      #notnull=True, unique=True,
                          #      # @ToDo: code_requires
                          #      label = T("Code"),
                          #      requires = IS_LENGTH(120),
                          #      ),
                          #self.org_organisation_id(requires = self.org_organisation_requires(updateable = True),
                          #                         ),
                          self.gis_location_id(),
                          Field("dispensing", "boolean",
                                default = True,
                                label = T("Dispensing"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("opening_times",
                                label = T("Opening Times"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("phone",
                                label = T("Phone"),
                                requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                                ),
                          Field("email",
                                label = T("Email"),
                                requires = IS_EMPTY_OR(IS_EMAIL()),
                                ),
                          Field("website",
                                label = T("Website"),
                                represent = s3_url_represent,
                                requires = IS_EMPTY_OR(IS_URL()),
                                ),
                          Field("obsolete", "boolean",
                                default = False,
                                label = T("Obsolete"),
                                represent = lambda opt: current.messages.OBSOLETE if opt else NONE,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Pharmacy"),
            title_display = T("Pharmacy Details"),
            title_list = T("Pharmacies"),
            title_update = T("Edit Pharmacy"),
            title_map = T("Map of Pharmacies"),
            label_list_button = T("List Pharmacies"),
            label_delete_button = T("Delete Pharmacy"),
            msg_record_created = T("Pharmacy added"),
            msg_record_modified = T("Pharmacy updated"),
            msg_record_deleted = T("Pharmacy deleted"),
            msg_list_empty = T("No Pharmacies currently registered"),
            )

        # Resource configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("name",),
                                                 ),
                       super_entity = (#"doc_entity",
                                       "org_site",
                                       #"pr_pentity",
                                       ),
                       )

        # ---------------------------------------------------------------------
        # Return global names to s3db
        #
        return None

# =============================================================================
def med_hospital_rheader(r, tabs=None):
    """ Page header for component resources """

    rheader = None
    if r.representation == "html":
        T = current.T
        s3db = current.s3db
        settings = current.deployment_settings
        tablename, record = s3_rheader_resource(r)
        if tablename == "med_hospital" and record:

            if not tabs:
                tabs = [(T("Details"), ""),
                        (T("Status"), "status"),
                        (T("Contacts"), "contact"),
                        (T("Images"), "image"),
                        (T("Services"), "services"),
                        (T("Bed Capacity"), "bed_capacity"),
                        ]

                if settings.get_med_activity_reports():
                    tabs.append((T("Activity Report"), "activity"))

                if settings.get_med_track_ctc():
                    tabs.append((T("Cholera Treatment Capability"), "ctc"))

                if settings.has_module("hrm"):
                    STAFF = settings.get_hrm_staff_label()
                    tabs.append((STAFF, "human_resource"))
                    permit = current.auth.s3_has_permission
                    if permit("update", tablename, r.id) and \
                       permit("create", "hrm_human_resource_site"):
                        tabs.append((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))

                if settings.has_module("inv"):
                    from .inv import inv_tabs, inv_req_tabs
                    tabs.extend(inv_req_tabs(r, match=False))
                    tabs.extend(inv_tabs(r))

                tabs.append((T("User Roles"), "roles"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            hospital = record

            db = current.db

            ltable = s3db.gis_location
            location = db(ltable.id == hospital.location_id).select(ltable.name,
                                                                    limitby = (0, 1),
                                                                    ).first()
            if location:
                location = location.name
            else:
                location = "unknown"

            stable = s3db.med_hospital_status
            s = db(stable.hospital_id == hospital.id).select(stable.facility_status,
                                                             stable.date_reopening,
                                                             #stable.ems_status,
                                                             #stable.clinical_status,
                                                             #stable.security_status,
                                                             limitby = (0, 1),
                                                             ).first()

            status = lambda k: (s is not None and
                                [stable[k].represent(s[k])] or
                                [T("n/a")])[0]
            total_beds = hospital.total_beds
            if total_beds is None:
                total_beds = NONE
            available_beds = hospital.available_beds
            if available_beds is None:
                available_beds = NONE
            rheader = DIV(TABLE(TR(TH("%s: " % T("Name"),
                                      ),
                                   hospital.name,
                                   TH("%s: " % T("Facility Status")
                                      ),
                                   status("facility_status"),
                                   ),
                                TR(TH("%s: " % T("Location")),
                                      location,
                                   TH("%s: " % T("Estimated Reopening Date"),
                                      ),
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
                                   ),
                                ),
                          rheader_tabs,
                          )

    return rheader

# END =========================================================================
