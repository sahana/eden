# -*- coding: utf-8 -*-
#
# s3fields unit tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3fields.py
#
import unittest
from gluon.languages import lazyT

from s3 import S3ResourceTree
from s3.s3fields import *
from s3compat import basestring

from unit_tests import run_suite

# =============================================================================
class S3RepresentTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):

        T = current.T
        self.test_opts = {
            1: "Test1",
            2: "Test2",
            3: "Test3"
        }

        current.auth.override = True

        s3db = current.s3db

        otable = s3db.org_organisation
        org1 = Storage(name="Represent Test Organisation1")
        org1_id = otable.insert(**org1)
        org1.update(id=org1_id)
        s3db.update_super(otable, org1)

        org2 = Storage(name="Represent Test Organisation2")
        org2_id = otable.insert(**org2)
        org2.update(id=org2_id)
        s3db.update_super(otable, org2)

        self.id1 = org1_id
        self.id2 = org2_id

        self.name1 = org1.name
        self.name2 = org2.name

    # -------------------------------------------------------------------------
    def testSetup(self):
        """ Check lazy setup method """

        # Check for options
        r = S3Represent(options=self.test_opts)
        self.assertFalse(r.setup)
        r._setup()
        self.assertTrue(r.setup)
        self.assertEqual(r.tablename, None)
        self.assertEqual(r.options, self.test_opts)

        # Check for lookups
        r = S3Represent(lookup="org_organisation")
        self.assertFalse(r.setup)
        self.assertEqual(r.options, None)
        self.assertEqual(r.tablename, "org_organisation")
        self.assertEqual(r.key, None)
        self.assertEqual(r.fields, None)
        self.assertEqual(r.labels, None)
        self.assertEqual(r.table, None)
        r._setup()
        self.assertTrue(r.setup)
        self.assertEqual(r.options, None)
        self.assertEqual(r.tablename, "org_organisation")
        self.assertEqual(r.key, "id")
        self.assertEqual(r.fields, ["name"])
        self.assertEqual(r.labels, None)
        self.assertEqual(r.table, current.db.org_organisation)

    # -------------------------------------------------------------------------
    def testOptions(self):
        """ Test option field representation """

        r = S3Represent(options=self.test_opts, none="NONE")

        # Standard variants
        self.assertEqual(r(1), "Test1")
        self.assertEqual(r.multiple([1, 2, 3]), "Test1, Test2, Test3")
        self.assertEqual(r.bulk([1, 2, 3]),
                         {
                            1: "Test1",
                            2: "Test2",
                            3: "Test3",
                            None: "NONE",
                         }
        )

        # list:type
        r = S3Represent(options=self.test_opts,
                        none="NONE", multiple=True)

        # Should work with both, single value and list
        self.assertEqual(r(1), "Test1")
        self.assertEqual(r([1, 2]), "Test1, Test2")

        # Multiple does always expect list of lists
        self.assertRaises(ValueError, r.multiple, [1, 2, 3])

        # Check multiple with list:type
        result = r.multiple([[1, 2]]).split(", ")
        self.assertTrue("Test1" in result)
        self.assertTrue("Test2" in result)
        self.assertEqual(len(result), 2)

        # Check that multiple with list:type de-duplicates properly
        result = r.multiple([[1, 2], [2, 3]]).split(", ")
        self.assertTrue("Test1" in result)
        self.assertTrue("Test2" in result)
        self.assertTrue("Test3" in result)
        self.assertEqual(len(result), 3)

        # Check bulk with list:type
        result = r.bulk([[1, 2], [2, 3]])
        self.assertEqual(len(result), 4)
        self.assertTrue(1 in result)
        self.assertEqual(result[1], "Test1")
        self.assertTrue(2 in result)
        self.assertEqual(result[2], "Test2")
        self.assertTrue(3 in result)
        self.assertEqual(result[3], "Test3")
        self.assertTrue(None in result)
        self.assertEqual(result[None], "NONE")

    # -------------------------------------------------------------------------
    def testForeignKeys(self):
        """ Test foreign key lookup representation """

        r = S3Represent(lookup="org_organisation")

        # Check lookup value by value
        self.assertEqual(r(self.id1), self.name1)
        self.assertEqual(r(self.id2), self.name2)
        self.assertEqual(r.queries, 2)

        # Check lookup of multiple values
        self.assertEqual(r.multiple([self.id1, self.id2]),
                         "%s, %s" % (self.name1, self.name2))
        # Should not have needed any additional queries
        self.assertEqual(r.queries, 2)

        # Check bulk lookup
        result = r.bulk([self.id1, self.id2])
        self.assertTrue(len(result), 3)
        self.assertEqual(result[self.id1], self.name1)
        self.assertEqual(result[self.id2], self.name2)
        self.assertTrue(None in result)
        # Should still not have needed any additional queries
        self.assertEqual(r.queries, 2)

        # Check that only one query is used for multiple values
        r = S3Represent(lookup="org_organisation")
        result = r.bulk([self.id1, self.id2])
        self.assertTrue(len(result), 3)
        self.assertEqual(r.queries, 1)

        # Check translation
        r = S3Represent(lookup="org_organisation", translate=True)
        result = r(self.id1)
        self.assertTrue(isinstance(result, lazyT))
        self.assertEqual(result, current.T(self.name1))

    def testRowsPrecedence(self):

        # Check that rows get preferred over values
        r = S3Represent(lookup="org_organisation")

        otable = current.s3db.org_organisation
        org1 = otable[self.id1]
        org2 = otable[self.id2]

        # Test single value
        self.assertEqual(r(None, row=org1), self.name1)
        self.assertEqual(r(self.id2, row=org1), self.name1)

        # Test multiple
        result = r.multiple(None, rows=[org1, org2])
        self.assertTrue(isinstance(result, basestring))
        self.assertTrue(", " in result)
        result = result.split(", ")
        self.assertEqual(len(result), 2)
        self.assertTrue(self.name1 in result)
        self.assertTrue(self.name2 in result)

        result = r.multiple([self.id1], rows=[org1, org2])
        self.assertTrue(isinstance(result, basestring))
        self.assertTrue(", " in result)
        result = result.split(", ")
        self.assertEqual(len(result), 2)
        self.assertTrue(self.name1 in result)
        self.assertTrue(self.name2 in result)

        # Test bulk
        result = r.bulk(None, rows=[org1, org2])
        self.assertTrue(len(result), 3)
        self.assertEqual(result[self.id1], self.name1)
        self.assertEqual(result[self.id2], self.name2)
        self.assertTrue(None in result)

        result = r.bulk([self.id1], rows=[org1, org2])
        self.assertTrue(len(result), 3)
        self.assertEqual(result[self.id1], self.name1)
        self.assertEqual(result[self.id2], self.name2)
        self.assertTrue(None in result)

    # -------------------------------------------------------------------------
    def testListReference(self):
        """ Test Foreign Key Representation in list:reference types """

        r = S3Represent(lookup="org_organisation",
                        multiple=True,
                        #linkto=URL(c="org", f="organisation", args=["[id]"]),
                        show_link=True)

        a = current.request.application

        # Single value gives a single result
        result = r(self.id1)
        self.assertTrue(isinstance(result, DIV))
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], A))
        self.assertEqual(result[0].attributes["_href"],
                         "/%s/org/organisation/%s" % (a, self.id1))
        self.assertEqual(result[0].components[0],
                         "Represent Test Organisation1")

        # Test with show_link=False
        result = r(self.id1, show_link=False)
        self.assertEqual(result, self.name1)

        # List value gives a comma-separated list
        result = r([self.id1, self.id2], show_link=False).split(", ")
        self.assertEqual(len(result), 2)
        self.assertTrue(self.name1 in result)
        self.assertTrue(self.name2 in result)

        values = [[self.id1, self.id2], [self.id2], [None, self.id1]]

        # Multiple lists give a comma-separated list of unique values
        result = r.multiple(values, show_link=False).split(", ")
        self.assertEqual(len(result), 3)
        self.assertTrue(self.name1 in result)
        self.assertTrue(self.name2 in result)
        self.assertTrue(current.messages.NONE in result)

        # Bulk representation gives a dict of all unique values
        result = r.bulk(values, show_link=False)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[self.id1], self.name1)
        self.assertEqual(result[self.id2], self.name2)
        self.assertTrue(None in result)

        # Test render_list method
        repr1 = r.render_list(values[0], result, show_link=False)
        self.assertEqual(repr1, ", ".join([self.name1, self.name2]))
        repr2 = r.render_list(values[1], result, show_link=False)
        self.assertEqual(repr2, self.name2)

        # Test render_list with show_link
        result = r.bulk(values)
        repr1 = r.render_list(values[0], result)
        self.assertTrue(isinstance(repr1, DIV))
        self.assertEqual(len(repr1), 3)
        self.assertTrue(isinstance(repr1[0], A))
        self.assertEqual(repr1[0].attributes["_href"],
                         "/%s/org/organisation/%s" % (a, self.id1))
        self.assertEqual(repr1[0].components[0],
                         "Represent Test Organisation1")
        self.assertEqual(repr1[1], ", ")
        self.assertTrue(isinstance(repr1[2], A))
        self.assertEqual(repr1[2].attributes["_href"],
                         "/%s/org/organisation/%s" % (a, self.id2))
        self.assertEqual(repr1[2].components[0],
                         "Represent Test Organisation2")

        # Check NONE-option
        repr2 = r.render_list(values[2], result)
        self.assertTrue(isinstance(repr2, DIV))
        self.assertEqual(len(repr2), 3)
        self.assertEqual(str(repr2[0]), str(current.messages.NONE))

        # Check representation of None and empty lists
        self.assertEqual(r(None, show_link=False), str(current.messages.NONE))
        self.assertEqual(r([]), str(current.messages.NONE))
        self.assertEqual(r.multiple([None], show_link=False), str(current.messages.NONE))
        self.assertEqual(r.multiple([[]], show_link=False), str(current.messages.NONE))

        # All that should have taken exactly 2 queries!
        self.assertEqual(r.queries, 2)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class S3ExtractLazyFKRepresentationTests(unittest.TestCase):
    """ Test lazy representation of foreign keys in datatables """

    tablename = "export_lazy_fk_represent"

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        db = current.db
        db.define_table(cls.tablename,
                        Field("location_id",
                              "reference gis_location"),
                        Field("organisation_id",
                              "reference org_organisation"),
                        Field("facility_type_id",
                              "list:reference org_facility_type"),
                        *s3_meta_fields())

    # -------------------------------------------------------------------------
    def setUp(self):

        tablename = self.tablename

        s3db = current.s3db
        table = s3db[tablename]
        s3db.add_components("org_organisation",
                            **{tablename: {"name": "test",
                                           "joinby": "organisation_id",
                                          },
                              }
                           )
        current.auth.override = True


        # Create locations
        locations = (Storage(name="FK Represent TestLocation 1"),
                     Storage(name="FK Represent TestLocation 2"))
        ltable = s3db.gis_location
        for i in range(len(locations)):
            location = locations[i]
            location_id = ltable.insert(**location)
            location["id"] = location_id
        self.locations = locations

        # Create facility types
        fac_types = (Storage(name="FK Represent TestFacType P"),
                     Storage(name="FK Represent TestFacType Q"),
                     Storage(name="FK Represent TestFacType R"))
        ttable = s3db.org_facility_type
        for i in range(len(fac_types)):
            fac_type = fac_types[i]
            fac_type_id = ttable.insert(**fac_type)
            fac_type["id"] = fac_type_id
        self.fac_types = fac_types

        # Create organisation
        org = Storage(name="FK Represent TestOrg A")
        otable = s3db.org_organisation
        org_id = otable.insert(**org)
        org["id"] = org_id
        s3db.update_super(otable, org)
        self.org = org

        # Create test records
        facs = (Storage(organisation_id=org.id,
                        facility_type_id=[fac_types[0].id, fac_types[1].id],
                        location_id=locations[0].id),
                Storage(organisation_id=org.id,
                        facility_type_id=[fac_types[1].id, fac_types[2].id],
                        location_id=locations[1].id))
        for i in range(len(facs)):
            fac = facs[i]
            fac_id = table.insert(**fac)
            fac["id"] = fac_id
        self.facs = facs

    # -------------------------------------------------------------------------
    def testRepresentReferenceSingleNoLinkto(self):
        """
            Test Representation of reference, single value,
            without linkto
        """

        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.organisation_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_organisation")
        table = resource.table
        table.organisation_id.represent = renderer

        data = resource.select(["id", "organisation_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)
        self.assertEqual(output[fname], self.org.name)

    # -------------------------------------------------------------------------
    def testRepresentReferenceSingleLinktoOn(self):
        """
            Test Representation of reference, single value,
            with linkto
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.organisation_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_organisation",
                               #linkto=URL(c="org", f="organisation", args=["[id]"]),
                               show_link=True)
        table = resource.table
        table.organisation_id.represent = renderer

        data = resource.select(["id", "organisation_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        representation = output[fname]
        self.assertTrue(isinstance(representation, A))
        self.assertEqual(representation.attributes["_href"],
                         "/%s/org/organisation/%s" %
                            (current.request.application, self.org.id))
        self.assertEqual(representation.components[0],
                         self.org.name)

    # -------------------------------------------------------------------------
    def testRepresentReferenceSingleLinktoOff(self):
        """
            Test Representation of reference, single value,
            with linkto + show_link=False
        """

        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.organisation_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_organisation",
                               linkto=URL(c="org", f="organisation", args=["[id]"]))
        table = resource.table
        table.organisation_id.represent = renderer

        data = resource.select(["id", "organisation_id"],
                               limit=None,
                               represent=True,
                               show_links=False)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))

        self.assertTrue(fname in output)
        self.assertEqual(output[fname], self.org.name)

    # -------------------------------------------------------------------------
    def testRepresentReferenceMultipleNoLinkto(self):
        """
            Test Representation of reference, multiple values,
            without linkto
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.location_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="gis_location")
        ftable.location_id.represent = renderer

        resource = s3db.resource("org_organisation", id=self.org.id)
        data = resource.select(["id", "test.location_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(len(result), 1)
        output = result[0]
        self.assertTrue(fname in output)
        names = output[fname].split(", ")
        self.assertEqual(len(names), 2)
        self.assertTrue(self.locations[0].name in names)
        self.assertTrue(self.locations[1].name in names)

    # -------------------------------------------------------------------------
    def testRepresentReferenceMultipleLinktoOn(self):
        """
            Test Representation of reference, multiple values,
            with linkto
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.location_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="gis_location",
                               #linkto=URL(c="gis", f="location", args=["[id]"]),
                               show_link=True)
        ftable.location_id.represent = renderer

        resource = s3db.resource("org_organisation", id=self.org.id)

        data = resource.select(["id", "name", "test.location_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(len(result), 1)
        output = result[0]
        self.assertTrue(fname in output)
        names = output[fname]
        self.assertTrue(isinstance(names, DIV))

        from lxml import etree
        tree = etree.fromstring("<div>%s</div>" % names)
        links = tree.findall("a")
        self.assertEqual(len(links), 2)

        appname = current.request.application
        a = lambda location: (location.name,
                              "/%s/gis/location/%s" % (appname, location.id))

        types = dict(a(location) for location in self.locations)
        for link in links:
            name = link.text
            self.assertTrue(name in types)
            self.assertEqual(link.get("href", None),
                             types[name])

    # -------------------------------------------------------------------------
    def testRepresentReferenceMultipleLinktoOff(self):
        """
            Test Representation of reference, multiple values,
            with linkto + show_link=False
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.location_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="gis_location",
                               linkto=URL(c="gis", f="location", args=["[id]"]))
        ftable.location_id.represent = renderer

        resource = s3db.resource("org_organisation", id=self.org.id)

        data = resource.select(["id", "name", "test.location_id"],
                               limit=None,
                               represent=True,
                               show_links=False)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(len(result), 1)
        output = result[0]
        self.assertTrue(fname in output)
        names = output[fname].split(", ")
        self.assertEqual(len(names), 2)
        self.assertTrue(self.locations[0].name in names)
        self.assertTrue(self.locations[1].name in names)

    # -------------------------------------------------------------------------
    def testRepresentListReferenceSingleNoLinkto(self):
        """
            Test Representation of list:reference, single value,
            without linkto
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True)
        table = resource.table
        table.facility_type_id.represent = renderer

        data = resource.select(["id", "facility_type_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        representation = output[fname].split(", ")
        self.assertEqual(len(representation), 2)
        self.assertTrue(self.fac_types[0].name in representation)
        self.assertTrue(self.fac_types[1].name in representation)

    # -------------------------------------------------------------------------
    def testRepresentListReferenceSingleLinktoOn(self):
        """
            Test Representation of list:reference, single value,
            with linkto
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True,
                               #linkto=URL(c="org", f="facility_type", args=["[id]"]),
                               show_link=True)
        table = resource.table
        table.facility_type_id.represent = renderer

        data = resource.select(["id", "facility_type_id"],
                               limit=None,
                               represent=True)

        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        names = output[fname]
        self.assertTrue(isinstance(names, DIV))

        from lxml import etree
        tree = etree.fromstring("<div>%s</div>" % names)
        links = tree.findall("a")
        self.assertEqual(len(links), 2)

        appname = current.request.application
        a = lambda fac_type: (fac_type.name,
                              "/%s/org/facility_type/%s" % (appname, fac_type.id))

        types = dict(a(fac_type) for fac_type in self.fac_types)
        for link in links:
            name = link.text
            self.assertTrue(name in types)
            self.assertEqual(link.get("href", None),
                             types[name])

    # -------------------------------------------------------------------------
    def testRepresentListReferenceSingleLinktoOff(self):
        """
            Test Representation of list:reference, single value,
            with linkto + show_link=False
        """
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        fac = self.facs[0]
        resource = s3db.resource(tablename, id=fac.id)

        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True,
                               linkto=URL(c="org", f="facility_type", args=["[id]"]))
        table = resource.table
        table.facility_type_id.represent = renderer

        data = resource.select(["id", "facility_type_id"],
                               limit=None,
                               represent=True,
                               show_links=False)

        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        representation = output[fname].split(", ")
        self.assertEqual(len(representation), 2)
        self.assertTrue(self.fac_types[0].name in representation)
        self.assertTrue(self.fac_types[1].name in representation)

    # -------------------------------------------------------------------------
    def testRepresentListReferenceMultipleNoLinkto(self):
        """
            Test Representation of list:reference, multiple values,
            without linkto
        """

        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.location_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="gis_location",
                               linkto=URL(c="gis", f="location", args=["[id]"]))
        ftable.location_id.represent = renderer

        resource = s3db.resource("org_organisation", id=self.org.id)

        data = resource.select(["id", "name", "test.location_id"],
                               limit=None,
                               represent=True,
                               show_links=False)

        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(len(result), 1)
        output = result[0]
        self.assertTrue(fname in output)
        names = output[fname].split(", ")
        self.assertEqual(len(names), 2)
        self.assertTrue(self.locations[0].name in names)
        self.assertTrue(self.locations[1].name in names)

    # -------------------------------------------------------------------------
    def testRepresentListReferenceSingleNoLinkto(self):
        """
            Test Representation of list:reference, single value,
            without linkto
        """

        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True)
        ftable.facility_type_id.represent = renderer

        org = self.org
        resource = s3db.resource("org_organisation", id=org.id)

        data = resource.select(["id", "test.facility_type_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)

        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        representation = output[fname].split(", ")
        self.assertEqual(len(representation), 3)
        self.assertTrue(self.fac_types[0].name in representation)
        self.assertTrue(self.fac_types[1].name in representation)
        self.assertTrue(self.fac_types[2].name in representation)

    # -------------------------------------------------------------------------
    def testRepresentListReferenceMultipleLinktoOn(self):
        """
            Test Representation of list:reference, multiple values,
            with linkto
        """

        s3db = current.s3db
        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True,
                               #linkto=URL(c="org", f="facility_type", args=["[id]"]),
                               show_link=True)
        ftable.facility_type_id.represent = renderer

        org = self.org
        resource = s3db.resource("org_organisation", id=org.id)

        data = resource.select(["id", "test.facility_type_id"],
                               limit=None,
                               represent=True)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)

        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        names = output[fname]
        self.assertTrue(isinstance(names, DIV))

        from lxml import etree
        tree = etree.fromstring("<div>%s</div>" % names)
        links = tree.findall("a")
        self.assertEqual(len(links), 3)

        appname = current.request.application
        a = lambda fac_type: (fac_type.name,
                              "/%s/org/facility_type/%s" % (appname, fac_type.id))

        types = dict(a(fac_type) for fac_type in self.fac_types)
        for link in links:
            name = link.text
            self.assertTrue(name in types)
            self.assertEqual(link.get("href", None),
                             types[name])

    # -------------------------------------------------------------------------
    def testRepresentListReferenceMultipleLinktoOff(self):

        s3db = current.s3db
        tablename = self.tablename
        fname = "%s.facility_type_id" % tablename

        ftable = current.db[tablename]
        renderer = S3Represent(lookup="org_facility_type",
                               multiple=True,
                               linkto=URL(c="org", f="facility_type", args=["[id]"]))
        ftable.facility_type_id.represent = renderer

        org = self.org
        resource = s3db.resource("org_organisation", id=org.id)

        data = resource.select(["id", "test.facility_type_id"],
                               limit=None,
                               represent=True,
                               show_links=False)
        result = data["rows"]

        self.assertEqual(renderer.queries, 1)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)

        output = result[0]
        self.assertTrue(isinstance(output, Storage))
        self.assertTrue(fname in output)

        representation = output[fname].split(", ")
        self.assertEqual(len(representation), 3)
        self.assertTrue(self.fac_types[0].name in representation)
        self.assertTrue(self.fac_types[1].name in representation)
        self.assertTrue(self.fac_types[2].name in representation)

    # -------------------------------------------------------------------------
    def tearDown(self):

        del current.model["components"]["org_organisation"]["test"]

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        try:
            current.db[cls.tablename].drop()
        except:
            pass


