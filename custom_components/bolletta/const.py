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

# Tipi di aggiornamento
COORD_EVENT = "coordinator_event"

# Parametri configurabili da configuration.yaml
CONF_FIX_QUOTA_AGGR_MEASURE = "fix_quota_aggr_measure"
CONF_MONTHLY_FEE = "monthly_fee"
CONF_NW_LOSS_PERCENTAGE = "nw_loss_percentage"
CONF_OTHER_FEE = "other_fee"
CONF_FIX_QUOTA_TRANSPORT = "fix_quota_transport"
CONF_QUOTA_POWER = "quota_power"
CONF_POWER_IN_USE = "power_in_use"
CONF_ENERGY_SC1 = "energy_sc1"
CONF_ASOS_SC1 = "asos_sc1"
CONF_ASOS_SC2 = "asos_sc2"
CONF_ARIM_SC1 = "arim_sc1"
CONF_ARIM_SC2 = "arim_sc2"
CONF_ACCISA_TAX = "accisa_tax"
CONF_IVA = "iva"
CONF_DISCOUNT = "discount"
CONF_TV_TAX = "tv_tax"
CONF_MONTHY_ENTITY_SENSOR = "monthly_entity_sensor"
CONF_PUN_SENSOR = "pun_sensor"
CONF_PUN_MP_SENSOR = "pun_mp_sensor"
