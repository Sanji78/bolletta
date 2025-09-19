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
    CONF_PUN_SENSOR,
    CONF_PUN_MP_SENSOR,
    CONF_ACTUAL_DATA_ONLY, 
    CONF_SCAN_HOUR, 
    CONF_ZONA
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
if AwesomeVersion(HA_VERSION) >= AwesomeVersion("2023.9.0"):
    selector_config["sort"] = True
    

class PUNOptionsFlow(config_entries.OptionsFlow):
    """Opzioni per prezzi PUN (= riconfigurazione successiva)"""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Inizializzazione options flow"""
        self.config_entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Gestisce le opzioni"""
        errors = {}

        # Schema dati di opzione (con default sui valori attuali)
        data_schema = {
            vol.Required(CONF_FIX_QUOTA_AGGR_MEASURE, default=self.config_entry.options.get(CONF_FIX_QUOTA_AGGR_MEASURE, self.config_entry.data[CONF_FIX_QUOTA_AGGR_MEASURE])) : cv.positive_float,
            vol.Required(CONF_MONTHLY_FEE, default=self.config_entry.options.get(CONF_MONTHLY_FEE, self.config_entry.data[CONF_MONTHLY_FEE])) : cv.positive_float,
            vol.Required(CONF_NW_LOSS_PERCENTAGE, default=self.config_entry.options.get(CONF_NW_LOSS_PERCENTAGE, self.config_entry.data[CONF_NW_LOSS_PERCENTAGE])) : vol.All(cv.positive_int, vol.Range(min=0, max=100)),
            vol.Required(CONF_OTHER_FEE, default=self.config_entry.options.get(CONF_OTHER_FEE, self.config_entry.data[CONF_OTHER_FEE])) : cv.positive_float,
        }

        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step2o", data_schema=vol.Schema(data_schema), errors=errors
        )

    async def async_step_step2o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data = user_input
        errors = {}
        data_schema = {
            vol.Required(CONF_FIX_QUOTA_TRANSPORT, default=self.config_entry.options.get(CONF_FIX_QUOTA_TRANSPORT, self.config_entry.data[CONF_FIX_QUOTA_TRANSPORT])) : cv.positive_float,
            vol.Required(CONF_QUOTA_POWER, default=self.config_entry.options.get(CONF_QUOTA_POWER, self.config_entry.data[CONF_QUOTA_POWER])) : cv.positive_float,
            vol.Required(CONF_POWER_IN_USE, default=self.config_entry.options.get(CONF_POWER_IN_USE, self.config_entry.data[CONF_POWER_IN_USE])) : cv.positive_float,
            vol.Required(CONF_ENERGY_SC1, default=self.config_entry.options.get(CONF_ENERGY_SC1, self.config_entry.data[CONF_ENERGY_SC1])) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step3o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step3o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_ASOS_SC1, default=self.config_entry.options.get(CONF_ASOS_SC1, self.config_entry.data[CONF_ASOS_SC1])) : cv.positive_float,
            vol.Required(CONF_ASOS_SC2, default=self.config_entry.options.get(CONF_ASOS_SC2, self.config_entry.data[CONF_ASOS_SC2])) : cv.positive_float,
            vol.Required(CONF_ARIM_SC1, default=self.config_entry.options.get(CONF_ARIM_SC1, self.config_entry.data[CONF_ARIM_SC1])) : cv.positive_float,
            vol.Required(CONF_ARIM_SC2, default=self.config_entry.options.get(CONF_ARIM_SC2, self.config_entry.data[CONF_ARIM_SC2])) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step4o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step4o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_ACCISA_TAX, default=self.config_entry.options.get(CONF_ACCISA_TAX, self.config_entry.data[CONF_ACCISA_TAX])) : cv.positive_float,
            vol.Required(CONF_IVA, default=self.config_entry.options.get(CONF_IVA, self.config_entry.data[CONF_IVA])) : vol.All(cv.positive_int, vol.Range(min=0, max=100)),
            vol.Required(CONF_DISCOUNT, default=self.config_entry.options.get(CONF_DISCOUNT, self.config_entry.data[CONF_DISCOUNT])) : cv.positive_float,
            vol.Required(CONF_TV_TAX, default=self.config_entry.options.get(CONF_TV_TAX, self.config_entry.data[CONF_TV_TAX])) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step5o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step5o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_MONTHY_ENTITY_SENSOR, default=self.config_entry.options.get(CONF_MONTHY_ENTITY_SENSOR, self.config_entry.data[CONF_MONTHY_ENTITY_SENSOR])) : selector.selector({
				"entity": {
					"multiple": "false",
				    "filter": [{"domain" : "sensor", "device_class" : "energy"}],
				}
			}),
            vol.Required(
                CONF_ZONA,
                default=self.config_entry.options.get(
                    CONF_ZONA, self.config_entry.data[CONF_ZONA]
                ),
            ): selector.SelectSelector(selector_config),
            vol.Required(
                CONF_SCAN_HOUR,
                default=self.config_entry.options.get(
                    CONF_SCAN_HOUR, self.config_entry.data[CONF_SCAN_HOUR]
                ),
            ): vol.All(cv.positive_int, vol.Range(min=0, max=23)),
            vol.Optional(
                CONF_ACTUAL_DATA_ONLY,
                default=self.config_entry.options.get(
                    CONF_ACTUAL_DATA_ONLY, self.config_entry.data[CONF_ACTUAL_DATA_ONLY]
                ),            
            ): cv.boolean,
            # vol.Required(CONF_PUN_SENSOR, default=self.config_entry.options.get(CONF_MONTHY_ENTITY_SENSOR, self.config_entry.data[CONF_PUN_SENSOR])) : selector.selector({
				# "entity": {
					# "multiple": "false",
				    # "filter": [{"domain" : "sensor"}],
				# }
			# }),
            # vol.Required(CONF_PUN_MP_SENSOR, default=self.config_entry.options.get(CONF_MONTHY_ENTITY_SENSOR, self.config_entry.data[CONF_PUN_MP_SENSOR])) : selector.selector({
				# "entity": {
					# "multiple": "false",
				    # "filter": [{"domain" : "sensor"}],
				# }
			# }),
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step6o", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step6o(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
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
            vol.Required(CONF_NW_LOSS_PERCENTAGE, default=10) : vol.All(cv.positive_int, vol.Range(min=0, max=100)),
            vol.Required(CONF_OTHER_FEE, default=0.014671) : cv.positive_float,
        }
        
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step2", data_schema=vol.Schema(data_schema), errors=errors, 
        )


    async def async_step_step2(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data = user_input
        errors = {}
        data_schema = {
            vol.Required(CONF_FIX_QUOTA_TRANSPORT, default=1.840000) : cv.positive_float,
            vol.Required(CONF_QUOTA_POWER, default=1.866567) : cv.positive_float,
            vol.Required(CONF_POWER_IN_USE, default=4.5) : cv.positive_float,
            vol.Required(CONF_ENERGY_SC1, default=0.012200) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step3", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step3(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_ASOS_SC1, default=0.029809) : cv.positive_float,
            vol.Required(CONF_ASOS_SC2, default=0.029809) : cv.positive_float,
            vol.Required(CONF_ARIM_SC1, default=0.008828) : cv.positive_float,
            vol.Required(CONF_ARIM_SC2, default=0.008828) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step4", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step4(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_ACCISA_TAX, default=0.022700) : cv.positive_float,
            vol.Required(CONF_IVA, default=10) : vol.All(cv.positive_int, vol.Range(min=0, max=100)),
            vol.Required(CONF_DISCOUNT, default=1) : cv.positive_float,
            vol.Required(CONF_TV_TAX, default=7) : cv.positive_float,
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step5", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step5(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        errors = {}
        data_schema = {
            vol.Required(CONF_MONTHY_ENTITY_SENSOR) : selector.selector({
				"entity": {
					"multiple": "false",
				    "filter": [{"domain" : "sensor", "device_class" : "energy"}],
				}
			}),
            vol.Required(CONF_ZONA, default=DEFAULT_ZONA.name): selector.SelectSelector(
                selector_config
            ),
            vol.Required(CONF_SCAN_HOUR, default=1): vol.All(
                cv.positive_int, vol.Range(min=0, max=23)
            ),
            vol.Optional(CONF_ACTUAL_DATA_ONLY, default=False): cv.boolean,
            # vol.Required(CONF_PUN_SENSOR) : selector.selector({
				# "entity": {
					# "multiple": "false",
				    # "filter": [{"domain" : "sensor"}],
				# }
			# }),
            # vol.Required(CONF_PUN_MP_SENSOR) : selector.selector({
				# "entity": {
					# "multiple": "false",
				    # "filter": [{"domain" : "sensor"}],
				# }
			# }),
        }
        # Mostra la schermata di configurazione, con gli eventuali errori
        return self.async_show_form(
            step_id="step6", data_schema=vol.Schema(data_schema), errors=errors, 
        )

    async def async_step_step6(self, user_input=None):
        """Gestione prima configurazione da Home Assistant"""
        self.data.update(user_input)
        if user_input is not None:
            # Configurazione valida (validazione integrata nello schema)
            return self.async_create_entry(
                title='Bolletta',
                data=self.data
            )
