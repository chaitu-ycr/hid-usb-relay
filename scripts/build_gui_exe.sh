#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/.."

PROJECT_ROOT="$PWD"
PYTHON="$PROJECT_ROOT/.venv/bin/python"
ENTRY_POINT="$PROJECT_ROOT/src/hid_usb_relay/gui.py"

DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"
SPEC_DIR="$PROJECT_ROOT/spec"

if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
  echo "ERROR: pyproject.toml not found."
  exit 1
fi

if [[ ! -f "$ENTRY_POINT" ]]; then
  echo "ERROR: Entry point not found: $ENTRY_POINT"
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Creating virtual environment..."
  "$PROJECT_ROOT/scripts/venv_setup.sh"
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "ERROR: Python executable not found in $PYTHON"
  exit 1
fi

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
  echo "ERROR: PyInstaller is not installed."
  exit 1
fi

PACKAGE_VERSION="$($PYTHON -c 'import tomllib, pathlib; print(tomllib.load(open(pathlib.Path("pyproject.toml"), "rb"))["project"]["version"])')"
if [[ -z "$PACKAGE_VERSION" ]]; then
  echo "ERROR: Version not found in pyproject.toml."
  exit 1
fi

OUTPUT_NAME="hid-usb-relay-gui-v$PACKAGE_VERSION"
EXE_PATH="$DIST_DIR/$OUTPUT_NAME"
ZIP_PATH="$DIST_DIR/$OUTPUT_NAME.zip"

printf "\n==========================================================\n"
printf "Building Version %s\n" "$PACKAGE_VERSION"
printf "==========================================================\n\n"

rm -rf "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"

"$PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --noconsole \
  --name "$OUTPUT_NAME" \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR" \
  --specpath "$SPEC_DIR" \
  --hidden-import dearpygui.dearpygui \
  "$ENTRY_POINT"

if [[ ! -f "$EXE_PATH" ]]; then
  echo "ERROR: Executable was not created."
  exit 1
fi

rm -f "$ZIP_PATH"
if ! command -v zip >/dev/null 2>&1; then
  echo "ERROR: zip utility is not installed."
  exit 1
fi

zip -j "$ZIP_PATH" "$EXE_PATH"

printf "\n==========================================================\n"
printf "BUILD SUCCESSFUL\n"
printf "==========================================================\n\n"
printf "Executable:\n    %s\n\n" "$EXE_PATH"
printf "Archive:\n    %s\n" "$ZIP_PATH"
