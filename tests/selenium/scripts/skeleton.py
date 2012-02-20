import sys
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Do we have any command-line arguments?
args = sys.argv
if args[1:]:
    # The 1st argument is taken to be the application name:
    application = args[1]
else:
    application = "eden"

# Get local session of firefox
browser = webdriver.Firefox()

# Load homepage
browser.get("http://localhost:8000/%s" % application)
assert "Sahana" in browser.title

# Register a user
elem = browser.find_element_by_id("auth_user_first_name")
elem.send_keys("Test")
elem = browser.find_element_by_id("auth_user_last_name")
elem.send_keys("User")
elem = browser.find_element_by_id("auth_user_email")
elem.send_keys("test@example.com")
elem = browser.find_element_by_id("auth_user_password")
elem.send_keys("eden")
elem = browser.find_element_by_id("auth_user_password_two")
elem.send_keys("eden")
elem = browser.find_element_by_xpath("//input[contains(@value,'Register')]")
elem.click()

# Let the page load
time.sleep(5.0)

# Check the result
try:
    browser.find_element_by_xpath("//div[@class='confirmation']")
except NoSuchElementException:
    assert 0, "Login unsuccesful"
else:
    print "Success"
browser.close()
