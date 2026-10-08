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

# key|owner_vehicle_key|target_status (reached by walking the acyclic
# transition table step by step below -- never jumped to directly).
# `maria-corolla` gets two orders on purpose, so its detail screen's
# service history always has more than one entry to show.
orders=(
  "corolla-brakes|maria-corolla|in_progress"
  "cg150-service|jose-cg150|quote"
  "frontier-oil|carlos-frontier|completed"
  "accent-diagnosis|luis-accent|approved"
  "corolla-alignment|maria-corolla|delivered"
  "pulsar-quote|jose-pulsar|cancelled"
)

# order_key|kind|item_key(empty unless inventory_part)|description|quantity|unit_price_cents
order_lines=(
  "corolla-brakes|labor||Cambio de pastillas delanteras|1|35000"
  "corolla-brakes|inventory_part|pastillas-freno|Pastillas de freno delanteras|1|65000"
  "cg150-service|labor||Revisión general|1|25000"
  "cg150-service|inventory_part|cadena-moto-428|Cadena de moto 428|1|45000"
  "cg150-service|external_part||Llanta trasera 3.00-18|1|90000"
  "frontier-oil|inventory_part|aceite-20w50|Aceite de motor 20W-50|2|62000"
  "frontier-oil|inventory_part|filtro-aceite|Filtro de aceite (Toyota/Nissan)|1|18000"
  "frontier-oil|labor||Cambio de aceite y filtro|1|15000"
  "accent-diagnosis|labor||Diagnóstico general|1|30000"
  "corolla-alignment|labor||Alineación y balanceo|1|40000"
)

# key|order_key|amount_cents|method
# Frontier oil (total L1,570.00: 2 x aceite-20w50 + filtro-aceite + labor)
# gets a partial cash deposit, on purpose, so it still shows a balance due.
# Corolla alignment (total L400.00, labor only) gets a transfer that
# settles it exactly, so both a partial and a fully-paid order are visible.
payments=(
  "frontier-deposit|frontier-oil|50000|cash"
  "corolla-alignment-paid|corolla-alignment|40000|transfer"
)

# The ordered `PUT .../status` steps that walk each target status from
# `quote`, one edge of the acyclic transition table at a time (`design.md`'s
# AD-7) -- never a direct jump. On a rerun, every step the order already
# passed replies 200 (no-op, already there) or 409 (unreachable from a
# later status, i.e. a tester already moved it further); either way
# nothing new is created.
declare -A status_sequence=(
  [quote]=""
  [approved]="approved"
  [in_progress]="approved in_progress"
  [completed]="approved in_progress completed"
  [delivered]="approved in_progress completed delivered"
  [cancelled]="cancelled"
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

declare -A vehicle_ids
vehicles_created=0
vehicles_present=0
vehicles_edited=0
vehicles_plate_conflict=0
for entry in "${vehicles[@]}"; do
  IFS='|' read -r key owner_key vehicle_type make model year plate <<<"$entry"
  vehicle_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/vehicle/$key")"
  vehicle_ids["$key"]="$vehicle_id"
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

declare -A order_ids
orders_created=0
orders_present=0
orders_edited=0
for entry in "${orders[@]}"; do
  IFS='|' read -r key vehicle_key _target_status <<<"$entry"
  order_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/order/$key")"
  order_ids["$key"]="$order_id"
  vehicle_id="${vehicle_ids[$vehicle_key]}"
  order_json="$(jq -n --arg id "$order_id" --arg vehicle_id "$vehicle_id" '{id: $id, vehicle_id: $vehicle_id}')"
  status="$(request POST /api/work-orders "$order_json")"
  case "$status" in
    201) orders_created=$((orders_created + 1)) ;;
    200) orders_present=$((orders_present + 1)) ;;
    409)
      # work_order_id_conflict: a tester edited this seeded order. Leave it.
      orders_edited=$((orders_edited + 1))
      ;;
    *) fail "creating work order \"$key\" returned HTTP $status" ;;
  esac
done

