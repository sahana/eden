# -*- coding: utf-8 -*-
#
# Core Benchmarks
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/benchmark.py
#
# Note:
#
# These tests represent the performance of specific server-side core
# functions of Sahana Eden which are typically called millions of times
# during normal operation of the site.
#
# The results of these tests depend on many variables (e.g. hardware
# configuration, software stack etc.), thus, to compare the results
# in order to optimize code or detect newly introduced bottlenecks the
# tests must be run on always the same environment.
#
# When running these tests in order to optimize the environment, you can
# use these benchmarks as a rough guideline for what you can expect:
#
# S3Model.configure = 2.90979003906 µs
# S3Model.get_config = 2.2715420723 µs
# S3Model.table(non-table) = 2.13528013229 µs
# S3Model.get(non-table) = 2.0619969368 µs
# S3Model.__getattr__(non-table) = 4.12402009964 µs
# S3Model.__getitem__(non-table) = 4.24327015877 µs
# S3Model.table = 2.91769790649 µs
# S3Model.__getattr__ = 4.959856987 µs
# S3Model.__getitem__ = 5.19830703735 µs
# S3Resource.import_xml = 12.0009431839 ms (=83 rec/sec)
# S3Resource.export (incl. DB extraction) = 3.75156188011 ms (=266 rec/sec)
# S3Resource.export (w/o DB extraction) = 1.7192029953 ms (=581 rec/sec)
# S3Resource.__init__ = 2.65161395073 ms
# S3Resource.load = 5.55664610863 ms
#
# If you cannot achieve approximately these or even better results, then
# it is recommendable to put effort into the optimization of the environment
# in order to run Sahana Eden with acceptable performance. Typically you would
# try to deploy Eden in an enviroment that allows 2-10 times better performance
# than that.
#
# If you get FAIL messages, then the overall performance of Sahana Eden in
# your enviroment is likely to be completely unacceptable.
#
import sys
import timeit
import unittest

from unit_tests import run_suite

def info(msg):
    sys.stdout.write("%s\n" % msg)

