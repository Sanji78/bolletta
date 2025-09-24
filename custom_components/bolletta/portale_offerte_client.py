"""PortaleOfferte CSV parser for retrieving bill parameters.

Fetches:
https://www.ilportaleofferte.it/portaleOfferte/resources/opendata/csv/parametri/{year}_{month}/PO_Parametri_E_{yyyymmdd}.csv

Behavior:
- mp: latest available file up to today (tries today, then day-1, day-2, ... until found or limit)
- mpp: last-day-of-previous-month (if not present, steps backwards until it finds a file)
- caching per yyyymmdd
- returns {"mp": {...}, "mpp": {...}} similar to AreraClient.get_current_tariffs
"""
from __future__ import annotations

import io
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Any
import csv

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    RESIDENTIAL,
    NOT_RESIDENTIAL,
    CONF_ACCISA_TAX,
    CONF_IVA,
    CONF_ASOS_SC1,
    CONF_ASOS_SC1_MP,
    CONF_ARIM_SC1,
    CONF_ARIM_SC1_MP,
    CONF_NW_LOSS_PERCENTAGE,
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.ilportaleofferte.it/portaleOfferte/resources/opendata/csv/parametri"
FILENAME_TEMPLATE = "PO_Parametri_E_{yyyymmdd}.csv"


