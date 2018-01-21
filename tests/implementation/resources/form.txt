*** Settings ***
Documentation       Keywords for manipulating forms

*** Variables ***

*** Keywords ***

#Testsuite:hrm; Testcase:Create Staff Member
Create A New Entry
    [Documentation]     Usage - Name Value :List of Name Value
    # ...     pairs (can take dropdowns and text fields as of now).
    # ...     eg: @{NV}  priority  High name  tester
    # ... Sub Url : List of strings which are concatenated to create
    # ...     the URL. eg: @{Sub Url}  project  task
    # ... Create both as list arguments but pass them as scalar
    # ...      arguments. eg: Create A New Entry  ${NV}  ${Sub Url}

    [Arguments]  ${Name Value}  ${Sub Url}
    ${url}  Catenate  SEPARATOR=  ${BASEURL}
    :FOR  ${substring}  IN  @{Sub Url}
    \  ${url}  Catenate  SEPARATOR=/  ${url}  ${substring}
    Go To  ${url}
    Click Element  show-add-btn
    :FOR  ${name}  ${value}  IN  @{Name Value}
    \  ${tag}  Get Element Attribute  ${name}@tagName
    \  Run Keyword If  '${tag}' == 'INPUT'  Input Text  ${name}  ${value}
    \  Run Keyword If   '${tag}' == 'SELECT'  Select From List  ${name}  ${value}
    Click Button  xpath=//input[@value="Save"]
