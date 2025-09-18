from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util
from homeassistant.helpers.restore_state import (
    RestoreEntity,
    ExtraStoredData,
    RestoredExtraData
)
from typing import Any, Dict

from . import PUNDataUpdateCoordinator
from .const import (
    DOMAIN,
    BILL_ENERGY_FIX_QUOTE,
    BILL_ENERGY_ENERGY_QUOTE,
    BILL_TRANSPORT_FIX_QUOTE,
    BILL_TRANSPORT_POWER_QUOTE,
    BILL_TRANSPORT_ENERGY_QUOTE,
    BILL_ASOS_ARIM_QUOTE,
    BILL_ACCISA_TAX,
    BILL_IVA,
    BILL_TOTAL,
)

from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
ATTR_ROUNDED_DECIMALS = "rounded_decimals"

bill_total_energy_fix_quote = 0
bill_total_energy_energy_quote = 0
bill_total_transport_fix_quote = 0
bill_total_transport_power_quote = 0
bill_total_transport_energy_quote = 0
bill_total_asos_arim_quote = 0
bill_total_accisa_tax = 0
bill_total_iva = 0

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None) -> None:
    """Inizializza e crea i sensori"""

    # Restituisce il coordinator
    coordinator = hass.data[DOMAIN][config.entry_id]

    # Verifica la versione di Home Assistant
    global has_suggested_display_precision
    has_suggested_display_precision = (AwesomeVersion(HA_VERSION) >= AwesomeVersion("2023.3.0"))

    # Crea i sensori (legati al coordinator)
    entities = []
    
    entities.append(BillSensorEntity(coordinator, BILL_ENERGY_FIX_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_ENERGY_ENERGY_QUOTE))

    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_FIX_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_POWER_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_ENERGY_QUOTE))

    entities.append(BillSensorEntity(coordinator, BILL_ASOS_ARIM_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_ACCISA_TAX))

    entities.append(BillSensorEntity(coordinator, BILL_IVA))
    entities.append(BillSensorEntity(coordinator, BILL_TOTAL))

    # Aggiunge i sensori ma non aggiorna automaticamente via web
    # per lasciare il tempo ad Home Assistant di avviarsi
    async_add_entities(entities, update_before_add=False)


def decode_fascia(fascia: int) -> str | None:
    if fascia == 3:
        return "F3"
    elif fascia == 2:
        return "F2"
    elif fascia == 1:
        return "F1"
    else:
        return None


def fmt_float(num: float):
    """Formatta adeguatamente il numero decimale"""
    if has_suggested_display_precision:
        return num
    
    # In versioni precedenti di Home Assistant che non supportano
    # l'attributo 'suggested_display_precision' restituisce il numero
    # decimale già adeguatamente formattato come stringa
    return format(round(num, 6), '.6f')

class BillSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore relativo alla fattura"""
    
    def __init__(self, coordinator: PUNDataUpdateCoordinator, tipo: int) -> None:
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator
        self.tipo = tipo

        # ID univoco sensore basato su un nome fisso
        if (self.tipo == BILL_ENERGY_FIX_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_energy_fix_quote')
        elif (self.tipo == BILL_ENERGY_ENERGY_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_energy_energy_quote')
        elif (self.tipo == BILL_TRANSPORT_FIX_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_transport_fix_quote')
        elif (self.tipo == BILL_TRANSPORT_POWER_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_transport_power_quote')
        elif (self.tipo == BILL_TRANSPORT_ENERGY_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_transport_energy_quote')
        elif (self.tipo == BILL_ASOS_ARIM_QUOTE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_asos_arim_quote')
        elif (self.tipo == BILL_ACCISA_TAX):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_accisa_tax')
        elif (self.tipo == BILL_IVA):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_iva')
        elif (self.tipo == BILL_TOTAL):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_total')
        else:
            self.entity_id = None
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = True

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_suggested_display_precision = 2
        self._available = False
        self._native_value = 0
        
    def manage_update(self):
        global bill_total_energy_fix_quote
        global bill_total_energy_energy_quote
        global bill_total_transport_fix_quote
        global bill_total_transport_power_quote
        global bill_total_transport_energy_quote
        global bill_total_asos_arim_quote
        global bill_total_accisa_tax
        global bill_total_iva

        if self.tipo==BILL_ENERGY_FIX_QUOTE:  
            total = round(self.coordinator.fix_quota_aggr_measure * 2 + self.coordinator.monthly_fee * 2,2)

            self._available = True
            self._native_value = total
            bill_total_energy_fix_quote = total
            self.async_write_ha_state()
        elif self.tipo==BILL_ENERGY_ENERGY_QUOTE:  
            current_month = dt_util.now().date().month
            
            total = 0
            total = float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * ((1 + float(self.coordinator.nw_loss_percentage)/100) *  float(self.hass.states.get(self.coordinator.pun_sensor).state) + float(self.coordinator.other_fee))
            if (current_month % 2) == 0:
                total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * ((1 + float(self.coordinator.nw_loss_percentage)/100) *  float(self.hass.states.get(self.coordinator.pun_mp_sensor).state) + float(self.coordinator.other_fee))
                
            self._available = True
            self._native_value = total
            bill_total_energy_energy_quote = total
            self.async_write_ha_state()
        elif self.tipo==BILL_TRANSPORT_FIX_QUOTE:  
            total = 0
            total = self.coordinator.fix_quota_transport * 2
            self._available = True
            self._native_value = total
            bill_total_transport_fix_quote = total
            self.async_write_ha_state()
        elif self.tipo==BILL_TRANSPORT_POWER_QUOTE:  
            total = 0
            total = self.coordinator.quota_power * self.coordinator.power_in_use * 2
            self._available = True
            self._native_value = total
            bill_total_transport_power_quote = total
            self.async_write_ha_state()
        elif self.tipo==BILL_TRANSPORT_ENERGY_QUOTE:  
            current_month = dt_util.now().date().month

            total = 0
            total = float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.energy_sc1
            if (current_month % 2) == 0:
                total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.energy_sc1
            self._available = True
            self._native_value = total
            bill_total_transport_energy_quote = total
            self.async_write_ha_state()




        elif self.tipo==BILL_ASOS_ARIM_QUOTE:  
            current_month = dt_util.now().date().month

            total = 0
            total = float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.asos_sc1
            # total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.asos_sc2
            total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.arim_sc1
            # total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.arim_sc2
            if (current_month % 2) == 0:
                total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.asos_sc1
                # total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.asos_sc2
                total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.arim_sc1
                # total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.arim_sc2
            self._available = True
            self._native_value = total
            bill_total_asos_arim_quote = total
            self.async_write_ha_state()

        elif self.tipo==BILL_ACCISA_TAX:  
            current_month = dt_util.now().date().month

            total = 0
            total = float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.accisa_tax
            if (current_month % 2) == 0:
                total += float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.accisa_tax
            self._available = True
            self._native_value = total
            bill_total_accisa_tax = total
            self.async_write_ha_state()

        elif self.tipo==BILL_IVA:  
            total = round(float(bill_total_energy_fix_quote),2)
            total += round(float(bill_total_energy_energy_quote),2)
            total += round(float(bill_total_transport_fix_quote),2)
            total += round(float(bill_total_transport_power_quote),2)
            total += round(float(bill_total_transport_energy_quote),2)
            total += round(float(bill_total_asos_arim_quote),2)
            total += round(float(bill_total_accisa_tax),2)
            
            total = total * float(self.coordinator.iva)/100
            self._available = True
            self._native_value = total
            bill_total_iva = total
            self.async_write_ha_state()

        elif self.tipo==BILL_TOTAL:  
            current_month = dt_util.now().date().month
            
            total = round(float(bill_total_energy_fix_quote),2)
            total += round(float(bill_total_energy_energy_quote),2)
            total += round(float(bill_total_transport_fix_quote),2)
            total += round(float(bill_total_transport_power_quote),2)
            total += round(float(bill_total_transport_energy_quote),2)
            total += round(float(bill_total_asos_arim_quote),2)
            total += round(float(bill_total_accisa_tax),2)
            total += round(float(bill_total_iva),2)
            total -= round(float(self.coordinator.discount),2)*2
            if current_month!=11 and current_month!=12:
                total += round(float(self.coordinator.tv_tax),2)*2
            self._available = True
            self._native_value = total
            self.async_write_ha_state()

    async def async_update(self):
        self.manage_update()
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator"""
        self.manage_update()
        

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Determina i dati da salvare per il ripristino successivo"""
        return RestoredExtraData(dict(
            native_value = self._native_value if self._available else None
        ))
    
    async def async_added_to_hass(self) -> None:
        """Entità aggiunta ad Home Assistant"""
        await super().async_added_to_hass()

        # Recupera lo stato precedente, se esiste        
        if (old_data := await self.async_get_last_extra_data()) is not None:
            if (old_native_value := old_data.as_dict().get('native_value')) is not None:
                self._available = True
                self._native_value = old_native_value

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico"""
        return True

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile"""
        return self._available

    @property
    def native_value(self) -> float:
        """Valore corrente del sensore"""
        return self._native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unita' di misura"""
        return f"{CURRENCY_EURO}"
            
    @property
    def state(self) -> str:
        return fmt_float(self.native_value)

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend"""
        return "mdi:currency-eur"

    @property
    def name(self) -> str:
        """Restituisce il nome del sensore"""
        if (self.tipo == BILL_ENERGY_FIX_QUOTE):
            return "Bolletta - Spesa per l'energia - Quota fissa"
        elif (self.tipo == BILL_ENERGY_ENERGY_QUOTE):
            return "Bolletta - Spesa per l'energia - Quota energia"
        elif (self.tipo == BILL_TRANSPORT_FIX_QUOTE):
            return "Bolletta - Spesa per il trasporto e contatore - Quota fissa"
        elif (self.tipo == BILL_TRANSPORT_POWER_QUOTE):
            return "Bolletta - Spesa per il trasporto e contatore - Quota potenza"
        elif (self.tipo == BILL_TRANSPORT_ENERGY_QUOTE):
            return "Bolletta - Spesa per il trasporto e contatore - Quota energia"
        elif (self.tipo == BILL_ASOS_ARIM_QUOTE):
            return "Bolletta - Spesa per gli oneri di sistema"
        elif (self.tipo == BILL_ACCISA_TAX):
            return "Bolletta - Imposta erariale di consumo - Accisa"
        elif (self.tipo == BILL_IVA):
            return "Bolletta - Totale IVA"
        elif (self.tipo == BILL_TOTAL):
            return "Bolletta - Totale Fattura"
        else:
            return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Restituisce gli attributi di stato"""
        if has_suggested_display_precision:
            return None
        
        # Nelle versioni precedenti di Home Assistant
        # restituisce un valore arrotondato come attributo
        state_attr = {
            ATTR_ROUNDED_DECIMALS: str(format(round(self.native_value, 3), '.3f'))
        }
        return state_attr


