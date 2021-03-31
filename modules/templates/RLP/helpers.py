# -*- coding: utf-8 -*-

"""
    Helper functions and classes for RLP template

    @license: MIT
"""

from gluon import current, A, URL, XML

from s3 import FS, S3DateFilter, S3OptionsFilter, S3Represent, s3_fullname

# =============================================================================
def rlp_active_deployments(ctable, from_date=None, to_date=None):
    """
        Helper to construct a component filter expression
        for active deployments within the given interval (or now)

        @param ctable: the (potentially aliased) component table
        @param from_date: start of the interval
        @param to_date: end of the interval

        @note: with no dates, today is assumed as the interval start+end
    """

    start = ctable.date
    end = ctable.end_date

    if not from_date and not to_date:
        from_date = to_date = current.request.utcnow

    if from_date and to_date:
        query = ((start <= to_date) | (start == None)) & \
                ((end >= from_date) | (end == None))
    elif to_date:
        query = (start <= to_date) | (start == None)
    else:
        query = (start >= from_date) | (end >= from_date) | \
                ((start == None) & (end == None))

    return query & ctable.status.belongs(("APPR", "IMPL"))

# =============================================================================
def rlp_deployed_with_org(person_id):
    """
        Check whether one or more volunteers have active or upcoming
        deployments managed by the current user (i.e. where user is
        either HRMANAGER for the deploying organisation, or COORDINATOR)

        @param person_id: a pr_person record ID, or a set|list|tuple thereof
    """

    s3 = current.response.s3

    if isinstance(person_id, (list, tuple)):
        person_ids = set(person_id)
    elif not isinstance(person_id, set):
        person_ids = {person_id}
    else:
        person_ids = person_id

    # Cache in response.s3 (we may need to check this at several points)
    deployed_with_org = s3.rlp_deployed_with_org
    if not deployed_with_org:
        deployed_with_org = s3.rlp_deployed_with_org = set()
    elif all(person_id in deployed_with_org for person_id in person_ids):
        return True

    # Check all other person_ids
    check_ids = person_ids - deployed_with_org

    today = current.request.utcnow.date()
    dtable = current.s3db.hrm_delegation
    query = current.auth.s3_accessible_query("read", dtable) & \
            (dtable.person_id.belongs(check_ids)) & \
            rlp_active_deployments(dtable, from_date=today) & \
            (dtable.deleted == False)
    deployed = current.db(query).select(dtable.person_id)
    deployed_with_org |= {row.person_id for row in deployed}

    # Update cache
    s3.rlp_deployed_with_org = deployed_with_org

    return all(person_id in deployed_with_org for person_id in person_ids)

# =============================================================================
def rlp_delegation_read_multiple_orgs():
    """
        Check if user can manage delegations of multiple orgs, and if yes,
        which.

        @returns: tuple (multiple_orgs, org_ids), where:
                        multiple (boolean) - user can manage multiple orgs
                        org_ids (list) - list of the orgs the user can manage

        @note: multiple=True and org_ids=[] means the user can manage
               delegations for all organisations (site-wide role)
    """

    realms = current.auth.permission.permitted_realms("hrm_delegation", "read")
    if realms is None:
        multiple_orgs = True
        org_ids = []
    else:
        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(realms)) & \
                (otable.deleted == False)
        rows = current.db(query).select(otable.id, limitby=(0, len(realms)))
        multiple_orgs = len(rows) > 1
        org_ids = [row.id for row in rows]

    return multiple_orgs, org_ids

