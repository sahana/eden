# -*- coding: utf-8 -*-
"""
    Sahana Eden Volunteers Management
    (Extends modules/eden/hrm.py)

    @copyright: 2012-15 (c) Sahana Software Foundation
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

__all__ = ("S3VolunteerModel",
           "S3VolunteerAwardModel",
           "S3VolunteerClusterModel",
           "vol_service_record",
           "vol_person_controller",
           "vol_volunteer_controller",
           )

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3VolunteerModel(S3Model):

    names = ("vol_details",)

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        availability_opts = {1: T("No Restrictions"),
                             2: T("Weekends only"),
                             3: T("School Holidays only"),
                             }

        # ---------------------------------------------------------------------
        # Volunteer Details
        # - extra details for volunteers
        #
        tablename = "vol_details"
        self.define_table(tablename,
                          self.hrm_human_resource_id(ondelete = "CASCADE"),
                          Field("volunteer_type",
                                readable = False,
                                writable = False,
                                ),
                          Field("active", "boolean",
                                default = False,
                                label = T("Active"),
                                represent = self.vol_active_represent,
                                ),
                          Field("availability", "integer",
                                label = T("Availability"),
                                represent = lambda opt: \
                                            availability_opts.get(opt,
                                                          UNKNOWN_OPT),
                                requires = IS_EMPTY_OR(
                                             IS_IN_SET(availability_opts)
                                           ),
                                ),
                          Field("card", "boolean",
                                default = False,
                                label = T("Card holder"),
                                represent = self.vol_active_represent,
                                # Enable in-template when-required
                                readable = False,
                                writable = False,
                                ),
                          *s3_meta_fields())

    # =========================================================================
    @staticmethod
    def vol_active_represent(opt):
        """ Represent the Active status of a Volunteer """

        if "report" in current.request.args:
            # We can't use a represent
            return opt

        # List view, so HTML represent is fine
        if opt:
            output = DIV(current.T("Yes"), _style="color:green")
        else:
            output = DIV(current.T("No"), _style="color:red")
        return output

# =============================================================================
class S3VolunteerAwardModel(S3Model):

    names = ("vol_award",
             "vol_volunteer_award",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Volunteer Award
        #
        tablename = "vol_award"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     self.org_organisation_id(default = root_org,
                                              readable = is_admin,
                                              writable = is_admin,
                                              ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Award"),
            title_display = T("Award"),
            title_list = T("Awards"),
            title_update = T("Edit Award"),
            title_upload = T("Import Awards"),
            label_list_button = T("List Awards"),
            label_delete_button = T("Delete Award"),
            msg_record_created = T("Award added"),
            msg_record_modified = T("Award updated"),
            msg_record_deleted = T("Award deleted"),
            msg_list_empty = T("No Awards found"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "award",
                                    label = crud_strings[tablename].label_create,
                                    title = T("Award"),
                                    )

        represent = S3Represent(lookup=tablename)
        award_id = S3ReusableField("award_id", "reference %s" % tablename,
                                   label = T("Award"),
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db,
                                                          "vol_award.id",
                                                          represent,
                                                          filterby="organisation_id",
                                                          filter_opts=filter_opts)),
                                   represent = represent,
                                   comment = comment
                                   )

        # ---------------------------------------------------------------------
        # Volunteers <> Awards link table
        #
        tablename = "vol_volunteer_award"
        define_table(tablename,
                     self.pr_person_id(empty=False),
                     award_id(),
                     s3_date(),
                     Field("number",
                           label = T("Number"),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("file", "upload",
                           autodelete = True,
                           label = T("Attachment"),
                           represent = self.vol_award_file_represent,
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Add Award"),
            title_display = T("Award"),
            title_list = T("Awards"),
            title_update = T("Edit Award"),
            title_upload = T("Import Awards"),
            label_list_button = T("List Awards"),
            label_delete_button = T("Delete Award"),
            msg_record_created = T("Award added"),
            msg_record_modified = T("Award updated"),
            msg_record_deleted = T("Award deleted"),
            msg_list_empty = T("No Awards found"))

        self.configure(tablename,
                       context = {"person": "person_id"},
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def vol_award_file_represent(file):
        """ File representation """

        if file:
            try:
                # Read the filename from the file
                filename = current.db.vol_volunteer_award.file.retrieve(file)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(filename,
                         _href=URL(c="default", f="download", args=[file]))
        else:
            return current.messages["NONE"]

# =============================================================================
class S3VolunteerClusterModel(S3Model):

    names = ("vol_cluster_type",
             "vol_cluster",
             "vol_cluster_position",
             "vol_volunteer_cluster",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster_type"
        define_table(tablename,
                     Field("name", length=255, unique=True,
                           label = T("Name")),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster Type"),
            title_display = T("Volunteer Cluster Type"),
            title_list = T("Volunteer Cluster Type"),
            title_update = T("Edit Volunteer Cluster Type"),
            title_upload = T("Import Volunteer Cluster Types"),
            label_list_button = T("List Volunteer Cluster Types"),
            label_delete_button = T("Delete Volunteer Cluster Type"),
            msg_record_created = T("Volunteer Cluster Type added"),
            msg_record_modified = T("Volunteer Cluster Type updated"),
            msg_record_deleted = T("Volunteer Cluster Type deleted"),
            msg_list_empty = T("No Volunteer Cluster Types"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster_type",
                                    vars = dict(child = "vol_cluster_type_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create,
                                    title = T("Volunteer Cluster Type"),
                                    )

        represent = S3Represent(lookup=tablename)
        vol_cluster_type_id = S3ReusableField("vol_cluster_type_id", "reference %s" % tablename,
                                              label = T("Volunteer Cluster Type"),
                                              requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_type.id",
                                                                      represent)),
                                              represent = represent,
                                              comment = comment
                                              )

        # ---------------------------------------------------------------------
        # Volunteer Cluster
        tablename = "vol_cluster"
        define_table(tablename,
                     vol_cluster_type_id(),
                     Field("name", length=255, unique=True,
                           label = T("Name")),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster"),
            title_display = T("Volunteer Cluster"),
            title_list = T("Volunteer Cluster"),
            title_update = T("Edit Volunteer Cluster"),
            title_upload = T("Import Volunteer Clusters"),
            label_list_button = T("List Volunteer Clusters"),
            label_delete_button = T("Delete Volunteer Cluster"),
            msg_record_created = T("Volunteer Cluster added"),
            msg_record_modified = T("Volunteer Cluster updated"),
            msg_record_deleted = T("Volunteer Cluster deleted"),
            msg_list_empty = T("No Volunteer Clusters"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster",
                                    vars = dict(child = "vol_cluster_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create,
                                    title = T("Volunteer Cluster"),
                                    )

        represent = S3Represent(lookup=tablename)
        vol_cluster_id = S3ReusableField("vol_cluster_id", "reference %s" % tablename,
                                         label = T("Volunteer Cluster"),
                                         requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db,
                                                                  "vol_cluster.id",
                                                                  represent)),
                                         represent = represent,
                                         comment = comment
                                         )

        # ---------------------------------------------------------------------
        # Volunteer Group Position
        #
        tablename = "vol_cluster_position"
        define_table(tablename,
                     Field("name", length=255, unique=True,
                           label = T("Name")),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Volunteer Cluster Position"),
            title_display = T("Volunteer Cluster Position"),
            title_list = T("Volunteer Cluster Position"),
            title_update = T("Edit Volunteer Cluster Position"),
            title_upload = T("Import Volunteer Cluster Positions"),
            label_list_button = T("List Volunteer Cluster Positions"),
            label_delete_button = T("Delete Volunteer Cluster Position"),
            msg_record_created = T("Volunteer Cluster Position added"),
            msg_record_modified = T("Volunteer Cluster Position updated"),
            msg_record_deleted = T("Volunteer Cluster Position deleted"),
            msg_list_empty = T("No Volunteer Cluster Positions"))

        comment = S3AddResourceLink(c = "vol",
                                    f = "cluster_position",
                                    vars = dict(child = "vol_cluster_position_id",
                                                parent = "volunteer_cluster"),
                                    label = crud_strings[tablename].label_create,
                                    title = T("Volunteer Cluster Position"),
                                    )

        represent = S3Represent(lookup=tablename)
        vol_cluster_position_id = S3ReusableField("vol_cluster_position_id", "reference %s" % tablename,
                                                label = T("Volunteer Cluster Position"),
                                                requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db,
                                                                      "vol_cluster_position.id",
                                                                      represent)),
                                                represent = represent,
                                                comment = comment
                                                )

        # ---------------------------------------------------------------------
        # Volunteer Cluster Link Table
        cluster_type_filter = '''
$.filterOptionsS3({
 'trigger':'vol_cluster_type_id',
 'target':'vol_cluster_id',
 'lookupKey':'vol_cluster_type_id',
 'lookupPrefix':'vol',
 'lookupResource':'cluster',
})'''

        tablename = "vol_volunteer_cluster"
        define_table(tablename,
                     self.hrm_human_resource_id(ondelete = "CASCADE"),
                     vol_cluster_type_id(script = cluster_type_filter), # This field is ONLY here to provide a filter
                     vol_cluster_id(readable=False,
                                    writable=False),
                     vol_cluster_position_id(readable=False,
                                             writable=False),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return dict(vol_cluster_type_id = vol_cluster_type_id,
                    vol_cluster_id = vol_cluster_id,
                    )

    # =====================================================================
    @staticmethod
    def defaults():
        """
            Return safe defaults for model globals, this will be called instead
            of model() in case the model has been deactivated in
            deployment_settings.
        """

        return dict(
            vol_cluster_id = S3ReusableField("vol_cluster_id", "integer",
                                             readable=False,
                                             writable=False),
            )

# =============================================================================
def vol_service_record(r, **attr):
    """
        Generate a Volunteer Service Record
    """

    record = r.record
    if record.type != 2:
        # Only relevant to volunteers
        return None

    T = current.T
    db = current.db
    settings = current.deployment_settings

    ptable = db.pr_person
    person_id = record.person_id
    person = db(ptable.id == person_id).select(ptable.pe_id,
                                               ptable.first_name,
                                               ptable.middle_name,
                                               ptable.last_name,
                                               ptable.comments,
                                               limitby=(0, 1),
                                               ).first()
    vol_name = s3_fullname(person)

    def callback(r):

        # Header
        s3db = current.s3db
        otable = db.org_organisation
        org_id = record.organisation_id
        org = db(otable.id == org_id).select(otable.name,
                                             otable.acronym, # Present for consistent cache key
                                             otable.logo,
                                             limitby=(0, 1),
                                             ).first()
        if settings.get_L10n_translate_org_organisation():
            org_name = s3db.org_OrganisationRepresent(parent=False,
                                                      acronym=False)(org_id)
        else:
            org_name = org.name

        logo = org.logo
        if logo:
            logo = s3db.org_organisation_logo(org)
        elif current.deployment_settings.get_org_branches():
            root_org = current.cache.ram(
                # Common key with auth.root_org
                "root_org_%s" % org_id,
                lambda: s3db.org_root_organisation(org_id),
                time_expire=120
                )
            logo = s3db.org_organisation_logo(root_org)

        innerTable = TABLE(TR(TH(vol_name)),
                           TR(TD(org_name)))
        person_details = TABLE(TR(TD(logo),
                                  TD(innerTable)
                                  ))

        pe_id = person.pe_id

        # Photo
        itable = s3db.pr_image
        query = (itable.pe_id == pe_id) & \
                (itable.profile == True)
        image = db(query).select(itable.image,
                                 limitby=(0, 1)).first()
        if image:
            image = image.image
            size = (160, None)
            image = s3db.pr_image_represent(image, size=size)
            size = s3db.pr_image_size(image, size)
            url = URL(c="default",
                      f="download",
                      args=image)
            avatar = IMG(_src=url,
                         _width=size[0],
                         _height=size[1],
                         )
            person_details[0].append(TD(avatar))

        # Contact Details
        contact_details = DIV()
        # Addresses
        addrtable = s3db.pr_address
        ltable = db.gis_location
        query = (addrtable.pe_id == pe_id) & \
                (addrtable.location_id == ltable.id)
        addresses = db(query).select(addrtable.type,
                                     ltable.addr_street,
                                     ltable.L3,
                                     ltable.L2,
                                     ltable.L1,
                                     orderby = addrtable.type,
                                     limitby=(0, 2))
        address_list = []
        for address in addresses:
            _location = address["gis_location"]
            address = TABLE(TR(TH(addrtable.type.represent(address["pr_address"].type))),
                            TR(_location.addr_street),
                            TR(_location.L3),
                            TR(_location.L2),
                            TR(_location.L1),
                            )
            address_list.append(address)

        # Contacts
        ctable = s3db.pr_contact
        contacts = db(ctable.pe_id == pe_id).select(ctable.contact_method,
                                                    ctable.value,
                                                    orderby = ctable.priority,
                                                    limitby=(0, 3))
        contact_list = TABLE()
        contact_represent = ctable.contact_method.represent
        for contact in contacts:
            contact_list.append(TH(contact_represent(contact.contact_method)))
            contact_list.append(contact.value)

        # Emergency Contact
        #ectable = s3db.pr_contact_emergency
        #emergency = db(ectable.pe_id == pe_id).select(ectable.name,
        #                                              ectable.relationship,
        #                                              ectable.phone,
        #                                              limitby=(0, 1)).first()
        #if emergency:
        #    econtact = TABLE(TR(TH(T("Emergency Contact"))),
        #                     TR(emergency.name),
        #                     TR(emergency.relationship),
        #                     TR(emergency.phone),
        #                     )
        #else:
        #    econtact = TABLE()
        contact_row = TR()
        if len(address_list) > 0:
            contact_row.append(TD(address_list[0]))
        if len(address_list) > 1:
            contact_row.append(TD(address_list[1]))
        contact_row.append(contact_list)
        #contact_row.append(econtact)

        # Identity
        idtable = s3db.pr_identity
        query = (idtable.person_id == person_id) & \
                (idtable.deleted == False)
        rows = db(query).select(idtable.type,
                                idtable.value,
                                idtable.valid_until)
        id_row = TR()
        for identity in rows:
            id_row.append(TABLE(TR(TH(idtable.type.represent(identity.type))),
                                TR(identity.value),
                                TR(identity.valid_until),
                                ))

        # Comments:
        comments = person.comments or ""
        if comments:
            comments = TABLE(TR(TH(T("Comments"))),
                             TR(comments))

        # Training Courses
        hours = {}
        ttable = s3db.hrm_training
        ctable = s3db.hrm_course
        query = (ttable.deleted == False) & \
                (ttable.person_id == person_id) & \
                (ttable.course_id == ctable.id)
        rows = db(query).select(ctable.name,
                                ttable.date,
                                ttable.hours,
                                orderby = ~ttable.date)
        date_represent = ttable.date.represent
        for row in rows:
            _row = row["hrm_training"]
            _date = _row.date
            hours[_date.date()] = dict(course = row["hrm_course"].name,
                                       date = date_represent(_date),
                                       hours = _row.hours or "",
                                       )
        courses = TABLE(TR(TH(T("Date")),
                           TH(T("Training")),
                           TH(T("Hours"))))
        _hours = {}
        for key in sorted(hours.iterkeys()):
            _hours[key] = hours[key]
        total = 0
        for hour in hours:
            _hour = hours[hour]
            __hours = _hour["hours"] or 0
            courses.append(TR(_hour["date"],
                              _hour["course"],
                              str(__hours)
                              ))
            total += __hours
        if total > 0:
            courses.append(TR(TD(""), TD("Total"), TD("%d" % total)))

        # Programme Hours
        # - grouped by Programme/Role
        programmes = OrderedDict()
        hrstable = s3db.hrm_programme_hours
        ptable = db.hrm_programme
        jtable = db.hrm_job_title
        query = (hrstable.deleted == False) & \
                (hrstable.training == False) & \
                (hrstable.person_id == person_id) & \
                (hrstable.programme_id == ptable.id)
        left = jtable.on(hrstable.job_title_id == jtable.id)
        rows = db(query).select(hrstable.date,
                                hrstable.hours,
                                jtable.name,
                                ptable.name,
                                ptable.name_long,
                                left=left,
                                orderby = ~hrstable.date)
        NONE = current.messages["NONE"]
        for row in rows:
            _row = row["hrm_programme_hours"]
            _date = _row.date
            hours = _row.hours or 0
            role = row["hrm_job_title"]["name"] or NONE
            prow = row["hrm_programme"]
            if prow.name_long:
                programme = prow.name_long
            else:
                programme = prow.name
            if programme not in programmes:
                programmes[programme] = OrderedDict()
            p = programmes[programme]
            if role in p:
                p[role]["end_date"] = _date
                p[role]["hours"] += hours
            else:
                p[role] = dict(start_date = _date,
                               end_date = _date,
                               hours = hours,
                               )
        date_represent = hrstable.date.represent
        programme = TABLE(TR(TH(T("Start Date")),
                             TH(T("End Date")),
                             TH(T("Work on Program")),
                             TH(T("Role")),
                             TH(T("Hours"))))
        total = 0
        for p in programmes:
            _p = programmes[p]
            for r in _p:
                role = _p[r]
                hours = role["hours"]
                total += hours
                programme.append(TR(date_represent(role["start_date"]),
                                    date_represent(role["end_date"]),
                                    p,
                                    r,
                                    str(hours)
                                    ))

        if total > 0:
            programme.append(TR("", "", "", TD("Total"), TD("%d" % total)))

        # Space for the printed document to be signed
        datestamp = S3DateTime.date_represent(current.request.now)
        datestamp = "%s: %s" % (T("Date Printed"), datestamp)
        manager = settings.get_hrm_vol_service_record_manager()
        signature = TABLE(TR(TH(T("Signature"))),
                          TR(TD()),
                          TR(TD(manager)),
                          TR(TD(datestamp)))

        output = DIV(TABLE(TR(TH(T("Volunteer Service Record")))),
                     person_details,
                     TABLE(contact_row),
                     TABLE(id_row),
                     TABLE(comments),
                     TABLE(courses),
                     TABLE(programme),
                     TABLE(signature),
                     )

        return output

    from s3.s3export import S3Exporter
    exporter = S3Exporter().pdf
    pdf_title = vol_name + " - " + s3_unicode(T("Volunteer Service Record")) # %-string substitution doesn't work
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = pdf_title,
                    pdf_table_autogrow = "B",
                    pdf_callback = callback,
                    **attr
                    )

# =============================================================================
def vol_volunteer_controller():
    """ Volunteers Controller """

    s3 = current.response.s3
    s3db = current.s3db
    settings = current.deployment_settings
    T = current.T

    # Volunteers only
    s3.filter = FS("type") == 2

    vol_experience = settings.get_hrm_vol_experience()

    def prep(r):
        resource = r.resource
        get_config = resource.get_config

        # CRUD String
        s3.crud_strings[resource.tablename] = s3.crud_strings["hrm_volunteer"]

        # Default to volunteers
        table = r.table
        table.type.default = 2

        # Volunteers use home address
        location_id = table.location_id
        location_id.label = T("Home Address")

        # Configure list_fields
        if r.representation == "xls":
            # Split person_id into first/middle/last to
            # make it match Import sheets
            list_fields = ["person_id$first_name",
                           "person_id$middle_name",
                           "person_id$last_name",
                           ]
        else:
            list_fields = ["person_id",
                           ]
        if settings.get_hrm_use_code() is True:
            list_fields.append("code")
        list_fields.append("job_title_id")
        if settings.get_hrm_multiple_orgs():
            list_fields.append("organisation_id")
        list_fields.extend(((settings.get_ui_label_mobile_phone(), "phone.value"),
                            (T("Email"), "email.value"),
                            "location_id",
                            ))
        if settings.get_hrm_use_trainings():
            list_fields.append((T("Trainings"),"person_id$training.course_id"))
        if settings.get_hrm_use_certificates():
            list_fields.append((T("Certificates"),"person_id$certification.certificate_id"))

        # Volunteer Programme and Active-status
        report_options = get_config("report_options")
        if vol_experience in ("programme", "both"):
            # Don't use status field
            table.status.readable = table.status.writable = False
            # Use active field?
            vol_active = settings.get_hrm_vol_active()
            if vol_active:
                list_fields.insert(3, (T("Active?"), "details.active"))
            # Add Programme to List Fields
            list_fields.insert(6, "person_id$hours.programme_id")

            # Add active and programme to Report Options
            report_fields = report_options.rows
            report_fields.append("person_id$hours.programme_id")
            if vol_active:
                report_fields.append((T("Active?"), "details.active"))
            report_options.rows = report_fields
            report_options.cols = report_fields
            report_options.fact = report_fields
        else:
            # Use status field
            list_fields.append("status")

        # Update filter widgets
        filter_widgets = \
            s3db.hrm_human_resource_filters(resource_type="volunteer",
                                            hrm_type_opts=s3db.hrm_type_opts)

        # Reconfigure
        resource.configure(list_fields = list_fields,
                           filter_widgets = filter_widgets,
                           report_options = report_options,
                           )

        if r.interactive:
            if r.id:
                if r.method not in ("profile", "delete"):
                    # Redirect to person controller
                    vars = {"human_resource.id": r.id,
                            "group": "volunteer"
                            }
                    if r.representation == "iframe":
                        vars["format"] = "iframe"
                        args = [r.method]
                    else:
                        args = []
                    redirect(URL(f="person", vars=vars, args=args))
            else:
                if r.method == "import":
                    # Redirect to person controller
                    redirect(URL(f="person",
                                 args="import",
                                 vars={"group": "volunteer"}))

                elif not r.component and r.method != "delete":
                    # Configure AddPersonWidget
                    table.person_id.widget = S3AddPersonWidget2(controller="vol")
                    # Show location ID
                    location_id.writable = location_id.readable = True
                    # Hide unwanted fields
                    for fn in ("site_id",
                               "department_id",
                               "essential",
                               "site_contact",
                               "status",
                               ):
                        table[fn].writable = table[fn].readable = False
                    # Hide volunteer ID as per setting
                    if settings.get_hrm_use_code() is not True:
                        table.code.readable = table.code.writable = False
                    # Organisation Dependent Fields
                    # @ToDo: Move these to the IFRC Template
                    set_org_dependent_field = settings.set_org_dependent_field
                    set_org_dependent_field("pr_person_details", "father_name")
                    set_org_dependent_field("pr_person_details", "mother_name")
                    set_org_dependent_field("pr_person_details", "affiliations")
                    set_org_dependent_field("pr_person_details", "company")
                    set_org_dependent_field("vol_details", "availability")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")
                    # Label for "occupation"
                    s3db.pr_person_details.occupation.label = T("Normal Job")
                    # Assume staff only between 12-81
                    dob = s3db.pr_person.date_of_birth
                    dob.widget = S3CalendarWidget(past_months = 972,
                                                  future_months = -144,
                                                  )
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and not r.component:
            # Configure action buttons
            S3CRUD.action_buttons(r, deletable=settings.get_hrm_deletable())
            if settings.has_module("msg") and \
               settings.get_hrm_compose_button() and \
               current.auth.permission.has_permission("update", c="hrm", f="compose"):
                # @ToDo: Remove this now that we have it in Events?
                s3.actions.append({
                        "url": URL(f="compose",
                                    vars = {"human_resource.id": "[id]"}),
                        "_class": "action-btn send",
                        "label": str(T("Send Message"))
                    })

        elif r.representation == "plain":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp

    return current.rest_controller("hrm", "human_resource")

# -----------------------------------------------------------------------------
def vol_person_controller():
    """
        Person Controller
        - used to see PR component tabs, for Personal Profile & Imports
        - includes components relevant to HRM
    """

    db = current.db
    get_vars = current.request.get_vars
    resourcename = "person"
    response = current.response
    s3 = response.s3
    s3db = current.s3db
    session = current.session
    settings = current.deployment_settings
    T = current.T

    configure = s3db.configure
    set_method = s3db.set_method

    # Custom Method for Contacts
    set_method("pr", resourcename,
               method = "contacts",
               action = s3db.pr_Contacts)

    # Custom Method for CV
    set_method("pr", resourcename,
               method = "cv",
               action = s3db.hrm_CV)

    # Custom Method for HR Record
    set_method("pr", resourcename,
               method = "record",
               action = s3db.hrm_Record)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_components("pr_person", asset_asset="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        configure("asset_asset",
                  insertable = False,
                  editable = False,
                  deletable = False)

    group = get_vars.get("group", "volunteer")
    hr_id = get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    table = s3db.hrm_human_resource
    table.type.default = 2
    get_vars["xsltmode"] = "volunteer"
    if hr_id:
        hr = db(table.id == hr_id).select(table.type,
                                          limitby=(0, 1)).first()
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            get_vars["group"] = group

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    configure(tablename,
              deletable = False)

    mode = session.s3.hrm.mode
    if mode is not None:
        # Configure for personal mode
        s3db.hrm_human_resource.organisation_id.readable = True
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        configure("hrm_human_resource",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_certification",
                  insertable = True,
                  editable = True,
                  deletable = True)
        configure("hrm_credential",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_competency",
                  insertable = True,  # Can add unconfirmed
                  editable = False,
                  deletable = False)
        configure("hrm_training",    # Can add but not provide grade
                  insertable = True,
                  editable = False,
                  deletable = False)
        configure("hrm_experience",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("pr_group_membership",
                  insertable = False,
                  editable = False,
                  deletable = False)
    else:
        # Configure for HR manager mode
        s3.crud_strings[tablename].update(
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details"),
                title_upload = T("Import Volunteers"),
                )

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the organisation
            before processing a new data import, used for the import_prep
            hook in response.s3
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                else:
                    return # don't delete if no group specified

                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3db.resource("hrm_human_resource", filter=query)
                        resource.delete(format="xml", cascade=True)
    s3.import_prep = import_prep

    # CRUD pre-process
    def prep(r):

        # Plug-in role matrix for Admins/OrgAdmins
        S3PersonRoleManager.set_method(r, entity="pr_person")

        if r.representation == "s3json":
            current.xml.show_ids = True
        elif r.interactive and r.method != "import":
            if not r.component:
                table = r.table
                # Assume volunteers only between 12-81
                dob = table.date_of_birth
                dob.widget = S3CalendarWidget(past_months = 972,
                                              future_months = -144,
                                              )
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False
                table.age_group.readable = table.age_group.writable = False

                s3db.pr_person_details.occupation.label = T("Normal Job")

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person", "middle_name")
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "grandfather_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "year_of_birth")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")

            else:
                if r.component_name == "hours":
                    # Exclude records which are just to link to Programme
                    component_table = r.component.table
                    filter = (r.component.table.hours != None)
                    r.resource.add_component_filter("hours", filter)
                    component_table.training.readable = False
                    component_table.training_id.readable = False

                elif r.component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = table.ethnicity.readable = True
                    table.blood_type.writable = table.blood_type.readable = True
                    table.medical_conditions.writable = table.medical_conditions.readable = True
                    table.other_details.writable = table.other_details.readable = True

                elif r.component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False)

                elif r.component_name == "group_membership":
                    s3db.hrm_configure_pr_group_membership()

            if r.method == "record" or r.component_name == "human_resource":
                table = s3db.hrm_human_resource
                table.code.writable = table.code.readable = False
                table.department_id.writable = table.department_id.readable = False
                table.essential.writable = table.essential.readable = False
                #table.location_id.readable = table.location_id.writable = True
                table.person_id.writable = table.person_id.readable = False
                table.site_id.writable = table.site_id.readable = False
                table.site_contact.writable = table.site_contact.readable = False
                org = session.s3.hrm.org
                field = table.organisation_id
                if org is None:
                    field.widget = None
                else:
                    field.default = org
                    field.readable = field.writable = False

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("vol_details", "availability")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")

            resource = r.resource
            if mode is not None:
                r.resource.build_query(id=s3_logged_in_person())
            elif r.method not in ("deduplicate", "search_ac"):
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="volunteer"))
                if resource.count() == 1:
                    resource.load()
                    r.record = resource.records().first()
                    if r.record:
                        r.id = r.record.id
                if not r.record:
                    session.error = T("Record not found")
                    redirect(URL(f="volunteer"))
                if hr_id and r.component_name == "human_resource":
                    r.component_id = hr_id
                configure("hrm_human_resource", insertable = False)

        elif r.component_name == "group_membership" and r.representation == "aadata":
            s3db.hrm_configure_pr_group_membership()

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both") and \
                   r.method not in ("report", "import") and \
                   "form" in output:
                    # Insert field to set the Programme
                    # @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
                    sep = ": "
                    table = s3db.hrm_programme_hours
                    field = table.programme_id
                    if r.id:
                        query = (table.person_id == r.id)
                        default = db(query).select(table.programme_id,
                                                   orderby=table.date).last()
                        if default:
                            default = default.programme_id
                    else:
                        default = field.default
                    widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                    field_id = "%s_%s" % (table._tablename, field.name)
                    label = field.label
                    label = LABEL(label, label and sep, _for=field_id,
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                    s3_formstyle = settings.get_ui_formstyle()
                    programme = s3_formstyle(row_id, label, widget,
                                             field.comment)
                    try:
                        output["form"][0].insert(2, programme[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(2, programme[0])
                    except:
                        pass

            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname = session.s3.hrm.orgname
    else:
        orgname = None

    return current.rest_controller("pr", resourcename,
                                   csv_template = ("hrm", "volunteer"),
                                   csv_stylesheet = ("hrm", "person.xsl"),
                                   csv_extra_fields = [
                                        dict(label="Type",
                                             field=s3db.hrm_human_resource.type)
                                        ],
                                   orgname = orgname,
                                   replace_option = T("Remove existing data before import"),
                                   rheader = s3db.hrm_rheader,
                                   )

# END =========================================================================
