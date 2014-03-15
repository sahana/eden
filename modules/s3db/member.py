# -*- coding: utf-8 -*-

""" Sahana Eden Members Model

    @copyright: 2012-13 (c) Sahana Software Foundation
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
from s3layouts import S3AddResourceLink

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
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        organisation_id = self.org_organisation_id

        NONE = current.messages["NONE"]

        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)

        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table

        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        if settings.get_org_autocomplete():
            org_widget = S3OrganisationAutocompleteWidget(default_from_profile=True)
        else:
            org_widget = None

        # ---------------------------------------------------------------------
        # Membership Types
        #
        tablename = "member_membership_type"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label=T("Name")),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
                                     ),
                     s3_comments(label=T("Description"), comment=None),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Membership Type"),
            title_display = T("Membership Type Details"),
            title_list = T("Membership Types"),
            title_update = T("Edit Membership Type"),
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

        represent = S3Represent(lookup=tablename)
        membership_type_id = S3ReusableField("membership_type_id", "reference %s" % tablename,
                                             sortby = "name",
                                             label = T("Type"),
                                             requires = IS_NULL_OR(
                                                            IS_ONE_OF(db, "member_membership_type.id",
                                                                      represent,
                                                                      filterby="organisation_id",
                                                                      filter_opts=filter_opts)),
                                             represent = represent,
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
        tablename = "member_membership"
        define_table(tablename,
                     organisation_id(
                        empty = False,
                        requires = self.org_organisation_requires(
                                        updateable = True,
                                        ),
                        widget = org_widget,
                      ),
                      Field("code",
                            label = T("Member ID"),
                            #readable = False,
                            #writable = False,
                            ),
                      self.pr_person_id(
                        comment = None,
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="member"),
                      ),
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
                      self.gis_location_id(readable = False,
                                           writable = False),
                      Field.Method("paid",
                                   self.member_membership_paid),
                      *s3_meta_fields())

        crud_strings[tablename] = Storage(
            title_create = T("Add Member"),
            title_display = T("Member Details"),
            title_list = T("Members"),
            title_update = T("Edit Member"),
            title_upload = T("Import Members"),
            subtitle_create = T("Add New Member"),
            label_list_button = T("List Members"),
            label_create_button = T("Add Member"),
            label_delete_button = T("Delete Member"),
            msg_record_created = T("Member added"),
            msg_record_modified = T("Member updated"),
            msg_record_deleted = T("Member deleted"),
            msg_list_empty = T("No Members currently registered"))

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

            rows = db(query).select(ttable.id, ttable.name)
            return dict((row.id, row.name) for row in rows)

        # Which levels of Hierarchy are we using?
        hierarchy = current.gis.get_location_hierarchy()
        levels = hierarchy.keys()
        if len(settings.get_gis_countries()) == 1 or \
           s3.gis.config.region_location_id:
            levels.remove("L0")

        list_fields = ["person_id",
                       "organisation_id",
                       "membership_type_id",
                       "start_date",
                       # useful for testing the paid virtual field
                       #"membership_paid",
                       (T("Paid"), "paid"),
                       (T("Email"), "email.value"),
                       (T("Phone"), "phone.value"),
                       ]

        report_fields = ["person_id",
                         "membership_type_id",
                         "paid",
                         "organisation_id",
                         ]

        text_fields = ["membership_type_id",
                       "organisation_id$name",
                       "organisation_id$acronym",
                       "person_id$first_name",
                       "person_id$middle_name",
                       "person_id$last_name",
                       ]

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            report_fields.append(lfield)
            text_fields.append(lfield)

        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         ),
            S3OptionsFilter("membership_type_id",
                            cols = 3,
                            options = member_type_opts,
                            hidden = True,
                            ),
            S3OptionsFilter("paid",
                            cols = 3,
                            options = {T("paid"):    T("paid"),
                                       T("overdue"): T("overdue"),
                                       T("expired"): T("expired"),
                                       },
                            hidden = True,
                            ),
            S3OptionsFilter("organisation_id",
                            widget = "multiselect",
                            hidden = True,
                            ),
            S3LocationFilter("location_id",
                             label = T("Location"),
                             levels = levels,
                             widget = "multiselect",
                             hidden = True,
                             ),
            ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 facts = report_fields,
                                 defaults = Storage(
                                    cols = "membership.organisation_id",
                                    rows = "membership.membership_type_id",
                                    fact = "count(membership.person_id)",
                                    totals = True,
                                    )
                                 )

        configure(tablename,
                  create_next = URL(f="person", args="address",
                                    vars={"membership.id": "[id]"}),
                  deduplicate = self.member_duplicate,
                  extra_fields = ["start_date", "membership_paid"],
                  list_fields = list_fields,
                  onaccept = self.member_onaccept,
                  report_options = report_options,
                  filter_widgets = filter_widgets,
                  update_realm = True,
                  # Default summary
                  summary = [{"name": "addform",
                              "common": True,
                              "widgets": [{"method": "create"}],
                             },
                             {"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"}]
                              },
                             {"name": "report",
                              "label": "Report",
                              "widgets": [{"method": "report",
                                           "ajax_init": True}]
                              },
                             {"name": "map",
                              "label": "Map",
                              "widgets": [{"method": "map",
                                           "ajax_init": True}],
                              },
                             ],
                  )

        # Components
        add_components(tablename,
                       # Contact Information
                       pr_contact = (# Email
                                     {"name": "email",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": "contact_method",
                                      "filterfor": ["EMAIL"],
                                     },
                                     # Phone
                                     {"name": "phone",
                                      "link": "pr_person",
                                      "joinby": "id",
                                      "key": "pe_id",
                                      "fkey": "pe_id",
                                      "pkey": "person_id",
                                      "filterby": "contact_method",
                                      "filterfor": ["SMS",
                                                    "HOME_PHONE",
                                                    "WORK_PHONE",
                                                   ],
                                     },
                                    ),
                      )
                      
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def member_membership_paid(row):
        """
            Whether the member has paid within 12 months of start_date
            anniversary

            @ToDo: Formula should come from the deployment_template
        """

        try:
            start_date = row["member_membership.start_date"]
        except AttributeError:
            # not available
            start_date = None
        try:
            paid_date = row["member_membership.membership_paid"]
        except AttributeError:
            # not available
            paid_date = None

        if start_date:

            T = current.T
            PAID = T("paid")
            OVERDUE = T("overdue")
            LAPSED = T("expired")
            lapsed = datetime.timedelta(days=183) # 6 months
            year = datetime.timedelta(days=365)
            now = current.request.utcnow.date()

            if not paid_date:
                # Never renewed since Membership started
                # => due within 1 year
                due = start_date + year
                if now < due:
                    return PAID
                elif now > (due + lapsed):
                    return LAPSED
                else:
                    return OVERDUE

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
                # now_month < start_month
                due = datetime.date((now.year - 1), start_month, start_date.day)

            if paid_date >= due:
                return PAID
            elif (due - paid_date) > lapsed:
                return LAPSED
            else:
                return OVERDUE

        return current.messages["NONE"]
        
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
        # @ToDo
        #s3db.pr_update_affiliations(mtable, record)

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
    
# END =========================================================================
