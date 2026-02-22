"""
Home Assistant TTS Integration for Silero API Server.
This file can be used as a basis for a custom_component in Home Assistant.
"""
from __future__ import annotations

import logging
import requests
from typing import Any

import voluptuous as vol
from homeassistant.components.tts import (
    CONF_LANG,
    PLATFORM_SCHEMA as TTS_PLATFORM_SCHEMA,
    Provider,
    TtsAudioType,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_VOICE = "voice"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8001
DEFAULT_LANG = "ru"
DEFAULT_VOICE = "baya"
DEFAULT_PROTOCOL = "http"

PLATFORM_SCHEMA = TTS_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(["http", "https"]),
        vol.Optional(CONF_LANG, default=DEFAULT_LANG): cv.string,
        vol.Optional(CONF_VOICE, default=DEFAULT_VOICE): cv.string,
    }
)

def get_engine(hass, config, discovery_info=None):
    """Set up Silero TTS speech component."""
    return SileroTTSProvider(hass, config)

class SileroTTSProvider(Provider):
    """Silero TTS speech api provider."""

    def __init__(self, hass, conf):
        """Init Silero TTS service."""
        self.hass = hass
        self._host = conf.get(CONF_HOST)
        self._port = conf.get(CONF_PORT)
        self._protocol = conf.get(CONF_PROTOCOL)
        self._lang = conf.get(CONF_LANG)
        self._voice = conf.get(CONF_VOICE)
        self.name = "SileroTTS"

        self._url = f"{self._protocol}://{self._host}:{self._port}/v1/audio/speech"

    @property
    def default_language(self) -> str:
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return [self._lang]

    @property
    def supported_options(self) -> list[str]:
        """Return a list of supported options."""
        return [CONF_VOICE]

    def get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS from Silero API."""
        voice = options.get(CONF_VOICE, self._voice)
        
        payload = {
            "input": message,
            "voice": voice,
            "model": "tts-1"
        }

        try:
            response = requests.post(self._url, json=payload, timeout=10)
            response.raise_for_status()
            return "wav", response.content
        except Exception as e:
            _LOGGER.error("Error occurred while fetching TTS from Silero API: %s", e)
            return None, None
