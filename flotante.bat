@echo off
setlocal enableextensions
title Volver a flotante - Reloj Mundial

REM Devuelve el widget a modo FLOTANTE (movible, con fondo) y lo quita del
REM fondo de pantalla. Util cuando quedo "pegado al wallpaper" y ya no se
REM puede hacer clic sobre el para abrir Ajustes.

set "APPDIR=%LOCALAPPDATA%\RelojMundial"
set "SCRIPT=%APPDIR%\worldclock.pyw"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0worldclock.pyw"

REM ---- Localizar pythonw ----
set "PYW="
for /f "delims=" %%i in ('py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do set "PYW=%%i"
if not defined PYW for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
    echo No se encontro Python. Instala Python 3.9+ y marca "Add Python to PATH".
    pause
    exit /b 1
)

REM ---- Cerrar la instancia pegada al wallpaper ----
echo Cerrando el widget...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'worldclock' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
ping -n 2 127.0.0.1 >nul

echo Abriendo en modo flotante (movible)...
start "" "%PYW%" "%SCRIPT%" --flotante --front
endlocal
