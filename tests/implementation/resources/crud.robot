*** Settings ***
Documentation       Keywords for CRUD

*** Variables ***
${SubmitButton}     jquery:#submit_record__row input.btn[type='submit']

*** Keywords ***
#TestSuite: org; Test case:Create Organization
Submit CRUD Form
    [Documentation]  Clicks the submit button in a CRUD form
    Click Button  ${SubmitButton}
    Wait Until Page Does Not Contain Element  ${SubmitButton}  3s  Failed to submit form

#Testsuite: org; Testcase: Create organisation without name
Field Should Have Error
    [Arguments]  ${elementID}
    [Documentation]  Verifies that the form field with _element ID_
    ...              has a validation error message attached.
    ${count}=  Execute JavaScript  return $('#${elementID}').parent().find('div.error').length;
    Should Be Equal  ${count}  ${1}  msg=No validation error shown for ${elementID}

#Testsuite: org; Testcase: Create office
Select Option
    [Arguments]  ${elementID}  ${label}
    [Documentation]  Selects the first option from _elementID_ that contains _label_
    ${index}=  Execute JavaScript  return $('#${elementID} option:contains("${label}")').first().index();
    Should Be True  0 <= ${index}  msg=Option ${label} not found in ${elementID}
    # Odd but true: expects a string as index:
    Select From List By Index  ${elementID}  ${index.__str__()}
