# -*- coding: utf-8 -*-

""" Sahana Eden Beneficiary Registry and Case Management Models

    @copyright: 2018-2019 (c) Sahana Software Foundation
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

__all__ = ("BRCaseModel",
           "BRNeedsModel",
           "BRInstanceModel",
           "BRResponseModel",
           "BRAppointmentModel",
           "BRCaseEventModel",
           "BRPaymentModel",
           "BRNotesModel",
           "BRLanguageModel",
           "BRLegalStatusModel",
           "BRServiceContactModel",
           "BRReferralModel",
           "BRVulnerabilityModel",
           "br_DocEntityRepresent",
           "br_case_read_orgs",
           "br_case_default_org",
           "br_case_default_status",
           "br_group_membership_onaccept",
           "br_household_size",
           "br_rheader",
           "br_terminology",
           "br_crud_strings",
           )

#import datetime

#from collections import OrderedDict

from gluon import *
from gluon.storage import Messages, Storage

from ..s3 import *
#from s3layouts import S3PopupLink

CASE_GROUP = 7

# =============================================================================
class BRCaseModel(S3Model):
    """
        Model for BR Cases
    """

    # TODO separate table for transferability

    names = ("br_case",
             "br_case_status",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # TODO Case Type
        #

        # ---------------------------------------------------------------------
        # Case Status
        #
        tablename = "br_case_status"
        define_table(tablename,
                     Field("workflow_position", "integer",
                           default = 1,
                           label = T("Workflow Position"),
                           requires = IS_INT_IN_RANGE(1, None),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Workflow Position"),
                                                             T("Rank when ordering cases by status"),
                                                             ),
                                         ),
                           ),
                     Field("code", length=64, notnull=True, unique=True,
                           label = T("Status Code"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.code" % tablename,
                                                     ),
                                       ],
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Status Code"),
                                                             T("A unique code to identify the status"),
                                                             ),
                                         ),
                           ),
                     Field("name",
                           label = T("Status"),
                           # Prep only, to allow single column imports of cases:
                           #requires = IS_NOT_EMPTY(),
                           ),
                     Field("is_default", "boolean",
                           default = False,
                           label = T("Default Status"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Default Status"),
                                                             T("This status applies for new cases unless specified otherwise"),
                                                             ),
                                         ),
                           ),
                     Field("is_closed", "boolean",
                           default = False,
                           label = T("Case Closed"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Case Closed"),
                                                           T("Cases with this status are closed"),
                                                           ),
                                         ),
                           ),
                     s3_comments(
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" % (T("Comments"),
                                                             T("Describe the meaning, reasons and potential consequences of this status"),
                                                             ),
                                         ),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Case Status"),
            title_display = T("Case Status"),
            title_list = T("Case Statuses"),
            title_update = T("Edit Case Status"),
            label_list_button = T("List Case Statuses"),
            label_delete_button = T("Delete Case Status"),
            msg_record_created = T("Case Status added"),
            msg_record_modified = T("Case Status updated"),
            msg_record_deleted = T("Case Status deleted"),
            msg_list_empty = T("No Case Statuses currently defined")
            )

        # Table configuration
        configure(tablename,
                  # Allow imports to change the status code:
                  deduplicate = S3Duplicate(primary = ("name",),
                                            ignore_deleted = True,
                                            ),
                  onaccept = self.case_status_onaccept,
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "br_case_status.id",
                                                          represent,
                                                          orderby = "br_case_status.workflow_position",
                                                          sort = False,
                                                          )),
                                    sortby = "workflow_position",
                                    )

        # ---------------------------------------------------------------------
        # Case: TODO explain entity
        #
        default_organisation = settings.get_org_default_organisation()

        # Household size tracking
        household_size = settings.get_br_household_size()
        household_size_writable = household_size and household_size != "auto"

        tablename = "br_case"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),

                     # Case assignment
                     self.org_organisation_id(
                            default = default_organisation,
                            readable = not default_organisation,
                            writable = not default_organisation,
                            ),

                     # The beneficiary
                     self.pr_person_id(ondelete = "CASCADE",
                                       ),

                     # Basic date fields
                     s3_date(label = T("Registration Date"),
                             default = "now",
                             empty = False,
                             ),

                     # Case status
                     status_id(),

                     # Household size tracking
                     Field("household_size", "integer",
                           default = 1,
                           label = T("Household Size"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, None)),
                           readable = household_size,
                           writable = household_size_writable,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Household Size"),
                                                           T("Number of persons belonging to the same household"),
                                                           ),
                                         ),
                           ),

                     # Invalid flag
                     Field("invalid", "boolean",
                           default = False,
                           label = T("Invalid"),
                           represent = s3_yes_no_represent,
                           # Enabled in controller:
                           readable = False,
                           writable = False,
                           ),

                     # Standard comments and meta fields
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       create_onaccept = self.case_create_onaccept,
                       update_onaccept = self.case_onaccept,
                       super_entity = ("doc_entity",),
                       )

        # ---------------------------------------------------------------------
        # TODO Case Details
        #

        # ---------------------------------------------------------------------
        # TODO Case Dates
        #

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        #dummy = S3ReusableField("dummy_id", "integer",
        #                        readable = False,
        #                        writable = False,
        #                        )

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def case_status_onaccept(form):
        """
            Onaccept routine for case statuses:
                - only one status can be the default

            @param form: the FORM
        """

        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        # If this status is the default, then set is_default-flag
        # for all other statuses to False:
        if "is_default" in form_vars and form_vars.is_default:
            table = current.s3db.br_case_status
            current.db(table.id != record_id).update(is_default = False)

    # -------------------------------------------------------------------------
    @classmethod
    def case_create_onaccept(cls, form):
        """
            Wrapper for case_onaccept when called during create
            rather than update

            @param form: the FORM
        """

        cls.case_onaccept(form, create=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def case_onaccept(form, create=False):
        """
            Case onaccept routine:
            - auto-create active appointments
            - count household size for new cases

            @param form: the FORM
            @param create: perform additional actions for new cases
        """

        db = current.db
        s3db = current.s3db

        # Read form data
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        # Get the case
        ctable = s3db.br_case
        stable = s3db.br_case_status
        left = stable.on(stable.id == ctable.status_id)
        query = (ctable.id == record_id)
        row = db(query).select(ctable.id,
                               ctable.person_id,
                               #ctable.closed_on,
                               stable.is_closed,
                               left = left,
                               limitby = (0, 1),
                               ).first()
        if not row:
            return
        case = row.br_case

        # Update closed_on date TODO
        #if row.br_case_status.is_closed:
        #    if not case.closed_on:
        #        case.update_record(closed_on = current.request.utcnow.date())
        #elif case.closed_on:
        #    case.update_record(closed_on = None)

        # Get the person ID
        person_id = case.person_id

        # Auto-create standard appointments TODO
        #atable = s3db.br_case_appointment
        #ttable = s3db.br_case_appointment_type
        #left = atable.on((atable.type_id == ttable.id) &
        #                 (atable.person_id == person_id) &
        #                 (atable.deleted != True))
        #query = (atable.id == None) & \
        #        (ttable.active == True) & \
        #        (ttable.deleted != True)
        #rows = db(query).select(ttable.id, left=left)
        #for row in rows:
        #    atable.insert(case_id = record_id,
        #                  person_id = person_id,
        #                  type_id = row.id,
        #                  )

        if create and \
           current.deployment_settings.get_br_household_size() == "auto":
            # Count household size for newly created cases, in order
            # to catch pre-existing case group memberships
            gtable = s3db.pr_group
            mtable = s3db.pr_group_membership
            query = ((mtable.person_id == person_id) & \
                     (mtable.deleted != True) & \
                     (gtable.id == mtable.group_id) & \
                     (gtable.group_type == 7))
            rows = db(query).select(gtable.id)
            for row in rows:
                br_household_size(row.id)

# =============================================================================
class BRNeedsModel(S3Model):
    pass

# =============================================================================
class BRInstanceModel(S3Model):
    pass

# =============================================================================
class BRResponseModel(S3Model):
    pass

# =============================================================================
class BRAppointmentModel(S3Model):
    pass

# =============================================================================
class BRCaseEventModel(S3Model):
    pass

# =============================================================================
class BRPaymentModel(S3Model):
    pass

# =============================================================================
class BRNotesModel(S3Model):
    pass

# =============================================================================
# =============================================================================
class BRLanguageModel(S3Model):
    pass

# =============================================================================
class BRLegalStatusModel(S3Model):
    pass

# =============================================================================
class BRServiceContactModel(S3Model):
    pass

# =============================================================================
# =============================================================================
class BRReferralModel(S3Model):
    pass

# =============================================================================
class BRVulnerabilityModel(S3Model):
    pass

# =============================================================================
# =============================================================================
class br_DocEntityRepresent(S3Represent):
    """ Module context-specific representation of doc-entities """

    def __init__(self,
                 case_label=None,
                 case_group_label=None,
                 activity_label=None,
                 use_sector=True,
                 use_need=False,
                 show_link=False,
                 ):
        """
            Constructor

            @param case_label: label for cases (default: "Case")
            @param case_group_label: label for case groups (default: "Case Group")
            @param activity_label: label for case activities
                                   (default: "Activity")
            @param use_need: use need if available instead of subject
            @param use_sector: use sector if available instead of
                               activity label
            @param show_link: show representation as clickable link
        """

        super(br_DocEntityRepresent, self).__init__(lookup = "doc_entity",
                                                    show_link = show_link,
                                                    )

        T = current.T

        if case_label:
            self.case_label = case_label
        else:
            self.case_label = br_terminology().CASE

        if case_group_label:
            self.case_group_label = case_group_label
        else:
            self.case_group_label = T("Family")

        if activity_label:
            self.activity_label = activity_label
        else:
            self.activity_label = T("Activity")

        self.use_need = use_need
        self.use_sector = use_sector

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        table = self.table
        ptable = s3db.pr_person

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = db(query).select(table.doc_id,
                                table.instance_type,
                                limitby = (0, count),
                                orderby = table.instance_type,
                                )
        self.queries += 1

        # Sort by instance type
        doc_ids = {}
        for row in rows:
            doc_id = row.doc_id
            instance_type = row.instance_type
            if instance_type not in doc_ids:
                doc_ids[instance_type] = {doc_id: row}
            else:
                doc_ids[instance_type][doc_id] = row

        need_ids = set()
        sector_ids = set()
        for instance_type in ("br_case", "br_case_activity", "pr_group"):

            doc_entities = doc_ids.get(instance_type)
            if not doc_entities:
                continue

            # The instance table
            itable = s3db[instance_type]

            # Look up person and instance data
            query = itable.doc_id.belongs(doc_entities.keys())
            if instance_type == "pr_group":
                mtable = s3db.pr_group_membership
                left = [mtable.on((mtable.group_id == itable.id) & \
                                  (mtable.deleted == False)),
                        ptable.on(ptable.id == mtable.person_id),
                        ]
            else:
                left = ptable.on(ptable.id == itable.person_id)
            fields = [itable.id,
                      itable.doc_id,
                      ptable.id,
                      ptable.first_name,
                      ptable.middle_name,
                      ptable.last_name,
                      ]
            if instance_type == "br_case_activity":
                fields.extend((itable.sector_id,
                               itable.subject,
                               itable.need_id,
                               ))
            if instance_type == "pr_group":
                fields.extend((itable.name,
                               itable.group_type,
                               ))
            irows = db(query).select(left=left, *fields)
            self.queries += 1

            # Add the person+instance data to the entity rows
            for irow in irows:
                instance = irow[instance_type]
                entity = doc_entities[instance.doc_id]

                if hasattr(instance, "sector_id"):
                    sector_ids.add(instance.sector_id)
                if hasattr(instance, "need_id"):
                    need_ids.add(instance.need_id)

                entity[instance_type] = instance
                entity.pr_person = irow.pr_person

            # Bulk represent any sector ids
            if sector_ids and "sector_id" in itable.fields:
                represent = itable.sector_id.represent
                if represent and hasattr(represent, "bulk"):
                    represent.bulk(list(sector_ids))

            # Bulk represent any need ids
            if need_ids and "need_id" in itable.fields:
                represent = itable.need_id.represent
                if represent and hasattr(represent, "bulk"):
                    represent.bulk(list(need_ids))

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        reprstr = self.default

        instance_type = row.instance_type
        if hasattr(row, "pr_person"):

            if instance_type == "br_case":

                person = row.pr_person
                title = s3_fullname(person)
                label = self.case_label

            elif instance_type == "br_case_activity":

                table = current.s3db.br_case_activity
                activity = row.br_case_activity

                title = activity.subject
                if self.use_need:
                    need_id = activity.need_id
                    if need_id:
                        represent = table.need_id.represent
                        title = represent(need_id)

                label = self.activity_label
                if self.use_sector:
                    sector_id = activity.sector_id
                    if sector_id:
                        represent = table.sector_id.represent
                        label = represent(sector_id)

            elif instance_type == "pr_group":

                group = row.pr_group

                if group.group_type == 7:
                    label = self.case_group_label
                    if group.name:
                        title = group.name
                    else:
                        person = row.pr_person
                        title = s3_fullname(person)
                else:
                    label = current.T("Group")
                    title = group.name or self.default
            else:
                title = None
                label = None

            if title:
                reprstr = "%s (%s)" % (s3_str(title), s3_str(label))

        return reprstr

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (doc_entity.doc_id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        link = v

        if row:
            if row.instance_type == "br_case_activity":
                try:
                    person_id = row.pr_person.id
                    case_activity_id = row.br_case_activity.id
                except AttributeError:
                    pass
                else:
                    url = URL(c = "br",
                              f = "person",
                              args = [person_id,
                                      "case_activity",
                                      case_activity_id,
                                      ],
                              extension="",
                              )
                    link = A(v, _href=url)

        return link

# =============================================================================
# =============================================================================
def br_case_default_status():
    """
        Helper to get/set the default status for case records

        @return: the default status_id
    """

    s3db = current.s3db

    ctable = s3db.br_case
    field = ctable.status_id

    default = field.default
    if not default:

        # Look up the default status
        stable = s3db.br_case_status
        query = (stable.is_default == True) & \
                (stable.deleted != True)
        row = current.db(query).select(stable.id, limitby=(0, 1)).first()

        if row:
            # Set as field default in case table
            default = field.default = row.id

    return default

# -------------------------------------------------------------------------
def br_case_read_orgs():
    """
        Check if the user has read access to cases of more than one org

        @returns: tuple (multiple_orgs, org_ids)
    """

    realms = current.auth.permission.permitted_realms("br_case", "read")
    if realms is None:
        multiple_orgs = True
        org_ids = []
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id)
        multiple_orgs = len(rows) > 1
        org_ids = [row.id for row in rows]

    return multiple_orgs, org_ids

# -------------------------------------------------------------------------
def br_case_default_org():
    """
        Determine the default organisation for new cases

        @returns: tuple (default_org, multiple_orgs)
    """

    default_org = current.deployment_settings.get_org_default_organisation()
    if default_org:
        return default_org, False

    auth = current.auth
    realms = auth.permission.permitted_realms("br_case", "create")

    if realms is None:
        # User can create cases for any org
        orgs = []
        multiple_orgs = True
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id)
        orgs = [row.id for row in rows]
        multiple_orgs = len(rows) > 1

    if multiple_orgs:
        user_org = auth.user.organisation_id if auth.user else None
        if user_org and user_org in orgs:
            default_org = user_org
    elif orgs:
        default_org = orgs[0]

    return default_org, multiple_orgs

# =============================================================================
def br_household_size(group_id):
    """
        Update the household_size for all cases in the given case group,
        taking into account that the same person could belong to multiple
        case groups. To be called onaccept of pr_group_membership if automatic
        household size is enabled

        @param group_id: the group_id of the case group (group_type == 7)
    """

    db = current.db
    s3db = current.s3db
    ptable = s3db.pr_person
    gtable = s3db.pr_group
    mtable = s3db.pr_group_membership

    # Get all persons related to this group_id, make sure this is a case group
    join = [mtable.on((mtable.group_id == gtable.id) &
                      (mtable.deleted != True)),
            ptable.on(ptable.id == mtable.person_id)
            ]
    query = (gtable.id == group_id) & \
            (gtable.group_type == 7) & \
            (gtable.deleted != True)
    rows = db(query).select(ptable.id, join=join)
    person_ids = set([row.id for row in rows])

    if person_ids:
        # Get case group members for each of these person_ids
        ctable = s3db.br_case
        rtable = ctable.with_alias("member_cases")
        otable = mtable.with_alias("case_members")
        join = ctable.on(ctable.person_id == mtable.person_id)
        left = [otable.on((otable.group_id == mtable.group_id) &
                          (otable.deleted != True)),
                rtable.on(rtable.person_id == otable.person_id),
                ]
        query = (mtable.person_id.belongs(person_ids)) & \
                (mtable.deleted != True) & \
                (rtable.id != None)
        rows = db(query).select(ctable.id,
                                otable.person_id,
                                join = join,
                                left = left,
                                )

        # Count heads
        CASE = str(ctable.id)
        MEMBER = str(otable.person_id)
        groups = {}
        for row in rows:
            member_id = row[MEMBER]
            case_id = row[CASE]
            if case_id not in groups:
                groups[case_id] = set([member_id])
            else:
                groups[case_id].add(member_id)

        # Update the related cases
        for case_id, members in groups.items():
            number_of_members = len(members)
            db(ctable.id == case_id).update(household_size = number_of_members)

# =============================================================================
def br_group_membership_onaccept(membership, group, group_id, person_id):
    """
        Module-specific extensions for pr_group_membership_onaccept

        @param membership: the pr_group_membership record
                           - required fields: id, deleted, group_head
        @param group: the pr_group record
                      - required fields: id, group_type
        @param group_id: the group ID (if membership was deleted)
        @param person_id: the person ID (if membership was deleted)
    """

    db = current.db
    s3db = current.s3db

    table = s3db.pr_group_membership
    gtable = s3db.pr_group
    ctable = s3db.br_case

    response = current.response
    s3 = response.s3
    if s3.purge_case_groups:
        return

    # Get the group type
    if not group.id and group_id:
        query = (gtable.id == group_id) & \
                (gtable.deleted != True)
        row = db(query).select(#gtable.id,
                               gtable.group_type,
                               limitby = (0, 1),
                               ).first()
        if row:
            group = row

    if group.group_type == CASE_GROUP:

        # Case groups should only have one group head
        if not membership.deleted and membership.group_head:
            query = (table.group_id == group_id) & \
                    (table.id != membership.id) & \
                    (table.group_head == True)
            db(query).update(group_head=False)

        update_household_size = current.deployment_settings.get_br_household_size() == "auto"
        recount = s3db.br_household_size

        if update_household_size and membership.deleted and person_id:
            # Update the household size for removed group member
            query = (table.person_id == person_id) & \
                    (table.group_id != group_id) & \
                    (table.deleted != True) & \
                    (gtable.id == table.group_id) & \
                    (gtable.group_type == CASE_GROUP)
            row = db(query).select(table.group_id, limitby=(0, 1)).first()
            if row:
                # Person still belongs to other case groups, count properly:
                recount(row.group_id)
            else:
                # No further case groups, so household size is 1
                ctable = s3db.br_case
                cquery = (ctable.person_id == person_id)
                db(cquery).update(household_size = 1)

        if not s3.bulk:
            # Get number of (remaining) members in this group
            query = (table.group_id == group_id) & \
                    (table.deleted != True)
            rows = db(query).select(table.id, limitby = (0, 2))

            if len(rows) < 2:
                # Update the household size for current group members
                if update_household_size:
                    recount(group_id)
                    update_household_size = False
                # Remove the case group if it only has one member
                s3.purge_case_groups = True
                resource = s3db.resource("pr_group", id=group_id)
                resource.delete()
                s3.purge_case_groups = False

            elif not membership.deleted:
                # Generate a case for new case group member
                # ...unless we already have one
                query = (ctable.person_id == person_id) & \
                        (ctable.deleted != True)
                row = db(query).select(ctable.id, limitby=(0, 1)).first()
                if not row:
                    # Customise case resource
                    r = S3Request("br", "case", current.request)
                    r.customise_resource("br_case")

                    # Get the default case status from database
                    s3db.br_case_default_status()

                    # Create a case
                    cresource = s3db.resource("br_case")
                    try:
                        # Using resource.insert for proper authorization
                        # and post-processing (=audit, ownership, realm,
                        # onaccept)
                        cresource.insert(person_id=person_id)
                    except S3PermissionError:
                        # Unlikely (but possible) that this situation
                        # is deliberate => issue a warning
                        response.warning = current.T("No permission to create a case record for new group member")

        # Update the household size for current group members
        if update_household_size:
            recount(group_id)

# =============================================================================
def br_rheader(r, tabs=None):
    """ BR Resource Headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        record_id = record.id

        if tablename == "pr_person":

            if not tabs:

                # Basic Case Documentation
                tabs = [(T("Basic Details"), None),
                        (T("Contact Info"), "contacts"), # TODO make optional
                        # optional ID-tab TODO
                        (T("Family Members"), "group_membership/"), # TODO make optional
                        (T("Photos"), "image"), # TODO make optional
                        (T("Documents"), "document/"), # TODO make optional
                        ]

            case = resource.select(["first_name",
                                    "middle_name",
                                    "last_name",
                                    "case.status_id",
                                    "case.invalid",
                                    "case.household_size",
                                    "case.organisation_id",
                                    ],
                                    represent = True,
                                    raw_data = True,
                                    ).rows

            if not case:
                # Target record exists, but doesn't match filters
                return None

            # Extract case data
            case = case[0]

            name = s3_fullname
            case_status = lambda row: case["br_case.status_id"]
            household_size = lambda row: case["br_case.household_size"]
            organisation = lambda row: case["br_case.organisation_id"]

            rheader_fields = [[(T("ID"), "pe_label"),
                               (T("Case Status"), case_status),
                               (T("Organisation"), organisation),
                               ],
                              ["date_of_birth",
                               (T("Size of Family"), household_size),
                               ],
                              ]

            invalid = case["_row"]["br_case.invalid"]
            if invalid:
                # "Invalid Case" Hint
                hint = lambda record: SPAN(T("Invalid Case"),
                                           _class="invalid-case",
                                           )
                rheader_fields.insert(0, [(None, hint)])

            # Generate rheader XML
            rheader = S3ResourceHeader(rheader_fields, tabs, title=name)(
                            r,
                            table = resource.table,
                            record = record,
                            )

            # Add profile picture
            from s3 import s3_avatar_represent
            rheader.insert(0, A(s3_avatar_represent(record_id,
                                                    "pr_person",
                                                    _class = "rheader-avatar",
                                                    ),
                                _href=URL(f = "person",
                                          args = [record_id, "image"],
                                          vars = r.get_vars,
                                          ),
                                )
                           )
        else:
            rheader = None

    return rheader

