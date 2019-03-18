*** Settings ***
Documentation     Run using "python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest_runner.py -A survey"
...               This is to test the creation and modification of the templates
...               within the survey module.
...               **Basic workflow**:
...               1 Create a new template
...               2 Add sections to the template
...               3 Add Questions to each section
...               4 Add Grid questions (these are related questions which will presented in a grid)
...               5 Add possible options that can be selected for option type questions
...               6 Delete a template
...               **Additional workflow**:
...               1 Select an existing section
...               2 Move the section order
...               3 Move the question order
...               4 Move a question from one section to another
...               5 Delete a question
...               6 Rename a section
...               7 Delete a section

Resource  ../../resources/main.robot

Suite Setup  Survey Start


*** Variables ***
${TEMPLATE URL}  ${BASEURL}/survey/template
${TEMPLATE ID}  1
${TEMPLATE COUNT}
${QUESTION COUNT}
${Stop On First Error}  True  # Change to False to see what the error would be


*** Keywords ***
Survey Start
    ${count}=  Count Entries Of Table  survey_template
    Set Suite Variable  ${TEMPLATE COUNT}  ${count}
    ${count}=  Count Entries Of Table  survey_question
    Set Suite Variable  ${QUESTION COUNT}  ${count}

Get New Template ID
    [Documentation]  Set the id of the Survey Template just created
    ${query}=  Set Variable  Select id From survey_template Where deleted != 'True' Order By id DESC
    ${output}=  Execute Sql String  ${query}
    ${row}=  Get From List  ${output}  0
    ${id}=  Get From Dictionary  ${row}  id
    Set Suite Variable  ${TEMPLATE ID}  ${id}

Get Section Count
    [Documentation]  Return the number of sections in the current Survey Template
    ${query}=  Set Variable  select count(*) from survey_section where survey_section.template_id ='${TEMPLATE ID}';
    ${output}=  Execute Sql String  ${query}
    ${row}=  Get From List  ${output}  0
    ${count}=  Get From Dictionary  ${row}  count(*)
    [Return]  ${count}

Get Question Count In Section
    [Arguments]  ${section}
    [Documentation]  Return the number of sections in the current Section
    ${query}=  Set Variable  select count(*) from survey_section, survey_question_list where survey_section.template_id ='${TEMPLATE ID}' and survey_section.id = section_id and name = '${section}';
    ${output}=  Execute Sql String  ${query}
    ${row}=  Get From List  ${output}  0
    ${count}=  Get From Dictionary  ${row}  count(*)
    [Return]  ${count}

Create Section For Template
    [Arguments]  ${name}
    [Documentation]  Create a section for the Survey Template just created
    Click Link  Add Section
    Input Text  survey_section_name  ${name}
    # This will be an AJAX call can Submit CRUD Form be used?
    Click Link  Save

Select Template Section
    [Arguments]  ${name}
    [Documentation]  Select existing section for the Survey Template
    Click Link  ${name}

Move Section Up
    [Arguments]  ${name}
    [Documentation]  Move the selected section before the previous section
    ${move_up}=  Set Variable  ${name}_up
    Click Link  ${move_up}

Move Section Down
    [Arguments]  ${name}
    [Documentation]  Move the selected section after the next section
    ${move_down}=  Set Variable  ${name}_down
    Click Link  ${move_down}

Create Question For Active Section
    [Arguments]  ${name}  ${type}  ${code}
    [Documentation]  Create a section for the Survey Template just created
    Click Link  Add Question
    Select Radio Button  ${type}
    Wait Until Page Contains Element  survey_question_name
    Input Text  survey_question_name  ${name}
    Input Text  survey_question_code  ${code}

Add Grid Question Dimensions
    [Arguments]  ${col-cnt}  ${row-cnt}
    [Documentation]  Add the the dimension for the grid question
    Input Text  survey_question_metadata_col_cnt  ${col-cnt}
    Input Text  survey_question_metadata_row_cnt  ${row-cnt}

Add Grid Question Row Headings
    [Arguments]  @{headings}
    [Documentation]  Add the headings for each row
    ${cnt}=  Set Variable  0
    :FOR  ${heading}  IN  @{headings}
    \  ${cnt}=  Evaluate  ${cnt} + 1
    \  ${html_id}=  Set Variable  survey_question_metadata_row_heading_${cnt}
    \  Input Text ${html_id}  ${heading}

