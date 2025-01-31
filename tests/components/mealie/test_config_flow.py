"""Tests for the Mealie config flow."""

from unittest.mock import AsyncMock

from aiomealie import About, MealieAuthenticationError, MealieConnectionError
import pytest

from homeassistant.components.mealie.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_full_flow(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Mealie"
    assert result["data"] == {
        CONF_HOST: "demo.mealie.io",
        CONF_API_TOKEN: "token",
    }
    assert result["result"].unique_id == "bf1c62fe-4941-4332-9886-e54e88dbdba0"


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (MealieConnectionError, "cannot_connect"),
        (MealieAuthenticationError, "invalid_auth"),
        (Exception, "unknown"),
    ],
)
async def test_flow_errors(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test flow errors."""
    mock_mealie_client.get_user_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_mealie_client.get_user_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    ("version"),
    [
        ("v1.0.0beta-5"),
        ("v1.0.0-RC2"),
        ("v0.1.0"),
        ("something"),
    ],
)
async def test_flow_version_error(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    version,
) -> None:
    """Test flow version error."""
    mock_mealie_client.get_about.return_value = About(version=version)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "mealie_version"}


async def test_duplicate(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "demo.mealie.io", CONF_API_TOKEN: "token"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