#=============================================================================
class S3ExportLazyFKRepresentationTests(unittest.TestCase):
    """ Test lazy representations of foreign keys in exports """

    # -------------------------------------------------------------------------
    def setUp(self):

        self.tablename = tablename = "export_lazy_fk_represent"
        db = current.db
        db.define_table(tablename,
                        Field("location_id",
                              "reference gis_location"),
                        Field("organisation_id",
                              "reference org_organisation"),
                        Field("facility_type_id",
                              "list:reference org_facility_type"),
                        *s3_meta_fields())

        current.auth.override = True

        s3db = current.s3db

        # Create locations
        locations = (Storage(name="FK Represent TestLocation 1"),
                     Storage(name="FK Represent TestLocation 2"))
        ltable = s3db.gis_location
        for i in range(len(locations)):
            location = locations[i]
            location_id = ltable.insert(**location)
            location["id"] = location_id
        self.locations = Storage([(l.id, l) for l in locations])

        # Create facility types
        fac_types = (Storage(name="FK Represent TestFacType P"),
                     Storage(name="FK Represent TestFacType Q"),
                     Storage(name="FK Represent TestFacType R"))
        ttable = s3db.org_facility_type
        for i in range(len(fac_types)):
            fac_type = fac_types[i]
            fac_type_id = ttable.insert(**fac_type)
            fac_type["id"] = fac_type_id
        self.fac_types = Storage([(t.id, t) for t in fac_types])

        # Create organisation
        org = Storage(name="FK Represent TestOrg B")
        otable = s3db.org_organisation
        org_id = otable.insert(**org)
        org["id"] = org_id
        s3db.update_super(otable, org)
        self.org = org

        # Create test records
        facs = (Storage(organisation_id=org.id,
                        facility_type_id=[fac_types[0].id, fac_types[1].id],
                        location_id=locations[0].id),
                Storage(organisation_id=org.id,
                        facility_type_id=[fac_types[1].id, fac_types[2].id],
                        location_id=locations[1].id))
        for i in range(len(facs)):
            fac = facs[i]
            fac_id = db[tablename].insert(**fac)
            fac["id"] = fac_id
        self.facs = facs

    # -------------------------------------------------------------------------
    def testRepresentReferenceSingleNoLinkto(self):
        """
            Test Representation of reference, single value,
            without linkto
        """

        s3db = current.s3db

        resource = s3db.resource(self.tablename,
                                 id=[fac.id for fac in self.facs])
        table = resource.table

        # Attach lazy renderers
        org_id_renderer = S3Represent(lookup="org_organisation")
        table.organisation_id.represent = org_id_renderer

        fac_type_renderer = S3Represent(lookup="org_facility_type",
                                        multiple=True)
        table.facility_type_id.represent = fac_type_renderer

        loc_id_renderer = S3Represent(lookup="gis_location",
                                      linkto=URL(c="gis", f="location", args=["[id]"]))
        table.location_id.represent = loc_id_renderer

        # Export with IDs
        current.xml.show_ids = True
        tree = S3ResourceTree(resource).build(dereference=False)
        root = tree.getroot()

        locations = self.locations
        fac_types = self.fac_types
        org = self.org

        # Check correct representation in exports
        for fac in self.facs:

            # Find the element
            elem = root.findall("resource[@id='%s']" % fac.id)
            elem = elem[0] if len(elem) else None
            self.assertNotEqual(elem, None)

            find = lambda name: elem.findall("reference[@field='%s']" % name)

            organisation_id = find("organisation_id")
            organisation_id = organisation_id[0] \
                              if len(organisation_id) else None
            self.assertNotEqual(organisation_id, None)
            self.assertEqual(organisation_id.text, org.name)

            location_id = find("location_id")
            location_id = location_id[0] \
                          if len(location_id) else None
            self.assertNotEqual(location_id, None)
            location = locations[fac.location_id]
            self.assertEqual(location_id.text, location.name)

            facility_type_id = find("facility_type_id")
            facility_type_id = facility_type_id[0] \
                               if len(facility_type_id) else None
            self.assertNotEqual(facility_type_id, None)

            ftypes = ", ".join([fac_types[i].name
                                for i in fac.facility_type_id])
            self.assertEqual(facility_type_id.text, ftypes)

        # Check that only 1 query per renderer was needed for the export
        self.assertEqual(org_id_renderer.queries, 1)
        self.assertEqual(fac_type_renderer.queries, 1)
        self.assertEqual(loc_id_renderer.queries, 1)

    # -------------------------------------------------------------------------
    def tearDown(self):

        db = current.db
        db.rollback()
        current.auth.override = False
        try:
            db[self.tablename].drop()
        except:
            pass

