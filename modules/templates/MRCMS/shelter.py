"""
    MRCMS Shelter overview

    License: MIT
"""

import datetime
import json

from dateutil.relativedelta import relativedelta

from gluon import current, URL, \
                  A, DIV, H4, H5, I, IMG, INPUT, LABEL, \
                  SPAN, TABLE, TBODY, TD, TH, TR
from gluon.contenttype import contenttype
from gluon.streamer import DEFAULT_CHUNK_SIZE

from core import BooleanRepresent, CRUDMethod, CustomController, \
                 ICON, JSONSEPARATORS, PresenceRegistration, \
                 XLSXWriter, s3_format_fullname, s3_str

# =============================================================================
class ShelterOverview(CRUDMethod):
    """
        Overview page for a single shelter
    """

    def apply_method(self, r, **attr):
        """
            Entry point for the CRUDController

            Args:
                r: the CRUDRequest
                attr: controller parameters
        """

        if not r.record:
            r.error(405, current.ERROR.BAD_METHOD)
        if not self.permitted():
            r.unauthorised()

        output = None

        # Is the current user authorised to export the residents list?
        privileged = current.auth.s3_has_role("SHELTER_ADMIN")

        if r.http == "GET":
            if r.representation == "html":
                output = self.overview(r, privileged=privileged, **attr)
            elif r.representation == "xlsx":
                if not privileged:
                    r.unauthorised()
                else:
                    output = ResidentsList(r.record).xlsx()
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def permitted():
        """
            Checks whether the user is permitted to use this method

            Returns:
                bool
        """

        has_permission = current.auth.s3_has_permission

        return has_permission("read", "cr_shelter_registration") and \
               has_permission("read", "cr_shelter_unit")

    # -------------------------------------------------------------------------
    @staticmethod
    def overview(r, privileged=False, **attr):
        """
            Renders the shelter overview

            Args:
                r: the CRUDRequest
                attr: controller parameters
        """

        T = current.T

        record = r.record
        shelter_id = record.id

        status = ShelterStatus(shelter_id)

        # 1) Capacity -------------------------------------

        total_capacity = status.capacity()

        cap_regular = total_capacity.get("regular", 0)
        cap_transitory = total_capacity.get("transitory", 0)
        blocked = total_capacity.get("blocked", 0)

        unallocated = total_capacity.get("unallocated", 0)
        allocable = total_capacity.get("allocable", 0)

        capacity = DIV(H5(T("Capacity")),
                       TABLE(TR(TH(T("in Housing Units")), TD(cap_regular)),
                             TR(TH(T("in Staging Area")), TD(cap_transitory)),
                             TR(TD(_class="spacer", _colspan=2)),
                             TR(TH(T("Free places")), TD(unallocated)),
                             TR(TH(T("Non-allocable##shelter")), TD(blocked)),
                             TR(TH(T("Allocable##shelter")), TD(allocable), _class="stats-total"),
                             ),
                       _class="shelter-overview-stats",
                       )

        # 2) Current Occupancy ----------------------------

        population = status.population()

        regular = population.get("regular", 0)
        transitory = population.get("transitory", 0)
        total = regular + transitory

        families = status.families()
        children = status.children(max_age=18)

        cap_total = cap_regular + cap_transitory
        regular_css = "stats-excess" if regular > cap_regular else None
        transit_css = "stats-excess" if transitory > cap_transitory else None
        total_css = "stats_excess" if total > cap_total else ""

        occupancy = DIV(H5(T("Current Population##shelter")),
                        TABLE(TR(TH(T("in Housing Units")), TD(regular), _class=regular_css),
                              TR(TH(T("in Staging Area")), TD(transitory), _class=transit_css),
                              TR(TH(T("Total##set")), TD(total), _class="stats-total %s" % total_css),
                              TR(TD(_class="spacer", _colspan=2)),
                              TR(TH(T("Families")), TD(families)),
                              TR(TH(T("Children")), TD(children)),
                              ),
                        _class="shelter-overview-stats",
                        )

        # 3) Change ---------------------------------------

        days = 7
        ins = status.arrivals(days=days)
        outs = status.leavings(days=days)
        planned = status.planned(days=days)

        change = "%+d" % (ins - outs)
        available = max(0, total_capacity.get("available", 0) - planned)

        change = DIV(H5(T("Change (%(days)s Days)") % {"days": days}),
                     TABLE(TR(TH(T("Arrivals##shelter")), TD(ins)),
                           TR(TH(T("Leavings##shelter")), TD(outs)),
                           TR(TH(T("Change")), TD(change)),
                           TR(TD(_class="spacer", _colspan=2)),
                           TR(TH(T("Planned")), TD(planned)),
                           TR(TH(T("Available##disposable")), TD(available), _class="stats-total"),
                           ),
                     _class="shelter-overview-stats",
                     )

        # 4) Residents Overview ---------------------------

        if privileged:
            xlsx_btn = A(IMG(_src = "/%s/static/img/icon-xls.png" % r.application,
                             _style = "margin-left:1rem;vertical-align:text-top;",
                             ),
                        data = {"url": URL(c="cr", f="shelter",
                                           args = [r.id, "overview.xlsx"],
                                           ),
                                },
                        _title = T("Export in %(format)s format") % {"format": "XLSX"},
                        _class = "action-lnk s3-download-button",
                        )
        else:
            # User not authorised to export the residents list
            # => do not render export-button
            xlsx_btn = ""

        residents = DIV(H4(T("Residents Overview"), xlsx_btn),
                        ResidentsList(record, status=status).html(),
                        _class = "shelter-overview-residents",
                        )

        # 5) Presence Registration ------------------------

        if PresenceRegistration.permitted("cr_shelter", record.site_id):
            # Action button for presence registration
            registration = A(T("Presence Registration"),
                             _href = r.url(method="presence"),
                             _class = "action-btn dashboard-action",
                             )
        else:
            registration = ""

        # 6) Presence List --------------------------------

        # TODO Move styles into theme
        if current.auth.s3_has_roles(("ORG_ADMIN", "SECURITY")):
            presence = A(I(_class="fa fa-table", _style="margin-right:0.3rem;"),
                         T("Presence List"),
                         data = {"url": URL(c="cr", f="shelter",
                                            args = [r.id, "presence_list.xlsx"],
                                            ),
                                 },
                         _class = "action-lnk s3-download-button",
                         )
        else:
            presence = ""

        # Combined output and view template
        output = {"title": T("Shelter Overview"),
                  "occupancy": occupancy,
                  "capacity": capacity,
                  "change": change,
                  "presence": presence,
                  "residents": residents,
                  "registration": registration,
                  }
        CustomController._view("MRCMS", "shelter_overview.html")

        return output

