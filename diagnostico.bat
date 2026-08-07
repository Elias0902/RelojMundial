@echo off
setlocal enableextensions
title Diagnostico - Reloj Mundial

REM Ejecuta el widget con CONSOLA visible para ver cualquier error en pantalla.

set "APPDIR=%LOCALAPPDATA%\RelojMundial"
set "SCRIPT=%APPDIR%\worldclock.pyw"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0worldclock.pyw"

set "PY="
for /f "delims=" %%i in ('py -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%i"
if not defined PY for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set "PY=%%i"

if not defined PY (
    echo No se encontro Python. Instala Python 3.9+ y marca "Add Python to PATH".
    pause
    exit /b 1
)

echo Python: %PY%
echo Script: %SCRIPT%
echo.
echo Version de Python:
"%PY%" --version
echo.
echo Ejecutando el widget (cierra la ventana del reloj para terminar)...
echo Si algo falla, el error aparecera aqui abajo.
echo ---------------------------------------------------------------
"%PY%" "%SCRIPT%" --front
echo ---------------------------------------------------------------
echo El programa termino. Revisa arriba si hubo algun error.
echo.
pause
endlocal
