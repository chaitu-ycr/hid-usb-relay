@echo off
setlocal enabledelayedexpansion
pushd %~dp0\.. || exit /b 1

set "PROJECT_ROOT=%cd%"
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "SPEC_DIR=%BUILD_DIR%"
set "ENTRY_POINT=src\hid_usb_relay\gui.py"

for /f "usebackq delims=" %%V in (`powershell -NoProfile -Command "Get-Content '%PROJECT_ROOT%\pyproject.toml' | Select-String -Pattern '^\s*version\s*=\s*\"([^\"]+)\"' | ForEach-Object { $_.Matches[0].Groups[1].Value }"`) do set "PACKAGE_VERSION=%%V"
if not defined PACKAGE_VERSION echo ERROR: Could not read package version from pyproject.toml.& popd & exit /b 1

set "OUTPUT_NAME=hid-usb-relay-gui-v%PACKAGE_VERSION%"
set "ZIP_PATH=%DIST_DIR%\%OUTPUT_NAME%.exe.zip"

if not exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    echo Creating virtual environment...
    call "%PROJECT_ROOT%\scripts\venv_setup.bat" || goto :ERR
)

set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto :ERR

"%PYTHON%" -m pyinstaller --version >nul 2>nul || (
    echo Installing build dependencies...
    call "%PROJECT_ROOT%\scripts\venv_setup.bat" || goto :ERR
    "%PYTHON%" -m pyinstaller --version >nul 2>nul || goto :ERR
)

if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
mkdir "%DIST_DIR%" >nul 2>nul

"%PYTHON%" -m pyinstaller --noconfirm --clean --noconsole --onefile --name "%OUTPUT_NAME%" --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" --specpath "%SPEC_DIR%" --hidden-import dearpygui.dearpygui "%ENTRY_POINT%" || goto :ERR
if not exist "%DIST_DIR%\%OUTPUT_NAME%.exe" goto :ERR

powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%\%OUTPUT_NAME%.exe' -DestinationPath '%ZIP_PATH%' -Force" || goto :ERR

echo Build complete.
echo Executable: %DIST_DIR%\%OUTPUT_NAME%.exe
echo Archive: %ZIP_PATH%
popd
endlocal
exit /b 0

:ERR
echo ERROR: Build failed.
popd
endlocal
exit /b 1
