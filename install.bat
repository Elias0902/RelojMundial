@echo off
setlocal enableextensions enabledelayedexpansion
title Instalador - Reloj Mundial

echo ============================================
echo   Instalador de Reloj Mundial
echo ============================================
echo.

REM ---- Carpeta de origen (donde esta este .bat) ----
set "SRC=%~dp0"
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

REM ---- Carpeta de instalacion ----
set "APPDIR=%LOCALAPPDATA%\RelojMundial"
set "APPNAME=Reloj Mundial"
set "VERSION=2.1.0"

REM ---- Localizar Python (pythonw.exe) ----
set "PYW="
set "PY="
for /f "delims=" %%i in ('py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))" 2^>nul') do set "PYW=%%i"
for /f "delims=" %%i in ('py -c "import sys;print(sys.executable)" 2^>nul') do set "PY=%%i"

if not defined PYW (
    for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
)
if not defined PY (
    for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set "PY=%%i"
)

if not defined PYW (
    echo [ERROR] No se encontro Python en el sistema.
    echo Instala Python 3.9+ desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo Python detectado:
echo   %PYW%
echo.

REM ---- Cerrar la instancia en ejecucion (reinstalacion limpia) ----
echo Cerrando el widget si ya estaba abierto...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'worldclock' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
REM pequena pausa para liberar el archivo antes de copiar
ping -n 2 127.0.0.1 >nul
echo   Hecho.
echo.

REM ---- Crear carpeta e instalar archivos ----
echo Copiando archivos a:
echo   %APPDIR%
if not exist "%APPDIR%" mkdir "%APPDIR%"
copy /y "%SRC%\worldclock.pyw" "%APPDIR%\worldclock.pyw" >nul
copy /y "%SRC%\reloj.ico"      "%APPDIR%\reloj.ico"      >nul
copy /y "%SRC%\uninstall.bat"  "%APPDIR%\uninstall.bat"  >nul
copy /y "%SRC%\iniciar.bat"    "%APPDIR%\iniciar.bat"    >nul
if exist "%SRC%\flotante.bat" copy /y "%SRC%\flotante.bat" "%APPDIR%\flotante.bat" >nul
if exist "%SRC%\diagnostico.bat" copy /y "%SRC%\diagnostico.bat" "%APPDIR%\diagnostico.bat" >nul
if exist "%SRC%\README.txt" copy /y "%SRC%\README.txt" "%APPDIR%\README.txt" >nul
echo   Hecho.
echo.

REM ---- Instalar tzdata (zonas horarias con horario de verano) ----
echo Instalando base de datos de zonas horarias (tzdata)...
if defined PY (
    "%PY%" -m pip install --user --quiet tzdata 2>nul
) else (
    "%PYW%" -m pip install --user --quiet tzdata 2>nul
)
echo   Hecho.
echo.

REM ---- Acceso directo en el Menu Inicio ----
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
echo Creando acceso directo en el Menu Inicio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTMENU%\%APPNAME%.lnk');" ^
  "$s.TargetPath='%PYW%';" ^
  "$s.Arguments='\"%APPDIR%\worldclock.pyw\" --front';" ^
  "$s.WorkingDirectory='%APPDIR%';" ^
  "$s.IconLocation='%APPDIR%\reloj.ico';" ^
  "$s.Description='Reloj mundial: Venezuela, Chile y Espana';" ^
  "$s.Save()"
echo   Hecho.
echo.

REM ---- Autoarranque al iniciar sesion (clave Run del registro) ----
echo Configurando arranque automatico...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "RelojMundial" /t REG_SZ /d "\"%PYW%\" \"%APPDIR%\worldclock.pyw\"" /f >nul
echo   Hecho.
echo.

REM ---- Registrar en "Aplicaciones y caracteristicas" ----
echo Registrando la aplicacion en Windows...
set "UNKEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\RelojMundial"
reg add "%UNKEY%" /v "DisplayName"     /t REG_SZ    /d "%APPNAME%" /f >nul
reg add "%UNKEY%" /v "DisplayVersion"  /t REG_SZ    /d "%VERSION%" /f >nul
reg add "%UNKEY%" /v "Publisher"       /t REG_SZ    /d "Reloj Mundial" /f >nul
reg add "%UNKEY%" /v "DisplayIcon"     /t REG_SZ    /d "%APPDIR%\reloj.ico" /f >nul
reg add "%UNKEY%" /v "InstallLocation" /t REG_SZ    /d "%APPDIR%" /f >nul
reg add "%UNKEY%" /v "UninstallString" /t REG_SZ    /d "cmd /c \"%APPDIR%\uninstall.bat\"" /f >nul
reg add "%UNKEY%" /v "NoModify"        /t REG_DWORD /d 1 /f >nul
reg add "%UNKEY%" /v "NoRepair"        /t REG_DWORD /d 1 /f >nul
echo   Hecho.
echo.

REM ---- Iniciar el widget ahora (al frente para que se vea) ----
echo Iniciando el widget...
start "" "%PYW%" "%APPDIR%\worldclock.pyw" --front

echo.
echo ============================================
echo   Instalacion completada.
echo   - El widget se iniciara solo al encender el PC.
echo   - Aparece al FRENTE unos segundos y luego pasa al fondo
echo     del escritorio (modo por defecto).
echo   - Si NO lo ves: ejecuta  iniciar.bat  (lo abre al frente).
echo   - Si lo "pegaste al fondo de pantalla" y no puedes hacerle clic:
echo     ejecuta  flotante.bat  (lo devuelve a ventana movible).
echo   - Si algo falla: ejecuta  diagnostico.bat  (muestra el error).
echo   - Clic derecho o el boton de arriba a la derecha para opciones.
echo   - Para desinstalar: Configuracion ^> Aplicaciones,
echo     o ejecuta uninstall.bat en %APPDIR%.
echo ============================================
echo.
pause
endlocal
