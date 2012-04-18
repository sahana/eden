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
    
    links = dt_links(quiet=False)

    records = dt_data()
    warehouse_found = False
    tried = []
    for cnt, line in enumerate(records):
        if warehouse in line:
            tried.append(cnt)
            if dt_action(cnt+1,"Details"):
                warehouse_found = True
                break
    if warehouse_found == False:
        assert 0, "Unable to locate warehouse %s, tried to click rows %s" % (warehouse, tried)

    # Having opened the Lospalos warehouse
    # After a prepop the warehouse should have:
    #    4200 plastic sheets from Australia RC
    #    2000 plastic sheets from Acme 
    match = dt_find("Plastic Sheets")
    if match:
        found = False
        for cell in match:
            if dt_find("4200", row=cell[0], column=5, first=True):
               found = True
        assert found, "Unable to find 4200 Plastic Sheets"
    else:
        assert 0, "Unable to find any Plastic Sheets"
    
    assert 0, "Keep the browser window open"