lines_created=0
lines_present=0
lines_edited=0
for entry in "${order_lines[@]}"; do
  IFS='|' read -r order_key kind item_key description quantity unit_price_cents <<<"$entry"
  order_id="${order_ids[$order_key]}"
  line_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/line/$order_key/${item_key:-$kind}")"
  if [[ -n "$item_key" ]]; then
    item_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/$item_key")"
    line_json="$(jq -n --arg id "$line_id" --arg kind "$kind" --arg item_id "$item_id" --arg desc "$description" \
      --argjson qty "$quantity" --argjson price "$unit_price_cents" \
      '{id: $id, kind: $kind, item_id: $item_id, description: $desc, quantity: $qty, unit_price_cents: $price}')"
  else
    line_json="$(jq -n --arg id "$line_id" --arg kind "$kind" --arg desc "$description" \
      --argjson qty "$quantity" --argjson price "$unit_price_cents" \
      '{id: $id, kind: $kind, description: $desc, quantity: $qty, unit_price_cents: $price}')"
  fi
  status="$(request POST "/api/work-orders/$order_id/lines" "$line_json")"
  case "$status" in
    201) lines_created=$((lines_created + 1)) ;;
    200) lines_present=$((lines_present + 1)) ;;
    409)
      # work_order_line_id_conflict: a tester edited this seeded line. Leave it.
      lines_edited=$((lines_edited + 1))
      ;;
    *) fail "adding a line to \"$order_key\" returned HTTP $status" ;;
  esac
done

status_changes=0
status_tester_moved=0
for entry in "${orders[@]}"; do
  IFS='|' read -r key _vehicle_key target_status <<<"$entry"
  order_id="${order_ids[$key]}"
  for step_status in ${status_sequence[$target_status]}; do
    status_json="$(jq -n --arg s "$step_status" '{status: $s}')"
    status="$(request PUT "/api/work-orders/$order_id/status" "$status_json")"
    case "$status" in
      200) status_changes=$((status_changes + 1)) ;;
      409)
        # invalid_status_transition: a tester already moved this order past
        # (or around) this step, or a rerun finds it already settled past
        # this point. Leave it as the tester left it.
        status_tester_moved=$((status_tester_moved + 1))
        ;;
      *) fail "changing \"$key\" to \"$step_status\" returned HTTP $status" ;;
    esac
  done
done

payments_created=0
payments_present=0
payments_edited=0
payments_balance_conflict=0
for entry in "${payments[@]}"; do
  IFS='|' read -r key order_key amount_cents method <<<"$entry"
  payment_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/payment/$key")"
  order_id="${order_ids[$order_key]}"
  payment_json="$(jq -n --arg id "$payment_id" --argjson amount "$amount_cents" --arg method "$method" \
    '{id: $id, amount_cents: $amount, method: $method}')"
  status="$(request POST "/api/work-orders/$order_id/payments" "$payment_json")"
  case "$status" in
    201) payments_created=$((payments_created + 1)) ;;
    200) payments_present=$((payments_present + 1)) ;;
    409)
      # payment_id_conflict (a tester edited this seeded payment) or
      # payment_exceeds_balance (a tester edited the order's lines, so the
      # seeded amount no longer fits the balance): either way, a tester
      # touched this, kept.
      if [[ "$(jq -r '.detail' "$body_file")" == "payment_exceeds_balance" ]]; then
        payments_balance_conflict=$((payments_balance_conflict + 1))
      else
        payments_edited=$((payments_edited + 1))
      fi
      ;;
    *) fail "recording payment \"$key\" returned HTTP $status" ;;
  esac
done

