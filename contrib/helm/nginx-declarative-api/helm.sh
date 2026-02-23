#!/usr/bin/env bash
# ==============================================================================
# helm.sh — wrapper around helm install/upgrade
# ==============================================================================
# Ensures "helm list" APP VERSION always matches the deployed image tag by
# rewriting Chart.yaml's appVersion field before running Helm.
#
# Usage:
#   ./helm.sh install nginx-dapi . \
#       --namespace nginx-dapi --create-namespace \
#       --set nginxDapi.image.repository=registry.example.com/nginx-declarative-api \
#       --set nginxDapi.image.tag=5.5.1 \
#       --set devportal.image.repository=registry.example.com/nginx-declarative-api-devportal \
#       --set devportal.image.tag=5.5.1
#
#   ./helm.sh upgrade nginx-dapi . \
#       --namespace nginx-dapi \
#       --set nginxDapi.image.tag=5.5.2 \
#       --set devportal.image.tag=5.5.2
#
# The script extracts the value of --set nginxDapi.image.tag (or
# --set appVersion) and writes it into Chart.yaml before calling helm,
# then restores the original Chart.yaml afterwards.
# ==============================================================================

set -euo pipefail

CHART_YAML="$(dirname "$0")/Chart.yaml"
CHART_YAML_BACKUP="${CHART_YAML}.bak"

# ── helper: extract a --set key=value from the argument list ─────────────────
get_set_value() {
  local key="$1"; shift
  local args=("$@")
  local val=""
  for arg in "${args[@]}"; do
    case "$arg" in
      --set) : ;; # next arg handled below
    esac
  done
  # Walk pairs: find "--set key=value" or "--set-string key=value"
  local i=0
  while [ $i -lt ${#args[@]} ]; do
    local a="${args[$i]}"
    if [[ "$a" == "--set" || "$a" == "--set-string" ]]; then
      i=$((i+1))
      local pair="${args[$i]}"
      local k="${pair%%=*}"
      local v="${pair#*=}"
      if [[ "$k" == "$key" ]]; then
        val="$v"
      fi
    elif [[ "$a" == --set=* || "$a" == --set-string=* ]]; then
      local pair="${a#*=}"
      local k="${pair%%=*}"
      local v="${pair#*=}"
      if [[ "$k" == "$key" ]]; then
        val="$v"
      fi
    fi
    i=$((i+1))
  done
  echo "$val"
}

# ── resolve the version to stamp into Chart.yaml ─────────────────────────────
# Priority: --set appVersion  >  --set nginxDapi.image.tag  >  existing appVersion
APP_VERSION="$(get_set_value "appVersion" "$@")"
if [[ -z "$APP_VERSION" ]]; then
  APP_VERSION="$(get_set_value "nginxDapi.image.tag" "$@")"
fi
if [[ -z "$APP_VERSION" ]]; then
  echo "[helm.sh] No appVersion or nginxDapi.image.tag --set found; Chart.yaml unchanged."
else
  echo "[helm.sh] Setting Chart.yaml appVersion → ${APP_VERSION}"
  cp "$CHART_YAML" "$CHART_YAML_BACKUP"
  # Replace the appVersion line (handles both quoted and unquoted values)
  sed -i "s/^appVersion:.*$/appVersion: \"${APP_VERSION}\"/" "$CHART_YAML"
fi

# ── run helm with all original arguments ─────────────────────────────────────
helm "$@"
HELM_EXIT=$?

# ── restore Chart.yaml ────────────────────────────────────────────────────────
if [[ -f "$CHART_YAML_BACKUP" ]]; then
  mv "$CHART_YAML_BACKUP" "$CHART_YAML"
  echo "[helm.sh] Chart.yaml restored."
fi

exit $HELM_EXIT
