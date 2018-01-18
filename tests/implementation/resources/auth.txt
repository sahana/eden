*** Settings ***
Documentation       Keywords for authorization, usually automatically
...                 run during suite setup and tear down

*** Variables ***
${LOGIN URL}        ${BASEURL}/default/user/login
${LOGOUT URL}       ${BASEURL}/default/user/logout
${UsernameField}    auth_user_email
${PasswordField}    auth_user_password

*** Keywords ***
#Resource: auth.txt; Keyword: Login to Eden
Open Browser To Login Page
    [Documentation]  Open the browser at the login page
    Go To  ${LOGIN URL}
    Run Keyword And Ignore Error  Alert Should Not Be Present
    Maximize Browser Window

#Resource: auth.txt; Keyword: Login to Eden if Not Logged In
Check If Logged In
    [Documentation]  Checks if the user is logged in
    ${EXPR}=  Catenate  xpath=//a[@href="/${APPNAME}/default/user/logout"]
    ${count}=  Get Element Count  ${EXPR}
    Return From Keyword If  ${count} == 0  FAIL
    Return From Keyword  PASS

#Testsuite: hrm; testcase: Find Staff By Organization
Login To Eden If Not Logged In
    [Documentation]  Check if the user is logged in or not . If not
    ...                      login using Login To Eden Helper and given email
    ...                      and password
    [Arguments]  ${email}  ${passwd}
    ${status}=  Check If Logged In
    Run Keyword If  '${status}' == 'FAIL'  Login To Eden  ${email}  ${passwd}

#Similar to the keyword: Login to Eden if not logged in
Login To Eden
    [Documentation]  Open the browser and login to Eden with
    ...              the given username and password.
    [Arguments]  ${email}  ${passwd}
    Open Browser To Login Page
    Input Text  ${UsernameField}  ${email}
    Input Text  ${PasswordField}  ${passwd}
    Click Button  xpath=//input[contains(@class,"btn") and @type="submit"]
    Should Show Confirmation
    Go To  ${BASEURL}?_language=${LANGUAGE}

Self Register A New User
    [Documentation]  Opens up, fills and submits the registration form
    [Arguments]  ${fname}  ${lname}  ${email}  ${passwd}
    Go To  ${BASEURL}/default/user/register
    Input Text  auth_user_first_name  ${fname}
    Input Text  auth_user_last_name  ${lname}
    Input Text  auth_user_email  ${email}
    Input Text  auth_user_password  ${passwd}
    Input Text  auth_user_password_two  ${passwd}
    Click Button  xpath=//input[contains(@class,"btn") and @type="submit"]

#Resources: main.txt; keyword: End testing
Logout From Eden
    [Documentation]  Logout from Eden
    ${status}=  Check If Logged In
    Run Keyword If  '${status}' == 'PASS'  Go To  ${LOGOUT URL}
