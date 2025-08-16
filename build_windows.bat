@echo off
REM بناء ملف EXE
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller==6.6.0
pyinstaller --noconsole --onefile --add-data "assets\logo.png;assets" app.py
pause
