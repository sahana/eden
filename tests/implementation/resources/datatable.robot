*** Settings ***
Documentation       Keywords for datatables

*** Variables ***
${DataTableID}      datatable

*** Keywords ***

#Resources: datatable.txt; keyword: Should Give X Results
Get DataTable Row Count
    [Documentation]  Finds the total number of records in the datatable, and returns the value
    ${count}=  Execute JavaScript  return $('#datatable').dataTable().fnSettings()._iRecordsTotal;
    [Return]  ${count}

#Testsuite:hrm; Testcase:Finding Staff By Organization
Should Give X Results
    [Arguments]  ${number}
    # Convert to int if passed as string
    ${expected}=  Set Variable  ${${number}}
    [Documentation]  Fails if the total number of records in the datatable is not _number_
    ${count}=  Get DataTable Row Count
    Should Be Equal  ${count}  ${expected}  msg=Should have found ${expected} results but found ${count}  values=${false}

#Testsuite:orgl Testcase:Update Organisation
DataTable Should Contain
    [Arguments]  ${text}
    [Documentation]  Fails if the datatable does not contain _text_
    Table Should Contain  ${DataTableID}  ${text}

#Testsuite:orgl Testcase:Update Organisation
Click Edit In Row
    [Arguments]  ${index}
    [Documentation]  Clicks the Edit-button in datatable row _index_ (_index_ 1
    ...              is the first row). Only visible Edit-buttons can be clicked.
    Click Link  xpath=//table[@id='${DataTableID}']//td[contains(@class, 'actions')][${index}]//a[contains(@class, 'edit')]

#Testsuite:hrm; Testcase:Finding Staff By Organization
DataTable Row Should Contain
    [Arguments]  ${index}  ${label}  ${text}
    [Documentation]  Fails if row _index_ in the datatable does not contain _text_
    ...              in the column with _label_
    # Convert to int if passed as string
    ${index}=  Set Variable  ${${index}}
    ${column}=  Get DataTable Column By Label  ${label}
    Table Cell Should Contain  ${DataTableID}  ${index + 1}  ${column}  ${text}

#Resource: datatable.txt; Keyword:DataTable Row Should Contain
Get DataTable Column By Label
    [Arguments]  ${label}
    ${column}=  Execute JavaScript  return $('#${DataTableID} th').filter(function(){
                ...                 return $(this).text() === '${label}';}).index()+1;
    Should Be True  ${column} > ${0}  Column not found in datatable: "${label}"
    [Return]  ${column}

DataTable Search
    [Arguments]  ${text}
    Execute JavaScript  $('#${DataTableID}').dataTable().fnFilter( '${text}' );
