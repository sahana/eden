*** Settings ***
Documentation       Keywords for filter forms

*** Variables ***

*** Keywords ***
#Testsuite:hrm; Testcase:Finding Staff By Organization
Wait For Filter Result
    [Documentation]  Waits for the filter result to be returned from the Ajax call
    Sleep  3s  Wait for filter result

#Testsuite:hrm; Testcase:Finding Staff By Organization
Open Advanced Filter Options
    [Documentation]  Open the advanced filter options for datatable filter
    # @ToDo: check if button exists, check status via label_on/off attributes, check success
    Click Element  jquery=#datatable-filter-form a.filter-advanced:contains("More Options")

#Similar to Open Advanced Filter Options
Close Advanced Filter Options
    [Documentation]  Close the advanced filter options for datatable filter
    # @ToDo: check if button exists, check status via label_on/off attributes, check success
    Click Element  jquery=#datatable-filter-form a.filter-advanced:contains("Less Options")
