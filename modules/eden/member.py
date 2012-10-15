# -*- coding: utf-8 -*-

""" Sahana Eden Members Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3MembersModel",
           "member_rheader"
           ]

import datetime
from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3MembersModel(S3Model):
    """
    """

    names = ["member_membership_type",
             "member_membership",
             ]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        NONE = current.messages.NONE

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        root_org = auth.root_org()

        # ---------------------------------------------------------------------
        # Membership Types
        #
        tablename = "member_membership_type"
        table = define_table(tablename,
                             Field("name", notnull=True, length=64,
                                   label=T("Name")),
                             # Only included in order to be able to set
                             # realm_entity to filter appropriately
                             organisation_id(
                                             default = root_org,
                                             readable = False,
                                             writable = False,
                                             ),
                             s3_comments(label=T("Description"), comment=None),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Membership Type"),
            title_display = T("Membership Type Details"),
            title_list = T("Membership Types"),
            title_update = T("Edit Membership Type"),
            title_search = T("Search Membership Types"),
            title_upload = T("Import Membership Types"),
            subtitle_create = T("Add New Membership Type"),
            label_list_button = T("List Membership Types"),
            label_create_button = T("Add Membership Type"),
            label_delete_button = T("Delete Membership Type"),
            msg_record_created = T("Membership Type added"),
            msg_record_modified = T("Membership Type updated"),
            msg_record_deleted = T("Membership Type deleted"),
            msg_list_empty = T("No membership types currently registered"))

        label_create = crud_strings[tablename].label_create_button
        if root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)
        membership_type_id = S3ReusableField("membership_type_id", table,
            sortby = "name",
            label = T("Type"),
            requires = IS_NULL_OR(
                        IS_ONE_OF(db, "member_membership_type.id",
                                  self.membership_type_represent,
                                  filterby="organisation_id",
                                  filter_opts=filter_opts)),
            represent = self.membership_type_represent,
            comment=S3AddResourceLink(f="membership_type",
                                      label=label_create,
                                      title=label_create,
                                      tooltip=T("Add a new membership type to the catalog.")),
            ondelete = "SET NULL")

        configure(tablename,
                  deduplicate = self.member_type_duplicate,
                  )
        # ---------------------------------------------------------------------
        # Members
        #

        start_year = 2010 # @ToDo: deployment_setting
        end_year = current.request.now.year + 2
        year_opts = [x for x in range (start_year, end_year)]

        tablename = "member_membership"
        table = define_table(tablename,
                             organisation_id(#widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                             requires = self.org_organisation_requires(updateable=True),
                                             widget = None,
                                             empty=False),
                             Field("code",
                                   #readable=False,
                                   #writable=False,
                                   label=T("Member ID")),
                             person_id(widget=S3AddPersonWidget(controller="member"),
                                       requires=IS_ADD_PERSON_WIDGET(),
                                       comment=None),
                             membership_type_id(),
                             # History
                             s3_date("start_date",
                                     label = T("Date Joined"),
                                     ),
                             s3_date("end_date",
                                     label = T("Date resigned"),
                                     ),
                             Field("membership_fee", "double",
                                   label = T("Membership Fee"),
                                   ),
                             s3_date("membership_paid",
                                     label = T("Membership Paid")
                                     ),
                             # Location (from pr_address component)
                             location_id(readable=False,
                                         writable=False),
                             *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Member"),
            title_display = T("Member Details"),
            title_list = T("Members"),
            title_update = T("Edit Member"),
            title_search = T("Search Members"),
            title_upload = T("Import Members"),
            subtitle_create = T("Add New Member"),
            label_list_button = T("List Members"),
            label_create_button = T("Add Member"),
            label_delete_button = T("Delete Member"),
            msg_record_created = T("Member added"),
            msg_record_modified = T("Member updated"),
            msg_record_deleted = T("Member deleted"),
            msg_list_empty = T("No members currently registered"))

        table.virtualfields.append(MemberVirtualFields())

        def member_type_opts():
            """
                Provide the options for the Membership Type search filter
            """
            ttable = self.member_membership_type

            if root_org:
                query = (ttable.deleted == False) & \
                        ((ttable.organisation_id == root_org) | \
                         (ttable.organisation_id == None))
            else:
                query = (ttable.deleted == False) & \
                        (ttable.organisation_id == None)

            opts = db(query).select(ttable.id,
                                    ttable.name)
            _dict = {}
            for opt in opts:
                _dict[opt.id] = opt.name
            return _dict

        member_search = S3Search(
            simple=(self.member_search_simple_widget("simple")),
            advanced=(self.member_search_simple_widget("advanced"),
                      S3SearchOptionsWidget(
                        name="member_search_type",
                        label=T("Type"),
                        field="type",
                        cols = 3,
                        options = member_type_opts,
                      ),
                      S3SearchOptionsWidget(
                        name="member_search_paid",
                        label=T("Paid"),
                        field="paid",
                        cols = 3,
                        options = {
                                T("paid"):T("paid"),
                                T("overdue"):T("overdue"),
                                T("expired"):T("expired"),
                            },
                      ),
                      S3SearchOptionsWidget(
                        name="member_search_L1",
                        field="location_id$L1",
                        location_level="L1",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="member_search_L2",
                        field="location_id$L2",
                        location_level="L2",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="member_search_L3",
                        field="location_id$L3",
                        location_level="L3",
                        cols = 3,
                      ),
                      S3SearchOptionsWidget(
                        name="member_search_L4",
                        field="location_id$L4",
                        location_level="L4",
                        cols = 3,
                      ),
                      S3SearchLocationWidget(
                        name="member_search_map",
                        label=T("Map"),
                      ),
            )
        )

        configure(tablename,
                  deduplicate = self.member_duplicate,
                  onaccept = self.member_onaccept,
                  search_method = member_search,
                  list_fields=["person_id",
                               "organisation_id",
                               "membership_type_id",
                               "start_date",
                               # useful for testing the paid virtual field
                               #"membership_paid",
                               (T("Paid"), "paid"),
                               (T("Email"), "email"),
                               (T("Phone"), "phone"),
                               "location_id$L1",
                               "location_id$L2",
                               "location_id$L3",
                               "location_id$L4",
                               ],
                  update_realm=True,
                  )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def membership_type_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.member_membership_type
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def member_search_simple_widget(type):

        T = current.T

        return S3SearchSimpleWidget(
                    name = "member_search_simple_%s" % type,
                    label = T("Name"),
                    comment = T("You can search by person name - enter any of the first, middle or last names, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                    field = ["person_id$first_name",
                             "person_id$middle_name",
                             "person_id$last_name",
                            ]
                  )

    # ---------------------------------------------------------------------
    @staticmethod
    def member_onaccept(form):
        """ On-accept for Member records """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        setting = current.deployment_settings

        utable = current.auth.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        mtable = db.member_membership

        # Get the full record
        id = form.vars.id
        if id:
            query = (mtable.id == id)
            record = db(query).select(mtable.id,
                                      mtable.person_id,
                                      mtable.organisation_id,
                                      mtable.deleted,
                                      limitby=(0, 1)).first()
        else:
            return

        data = Storage()

        # Affiliation, record ownership and component ownership
        s3db.pr_update_affiliations(mtable, record)

        # realm_entity for the pr_person record
        person_id = record.person_id
        person = Storage(id = person_id)
        if setting.get_auth_person_realm_member_org():
            # Set pr_person.realm_entity to the human_resource's organisation pe_id
            organisation_id = record.organisation_id
            entity = s3db.pr_get_pe_id("org_organisation", organisation_id)
            if entity:
                auth.set_realm_entity(ptable, person,
                                      entity = entity,
                                      force_update = True)

        # Update the location ID from the Home Address
        atable = s3db.pr_address
        query = (atable.pe_id == ptable.pe_id) & \
                (ptable.id == record.person_id) & \
                (atable.type == 1) & \
                (atable.deleted == False)
        address = db(query).select(atable.location_id,
                                   limitby=(0, 1)).first()
        if address:
            data.location_id = address.location_id

        # Add record owner (user)
        query = (ptable.id == record.person_id) & \
                (ltable.pe_id == ptable.pe_id) & \
                (utable.id == ltable.user_id)
        user = db(query).select(utable.id,
                                utable.organisation_id,
                                utable.site_id,
                                limitby=(0, 1)).first()
        if user:
            user_id = user.id
            data.owned_by_user = user.id

        if not data:
            return
        record.update_record(**data)

        #if data.location_id:
        #    # Populate the Lx fields
        #    s3_lx_update(mtable, record.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def member_duplicate(item):
        """
            Member record duplicate detection, used for the deduplicate hook
        """

        if item.tablename == "member_membership":

            data = item.data
            person_id = "person_id" in data and data.person_id or None
            organisation_id = "organisation_id" in data and data.organisation_id or None

            table = item.table
            # 1 Membership record per Person<>Organisation
            query = (table.deleted != True) & \
                    (table.person_id == person_id) & \
                    (table.organisation_id == organisation_id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def member_type_duplicate(item):
        """
            Membership Type duplicate detection, used for the deduplicate hook
        """

        if item.tablename == "member_membership_type":

            data = item.data
            name = "name" in data and data.name or None
            organisation_id = "organisation_id" in data and data.organisation_id or None

            table = item.table
            # 1 Membership Type per Name<>Organisation
            query = (table.deleted != True) & \
                    (table.name == name) & \
                    (table.organisation_id == organisation_id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

# =============================================================================
def member_rheader(r, tabs=[]):
    """ Resource headers for component views """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None
    record = r.record
    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    T = current.T
    table = r.table
    resourcename = r.name

    # Tabs
    tabs = [(T("Person Details"), None),
            (T("Membership Details"), "membership"),
            (T("Addresses"), "address"),
            #(T("Contacts"), "contact"),
            (T("Contacts"), "contacts"),
           ]
    rheader_tabs = s3_rheader_tabs(r, tabs)

    if resourcename == "membership":
        ptable = current.s3db.pr_person
        query = (table.id == record.id) & \
                (ptable.id == table.person_id)
        person = current.db(query).select(ptable.id,
                                          ptable.first_name,
                                          ptable.middle_name,
                                          ptable.last_name,
                                          limitby=(0, 1)).first()
        if person is not None:
            rheader = DIV(DIV(s3_avatar_represent(person.id,
                                                  "pr_person",
                                                  _class="fleft"),
                              _style="padding-bottom:10px;"),
                          TABLE(
                            TR(TH(s3_fullname(person))),
                         ), rheader_tabs)
        else:
            rheader = None
    elif resourcename == "person":
        rheader = DIV(DIV(s3_avatar_represent(record.id,
                                              "pr_person",
                                              _class="fleft"),
                          _style="padding-bottom:10px;"),
                      TABLE(
            TR(TH(s3_fullname(record))),
            ), rheader_tabs)

    return rheader

# =============================================================================
class MemberVirtualFields:
    """ Virtual fields as dimension classes for reports """

    extra_fields = ["person_id",
                    "start_date",
                    "membership_paid",
                    ]

    # -------------------------------------------------------------------------
    def paid(self):
        """
            Whether the member has paid within 12 months of start_date
            anniversary

            @ToDo: Formula should come from the deployment_template
        """
        try:
            start_date = self.member_membership.start_date
        except AttributeError:
            # not available
            start_date = None
        try:
            paid_date = self.member_membership.membership_paid
        except AttributeError:
            # not available
            paid_date = None
        if start_date:
            T = current.T
            PAID = T("paid")
            OVERDUE = T("overdue")
            LAPSED = T("expired")
            lapsed = datetime.timedelta(days=183) # 6 months

            now = current.request.utcnow.date()
            now_month = now.month
            start_month = start_date.month
            if now_month > start_month:
                due = datetime.date(now.year, start_month, start_date.day)
            elif now_month == start_month:
                now_day = now.day
                start_day = start_date.day
                if now_day >= start_day:
                    due = datetime.date(now.year, start_month, start_day)
                else:
                    due = datetime.date((now.year - 1), start_month, start_day)
            else:
                due = datetime.date((now.year - 1), start_month, start_date.day)

            if not paid_date:
                # Never paid
                if (now - due) > lapsed:
                    return LAPSED
                else:
                    return OVERDUE

            if paid_date > due:
                return PAID
            elif (due - paid_date) > lapsed:
                return LAPSED
            else:
                return OVERDUE

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def email(self):
        """ Email addresses """
        try:
            person_id = self.member_membership.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.pr_person
            ctable = s3db.pr_contact
            query = (ctable.deleted == False) & \
                    (ctable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (ctable.contact_method == "EMAIL")
            contacts = current.db(query).select(ctable.value,
                                                orderby=ctable.priority)
            if contacts:
                values = [contact.value for contact in contacts]
                return ",".join(values)

        return current.messages.NONE

    # -------------------------------------------------------------------------
    def phone(self):
        """ Phone numbers """
        try:
            person_id = self.member_membership.person_id
        except AttributeError:
            # not available
            person_id = None
        if person_id:
            s3db = current.s3db
            ptable = s3db.pr_person
            ctable = s3db.pr_contact
            query = (ctable.deleted == False) & \
                    (ctable.pe_id == ptable.pe_id) & \
                    (ptable.id == person_id) & \
                    (ctable.contact_method.belongs(["SMS", "HOME_PHONE", "WORK_PHONE"]))
            contacts = current.db(query).select(ctable.value,
                                                orderby=ctable.priority)
            if contacts:
                values = [contact.value for contact in contacts]
                return ",".join(values)

        return current.messages.NONE

# END =========================================================================
