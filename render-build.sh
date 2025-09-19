#!/usr/bin/env bash
set -euo pipefail

python --version || true
pip --version || true

python -m pip install --upgrade pip setuptools wheel

pip install -r requirements.txt