# =============================================================================
#@unittest.skip("Comment or remove this line in modules/unit_tests/eden/benchmark.py to activate this test")
class S3PerformanceTests(unittest.TestCase):

    def testDBSelect(self):
        """ DAL query peak performance """

        db = current.db
        s3db = current.s3db

        info("")
        table = s3db.table("pr_person")
        x = lambda: [(row.first_name, row.last_name)
                     for row in db(table.id > 0).select(table.id,
                                                        table.first_name,
                                                        table.last_name,
                                                        limitby=(0, 50))]
        n = len(x())
        mlt = timeit.Timer(x).timeit(number = int(100/n))
        info("db.select = %s ms/record (=%s rec/sec)" % (mlt * 10.0, int(100/mlt)))

        x = lambda: [[(row.first_name, row.last_name)
                      for row in db(table.id < i).select(table.id,
                                                         table.first_name,
                                                         table.last_name)]
                     for i in range(n)]
        mlt = timeit.Timer(x).timeit(number = 10) * (100/n)
        info("db.select = %s ms/query (=%s q/sec)" % (mlt, int(1000/mlt)))

    def testS3ModelTable(self):

        s3db = current.s3db

        info("")
        table = s3db.table("pr_person")
        if table is not None:
            x = lambda: s3db.table("pr_person")
            mlt = timeit.Timer(x).timeit()
            info("S3Model.table = %s µs" % mlt)
            self.assertTrue(mlt<10)

            x = lambda: s3db.pr_person
            mlt = timeit.Timer(x).timeit()
            info("S3Model.__getattr__ = %s µs" % mlt)
            self.assertTrue(mlt<10)

            x = lambda: s3db["pr_person"]
            mlt = timeit.Timer(x).timeit()
            info("S3Model.__getitem__ = %s µs" % mlt)
            self.assertTrue(mlt<10)

    def testS3ModelName(self):

        s3db = current.s3db

        info("")
        func = s3db.get("pr_person_represent")
        if func is not None:
            x = lambda: s3db.table("pr_person_represent")
            mlt = timeit.Timer(x).timeit()
            info("S3Model.table(non-table) = %s µs" % mlt)
            self.assertTrue(mlt<10)

            x = lambda: s3db.get("pr_person_represent")
            mlt = timeit.Timer(x).timeit()
            info("S3Model.get(non-table) = %s µs" % mlt)
            self.assertTrue(mlt<10)

            x = lambda: s3db.pr_person_represent
            mlt = timeit.Timer(x).timeit()
            info("S3Model.__getattr__(non-table) = %s µs" % mlt)
            self.assertTrue(mlt<10)

            x = lambda: s3db["pr_person_represent"]
            mlt = timeit.Timer(x).timeit()
            info("S3Model.__getitem__(non-table) = %s µs" % mlt)
            self.assertTrue(mlt<10)

    def testS3ModelConfigure(self):

        s3db = current.s3db

        info("")
        configure = s3db.configure
        x = lambda: configure("pr_person", testconfig = "Test")
        mlt = timeit.Timer(x).timeit()
        info("S3Model.configure = %s µs" % mlt)
        self.assertTrue(mlt<10)

        get_config = s3db.get_config
        x = lambda: get_config("pr_person", "testconfig")
        mlt = timeit.Timer(x).timeit()
        info("S3Model.get_config = %s µs" % mlt)
        self.assertTrue(mlt<10)

    def testS3ResourceInit(self):

        info("")
        current.auth.override = True
        current.s3db.resource("pr_person")
        x = lambda: current.s3db.resource("pr_person")
        mlt = timeit.Timer(x).timeit(number=1000)
        info("S3Resource.__init__ = %s ms" % mlt)
        self.assertTrue(mlt<10)
        current.auth.override = False

    def testS3ResourceLoad(self):

        info("")
        current.auth.override = True
        resource = current.s3db.resource("pr_person")
        x = lambda: resource.load(limit=1)
        mlt = timeit.Timer(x).timeit(number=1000)
        info("S3Resource.load = %s ms" % mlt)
        self.assertTrue(mlt<10)
        current.auth.override = False

    def testS3ResourceImportExport(self):

        xmlstr = """
<s3xml>
  <resource name="org_organisation" tuid="Philippine Red Cross">
    <data field="name">Philippine Red Cross</data>
  </resource>
  <resource name="hrm_job_title" tuid="Team Leader">
    <data field="name">Team Leader</data>
    <reference field="organisation_id" resource="org_organisation" tuid="Philippine Red Cross"/>
  </resource>
  <resource name="pr_person">
    <data field="first_name">Chona</data>
    <data field="middle_name"/>
    <data field="last_name">Alinsub</data>
    <data field="initials"/>
    <data field="date_of_birth"/>
    <resource name="pr_person_details">
      <data field="father_name"/>
      <data field="mother_name"/>
      <data field="occupation"/>
      <data field="company"/>
      <data field="affiliations"/>
    </resource>
    <resource name="pr_contact">
      <data field="contact_method" value="SMS"/>
      <data field="value">9463778503</data>
    </resource>
    <resource name="pr_address">
      <reference field="location_id" resource="gis_location" tuid="Location L4: Rizal"/>
      <data field="type">1</data>
      <data field="building_name"/>
      <data field="address"/>
      <data field="postcode">6600</data>
      <data field="L0">Philippines</data>
      <data field="L1">Visayas</data>
      <data field="L2">Southern Leyte</data>
      <data field="L3">Maasin City</data>
      <data field="L4">Rizal</data>
    </resource>
    <resource name="hrm_human_resource">
      <data field="type">2</data>
      <reference field="job_title_id" resource="hrm_job_title" tuid="Team Leader"/>
      <reference field="organisation_id" resource="org_organisation" tuid="Philippine Red Cross"/>
    </resource>
  </resource>
  <resource name="gis_location" tuid="Location L1: Visayas">
    <reference field="parent" resource="gis_location" uuid="urn:iso:std:iso:3166:-1:code:PH"/>
    <data field="name">Visayas</data>
    <data field="level">L1</data>
  </resource>
  <resource name="gis_location" tuid="Location L2: Southern Leyte">
    <reference field="parent" resource="gis_location" tuid="Location L1: Visayas"/>
    <data field="name">Southern Leyte</data>
    <data field="level">L2</data>
  </resource>
  <resource name="gis_location" tuid="Location L3: Maasin City">
    <reference field="parent" resource="gis_location" tuid="Location L2: Southern Leyte"/>
    <data field="name">Maasin City</data>
    <data field="level">L3</data>
  </resource>
  <resource name="gis_location" tuid="Location L4: Rizal">
    <reference field="parent" resource="gis_location" tuid="Location L3: Maasin City"/>
    <data field="name">Rizal</data>
    <data field="level">L4</data>
  </resource>
</s3xml>"""

        from lxml import etree
        tree = etree.ElementTree(etree.fromstring(xmlstr))

        current.auth.override = True
        current.db.rollback()

        info("")
        resource = current.s3db.resource("org_organisation")
        x = lambda: resource.import_xml(tree)
        mlt = 0
        for i in range(100):
            mlt += timeit.Timer(x).timeit(number=1)
            current.db.rollback()
        mlt *= 10
        info("S3Resource.import_xml = %s ms (=%s rec/sec)" % (mlt, int(1000/mlt)))
        self.assertTrue(mlt<30)

        resource = current.s3db.resource("pr_person")
        from lxml import etree
        parent = etree.Element("test")
        rfields, dfields = resource.split_fields()
        x = lambda: resource._export_record(resource.table[1],
                                            rfields=rfields,
                                            dfields=dfields,
                                            parent=parent,
                                            export_map=Storage())
        mlt = timeit.Timer(x).timeit(number=1000)
        info("S3Resource.export (incl. DB extraction) = %s ms (=%s rec/sec)" % (mlt, int(1000/mlt)))
        self.assertTrue(mlt<10)

        resource = current.s3db.resource("pr_person")
        from lxml import etree
        parent = etree.Element("test")
        rfields, dfields = resource.split_fields()
        record = resource.table[1]
        x = lambda: resource._export_record(record,
                                            rfields=rfields,
                                            dfields=dfields,
                                            parent=parent,
                                            export_map=Storage())
        mlt = timeit.Timer(x).timeit(number=1000)
        info("S3Resource.export (w/o DB extraction) = %s ms (=%s rec/sec)" % (mlt, int(1000/mlt)))
        self.assertTrue(mlt<10)

        current.auth.override = False

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3PerformanceTests,
    )

# END ========================================================================
