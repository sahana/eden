# -*- coding: utf-8 -*-

""" Sahana Eden Members Model

    @copyright: 2012-2016 (c) Sahana Software Foundation
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

__all__ = ("S3MembersModel",
           "S3MemberProgrammeModel",
           "member_rheader"
           )

import datetime
from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3MembersModel(S3Model):
    """
    """

    names = ("member_membership_type",
             "member_membership",
             "member_membership_id",
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        organisation_id = self.org_organisation_id

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

        types = settings.get_member_membership_types()

        # ---------------------------------------------------------------------
        # Membership Types
        #
        tablename = "member_membership_type"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     organisation_id(default = root_org,
                                     readable = is_admin,
                                     writable = is_admin,
                                     ),
                     s3_comments(label = T("Description"),
                                 comment = None,
                                 ),
                     *s3_meta_fields())

        ADD_MEMBERSHIP_TYPE = T("Create Membership Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_MEMBERSHIP_TYPE,
            title_display = T("Membership Type Details"),
            title_list = T("Membership Types"),
            title_update = T("Edit Membership Type"),
            title_upload = T("Import Membership Types"),
            label_list_button = T("List Membership Types"),
            label_delete_button = T("Delete Membership Type"),
            msg_record_created = T("Membership Type added"),
            msg_record_modified = T("Membership Type updated"),
            msg_record_deleted = T("Membership Type deleted"),
            msg_list_empty = T("No membership types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        membership_type_id = S3ReusableField("membership_type_id", "reference %s" % tablename,
                                             label = T("Type"),
                                             ondelete = "SET NULL",
                                             readable = types,
                                             represent = represent,
                                             requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(db, "member_membership_type.id",
                                                                      represent,
                                                                      filterby="organisation_id",
                                                                      filter_opts=filter_opts)),
                                             sortby = "name",
                                             writable = types,
                                             comment = S3PopupLink(f = "membership_type",
                                                                   label = ADD_MEMBERSHIP_TYPE,
                                                                   title = ADD_MEMBERSHIP_TYPE,
                                                                   tooltip = T("Add a new membership type to the catalog."),
                                                                   ),
                                             )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       "organisation_id",
                                                       ),
                                            ignore_deleted = True,
                                            ),
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
                              set_min = "#member_membership_end_date",
                              ),
                      s3_date("end_date",
                              label = T("Date Resigned"),
                              set_max = "#member_membership_start_date",
                              start_field = "member_membership_start_date",
                              default_interval = 12,
                              ),
                      Field("leaving_reason",
                            label = T("Reason for Leaving"),
                            # Enable in template as-required
                            readable = False,
                            writable = False,
                            ),
                      s3_date("restart_date",
                              label = T("Date Rejoined"),
                              # Enable in template as-required
                              readable = False,
                              set_max = "#member_membership_end_date",
                              writable = False,
                              ),
                      Field("membership_fee", "double",
                            label = T("Membership Fee"),
                            ),
                      s3_date("membership_paid",
                              label = T("Membership Paid"),
                              ),
                      Field("fee_exemption", "boolean",
                            label = T("Exempted from Membership Fee"),
                            default = False,
                            # Expose in templates as needed:
                            readable = False,
                            writable = False,
                            ),
                      s3_comments(),
                      # Location (from pr_address component)
                      self.gis_location_id(readable = False,
                                           writable = False,
                                           ),
                      Field.Method("paid",
                                   self.member_membership_paid),
                      *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Member"),
            title_display = T("Member Details"),
            title_list = T("Members"),
            title_update = T("Edit Member"),
            title_upload = T("Import Members"),
            label_list_button = T("List Members"),
            label_delete_button = T("Delete Member"),
            msg_record_created = T("Member added"),
            msg_record_modified = T("Member updated"),
            msg_record_deleted = T("Member deleted"),
            msg_list_empty = T("No Members currently registered"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        list_fields = ["person_id",
                       "organisation_id",
                       ]
        if types:
            list_fields.append("membership_type_id")
        list_fields += ["start_date",
                        # useful for testing the paid virtual field
                        #"membership_paid",
                        (T("Paid"), "paid"),
                        (T("Email"), "email.value"),
                        (T("Phone"), "phone.value"),
                        ]

        report_fields = ["person_id"]
        if types:
            report_fields.append("membership_type_id")
            default_row = "membership.membership_type_id"
        else:
            default_row = "membership.paid"
        report_fields += [(T("Paid"), "paid"),
                          "organisation_id",
                          ]

        text_fields = ["organisation_id$name",
                       "organisation_id$acronym",
                       "person_id$first_name",
                       "person_id$middle_name",
                       "person_id$last_name",
                       ]
        if types:
            text_fields.append("membership_type_id")

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            report_fields.append(lfield)
            text_fields.append(lfield)

        if settings.get_org_branches():
            org_filter = S3HierarchyFilter("organisation_id",
                                           # Can be unhidden in customise_xx_resource if there is a need to use a default_filter
                                           hidden = True,
                                           leafonly = False,
                                           )
        else:
            org_filter = S3OptionsFilter("organisation_id",
                                         filter = True,
                                         header = "",
                                         # Can be unhidden in customise_xx_resource if there is a need to use a default_filter
                                         hidden = True,
                                         )

        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       ),
                          org_filter,
                          ]
        if types:
            filter_widgets.append(S3OptionsFilter("membership_type_id",
                                                  cols = 3,
                                                  hidden = True,
                                                  ))
        filter_widgets += [
            S3OptionsFilter("paid",
                            cols = 3,
                            label = T("Paid"),
                            options = {T("paid"):    T("paid"),
                                       T("overdue"): T("overdue"),
                                       T("expired"): T("expired"),
                                       #T("exempted"): T("exempted"),
                                       },
                            hidden = True,
                            ),
            S3LocationFilter("location_id",
                             label = T("Location"),
                             levels = levels,
                             hidden = True,
                             ),
            ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 facts = report_fields,
                                 defaults = Storage(
                                    cols = "membership.organisation_id",
                                    rows = default_row,
                                    fact = "count(membership.person_id)",
                                    totals = True,
                                    )
                                 )

        configure(tablename,
                  create_next = URL(f="person", args="address",
                                    vars={"membership.id": "[id]"}),
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "organisation_id",
                                                       ),
                                            ignore_deleted = True,
                                            ),
                  extra_fields = ("start_date",
                                  "membership_paid",
                                  "fee_exemption",
                                  ),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.member_onaccept,
                  report_options = report_options,
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
                  update_realm = True,
                  )

        # Components
        self.add_components(tablename,
                            # Contact Information
                            pr_contact = (# Email
                                          {"name": "email",
                                           "link": "pr_person",
                                           "joinby": "id",
                                           "key": "pe_id",
                                           "fkey": "pe_id",
                                           "pkey": "person_id",
                                           "filterby": "contact_method",
                                           "filterfor": ("EMAIL",),
                                           },
                                          # Phone
                                          {"name": "phone",
                                           "link": "pr_person",
                                           "joinby": "id",
                                           "key": "pe_id",
                                           "fkey": "pe_id",
                                           "pkey": "person_id",
                                           "filterby": "contact_method",
                                           "filterfor": ("SMS",
                                                         "HOME_PHONE",
                                                         "WORK_PHONE",
                                                         ),
                                           },
                                          ),
                            hrm_programme = {"link": "member_membership_programme",
                                             "joinby": "membership_id",
                                             "key": "programme_id",
                                             },
                            )

        represent = S3Represent(lookup=tablename, fields=["code"])
        membership_id = S3ReusableField("membership_id", "reference %s" % tablename,
                                        label = T("Member"),
                                        ondelete = "CASCADE",
                                        represent = represent,
                                        requires = IS_ONE_OF(db, "member_membership.id",
                                                             represent,
                                                             ),
                                        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(member_membership_id = membership_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def member_membership_paid(row):
        """
            Whether the member has paid within 12 months of start_date
            anniversary

            @ToDo: Formula should come from the deployment_template
        """

        T = current.T

        #try:
        #    exempted = row["member_membership.fee_exemption"]
        #except AttributeError:
        #    exempted = False
        #if excempted:
        #    return T("exempted")

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
        settings = current.deployment_settings

        utable = current.auth.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        mtable = db.member_membership

        # Get the full record
        _id = form.vars.id
        if _id:
            query = (mtable.id == _id)
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
        if settings.get_auth_person_realm_member_org():
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
            data.owned_by_user = user.id

        if not data:
            return
        record.update_record(**data)

# =============================================================================
class S3MemberProgrammeModel(S3Model):
    """ Member Programmes Model """

    names = ("member_membership_programme",
             )

    def model(self):

        # ---------------------------------------------------------------------
        # Link between members and programmes
        #
        tablename = "member_membership_programme"
        self.define_table(tablename,
                          self.hrm_programme_id(),
                          self.member_membership_id(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

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
    resourcename = r.name

    # Tabs
    tabs = [(T("Person Details"), None),
            (T("Membership Details"), "membership"),
            (T("Addresses"), "address"),
            #(T("Contacts"), "contact"),
            (T("Contacts"), "contacts"),
            ]

    if resourcename == "membership":
        table = r.table
        ptable = current.s3db.pr_person
        query = (table.id == record.id) & \
                (ptable.id == table.person_id)
        person = current.db(query).select(ptable.id,
                                          ptable.first_name,
                                          ptable.middle_name,
                                          ptable.last_name,
                                          limitby=(0, 1)).first()
        if person is not None:
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV(DIV(s3_avatar_represent(person.id,
                                                  "pr_person",
                                                  _class="fleft"),
                              _class="rheader-avatar",
                              ),
                          TABLE(TR(TH(s3_fullname(person))),
                                ),
                          rheader_tabs,
                          )
        else:
            rheader = None

    elif resourcename == "person":
        if current.deployment_settings.get_member_cv_tab():
            tabs.append((T("CV"), "cv"))
        rheader_tabs = s3_rheader_tabs(r, tabs)
        rheader = DIV(DIV(s3_avatar_represent(record.id,
                                              "pr_person",
                                              _class="fleft"),
                          _class="rheader-avatar",
                          ),
                      TABLE(TR(TH(s3_fullname(record))),
                            ),
                      rheader_tabs
                      )

    return rheader

# END =========================================================================