class PortaleOfferteClient:
    """Client to download and parse ilportaleofferte CSV parameters."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.session: ClientSession = async_get_clientsession(hass)
        # cached_data keyed by 'YYYYMMDD' -> dict of parsed params
        self._cached_data: Dict[str, Dict[str, float]] = {}
        self._max_lookback_days = 60  # safety stop if many days missing

    async def get_current_tariffs(self, house_type: str, power_in_use: float) -> Dict[str, Dict[str, float]]:
        """Return {'mp': {...}, 'mpp': {...}}.

        mp = latest available file up to today (tries today, day-1, ...).
        mpp = last day of previous month (if missing, step back until found).
        """
        today = datetime.now().date()
        # mp -> latest up to today (try today, yesterday, ...)
        mp_date = today
        mp_found = await self._fetch_until_found(mp_date, house_type, power_in_use, forward=False, limit_days=self._max_lookback_days)

        # mpp -> last day of previous month
        first_of_this_month = today.replace(day=1)
        last_of_prev_month = first_of_this_month - timedelta(days=1)
        mpp_date = last_of_prev_month
        mpp_found = await self._fetch_until_found(mpp_date, house_type, power_in_use, forward=False, limit_days=self._max_lookback_days)

        return {"mp": mp_found or {}, "mpp": mpp_found or {}}

    async def get_tariff_with_fallback(self, house_type: str, power_in_use: float) -> Optional[Dict[str, Dict[str, float]]]:
        """Same pattern as AreraClient - wrapper with error handling."""
        try:
            data = await self.get_current_tariffs(house_type, power_in_use)
            if not data:
                _LOGGER.warning("PortaleOfferte: no data found, returning None")
                return None
            return data
        except Exception as e:
            _LOGGER.error("PortaleOfferte: failed to fetch/parse data: %s", e, exc_info=True)
            return None

    async def _fetch_until_found(self, start_date: date, house_type: str, power_in_use: float, forward: bool = False, limit_days: int = 60) -> Optional[Dict[str, float]]:
        """Try date, then step backwards (or forwards) until a file is found or limit reached.

        - forward=False: go back in time (day-1, day-2, ...).
        - limit_days: absolute cap for attempts to avoid infinite loops.
        """
        attempts = 0
        cur_date = start_date
        while attempts < limit_days:
            key = cur_date.strftime("%Y%m%d")
            url = self._build_url_for_date(cur_date)
            _LOGGER.debug("PortaleOfferte: trying URL %s", url)
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        raw = await resp.read()
                        parsed = self._parse_csv(raw, house_type, power_in_use)
                        self._cached_data[key] = parsed
                        _LOGGER.info("PortaleOfferte: found and parsed file for %s", key)
                        return parsed
                    else:
                        _LOGGER.debug("PortaleOfferte: file %s not found (HTTP %s)", key, resp.status)
            except Exception as e:
                _LOGGER.debug("PortaleOfferte: error fetching %s -> %s", url, e)

            # step date
            attempts += 1
            cur_date = cur_date + timedelta(days=1) if forward else cur_date - timedelta(days=1)

        _LOGGER.warning("PortaleOfferte: no file found within %s days from %s", limit_days, start_date)
        return None

    def _build_url_for_date(self, dt: date) -> str:
        """Build URL for a given date.

        Directory uses 'YYYY_M' (month without leading zero) according to samples.
        Filename uses PO_Parametri_E_YYYYMMDD.csv
        """
        dir_part = f"{dt.year}_{dt.month}"
        filename = FILENAME_TEMPLATE.format(yyyymmdd=dt.strftime("%Y%m%d"))
        return f"{BASE_URL}/{dir_part}/{filename}"

    def _parse_csv(self, raw_bytes: bytes, house_type: str, power_in_use: float) -> Dict[str, float]:
        """Parse CSV content and map CSV parameters to the const keys.

        Best-effort mapping is used (residential vs non-residential).
        If a CSV parameter is missing, it will be omitted from the returned dict.
        """
        text = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        entries = {}
        # Build map of nome_parametro -> valore (float)
        for row in reader:
            name = row.get("nome_parametro")
            val = row.get("valore")
            if name is None:
                continue
            try:
                # Many CSV fields are numeric but may use '.' as decimal separator already
                entries[name.strip()] = float(val) if val not in (None, "") else None
            except Exception:
                # best-effort: replace comma, strip
                try:
                    v = str(val).replace(",", ".").strip()
                    entries[name.strip()] = float(v)
                except Exception:
                    entries[name.strip()] = None

        params: Dict[str, float] = {}

        # Best-effort mapping tables:
        if house_type == RESIDENTIAL and power_in_use<=3:
            # residential mapping (common keys)
            mapping = {
                CONF_ASOS_SC1: "asos_dr",  
                CONF_ARIM_SC1: "arim_dr",  
                CONF_ACCISA_TAX: "acc_c_r_l",  
                CONF_IVA: "iva_c",  
                CONF_NW_LOSS_PERCENTAGE: "lambda",
            }
        elif house_type == RESIDENTIAL and power_in_use>3:
            # residential mapping (common keys)
            mapping = {
                CONF_ASOS_SC1: "asos_dr",  
                CONF_ARIM_SC1: "arim_dr",  
                CONF_ACCISA_TAX: "acc_c_r_h",  
                CONF_IVA: "iva_c",  
                CONF_NW_LOSS_PERCENTAGE: "lambda",
            }
        else:
            # non residential mapping
            mapping = {
                CONF_ASOS_SC1: "asos_dnr_v",  
                CONF_ARIM_SC1: "arim_dnr_v",
                CONF_ACCISA_TAX: "acc_c_nr",
                CONF_IVA: "iva_c",
                CONF_NW_LOSS_PERCENTAGE: "lambda",
            }

        # For each mapping, set if available
        for const_key, csv_key in mapping.items():
            raw_v = entries.get(csv_key)
            if raw_v is None:
                # try alternative names - be forgiving
                alt = csv_key + "_f"
                raw_v = entries.get(alt, entries.get(csv_key.replace("_v", "_f")))
            if raw_v is not None:
                params[const_key] = float(raw_v)
                _LOGGER.debug("Mapped %s <- %s = %s", const_key, csv_key, raw_v)
            else:
                _LOGGER.debug("CSV param '%s' not found for mapping to %s", csv_key, const_key)

        # Also duplicate values to *_MP keys will be handled by coordinator when assigning (they request mp/mpp).
        # But for convenience, we can also include *_MP variants if parsing a file intended for MP or MPP (coordinator will copy):
        # (we do not know here whether this file is mp or mpp — coordinator will assign appropriately)

        return params
