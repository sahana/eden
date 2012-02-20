@echo off
rem Read Arguments
IF dummy==dummy%1 (
set application=eden
) ELSE (
set application=%1
)
IF dummy==dummy%2 (
set test=regressionTests
start selenium.cmd
ping -n 12 127.0.0.1
) ELSE (
set test=%2
)

c:
cd \bin\web2py\applications\%application%\tests\selenium\scripts

IF dummy==dummy%2 (
python %test%.py local_ff
) ELSE (
python %test%.py %application%
)