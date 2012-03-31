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
                                        requires = IS_LIST_OF(IS_IN_SET(year_opts)),
                                        ),
                                  # Location (from pr_address component)
                                  location_id(readable=False,
                                              writable=False),
                                  *s3.meta_fields())

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
                       list_fields=[
                                "person_id",
                                "type",
                                "start_date",
                                "end_date",
                                #@ToDo: virtual field to show if they are paid-up or not? (or rely on report?)
                            ])
        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage()

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
            #(T("Addresses"), "address"),
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
        rheader = DIV(DIV(s3_avatar_represent(person.id,
                                              "pr_person",
                                              _class="fleft"),
                          _style="padding-bottom:10px;"),
                      TABLE(
            TR(TH(s3_fullname(person))),
            ), rheader_tabs)
        
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