# =============================================================================
def rlp_deployment_sites(managed_orgs=False, organisation_id=None):
    """
        Lookup deployment sites

        @param managed_orgs: limit to sites of organisations the user
                             can manage delegations for
        @param organisation_id: limit to sites of this organisation
                                (overrides managed_orgs)

        @returns: a dict {site_id:site_name}
    """

    db = current.db
    s3db = current.s3db

    if organisation_id:
        # Only sites of the specified organisation
        orgs = [organisation_id]
    elif managed_orgs:
        # Only sites of managed organisations
        multiple, orgs = rlp_delegation_read_multiple_orgs()
        if not multiple and not orgs:
            return {} # No managed orgs
    else:
        orgs = None

    if not orgs:
        # Sites of all organisations except MSAGD
        from .config import MSAGD
        otable = current.s3db.org_organisation
        query = (otable.name != MSAGD) & (otable.deleted == False)
        orgs = [row.id for row in db(query).select(otable.id)]

    if not orgs:
        return {}

    # Look up all sites of orgs (filter by vol_deployments type flag)
    stable = s3db.org_site
    ltable = s3db.org_site_facility_type
    ttable = s3db.org_facility_type
    left = [ltable.on((ltable.site_id == stable.site_id) & (ltable.deleted == False)),
            ttable.on(ttable.id == ltable.facility_type_id),
            ]
    query = (stable.organisation_id.belongs(orgs)) & \
            (ttable.vol_deployments == True) & \
            (stable.deleted == False)
    rows = db(query).select(stable.site_id,
                            left = left,
                            orderby = (stable.organisation_id,
                                       stable.name,
                                       ),
                            )
    site_ids = [row.site_id for row in rows]

    represent = s3db.org_SiteRepresent(show_link=False)
    labels = represent.bulk(site_ids)

    return {site_id: labels[site_id] for site_id in site_ids}

# =============================================================================
def rlp_update_pool(form, tablename=None):
    """
        Form post-process to update pool membership if required
        by pool rules
            - called as post-process of default/person custom form
            - called directly by custom onaccept/ondelete of
              default/person/X/competency

        @param form: a person FORM, or a nested Storage containing
                     the person_id as form.vars.id
    """

    try:
        person_id = form.vars.id
    except AttributeError:
        person_id = None
    if not person_id:
        return

    from .poolrules import PoolRules
    pool_id = PoolRules()(person_id)

    if pool_id:
        db = current.db
        s3db = current.s3db

        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership
        join = gtable.on((gtable.id == mtable.group_id) & \
                         (gtable.group_type.belongs((21, 22))))
        query = (mtable.person_id == person_id) & \
                (mtable.deleted == False)
        rows = db(query).select(mtable.id,
                                mtable.group_id,
                                join = join,
                                )
        existing = None
        for row in rows:
            if row.group_id == pool_id:
                existing = row
            else:
                row.delete_record()
        if existing:
            s3db.onaccept(mtable, existing)
        else:
            data = {"group_id": pool_id, "person_id": person_id}
            data["id"] = mtable.insert(**data)
            current.auth.s3_set_record_owner(mtable, data["id"])
            s3db.onaccept(mtable, data, method="create")

# =============================================================================
def get_cms_intro(module, resource, name, cmsxml=False):
    """
        Get intro from CMS

        @param module: the module prefix
        @param resource: the resource name
        @param name: the post name
        @param cmsxml: whether to XML-escape the contents or not

        @returns: the post contents, or None if not available
    """

    # Get intro text from CMS
    db = current.db
    s3db = current.s3db

    ctable = s3db.cms_post
    ltable = s3db.cms_post_module
    join = ltable.on((ltable.post_id == ctable.id) & \
                        (ltable.module == module) & \
                        (ltable.resource == resource) & \
                        (ltable.deleted == False))

    query = (ctable.name == name) & \
            (ctable.deleted == False)
    row = db(query).select(ctable.body,
                            join = join,
                            cache = s3db.cache,
                            limitby = (0, 1),
                            ).first()
    if not row:
        return None

    return XML(row.body) if cmsxml else row.body

# =============================================================================
class RLPAvailabilityFilter(S3DateFilter):
    """
        Date-Range filter with custom variable
        - without this then we parse as a vfilter which clutters error console
          & is inefficient (including preventing a bigtable optimisation)
    """

    @classmethod
    def _variable(cls, selector, operator):

        return super()._variable("$$available", operator)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter(resource, get_vars):
        """
            Filter out volunteers who have a confirmed deployment during
            selected date interval
        """

        parse_dt = current.calendar.parse_date

        from_date = parse_dt(get_vars.get("$$available__ge"))
        to_date = parse_dt(get_vars.get("$$available__le"))

        if from_date or to_date:

            db = current.db
            s3db = current.s3db

            # Must pre-query to bypass realm limits
            dtable = s3db.hrm_delegation
            query = rlp_active_deployments(dtable, from_date, to_date)
            rows = db(query).select(dtable.person_id,
                                    cache = s3db.cache,
                                    )
            if rows:
                unavailable = {row.person_id for row in rows}
                resource.add_filter(~FS("id").belongs(unavailable))