# =============================================================================
class S3ReusableFieldTests(unittest.TestCase):
    """ Test multiple named widgets in reusable fields """

    # -------------------------------------------------------------------------
    def widget1(self):
        """ Dummy widget """
        pass

    def widget2(self):
        """ Dummy widget """
        pass

    def widget3(self):
        """ Dummy widget """
        pass

    # -------------------------------------------------------------------------
    def testWidgetOverrideWithoutDefault(self):
        """ Test setting the widget in the instance (no default) """

        rf = S3ReusableField("test", "integer")

        # Default None
        field = rf()
        self.assertEqual(field.widget, None)

        # Widget-parameter overrides default
        field = rf(widget=self.widget1)
        self.assertEqual(field.widget, self.widget1)

    # -------------------------------------------------------------------------
    def testWidgetOverrideWithDefault(self):
        """ Test overriding the default widget in the instance """

        rf = S3ReusableField("test", "integer",
                             widget=self.widget1)

        # Default widget
        field = rf()
        self.assertEqual(field.widget, self.widget1)

        # Widget-parameter overrides default
        field = rf(widget=self.widget2)
        self.assertEqual(field.widget, self.widget2)

    # -------------------------------------------------------------------------
    def testSingleWidget(self):
        """ Test using widget set with single widget """

        rf = S3ReusableField("test", "integer",
                             widgets=self.widget1)

        # Default
        field = rf()
        self.assertEqual(field.widget, self.widget1)

        # Deliberate default
        field = rf(widget="default")
        self.assertEqual(field.widget, self.widget1)

        # Override
        field = rf(widget=self.widget2)
        self.assertEqual(field.widget, self.widget2)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="alternative")

    # -------------------------------------------------------------------------
    def testMultipleWidgets(self):
        """ Test using widget set with multiple widgets """

        rf = S3ReusableField("test", "integer",
                             widgets={"default": self.widget1,
                                      "alternative": self.widget2,
                                      },
                             )

        # Using default from set
        field = rf()
        self.assertEqual(field.widget, self.widget1)

        # Deliberate default
        field = rf(widget="default")
        self.assertEqual(field.widget, self.widget1)

        # Other choice
        field = rf(widget="alternative")
        self.assertEqual(field.widget, self.widget2)

        # Override
        field = rf(widget=self.widget3)
        self.assertEqual(field.widget, self.widget3)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="other")

    # -------------------------------------------------------------------------
    def testMultipleWidgetsWithDefault(self):
        """ Test using widget set with multiple widgets and override default """

        rf = S3ReusableField("test", "integer",
                             widgets={"default": self.widget1,
                                      "alternative": self.widget2,
                                      },
                             widget=self.widget3,
                             )

        # "widget"-setting overrides "default"
        field = rf()
        self.assertEqual(field.widget, self.widget3)

        # "widget"-setting overrides "default"
        field = rf(widget="default")
        self.assertEqual(field.widget, self.widget3)

        # Other alternatives still available
        field = rf(widget="alternative")
        self.assertEqual(field.widget, self.widget2)

        # And can still override
        field = rf(widget=self.widget1)
        self.assertEqual(field.widget, self.widget1)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="other")

    # -------------------------------------------------------------------------
    def testFallbackWithDefault(self):
        """ Test fallback to default widget """

        rf = S3ReusableField("test", "integer",
                             widget=self.widget1,
                             widgets={"alternative": self.widget2},
                             )

        # Standard fallback
        field = rf()
        self.assertEqual(field.widget, self.widget1)

        # Deliberate default
        field = rf(widget="default")
        self.assertEqual(field.widget, self.widget1)

        # Alternative
        field = rf(widget="alternative")
        self.assertEqual(field.widget, self.widget2)

        # Override
        field = rf(widget=self.widget1)
        self.assertEqual(field.widget, self.widget1)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="other")

    # -------------------------------------------------------------------------
    def testExplicitNone(self):
        """ Test explicit None-widget in instance """

        rf = S3ReusableField("test", "integer",
                             widgets={"default": self.widget1,
                                      "alternative": self.widget2,
                                      },
                             widget=self.widget3,
                             )

        # Standard fallback
        field = rf(widget=None)
        self.assertEqual(field.widget, None)

    # -------------------------------------------------------------------------
    def testFallbackWithoutDefault(self):
        """ Test fallback to None """

        rf = S3ReusableField("test", "integer",
                             widgets={"alternative": self.widget2},
                             )

        # Standard fallback
        field = rf()
        self.assertEqual(field.widget, None)

        # Deliberate default
        field = rf(widget="default")
        self.assertEqual(field.widget, None)

        # Alternative
        field = rf(widget="alternative")
        self.assertEqual(field.widget, self.widget2)

        # Override
        field = rf(widget=self.widget1)
        self.assertEqual(field.widget, self.widget1)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="other")

    # -------------------------------------------------------------------------
    def testFallbackWithoutWidgets(self):
        """ Test fallback to None """

        rf = S3ReusableField("test", "integer")

        # Standard fallback
        field = rf()
        self.assertEqual(field.widget, None)

        # Deliberate default
        field = rf(widget="default")
        self.assertEqual(field.widget, None)

        # Alternative
        self.assertRaises(NameError, rf, widget="alternative")

        # Override
        field = rf(widget=self.widget1)
        self.assertEqual(field.widget, self.widget1)

        # Undefined widget
        self.assertRaises(NameError, rf, widget="other")

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3RepresentTests,
        S3ExtractLazyFKRepresentationTests,
        S3ExportLazyFKRepresentationTests,
        S3ReusableFieldTests,
    )

# END ========================================================================
