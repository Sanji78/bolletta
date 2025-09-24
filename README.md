# Bolletta — Electricity bill estimation (Home Assistant custom integration)

Custom Home Assistant integration that estimates your **electricity bill** based on:
- a monthly energy consumption sensor,
- PUN price calculation (either calculated from GME hourly prices or a fixed value),
- ARERA tariff parameters (automatically retrieved),
- Portale delle Offerte tax parameters (automatically retrieved),
- and a set of configurable parameters (fees, fixed charges, taxes, discounts, TV license, etc.).

**Repository**: `https://github.com/Sanji78/bolletta`  
**Author / Codeowner**: `@Sanji78`

---

## ✨ Main features

- Exposes several **sensor entities** representing bill items (energy fixed fee, energy consumption cost, transport fees, system charges, excise, VAT, total).
- **Automatic parameter retrieval** from ARERA (monthly tariff parameters) and Portale delle Offerte (tax rates and system charges).
- **Flexible billing periods** with configurable monthly/bimonthly billing and invoice shift options.
- **PUN integration** with two modes: calculated from GME market data or fixed value.
- **Precise calculations** that match actual utility bills to the cent.
- **Grouped devices** for better organization in Home Assistant (PUN, ARERA, Bolletta, PortaleOfferte).
- Built with a coordinator (`PUNDataUpdateCoordinator`) and sensors that compute values on update/poll.
- Compatible with Home Assistant via a **Config Flow** (no YAML configuration required).

---

## 🆕 What's New in Version 1.3.0

### Major Improvements
- **Automatic ARERA parameter retrieval**: No more manual entry of energy quotas, transport fees, ASOS/ARIM values
- **Automatic Portale delle Offerte integration**: Automatic retrieval of tax rates (IVA, accisa), network loss percentages
- **Enhanced billing flexibility**: Configurable monthly/bimonthly billing with invoice shift options
- **Improved sensor organization**: Sensors grouped into logical devices for better HA interface management
- **Precision calculations**: Fixed rounding issues - now matches actual utility bills exactly
- **Tested and validated**: Calculations verified against real utility bills with cent-level accuracy

### New Configuration Options
- **House type selection**: Residential vs Non-residential properties
- **Billing period switches**: Monthly billing and invoice shift toggles
- **Power contract level**: Differentiated parameters based on contract power (≤3kW vs >3kW)

### Automated Data Sources
- **ARERA Excel files**: Quarterly updated tariff parameters automatically downloaded and parsed
- **Portale delle Offerte CSV**: Daily updated tax parameters and system charges
- **GME market data**: Hourly PUN prices for accurate calculations

### Automatic PUN Calculation
The integration supports a **PUN mode** option (selected during config flow or from the integration Options):
- **Calculated (default)** — PUN is retrieved/averaged by the integration from hourly GSE zonal prices and used to compute the bill (this is the original behavior).
- **Fixed** — PUN is taken from a fixed numeric value entered by the user (option `fixed_pun_value`, expressed in `€/kWh`). When set, the integration uses that fixed value for all PUN-dependent calculations.

---

## 📦 Requirements

- Home Assistant (modern versions; integration tested with 2025 era compatibility).
- Python libraries: `holidays`, `bs4` (BeautifulSoup4), `openpyxl`

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

### Configuration Steps

#### Step 1: Basic Energy Costs
- **Fixed quota - Aggregation measures** (€/month)
- **Monthly fee** (€/month)
- **PUN Mode**: Choose between calculated (from GME) or fixed value
- **Other fees** - Dispatching (€/kWh)

#### Step 2: House Type and Consumption Sensor
- **House type**: Residential or Non-residential
- **Monthly consumption sensor**: Select your energy consumption sensor
- **Zone** (for PUN calculations) if using calculated mode
- **Scan hour** for data updates

#### Step 3: Contract Details
- **Power in use** (kW) - Your contracted power level

#### Step 4: Taxes and Discounts
- **Discount** (€/month)
- **TV Tax** (€/month)