Add Grid Question Column Headings
    [Arguments]  @{headings}
    [Documentation]  Add the headings for each column
    ${cnt}=  Set Variable  0
    :FOR  ${heading}  IN  @{headings}
    \  ${cnt}=  Evaluate  ${cnt} + 1
    \  ${html_id}=  Set Variable  survey_question_metadata_col_heading_${cnt}
    \  Input Text ${html_id}  ${heading}

Add Grid Question Types
    [Arguments]  @{types}
    [Documentation]  Assigns the type to each question in the grid
    ${cnt}=  Set Variable  0
    :FOR  ${type}  IN  @{types}
    \  ${cnt}=  Evaluate  ${cnt} + 1
    \  ${html_id}=  Set Variable  survey_question_metadata_cell_type_${cnt}
    \  Input Text ${html_id}  ${type}

Add Question Options
    [Arguments]  @{options}
    [Documentation]  Assigns the possible options for the question
    ${cnt}=  Set Variable  0
    :FOR  ${option}  IN  @{options}
    \  ${cnt}=  Evaluate  ${cnt} + 1
    \  ${html_id}=  Set Variable  survey_question_metadata_option_${cnt}
    \  Input Text ${html_id}  ${option}
    \  Click Link  survey_question_metadata_add_another_option

Get Question Position
    [Arguments]  ${name}
    [Documentation]  Returns the position of the question for this template
    ${query}=  Set Variable  select posn from survey_question_list, survey_question where template_id ='${TEMPLATE ID}' and code = '${name}' and survey_question.id = survey_question_list.question_id;
    ${output}=  Execute Sql String  ${query}
    ${row}=  Get From List  ${output}  0
    ${posn}=  Get From Dictionary  ${row}  posn
    [Return]  ${posn}

Get Question Section
    [Arguments]  ${name}
    [Documentation]  Returns the name of the section for this question for this template
    ${query}=  Set Variable  select survey_section.name from survey_question_list, survey_question, survey_section where survey_question_list.template_id ='${TEMPLATE ID}' and code = '${name}' and survey_question.id = survey_question_list.question_id and section_id = survey_section.id;
    ${output}=  Execute Sql String  ${query}
    ${row}=  Get From List  ${output}  0
    ${name}=  Get From Dictionary  ${row}  name
    [Return]  ${name}

Move Question Up
    [Arguments]  ${name}
    [Documentation]  Move the selected question before the previous question
    ${move_up}=  Set Variable  ${name}_up
    Click Link  ${move_up}

Move Question Down
    [Arguments]  ${name}
    [Documentation]  Move the selected question after the next question
    ${move_down}=  Set Variable  ${name}_down
    Click Link  ${move_down}

Drag Question To
    [Arguments]  ${source}  ${target}
    [Documentation]  Move the source question to the target.
...                  If the target is a section then question will be placed at the end,
...                  if the target is a question then source question will be placed before that question.
    Drag And Drop  ${source}  target=${target}

Delete Question
    [Arguments]  ${name}
    [Documentation]  Delete the question from the template
    ${delete}=  Set Variable  ${name}_delete
    Click Link  ${delete}

Delete Section
    [Arguments]  ${name}
    [Documentation]  Delete the section from the template
    ${delete}=  Set Variable  ${name}_delete
    Click Link  ${delete}

*** Test Cases ***

Test Keyword
    [Documentation]  Used to test keywords
    ...              Run using: python web2py.py --no-banner -M -S eden -R applications/eden/tests/edentest_runner.py -A  survey -t 'Test keyword'
    ...              For example...
#    Get New Template ID
#    Log to console  ${TEMPLATE ID}
#    ${posn}=  Get Question Position  24H-40
#    Log to console  ${posn}
#    ${posn}=  Get Question Position  24H-43
#    Log to console  ${posn}
#    ${section}=  Get Question Section  24H-40
#    Log to console  ${section}
#    ${count}=  Get Section Count
#    Log to console  ${count}
#    ${count}=  Get Question Count In Section  Background Information
#    Log to console  ${count}
#    ${count}=  Get Question Count In Section  Livelihoods
#    Log to console  ${count}
#    ${count}=  Get Section Count
#    Log to console  ${count}
#    ${name}=  Set Variable  24H-40
#    Log to console  ${TEMPLATE COUNT}
    No Operation


