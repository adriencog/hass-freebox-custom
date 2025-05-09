"""Support for Freebox Delta, Revolution and Mini 4K."""

from __future__ import annotations

import logging
from typing import Any

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)


SWITCH_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="wifi",
        name="Freebox WiFi",
        entity_category=EntityCategory.CONFIG,
    )
]

PORT_FORWARDING_SWITCH_DESCRIPTIONS = [
    SwitchEntityDescription(
        key="port_forwarding",
        name="Port Forwarding",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:forwardburger",
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch."""
    router: FreeboxRouter = hass.data[DOMAIN][entry.unique_id]
    entities = [
        FreeboxSwitch(router, entity_description)
        for entity_description in SWITCH_DESCRIPTIONS
    ]
    for config in router.port_forwarding_config.values():
        entities.extend(
            [
                FreeboxPortForwardingSwitch(router, config, entity_description)
                for entity_description in PORT_FORWARDING_SWITCH_DESCRIPTIONS
            ]
        )
    async_add_entities(entities, True)


class FreeboxSwitch(SwitchEntity):
    """Representation of a freebox switch."""

    def __init__(
        self, router: FreeboxRouter, entity_description: SwitchEntityDescription
    ) -> None:
        """Initialize the switch."""
        self.entity_description = entity_description
        self._router = router
        self._attr_device_info = router.device_info
        self._attr_unique_id = f"{router.mac} {entity_description.name}"

    async def _async_set_state(self, enabled: bool) -> None:
        """Turn the switch on or off."""
        try:
            await self._router.wifi.set_global_config({"enabled": enabled})
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox"
                " settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def async_update(self) -> None:
        """Get the state and update it."""
        data = await self._router.wifi.get_global_config()
        self._attr_is_on = bool(data["enabled"])


class FreeboxPortForwardingSwitch(SwitchEntity):
    """Representation of a freebox switch."""

    def __init__(
        self,
        router: FreeboxRouter,
        config: dict[str, Any],
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        self.entity_description = entity_description
        self._router = router
        self._attr_device_info = router.device_info
        self._attr_unique_id = f"{router.mac} {entity_description.name} {config['id']}"
        self._attr_name = f"{entity_description.name} {config['comment']}"
        self._redir_id = config["id"]

    async def _async_set_state(self, enabled: bool) -> None:
        """Turn the switch on or off."""
        try:
            await self._router.port_forwarding.edit_port_forwarding_configuration(
                self._redir_id, {"enabled": enabled}
            )
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox"
                " settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def async_update(self) -> None:
        """Get the state and update it."""
        data = self._router.port_forwarding_config.get(self._redir_id)
        self._attr_is_on = bool(data["enabled"])
