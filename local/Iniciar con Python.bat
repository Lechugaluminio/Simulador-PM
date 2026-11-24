@echo off
rem Alternativa a CroquisPM.exe para computadores que ya tienen Python instalado.
cd /d "%~dp0"
where pyw >nul 2>nul && (start "" pyw croquis_pm.py & exit /b)
where pythonw >nul 2>nul && (start "" pythonw croquis_pm.py & exit /b)
python croquis_pm.py