# =============================================================================
class ResidentsList:
    """
        A list of current residents at a shelter
    """

    def __init__(self, shelter, status=None):
        """
            Args:
                shelter: the shelter Row (including id, site_id and
                         organisation_id)
        """

        self.shelter = shelter
        self.status = status

        self.shelter_id = shelter.id
        self.site_id = shelter.site_id
        self.organisation_id = shelter.organisation_id

        self._residents = None

    # -------------------------------------------------------------------------
    @property
    def units(self):
        """
            The housing units of the shelter

            Returns:
                Rows (cr_shelter_unit)
        """

        status = self.status
        if not status:
            status = self.status = ShelterStatus(self.shelter_id)

        return status.units

    # -------------------------------------------------------------------------
    @property
    def residents(self):
        """
            The residents of the shelter (lazy property)

            Returns:
                a dict {shelter_unit_id: [Row, ...]}
        """

        residents = self._residents
        if residents is None:

            db = current.db
            s3db = current.s3db

            rtable = s3db.cr_shelter_registration
            ptable = s3db.pr_person
            dtable = s3db.pr_person_details
            ctable = s3db.dvr_case
            mtable = s3db.pr_group_membership
            sptable = s3db.org_site_presence

            left = [dtable.on((dtable.person_id == ptable.id) & \
                              (dtable.deleted == False)),
                    mtable.on((mtable.person_id == ptable.id) & \
                              (mtable.deleted == False)),
                    sptable.on((sptable.person_id == ptable.id) & \
                               (sptable.site_id == self.site_id) & \
                               (sptable.deleted == False)),
                    ]
            join = [rtable.on((rtable.person_id == ptable.id) & \
                              (rtable.shelter_id == self.shelter_id) & \
                              (rtable.registration_status != 3) & \
                              (rtable.deleted == False)),
                    ctable.on((ctable.person_id == ptable.id) & \
                              (ctable.organisation_id == self.organisation_id) & \
                              (ctable.deleted == False)),
                    ]
            query = (ptable.deleted == False)
            rows = db(query).select(ptable.id,
                                    ptable.pe_label,
                                    ptable.last_name,
                                    ptable.first_name,
                                    ptable.gender,
                                    ptable.date_of_birth,
                                    dtable.nationality,
                                    ctable.reference,
                                    ctable.household_size,
                                    ctable.last_seen_on,
                                    sptable.status,
                                    mtable.id,
                                    mtable.group_id,
                                    rtable.shelter_unit_id,
                                    rtable.registration_status,
                                    rtable.check_in_date,
                                    join = join,
                                    left = left,
                                    orderby = (rtable.shelter_unit_id,
                                               mtable.group_id,
                                               ptable.last_name,
                                               ptable.date_of_birth,
                                               ~ctable.id,
                                               ~mtable.id,
                                               ~dtable.id,
                                               ),
                                    )

            # Split up residents by housing unit
            residents = {}
            seen = set()
            for row in rows:
                if row.pr_person.id in seen:
                    continue
                seen.add(row.pr_person.id)
                registration = row.cr_shelter_registration
                unit_id = registration.shelter_unit_id
                if unit_id in residents:
                    unit_residents = residents[unit_id]
                else:
                    unit_residents = residents[unit_id] = []
                unit_residents.append(row)

            self._residents = residents

        return residents

    # -------------------------------------------------------------------------
    def html(self):
        """
            Returns the residents list as HTML

            Returns:
                TABLE.residents-list
        """

        T = current.T

        # TODO verify user is permitted to read cases of the shelter org
        # TODO if not permitted to read cases, show anonymous
        # TODO show_links always true if permitted
        show_links = current.auth.s3_has_permission("read", "pr_person", c="dvr", f="person")

        # Widget ID (to attach script)
        widget_id = "residents-overview"

        # Actions
        search = DIV(LABEL("%s:" % T("Filter"),
                           INPUT(_type = "text",
                                 _length = "20",
                                 ),
                           ICON("fa fa-times", _class="clear-search"),
                           ),
                     _class = "units-search",
                     )
        expand = DIV(A(T("Collapse All"),
                       _class = "action-lnk collapse-all",
                       ),
                     "|",
                     A(T("Expand All"),
                       _class = "action-lnk expand-all",
                       ),
                     _class = "units-expand",
                     )

        actions = DIV(search, expand, _class = "units-actions")

        # Units list
        residents_list = TABLE(_class="units-list")

        residents = self.residents
        units = self.units
        for unit in units:
            unit_residents = residents.get(unit.id)
            if unit.status == 3 and not unit_residents:
                continue
            section = self.unit_section(unit, unit_residents, show_links=show_links)
            residents_list.append(section)

        # Append residents not assigned to any housing unit
        unassigned = residents.get(None)
        if unassigned:
            section = self.unit_section(None, unassigned, show_links=show_links)
            residents_list.append(section)

        # Inject script
        self.inject_script(widget_id, {})

        return DIV(actions, residents_list, _id=widget_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject the necessary JavaScript for the widget

            Args:
                widget_id: the widget ID (=element ID of the person_id field)
                options: JSON-serializable dict of widget options
        """

        s3 = current.response.s3

        # Static script
        script = "/%s/static/scripts/templates/MRCMS/residents.js" % current.request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').residentsList(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts, separators=JSONSEPARATORS),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @classmethod
    def unit_section(cls, unit, residents, show_links=False):
        """
            Builds a table section with resident data of a housing unit

            Args:
                unit: the housing unit, cr_shelter_unit Row
                residents: the residents, joined Rows
                show_links: whether to show residents names as links to
                            their case files

            Returns:
                the table section (TBODY.unit)
        """

        T = current.T

        unit_section = TBODY(cls.unit_header(unit),
                             _class = "unit",
                             )

        c, p = [], []
        if residents:
            for row in residents:
                reg = row.cr_shelter_registration
                if reg.registration_status == 2:
                    c.append(row)
                else:
                    p.append(row)

        # Representation method for presence status
        presence_repr = BooleanRepresent(labels=False, icons=True, colors=True)

        total, occupied, free, blocked, planned = None, None, None, None, None

        for i, persons in enumerate((c, p)):

            css = ""

            if i == 0:
                # Checked-in residents
                occupied = len(persons)
                css = "checked-in"
                unit_section.append(cls.resident_header())
            elif persons:
                # Planned residents
                planned = len(persons)
                css = "planned"
                subheader = cls.unit_subheader(1, len(persons) if persons else 0, css="details residents-planned")
                unit_section.append(subheader)

            group_id = None
            even, odd = "group-even", "group-odd"
            for person in persons:
                gid = person.pr_group_membership.group_id
                if not gid or gid != group_id:
                    group_id = gid
                    even, odd = odd, even
                unit_section.append(cls.resident(person,
                                                 css = "resident %s %s" % (css, even),
                                                 show_link = show_links,
                                                 presence_repr = presence_repr,
                                                 ))

            # Render placeholder rows for unoccupied capacity
            total = unit.capacity if unit else None
            if i == 0 and unit and not unit.transitory:
                # Total and free capacity
                if total is None:
                    total = 0
                free = max(total - occupied, 0)

                # Blocked capacity (can be at most all free capacity)
                blocked = min(free, unit.blocked_capacity)

                # Remaining free capacity
                if unit.status == 1:
                    free = free - blocked
                else:
                    free = blocked = 0

                for _ in range(free):
                    empty = TR(TD(I(_class="fa fa-circle-o")),
                               TD(T("Allocable##shelter"), _colspan = 6),
                               _class = "details capacity-free",
                               )
                    unit_section.append(empty)
                for _ in range(blocked):
                    empty = TR(TD(I(_class="fa fa-ban")),
                               TD(T("Not allocable"), _colspan = 6),
                               _class = "details capacity-blocked",
                               )
                    unit_section.append(empty)

        unit_section["data"] = {"name": unit.name if unit else T("Not assigned"),
                                "capacity": json.dumps([total,
                                                        occupied,
                                                        free,
                                                        blocked,
                                                        planned,
                                                        ]),
                                }

        unit_section.append(TR(TD(_colspan=8), _class="unit-spacer"))

        return unit_section

    # -------------------------------------------------------------------------
    @staticmethod
    def unit_header(unit):
        """
            Generates a table row (TR) with housing unit details

            Args:
                unit - the cr_shelter_unit Row

            Returns:
                a TR element
        """

        T = current.T

        if not unit:
            label = T("Not assigned")
        else:
            # TODO also show capacity/occupancy data
            if unit.status == 1:
                icon = I(_class="fa fa-check", _title=T("Available"))
            elif unit.status == 3:
                icon = I(_class="fa fa-times", _title=T("Closed"))
            else:
                icon = I(_class="fa fa-ban", _title=T("Not allocable"))
            label = A(icon,
                      unit.name,
                      _href=URL(c = "cr",
                                f = "shelter",
                                args = [unit.shelter_id, "shelter_unit", unit.id],
                                ),
                      _class = "unit-link",
                      )

        header = DIV(label, _class="unit-label")

        return TR(TD(header,
                     SPAN(ICON("fa fa-caret-down expand"),
                          ICON("fa fa-caret-up collapse"),
                          _class="unit-expand",
                          ),
                     _colspan=7, _class="unit-data",
                     ),
                  _class = "unit-header",
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def unit_subheader(status, number, css=None):
        """
            Generates a table row (TR) with a registration status summary

            Args:
                status: the status value
                number: the number of items with that status

            Returns:
                a TR element
        """

        s3db = current.s3db
        rtable = s3db.cr_shelter_registration

        status_label = rtable.registration_status.represent(status)

        header = DIV("%s: %s" % (status_label, number),
                     _class = css,
                     )

        return TR(TD(header, _colspan=7), _class="details unit-subheader")

    # -------------------------------------------------------------------------
    @staticmethod
    def resident_header():
        """
            Generates a table row (TR) with column headers for resident
            details

            Returns:
                a TR element
        """

        T = current.T

        return TR(TH(),
                  TH(T("ID")),
                  TH(T("Name")),
                  TH(T("Gender")),
                  TH(T("Age")),
                  TH(T("Nationality")),
                  TH(T("Presence")),
                  _class = "details resident-header",
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def resident(row, css=None, show_link=False, presence_repr=None):
        """
            Generates a table row (TR) with resident details

            Args:
                row: the (joined) Row with resident data
                css: the CSS-class for the table row
                show_link: render the resident name as link to their case file
                presence_repr: representation method for the presence status

            Returns:
                a TR element
        """

        #T = current.T
        s3db = current.s3db

        ptable = s3db.pr_person
        dtable = s3db.pr_person_details
        #sptable = s3db.org_site_presence

        person = row.pr_person
        details = row.pr_person_details
        presence = row.org_site_presence

        # ID and names
        represent_str = lambda s: s if s else "-"
        label = represent_str(person.pe_label)
        lname = represent_str(person.last_name)
        fname = represent_str(person.first_name)
        name = s3_format_fullname(fname = fname,
                                  lname = lname,
                                  truncate = True,
                                  )
        if show_link:
            case_file = URL(c="dvr", f="person", args=[person.id])
            name = A(name, _href=case_file)

        # Gender, age, nationality
        gender = ptable.gender.represent(person.gender)
        dob = person.date_of_birth
        now = current.request.utcnow.date()
        age = str(relativedelta(now, dob).years) if dob else "-"
        nationality = dtable.nationality.represent(details.nationality)

        # Presence
        status = presence.status
        if status in ("IN", "OUT"):
            p = presence_repr(status == "IN") if presence_repr else status
        else:
            p = "-"

        # Registration status
        reg = row.cr_shelter_registration
        if reg.registration_status == 2:
            icon = "fa fa-bed"
        else:
            icon = "fa fa-suitcase"

        return TR(TD(I(_class=icon)),
                  TD(label),
                  TD(name, _class="resident-name"),
                  TD(gender),
                  TD(age),
                  TD(nationality),
                  TD(p, _class="resident-presence"),
                  _class = "details " + css,
                  )

    # -------------------------------------------------------------------------
    def xlsx(self):
        """
            Serializes the residents list as XLSX

            Returns:
                a bytes stream
        """

        # Prepare the input for XLSXWriter
        table_data = {"columns": [],
                      "headers": {},
                      "types": {},
                      "rows": self.data_rows(),
                      }
        for fname, label, ftype in self.columns:
            table_data["columns"].append(fname)
            table_data["headers"][fname] = label
            table_data["types"][fname] = ftype

        # Use a title row (also includes exported-date)
        current.deployment_settings.base.xls_title_row = True
        title = current.T("Residents Overview")
        shelter_name = self.shelter.name
        if shelter_name:
            title = "%s - %s" % (shelter_name, title)

        # Generate XLSX byte stream
        output = XLSXWriter.encode(table_data, title=title, as_stream=True)

        # Set response headers
        disposition = "attachment; filename=\"residents_list.xlsx\""
        response = current.response
        response.headers["Content-Type"] = contenttype(".xlsx")
        response.headers["Content-disposition"] = disposition

        # Return stream response
        return response.stream(output,
                               chunk_size = DEFAULT_CHUNK_SIZE,
                               request = current.request
                               )

    # -------------------------------------------------------------------------
    @property
    def columns(self):
        """
            The columns for XLSX export

            Returns:
                a tuple of tuples ((fieldname, label, type))
        """

        T = current.T

        case_administration = current.auth.permission.has_permission("create",
                                                                     c = "dvr",
                                                                     f = "person",
                                                                     t = "pr_person",
                                                                     )
        if case_administration:
            return (("unit", T("Housing Unit"), "string"),
                    ("pe_label", T("ID"), "string"),
                    ("refno", T("Principal Ref.No."), "string"),
                    ("last_name", T("Last Name"), "string"),
                    ("first_name", T("First Name"), "string"),
                    ("gender", T("Gender"), "string"),
                    ("dob", T("Date of Birth"), "date"),
                    ("age", T("Age"), "string"),
                    ("nationality", T("Nationality"), "string"),
                    ("household_size", T("Size of Family"), "integer"),
                    ("status", T("Status"), "string"),
                    ("check_in_date", T("Check-in date"), "date"),
                    ("last_seen_on", T("Last seen on"), "date"),
                    ("present", T("Present##presence"), "string"),
                    )
        else:
            # Limited fields
            return (("unit", T("Housing Unit"), "string"),
                    ("pe_label", T("ID"), "string"),
                    ("last_name", T("Last Name"), "string"),
                    ("first_name", T("First Name"), "string"),
                    ("gender", T("Gender"), "string"),
                    ("dob", T("Date of Birth"), "date"),
                    ("age", T("Age"), "string"),
                    ("nationality", T("Nationality"), "string"),
                    ("present", T("Present##presence"), "string"),
                    )

    # -------------------------------------------------------------------------
    def data_rows(self):
        """
            Builds the data rows for XLSX export

            Returns:
                an ordered list of dicts [{field: value, ...}, ...]
        """

        T = current.T

        data_rows = []

        now = datetime.datetime.utcnow().date()

        s3db = current.s3db
        ptable = s3db.pr_person
        dtable = s3db.pr_person_details
        ctable = s3db.dvr_case
        rtable = s3db.cr_shelter_registration

        residents = self.residents

        units = list(self.units) + [None]
        for unit in units:
            if unit:
                unit_name = unit.name
                unit_residents = residents.get(unit.id)
            else:
                unit_name = T("Not assigned")
                unit_residents = residents.get(None)

            if not unit_residents:
                continue

            checked_in, planned = [], []
            for row in unit_residents:

                reg = row.cr_shelter_registration

                data = {"unit": unit_name,
                        }
                status = reg.registration_status
                if status == 2:
                    checked_in.append(data)
                else:
                    planned.append(data)

                # Registration details
                data["status"] = rtable.registration_status.represent(status)
                data["check_in_date"] = rtable.check_in_date.represent(reg.check_in_date)

                # Person data
                person = row.pr_person
                for fn in ("pe_label", "first_name", "last_name", "gender"):
                    represent = ptable[fn].represent
                    if not represent:
                        represent = lambda v: s3_str(v) if v else "-"
                    data[fn] = represent(person[fn])

                # Date of Birth / Age
                dob = person.date_of_birth
                data["dob"] = ptable.date_of_birth.represent(dob)
                data["age"] = str(relativedelta(now, dob).years) if dob else "-"

                # Nationality
                details = row.pr_person_details
                data["nationality"] = dtable.nationality.represent(details.nationality)

                # Household size
                case = row.dvr_case
                data["refno"] = ctable.reference.represent(case.reference)
                household_size = case.household_size
                data["household_size"] = household_size if household_size else "-"

                # Presence
                data["last_seen_on"] = ctable.last_seen_on.represent(case.last_seen_on)
                presence = row.org_site_presence
                data["present"] = s3_str(T("yes")) if presence.status == "IN" else "-"

            data_rows.extend(checked_in)
            data_rows.extend(planned)

        return data_rows

# =============================================================================
class ShelterStatus:
    """ The current capacity/occupation status of a shelter """

    def __init__(self, shelter_id):
        """
            Args:
                shelter_id: the cr_shelter record ID
        """

        self.shelter_id = shelter_id

        # Initialize
        self._units = None
        self._units_by_id = None

        self._capacity = None
        self._population = None

    # -------------------------------------------------------------------------
    @property
    def units(self):
        """
            The housing units of the shelter (lazy property)

            Returns:
                Housing units as Rows, ordered by name
        """

        units = self._units
        if units is None:

            utable = current.s3db.cr_shelter_unit
            query = (utable.shelter_id == self.shelter_id) & \
                    (utable.deleted == False)
            units = current.db(query).select(utable.id,
                                             utable.shelter_id,
                                             utable.name,
                                             utable.status,
                                             utable.capacity,
                                             utable.blocked_capacity,
                                             utable.transitory,
                                             orderby = utable.name,
                                             )
            self._units = units

        return units

    # -------------------------------------------------------------------------
    @property
    def units_by_id(self):
        """
            The housing units of the shelter

            Returns:
                a dict {unit_id: Row(cr_shelter_unit)}
        """

        units = self._units_by_id
        if not units:
            units = self._units_by_id = {row.id: row for row in self.units}

        return units

    # -------------------------------------------------------------------------
    @property
    def unit_capacity(self):
        """
            The capacities of housing units in the shelter (lazy property)

            Returns:
                a dict {unit_id: {"total": the total capacity of the unit,
                                  "excess": excess occupancy,
                                  "unallocated": number of unallocated places,
                                  "blocked": number of blocked places,
                                  "allocable": number of allocable places,
                                  }}
        """

        capacity = self._capacity

        if capacity is None:
            self._capacity = capacity = {}

            population = self.unit_population
            for unit in self.units:
                unit_id = unit.id
                total_capacity = unit.capacity if unit.status == 1 else 0

                occupied = population.get(unit_id, 0)
                free = total_capacity - occupied

                unallocated = max(0, free)
                excess_occupancy = max(0, -free)

                blocked = min(unallocated, unit.blocked_capacity)
                allocable = unallocated - blocked

                capacity[unit_id] = {"total": total_capacity,
                                     "excess": excess_occupancy,
                                     "unallocated": unallocated,
                                     "blocked": blocked,
                                     "allocable": allocable,
                                     }
        return capacity

    # -------------------------------------------------------------------------
    @property
    def unit_population(self):
        """
            The current population numbers of housing units in the
            shelter (lazy property)

            Returns: a dict {unit_id: population number}
        """

        population = self._population
        if not population:
            # Initialize
            population = {u.id: 0 for u in self.units}
            population[None] = 0

            # Look up registrations
            table = current.s3db.cr_shelter_registration
            query = (table.shelter_id == self.shelter_id) & \
                    (table.registration_status == 2) & \
                    (table.deleted == False)
            unit_id = table.shelter_unit_id
            num_persons = table.person_id.count()
            rows = current.db(query).select(num_persons,
                                            table.shelter_unit_id,
                                            groupby = table.shelter_unit_id,
                                            )

            # Update population numbers from registrations
            for row in rows:
                population[row[unit_id]] = row[num_persons]

            self._population = population

        return population

    # -------------------------------------------------------------------------
    def capacity(self):
        """
            Calculates the overall capacity details for the shelter

            Returns:
                a dict {"regular": total capacity in regular housing units,
                        "transitory": total capacity in transitory units,
                        "unallocated": number of unallocated places,
                        "blocked": number of blocked places,
                        "allocable": number of allocable places,
                        "available": number of available places,
                        }
        """

        units = self.units_by_id
        unit_capacity = self.unit_capacity

        capacity_regular = 0
        capacity_transitory = 0
        capacity_unallocated = 0
        capacity_blocked = 0

        allocable = excess = 0
        for unit_id, u in unit_capacity.items():

            unit = units.get(unit_id)
            if not unit:
                continue

            if unit.transitory:
                capacity_transitory += u["total"]
                continue

            capacity_regular += u["total"]
            capacity_blocked += u["blocked"]
            capacity_unallocated += u["unallocated"]

            allocable += u["allocable"]
            excess += u["excess"]

        # Unallocated places and excess occupancy in units even out
        capacity_unallocated = max(0, capacity_unallocated - excess)

        # Allocable capacity is reduced by excess occupancy too
        capacity_allocable = max(0, allocable - excess)

        # Available capacity is allocable capacity reduced by unassigned people
        unassigned = self.population().get("transitory", 0)
        capacity_available = max(0, capacity_allocable - unassigned)

        return {"regular": capacity_regular,
                "transitory": capacity_transitory,
                "unallocated": capacity_unallocated,
                "blocked": capacity_blocked,
                "allocable": capacity_allocable,
                "available": capacity_available,
                }

    # -------------------------------------------------------------------------
    def population(self):
        """
            Returns the current total population of the shelter,
            differentiated by housing unit group_type

            Returns:
                a dict {"regular": population in regular housing,
                        "transitory": population in transitory housing
                        }

        """

        population_regular = population_transitory = 0

        units = self.units_by_id
        for unit_id, population in self.unit_population.items():
            if not unit_id:
                # No assigned housing counts as transitory housing
                population_transitory += population
            else:
                unit = units.get(unit_id)
                if unit.transitory:
                    population_transitory += population
                else:
                    population_regular += population

        return {"regular": population_regular,
                "transitory": population_transitory,
                }

    # -------------------------------------------------------------------------
    def families(self):
        """
            Returns the number of families (=case groups) with more than
            one member currently registered at the shelter
        """

        db = current.db
        s3db = current.s3db

        rtable = s3db.cr_shelter_registration
        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership

        # Subquery for registered people
        query = (rtable.shelter_id == self.shelter_id) & \
                (rtable.registration_status == 2) & \
                (rtable.deleted == False)
        checked_in_persons = db(query)._select(rtable.person_id)

        num_checked_in_members = mtable.person_id.count(distinct=True)

        join = gtable.on((gtable.id == mtable.group_id) &
                         (gtable.group_type == 7))
        query = mtable.person_id.belongs(checked_in_persons)
        rows = db(query).select(mtable.group_id,
                                join = join,
                                groupby = mtable.group_id,
                                having = (num_checked_in_members>1),
                                )
        return len(rows)

    # -------------------------------------------------------------------------
    def children(self, max_age=18):
        """
            Returns the number of children currently checked-in at the shelter

            Args:
                max_age: the maximum age of the children
            Returns:
                integer
        """

        s3db = current.s3db
        rtable = s3db.cr_shelter_registration
        ptable = s3db.pr_person

        now = datetime.datetime.utcnow()
        earliest = now - relativedelta(years=max_age)

        join = ptable.on((ptable.id == rtable.person_id) & \
                         (ptable.date_of_birth > earliest.date()))
        query = (rtable.shelter_id == self.shelter_id) & \
                (rtable.registration_status == 2) & \
                (rtable.deleted == False)
        num_children = rtable.person_id.count(distinct=True)
        row = current.db(query).select(num_children, join=join).first()

        return row[num_children]

    # -------------------------------------------------------------------------
    def arrivals(self, days=7):
        """
            Returns the number of people currently checked-in with a
            check-in date within the last n days

            Args:
                days: the number of days
            Returns:
                integer
        """

        today = datetime.datetime.utcnow().date()
        earliest = today - relativedelta(days=days)

        rtable = current.s3db.cr_shelter_registration
        query = (rtable.shelter_id == self.shelter_id) & \
                (rtable.registration_status == 2) & \
                (rtable.check_in_date >= earliest) & \
                (rtable.deleted == False)
        num_persons = rtable.person_id.count(distinct=True)
        row = current.db(query).select(num_persons).first()

        return row[num_persons]

    # -------------------------------------------------------------------------
    def leavings(self, days=7):
        """
            Returns the number of persons checked-out from the shelter
            within the past n days

            Args:
                days: the number of days
            Returns:
                integer
        """

        db = current.db
        s3db = current.s3db

        today = datetime.datetime.utcnow().date()
        earliest = today - relativedelta(days=days)

        # Subquery to exclude all currently checked-in people
        rtable = s3db.cr_shelter_registration
        query = (rtable.shelter_id == self.shelter_id) & \
                (rtable.registration_status == 2) & \
                (rtable.deleted == False)
        checked_in = db(query)._select(rtable.person_id)

        htable = s3db.cr_shelter_registration_history
        query = (htable.shelter_id == self.shelter_id) & \
                (~(htable.person_id.belongs(checked_in))) & \
                (htable.status == 3) & \
                (htable.previous_status == 2) & \
                (htable.date >= earliest) & \
                (htable.deleted == False)
        num_persons = htable.person_id.count(distinct=True)
        row = db(query).select(num_persons).first()

        return row[num_persons]

    # -------------------------------------------------------------------------
    def planned(self, days=7):
        """
            Returns the number of planned check-ins for the shelter

            Args:
                days: the planning horizon (latest planned check-in date)
            Returns:
                integer

            Note:
                currently the planning horizon has no effect as there
                is no "planned check-in date" field yet
        """

        # TODO implement planning horizon?
        #today = datetime.datetime.utcnow().date()
        #latest = today + relativedelta(days=days)
        #query &= (rtable.planned_date <= latest)

        rtable = current.s3db.cr_shelter_registration
        query = (rtable.shelter_id == self.shelter_id) & \
                (rtable.registration_status == 1) & \
                (rtable.deleted == False)
        num_persons = rtable.person_id.count(distinct=True)
        row = current.db(query).select(num_persons).first()

        return row[num_persons]

# END =========================================================================
