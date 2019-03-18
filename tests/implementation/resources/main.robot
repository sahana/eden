*** Settings ***
Documentation     Main resource file for EdenTests
Resource  auth.robot
Resource  base.robot
Resource  crud.robot
Resource  filter.robot
Resource  datatable.robot
Resource  widgets.robot
Resource  form.robot
Library  SeleniumLibrary  run_on_failure=Catch Error If Available Else Take Screenshot
Library  Collections
Library  String
Variables  ../../execution/settings/config.py
Library  ../../execution/libs/edentest_robot.py  ${SERVER}  ${APPNAME}  ${ADMIN EMAIL}  ${ADMIN PASSWORD}
Library  ../../execution/libs/edentest_database_local.py

*** Variables ***
${BASEURL}  ${PROTO}://${SERVER}/${APPNAME}
${HOMEPAGE}  ${BASEURL}/default/index

*** Keywords ***
Start Browser With Proxy
    ${proxy}=  Evaluate  sys.modules['selenium.webdriver'].Proxy()  sys, selenium.webdriver
    ${proxy.http_proxy}=  Set Variable  ${HTTP_PROXY}
    ${proxy.no_proxy}=  Set Variable  ${NO_PROXY}
    Create Webdriver  ${BROWSER}  proxy=${proxy}

Start Browser
    Create Webdriver  ${BROWSER}

Start Testing
    [Documentation]  Starts the test, sets the template global variable
    ${deployment settings} =  Get Deployment Settings  template
    ${TEMPLATE}=  Get From Dictionary  ${deployment settings}  template
    Set Global Variable  ${TEMPLATE}
    Run Keyword If  "${HTTP_PROXY}" != "" and "${BROWSER}" == "Firefox"  Start Browser With Proxy
    ...  ELSE  Start Browser
    Set Selenium Speed  ${DELAY}

End Testing
    [Documentation]  Ends the test
    Logout From Eden
    Close Browser
