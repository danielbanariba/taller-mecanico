#!/usr/bin/env bash
# Seed the shared demo account of the public test deployment: register it
# (or log in if it already exists) and create a handful of sample parts
# through the real API. Safe to rerun: item ids are derived from fixed
# keys, so a rerun replays the same creates instead of duplicating them.
#
# Usage (credentials come from demo.env, the same values the web build
# prefills on the login form):
#
#   bash -c 'set -a; . ~/.config/taller-mecanico/demo.env; set +a; \
#     deploy/demo/seed-demo-account.sh [base-url]'
#
# The base URL defaults to the public HTTPS one. The session cookie is
# `Secure`, so curl does not send it back over plain http.
set -euo pipefail

base_url="${1:-https://inventario-taller.danielbanariba.com}"
base_url="${base_url%/}"
phone="${VITE_DEMO_PHONE:?set VITE_DEMO_PHONE (load demo.env first)}"
password="${VITE_DEMO_PASSWORD:?set VITE_DEMO_PASSWORD (load demo.env first)}"

workshop_name="Taller Demo"
owner_name="Demo"
# Namespace for the deterministic (UUIDv5) item ids. Changing it, or an
# item's key below, makes the next run create a new item.
id_namespace="taller-mecanico/demo-seed"

# key|name|category|unit|min_stock|sale_price_cents|initial_stock
# Prices are in HNL cents. Three items start at or below their minimum so
# the low-stock alert is visible right away.
items=(
  "aceite-20w50|Aceite de motor 20W-50|Lubricantes|galón|4|62000|10"
  "filtro-aceite|Filtro de aceite (Toyota/Nissan)|Filtros|unidad|5|18000|3"
  "pastillas-freno|Pastillas de freno delanteras|Frenos|juego|4|65000|2"
  "bujia-ngk|Bujía NGK|Encendido|unidad|8|12000|16"
  "refrigerante|Refrigerante verde|Enfriamiento|galón|3|38000|6"
  "banda-distribucion|Banda de distribución|Motor|unidad|2|95000|2"
  "liquido-frenos|Líquido de frenos DOT 3|Frenos|litro|3|16000|7"
  "cadena-moto-428|Cadena de moto 428|Motos|unidad|2|45000|5"
)

cookie_jar="$(mktemp)"
body_file="$(mktemp)"
trap 'rm -f "$cookie_jar" "$body_file"' EXIT

# request METHOD PATH [JSON]: prints the HTTP status; the body lands in $body_file.
request() {
  local method="$1" path="$2" json="${3:-}"
  local args=(-sS -o "$body_file" -w '%{http_code}' -X "$method" -b "$cookie_jar" -c "$cookie_jar")
  if [[ -n "$json" ]]; then
    args+=(-H 'Content-Type: application/json' --data "$json")
  fi
  curl "${args[@]}" "$base_url$path"
}

fail() {
  echo "error: $1" >&2
  if [[ -s "$body_file" ]]; then
    echo "response: $(head -c 300 "$body_file")" >&2
  fi
  exit 1
}

register_json="$(jq -n --arg w "$workshop_name" --arg o "$owner_name" --arg p "$phone" --arg pw "$password" \
  '{workshop_name: $w, owner_name: $o, phone: $p, password: $pw}')"
status="$(request POST /api/auth/register "$register_json")"
case "$status" in
  201) account="registered" ;;
  409)
    login_json="$(jq -n --arg p "$phone" --arg pw "$password" '{phone: $p, password: $pw}')"
    status="$(request POST /api/auth/login "$login_json")"
    case "$status" in
      200) account="already existed, logged in" ;;
      401) fail "the phone is registered but the password does not match VITE_DEMO_PASSWORD" ;;
      429) fail "the phone is locked after too many failed logins; wait 15 minutes" ;;
      *) fail "login returned HTTP $status" ;;
    esac
    ;;
  *) fail "register returned HTTP $status" ;;
esac

created=0
present=0
edited=0
name_taken=0
for entry in "${items[@]}"; do
  IFS='|' read -r key name category unit min_stock price_cents initial_stock <<<"$entry"
  item_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/$key")"
  item_json="$(jq -n --arg id "$item_id" --arg name "$name" --arg category "$category" --arg unit "$unit" \
    --argjson min "$min_stock" --argjson price "$price_cents" --argjson stock "$initial_stock" \
    '{id: $id, name: $name, category: $category, unit: $unit, min_stock: $min,
      sale_price_cents: $price, initial_stock: $stock}')"
  status="$(request POST /api/inventory/items "$item_json")"
  case "$status" in
    201) created=$((created + 1)) ;;
    200) present=$((present + 1)) ;;
    409)
      # The item exists but a tester edited it (item_id_conflict), or a
      # tester created another item with this name (item_name_taken).
      # Either way, leave the testers' data alone.
      if [[ "$(jq -r '.detail' "$body_file")" == "item_name_taken" ]]; then
        name_taken=$((name_taken + 1))
      else
        edited=$((edited + 1))
      fi
      ;;
    *) fail "creating \"$name\" returned HTTP $status" ;;
  esac
done

status="$(request GET /api/inventory/items)"
[[ "$status" == "200" ]] || fail "listing items returned HTTP $status"
total="$(jq 'length' "$body_file")"
low="$(jq '[.[] | select(.is_low)] | length' "$body_file")"

echo "Demo account $phone ($workshop_name): $account"
echo "Sample items: $created created, $present already present, $edited edited by testers (kept), $name_taken skipped (name taken)"
echo "Workshop now lists $total active items, $low of them low on stock"
