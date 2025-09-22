from datetime import date, timedelta, datetime
import holidays
from statistics import mean
import zipfile, io
from bs4 import BeautifulSoup
import defusedxml.ElementTree as et
from typing import Tuple
from functools import partial

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_track_point_in_time, async_call_later
import homeassistant.util.dt as dt_util
from zoneinfo import ZoneInfo
from .coordinator import PUNDataUpdateCoordinator
from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as HA_VERSION
if (AwesomeVersion(HA_VERSION) >= AwesomeVersion("2024.5.0")):
    from homeassistant.setup import SetupPhases, async_pause_setup

from .const import (
    DOMAIN,
    COORD_EVENT,
    CONF_FIX_QUOTA_AGGR_MEASURE,
    CONF_MONTHLY_FEE,
    CONF_NW_LOSS_PERCENTAGE,
    CONF_OTHER_FEE,
    CONF_FIX_QUOTA_TRANSPORT,
    CONF_QUOTA_POWER,
    CONF_POWER_IN_USE,
    CONF_ENERGY_SC1,
    CONF_ASOS_SC1,
    CONF_ASOS_SC2,
    CONF_ARIM_SC1,
    CONF_ARIM_SC2,
    CONF_ACCISA_TAX,
    CONF_IVA,
    CONF_DISCOUNT,
    CONF_TV_TAX,
    CONF_MONTHY_ENTITY_SENSOR,
    CONF_PUN_MODE,
    CONF_FIXED_PUN_VALUE
)

import logging
_LOGGER = logging.getLogger(__name__)

# Usa sempre il fuso orario italiano (i dati del sito sono per il mercato italiano)
tz_pun = ZoneInfo('Europe/Rome')

# Definisce i tipi di entità
PLATFORMS: list[str] = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Impostazione dell'integrazione da configurazione Home Assistant"""

    # Carica le dipendenze di holidays in background per evitare errori nel log
    if (AwesomeVersion(HA_VERSION) >= AwesomeVersion("2024.5.0")):
        with async_pause_setup(hass, SetupPhases.WAIT_IMPORT_PACKAGES):
            await hass.async_add_import_executor_job(holidays.IT)

    # Salva il coordinator nella configurazione
    coordinator = PUNDataUpdateCoordinator(hass, config)
    hass.data.setdefault(DOMAIN, {})[config.entry_id] = coordinator

    # Aggiorna immediatamente la fascia oraria corrente
    await coordinator.update_fascia()

    # Aggiorna immediatamente il prezzo zonale corrente
    await coordinator.update_prezzo_zonale()
    
    # Crea i sensori con la configurazione specificata
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

    # Schedula l'aggiornamento via web 10 secondi dopo l'avvio
    coordinator.schedule_token = async_call_later(
        hass, timedelta(seconds=10), coordinator.update_pun
    )
    
    # Registra il callback di modifica opzioni
    config.async_on_unload(config.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Rimozione dell'integrazione da Home Assistant"""
    
    # Scarica i sensori (disabilitando di conseguenza il coordinator)
    unload_ok = await hass.config_entries.async_unload_platforms(config, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config.entry_id)

    return unload_ok

async def update_listener(hass: HomeAssistant, config: ConfigEntry) -> None:
    """Modificate le opzioni da Home Assistant"""

    # Recupera il coordinator
    coordinator = hass.data[DOMAIN][config.entry_id]

    if config.options[CONF_FIX_QUOTA_AGGR_MEASURE] != coordinator.fix_quota_aggr_measure:
        coordinator.fix_quota_aggr_measure = config.options[CONF_FIX_QUOTA_AGGR_MEASURE]
        
    if config.options[CONF_MONTHLY_FEE] != coordinator.monthly_fee:
        coordinator.monthly_fee = config.options[CONF_MONTHLY_FEE]


    if config.options[CONF_NW_LOSS_PERCENTAGE] != coordinator.nw_loss_percentage:
        coordinator.nw_loss_percentage = config.options[CONF_NW_LOSS_PERCENTAGE]
    if config.options[CONF_OTHER_FEE] != coordinator.other_fee:
        coordinator.other_fee = config.options[CONF_OTHER_FEE]
    if config.options[CONF_MONTHY_ENTITY_SENSOR] != coordinator.monthly_entity_sensor:
        coordinator.monthly_entity_sensor = config.options[CONF_MONTHY_ENTITY_SENSOR]
    if config.options[CONF_PUN_MODE] != coordinator.pun_mode:
        coordinator.pun_mode = config.options[CONF_PUN_MODE]
    if config.options.get(CONF_FIXED_PUN_VALUE) != coordinator.fixed_pun_value:
        coordinator.fixed_pun_value = config.options.get(CONF_FIXED_PUN_VALUE)

    if config.options[CONF_FIX_QUOTA_TRANSPORT] != coordinator.fix_quota_transport:
        coordinator.fix_quota_transport = config.options[CONF_FIX_QUOTA_TRANSPORT]
    if config.options[CONF_QUOTA_POWER] != coordinator.quota_power:
        coordinator.quota_power = config.options[CONF_QUOTA_POWER]
    if config.options[CONF_POWER_IN_USE] != coordinator.power_in_use:
        coordinator.power_in_use = config.options[CONF_POWER_IN_USE]
    if config.options[CONF_ENERGY_SC1] != coordinator.energy_sc1:
        coordinator.energy_sc1 = config.options[CONF_ENERGY_SC1]

    if config.options[CONF_ASOS_SC1] != coordinator.asos_sc1:
        coordinator.asos_sc1 = config.options[CONF_ASOS_SC1]
    if config.options[CONF_ASOS_SC2] != coordinator.asos_sc2:
        coordinator.asos_sc2 = config.options[CONF_ASOS_SC2]
    if config.options[CONF_ARIM_SC1] != coordinator.arim_sc1:
        coordinator.arim_sc1 = config.options[CONF_ARIM_SC1]
    if config.options[CONF_ARIM_SC2] != coordinator.arim_sc2:
        coordinator.arim_sc2 = config.options[CONF_ARIM_SC2]
    if config.options[CONF_ACCISA_TAX] != coordinator.accisa_tax:
        coordinator.accisa_tax = config.options[CONF_ACCISA_TAX]

    if config.options[CONF_IVA] != coordinator.iva:
        coordinator.iva = config.options[CONF_IVA]
    if config.options[CONF_DISCOUNT] != coordinator.discount:
        coordinator.discount = config.options[CONF_DISCOUNT]
    if config.options[CONF_TV_TAX] != coordinator.tv_tax:
        coordinator.tv_tax = config.options[CONF_TV_TAX]


