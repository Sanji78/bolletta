from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as HA_VERSION
import voluptuous as vol
from .const import (
    DOMAIN,
    CONF_FIX_QUOTA_AGGR_MEASURE,
    CONF_MONTHLY_FEE,
    CONF_OTHER_FEE,
    CONF_POWER_IN_USE,
    CONF_DISCOUNT,
    CONF_TV_TAX,
    CONF_MONTHY_ENTITY_SENSOR,
    CONF_PUN_SENSOR,
    CONF_PUN_MP_SENSOR,
    CONF_SCAN_HOUR, 
    CONF_ZONA,
    CONF_PUN_MODE,
    CONF_FIXED_PUN_VALUE,
    PUN_MODE_CALCULATED,
    PUN_MODE_FIXED,
    CONF_HOUSE_TYPE,
    RESIDENTIAL,
    NOT_RESIDENTIAL
)
from .interfaces import DEFAULT_ZONA, Zona

# Configurazione del selettore compatibile con HA 2023.4.0
selector_config = selector.SelectSelectorConfig(
    options=[
        selector.SelectOptionDict(value=zona.name, label=zona.value) for zona in Zona
    ],
    mode=selector.SelectSelectorMode.DROPDOWN,
    translation_key="zona",
)
pun_mode_selector_config = selector.SelectSelectorConfig(
    options=[
        selector.SelectOptionDict(value=PUN_MODE_CALCULATED, label="calculated"),
        selector.SelectOptionDict(value=PUN_MODE_FIXED, label="fixed"),
    ],
    mode=selector.SelectSelectorMode.DROPDOWN,
    translation_key="pun_mode",
)
house_type_selector_config = selector.SelectSelectorConfig(
    options=[
        selector.SelectOptionDict(value=RESIDENTIAL, label="residential"),
        selector.SelectOptionDict(value=NOT_RESIDENTIAL, label="not_residential"),
    ],
    mode=selector.SelectSelectorMode.DROPDOWN,
    translation_key="house_type",
)
if AwesomeVersion(HA_VERSION) >= AwesomeVersion("2023.9.0"):
    selector_config["sort"] = True
    