### Important Notes
- **ARERA and Portale delle Offerte parameters are now automatically retrieved** - no manual entry needed
- The integration will automatically download and update tariff parameters monthly
- **Monthly consumption sensor must provide `last_period` attribute** for bimonthly billing calculations

---

## 🔎 Exposed Entities

### Bolletta Device (Bill Calculation)
- `sensor.bill_energy_fix_quote` - Energy fixed quota
- `sensor.bill_energy_energy_quote` - Energy variable quota
- `sensor.bill_transport_fix_quote` - Transport fixed quota
- `sensor.bill_transport_power_quote` - Transport power quota
- `sensor.bill_transport_energy_quote` - Transport energy quota
- `sensor.bill_asos_arim_quote` - System charges (ASOS/ARIM)
- `sensor.bill_accisa_tax` - Excise tax
- `sensor.bill_iva` - VAT total
- `sensor.bill_total` - Total bill amount
- `sensor.bill_kwh_price` - Effective price per kWh

### PUN Device (National Single Price)
- `sensor.pun_mono_orario` - Current month hourly average
- `sensor.pun_mono_orario_mp` - Previous month hourly average
- `sensor.pun_fascia_f1` / `sensor.pun_fascia_f2` / `sensor.pun_fascia_f3` - Current month by tariff band
- `sensor.pun_fascia_f1_mp` / etc. - Previous month by tariff band
- `sensor.pun_fascia_corrente` - Current active tariff band
- `sensor.pun_prezzo_fascia_corrente` - Price for current tariff band
- `sensor.pun_prezzo_zonale` - Zonal price (current hour)
- `sensor.pun_orario` - Hourly PUN price

### ARERA Device (Regulatory Parameters)
- `sensor.arera_energy_sc1` - Energy quota Scaglione 1
- `sensor.arera_fix_quota_transport` - Transport fixed quota
- `sensor.arera_quota_power` - Power quota
- `sensor.arera_asos_sc1` - ASOS variable quota
- `sensor.arera_arim_sc1` - ARIM variable quota
- (Plus previous month variants for all parameters)

### PortaleOfferte Device (Tax Parameters)
- `sensor.portaleofferte_accisa_tax` - Excise tax rate
- `sensor.portaleofferte_iva` - VAT rate
- `sensor.portaleofferte_nw_loss_percentage` - Network loss percentage
- `sensor.portaleofferte_port_asos_sc1` - Portale ASOS rate
- `sensor.portaleofferte_port_arim_sc1` - Portale ARIM rate
- (Plus previous month variants for all parameters)

### Configuration Switches
- `switch.invoice_shift` - Toggle for shifting invoice cutoff
- `switch.invoice_monthly` - Toggle for monthly billing (vs bimonthly)

---

## 💡 Billing Period Configuration

The integration now supports flexible billing periods:

### Monthly Billing
- Enable the `invoice_monthly` switch
- Calculations use only current month consumption

### Bimonthly Billing (Default)
- Disable the `invoice_monthly` switch
- Calculations include current and previous month consumption
- Use `invoice_shift` to adjust which months are grouped together

### Invoice Shift
- The `invoice_shift` switch controls month pairing for bimonthly bills
- Shifted: Feb/Mar, Apr/May, etc.
- Non-shifted: Jan/Feb, Mar/Apr, etc.

---

## 🎯 Precision and Accuracy

**This integration has been tested against actual utility bills and matches calculations to the cent.** The improvements include:

- Proper rounding at each calculation step
- Accurate handling of bimonthly billing periods
- Correct application of tax rates and discounts
- Precise energy quota calculations based on real consumption data

---

## 🐞 Troubleshooting

- If sensors show `unknown` or errors:
- Check that `monthly_entity_sensor` exists and has numeric value and the `last_period` attribute.
- Check logs (**Settings → System → Logs**) for entries under `custom_components.bolletta`.
- If `last_period` is not present on the consumption sensor, the bi-monthly logic will not work—ensure the source sensor provides `last_period`.
- If ARERA or Portale delle Offerte data fails to download:
- The integration will retry automatically with exponential backoff
- Check your internet connection and firewall settings
- Parameters will use cached values until new data is available

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
