import wsgi_intercept.webtest_intercept
from applications.sahana.modules.s3.s3test import WSGI_Test

class CR_Test(WSGI_Test):
    """
        Extended version of WSGI_Test for Shelter Registry.
        Designed to be run from Web2Py shell
        Copy to modules folder & run as:
            from applications.sahana.modules.test_cr import *
            test_cr(db)
        NB This doesn't yet work: NameError: global name 'create_fn' is not defined
    """
    
    module = "cr"

    def __init__(self, db):
        WSGI_Test.__init__(self, db)
        return
        
    def setUp(self,db):
        """
            Populate Shelter Registry with Test Data to make each test case separable
            Intercept WSGI calls to do in-process testing
        """
        # Not working :/
        #db = self._globals()
        #self.setUpShelter(db)
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT, create_fn)
        return

    def runTest(self,db):
        """ Unit Test all functions within Shelter Registry """
        self.runTestLogin()
        self.runTestShelter()
        return
    
    def runTestLogin(self):
        if "200 OK" in test.getPage("/sahana/%s/login" % module):
            test.assertHeader("Content-Type", "text/html")
            test.assertInBody("Login")
        return

    def runTestShelter(self):
        resource = "shelter"
        if "200 OK" in test.getPage("/sahana/%s/%s" % (module, resource)):
            test.assertHeader("Content-Type", "text/html")
            test.assertInBody("List Shelters")
        # Need to login
        #if "200 OK" in test.getPage("/sahana/%s/%s/create" % (module, resource)):
        #    test.assertHeader("Content-Type", "text/html")
        #    test.assertInBody("Add Shelter")
        if "200 OK" in test.getPage("/sahana/%s/%s?format=json" % (module, resource)):
            test.assertHeader("Content-Type", "text/html")
            test.assertInBody("[")
        if "200 OK" in test.getPage("/sahana/%s/%s?format=csv" % (module, resource)):
            test.assertHeader("Content-Type", "text/csv")
        return

    def setUpShelter(self, db):
        """ Create test Data for Shelter Registry """
        resource = "shelter"
        table = module + "_" + resource
        if not len(db().select(db[table].ALL)):
            db[table].insert(
                name = "Test Shelter",
                description = "Just a test",
                location_id = 1,
                person_id = 1,
                address = "52 Test Street",
                capacity = 100,
                #dwellings=10,
                #persons_per_dwelling=10,
                #area="1 sq km"
            )
        return

def test_cr(db):
    test = CR_Test(db)
    test.setUp(db)
    test.runTest(db)
    return
            
if __name__ == "__main__":
    test_cr(db)
