#!/usr/bin/env bash
# Seed the shared demo account of the public test deployment: register it
# (or log in if it already exists) and create a handful of sample parts,
# customers and vehicles through the real API. Safe to rerun: every id is
# derived from a fixed key, so a rerun replays the same creates instead of
# duplicating them.
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

# key|full_name|phone (empty means no phone)
# Fictional names and patterned numbers only -- README.md warns testers
# never to message these. One of each: mobile, mobile, landline, no phone,
# mobile, so WhatsApp eligibility (phone_is_mobile) has a case of each.
customers=(
  "maria-hernandez|María Hernández|9000-0001"
  "jose-nunez|José Núñez|3000-0002"
  "carlos-mejia|Carlos Mejía|2200-0003"
  "ana-castillo|Ana Castillo|"
  "luis-zelaya|Luis Zelaya|8000-0005"
)

# key|owner_customer_key|vehicle_type|make|model|year|plate (raw, to exercise
# normalization: a dash, a space, lowercase, and no separator at all; empty
# plate means unplated, allowed any number of times per owner)
vehicles=(
  "maria-corolla|maria-hernandez|car|Toyota|Corolla|2012|DEM-0001"
  "jose-cg150|jose-nunez|motorcycle|Honda|CG 150|2019|DEM 0002"
  "jose-pulsar|jose-nunez|motorcycle|Bajaj|Pulsar||"
  "carlos-frontier|carlos-mejia|car|Nissan|Frontier|2015|dem0003"
  "ana-ax100|ana-castillo|motorcycle|Suzuki|AX100||"
  "luis-accent|luis-zelaya|car|Hyundai|Accent|2010|DEM0004"
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

declare -A customer_ids
customers_created=0
customers_present=0
customers_edited=0
for entry in "${customers[@]}"; do
  IFS='|' read -r key full_name customer_phone <<<"$entry"
  customer_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/customer/$key")"
  customer_ids["$key"]="$customer_id"
  customer_json="$(jq -n --arg id "$customer_id" --arg name "$full_name" --arg phone "$customer_phone" \
    '{id: $id, full_name: $name} + (if $phone == "" then {} else {phone: $phone} end)')"
  status="$(request POST /api/customers "$customer_json")"
  case "$status" in
    201) customers_created=$((customers_created + 1)) ;;
    200) customers_present=$((customers_present + 1)) ;;
    409)
      # customer_id_conflict: a tester edited this seeded customer. Leave it.
      customers_edited=$((customers_edited + 1))
      ;;
    *) fail "creating customer \"$full_name\" returned HTTP $status" ;;
  esac
done

vehicles_created=0
vehicles_present=0
vehicles_edited=0
vehicles_plate_conflict=0
for entry in "${vehicles[@]}"; do
  IFS='|' read -r key owner_key vehicle_type make model year plate <<<"$entry"
  vehicle_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/vehicle/$key")"
  owner_id="${customer_ids[$owner_key]}"
  vehicle_json="$(jq -n --arg id "$vehicle_id" --arg customer_id "$owner_id" --arg type "$vehicle_type" \
    --arg make "$make" --arg model "$model" --arg year "$year" --arg plate "$plate" '
      {id: $id, customer_id: $customer_id, vehicle_type: $type, make: $make}
      + (if $model == "" then {} else {model: $model} end)
      + (if $year == "" then {} else {year: ($year | tonumber)} end)
      + (if $plate == "" then {} else {plate: $plate} end)
    ')"
  status="$(request POST /api/vehicles "$vehicle_json")"
  case "$status" in
    201) vehicles_created=$((vehicles_created + 1)) ;;
    200) vehicles_present=$((vehicles_present + 1)) ;;
    409)
      # vehicle_id_conflict (edited) or plate_taken (a tester's own vehicle
      # now holds this plate): either way, a tester touched this, kept.
      if [[ "$(jq -r '.detail' "$body_file")" == "plate_taken" ]]; then
        vehicles_plate_conflict=$((vehicles_plate_conflict + 1))
      else
        vehicles_edited=$((vehicles_edited + 1))
      fi
      ;;
    *) fail "creating vehicle \"$key\" returned HTTP $status" ;;
  esac
done

status="$(request GET /api/customers)"
[[ "$status" == "200" ]] || fail "listing customers returned HTTP $status"
customers_total="$(jq 'length' "$body_file")"

echo "Demo account $phone ($workshop_name): $account"
echo "Sample items: $created created, $present already present, $edited edited by testers (kept), $name_taken skipped (name taken)"
echo "Workshop now lists $total active items, $low of them low on stock"
echo "Sample customers: $customers_created created, $customers_present already present, $customers_edited edited by testers (kept)"
echo "Sample vehicles: $vehicles_created created, $vehicles_present already present, $vehicles_edited edited by testers (kept), $vehicles_plate_conflict plate conflicts (kept)"
echo "Workshop now lists $customers_total active customers"
