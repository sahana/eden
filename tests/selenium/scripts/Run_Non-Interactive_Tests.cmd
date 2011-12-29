@echo off
start start_selenium.cmd
ping -n 4 127.0.0.1
python regressionTests.py local_ff