@echo off
set PYTHON=C:\Users\Atiya\AppData\Local\Python\pythoncore-3.14-64\python.exe
set APP=%~dp0translator_app.py
"%PYTHON%" "%APP%"
if %errorlevel% neq 0 pause
