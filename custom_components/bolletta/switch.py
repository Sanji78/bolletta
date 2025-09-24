import logging
from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    SwitchEntity
)


from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from . import PUNDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        BillConfigSwitchEntity(coordinator, "invoice_shift", "Fattura mesi pari", default=False),
        BillConfigSwitchEntity(coordinator, "invoice_monthly", "Fattura mensile", default=False),
    ]

    async_add_entities(entities)


class BillConfigSwitchEntity(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Switch di configurazione per la logica della fattura"""

    def __init__(self, coordinator: PUNDataUpdateCoordinator, key: str, name: str, default: bool) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.key = key
        self._attr_name = name
        self._state = default
        self.entity_id = ENTITY_ID_FORMAT.format(f"{key}")
        self._attr_unique_id = self.entity_id
        self._attr_has_entity_name = False
        
    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs):
        self._state = True
        self.async_write_ha_state()
        # forza i sensori bolletta a ricalcolare
        self.coordinator.async_update_listeners()

    async def async_turn_off(self, **kwargs):
        self._state = False
        self.async_write_ha_state()
        # forza i sensori bolletta a ricalcolare
        self.coordinator.async_update_listeners()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (old_state := await self.async_get_last_state()) is not None:
            self._state = old_state.state == "on"


    @property
    def device_info(self):
        """Return device information for Bolletta."""
        return {
            "identifiers": {(DOMAIN, "bolletta")},
            "name": "Monitor Costi Energia",
            "manufacturer": "Bolletta",
            "model": "Calcolo della Bolletta Elettrica",
        }