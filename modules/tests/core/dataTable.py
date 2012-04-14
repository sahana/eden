__all__ = ["dt_filter",
           "dt_row_cnt",
           "dt_data",
           "dt_data_item",
           "dt_find",
           "dt_links",
           "dt_action",
          ]

# @todo Their are performance issues need to profile and find out in which functions are the bottlenecks
 
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
def dt_data(row_list = None,
            add_header = False):
    """ return the data in the displayed dataTable """
    config = current.test_config
    browser = config.browser

    cell = browser.find_element_by_id("table-container")
    text = cell.text
    parts = text.splitlines()
    records = []
    cnt = 0
    lastrow = ""
    header = ""
    for row in parts:
        if row.startswith("Detail"):
            header = lastrow
            row = row[8:]
            if row_list == None or cnt in row_list:
                records.append(row)
            cnt += 1
        else:
            lastrow = row
    if add_header:
        return [header] + records
    return records

# -----------------------------------------------------------------------------
def dt_data_item(row = 1,
                 column = 1,
                 tableID = "list",
                ):
    """ Returns the data found in the cell of the dataTable """
    config = current.test_config
    browser = config.browser

    td =  ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, row, column)
    try:
        elem = browser.find_element_by_xpath(td)
        return elem.text
    except:
        return False

# -----------------------------------------------------------------------------
def dt_find(search = "",
            row = None,
            column = None,
            tableID = "list",
            first = False,
           ):
    """ Find the cells where search is found in the dataTable """
    # 'todo need to fix the searching on numbers
    config = current.test_config
    browser = config.browser

    # Calculate the rows that need to be navigated along to find the search string
    colList = []
    rowList = []
    if row == None:
        r = 1
        while True:
            tr =  ".//*[@id='%s']/tbody/tr[%s]" % (tableID, r)
            try:
                elem = browser.find_element_by_xpath(tr)
                rowList.append(r)
                r += 1
            except:
                break
    elif isinstance(row, int):
        rowList = [row]
    else:
        rowList = row
    # Calculate the columns that need to be navigated down to find the search string
    if column == None:
        c = 1
        while True:
            td = ".//*[@id='%s']/tbody/tr[1]/td[%s]" % (tableID, c)
            try:
                elem = browser.find_element_by_xpath(td)
                colList.append(c)
                c += 1
            except:
                break
    elif isinstance(column, int):
        colList = [column]
    else:
        colList = column
    s3_debug("rows %s, columns %s" % (rowList, colList))
    # Now try and find a match
    result = []
    for r in rowList:
        for c in colList:
            td = ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, r, c)
            try:
                elem = browser.find_element_by_xpath(td)
                s3_debug("got %s, needle %s" % (elem.text, search))
                if elem.text == search:
                    if first:
                        return (r, c)
                    else:
                        result.append((r, c))
            except:
                pass
    return result

        
# -----------------------------------------------------------------------------
def dt_links(row = 1,
             tableID = "list",
             quiet = True
            ):
    """ Returns a list of links in the given row of the dataTable """
    config = current.test_config
    browser = config.browser

    links = []
    # loop through each column
    column = 1
    while True:
        td =  ".//*[@id='%s']/tbody/tr[%s]/td[%s]" % (tableID, row, column)
        try:
            elem = browser.find_element_by_xpath(td)
        except:
            break
        # loop through looking for links in the cell
        cnt = 1
        while True:
            link = ".//*[@id='%s']/tbody/tr[%s]/td[%s]/a[%s]" % (tableID, row, column, cnt)
            try:
                elem = browser.find_element_by_xpath(link)
            except:
                break
            cnt += 1
            if not quiet:
                s3_debug("%2d) %s" % (column, elem.text))
            links.append([column,elem.text])
        column += 1
    return links

def dt_action(row = 1,
              action = "Open",
              column = 1,
              tableID = "list",
             ):
    """ click the action button in the dataTable """
    config = current.test_config
    browser = config.browser

    # What looks like a fairly fragile xpath, but it should work unless DataTable changes
    button = ".//*[@id='%s']/tbody/tr[%s]/td[%s]/a[contains(text(),'%s')]" % (tableID, row, column, action)
    try:
        elem = browser.find_element_by_xpath(button)
    except:
        return False
    elem.click()
    return True
