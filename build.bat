@echo off
REM One-click build: creates venv, installs deps, builds dist\AdvanceTodoAI.exe
if not exist venv ( py -3 -m venv venv )
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python build.py
echo.
echo Done. Your program: dist\AdvanceTodoAI.exe
pause