Create New Survey Template
    Login To Eden If Not Logged In  ${VALID USER}  ${VALID PASSWORD}
    Go To  ${TEMPLATE URL}/create
    Input Text  survey_template_name  New Test Template
    Input Text  survey_template_description  A Template created by the test suite
    Input Text  survey_template_competion_qstn  Name of person who completed the questionnaire
    Input Text  survey_template_date_qstn  Date the questionnaire was completed
    Input Text  survey_template_time_qstn  Time the questionnaire was completed
    # Not yet implemented and so should fail here
    Code Incomplete Abort Test  ${Stop On First Error}  ValueError  Unselect Checkbox  Use P-code
    Select Checkbox  Use LO
    Select Checkbox  Use L1
    Select Checkbox  Use L2
    Select Checkbox  Use L3
    Unselect Checkbox  Use L4
    Unselect Checkbox  Use L5
    Select Checkbox  Use Lat
    Select Checkbox  Use Lon
    Submit CRUD Form
    ${TEMPLATE ID}=  Get New Template ID
    Should Show Confirmation
    Go To  ${TEMPLATE URL}
    Should Give X Results  ${TEMPLATE COUNT}+1

Add Questions to Template
    Login To Eden If Not Logged In  ${VALID USER}  ${VALID PASSWORD}
    # Not yet implemented and so should fail here
    Go To URL If Not Already There  ${TEMPLATE URL}/${TEMPLATE ID}/Question/Create
    Code Incomplete Abort Test  ${Stop On First Error}  ValueError  Create Section For Template  Background Information
    Create Question For Active Section  Short Text  Type of disaster  24H-1
    Create Question For Active Section  Yes No  Capacity to respond quickly  24H-2
    Create Question For Active Section  Numeric  Approximate number of inhabitants  24H-3
    Create Question For Active Section  Short Text  Name of contact person in the community  24H-4
    Create Question For Active Section  Short Text  Contact information  24H-5
    Create Question For Active Section  Numeric  # Injured  24H-6
    Create Question For Active Section  Numeric  # Dead  24H-7
    Create Question For Active Section  Numeric  # Missing  24H-8
    Create Question For Active Section  Numeric  # Minor damage  24H-9
    Create Question For Active Section  Numeric  # Moderate damage  24H-10
    Create Question For Active Section  Numeric  # Destroyed  24H-11
    Create Question For Active Section  Grid  Displaced  24H-12-
    Add Grid Question Dimensions  2  2
    Add Grid Question Row Headings  Displaced  Evacuated
    Add Grid Question Column Headings  Currently known  Projected
    Add Grid Question Types  Numeric  Numeric  Numeric  Numeric
    Create Question For Active Section  Option Other  How are people being sheltered?  24H-16
    Add Question Options  Shelter  Host families  Camps
    Create Section For Template  Infrastructure
    Create Question For Active Section  Long Text  Status of roads/best way to access affected area  24H-18
    Create Question For Active Section  Short Text  Rail  24H-19
    Create Question For Active Section  Short Text  Bridges  24H-20
    Create Question For Active Section  Short Text  Water facilities  24H-21
    Create Question For Active Section  Short Text  Sewage systems  24H-22
    Create Question For Active Section  Short Text  Schools  24H-23
    Create Question For Active Section  Short Text  Health facilities  24H-24
    Create Question For Active Section  Short Text  Electricity  24H-25
    Create Question For Active Section  Short Text  Telephones  24H-26
    Create Question For Active Section  Short Text  Airport  24H-27
    Create Question For Active Section  Short Text  Seaport  24H-28
    Create Question For Active Section  Short Text  Hazardous materials  24H-29
    Create Question For Active Section  Short Text  Toxic spills  24H-30
    Create Question For Active Section  Short Text  Oil spills  24H-31
    Create Question For Active Section  Short Text  Mines/ERW  24H-32
    Create Question For Active Section  Short Text  Other  24H-33
    Create Section For Template  Livelihoods
    Create Question For Active Section  Short Text  Commercial buildings  24H-34
    Create Question For Active Section  Short Text  Businesses/factories  24H-35
    Create Question For Active Section  Short Text  Government buildings  24H-36
    Create Question For Active Section  Long Text  Brief description of livelihood groups and how they are affected (secondary information)  24H-37
    Create Question For Active Section  Short Text  Crops/gardens  24H-38
    Create Question For Active Section  Short Text  Animals (eg livestock, poultry, etc)  24H-39
    Create Question For Active Section  Short Text  Tools  24H-40
    Create Question For Active Section  Short Text  Boats  24H-41
    Create Question For Active Section  Short Text  Nets  24H-42
    Create Question For Active Section  Short Text  Tools  24H-43
    Create Section For Template  Response
    Create Question For Active Section  Yes No Don't Know  Is the local government active in the disaster response?  24H-44
    Create Question For Active Section  Yes No Don't Know  Is the community responding to the disaster?  24H-45
    Create Question For Active Section  Yes No Don't Know  Are NGOs responding in the disaster area?  24H-46
    Create Question For Active Section  Long Text  Which NGOs responding in the disaster area?  24H-47
    Create Question For Active Section  Option  Expected needs  24H-48
    Add Question Options  Rural  Peri-Urban  Urban
    Select Template Section  Background Information
    Create Question For Active Section  Long Text  Describe shelter situation  24H-17
    Submit CRUD Form
    Should Show Confirmation
    ${current_question_cnt}=  Row Count  s3db.survey_question.id > 0
    ${expected}=  Set Variable  48
    ${diff}=  Evaluate  ${current_question_cnt} - ${QUESTION COUNT}
    Should Be Equal  ${expected}  ${diff}  msg=Should have found new ${expected} questions added but ${diff} were added.

