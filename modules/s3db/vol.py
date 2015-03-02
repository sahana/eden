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

__all__ = ["S3VolunteerModel",
           "S3VolunteerAwardModel",
           "S3VolunteerClusterModel",
           "vol_service_record",
           ]

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
                           label = T("Name")),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     self.org_organisation_id(default = root_org,
                                              readable = is_admin,
                                              writable = is_admin,
                                              ),
                     s3_comments(label=T("Description"),
                                 comment=None),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Award"),
            title_display = T("Award"),
            title_list = T("Award"),
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
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Award"),
            title_display = T("Award"),
            title_list = T("Award"),
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
        return dict()

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
                                             otable.acronym,
                                             otable.logo,
                                             limitby=(0, 1),
                                             ).first()
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
        manager = T("Branch Coordinator")
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
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = "%s - %s" % \
                        (vol_name, T("Volunteer Service Record")),
                    pdf_table_autogrow = "B",
                    pdf_callback = callback,
                    **attr
                    )

# END =========================================================================
