#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_CQ_EDITOR="$ROOT/.venv/bin/cq-editor"
PACKAGED_CQ_EDITOR="$ROOT/tools/cq-editor/CQ-editor"
VIEWER="${1:-$ROOT/cad/view_p300_poc_fixture.py}"

if [[ "$VIEWER" != /* ]]; then
  VIEWER="$ROOT/$VIEWER"
fi

if [[ ! -f "$VIEWER" ]]; then
  echo "Viewer script not found at: $VIEWER" >&2
  exit 1
fi

if [[ -x "$VENV_CQ_EDITOR" ]]; then
  CQ_EDITOR="$VENV_CQ_EDITOR"
elif [[ -x "$PACKAGED_CQ_EDITOR" ]]; then
  CQ_EDITOR="$PACKAGED_CQ_EDITOR"
else
  echo "CQ-Editor not found at: $VENV_CQ_EDITOR or $PACKAGED_CQ_EDITOR" >&2
  echo "Run 'uv sync --python 3.11 --extra dev' or install it from https://cadquery.github.io/downloads" >&2
  exit 1
fi

# The packaged CQ-Editor binary is built with PyInstaller. PyInstaller's splash
# screen support is incompatible with macOS, and the app can throw
# KeyError: '_PYI_SPLASH_IPC' unless the splash screen is explicitly suppressed.
launchctl setenv PYINSTALLER_SUPPRESS_SPLASH_SCREEN 1
export PYINSTALLER_SUPPRESS_SPLASH_SCREEN=1

cd "$ROOT"
exec "$CQ_EDITOR" "$VIEWER"
