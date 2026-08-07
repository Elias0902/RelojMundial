@echo off
setlocal enableextensions
title Iniciar - Reloj Mundial

REM Lanza el widget SIEMPRE visible (al frente). Si falla, muestra el error.

set "APPDIR=%LOCALAPPDATA%\RelojMundial"
set "SCRIPT=%APPDIR%\worldclock.pyw"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0worldclock.pyw"
set "ERR=%APPDATA%\RelojMundial\error.log"

REM ---- Localizar pythonw ----
set "PYW="
for /f "delims=" %%i in ('py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do set "PYW=%%i"
if not defined PYW for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"

if not defined PYW (
    echo No se encontro Python en el sistema.
    echo Instala Python 3.9+ desde https://www.python.org/downloads/
    echo y marca "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo No se encontro worldclock.pyw
    echo Esperado en: %SCRIPT%
    echo.
    pause
    exit /b 1
)

if exist "%ERR%" del /q "%ERR%" >nul 2>&1

echo Iniciando Reloj Mundial...
start "" "%PYW%" "%SCRIPT%" --front

REM Esperar y comprobar si hubo error
timeout /t 3 >nul
if exist "%ERR%" (
    echo.
    echo ================= HUBO UN ERROR =================
    type "%ERR%"
    echo =================================================
    echo.
    start "" notepad "%ERR%"
    pause
) else (
    echo El widget se abrio (aparece al frente unos segundos).
    timeout /t 2 >nul
)
endlocal
