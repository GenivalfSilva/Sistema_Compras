@echo off
echo Restarting Django server...
taskkill /f /im python.exe 2>nul
cd /d %~dp0
call venv\Scripts\activate.bat
python manage.py runserver
