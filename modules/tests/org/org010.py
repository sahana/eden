# Manage user access levels on organisations
__all__ = ["org010"]

# Selenium WebDriver
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys
from gluon import current
from s3 import s3_debug
from tests import *

def org010():
    """
    1. Log in as admin
    2. Give test user org admin rights over Timor-Leste
    3. Give user margarida.martins@redcross.tl some access on Timor-Leste
    4. Log in as test user
    5. Revoke all access for margarida.martins@redcross.tl on Timor-Leste
    """

    as_admin()
    logout()

    as_orgadmin()
    logout()

def as_admin():
    """
    Run the tests as an administrator
    """
    config = current.test_config
    browser = config.browser
    driver = browser

    login(account='admin')
    make_user_orgadmin()
    open_organisation_roles()
    select_user()

    # Set some new access levels
    driver.find_element_by_id('role_volvol_reader').click()
    driver.find_element_by_id('role_projectproject_data_entry').click()
    driver.find_element_by_id('role_projectproject_data_entry').submit()

    # @todo: check the values of the matrix

def as_orgadmin():
    """
    Run the tests as an org admin
    """
    config = current.test_config
    browser = config.browser
    driver = browser

    login()
    open_organisation_roles(action="Details")
    select_user()

    # Reset those access levels back to None
    driver.find_element_by_id('role_volNone').click()
    driver.find_element_by_id('role_projectNone').click()
    driver.find_element_by_id('role_projectNone').submit()

    # @todo: check the values of the matrix

def make_user_orgadmin():
    config = current.test_config
    browser = config.browser
    driver = browser

    browser.get("%s/admin/user" % config.url)

    # Open the roles page for text@example.com user account
    dt_filter("test@example.com")
    dt_action(action="Roles")

    # Give org admin rights to Test User on Timor-Leste Red Cross Society
    Select(driver.find_element_by_name("group_id")).select_by_visible_text("Organisation Admin")
    Select(driver.find_element_by_name("pe_id")).select_by_visible_text("Timor-Leste Red Cross Society (Organization)")
    driver.find_element_by_id("submit_add_button").click()

def open_organisation_roles(action="Open"):
    config = current.test_config
    browser = config.browser
    driver = browser

    # Go to the organisation list
    browser.get("%s/org/organisation" % config.url)

    # Open the Timor-Leste organisation
    dt_filter("Timor-Leste")
    dt_action(action=action)

    # Go to the organisations' User Roles tab
    driver.find_element_by_link_text("User Roles").click()

def select_user():
    config = current.test_config
    browser = config.browser
    driver = browser

    # Select a user from the drop-down list
    Select(driver.find_element_by_name("user")).select_by_visible_text("test@example.com")
    driver.find_element_by_xpath("//input[@type='submit']").click()
