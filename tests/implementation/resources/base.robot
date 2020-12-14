*** Settings ***
Documentation       Global keywords for Eden tests

*** Variables ***
${CONFIRMATION}     jquery:div.alert-success
${ERROR}            jquery:div.alert-error
${ABORTED EARLY}    Test Aborted, awaiting for code to be completed

*** Keywords ***
#Testsuite: SSF; Test: Create a project
Should Show Confirmation
    [Documentation]  Checks for the confirmation element and the message inside it (if given
    ...              as an argument) on the page and fails if it is not present.
    [Arguments]  @{message}
    Wait Until Page Contains Element  ${CONFIRMATION}  2s  Confirmation message not shown
    ${msg len} =  Get Length  ${message}
    Run Keyword if  ${msg len} >= 1  Element Should Contain  ${CONFIRMATION}  @{message}[0]

Should Show Error
    [Documentation]  Fails if no error message is visible in the page
    [Arguments]  @{message}
    Wait Until Page Contains Element  ${ERROR}  2s  Error message not shown
    ${msg len} =  Get Length  ${message}
    Run Keyword if  ${msg len} >= 1  Element Should Contain  ${ERROR}  @{message}[0]

Code Incomplete Abort Test
    [Documentation]  This will run a keyword which is expected to fail
    ...              but fail with a helpful message
    [Arguments]  ${condition}  ${error}  ${keyword}  @{args}
    ${error}=  Run Keyword And Expect Error  ${error}*  ${keyword}  @{args}
    Run Keyword If  ${condition}  Fail  ${ABORTED EARLY}  ELSE  Fail  ${error}

#Testsuite: SSF; Used in init
Run On Templates
    [Documentation]  Run if the current template is in the argument
    ...              USAGE: To apply it at a suite level, add it to start testing.
    ...              To apply it at at a test level, add it at begining of the test
    [Arguments]  @{Template List}
    Should Contain  ${Template List}  ${TEMPLATE}  The test does not run on the current template

Do Not Run on Templates
    [Documentation]  Do not run if the current template is in the argument
    ...              USAGE : Similar to Run on Templates
    [Arguments]  @{Template List}
    Should Not Contain  ${Template List}  ${TEMPLATE}  The test does not run on the current template

#Resources:main.txt;
Catch Error If Available Else Take Screenshot
    [Documentation]  Run on failure mechanism of EdenTest
    Run Keyword And Ignore Error  Handle Alert  DISMISS  1
    ${output}=  Check For Ticket And Catch Exception
    ${ss}=  Run Keyword If  ${output}==0  Capture Page Screenshot
    Run Keyword If  ${output}==0  Log  Screenshot: ${ss}  ERROR

#Resources:base.txt; keyword:Catch Error If Available Else Take Screenshot
Check for ticket and catch exception
    [Documentation]  Looks for tickets and if found, returns the traceback
    ...  In case optional argument Failed URL is given, it returns
    ...  the error generated otherwise it returns the 1/0
    [Arguments]  @{Failed URL}
    ${ticket}=  Run Keyword and Return Status  Page Should Contain  Ticket issued:
    ${serror}=  Run Keyword and Return Status  Page Should Contain  INTERNAL SERVER ERROR
    # If no error found, return
    Run Keyword Unless  ${ticket} or ${serror}  Return From Keyword  ${0}

    # Get the ticket ID and construct a URL for the internal ticket viewer
    ${Ticket URL}=  Get Element Attribute  xpath=//a[contains(@href,"/ticket/")]  href
    ${Ticket ID}=  Fetch From Right  ${Ticket URL}  /
    ${Ticket Link}=  Catenate  SEPARATOR=  ${BASEURL}  /admin/ticket/  ${APPNAME}  /  ${Ticket ID}

    # Login as ADMIN
    Logout From Eden
    Login To Eden  ${ADMIN EMAIL}  ${ADMIN PASSWORD}
    Go To  ${Ticket Link}

    # Fetch the traceback, then log out
    ${Traceback}=  Get Table Cell  xpath=//pre[contains(text(), "Traceback")]/ancestor::table[1]  1  2
    ${Ticket URL}=  Get Location
    Logout From Eden

    # Generate log entry
    @{With Failed URL}=  Set Variable  Failed URL: ${Failed URL}\n Ticket URL: ${Ticket URL} \n
    ...  Traceback:\n ${Traceback} \n

    @{Without Failed URL}=  Set Variable  Ticket URL: ${Ticket URL} \n
    ...  Traceback: \n ${Traceback} \n----\n

    # Log it
    ${passed}=  Run Keyword and Return Status  Should Not Be Empty  ${Failed URL}
    Run Keyword If  ${passed}  Log  ${With Failed URL}[0] ${With Failed URL}[1]  ERROR
    Run Keyword Unless  ${passed}  Log  ${Without Failed URL}[0] ${Without Failed URL}[1]  ERROR

    # Return errors if the Failed URL is given
    Return From Keyword if  ${passed}  @{With Failed URL}

    [Return]  ${1}

#Resources: base.txt; keyword: Check for ticket and catch exception
Login To Admin Interface If Not Logged In
    [Documentation]  Login to the admin interface to access the ticket
    ${passed}=  Run Keyword and Return Status  Page Should Contain  Administrator Password:
    Run Keyword Unless  ${passed}  Return From Keyword
    Input Text  password  ${WEB2PY PASSWD}
    Click Button  Login

Go To URL If Not Already There
    [Arguments]  ${URL}
    [Documentation]  Go to the URL if that is not the current page
    ${status}  ${value}  Run Keyword And Ignore Error  Location Should Be  ${URL}
    Run keyword If  '${status}'=='FAIL'  Go To  ${URL}

Open Page
    [Arguments]  ${URL}
    [Documentation]  Go to the URL, confirming any pending alerts
    Go To  ${URL}
    Register Keyword To Run On Failure  NOTHING
    Run Keyword And Ignore Error  Alert Should Not Be Present
    Register Keyword To Run On Failure  Catch Error If Available Else Take Screenshot
