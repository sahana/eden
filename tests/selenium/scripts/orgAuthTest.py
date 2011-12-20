"""
    OrgAuth Test cases
"""
from sahanaTest import SahanaTest
import unittest, re

class OrgAuthTest(SahanaTest):
    """ 
        The _sortList variable is used to keep a list of all test methods
        that will be run by the test class.
        The test methods  will be run in the order given in this list.

        If this variable is not provided then only methods that have the prefix test_
        will be run and the order is not guaranteed 
    """
    _sortList = (
                    "_prepare",
                    "checkNormalPermissionsTab",
                    "checkAdminPermissionsTab",
                    "checkOrgAdminPermissionsTab",
                    "checkDelegation",
                    "_cleanup",
                )

    def _createDummyOrgs(self):
        sel=self.selenium
        OrgAuthTest.org_name = "dummy org"
        OrgAuthTest.other_org = "another org"
        
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        
        sel.open("org/organisation/create")
        self.action.fillForm("org_organisation_name", OrgAuthTest.org_name)
        self.action.saveForm("Save", "Organization added")
        
        sel.open("org/organisation/create")
        self.action.fillForm("org_organisation_name", OrgAuthTest.other_org)
        self.action.saveForm("Save", "Organization added")
        
    def _openOrg(self, org_name):
        sel=self.selenium
        
        # Open dummyorg
        sel.open("org/organisation")
        self.action.searchUnique(org_name)
        sel.click("link=%s" % OrgAuthTest.action_map[self._user])
        sel.wait_for_page_to_load("30000")
        
    def _deleteDummyOrgs(self):
        sel=self.selenium
        self.action.deleteObject("org/organisation", OrgAuthTest.org_name, "Organization")
        sel.wait_for_page_to_load("30000")
        self.action.deleteObject("org/organisation", OrgAuthTest.another_org, "Organization")
        sel.wait_for_page_to_load("30000")
        
    def _prepare(self):
        """
            prepare dummy env for test
        """
        OrgAuthTest.action_map = {
                "adminuser@example.com":"Open", 
                "normaluser@example.com":"Details" }
        self._createDummyOrgs()
        
    def _cleanup(self):
        """
            cleanup dummy env
        """
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        self._deleteDummyOrgs()
    
    def checkNormalPermissionsTab(self):
        """
            1. as normal user
            2. Jump to dummy org's details
            3. look for absence of permissions tab
        """
        sel=self.selenium
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password)
        
        self._openOrg(OrgAuthTest.org_name)
        self.assertTrue(not self.action.checkTab("Permissions"))

    def checkAdminPermissionsTab(self):
        """
            1. as admin,
            2. check for permissions tab's presence under dummy org's details
        """
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        self._openOrg(OrgAuthTest.org_name)
        self.assertTrue(self.action.checkTab("Permissions"))
        
    def checkOrgAdminPermissionsTab(self):
        """
            1. as admin,
            2. assign a normal user as orgadmin of dummy org
            3. Log in as Normal user
            4. check for permissions tab presence under dummy org's details
        """
        sel=self.selenium
        self._openOrg(OrgAuthTest.org_name)
        self.action.clickTab("Permissions")
        # OrgAdmin role
        sel.click("//table[@id='list']/tbody/tr[7]/td/a")
        sel.wait_for_page_to_load("30000")
        user_search_element = "//div[5]/div/div/div[2]/div[3]/form/table/tbody/tr[8]/td/div/div[2]/div/input"
        sel.type_keys(user_search_element, "normal")
        sel.click("link=Add all")
        self.action.saveForm("Save", "Permission updated")
        
        # check for permissions tab as normal user
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password)
        self._openOrg(OrgAuthTest.org_name)
        self.assertTrue(self.action.checkTab("Permissions"))
    
    def checkDelegation(self):
        """
            1. Delegate a permission to dummy org
            2. verify in list view
        """
        sel=self.selenium
        # we're orgadmin already in sequence
        self._openOrg(OrgAuthTest.org_name)
        self.action.clickTab("Permissions")
        # OrgAdmin role
        orgadmin_role = "//table[@id='list']/tbody/tr[7]/td/a"
        sel.click(orgadmin_role)
        sel.wait_for_page_to_load("30000")
        
        org_search_element="//div[5]/div/div/div[2]/div[3]/form/table/tbody/tr[11]/td/div/div[2]/div/input"
        add_all_button="//tr[@id='auth_role_set_orgs_delegated__row']/td/div/div[2]/div/a"
        orgadmin_delegation="//div[5]/div/div/div[2]/div[3]/div[2]/div[5]/table/tbody/tr[7]/td[4]"
        
        sel.type_keys(org_search_element, "another org")
        sel.click(add_all_button)
        self.action.saveForm("Save", "Permission updated")
        self.assertTrue(sel.get_text(orgadmin_delegation) == OrgAuthTest.other_org)
        
if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
