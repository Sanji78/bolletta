import logging
from typing import Any

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
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval

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
    BILL_KWH_PRICE,
    COORD_EVENT,
    DOMAIN,
    EVENT_UPDATE_FASCIA,
    EVENT_UPDATE_PREZZO_ZONALE,
    EVENT_UPDATE_PUN,
    PUN_MODE_FIXED,
    CONF_ENERGY_SC1,
    CONF_ENERGY_SC1_MP,
    CONF_FIX_QUOTA_TRANSPORT,
    CONF_FIX_QUOTA_TRANSPORT_MP,
    CONF_QUOTA_POWER,
    CONF_QUOTA_POWER_MP,
    CONF_ASOS_SC1,
    CONF_ASOS_SC1_MP,
    CONF_ARIM_SC1,
    CONF_ARIM_SC1_MP,
)

from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy, __version__ as HA_VERSION
from .interfaces import Fascia, PunValues, PunValuesMP
from .utils import datetime_to_packed_string, get_next_date

ATTR_ROUNDED_DECIMALS = "rounded_decimals"
bill_total_energy_fix_quote = 0
bill_total_energy_energy_quote = 0
bill_total_transport_fix_quote = 0
bill_total_transport_power_quote = 0
bill_total_transport_energy_quote = 0
bill_total_asos_arim_quote = 0
bill_total_accisa_tax = 0
bill_total_iva = 0
bill_kwh_price = 0
ATTR_PREFIX_PREZZO_OGGI = "oggi_h_"
ATTR_PREFIX_PREZZO_DOMANI = "domani_h_"

# Ottiene il logger
_LOGGER = logging.getLogger(__name__)

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
    entities: list[SensorEntity] = []
    
    entities.append(BillSensorEntity(coordinator, BILL_ENERGY_FIX_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_ENERGY_ENERGY_QUOTE))

    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_FIX_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_POWER_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_TRANSPORT_ENERGY_QUOTE))

    entities.append(BillSensorEntity(coordinator, BILL_ASOS_ARIM_QUOTE))
    entities.append(BillSensorEntity(coordinator, BILL_ACCISA_TAX))

    entities.append(BillSensorEntity(coordinator, BILL_IVA))
    entities.append(BillSensorEntity(coordinator, BILL_TOTAL))
    entities.append(BillSensorEntity(coordinator, BILL_KWH_PRICE))
    
    entities.extend(
        PUNSensorEntity(coordinator, fascia) for fascia in PunValues().value
    )
    entities.extend(
        PUNSensorEntity(coordinator, fascia) for fascia in PunValuesMP().value
    )

    # ARERA sensors - grouped under different device
    entities.append(AreraSensorEntity(coordinator, CONF_ENERGY_SC1))
    entities.append(AreraSensorEntity(coordinator, CONF_ENERGY_SC1_MP))
    entities.append(AreraSensorEntity(coordinator, CONF_FIX_QUOTA_TRANSPORT))
    entities.append(AreraSensorEntity(coordinator, CONF_FIX_QUOTA_TRANSPORT_MP))
    entities.append(AreraSensorEntity(coordinator, CONF_QUOTA_POWER))
    entities.append(AreraSensorEntity(coordinator, CONF_QUOTA_POWER_MP))
    entities.append(AreraSensorEntity(coordinator, CONF_ASOS_SC1))
    entities.append(AreraSensorEntity(coordinator, CONF_ASOS_SC1_MP))
    entities.append(AreraSensorEntity(coordinator, CONF_ARIM_SC1))
    entities.append(AreraSensorEntity(coordinator, CONF_ARIM_SC1_MP))

    # PortaleOfferte sensors - grouped under different device
    entities.append(PortaleOfferteSensorEntity(coordinator, "accisa_tax"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "accisa_tax_mp"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "iva"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "iva_mp"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "nw_loss_percentage"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "nw_loss_percentage_mp"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "port_asos_sc1"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "port_asos_sc1_mp"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "port_arim_sc1"))
    entities.append(PortaleOfferteSensorEntity(coordinator, "port_arim_sc1_mp"))

    # Crea sensori aggiuntivi
    entities.append(FasciaPUNSensorEntity(coordinator))
    entities.append(PrezzoFasciaPUNSensorEntity(coordinator))
    entities.append(PrezzoZonaleSensorEntity(coordinator))
    entities.append(PUNOrarioSensorEntity(coordinator))

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

from homeassistant.components.binary_sensor import BinarySensorEntity

class PortaleOfferteSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore per i parametri provenienti da ilportaleofferte."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator, tipo: str) -> None:
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator
        self.tipo = tipo

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format(f"portaleofferte_{tipo}")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_suggested_display_precision = 6
        self._available = False
        self._native_value = 0.0

    @property
    def device_info(self):
        """Return device information for PortaleOfferte parameters."""
        return {
            "identifiers": {(DOMAIN, "portale_offerte_parameters")},
            "name": "Parametri IlPortaleOfferte",
            "manufacturer": "IlPortaleOfferte",
            "model": "Parametri Opendata",
        }

    def manage_update(self):
        """Aggiorna il valore leggendo gli attributi dal coordinator."""
        try:
            if self.tipo == "accisa_tax":
                self._native_value = float(getattr(self.coordinator, "accisa_tax", 0.0) or 0.0)
            elif self.tipo == "accisa_tax_mp":
                self._native_value = float(getattr(self.coordinator, "accisa_tax_mp", 0.0) or 0.0)
            elif self.tipo == "iva":
                self._native_value = float(getattr(self.coordinator, "iva", 0.0) or 0.0)
            elif self.tipo == "iva_mp":
                self._native_value = float(getattr(self.coordinator, "iva_mp", 0.0) or 0.0)
            elif self.tipo == "nw_loss_percentage":
                self._native_value = float(getattr(self.coordinator, "nw_loss_percentage", 0.0) or 0.0)
            elif self.tipo == "nw_loss_percentage_mp":
                self._native_value = float(getattr(self.coordinator, "nw_loss_percentage_mp", 0.0) or 0.0)
            elif self.tipo == "port_asos_sc1":
                self._native_value = float(getattr(self.coordinator, "port_asos_sc1", 0.0) or 0.0)
            elif self.tipo == "port_asos_sc1_mp":
                self._native_value = float(getattr(self.coordinator, "port_asos_sc1_mp", 0.0) or 0.0)
            elif self.tipo == "port_arim_sc1":
                self._native_value = float(getattr(self.coordinator, "port_arim_sc1", 0.0) or 0.0)
            elif self.tipo == "port_arim_sc1_mp":
                self._native_value = float(getattr(self.coordinator, "port_arim_sc1_mp", 0.0) or 0.0)
            else:
                # Unknown tipo -> do nothing
                return

            self._available = True
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"Errore nell'aggiornamento del sensore PortaleOfferte {self.tipo}: {e}")
            self._available = False

    async def async_update(self):
        self.manage_update()

    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""
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
        """Unita' di misura specifica per il parametro PortaleOfferte."""
        # Parametri che sono percentuali
        percent_keys = {"iva", "iva_mp", "nw_loss_percentage", "nw_loss_percentage_mp"}

        # Parametri espressi in euro per kWh (valori variabili/energia)
        eur_per_kwh_keys = {
            "accisa_tax",
            "accisa_tax_mp",
            "port_asos_sc1",
            "port_asos_sc1_mp",
            "port_arim_sc1",
            "port_arim_sc1_mp",
        }

        if self.tipo in percent_keys:
            return "%"  # percentuale
        if self.tipo in eur_per_kwh_keys:
            return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
        # fallback: string describing the parameter
        return self.tipo


    @property
    def state(self) -> str:
        # Parametri che sono percentuali
        percent_keys = {"iva", "iva_mp", "nw_loss_percentage", "nw_loss_percentage_mp"}

        # Parametri espressi in euro per kWh (valori variabili/energia)
        eur_per_kwh_keys = {
            "accisa_tax",
            "accisa_tax_mp",
            "port_asos_sc1",
            "port_asos_sc1_mp",
            "port_arim_sc1",
            "port_arim_sc1_mp",
        }

        if self.tipo in percent_keys:
            return fmt_float(self.native_value) * 100
        if self.tipo in eur_per_kwh_keys:
            return fmt_float(self.native_value)
        # fallback: string describing the parameter
        return self.tipo

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend"""
        return "mdi:chart-line-variant"

    @property
    def name(self) -> str:
        """Restituisce il nome del sensore"""
        names = {
            "accisa_tax": "Imposta erariale di consumo (accisa)",
            "accisa_tax_mp": "Imposta erariale di consumo (accisa) Mese Precedente",
            "iva": "IVA",
            "iva_mp": "IVA Mese Precedente",
            "nw_loss_percentage": "Perdite di rete in percentuale",
            "nw_loss_percentage_mp": "Perdite di rete in percentuale Mese Precedente",
            "port_asos_sc1": "ASOS",
            "port_asos_sc1_mp": "ASOS Mese Precedente",
            "port_arim_sc1": "ARIM",
            "port_arim_sc1_mp": "ARIM Mese Precedente",
        }
        return names.get(self.tipo, f"PortaleOfferte {self.tipo}")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Restituisce gli attributi di stato"""
        if has_suggested_display_precision:
            return None

        state_attr = {
            ATTR_ROUNDED_DECIMALS: str(format(round(self.native_value, 6), '.6f'))
        }
        return state_attr


class AreraSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore per i parametri ARERA"""
    
    def __init__(self, coordinator: PUNDataUpdateCoordinator, tipo: str) -> None:
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator
        self.tipo = tipo

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format(f"arera_{tipo}")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_suggested_display_precision = 6
        self._available = False
        self._native_value = 0

    @property
    def device_info(self):
        """Return device information for ARERA parameters."""
        return {
            "identifiers": {(DOMAIN, "arera_parameters")},
            "name": "Parametri Arera",
            "manufacturer": "Arera",
            "model": "Parametri Tariffari Arera",
        }
        
    def manage_update(self):
        """Gestisce l'aggiornamento dei valori ARERA"""
        try:
            if self.tipo == CONF_ENERGY_SC1:
                self._native_value = self.coordinator.energy_sc1
            elif self.tipo == CONF_ENERGY_SC1_MP:
                self._native_value = self.coordinator.energy_sc1_mp
            elif self.tipo == CONF_FIX_QUOTA_TRANSPORT:
                self._native_value = self.coordinator.fix_quota_transport
            elif self.tipo == CONF_FIX_QUOTA_TRANSPORT_MP:
                self._native_value = self.coordinator.fix_quota_transport_mp
            elif self.tipo == CONF_QUOTA_POWER:
                self._native_value = self.coordinator.quota_power
            elif self.tipo == CONF_QUOTA_POWER_MP:
                self._native_value = self.coordinator.quota_power_mp
            elif self.tipo == CONF_ASOS_SC1:
                self._native_value = self.coordinator.asos_sc1
            elif self.tipo == CONF_ASOS_SC1_MP:
                self._native_value = self.coordinator.asos_sc1_mp
            elif self.tipo == CONF_ARIM_SC1:
                self._native_value = self.coordinator.arim_sc1
            elif self.tipo == CONF_ARIM_SC1_MP:
                self._native_value = self.coordinator.arim_sc1_mp
            else:
                return
            
            self._available = True
            self.async_write_ha_state()
            
        except Exception as e:
            _LOGGER.error(f"Errore nell'aggiornamento del sensore ARERA {self.tipo}: {e}")
            self._available = False
        
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
        return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"

    @property
    def native_unit_of_measurement(self) -> str:
        eur_per_month_keys = {"fix_quota_transport", "fix_quota_transport_mp"}
        eur_per_kwh_per_month_keys = {"quota_power", "quota_power_mp"}

        # Parametri espressi in euro per kWh (valori variabili/energia)
        eur_per_kwh_keys = {
            "energy_sc1",
            "energy_sc1_mp",
            "asos_sc1",
            "asos_sc1_mp",
            "arim_sc1",
            "arim_sc1_mp",
        }

        if self.tipo in eur_per_month_keys:
            return f"{CURRENCY_EURO}/mese"
        if self.tipo in eur_per_kwh_per_month_keys:
            return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}/mese"
        if self.tipo in eur_per_kwh_keys:
            return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
        # fallback: string describing the parameter
        return self.tipo


    @property
    def state(self) -> str:
        return fmt_float(self.native_value)

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend"""
        return "mdi:chart-line"

    @property
    def name(self) -> str:
        """Restituisce il nome del sensore"""
        names = {
            CONF_ENERGY_SC1: "Quota energia",
            CONF_ENERGY_SC1_MP: "Quota energia Mese Precedente",
            CONF_FIX_QUOTA_TRANSPORT: "Quota Fissa Trasporto",
            CONF_FIX_QUOTA_TRANSPORT_MP: "Quota Fissa Trasporto Mese Precedente",
            CONF_QUOTA_POWER: "Quota Potenza",
            CONF_QUOTA_POWER_MP: "Quota Potenza Mese Precedente",
            CONF_ASOS_SC1: "ASOS",
            CONF_ASOS_SC1_MP: "ASOS Mese Precedente",
            CONF_ARIM_SC1: "ARIM",
            CONF_ARIM_SC1_MP: "ARIM Mese Precedente",
        }
        return names.get(self.tipo, "Parametro Arera")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Restituisce gli attributi di stato"""
        if has_suggested_display_precision:
            return None
        
        # Nelle versioni precedenti di Home Assistant
        # restituisce un valore arrotondato come attributo
        state_attr = {
            ATTR_ROUNDED_DECIMALS: str(format(round(self.native_value, 6), '.6f'))
        }
        return state_attr
        
class BillSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore relativo alla fattura"""
    
    def __init__(self, coordinator: PUNDataUpdateCoordinator, tipo: int) -> None:
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator
        self.tipo = tipo

        # ID univoco sensore basato su un nome fisso
        if (self.tipo == BILL_KWH_PRICE):
            self.entity_id = ENTITY_ID_FORMAT.format('bill_kwh_price')
        elif (self.tipo == BILL_ENERGY_FIX_QUOTE):
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
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_suggested_display_precision = 2
        self._available = False
        self._native_value = 0

    @property
    def device_info(self):
        """Return device information for Bolletta."""
        return {
            "identifiers": {(DOMAIN, "bolletta")},
            "name": "Monitor Costi Energia",
            "manufacturer": "Bolletta",
            "model": "Calcolo della Bolletta Elettrica",
        }
        
    def manage_update(self):
        global bill_total_energy_fix_quote
        global bill_total_energy_energy_quote
        global bill_total_transport_fix_quote
        global bill_total_transport_power_quote
        global bill_total_transport_energy_quote
        global bill_total_asos_arim_quote
        global bill_total_accisa_tax
        global bill_total_iva
        global bill_kwh_price
        
        fattura_shift = self.hass.states.get("switch.invoice_shift")
        fattura_mensile = self.hass.states.get("switch.invoice_monthly")

        shift_on = fattura_shift and fattura_shift.state == "on"
        monthly = fattura_mensile and fattura_mensile.state == "on"
        current_month = dt_util.now().date().month

        if monthly:
            # fatturazione mese singolo → non sommare mai last_period
            include_last_period = False
        else:
            # bimestrale
            if shift_on:
                include_last_period = (current_month % 2) == 1   # Feb/Mar, Apr/Mag…
            else:
                include_last_period = (current_month % 2) == 0   # Gen/Feb, Mar/Apr…


        if self.tipo==BILL_KWH_PRICE:  
            try:
                if self.coordinator.pun_mode == PUN_MODE_FIXED:
                    pun_value = self.coordinator.fixed_pun_value
                    total = round(float(pun_value) , 2)
                    total += round((float(self.coordinator.nw_loss_percentage)/100) *  float(pun_value) , 2)
                    total += round(float(self.coordinator.other_fee) , 2)
                else:
                    total = round(float(self.hass.states.get('sensor.pun_mono_orario').state) , 2)
                    total += round((float(self.coordinator.nw_loss_percentage)/100) *  float(self.hass.states.get('sensor.pun_mono_orario').state) , 2)
                    total += round(float(self.coordinator.other_fee) , 2)
                            
                total += round(self.coordinator.energy_sc1 , 2)
                total += round(self.coordinator.asos_sc1 , 2)
                total += round(self.coordinator.arim_sc1 , 2)
                total += round(self.coordinator.accisa_tax , 2)

                self._available = True
                self._native_value = total
                bill_kwh_price = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_ENERGY_FIX_QUOTE:  
            try:
                total = round(self.coordinator.fix_quota_aggr_measure ,2) + round(self.coordinator.monthly_fee ,2)
                if include_last_period:
                    total += round(self.coordinator.fix_quota_aggr_measure ,2) + round(self.coordinator.monthly_fee ,2)

                self._available = True
                self._native_value = total
                bill_total_energy_fix_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_ENERGY_ENERGY_QUOTE:  
            try:
                total = 0

                if self.coordinator.pun_mode == PUN_MODE_FIXED:
                    pun_value = self.coordinator.fixed_pun_value
                    total = round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) *  float(pun_value), 2)
                    total = float(f"{total:.2f}")
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * ((float(self.coordinator.nw_loss_percentage)) *  float(pun_value)), 2)
                    total = float(f"{total:.2f}")
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * ((float(self.coordinator.other_fee))), 2)
                    total = float(f"{total:.2f}")
                    if include_last_period:
                        total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) *  float(pun_value), 2)
                        total = float(f"{total:.2f}")
                        total += round((float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * ((float(self.coordinator.nw_loss_percentage)) *  float(pun_value))), 2)
                        total = float(f"{total:.2f}")
                        total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * ((float(self.coordinator.other_fee))), 2)
                        total = float(f"{total:.2f}")
                else:
                    total = round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) *  float(self.hass.states.get('sensor.pun_mono_orario').state), 2)
                    total = float(f"{total:.2f}")
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * ((float(self.coordinator.nw_loss_percentage)) *  float(self.hass.states.get('sensor.pun_mono_orario').state)), 2)
                    total = float(f"{total:.2f}")
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * ((float(self.coordinator.other_fee))), 2)
                    total = float(f"{total:.2f}")
                    if include_last_period:
                        total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) *  float(self.hass.states.get('sensor.pun_mono_orario_mp').state) , 2)
                        total = float(f"{total:.2f}")
                        total += round((float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * ((float(self.coordinator.nw_loss_percentage)) *  float(self.hass.states.get('sensor.pun_mono_orario_mp').state))), 2)
                        total = float(f"{total:.2f}")
                        total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * ((float(self.coordinator.other_fee))), 2)
                        total = float(f"{total:.2f}")
                     
                self._available = True
                self._native_value = total
                bill_total_energy_energy_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_TRANSPORT_FIX_QUOTE:  
            try:
                total = 0
                total = round(self.coordinator.fix_quota_transport,2)
                if include_last_period:
                    total += round(self.coordinator.fix_quota_transport_mp,2)
                self._available = True
                self._native_value = total
                bill_total_transport_fix_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_TRANSPORT_POWER_QUOTE:  
            try:
                total = 0
                total = round((self.coordinator.quota_power) * self.coordinator.power_in_use,2)
                if include_last_period:
                    total += round((self.coordinator.quota_power_mp) * self.coordinator.power_in_use,2)
                self._available = True
                self._native_value = total
                bill_total_transport_power_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_TRANSPORT_ENERGY_QUOTE:  
            try:
                total = 0
                total = round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.energy_sc1,2)
                if include_last_period:
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.energy_sc1_mp,2)
                self._available = True
                self._native_value = total
                bill_total_transport_energy_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_ASOS_ARIM_QUOTE:  
            try:
                total = 0
                total = round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.asos_sc1,2)
                total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.arim_sc1,2)
                if include_last_period:
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.asos_sc1_mp,2)
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.arim_sc1_mp,2)
                self._available = True
                self._native_value = total
                bill_total_asos_arim_quote = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_ACCISA_TAX:  
            try:
                total = 0
                total = round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).state) * self.coordinator.accisa_tax,2)
                if include_last_period:
                    total += round(float(self.hass.states.get(self.coordinator.monthly_entity_sensor).attributes['last_period']) * self.coordinator.accisa_tax,2)
                self._available = True
                self._native_value = total
                bill_total_accisa_tax = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_IVA:  
            try:
                total = round(float(bill_total_energy_fix_quote),2)
                total += round(float(bill_total_energy_energy_quote),2)
                total += round(float(bill_total_transport_fix_quote),2)
                total += round(float(bill_total_transport_power_quote),2)
                total += round(float(bill_total_transport_energy_quote),2)
                total += round(float(bill_total_asos_arim_quote),2)
                total += round(float(bill_total_accisa_tax),2)
                total -= round(float(self.coordinator.discount),2)*2
                
                total = total * float(self.coordinator.iva)
                self._available = True
                self._native_value = total
                bill_total_iva = total
                self.async_write_ha_state()
            except:
                self._available = False
                self.async_write_ha_state()                
        elif self.tipo==BILL_TOTAL:  
            try:
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
            except:
                self._available = False
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

        # async def _periodic_update(now):
            # self.manage_update()

        # async_track_time_interval(self.hass, _periodic_update, timedelta(seconds=3))
        
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
        if (self.tipo == BILL_KWH_PRICE):
            return "Prezzo del KWh"
        elif (self.tipo == BILL_ENERGY_FIX_QUOTE):
            return "Spesa per l'energia - Quota fissa"
        elif (self.tipo == BILL_ENERGY_ENERGY_QUOTE):
            return "Spesa per l'energia - Quota energia"
        elif (self.tipo == BILL_TRANSPORT_FIX_QUOTE):
            return "Spesa per il trasporto e contatore - Quota fissa"
        elif (self.tipo == BILL_TRANSPORT_POWER_QUOTE):
            return "Spesa per il trasporto e contatore - Quota potenza"
        elif (self.tipo == BILL_TRANSPORT_ENERGY_QUOTE):
            return "Spesa per il trasporto e contatore - Quota energia"
        elif (self.tipo == BILL_ASOS_ARIM_QUOTE):
            return "Spesa per gli oneri di sistema"
        elif (self.tipo == BILL_ACCISA_TAX):
            return "Imposta erariale di consumo - Accisa"
        elif (self.tipo == BILL_IVA):
            return "Totale IVA"
        elif (self.tipo == BILL_TOTAL):
            return "Totale Fattura"
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

class PUNSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore PUN relativo al prezzo medio mensile per fasce."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator, fascia: Fascia) -> None:
        """Inizializza il sensore."""
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator
        self.fascia = fascia

        # ID univoco sensore basato su un nome fisso
        match self.fascia:
            case Fascia.MONO:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_mono_orario")
            case Fascia.F1:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f1")
            case Fascia.F2:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f2")
            case Fascia.F3:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f3")
            case Fascia.F23:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f23")
            case Fascia.MONO_MP:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_mono_orario_mp")
            case Fascia.F1_MP:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f1_mp")
            case Fascia.F2_MP:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f2_mp")
            case Fascia.F3_MP:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f3_mp")
            case Fascia.F23_MP:
                self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_f23_mp")
            case _:
                self.entity_id = None
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 6
        self._available = False
        self._native_value = 0

    @property
    def device_info(self):
        """Return device information for PUN parameters."""
        return {
            "identifiers": {(DOMAIN, "PUN")},
            "name": "Prezzo Unico Nazionale (PUN)",
            "manufacturer": "Gestore Mercati Energetici",
            "model": "Dati PUN in Tempo Reale",
        }
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""

        # Identifica l'evento che ha scatenato l'aggiornamento
        if self.coordinator.data is None:
            return
        if (coordinator_event := self.coordinator.data.get(COORD_EVENT)) is None:
            return

        # Aggiorna il sensore in caso di variazione di prezzi
        if coordinator_event != EVENT_UPDATE_PUN:
            return

        if self.fascia != Fascia.F23 and self.fascia != Fascia.F23_MP:
            # Tutte le fasce tranne F23
            if "_MP" not in self.fascia.value:
                if len(self.coordinator.pun_data.pun[self.fascia]) > 0:
                    # Ci sono dati, sensore disponibile
                    self._available = True
                    self._native_value = self.coordinator.pun_values.value[self.fascia]
                else:
                    # Non ci sono dati, sensore non disponibile
                    self._available = False
            elif "_MP" in self.fascia.value:
                if len(self.coordinator.pun_data_mp.pun[self.fascia]) > 0:
                    # Ci sono dati, sensore disponibile
                    self._available = True
                    self._native_value = self.coordinator.pun_values_mp.value[self.fascia]
                else:
                    # Non ci sono dati, sensore non disponibile
                    self._available = False
        elif (
            len(self.coordinator.pun_data.pun[Fascia.F2])
            and len(self.coordinator.pun_data.pun[Fascia.F3])
        ) > 0 and self.fascia == Fascia.F23:
            # Caso speciale per fascia F23: affinché sia disponibile devono
            # esserci dati sia sulla fascia F2 che sulla F3,
            # visto che è calcolata a partire da questi
            self._available = True
            self._native_value = self.coordinator.pun_values.value[self.fascia]
        elif (
            len(self.coordinator.pun_data_mp.pun[Fascia.F2_MP])
            and len(self.coordinator.pun_data_mp.pun[Fascia.F3_MP])
        ) > 0 and self.fascia == Fascia.F23_MP:
            # Caso speciale per fascia F23: affinché sia disponibile devono
            # esserci dati sia sulla fascia F2 che sulla F3,
            # visto che è calcolata a partire da questi
            self._available = True
            self._native_value = self.coordinator.pun_values_mp.value[self.fascia]
        else:
            # Non ci sono dati, sensore non disponibile
            self._available = False

        # Aggiorna lo stato di Home Assistant
        self.async_write_ha_state()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Determina i dati da salvare per il ripristino successivo."""
        return RestoredExtraData(
            {"native_value": self._native_value if self._available else None}
        )

    async def async_added_to_hass(self) -> None:
        """Entità aggiunta ad Home Assistant."""
        await super().async_added_to_hass()

        # Recupera lo stato precedente, se esiste
        if (old_data := await self.async_get_last_extra_data()) is not None:
            if (old_native_value := old_data.as_dict().get("native_value")) is not None:
                self._available = True
                self._native_value = old_native_value

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico."""
        return False

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile."""
        return self._available

    @property
    def native_value(self) -> float:
        """Valore corrente del sensore."""
        return self._native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unita' di misura."""
        return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend."""
        return "mdi:chart-line"

    @property
    def name(self) -> str | None:
        """Restituisce il nome del sensore."""
        if self.fascia == Fascia.MONO:
            return "PUN mono-orario"
        if self.fascia == Fascia.MONO_MP:
            return "PUN mono-orario mese precedente"
        if self.fascia and "_MP" not in str(self.fascia.value):
            return f"PUN fascia {self.fascia.value}"
        if self.fascia and "_MP" in str(self.fascia.value):
            return f"PUN fascia {self.fascia.value.replace("_MP","")} mese precedente"
        return None

class FasciaPUNSensorEntity(CoordinatorEntity, SensorEntity):
    """Sensore che rappresenta il nome la fascia oraria PUN corrente."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator) -> None:
        """Inizializza il sensore."""
        super().__init__(coordinator)

        # Inizializza coordinator
        self.coordinator = coordinator

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format("pun_fascia_corrente")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

    @property
    def device_info(self):
        """Return device information for PUN parameters."""
        return {
            "identifiers": {(DOMAIN, "PUN")},
            "name": "Prezzo Unico Nazionale (PUN)",
            "manufacturer": "Gestore Mercati Energetici",
            "model": "Dati PUN in Tempo Reale",
        }
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""

        # Identifica l'evento che ha scatenato l'aggiornamento
        if self.coordinator.data is None:
            return
        if (coordinator_event := self.coordinator.data.get(COORD_EVENT)) is None:
            return

        # Aggiorna il sensore in caso di variazione di fascia
        if coordinator_event != EVENT_UPDATE_FASCIA:
            return

        self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico."""
        return False

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile."""
        return self.coordinator.fascia_corrente is not None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Classe del sensore."""
        return SensorDeviceClass.ENUM

    @property
    def options(self) -> list[str] | None:
        """Possibili stati del sensore."""
        return [Fascia.F1.value, Fascia.F2.value, Fascia.F3.value]

    @property
    def native_value(self) -> str | None:
        """Restituisce la fascia corrente come stato."""
        if not self.coordinator.fascia_corrente:
            return None
        return self.coordinator.fascia_corrente.value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Attributi aggiuntivi del sensore."""
        return {
            "fascia_successiva": self.coordinator.fascia_successiva.value
            if self.coordinator.fascia_successiva
            else None,
            "inizio_fascia_successiva": self.coordinator.prossimo_cambio_fascia,
            "termine_fascia_successiva": self.coordinator.termine_prossima_fascia,
        }

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend."""
        return "mdi:timeline-clock-outline"

    @property
    def name(self) -> str:
        """Restituisce il nome del sensore."""
        return "Fascia corrente"

class PrezzoFasciaPUNSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore che rappresenta il prezzo PUN della fascia corrente."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator) -> None:
        """Inizializza il sensore."""
        super().__init__(coordinator)

        # Inizializza coordinator
        self.coordinator = coordinator

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format("pun_prezzo_fascia_corrente")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 6
        self._available = False
        self._native_value = 0
        self._friendly_name = "Prezzo fascia corrente"

    @property
    def device_info(self):
        """Return device information for PUN parameters."""
        return {
            "identifiers": {(DOMAIN, "PUN")},
            "name": "Prezzo Unico Nazionale (PUN)",
            "manufacturer": "Gestore Mercati Energetici",
            "model": "Dati PUN in Tempo Reale",
        }
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""

        # Identifica l'evento che ha scatenato l'aggiornamento
        if self.coordinator.data is None:
            return
        if (coordinator_event := self.coordinator.data.get(COORD_EVENT)) is None:
            return

        # Aggiorna il sensore in caso di variazione di prezzi o di fascia
        if coordinator_event not in (EVENT_UPDATE_PUN, EVENT_UPDATE_FASCIA):
            return

        if self.coordinator.fascia_corrente is not None:
            self._available = (
                len(self.coordinator.pun_data.pun[self.coordinator.fascia_corrente]) > 0
            )
            self._native_value = self.coordinator.pun_values.value[
                self.coordinator.fascia_corrente
            ]
            self._friendly_name = (
                f"Prezzo fascia corrente ({self.coordinator.fascia_corrente.value})"
            )
        else:
            self._available = False
            self._native_value = 0
            self._friendly_name = "Prezzo fascia corrente"
        self.async_write_ha_state()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Determina i dati da salvare per il ripristino successivo."""
        return RestoredExtraData(
            {
                "native_value": self._native_value if self._available else None,
                "friendly_name": self._friendly_name if self._available else None,
            }
        )

    async def async_added_to_hass(self) -> None:
        """Entità aggiunta ad Home Assistant."""
        await super().async_added_to_hass()

        # Recupera lo stato precedente, se esiste
        if (old_data := await self.async_get_last_extra_data()) is not None:
            if (old_native_value := old_data.as_dict().get("native_value")) is not None:
                self._available = True
                self._native_value = old_native_value
            if (
                old_friendly_name := old_data.as_dict().get("friendly_name")
            ) is not None:
                self._friendly_name = old_friendly_name

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico."""
        return False

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile."""
        return self._available

    @property
    def native_value(self) -> float:
        """Restituisce il prezzo della fascia corrente."""
        return self._native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unita' di misura."""
        return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend."""
        return "mdi:currency-eur"

    @property
    def name(self) -> str:
        """Restituisce il nome del sensore."""
        return self._friendly_name

class PrezzoZonaleSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Sensore del prezzo zonale aggiornato ogni ora."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator) -> None:
        """Inizializza il sensore."""
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format("pun_prezzo_zonale")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 6
        self._available: bool = False
        self._native_value: float = 0
        self._friendly_name: str = "Prezzo zonale"
        self._prezzi_zonali: dict[str, float | None] = {}
        
    @property
    def device_info(self):
        """Return device information for PUN parameters."""
        return {
            "identifiers": {(DOMAIN, "PUN")},
            "name": "Prezzo Unico Nazionale (PUN)",
            "manufacturer": "Gestore Mercati Energetici",
            "model": "Dati PUN in Tempo Reale",
        }
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""

        # Identifica l'evento che ha scatenato l'aggiornamento
        if self.coordinator.data is None:
            return
        if (coordinator_event := self.coordinator.data.get(COORD_EVENT)) is None:
            return

        # Aggiornata la zona e/o i prezzi
        if coordinator_event == EVENT_UPDATE_PUN:
            if self.coordinator.pun_data.zona is not None:
                # Imposta il nome della zona
                self._friendly_name = (
                    f"Prezzo zonale ({self.coordinator.pun_data.zona.value})"
                )
                # Verifica che il coordinator abbia i prezzi
                if self.coordinator.pun_data.prezzi_zonali:
                    # Copia i dati dal coordinator in locale (per il backup)
                    self._prezzi_zonali = dict(self.coordinator.pun_data.prezzi_zonali)
            else:
                # Nessuna zona impostata
                self._friendly_name = "Prezzo zonale"
                self._prezzi_zonali = {}
                self._available = False
                self.async_write_ha_state()
                return

        # Cambiato l'orario del prezzo
        if coordinator_event in (EVENT_UPDATE_PUN, EVENT_UPDATE_PREZZO_ZONALE):
            if self.coordinator.pun_data.zona is not None:
                # Controlla se il prezzo orario esiste per l'ora corrente
                if (
                    datetime_to_packed_string(self.coordinator.orario_prezzo)
                    in self._prezzi_zonali
                ):
                    # Aggiorna il valore al prezzo orario
                    if (
                        valore := self._prezzi_zonali[
                            datetime_to_packed_string(self.coordinator.orario_prezzo)
                        ]
                    ) is not None:
                        self._native_value = valore
                        self._available = True
                    else:
                        # Prezzo non disponibile
                        self._available = False
                else:
                    # Orario non disponibile
                    self._available = False
            else:
                # Nessuna zona impostata
                self._available = False

        # Aggiorna lo stato di Home Assistant
        self.async_write_ha_state()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Determina i dati da salvare per il ripristino successivo."""

        # Salva i dati per la prossima istanza
        return RestoredExtraData(
            {
                "friendly_name": self._friendly_name if self._available else None,
                "zona": self.coordinator.pun_data.zona.name
                if self.coordinator.pun_data.zona is not None
                else None,
                "prezzi_zonali": self._prezzi_zonali,
            }
        )

    async def async_added_to_hass(self) -> None:
        """Entità aggiunta ad Home Assistant."""
        await super().async_added_to_hass()

        # Recupera lo stato precedente, se esiste
        if (old_data := await self.async_get_last_extra_data()) is not None:
            # Recupera il dizionario con i valori precedenti
            old_data_dict = old_data.as_dict()

            # Zona geografica
            if (old_zona_str := old_data_dict.get("zona")) is not None:
                # Verifica che la zona attuale sia disponibile
                # (se non lo è, c'è un errore nella configurazione)
                if self.coordinator.pun_data.zona is None:
                    _LOGGER.warning(
                        "La zona geografica memorizzata '%s' non sembra essere più valida.",
                        old_zona_str,
                    )
                    self._available = False
                    return

                # Controlla se la zona memorizzata è diversa dall'attuale
                if old_zona_str != self.coordinator.pun_data.zona.name:
                    _LOGGER.debug(
                        "Ignorati i dati precedenti, perché riferiti alla zona '%s' (anziché '%s').",
                        old_zona_str,
                        self.coordinator.pun_data.zona.name,
                    )
                    self._available = False
                    return

            # Nome
            if (old_friendly_name := old_data_dict.get("friendly_name")) is not None:
                self._friendly_name = old_friendly_name

            # Valori delle fasce orarie
            if (old_prezzi_zonali := old_data_dict.get("prezzi_zonali")) is not None:
                self._prezzi_zonali = old_prezzi_zonali

                # Controlla se il prezzo orario esiste per l'ora corrente
                if (
                    datetime_to_packed_string(self.coordinator.orario_prezzo)
                    in self._prezzi_zonali
                ):
                    # Aggiorna il valore al prezzo orario
                    if (
                        valore := self._prezzi_zonali[
                            datetime_to_packed_string(self.coordinator.orario_prezzo)
                        ]
                    ) is not None:
                        self._native_value = valore
                        self._available = True
                    else:
                        # Prezzo non disponibile
                        self._available = False
                else:
                    # Imposta come non disponibile
                    self._available = False

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico."""
        return False

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile."""
        return self._available

    @property
    def native_value(self) -> float:
        """Valore corrente del sensore."""
        return self._native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unita' di misura."""
        return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend."""
        return "mdi:map-clock-outline"

    @property
    def name(self) -> str | None:
        """Restituisce il nome del sensore."""
        return self._friendly_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Restituisce gli attributi di stato."""

        # Crea il dizionario degli attributi
        attributes: dict[str, Any] = {}

        # Aggiunge i prezzi orari negli attributi, ora per ora
        if self.coordinator.pun_data.zona is not None:
            for h in range(24):
                # Prezzi di oggi
                data_oggi = get_next_date(
                    dataora=self.coordinator.orario_prezzo, ora=h, offset=0
                )
                attributes[ATTR_PREFIX_PREZZO_OGGI + f"{h:02d}"] = (
                    self._prezzi_zonali.get(datetime_to_packed_string(data_oggi))
                )

            for h in range(24):
                # Prezzi di domani
                data_domani = get_next_date(
                    dataora=self.coordinator.orario_prezzo, ora=h, offset=1
                )
                attributes[ATTR_PREFIX_PREZZO_DOMANI + f"{h:02d}"] = (
                    self._prezzi_zonali.get(datetime_to_packed_string(data_domani))
                )

        # Restituisce gli attributi
        return attributes

class PUNOrarioSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):

    """Sensore del prezzo PUN aggiornato ogni ora."""

    def __init__(self, coordinator: PUNDataUpdateCoordinator) -> None:
        """Inizializza il sensore."""
        super().__init__(coordinator)

        # Inizializza coordinator e tipo
        self.coordinator = coordinator

        # ID univoco sensore basato su un nome fisso
        self.entity_id = ENTITY_ID_FORMAT.format("pun_orario")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False

        # Inizializza le proprietà comuni
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 6
        self._available: bool = False
        self._native_value: float = 0
        self._friendly_name: str = "PUN orario"
        self._pun_orari: dict[str, float | None] = {}

    @property
    def device_info(self):
        """Return device information for PUN parameters."""
        return {
            "identifiers": {(DOMAIN, "PUN")},
            "name": "Prezzo Unico Nazionale (PUN)",
            "manufacturer": "Gestore Mercati Energetici",
            "model": "Dati PUN in Tempo Reale",
        }
        
    def _handle_coordinator_update(self) -> None:
        """Gestisce l'aggiornamento dei dati dal coordinator."""

        # Identifica l'evento che ha scatenato l'aggiornamento
        if self.coordinator.data is None:
            return
        if (coordinator_event := self.coordinator.data.get(COORD_EVENT)) is None:
            return

        # Aggiornati i prezzi PUN
        if coordinator_event == EVENT_UPDATE_PUN:
            # Verifica che il coordinator abbia i prezzi
            if self.coordinator.pun_data.pun_orari:
                # Copia i dati dal coordinator in locale (per il backup)
                self._pun_orari = dict(self.coordinator.pun_data.pun_orari)

        # Cambiato l'orario del prezzo
        if coordinator_event in (EVENT_UPDATE_PUN, EVENT_UPDATE_PREZZO_ZONALE):
            # Controlla se il PUN orario esiste per l'ora corrente
            if (
                datetime_to_packed_string(self.coordinator.orario_prezzo)
                in self._pun_orari
            ):
                # Aggiorna il valore al prezzo orario
                if (
                    valore := self._pun_orari[
                        datetime_to_packed_string(self.coordinator.orario_prezzo)
                    ]
                ) is not None:
                    self._native_value = valore
                    self._available = True
                else:
                    # Prezzo non disponibile
                    self._available = False
            else:
                # Orario non disponibile
                self._available = False

        # Aggiorna lo stato di Home Assistant
        self.async_write_ha_state()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        """Determina i dati da salvare per il ripristino successivo."""

        # Salva i dati per la prossima istanza
        return RestoredExtraData(
            {
                "pun_orari": self._pun_orari,
            }
        )

    async def async_added_to_hass(self) -> None:
        """Entità aggiunta ad Home Assistant."""
        await super().async_added_to_hass()

        # Recupera lo stato precedente, se esiste
        if (old_data := await self.async_get_last_extra_data()) is not None:
            # Recupera il dizionario con i valori precedenti
            old_data_dict = old_data.as_dict()

            # Valori dei prezzi orari
            if (old_pun_orari := old_data_dict.get("pun_orari")) is not None:
                self._pun_orari = old_pun_orari

                # Controlla se il prezzo orario esiste per l'ora corrente
                if (
                    datetime_to_packed_string(self.coordinator.orario_prezzo)
                    in self._pun_orari
                ):
                    # Aggiorna il valore al prezzo orario
                    if (
                        valore := self._pun_orari[
                            datetime_to_packed_string(self.coordinator.orario_prezzo)
                        ]
                    ) is not None:
                        self._native_value = valore
                        self._available = True
                    else:
                        # Prezzo non disponibile
                        self._available = False
                else:
                    # Imposta come non disponibile
                    self._available = False

    @property
    def should_poll(self) -> bool:
        """Determina l'aggiornamento automatico."""
        return False

    @property
    def available(self) -> bool:
        """Determina se il valore è disponibile."""
        return self._available

    @property
    def native_value(self) -> float:
        """Valore corrente del sensore."""
        return self._native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unita' di misura."""
        return f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"

    @property
    def icon(self) -> str:
        """Icona da usare nel frontend."""
        if AwesomeVersion(HA_VERSION) < AwesomeVersion("2024.1.0"):
            return "mdi:receipt-clock-outline"
        return "mdi:invoice-clock-outline"

    @property
    def name(self) -> str | None:
        """Restituisce il nome del sensore."""
        return self._friendly_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Restituisce gli attributi di stato."""

        # Crea il dizionario degli attributi
        attributes: dict[str, Any] = {}

        # Aggiunge i prezzi orari negli attributi, ora per ora
        for h in range(24):
            # Prezzi di oggi
            data_oggi = get_next_date(
                dataora=self.coordinator.orario_prezzo, ora=h, offset=0
            )
            attributes[ATTR_PREFIX_PREZZO_OGGI + f"{h:02d}"] = self._pun_orari.get(
                datetime_to_packed_string(data_oggi)
            )

        for h in range(24):
            # Prezzi di domani
            data_domani = get_next_date(
                dataora=self.coordinator.orario_prezzo, ora=h, offset=1
            )
            attributes[ATTR_PREFIX_PREZZO_DOMANI + f"{h:02d}"] = self._pun_orari.get(
                datetime_to_packed_string(data_domani)
            )

        # Restituisce gli attributi
        return attributes