class PUNOptionsFlow(config_entries.OptionsFlow):
    """Opzioni per prezzi PUN (= riconfigurazione successiva)"""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Inizializzazione options flow"""
        self._entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Gestisce le opzioni"""
        errors = {}

        pun_mode = self._entry.options.get(
            CONF_PUN_MODE,
            self._entry.data.get(CONF_PUN_MODE, PUN_MODE_CALCULATED),
        )
        # Schema dati di opzione (con default sui valori attuali)
        data_schema = {
            vol.Required(CONF_FIX_QUOTA_AGGR_MEASURE, default=self._entry.options.get(CONF_FIX_QUOTA_AGGR_MEASURE, self._entry.data[CONF_FIX_QUOTA_AGGR_MEASURE])) : cv.positive_float,
            vol.Required(CONF_MONTHLY_FEE, default=self._entry.options.get(CONF_MONTHLY_FEE, self._entry.data[CONF_MONTHLY_FEE])) : cv.positive_float,
            vol.Required(CONF_PUN_MODE, default=pun_mode): selector.SelectSelector(pun_mode_selector_config),
            vol.Required(CONF_OTHER_FEE, default=self._entry.options.get(CONF_OTHER_FEE, self._entry.data[CONF_OTHER_FEE])) : cv.positive_float,
        }

        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step2o", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_step2o(self, user_input=None):
        """Step 5o: campi condizionali in base alla modalità PUN (options)"""
        self.data = user_input
        errors = {}

        opt = self._entry.options
        dat = self._entry.data

        pun_mode = self.data.get(CONF_PUN_MODE, opt.get(CONF_PUN_MODE, dat.get(CONF_PUN_MODE, PUN_MODE_CALCULATED)))
        house_type = self.data.get(CONF_HOUSE_TYPE, opt.get(CONF_HOUSE_TYPE, dat.get(CONF_HOUSE_TYPE, RESIDENTIAL)))

        if pun_mode == PUN_MODE_CALCULATED:
            data_schema = {
                vol.Required(CONF_HOUSE_TYPE, default=house_type): selector.SelectSelector(house_type_selector_config),
                vol.Required(CONF_MONTHY_ENTITY_SENSOR, default=self.data.get(CONF_MONTHY_ENTITY_SENSOR, opt.get(CONF_MONTHY_ENTITY_SENSOR, dat[CONF_MONTHY_ENTITY_SENSOR]))):
                    selector.selector({
                        "entity": {
                            "multiple": "false",
                            "filter": [{"domain": "sensor", "device_class": "energy"}],
                        }
                    }),
                vol.Required(CONF_ZONA, default=self.data.get(CONF_ZONA, opt.get(CONF_ZONA, dat.get(CONF_ZONA, DEFAULT_ZONA.name)))):
                    selector.SelectSelector(selector_config),
                vol.Required(CONF_SCAN_HOUR, default=self.data.get(CONF_SCAN_HOUR, opt.get(CONF_SCAN_HOUR, dat.get(CONF_SCAN_HOUR, 1)))):
                    vol.All(cv.positive_int, vol.Range(min=0, max=23)),
            }

        elif pun_mode == PUN_MODE_FIXED:
            data_schema = {
                vol.Required(CONF_HOUSE_TYPE, default=house_type): selector.SelectSelector(house_type_selector_config),
                vol.Required(CONF_MONTHY_ENTITY_SENSOR, default=self.data.get(CONF_MONTHY_ENTITY_SENSOR, opt.get(CONF_MONTHY_ENTITY_SENSOR, dat[CONF_MONTHY_ENTITY_SENSOR]))):
                    selector.selector({
                        "entity": {
                            "multiple": "false",
                            "filter": [{"domain": "sensor", "device_class": "energy"}],
                        }
                    }),
                vol.Required(CONF_FIXED_PUN_VALUE, default=self.data.get(CONF_FIXED_PUN_VALUE, opt.get(CONF_FIXED_PUN_VALUE, dat.get(CONF_FIXED_PUN_VALUE, 0.20)))):
                    cv.positive_float,
            }

        return self.async_show_form(
            step_id="step3o", data_schema=vol.Schema(data_schema), errors=errors,
        )
        
    async def async_step_step3o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        errors = {}
        data_schema = {
            vol.Required(CONF_POWER_IN_USE, default=self._entry.options.get(CONF_POWER_IN_USE, self._entry.data[CONF_POWER_IN_USE])) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step4o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step4o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        errors = {}
        data_schema = {
            vol.Required(CONF_DISCOUNT, default=self._entry.options.get(CONF_DISCOUNT, self._entry.data[CONF_DISCOUNT])) : cv.positive_float,
            vol.Required(CONF_TV_TAX, default=self._entry.options.get(CONF_TV_TAX, self._entry.data[CONF_TV_TAX])) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step5o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step5o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        if user_input is not None:
           
            # Configurazione valida (validazione integrata nello schema)
            return self.async_create_entry(
                title='Bolletta',
                data=self.data
            )

class PUNConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configurazione per prezzi PUN (= prima configurazione)"""

    # Versione della configurazione (per utilizzi futuri)
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> PUNOptionsFlow:
        """Ottiene le opzioni per questa configurazione"""
        return PUNOptionsFlow(entry)

    async def async_step_user(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        # Controlla che l'integrazione non venga eseguita più volte
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors = {}

        # Schema dati di configurazione (con default fissi)
        data_schema = {
            
            vol.Required(CONF_FIX_QUOTA_AGGR_MEASURE, default=0.007000) : cv.positive_float,
            vol.Required(CONF_MONTHLY_FEE, default=12.000000) : cv.positive_float,
            vol.Required(CONF_PUN_MODE, default=PUN_MODE_CALCULATED): selector.SelectSelector(pun_mode_selector_config),        
            vol.Required(CONF_OTHER_FEE, default=0.023063) : cv.positive_float,
        }
        
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step2", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step2(self, user_input=None):
        """Step 5: campi condizionali in base alla modalità PUN"""
        self.data = user_input
        errors = {}

        pun_mode = self.data.get(CONF_PUN_MODE, PUN_MODE_CALCULATED)
        house_type = self.data.get(CONF_HOUSE_TYPE, RESIDENTIAL)

        if pun_mode == PUN_MODE_CALCULATED:
            data_schema = {
                vol.Required(CONF_HOUSE_TYPE, default=house_type): selector.SelectSelector(house_type_selector_config),
                vol.Required(CONF_MONTHY_ENTITY_SENSOR, default=self.data.get(CONF_MONTHY_ENTITY_SENSOR)):
                    selector.selector({
                        "entity": {
                            "multiple": "false",
                            "filter": [{"domain": "sensor", "device_class": "energy"}],
                        }
                    }),
                vol.Required(CONF_ZONA, default=self.data.get(CONF_ZONA, DEFAULT_ZONA.name)):
                    selector.SelectSelector(selector_config),
                vol.Required(CONF_SCAN_HOUR, default=self.data.get(CONF_SCAN_HOUR, 1)):
                    vol.All(cv.positive_int, vol.Range(min=0, max=23)),
            }

        elif pun_mode == PUN_MODE_FIXED:
            data_schema = {
                vol.Required(CONF_HOUSE_TYPE, default=house_type): selector.SelectSelector(house_type_selector_config),
                vol.Required(CONF_MONTHY_ENTITY_SENSOR, default=self.data.get(CONF_MONTHY_ENTITY_SENSOR)):
                    selector.selector({
                        "entity": {
                            "multiple": "false",
                            "filter": [{"domain": "sensor", "device_class": "energy"}],
                        }
                    }),
                vol.Required(CONF_FIXED_PUN_VALUE, default=self.data.get(CONF_FIXED_PUN_VALUE, 0.20)):
                    cv.positive_float,
            }

        return self.async_show_form(
            step_id="step3", data_schema=vol.Schema(data_schema), errors=errors,
        )


    async def async_step_step3(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        errors = {}
        data_schema = {
            vol.Required(CONF_POWER_IN_USE, default=4.5) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step4", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step4(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        errors = {}
        data_schema = {
            vol.Required(CONF_DISCOUNT, default=1) : cv.positive_float,
            vol.Required(CONF_TV_TAX, default=9) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step5", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step5(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input or {})
        if user_input is not None:
            # Configurazione valida (validazione integrata nello schema)
            return self.async_create_entry(
                title='Bolletta',
                data=self.data
            )
