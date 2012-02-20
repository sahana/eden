@echo off

rem Start the Selenium Server
rem Designed to be called from 'test.cmd'

netstat -an | findstr /RC:":4444 .*LISTENING" && ECHO Port is in use && EXIT 1

c:
cd \bin
java -jar selenium-server-standalone-2.19.0.jar -singlewindow -port 4444
