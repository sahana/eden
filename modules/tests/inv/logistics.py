__all__ = ["inventory"]

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

from tests import *

# These tests assume that regression/inv-mngt has been added to prepop
# -----------------------------------------------------------------------------
def inventory():
    """ Tests for Inventory """

    config = current.test_config
    browser = config.browser

    # Login
    login()

    # Open Inv module
    url = "%s/inv/inv_item" % config.url
    url = "%s/inv/warehouse" % config.url
    browser.get(url)

    # Check that the inventory is correct.
    (start, end, length) = dt_row_cnt(check=(1,6,6), quiet=False)
    # look for the entries in Lospalos Warehouse
    warehouse = "Lospalos Warehouse"
    if not dt_filter(warehouse):
        assert 0, "DataTable not working correctly"

    (start, end, total, filtered) = dt_row_cnt(check=(1,1,1,6), quiet=False)
    if not dt_filter():
        assert 0, "DataTable not working correctly"
    (start, end, length) = dt_row_cnt(check=(1,6,6))
    
    records = dt_data()
    for line in records:
        s3_debug(line)
        

    assert 0, "Keep the browser window open"