# =============================================================================
class RLPAvailabilitySiteFilter(S3OptionsFilter):
    """
        Options filter with custom variable
        - without this then we parse as a vfilter which clutters error console
          & is inefficient (including preventing a bigtable optimisation)
    """

    @classmethod
    def _variable(cls, selector, operator):

        return super()._variable("$$sites", operator)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter(resource, get_vars):
        """
            Include volunteers who have marked themselves available at
            the selected sites, or have not chosen any sites
        """

        sites = get_vars.get("$$sites__belongs")
        if sites:
            sites = [int(site_id) for site_id in sites.split(",") if site_id.isdigit()]
        if sites:
            query = FS("availability_sites.site_id").belongs(sites)
            resource.add_filter(query)

# =============================================================================
class RLPWeeklyAvailabilityFilter(S3OptionsFilter):
    """
        Options filter with custom variable
        - without this then we parse as a vfilter which clutters error console
          & is inefficient (including preventing a bigtable optimisation)
    """

    @classmethod
    def _variable(cls, selector, operator):

        return super()._variable("$$weekly", operator)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_filter(resource, get_vars):
        """
            Include volunteers who have marked themselves available on
            the selected days of week, or have not chosen any days
        """

        days, matchall = get_vars.get("$$weekly__anyof"), False
        if not days:
            days, matchall = get_vars.get("$$weekly__contains"), True

        if days:
            days = [int(d) for d in days.split(",") if d.isdigit()]
            weekly = sum(2**d for d in days) if days else 0b1111111
            if matchall:
                subset = [i for i in range(weekly, 128) if (i & weekly) == weekly]
                query = FS("availability.weekly").belongs(subset)
            else:
                subset = [i for i in range(128) if not (i & weekly)]
                query = ~(FS("availability.weekly").belongs(subset))
            resource.add_filter(query)

# =============================================================================
class RLPDelegatedPersonRepresent(S3Represent):

    def __init__(self, show_link=True, linkto=None):
        """
            Constructor

            @param show_link: show representation as clickable link
            @param linkto: URL for the link, using "[id]" as placeholder
                           for the record ID
        """

        super(RLPDelegatedPersonRepresent, self).__init__(
                                                lookup = "pr_person",
                                                show_link = show_link,
                                                linkto = linkto,
                                                )

        self.coordinator = current.auth.s3_has_role("COORDINATOR")

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

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        # Get the person names
        rows = db(query).select(table.id,
                                table.pe_label,
                                table.first_name,
                                table.middle_name,
                                table.last_name,
                                limitby = (0, count),
                                )
        self.queries += 1
        person_ids = {row.id for row in rows}

        # For all persons found, get the alias
        pdtable = s3db.pr_person_details
        query = (pdtable.person_id.belongs(person_ids)) & \
                (pdtable.deleted == False)
        details = db(query).select(pdtable.person_id, pdtable.alias)
        aliases = {item.person_id: item.alias for item in details}
        self.queries += 1

        # Check which persons are currently deployed with org
        rlp_deployed_with_org(person_ids)

        for row in rows:
            alias = aliases.get(row.id, "***")
            row.alias = alias if alias else "-"

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent a row

            @param row: the Row
        """

        if self.coordinator or \
           row.id in current.response.s3.rlp_deployed_with_org:
            repr_str = "[%s] %s" % (row.pe_label, s3_fullname(row))
        else:
            repr_str = "[%s] %s" % (row.pe_label, row.alias)

        return repr_str

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (br_case_activity.id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        url = URL(c = "vol", f = "person", args = [row.id], extension = "")

        return A(v, _href = url)

# END =========================================================================
