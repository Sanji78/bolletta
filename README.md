# Bolletta — Electricity bill estimation (Home Assistant custom integration)

Custom Home Assistant integration that estimates your **electricity bill** based on:
- a monthly energy consumption sensor,
- PUN price calculation (either calculated from GSE hourly prices or a fixed value),
- and a set of configurable parameters (fees, fixed charges, taxes, discounts, TV license, etc.).

**Repository**: `https://github.com/Sanji78/bolletta`  
**Author / Codeowner**: `@Sanji78`

---

## ✨ Main features

- Exposes several **sensor entities** representing bill items (energy fixed fee, energy consumption cost, transport fees, system charges, excise, VAT, total).
- Calculations rely on configurable values (fixed fees, network loss percentage, variable charges, VAT, cashback discount, TV license).
- **PUN (zonal average price) can now be used in two ways**: either *calculated automatically* by the integration (from GSE hourly prices) **or** provided as a *fixed PUN value* via the UI. This gives flexibility for testing, offline scenarios, or stable-rate calculations.
- Built with a coordinator (`PUNDataUpdateCoordinator`) and sensors that compute values on update/poll.
- Compatible with Home Assistant via a **Config Flow** (no YAML configuration required).

---

## 📦 Requirements

- Home Assistant (modern versions; integration tested with 2024 era compatibility).
- Python libraries listed in `manifest.json`: `holidays`, `bs4` (BeautifulSoup4).

---

## ⚙️ What changed — PUN mode support

### New behavior
The integration supports a **PUN mode** option (selected during config flow or from the integration Options):

- **Calculated (default)** — PUN is retrieved/averaged by the integration from hourly GSE zonal prices and used to compute the bill (this is the original behavior).
- **Fixed** — PUN is taken from a fixed numeric value entered by the user (option `fixed_pun_value`, expressed in `€/kWh`). When set, the integration uses that fixed value for all PUN-dependent calculations.

### UI / Config flow
During configuration (or in the Options flow) you will find a new dropdown labeled **"Modalità di utilizzo del PUN"** (PUN Mode) with choices:
- `Calcolato da GSE` (calculated)
- `Fisso` (fixed)

If you choose **Fisso**, an additional numeric field appears: **Valore del PUN fisso** (fixed_pun_value in `€/kWh`).

If you choose **Calcolato da GSE**, no fixed value is required and the integration computes PUN sensors internally:
- `sensor.pun_mono_orario`, `sensor.pun_fascia_*`, etc.

Both modes are available at setup time and later through **Settings → Devices & Services → Your integration → Options**.

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
2. Search for **Bolletta** and follow the configuration flow.
   - The config flow asks for several numeric defaults (fees, charges, VAT, etc.) and the `monthly_entity_sensor`.
   - Choose **PUN Mode**: *Calculated* (default) or *Fixed*.
   - If *Fixed* is chosen, enter **Valore del PUN fisso** (€/kWh).
3. You can update all values later via the integration **Options**.

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
- `monthly_entity_sensor` — **Monthly energy sensor** (must be a `sensor` with device_class `energy` and provide `state` and attribute `last_period`). This is still required: the integration uses this sensor as the primary source of monthly consumption.

---

## 🔎 Exposed entities (sensors)

The integration creates the following sensors (entity_id):

- `sensor.bill_energy_fix_quote`  
  *Energy expense — Fixed fee*  
  Calculation: `fix_quota_aggr_measure * 2 + monthly_fee * 2` (rounded to 2 decimals).

- `sensor.bill_energy_energy_quote`  
  *Energy expense — Energy quota*  
  Calculation: `monthly_consumption * ((1 + nw_loss_percentage/100) * pun + other_fee)`  
  If the current month is even (assumption of bi-monthly billing), the previous period is added using the `last_period` attribute from the consumption sensor.

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

- `sensor.bill_kwh_price`  
  *Price per kWh (effective price used in bill calculations)*  
  Calculation: `((1 + nw_loss_percentage/100) * pun_mono_orario + other_fee) + energy_sc1 + asos_sc1 + arim_sc1` (sum of per-kWh components; displayed as €/kWh and used to compute energy line items).

- `sensor.pun_mono_orario`  
  *PUN mono-hourly (zonal average price — current month)*  
  Calculation: average of the hourly PUN prices for the current month expressed as `€ / kWh` (suggested display precision 6 decimals).

- `sensor.pun_mono_orario_mp`  
  *PUN mono-hourly — previous month*  
  Calculation: average of the hourly PUN prices for the previous month expressed as `€ / kWh` (used for bi-monthly / previous-period comparisons).

- `sensor.pun_fascia_f1`  
  *PUN — average price for tariff band F1 (current month)*  
  Calculation: average of hourly PUN values that fall into F1 for the current month, expressed as `€ / kWh`.

- `sensor.pun_fascia_f2`  
  *PUN — average price for tariff band F2 (current month)*  
  Calculation: average of hourly PUN values that fall into F2 for the current month, expressed as `€ / kWh`.

- `sensor.pun_fascia_f3`  
  *PUN — average price for tariff band F3 (current month)*  
  Calculation: average of hourly PUN values that fall into F3 for the current month, expressed as `€ / kWh`.

- `sensor.pun_fascia_f1_mp`  
  *PUN — average price for tariff band F1 (previous month)*  
  Calculation: same as `pun_fascia_f1` but computed over the previous month (`€ / kWh`).

- `sensor.pun_fascia_f2_mp`  
  *PUN — average price for tariff band F2 (previous month)*  
  Calculation: same as `pun_fascia_f2` but computed over the previous month (`€ / kWh`).

