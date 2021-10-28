# -*- coding: utf-8 -*-

""" Sahana Eden Dissemination Model

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("DisseminationFinBrokerModel",
           "DisseminationIncidentReportModel",
           "DisseminationInvItemModel",
           "DisseminationMedContactModel",
           "DisseminationSecurityCheckpointModel",
           "DisseminationSecurityZoneModel",
           "DisseminationSiteModel",
           "DisseminationTransportFlightModel",
           "disseminate",
           )

from gluon import *

from s3 import *

def dissemination():
    T = current.T
    dissemination_opts = (("NONE", T("Do NOT Disseminate")),
                          ("ORG", T("Organization-only")),
                          ("WORKING_GROUP", T("Disseminate to Working Group")),
                          ("ALL", T("Disseminate to ALL")),
                          )
    return S3ReusableField("dissemination",
                           default = "NONE",
                           label = T("Dissemination Level"),
                           represent = S3Represent(options = dict(dissemination_opts)),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(dissemination_opts,
                                                  zero = None,
                                                  )
                                        ),
                           )

WORKING_GROUPS = {"cr_shelter": "LOGISTICS",
                  "event_incident_report": "SECURITY",
                  "fin_broker": "LOGISTICS",
                  "inv_inv_item": "LOGISTICS",
                  "med_contact": "MEDICAL",
                  "security_checkpoint": "SECURITY",
                  "security_zone": "SECURITY",
                  "transport_flight": "FLIGHTS",
                  }

# =============================================================================
class DisseminationFinBrokerModel(S3Model):

    names = ("dissemination_fin_broker",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Fin Brokers
        #
        tablename = "dissemination_fin_broker"
        self.define_table(tablename,
                          self.fin_broker_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationIncidentReportModel(S3Model):

    names = ("dissemination_incident_report",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Incident Reports
        #
        tablename = "dissemination_incident_report"
        self.define_table(tablename,
                          self.event_incident_report_id(empty = False,
                                                        #ondelete = "CASCADE",
                                                        ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationInvItemModel(S3Model):

    names = ("dissemination_inv_item",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Inv Items
        #
        tablename = "dissemination_inv_item"
        self.define_table(tablename,
                          self.inv_item_id(#empty = False,
                                           #ondelete = "CASCADE",
                                           ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationMedContactModel(S3Model):

    names = ("dissemination_med_contact",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Med Contacts
        #
        tablename = "dissemination_med_contact"
        self.define_table(tablename,
                          self.med_contact_id(#empty = False,
                                              #ondelete = "CASCADE",
                                              ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationSecurityCheckpointModel(S3Model):

    names = ("dissemination_security_checkpoint",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Checkpoints
        #
        tablename = "dissemination_security_checkpoint"
        self.define_table(tablename,
                          self.security_checkpoint_id(empty = False,
                                                      ondelete = "CASCADE",
                                                      ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationSecurityZoneModel(S3Model):

    names = ("dissemination_security_zone",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Security Zones
        #
        tablename = "dissemination_security_zone"
        self.define_table(tablename,
                          self.security_zone_id(empty = False,
                                                ondelete = "CASCADE",
                                                ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationSiteModel(S3Model):

    names = ("dissemination_org_site",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Sites (Currently just Shelters)
        #
        tablename = "dissemination_org_site"
        self.define_table(tablename,
                          self.org_site_id(), # super-link. Cannot alter ondelete, Empty by default.
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class DisseminationTransportFlightModel(S3Model):

    names = ("dissemination_transport_flight",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Link Dissemination to Flights
        #
        tablename = "dissemination_transport_flight"
        self.define_table(tablename,
                          self.transport_flight_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          dissemination()(),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def disseminate(form):
    """
        Disseminate to the correct people by setting the appropriate inheritance
        to the resource's unique pr_realm record
    """

    form_vars = form.vars
    level = form_vars.sub_dissemination_dissemination

    record = form.record
    if record:
        # Has the Dissemination level changed?
        if level == record.sub_dissemination_dissemination:
            # No change
            return

    db = current.db
    s3db = current.s3db

    record_id = form_vars.id

    #table = form.table # https://github.com/web2py/pydal/issues/547
    tablename = form.table._tablename
    table = s3db.table(tablename)

    # Read current realm_entity
    record = db(table.id == record_id).select(table.id,
                                              table.realm_entity,
                                              limitby = (0, 1),
                                              ).first()

    realm_entity = record.realm_entity

    if realm_entity:
        # Check it's a pr_realm record
        petable = s3db.pr_pentity
        pe = db(petable.pe_id == realm_entity).select(petable.instance_type,
                                                      limitby = (0, 1)
                                                      ).first()
        if pe.instance_type != "pr_realm":
            current.log.debug("Disseminate: record %s in %s had a realm of type %s" % (record_id,
                                                                                       tablename,
                                                                                       pe.instance_type,
                                                                                       ))
            realm_entity = None

    if realm_entity:
        # Delete all current affiliations
        from s3db.pr import pr_remove_affiliation
        pr_remove_affiliation(None, realm_entity)

    else:
        # Create a pr_realm record
        rtable = s3db.pr_realm
        realm_id = rtable.insert(name = "%s_%s" % (tablename,
                                                   record_id,
                                                   ))
        realm = Storage(id = realm_id)
        s3db.update_super(rtable, realm)
        realm_entity = realm["pe_id"]
        # Set this record to use this for it's realm
        record.update_record(realm_entity = realm_entity)

    # Lookup the Working Group
    WG = WORKING_GROUPS.get(tablename)

    # Set appropriate affiliations
    from s3db.pr import pr_add_affiliation

    # Lookup Org
    # @ToDo: This may not be reliable as some ppl are working x-org, but most records have no org in
    organisation_id = current.auth.user.organisation_id
    if not organisation_id:
        # We can't set all levels correctly
        if level not in ("WORKING_GROUP",
                         "ALL",
                         ):
            current.log.debug("Disseminate: No user.organisation_id, so cannot set level to %s" % level)
            # Nothing we can do
            return
        # Add the WG
        ftable = s3db.pr_forum
        forum = db(ftable.uuid == WG).select(ftable.pe_id,
                                             limitby = (0, 1),
                                             ).first()
        pr_add_affiliation(forum.pe_id, realm_entity, role="Realm Hierarchy")
        if level == "ALL":
            # Add All Orgs
            otable = s3db.org_organisation
            orgs = db(otable.deleted == False).select(otable.pe_id)
            for org in orgs:
                pr_add_affiliation(org.pe_id, realm_entity, role="Realm Hierarchy")
        return

    # Lookup the Forums
    ftable = s3db.pr_forum
    if level in ("WORKING_GROUP",
                 "ALL",
                 ):
        # Org WG RW & WG
        forum_uuids = ("%s_RW_%s" % (WG,
                                     organisation_id,
                                     ),
                       WG,
                       )
        
        forums = db(ftable.uuid.belongs(forum_uuids)).select(ftable.pe_id)
        for forum in forums:
            pr_add_affiliation(forum.pe_id, realm_entity, role="Realm Hierarchy")
    else:
        # Just Org WG RW
        forum = db(ftable.uuid == "%s_RW_%s" % (WG,
                                                organisation_id,
                                                )).select(ftable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
        pr_add_affiliation(forum.pe_id, realm_entity, role="Realm Hierarchy")

    if level != "NONE":
        # Lookup the Orgs
        otable = s3db.org_organisation
        if level == "ALL":
            # All Orgs
            orgs = db(otable.deleted == False).select(otable.pe_id)
            for org in orgs:
                pr_add_affiliation(org.pe_id, realm_entity, role="Realm Hierarchy")
        else:
            # Just our Org
            org = db(otable.id == organisation_id).select(otable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            pr_add_affiliation(org.pe_id, realm_entity, role="Realm Hierarchy")

    return

# END =========================================================================
