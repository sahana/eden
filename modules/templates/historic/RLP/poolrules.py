# -*- coding: utf-8 -*-

"""
    Pool Assignment Rules Helpers for RLP Template

    @license MIT
"""

import os

from lxml import etree

from gluon import current

# =============================================================================
class PoolRules(object):
    """
        Helper object to represent pool assignment rules
    """

    def __init__(self, rules=None):
        """
            Constructor

            @param rules: the path to the rules file, using default
                          path if omitted
        """

        if rules is None:
            settings = current.deployment_settings
            self.source = os.path.join(current.request.folder,
                                       "modules",
                                       "templates",
                                       "RLP",
                                       settings.get_custom("poolrules"),
                                       )
        else:
            self.source = str(rules)

        self._rules = None

    # -------------------------------------------------------------------------
    @property
    def rules(self):
        """
            The root element of the pool assignment rules
                - lazy-parses the rules XML file

            @returns: the root Element
        """

        if self._rules is None:
            try:
                tree = etree.parse(self.source)
            except (IOError, etree.Error):
                current.log.error("Could not parse pool rules")
            else:
                self._rules = tree.getroot()
        return self._rules

    # -------------------------------------------------------------------------
    def __call__(self, person_id):
        """
            Get the ID of the pool to assign the person to

            @param person_id: the person ID

            @returns: the pool ID
        """

        rules = self.rules
        if rules is None:
            return None

        # Lookup the relevant properties of the person
        item = self.lookup(person_id)

        # Get the default pool name
        pool = rules.get("default")

        # Process each pool assignment rule
        for option in rules.findall("assign"):

            # Get the pool name
            poolname = option.get("pool")

            # Check whether all rules apply
            assign = True
            for rule in option:
                if not self.applies(item, rule):
                    assign = False
                    break
            if assign:
                pool = poolname
                break

        if pool:
            # Look up the pool_id
            gtable = current.s3db.pr_group
            query = (gtable.name == pool) & \
                    (gtable.group_type.belongs(21, 22)) & \
                    (gtable.deleted == False)
            pool = current.db(query).select(gtable.id, limitby=(0, 1)).first()
            pool_id = pool.id if pool else None
        else:
            # No pool to assign to
            pool_id = None

        return pool_id

    # -------------------------------------------------------------------------
    @classmethod
    def applies(cls, item, rule):
        """
            Check if a rule applies to item

            @param item: the item
            @param rule: the rule Element
        """

        tag = rule.tag

        if tag == "all-of":
            return all(cls.applies(item, partial) for partial in rule)

        if tag == "any-of":
            return any(cls.applies(item, partial) for partial in rule)

        if tag == "none-of":
            return not any(cls.applies(item, partial) for partial in rule)

        return cls.has(item, rule)

    # -------------------------------------------------------------------------
    @staticmethod
    def has(item, rule):
        """
            Check if the item has the required property value

            @param item: the item
            @param rule: the rule Element, representing a key-value-pair with
                         key=tagname and value=element text
        """

        k, v = rule.tag, rule.text

        p = item.get(k)
        if not v:
            # Empty tag means any value at all
            return bool(p)
        else:
            return p is not None and v in p

    # -------------------------------------------------------------------------
    @staticmethod
    def lookup(person_id):
        """
            Look up the relevant properties (pools, skills, occupations)
            of a person record

            @param person_id: the person ID

            @returns: a dict {property-name: {set of names}}
        """

        db = current.db
        s3db = current.s3db

        # Look up pool memberships
        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership

        left = gtable.on(gtable.id == mtable.group_id)
        query = (mtable.person_id == person_id) & \
                (mtable.deleted == False) & \
                (gtable.group_type.belongs((21, 22)))
        rows = db(query).select(gtable.name, left=left)
        pools = {row.name for row in rows}

        # Look up occupation types
        ttable = s3db.pr_occupation_type
        ltable = s3db.pr_occupation_type_person

        join = ttable.on(ttable.id == ltable.occupation_type_id)
        query = (ltable.person_id == person_id) & \
                (ltable.deleted == False)
        rows = db(query).select(ttable.name, join=join)
        occupations = {row.name for row in rows}

        # Look up skills
        stable = s3db.hrm_skill
        ctable = s3db.hrm_competency

        join = stable.on(stable.id == ctable.skill_id)
        query = (ctable.person_id == person_id) & \
                (ctable.deleted == False)
        rows = db(query).select(stable.name, join=join)
        skills = {row.name for row in rows}

        return {"pool": pools,
                "occupation": occupations,
                "skill": skills,
                }

# END =========================================================================
