@echo off
REM Start Django development server accessible from React Native
REM This binds to 0.0.0.0 to allow connections from emulators and devices

call venv\Scripts\activate.bat
python manage.py runserver 0.0.0.0:8000



