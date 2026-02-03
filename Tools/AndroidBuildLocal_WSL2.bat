@REM @echo off
REM ============================================================================
REM WARNING: Call this from project root!
REM Perform a local build to create an Android APK (assuming you have a WSL2 set
REM up to do the build)
REM ============================================================================
setlocal EnableExtensions EnableDelayedExpansion

REM --- Config ---
REM CB: Happens to be what I used when I set up the build environment, believe this
REM is not a hard requirement
set "DISTRO=Ubuntu-22.04" 

rem Compute BASENAME globally (available to all calls)
for %%I in ("%CD%") do set "BASENAME=%%~nI"


REM ============================================================================
REM 1) Copy relevant files
REM ============================================================================
REM Copy across unit tests
call :copy-dir-to-wsl2 "java"
call :copy-dir-to-wsl2 "python"
call :copy-file-to-wsl2 "main.py"
call :copy-file-to-wsl2 "buildozer.spec"

REM ============================================================================
REM 2) Perform the build
REM ============================================================================
wsl -d %DISTRO% -- bash -lc "cd ~/%BASENAME%_Copy && buildozer -v android debug --allow-external --allow-downgrade"

REM ============================================================================
REM 3) Copy back APK to Windows project folder (APK also in WSL at ~/%BASENAME%_Copy/bin/)
REM ============================================================================
call :ensure-dir LocalAndroidBuild
for /f "delims=" %%P in ('wsl -d %DISTRO% -e wslpath -a "%CD%"') do set "WSL_PROJECT=%%P"
wsl -d %DISTRO% -e bash -c "cp -v ~/%BASENAME%_Copy/bin/*.apk '%WSL_PROJECT%/LocalAndroidBuild/' 2>/dev/null || true"
exit

REM ============================================================================
REM Functions
REM ============================================================================
:copy-dir-to-wsl2
set "SUB_DIR=%~1"
echo Syncing "%SUB_DIR%\" -> "$HOME/%BASENAME%_Copy/%SUB_DIR%"
wsl -d %DISTRO% -- bash -lc "mkdir -p ~/%BASENAME%_Copy/%SUB_DIR% && rsync -av --delete ./%SUB_DIR%/ ~/%BASENAME%_Copy/%SUB_DIR%"
exit /b 0

:copy-file-to-wsl2
set "FILE=%~1"
echo Syncing "%FILE%" -> "$HOME/%BASENAME%_Copy/%FILE%"
wsl -d %DISTRO% -- bash -lc "rsync -av --delete ./%FILE% ~/%BASENAME%_Copy/%FILE%"
exit /b 0

:ensure-dir
rem %~1 = directory path
if not exist "%~1" (
    echo Creating directory: %~1
    mkdir "%~1"
) else (
    echo Directory already exists: %~1
)
exit /b
