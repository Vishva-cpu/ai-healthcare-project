@echo off
REM ---------------------------------------------------------
REM  py.bat – force the use of the Python 3.14 install that
REM  already contains the Groq client (and any other deps).
REM ---------------------------------------------------------
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" %*