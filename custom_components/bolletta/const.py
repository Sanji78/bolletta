from enum import StrEnum

# Dominio HomeAssistant
DOMAIN = "bolletta"

BILL_ENERGY_FIX_QUOTE = 1
BILL_ENERGY_ENERGY_QUOTE = 2
BILL_TRANSPORT_FIX_QUOTE = 3
BILL_TRANSPORT_POWER_QUOTE = 4
BILL_TRANSPORT_ENERGY_QUOTE = 5
BILL_ASOS_ARIM_QUOTE = 6
BILL_ACCISA_TAX = 7
BILL_IVA = 8
BILL_TOTAL = 9
BILL_KWH_PRICE = 10

# Parametri configurabili
CONF_FIX_QUOTA_AGGR_MEASURE = "fix_quota_aggr_measure"
CONF_MONTHLY_FEE = "monthly_fee"
CONF_NW_LOSS_PERCENTAGE = "nw_loss_percentage"
CONF_OTHER_FEE = "other_fee"
CONF_POWER_IN_USE = "power_in_use"
CONF_ACCISA_TAX = "accisa_tax"
CONF_IVA = "iva"
CONF_DISCOUNT = "discount"
CONF_TV_TAX = "tv_tax"
CONF_MONTHY_ENTITY_SENSOR = "monthly_entity_sensor"
CONF_PUN_SENSOR = "pun_sensor"
CONF_PUN_MP_SENSOR = "pun_mp_sensor"

# Parametri di ARERA
CONF_ENERGY_SC1 = "energy_sc1"
CONF_ENERGY_SC1_MP = "energy_sc1_mp"
CONF_FIX_QUOTA_TRANSPORT = "fix_quota_transport"
CONF_FIX_QUOTA_TRANSPORT_MP = "fix_quota_transport_mp"
CONF_QUOTA_POWER = "quota_power"
CONF_QUOTA_POWER_MP = "quota_power_mp"
CONF_ASOS_SC1 = "asos_sc1"
CONF_ASOS_SC1_MP = "asos_sc1_mp"
CONF_ARIM_SC1 = "arim_sc1"
CONF_ARIM_SC1_MP = "arim_sc1_mp"


# Tipi di sensore da creare
PUN_FASCIA_MONO = 0
PUN_FASCIA_F1 = 1
PUN_FASCIA_F2 = 2
PUN_FASCIA_F3 = 3
PUN_FASCIA_F23 = 4

# Intervalli di tempo per i tentativi
WEB_RETRIES_MINUTES = [1, 10, 60, 120, 180]

# Tipi di aggiornamento
COORD_EVENT = "coordinator_event"
EVENT_UPDATE_FASCIA = "event_update_fascia"
EVENT_UPDATE_PUN = "event_update_pun"
EVENT_UPDATE_PREZZO_ZONALE = "event_update_prezzo_zonale"
EVENT_UPDATE_ARERA = "event_update_arera"

# Parametri configurabili da configuration.yaml
CONF_SCAN_HOUR = "scan_hour"
CONF_ZONA = "zona"

# Parametri interni
CONF_SCAN_MINUTE = "scan_minute"

# Modalità di utilizzo PUN
CONF_PUN_MODE = "pun_mode"
CONF_FIXED_PUN_VALUE = "fixed_pun_value"
PUN_MODE_CALCULATED = "calculated"
PUN_MODE_FIXED = "fixed"

# Abitazione
CONF_HOUSE_TYPE = "house_type"
RESIDENTIAL = "residential"
NOT_RESIDENTIAL = "not_residential"
HOUSE_TYPE_LABELS = {
    RESIDENTIAL: "Abitazioni di residenza anagrafica",
    NOT_RESIDENTIAL: "Abitazioni diverse dalla residenza anagrafica",
}