- `sensor.pun_fascia_f3_mp`  
  *PUN — average price for tariff band F3 (previous month)*  
  Calculation: same as `pun_fascia_f3` but computed over the previous month (`€ / kWh`).

- `sensor.pun_fascia_f23`  
  *PUN — combined F2+F3 average (current month)*  
  Calculation: combined average of F2 and F3 hourly values for the current month (used by some tariff calculations when F2 and F3 are handled together).

- `sensor.pun_fascia_f23_mp`  
  *PUN — combined F2+F3 average (previous month)*  
  Calculation: combined average of F2 and F3 hourly values for the previous month.

- `sensor.pun_fascia_corrente`  
  *Current PUN time band (enum: F1 / F2 / F3)*  
  Calculation: returns the currently active time band (F1/F2/F3). Attributes include `fascia_successiva`, `inizio_fascia_successiva`, and `termine_fascia_successiva`.

- `sensor.pun_prezzo_fascia_corrente`  
  *Price for the current time band*  
  Calculation: the average PUN price for the currently active band (F1/F2/F3) for the relevant period (`€ / kWh`).

- `sensor.pun_prezzo_zonale`  
  *Zonal hourly price (current hour — zone-aware)*  
  Calculation: current zonal price for the configured zone (`€ / kWh`). Attributes include hourly zonal prices for today and tomorrow (`oggi_h_00` … `oggi_h_23`, `domani_h_00` … `domani_h_23`) and a `zona` attribute when available.

- `sensor.pun_orario`  
  *Hourly PUN price for the current hour (with hourly history in attributes)*  
  Calculation: current PUN for the active hour (`€ / kWh`). Attributes expose the full hourly series for today and tomorrow (`oggi_h_00` … `oggi_h_23`, `domani_h_00` … `domani_h_23`) and a cached `pun_orari` dictionary restored after restart.


### Technical notes about entities
- Unit: `€` (monetary).  
- `state` is a formatted number; integration attempts to set `suggested_display_precision` when supported by HA.
- Sensors use `should_poll = True` — they are recalculated when Home Assistant polls them or on manual update.

---

## 🧾 Requirements for external sensors

- `monthly_entity_sensor` must be a consumption sensor that provides:
  - `.state` → monthly consumption (numeric).
  - `.attributes['last_period']` → previous period consumption (used for bi-monthly calculation).
- **PUN sensors are no longer required** because the integration calculates PUN internally. 

If these sensors are missing or don't provide the expected data, calculations may fail or generate errors in the log.

---

## 🕘 Updates and calculation behavior

- `PUNDataUpdateCoordinator` holds configuration parameters and **does** force automatic web updates (every 10 seconds). Individual sensors perform calculations in `manage_update()` and are configured for polling.

---

## 🐞 Troubleshooting

- If sensors show `unknown` or errors:
  - Check that `monthly_entity_sensor` exists and has numeric value and the `last_period` attribute.
  - Check logs (**Settings → System → Logs**) for entries under `custom_components.bolletta`.
- If `last_period` is not present on the consumption sensor, the bi-monthly logic will not work—ensure the source sensor provides `last_period`.

---

## 🛠 Creating an external monthly consumed kWh sensor (Utility Meter helper)

If you currently have a sensor that provides **daily consumed kWh** (for example `sensor.daily_consumed_kwh`) you can create a **monthly** consumption sensor that stores the previous month's value (`last_period`) using Home Assistant's **Utility Meter** helper. The integration uses the `last_period` attribute to include the previous billing period when needed (bi-monthly billing).

Follow these steps (UI method):

1. In Home Assistant go to **Settings → Devices & Services → Helpers**.  
2. Click **Add Helper** (bottom right).  
3. Choose **Utility meter**.  
4. Fill the helper form:
   - **Name**: e.g. `Monthly energy (from daily)` (this will create an entity like `sensor.monthly_energy_from_daily`).
   - **Source**: select your daily consumed kWh sensor (e.g. `sensor.daily_consumed_kwh`).
   - **Meter reset cycle**: choose **Monthly**.
   - Leave tariffs (if present) empty unless you need separate tariff meters.
5. Save the helper.

What you get:
- A new entity (e.g. `sensor.monthly_energy_from_daily`) that accumulates and resets on a monthly cycle.
- The helper exposes an attribute `last_period` which contains the total consumption of the **previous** cycle (the previous month). You can access it in templates with:
   ```jinja
   {{ state_attr('sensor.monthly_energy_from_daily', 'last_period') }}
   ```
- Use the new helper entity as the `monthly_entity_sensor` in the Bolletta integration configuration.

YAML example (alternative to UI):

If you prefer YAML-based configuration (for installations that still use YAML for helpers), you can add to your `configuration.yaml` (or include file) something along these lines:

```yaml
utility_meter:
  monthly_energy_from_daily:
    source: sensor.daily_consumed_kwh
    cycle: monthly
```

Notes & tips:
- The Utility Meter helper stores the `last_period` attribute automatically. You can use this attribute in templates or set your integration to read it.
- Be aware of timezone / daylight-saving quirks: some users reported the monthly reset happening slightly earlier or later depending on timezone and DST transitions; if your reset appears off by some hours, double-check Home Assistant's timezone setting and the recorder settings. If you need custom reset times, consider using automations to snapshot the current value before reset. (See Home Assistant Utility Meter docs for behavior details.)
- If you need the entity to appear as an energy-type sensor for the Energy Dashboard, make sure the source sensor has appropriate `device_class: energy` and `state_class: total_increasing` metadata where applicable.

References and further reading:
- Official Utility Meter integration documentation.  
- Community threads discussing the `last_period` attribute and reset timing.

(See links in this README response for the docs referenced.)

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
