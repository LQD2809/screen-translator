"""Translation providers for Screen Translator."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ArgosTranslator:
    """Translate offline using an installed Argos language package."""

    def translate(self, text: str, source: str, target: str) -> str:
        try:
            from argostranslate import translate as argos_translate
        except ImportError as exc:
            raise RuntimeError(
                "Local translation needs Argos Translate and an installed language package. "
                "Install the source-to-target package, or select LibreTranslate."
            ) from exc

        try:
            result = argos_translate.translate(text, source, target)
        except Exception as exc:
            raise RuntimeError(
                f"No usable local language package was found for {source} to {target}. "
                "Install that Argos package or select LibreTranslate."
            ) from exc
        if not isinstance(result, str):
            raise RuntimeError("Argos Translate returned an invalid result.")
        return result


class LibreTranslateTranslator:
    """Translate using an explicitly configured LibreTranslate endpoint."""

    def __init__(self, endpoint: str, api_key: str | None = None):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def translate(self, text: str, source: str, target: str) -> str:
        payload = {"q": text, "source": source, "target": target, "format": "text"}
        if self.api_key:
            payload["api_key"] = self.api_key
        request = Request(
            f"{self.endpoint}/translate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"LibreTranslate returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not reach LibreTranslate: {exc}") from exc
        translated = result.get("translatedText") if isinstance(result, dict) else None
        if not isinstance(translated, str):
            raise RuntimeError("LibreTranslate response did not contain translatedText.")
        return translated


def create_translator(provider: str):
    if provider == "local":
        return ArgosTranslator()
    if provider == "libretranslate":
        endpoint = os.environ.get("LIBRETRANSLATE_URL", "http://localhost:5000").strip()
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("LIBRETRANSLATE_URL must begin with http:// or https://.")
        return LibreTranslateTranslator(endpoint, os.environ.get("LIBRETRANSLATE_API_KEY"))
    raise ValueError(f"Unknown translation provider: {provider}")
