@echo off
rem Read Arguments
IF dummy==dummy%1 (
set application=eden
) ELSE (
set application=%1
)

IF dummy==dummy%2 (

rem Full Suite using legacy Selenium .jar
set test=regressionTests
start selenium.cmd
ping -n 12 127.0.0.1
c:
cd \bin\web2py\applications\%application%\tests\selenium\scripts
python %test%.py local_ff

) ELSE (

rem Individual script using WebDriver
set test=%2
cd \bin\web2py
python web2py.py -S %application% -M -R applications/eden/modules/tests/suite.py -A %test%

)