# =============================================================================
def br_terminology():
    """
        Terminology-sensitive labels for BR (other than CRUD strings)

        @returns: Messages instance
    """

    labels = current.response.s3.br_labels
    if labels is None:

        terminology = current.deployment_settings.get_br_terminology()
        labels = Messages(current.T)

        if terminology == "Beneficiary":
            labels.CASE = "Beneficiary"
            labels.CASES = "Beneficiaries"
            labels.CURRENT = "Current Beneficiaries"
            labels.CLOSED = "Former Beneficiaries"

        elif terminology == "Client":
            labels.CASE = "Client"
            labels.CASES = "Clients"
            labels.CURRENT = "Current Clients"
            labels.CLOSED = "Former Clients"

        else:
            labels.CASE = "Case"
            labels.CASES = "Cases"
            labels.CURRENT = "Current Cases"
            labels.CLOSED = "Closed Cases"

        current.response.s3.br_labels = labels

    return labels

# =============================================================================
def br_crud_strings(tablename):
    """
        Terminology-sensitive CRUD strings for BR

        @param tablename: the table name

        @returns: Storage of CRUD strings
    """

    T = current.T
    terminology = current.deployment_settings.get_br_terminology()

    if tablename == "pr_person":
        if terminology == "Beneficiary":
            crud_strings = Storage(
                label_create = T("Create Beneficiary"),
                title_display = T("Beneficiary Details"),
                title_list = T("Beneficiaries"),
                title_update = T("Edit Beneficiary Details"),
                label_list_button = T("List Beneficiaries"),
                label_delete_button = T("Delete Beneficiary"),
                msg_record_created = T("Beneficiary added"),
                msg_record_modified = T("Beneficiary details updated"),
                msg_record_deleted = T("Beneficiary deleted"),
                msg_list_empty = T("No Beneficiaries currently registered")
                )
        elif terminology == "Client":
            crud_strings = Storage(
                label_create = T("Create Client"),
                title_display = T("Client Details"),
                title_list = T("Clients"),
                title_update = T("Edit Client Details"),
                label_list_button = T("List Clients"),
                label_delete_button = T("Delete Client"),
                msg_record_created = T("Client added"),
                msg_record_modified = T("Client details updated"),
                msg_record_deleted = T("Client deleted"),
                msg_list_empty = T("No Clients currently registered")
                )
        else:
            crud_strings = Storage(
                label_create = T("Create Case"),
                title_display = T("Case Details"),
                title_list = T("Cases"),
                title_update = T("Edit Case Details"),
                label_list_button = T("List Cases"),
                label_delete_button = T("Delete Case"),
                msg_record_created = T("Case added"),
                msg_record_modified = T("Case details updated"),
                msg_record_deleted = T("Case deleted"),
                msg_list_empty = T("No Cases currently registered")
                )
    else:
        crud_strings = current.response.s3.crud_strings.get(tablename)

    return crud_strings

# END =========================================================================
