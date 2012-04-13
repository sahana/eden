__all__ = ["dt_filter", "dt_row_cnt", "dt_data",]

# Selenium WebDriver
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
#from selenium.webdriver.common.keys import Keys

from gluon import current

from s3 import s3_debug

import time

# -----------------------------------------------------------------------------
def dt_filter(search_string=" ",
              forceClear = True,
              quiet = True):
    """ filter the dataTable """
    if forceClear:
        if not dt_filter(forceClear = False,
                         quiet = quiet):
            return False
    config = current.test_config
    browser = config.browser

    sleep_limit = 10
    elem = browser.find_element_by_css_selector('label > input[type="text"]')
    elem.clear()
    elem.send_keys(search_string)

    time.sleep(1) # give time for the list_processing element to appear
    waiting_elem = browser.find_element_by_id("list_processing")
    sleep_time = 0
    while (waiting_elem.value_of_css_property("visibility") == "visible"):
        time.sleep(1)
        sleep_time += 1
        if sleep_time > sleep_limit:
            if not quiet:
                s3_debug("DataTable filter didn't respond within %d seconds" % sleep_limit)
            return False
    return True

# -----------------------------------------------------------------------------
def dt_row_cnt(check = (),
              quiet = True):
    """ return the rows that are being displayed and the total rows in the dataTable """
    config = current.test_config
    browser = config.browser

    elem = browser.find_element_by_id("list_info")
    details = elem.text
    if not quiet:
        s3_debug(details)
    words = details.split()
    start = int(words[1])
    end = int(words[3])
    length = int(words[5])
    filtered = None
    if len(words) > 10:
        filtered = int(words[9])
    if check != ():
        if len(check ) == 3:
            expected = "Showing %d to %d of %d entries" % check
            actual = "Showing %d to %d of %d entries" % (start, end, length)
            assert (start, end, length) == check, "Expected result of '%s' doesn't equal '%s'" % (expected, actual)
        elif len(check) == 4:
            expected = "Showing %d to %d of %d entries (filtered from %d total entries)" % check
            if filtered:
                actual = "Showing %d to %d of %d entries (filtered from %d total entries)" % (start, end, length, filtered)
            else:
                actual = "Showing %d to %d of %d entries" % (start, end, length)
            assert (start, end, length, filtered) == check, "Expected result of '%s' doesn't equal '%s'" % (expected, actual)
    if len(words) > 10:
        return (start, end, length, filtered)
    else:
        return (start, end, length)

# -----------------------------------------------------------------------------
def dt_data():
    """ return the data in the displayed dataTable """
    config = current.test_config
    browser = config.browser

    cell = browser.find_element_by_id("table-container")
    text = cell.text
    parts = text.splitlines()
    records = []
    for row in parts:
        if row.startswith("Detail"):
            row = row[8:]
            records.append(row)
    return records
