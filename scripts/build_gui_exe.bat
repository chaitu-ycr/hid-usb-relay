@echo off
setlocal EnableExtensions

REM ==========================================================
REM HID USB Relay GUI Build Script
REM ==========================================================

pushd "%~dp0\.." || (
    echo ERROR: Unable to locate project root.
    exit /b 1
)

set "PROJECT_ROOT=%CD%"
set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "ENTRY_POINT=%PROJECT_ROOT%\src\hid_usb_relay\gui.py"

set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "SPEC_DIR=%PROJECT_ROOT%\spec"

REM ==========================================================
REM Verify project files
REM ==========================================================

if not exist "%PROJECT_ROOT%\pyproject.toml" (
    echo ERROR: pyproject.toml not found.
    goto :ERROR
)

if not exist "%ENTRY_POINT%" (
    echo ERROR: Entry point not found:
    echo %ENTRY_POINT%
    goto :ERROR
)

REM ==========================================================
REM Create virtual environment if needed
REM ==========================================================

if not exist "%PYTHON%" (
    echo Creating virtual environment...

    call "%PROJECT_ROOT%\scripts\venv_setup.bat"
    if errorlevel 1 goto :ERROR
)

if not exist "%PYTHON%" (
    echo ERROR: Python executable not found.
    goto :ERROR
)

REM ==========================================================
REM Verify PyInstaller
REM ==========================================================

"%PYTHON%" -m PyInstaller --version >nul 2>&1

if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    goto :ERROR
)

REM ==========================================================
REM Read version from pyproject.toml
REM ==========================================================

set "VERSION_FILE=%TEMP%\hid_usb_relay_version.txt"
set "PACKAGE_VERSION="

"%PYTHON%" -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" > "%VERSION_FILE%"

if errorlevel 1 (
    echo ERROR: Failed to read version from pyproject.toml.
    if exist "%VERSION_FILE%" del "%VERSION_FILE%"
    goto :ERROR
)

set /p PACKAGE_VERSION=<"%VERSION_FILE%"
del "%VERSION_FILE%" >nul 2>&1

if not defined PACKAGE_VERSION (
    echo ERROR: Version not found.
    goto :ERROR
)

set "OUTPUT_NAME=hid-usb-relay-gui-v%PACKAGE_VERSION%"
set "EXE_PATH=%DIST_DIR%\%OUTPUT_NAME%.exe"
set "ZIP_PATH=%DIST_DIR%\%OUTPUT_NAME%.zip"

echo.
echo ==========================================================
echo Building Version %PACKAGE_VERSION%
echo ==========================================================
echo.

REM ==========================================================
REM Clean previous build
REM ==========================================================

if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
if exist "%SPEC_DIR%" rd /s /q "%SPEC_DIR%"

mkdir "%DIST_DIR%" || goto :ERROR
mkdir "%BUILD_DIR%" || goto :ERROR
mkdir "%SPEC_DIR%" || goto :ERROR

REM ==========================================================
REM Build executable
REM ==========================================================

"%PYTHON%" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name "%OUTPUT_NAME%" ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --hidden-import dearpygui.dearpygui ^
    "%ENTRY_POINT%"

if errorlevel 1 goto :ERROR

if not exist "%EXE_PATH%" (
    echo ERROR: Executable was not created.
    goto :ERROR
)

REM ==========================================================
REM Create ZIP
REM ==========================================================

where tar >nul 2>&1

if errorlevel 1 (
    echo ERROR: Windows tar.exe not found.
    goto :ERROR
)

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

tar -a -c -f "%ZIP_PATH%" -C "%DIST_DIR%" "%OUTPUT_NAME%.exe"

if errorlevel 1 (
    echo ERROR: Failed to create ZIP archive.
    goto :ERROR
)

echo.
echo ==========================================================
echo BUILD SUCCESSFUL
echo ==========================================================
echo.
echo Executable:
echo     %EXE_PATH%
echo.
echo Archive:
echo     %ZIP_PATH%
echo.

popd
endlocal
exit /b 0

:ERROR

echo.
echo ==========================================================
echo BUILD FAILED
echo ==========================================================

popd
endlocal
exit /b 1
