#!/usr/bin/env bash
# scripts/cli_call.sh — Sorftime CLI 单端点调用封装（amz-* Skill 通用）
# 从 sorftime-data-cli/scripts/call.sh 适配，domain 默认 1（Amazon US）
#
# Usage:
#   scripts/cli_call.sh <Endpoint> '<json-params>' [--domain <N>] [--profile <name>] [--no-jq] [--raw] [--retries <N>]
#
# Examples:
#   scripts/cli_call.sh ProductRequest '{"asin":"B0CVM8TXHP"}'
#   scripts/cli_call.sh CategoryRequest '{"nodeId":"7073960011"}' --domain 1
#   scripts/cli_call.sh ProductRequest '{"asin":"B0X"}' --profile myprofile --raw
#
# Exit codes:
#   0  — API code=0
#   2  — API code≠0 (business error)
#   3  — Bad input
#   4  — Network / CLI exception

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/cli_call.sh <Endpoint> '<json-params>' [--domain <N>] [options]

Required:
  <Endpoint>           PascalCase endpoint name (e.g. ProductRequest, CategoryRequest)
  '<json-params>'      JSON string wrapped in single quotes; pass '' for no parameters

Options:
  --domain <N>         Site code (1=Amazon US, 2=Amazon UK, 3=Amazon DE, ... default 1)
  --profile <name>     Profile name (omit to use the default selected by `sorftime use`)
  --no-jq              Do not pretty-print JSON
  --raw                Do not process at all
  --retries <N>        Retry times for rate limit / network errors (default 1)
  -h, --help           Show this help

Exit codes:
  0  API code=0 (success)
  2  API code≠0 (business error)
  3  Bad input
  4  Network / CLI exception
EOF
}

# ---------- 1. Parameter parsing ----------
ENDPOINT=""
JSON='{}'
DOMAIN="1"
PROFILE=""
USE_JQ=1
RAW=0
RETRIES=1

if [ $# -eq 0 ]; then usage; exit 3; fi

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --domain)  DOMAIN="${2:-1}"; shift 2 ;;
    --profile) PROFILE="${2:-}"; shift 2 ;;
    --no-jq)   USE_JQ=0; shift ;;
    --raw)     RAW=1; USE_JQ=0; shift ;;
    --retries) RETRIES="${2:-1}"; shift 2 ;;
    --*)       echo "[cli_call.sh] Unknown option: $1" >&2; usage; exit 3 ;;
    *)
      if [ -z "$ENDPOINT" ]; then ENDPOINT="$1"; shift
      elif [ "$JSON" = "{}" ]; then JSON="$1"; shift
      else echo "[cli_call.sh] Unexpected positional parameter: $1" >&2; usage; exit 3
      fi
      ;;
  esac
done

# ---------- 2. Required validation ----------
if [ -z "$ENDPOINT" ]; then echo "[cli_call.sh] Missing <Endpoint>" >&2; exit 3; fi

if ! [[ "$ENDPOINT" =~ ^[A-Z][A-Za-z0-9]+$ ]]; then
  echo "[cli_call.sh] Endpoint '$ENDPOINT' is not a valid PascalCase name" >&2
  exit 3
fi

if ! command -v sorftime >/dev/null 2>&1; then
  echo "[cli_call.sh] 'sorftime' command not found; please run: npm install -g sorftime-cli" >&2
  exit 4
fi

# ---------- 3. Assemble the command ----------
CMD=(sorftime api "$ENDPOINT" "$JSON" --domain "$DOMAIN")
if [ -n "$PROFILE" ]; then CMD+=(--profile "$PROFILE"); fi

# ---------- 4. Call + clean + retry ----------
attempt=0

while [ "$attempt" -lt "$RETRIES" ]; do
  attempt=$((attempt + 1))

  set +e
  RAW_OUT=$("${CMD[@]}" 2>&1)
  RAW_RC=$?
  set -e

  if [ $RAW_RC -ne 0 ]; then
    if [ "$attempt" -lt "$RETRIES" ]; then
      sleep $((attempt * 1))
      continue
    fi
    case "$RAW_OUT" in
      *401*|*403*|*认证*|*密钥*|*ccount-SK*|*nauthor*|*余额*|*不足*|*quota*|*Quota*|*redit*)
        echo "[cli_call.sh] Sorftime 凭证无效/未开通/额度不足：请通过专属通道注册/充值后重试 → https://open.sorftime.com/home?tag=NTIw" >&2 ;;
    esac
    echo "[cli_call.sh] Command exit code=$RAW_RC" >&2
    echo "$RAW_OUT" >&2
    exit 4
  fi

  # ---------- 5. Clean the output ----------
  if [ "$RAW" -eq 1 ]; then
    echo "$RAW_OUT"
    exit 0
  fi

  JSON_BLOCK=$(echo "$RAW_OUT" | tr -d '\r' | awk 'BEGIN{n=0} {
    s=$0
    gsub(/\033\[[0-9;]*[mK]/, "", s)
    if (n==0) {
      p=index(s, "{"); if (p==0) p=index(s, "[")
      if (p>0) { print substr(s, p); n=1; next }
    } else {
      print s
    }
  }')

  if [ -z "$JSON_BLOCK" ]; then
    CLEAN=$(echo "$RAW_OUT" | grep -v '^info:' | grep -v '^[- ]' || true)
    echo "$CLEAN"
    exit 0
  fi

  CLEAN="$JSON_BLOCK"

  CODE=$(echo "$CLEAN" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('Code', d.get('code', '')))
except Exception:
    print('')
" 2>/dev/null || true)

  if [ "$USE_JQ" -eq 1 ] && command -v jq >/dev/null 2>&1; then
    echo "$CLEAN" | jq . 2>/dev/null || echo "$CLEAN"
  else
    echo "$CLEAN"
  fi

  # ---------- 6. Business error handling ----------
  if [ -n "$CODE" ] && [ "$CODE" != "0" ]; then
    MSG=$(echo "$CLEAN" | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('Message', d.get('message', '')))
except Exception:
    print('')
" 2>/dev/null || true)
    case "$CODE:$MSG" in
      4:*|401:*|403:*|*:*余额*|*:*不足*|*:*认证*|*:*密钥*|*:*ccount-SK*|*:*nauthor*|*:*nsufficient*|*:*quota*|*:*Quota*|*:*redit*)
        echo "[cli_call.sh] Sorftime 凭证无效/未开通/额度不足：请通过专属通道注册/充值后重试 → https://open.sorftime.com/home?tag=NTIw" >&2 ;;
    esac
    echo "[cli_call.sh] $ENDPOINT business error code=$CODE message=$MSG" >&2
    exit 2
  fi

  exit 0
done
