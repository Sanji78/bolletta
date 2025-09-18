
# Bolletta — Electricity bill estimation (Home Assistant custom integration)

Custom Home Assistant integration that estimates your **electricity bill** based on:
- a monthly energy consumption sensor,
- PUN price sensors (current and previous month),
- and a set of configurable parameters (fees, fixed charges, taxes, discounts, TV license, etc.).

**Repository**: `https://github.com/Sanji78/bolletta`  
**Author / Codeowner**: `@Sanji78`

---

## ✨ Main features

- Exposes several **sensor entities** representing bill items (energy fixed fee, energy consumption cost, transport fees, system charges, excise, VAT, total).
- Calculations rely on configurable values (fixed fees, network loss percentage, variable charges, VAT, cashback discount, TV license).
- Supports PUN (zonal average price) calculation and PUN of the previous month (used when billing is bi-monthly).
- Built with a coordinator (`PUNDataUpdateCoordinator`) and sensors that compute values on update/poll.
- Compatible with Home Assistant via a **Config Flow** (no YAML configuration required).

---

## 📦 Requirements

- Home Assistant (modern versions; integration tested with 2024 era compatibility).
- Python libraries listed in `manifest.json`: `holidays`, `bs4` (BeautifulSoup4).

---

## 🔧 Installation

### Option A — HACS (recommended)
1. Make sure you have [HACS](https://hacs.xyz/) installed.
2. Go to **HACS → Integrations → ⋮ → Custom repositories**.
3. Add `https://github.com/Sanji78/bolletta` with **Category: Integration**.
4. Install **Bolletta** from HACS and restart Home Assistant.

### Option B — Manual
1. Copy the folder `custom_components/bolletta` into your Home Assistant configuration directory:
   ```
   <config>/custom_components/bolletta
   ```
2. Restart Home Assistant.

---

## ⚙️ Configuration (UI)

1. In Home Assistant: **Settings → Devices & Services → Add Integration**.
2. Search for **Bolletta** and follow the configuration flow:
   - The config flow will ask for several numeric defaults (fees, charges, VAT, etc.) and 3 sensors (monthly energy sensor, current PUN sensor, previous-month PUN sensor).
   - All values can be changed later via the integration **Options**.

> Note: The integration provides an options flow to update parameters after initial setup.

### Main parameters (options)
- `fix_quota_aggr_measure` — Fixed quota: aggregation of measures (€/month)
- `monthly_fee` — Monthly contribution (€/month)
- `nw_loss_percentage` — Network loss percentage (%) — integer 0–100
- `other_fee` — Other fees - Dispatching (€/kWh)
- `fix_quota_transport` — Transport fixed quota (€/month)
- `quota_power` — Power quota (€/kW/month)
- `power_in_use` — Contracted power (kW)
- `energy_sc1` — Energy quota Tier 1 (€/kWh)
- `asos_sc1`, `asos_sc2` — ASOS variable quotas per tier (€/kWh)
- `arim_sc1`, `arim_sc2` — ARIM variable quotas per tier (€/kWh)
- `accisa_tax` — Excise duty (€/kWh)
- `iva` — VAT (%) (integer 0–100)
- `discount` — Cashback discount (€/month)
- `tv_tax` — TV license (€/month)
- `monthly_entity_sensor` — Monthly energy sensor (must be a `sensor` with device_class `energy` and provide `state` and attribute `last_period`)
- `pun_sensor` — Current PUN price sensor
- `pun_mp_sensor` — Previous-month PUN price sensor

---

## 🔎 Exposed entities (sensors)

The integration creates the following sensors (entity_id):

- `sensor.bill_energy_fix_quote`  
  *Energy expense — Fixed fee*  
  Calculation: `fix_quota_aggr_measure * 2 + monthly_fee * 2` (rounded to 2 decimals).

- `sensor.bill_energy_energy_quote`  
  *Energy expense — Energy quota*  
  Calculation: `monthly_consumption * ((1 + nw_loss_percentage/100) * pun + other_fee)`  
  If the current month is even (assumption of bi-monthly billing), the previous period is added using `pun_mp_sensor` and the `last_period` attribute from the consumption sensor.

- `sensor.bill_transport_fix_quote`  
  *Transport and meter handling — Fixed fee*  
  Calculation: `fix_quota_transport * 2`.

- `sensor.bill_transport_power_quote`  
  *Transport — Power quota*  
  Calculation: `quota_power * power_in_use * 2`.

- `sensor.bill_transport_energy_quote`  
  *Transport — Energy quota*  
  Calculation: `monthly_consumption * energy_sc1` (+ previous period if month is even).

- `sensor.bill_asos_arim_quote`  
  *System charges (ASOS / ARIM)*  
  Calculation: combines `asos_sc1` (and optionally `asos_sc2`) and `arim_sc1` (and `arim_sc2`) applied on monthly consumption and, if month is even, on the previous period as well.

- `sensor.bill_accisa_tax`  
  *Excise duty (Accisa)*  
  Calculation: `monthly_consumption * accisa_tax` (+ previous period if month is even).

- `sensor.bill_iva`  
  *Total VAT*  
  Calculation: VAT applied to the taxable total.

- `sensor.bill_total`  
  *Total bill*  
  Sum of all items above, VAT, subtract discounts (discount) and add TV license except for November and December (logic present in the code).

### Technical notes about entities
- Unit: `€` (monetary).  
- `state` is a formatted number; integration attempts to set `suggested_display_precision` when supported by HA.
- Sensors use `should_poll = True` — they are recalculated when Home Assistant polls them or on manual update.

---

## 🧾 Requirements for external sensors

- `monthly_entity_sensor` must be a consumption sensor that provides:
  - `.state` → monthly consumption (numeric).
  - `.attributes['last_period']` → previous period consumption (used for bi-monthly calculation).
- `pun_sensor` and `pun_mp_sensor` must expose the PUN price for the current and previous month respectively.

If these sensors are missing or don't provide the expected data, calculations may fail or generate errors in the log.

---

## 🕘 Updates and calculation behavior

- `PUNDataUpdateCoordinator` holds configuration parameters but **does not** force automatic web updates (no `update_interval` set). Individual sensors perform calculations in `manage_update()` and are configured for polling.
- To force recalculation:
  - use the **Refresh entity** action in Home Assistant,
  - or restart the integration/Home Assistant.

---

## 🐞 Troubleshooting

- If sensors show `unknown` or errors:
  - Check that `monthly_entity_sensor`, `pun_sensor`, `pun_mp_sensor` exist and have numeric values.
  - Check logs (**Settings → System → Logs**) for entries under `custom_components.bolletta`.
- If `last_period` is not present on the consumption sensor, the bi-monthly logic will not work—ensure the source sensor provides `last_period`.

---

## 📣 Contributing

PRs and bug reports are welcome. Open issues or PRs at:
`https://github.com/Sanji78/bolletta`

---

## ❤️ Donate
If this project helps you, consider buying me a coffee:  
**[PayPal](https://www.paypal.me/elenacapasso80)**

..and yes... 😊 the paypal account is correct. Thank you so much!

---


## 📜 License

Distributed under the **MIT** license. See `LICENSE` in the repository.

---

## Contact / Support
- Repository: `https://github.com/Sanji78/bolletta`  
- Issue tracker: `https://github.com/Sanji78/bolletta/issues`

