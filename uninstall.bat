@echo off
setlocal enableextensions
title Desinstalador - Reloj Mundial

echo ============================================
echo   Desinstalador de Reloj Mundial
echo ============================================
echo.

set "APPDIR=%LOCALAPPDATA%\RelojMundial"
set "CFGDIR=%APPDATA%\RelojMundial"
set "APPNAME=Reloj Mundial"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo Este desinstalador eliminara Reloj Mundial de tu equipo.
choice /c SN /n /m "Deseas continuar? (S/N): "
if errorlevel 2 (
    echo Cancelado.
    timeout /t 2 >nul
    exit /b 0
)
echo.

REM ---- Detener el widget si esta en ejecucion ----
echo Cerrando el widget...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*worldclock.pyw*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" 2>nul
echo   Hecho.

REM ---- Quitar arranque automatico ----
echo Quitando arranque automatico...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "RelojMundial" /f >nul 2>&1
echo   Hecho.

REM ---- Quitar registro de "Aplicaciones y caracteristicas" ----
echo Quitando registro de la aplicacion...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\RelojMundial" /f >nul 2>&1
echo   Hecho.

REM ---- Quitar acceso directo del Menu Inicio ----
echo Quitando acceso directo...
if exist "%STARTMENU%\%APPNAME%.lnk" del /f /q "%STARTMENU%\%APPNAME%.lnk" >nul 2>&1
echo   Hecho.

REM ---- Quitar configuracion del usuario ----
if exist "%CFGDIR%" rmdir /s /q "%CFGDIR%" >nul 2>&1

echo.
echo Eliminando archivos de la aplicacion...

REM ---- Autoeliminacion: borrar la carpeta de instalacion (incluye este .bat) ----
start "" /min cmd /c "timeout /t 2 >nul & rmdir /s /q ""%APPDIR%"""

echo.
echo ============================================
echo   Reloj Mundial ha sido desinstalado.
echo ============================================
timeout /t 3 >nul
endlocal
exit
