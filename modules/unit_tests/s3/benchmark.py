# -*- coding: utf-8 -*-
#
# Core Method Performance Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/benchmark.py
#
import unittest
import timeit

# =============================================================================
@unittest.skip("Comment or remove this line in modules/unit_tests/eden/benchmark.py to activate this test")
class S3PerformanceTests(unittest.TestCase):

    def testS3ModelTable(self):

        s3db = current.s3db

        print ""
        table = s3db.table("pr_person")
        if table is not None:
            x = lambda: s3db.table("pr_person")
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.table = %s ns" % mlt

            x = lambda: s3db.pr_person
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.__getattr__ = %s ns" % mlt

            x = lambda: s3db["pr_person"]
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.__getitem__ = %s ns" % mlt

    def testS3ModelName(self):

        s3db = current.s3db

        print ""
        func = s3db.get("pr_person_represent")
        if func is not None:
            x = lambda: s3db.table("pr_person_represent")
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.table(non-table) = %s ns" % mlt

            x = lambda: s3db.get("pr_person_represent")
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.get(non-table) = %s ns" % mlt

            x = lambda: s3db.pr_person_represent
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.__getattr__(non-table) = %s ns" % mlt

            x = lambda: s3db["pr_person_represent"]
            mlt = timeit.Timer(x).timeit()
            self.assertTrue(mlt<10)
            print "S3Model.__getitem__(non-table) = %s ns" % mlt

    def testS3ModelConfigure(self):

        s3db = current.s3db

        print ""
        configure = s3db.configure
        x = lambda: configure("pr_person", testconfig = "Test")
        mlt = timeit.Timer(x).timeit()
        self.assertTrue(mlt<10)
        print "S3Model.configure = %s ns" % mlt

        get_config = s3db.get_config
        x = lambda: get_config("pr_person", "testconfig")
        mlt = timeit.Timer(x).timeit()
        self.assertTrue(mlt<10)
        print "S3Model.get_config = %s ns" % mlt

    def testS3ResourceInit(self):

        print ""
        auth.override = True
        current.s3db.resource("pr_person")
        x = lambda: current.s3db.resource("pr_person")
        mlt = timeit.Timer(x).timeit(number=1000)
        self.assertTrue(mlt<10)
        print "S3Resource.__init__ = %s ms" % mlt
        auth.override = False

    def testS3ResourceLoad(self):

        print ""
        auth.override = True
        resource = current.s3db.resource("pr_person")
        x = lambda: resource.load(limit=1)
        mlt = timeit.Timer(x).timeit(number=1000)
        self.assertTrue(mlt<10)
        print "S3Resource.load = %s ms" % mlt
        auth.override = False

    def testS3ResourceExportRecord(self):

        print ""
        auth.override = True
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
        self.assertTrue(mlt<10)
        print "S3Resource._export_record = %s ms" % mlt
        auth.override = False

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        S3PerformanceTests,
    )

# END ========================================================================