Rearrange Questions
    Login To Eden If Not Logged In  ${VALID USER}  ${VALID PASSWORD}
    # Not yet implemented and so should fail here
    Go To URL If Not Already There  ${TEMPLATE URL}/${TEMPLATE ID}/Question/Create
    Code Incomplete Abort Test  ${Stop On First Error}  ValueError  Select Template Section  Response
    Move Section Up
    Select Template Section  Livelihoods
    Move Section Up

    ${posn}=  Get Question Position  24H-40
    Should Be Equal  40  ${posn}
    Move Question UP  24H-40
    ${posn}=  Get Question Position  24H-40
    Should Be Equal  39  ${posn}
    Move Question Down  24H-40
    ${posn}=  Get Question Position  24H-40
    Should Be Equal  40  ${posn}

    ${posn}=  Get Question Position  24H-40
    Should Be Equal  40  ${posn}
    ${section}=  Get Question Section  24H-40
    Should Be Equal  Livelihoods  ${section}
    Drag Question To  24H-40  Response
    ${section}=  Get Question Section  24H-40
    Should Be Equal  Response  ${section}
    Drag Question To  24H-40  Livelihoods
    ${section}=  Get Question Section  24H-40
    Should Be Equal  Livelihoods  ${section}
    Drag Question To  24H-40  24H-41
    ${posn}=  Get Question Position  24H-40
    Should Be Equal  40  ${posn}

Delete New Question and Section
    Login To Eden If Not Logged In  ${VALID USER}  ${VALID PASSWORD}
    ${original section count}=  Get Section Count
    # Not yet implemented and so should fail here
    Go To URL If Not Already There  ${TEMPLATE URL}/${TEMPLATE ID}/Question/Create
    Code Incomplete Abort Test  ${Stop On First Error}  ValueError  Create Section For Template  Temp
    ${original question count}=  Get Question Count In Section  Temp
    ${current section count}=  Get Section Count
    Should Be Equal  ${original section count}+1  ${current section count}
    Create Question For Active Section  Short Text  Temp  24H-Temp
    ${current question count}=  Get Question Count In Section
    Should Be Equal  ${original question count}+1  ${current question count}
    Delete Question  24H-Temp
    ${current question count}=  Get Question Count In Section
    Should Be Equal  ${original question count}  ${current question count}
    Delete Section   Temp
    ${current section count}=  Get Section Count
    Should Be Equal  ${original section count}  ${current section count}

Delete New Survey Template
    Login To Eden If Not Logged In  ${VALID USER}  ${VALID PASSWORD}
    Go To  ${TEMPLATE URL}
    # Should fail here until the code to create the template has been implemented
    Code Incomplete Abort Test  ${Stop On First Error}  Should have found 2 results but found 1  Should Give X Results  ${TEMPLATE COUNT}+1
    DataTable Search  New Test Template
    Should Give X Results  1
    Click Link  Delete
    ${message}=  Confirm Action	# Chooses Ok
    Should Be Equal  ${message}  Are you sure you want to delete this record?
    Should Show Confirmation  Assessment Template deleted
    Go To  ${TEMPLATE URL}
    Should Give X Results  ${TEMPLATE COUNT}
    ${current_question_cnt}=  Row Count  s3db.survey_question.id > 0
    Should Be Equal  ${QUESTION COUNT}  ${current_question_cnt}  msg=Should have ${QUESTION COUNT} questions but found ${current_question_cnt}.
