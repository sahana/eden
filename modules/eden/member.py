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

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MembersModel(S3Model):
    """
    """

    names = ["member_membership",
             ]

    def model(self):

        T = current.T
        s3 = current.response.s3
        settings = current.deployment_settings

        person_id = self.pr_person_id
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        s3_date_represent = S3DateTime.date_represent
        s3_date_format = settings.get_L10n_date_format()

        # ---------------------------------------------------------------------
        # Members
        #
        member_type_opts = {
            1: T("Normal Member"),
            2: T("Life Member"),
            3: T("Honorary Member"),
        }

        start_year = 2010 # @ToDo: deployment_setting
        end_year = current.request.now.year + 2
        year_opts = [x for x in range (start_year, end_year)]

        tablename = "member_membership"
        table = self.define_table(tablename,
                                  organisation_id(widget=S3OrganisationAutocompleteWidget(default_from_profile=True),
                                                  empty=False),
                                  person_id(widget=S3AddPersonWidget(controller="member"),
                                            requires=IS_ADD_PERSON_WIDGET(),
                                            comment=None),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(member_type_opts,
                                                             zero=None),
                                        default = 1,
                                        label = T("Type"),
                                        represent = lambda opt: \
                                            member_type_opts.get(opt,
                                                              UNKNOWN_OPT)),
                                  # History
                                  Field("start_date", "date",
                                        label = T("Date Joined"),
                                        requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("end_date", "date",
                                        label = T("Date resigned"),
                                        requires = IS_EMPTY_OR(IS_DATE(format = s3_date_format)),
                                        represent = s3_date_represent,
                                        widget = S3DateWidget()
                                        ),
                                  Field("membership_fee", "double",
                                        label = T("Membership Fee"),
                                        ),
                                  Field("membership_paid", "list:integer",
                                        label = T("Membership Paid"),
                                        # @ToDo: IS_NULL_OR()
                                        # https://groups.google.com/d/topic/web2py/qLo16MRi0UY/discussion
                                        requires = IS_LIST_OF(IS_IN_SET(year_opts)),
                                        ),
                                  # Location (from pr_address component)
                                  location_id(readable=False,
                                              writable=False),
                                   *(s3.lx_fields() + s3.meta_fields()))

        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Member"),
            title_display = T("Member Details"),
            title_list = T("Members"),
            title_update = T("Edit Member"),
            title_search = T("Search Members"),
            title_upload = T("Import Members"),
            subtitle_create = T("Add New Member"),
            subtitle_list = T("Members"),
            label_list_button = T("List All Members"),
            label_create_button = T("Add Member"),
            label_delete_button = T("Delete Member"),
            msg_record_created = T("Member added"),
            msg_record_modified = T("Member updated"),
            msg_record_deleted = T("Member deleted"),
            msg_list_empty = T("No members currently registered"))

        self.configure(tablename,
                       deduplicate = self.member_deduplicate,
                       onaccept = self.member_onaccept,
                       list_fields=[
                                "person_id",
                                "type",
                                "start_date",
                                "end_date",
                                "membership_paid",
                                #@ToDo: virtual field to show if they are paid-up or not? (or rely on report?)
                            ])
        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

    # ---------------------------------------------------------------------
    @staticmethod
    def member_onaccept(form):
        """ On-accept for Member records """

        db = current.db
        s3db = current.s3db

        utable = current.auth.settings.table_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        mtable = s3db.member_membership

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

        # Affiliation
        s3db.pr_update_affiliations(mtable, record)

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

        if data.location_id:
            # Populate the Lx fields
            current.response.s3.lx_update(mtable, record.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def member_deduplicate(item):
        """
            Member record duplicate detection, used for the deduplicate hook

            @param item: the S3ImportItem to check
        """

        if item.tablename == "member_membership":

            db = current.db
            s3db = current.s3db

            mtable = s3db.member_membership

            data = item.data

            person_id = data.person_id
            organisation_id = data.organisation_id

            # 1 Membership record per Person<>Organisation
            query = (mtable.deleted != True) & \
                    (mtable.person_id == person_id) & \
                    (mtable.organisation_id == organisation_id)
            row = db(query).select(mtable.id,
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
        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person
        query = (table.id == record.id) & \
                (ptable.id == table.person_id)
        person = db(query).select(ptable.id,
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