# --- Phase A (sar-invoicing): fiscal profile, a Factura 01 range, María
# Hernández's billing data, and one issued Factura on the Corolla alignment
# order. The profile, RTN and CAI are all obviously fictional
# (design.md's AD-17, question 3): no real workshop's data belongs here.
#
# `range_deadline` is a FIXED literal, not `today + 364 days` computed at
# run time. Registering a range sends the same `{id, ..., issue_deadline}`
# payload every run so the server's replay check (AD-6) can return 200 on
# a rerun instead of a conflict; a deadline computed from "today" would
# change every day the script runs and break that replay. Once this fixed
# date passes, registering a *new* range needs a later deadline -- see
# README.md's "yearly re-registration" note.
profile_json="$(jq -n '{
  rtn: "99999999999999",
  legal_name: "Taller Demostración S. de R.L.",
  trade_name: "Taller Demo",
  address: "Colonia Demostración, Tegucigalpa, Honduras",
  phone: "2200-0000",
  email: "demo@example.invalid",
  establishment_code: "001",
  emission_point_code: "001"
}')"
status="$(request PUT /api/invoicing/profile "$profile_json")"
case "$status" in
  201) profile_result="created" ;;
  200) profile_result="already present" ;;
  *) fail "saving the fiscal profile returned HTTP $status" ;;
esac

maria_id="${customer_ids[maria-hernandez]}"
status="$(request PATCH "/api/customers/$maria_id" '{"billing_name": "María Hernández", "rtn": "99999999990001"}')"
[[ "$status" == "200" ]] || fail "setting María Hernández's billing data returned HTTP $status"

range_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/invoicing/range/factura-01")"
range_deadline="2027-10-06"
range_json="$(jq -n --arg id "$range_id" --arg dl "$range_deadline" '{
  id: $id, document_type: "01", cai: "010101-010101-010101-010101-DEMO01-01",
  range_start: 1, range_end: 500, issue_deadline: $dl
}')"
status="$(request POST /api/invoicing/cai-ranges "$range_json")"
case "$status" in
  201) range_result="created" ;;
  200) range_result="already present" ;;
  422)
    fail "registering the seeded CAI range returned HTTP 422 -- the fixed issue_deadline ($range_deadline) has probably passed; see README.md's yearly re-registration note"
    ;;
  *) fail "registering the seeded CAI range returned HTTP $status" ;;
esac

invoice_id="$(uuidgen --sha1 --namespace @url --name "$id_namespace/invoicing/invoice/corolla-alignment")"
invoice_json="$(jq -n --arg id "$invoice_id" --arg oid "${order_ids[corolla-alignment]}" '{id: $id, order_id: $oid}')"
status="$(request POST /api/invoicing/invoices "$invoice_json")"
case "$status" in
  201) invoice_result="issued" ;;
  200) invoice_result="already present" ;;
  *) fail "issuing the seeded Factura returned HTTP $status" ;;
esac

status="$(request GET /api/customers)"
[[ "$status" == "200" ]] || fail "listing customers returned HTTP $status"
customers_total="$(jq 'length' "$body_file")"

status="$(request GET /api/work-orders?status_group=all)"
[[ "$status" == "200" ]] || fail "listing work orders returned HTTP $status"
orders_total="$(jq 'length' "$body_file")"

echo "Demo account $phone ($workshop_name): $account"
echo "Sample items: $created created, $present already present, $edited edited by testers (kept), $name_taken skipped (name taken)"
echo "Workshop now lists $total active items, $low of them low on stock"
echo "Sample customers: $customers_created created, $customers_present already present, $customers_edited edited by testers (kept)"
echo "Sample vehicles: $vehicles_created created, $vehicles_present already present, $vehicles_edited edited by testers (kept), $vehicles_plate_conflict plate conflicts (kept)"
echo "Workshop now lists $customers_total active customers"
echo "Sample work orders: $orders_created created, $orders_present already present, $orders_edited edited by testers (kept)"
echo "Sample order lines: $lines_created created, $lines_present already present, $lines_edited edited by testers (kept)"
echo "Sample status changes: $status_changes applied, $status_tester_moved left as testers moved them (already there or unreachable)"
echo "Workshop now lists $orders_total work orders (any status)"
echo "Sample payments: $payments_created created, $payments_present already present, $payments_edited edited by testers (kept), $payments_balance_conflict balance conflicts (kept)"
echo "Fiscal profile (Taller Demostración S. de R.L.): $profile_result"
echo "María Hernández's billing name and RTN: set"
echo "Sample CAI range (Factura 01, 1-500, deadline $range_deadline): $range_result"
echo "Sample Factura on the Corolla alignment order (001-001-01-00000001): $invoice_result"
