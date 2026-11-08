#!/usr/bin/env bash
# DSAI-02: prove the pins the rest of the course expects.
set -euo pipefail

pass=0
fail=0

ok() { echo "PASS  $1"; pass=$((pass + 1)); }
bad() { echo "FAIL  $1"; fail=$((fail + 1)); }

check_cmd() {
  local name="$1" want="$2"
  shift 2
  if ! command -v "$name" >/dev/null 2>&1; then
    bad "$name not on PATH"
    return
  fi
  local out
  out=$("$@" 2>&1 | head -1)
  case "$out" in
    *$want*) ok "$name ($out)" ;;
    *) bad "$name ($out) (want $want)" ;;
  esac
}

# Python (mise pin 3.13.x)
if command -v python >/dev/null 2>&1; then
  pyver=$(python -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')
  case "$pyver" in
    3.13.*) ok "python $pyver" ;;
    *) bad "python $pyver (want 3.13.x)" ;;
  esac
else
  bad "python not on PATH"
fi

# Terraform 1.17.x
if command -v terraform >/dev/null 2>&1; then
  ver=$(terraform version -json 2>/dev/null | sed -n 's/.*"terraform_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
  if [[ -z "$ver" ]]; then
    ver=$(terraform version | head -1 | sed -n 's/.*v\([0-9.]*\).*/\1/p')
  fi
  case "$ver" in
    1.17.*) ok "terraform $ver" ;;
    *) bad "terraform $ver (want 1.17.x)" ;;
  esac
else
  bad "terraform not on PATH"
fi

# uv
if command -v uv >/dev/null 2>&1; then
  uvver=$(uv --version 2>&1 | head -1)
  case "$uvver" in
    *0.13.*) ok "uv $uvver" ;;
    *) bad "uv $uvver (want 0.13.x)" ;;
  esac
else
  bad "uv not on PATH"
fi

# Semgrep
if command -v semgrep >/dev/null 2>&1; then
  sg=$(semgrep --version 2>&1 | head -1)
  case "$sg" in
    *1.18*) ok "semgrep $sg" ;;
    *) bad "semgrep $sg (want 1.18x)" ;;
  esac
else
  bad "semgrep not on PATH"
fi

# gitleaks
if command -v gitleaks >/dev/null 2>&1; then
  gl=$(gitleaks version 2>&1 | head -1)
  case "$gl" in
    *8.30*) ok "gitleaks $gl" ;;
    *) bad "gitleaks $gl (want 8.30.x)" ;;
  esac
else
  bad "gitleaks not on PATH"
fi

# Checkov
if command -v checkov >/dev/null 2>&1; then
  ck=$(checkov --version 2>&1 | head -1)
  case "$ck" in
    *3.4*) ok "checkov $ck" ;;
    *) bad "checkov $ck (want 3.4.x)" ;;
  esac
else
  bad "checkov not on PATH"
fi

# OSV-Scanner
if command -v osv-scanner >/dev/null 2>&1; then
  osv=$(osv-scanner --version 2>&1 | head -1)
  case "$osv" in
    *2.7*|*version:*2.7*|*"2.7."*) ok "osv-scanner $osv" ;;
    *) bad "osv-scanner $osv (want 2.7.x)" ;;
  esac
else
  bad "osv-scanner not on PATH"
fi

# tflint
if command -v tflint >/dev/null 2>&1; then
  tf=$(tflint --version 2>&1 | head -1)
  case "$tf" in
    *0.65*|*0.66*) ok "tflint $tf" ;;
    *) bad "tflint $tf (want 0.65.x or 0.66.x)" ;;
  esac
else
  bad "tflint not on PATH"
fi

# pre-commit
if command -v pre-commit >/dev/null 2>&1; then
  pc=$(pre-commit --version 2>&1 | head -1)
  case "$pc" in
    *4.7*) ok "pre-commit $pc" ;;
    *) bad "pre-commit $pc (want 4.7.x)" ;;
  esac
else
  bad "pre-commit not on PATH"
fi

echo
echo "Summary: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]
