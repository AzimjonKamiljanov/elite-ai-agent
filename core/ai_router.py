"""
AI Router — Multi-provider AI so'rovlarni yo'naltirish tizimi.
Qo'llab-quvvatlanadigan provayderlar: Gemini, DeepSeek, OpenRouter, Groq, HuggingFace.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

# Logging sozlash
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI  # type: ignore

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "models.json"

_DEFAULT_CONFIG: dict = {
    "providers": {
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "models": {
                "fast": "gemini-2.0-flash-lite",
                "code": "gemini-2.5-flash-preview-05-20",
                "pro": "gemini-2.5-pro-preview-06-05",
                "all": [
                    "gemini-2.5-pro-preview-06-05",
                    "gemini-2.5-flash-preview-05-20",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                ],
            },
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "models": {
                "fast": "deepseek-chat",
                "code": "deepseek-coder",
                "pro": "deepseek-reasoner",
                "all": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
            },
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "models": {
                "fast": "meta-llama/llama-3.1-8b-instruct:free",
                "code": "deepseek/deepseek-coder-v2",
                "pro": "anthropic/claude-sonnet-4",
                "all": [
                    "anthropic/claude-sonnet-4",
                    "anthropic/claude-3.5-sonnet",
                    "google/gemini-2.5-pro-preview",
                    "google/gemini-2.5-flash-preview-05-20",
                    "deepseek/deepseek-coder-v2",
                    "deepseek/deepseek-r1",
                    "meta-llama/llama-3.1-8b-instruct:free",
                    "meta-llama/llama-3.3-70b-instruct",
                    "qwen/qwen-2.5-72b-instruct",
                    "mistralai/mistral-large-latest",
                ],
            },
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "models": {
                "fast": "llama-3.1-8b-instant",
                "code": "llama-3.3-70b-versatile",
                "pro": "llama-3.3-70b-versatile",
                "all": [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it",
                ],
            },
        },
        "huggingface": {
            "base_url": "https://api-inference.huggingface.co/v1/",
            "models": {
                "fast": "mistralai/Mistral-7B-Instruct-v0.3",
                "code": "bigcode/starcoder2-15b",
                "pro": "meta-llama/Meta-Llama-3-8B-Instruct",
                "all": [
                    "meta-llama/Meta-Llama-3-8B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3",
                    "bigcode/starcoder2-15b",
                    "microsoft/Phi-3-mini-4k-instruct",
                ],
            },
        },
    },
    "default_provider": "gemini",
    "fallback_order": ["gemini", "deepseek", "openrouter", "groq", "huggingface"],
}


def _load_config() -> dict:
    """Model konfiguratsiyasini yuklash."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _DEFAULT_CONFIG


class AIRouter:
    """Multi-AI Orchestration — so'rovlarni eng mos modelga yo'naltirish."""

    def __init__(self) -> None:
        self._config = _load_config()
        self._api_keys: dict[str, Optional[str]] = {}
        self._load_api_keys()

    def _load_api_keys(self) -> None:
        """API kalitlarini atrof-muhitdan yoki .env dan qayta yuklash."""
        # Ensure we try reading from .env if dotenv_values is available
        env_vals = {}
        try:
            from dotenv import dotenv_values
            env_file = Path(__file__).parent.parent / ".env"
            if env_file.exists():
                env_vals = dotenv_values(str(env_file))
        except ImportError:
            pass

        def get_val(key: str) -> Optional[str]:
            val = env_vals.get(key) or os.getenv(key)
            if val and not val.startswith("your_"):
                return val
            return None

        self._api_keys = {
            "gemini": get_val("GEMINI_API_KEY_1") or get_val("GEMINI_API_KEY_2"),
            "deepseek": get_val("DEEPSEEK_API_KEY"),
            "openrouter": get_val("OPENROUTER_API_KEY"),
            "groq": get_val("GROQ_API_KEY"),
            "huggingface": get_val("HUGGINGFACE_API_KEY"),
        }
        self._forced_provider: Optional[str] = None
        self._forced_model: Optional[str] = None

    def set_provider(self, name: str) -> None:
        """Foydalanuvchi tomonidan provayderni tanlash.

        Tanlangan provayder eksklyuziv tarzda ishlatiladi — boshqa provayderga
        fallback QILINMAYDI. Avtomatik rejimga qaytish uchun reset_auto() ishlating.
        Agar provayder nomi noto'g'ri bo'lsa, ValueError ko'tariladi.
        """
        if name not in self._config["providers"]:
            available = ", ".join(self._config["providers"].keys())
            raise ValueError(f"Noto'g'ri provayder: '{name}'. Mavjud: {available}")
        self._forced_provider = name

    def set_model(self, model_name: str) -> None:
        """Foydalanuvchi tomonidan aniq modelni tanlash (override sifatida)."""
        self._forced_model = model_name

    def reset_auto(self) -> None:
        """Avtomatik rejimga qaytish — majburiy provider/model tanlovni olib tashlash."""
        self._forced_provider = None
        self._forced_model = None

    def get_current_provider(self) -> Optional[str]:
        """Hozirgi tanlangan providerni qaytarish (None = avtomatik)."""
        return self._forced_provider

    def get_current_model(self) -> Optional[str]:
        """Hozirgi tanlangan modelni qaytarish (None = avtomatik)."""
        return self._forced_model

    def list_all_models(self) -> str:
        """Barcha provayderlarning barcha modellarini jadval ko'rinishida qaytarish."""
        lines: list[str] = []
        for provider, cfg in self._config["providers"].items():
            has_key = bool(self._api_keys.get(provider))
            status = "✅" if has_key else "❌"
            lines.append(f"\n{status} **{provider.upper()}**")
            models = cfg.get("models", {})
            all_models: list[str] = models.get("all", [
                models.get("fast", ""),
                models.get("code", ""),
                models.get("pro", ""),
            ])
            for m in all_models:
                if m:
                    tags = []
                    if m == models.get("fast"):
                        tags.append("fast")
                    if m == models.get("code"):
                        tags.append("code")
                    if m == models.get("pro"):
                        tags.append("pro")
                    tag_str = f" [{', '.join(tags)}]" if tags else ""
                    lines.append(f"  • {m}{tag_str}")
        return "\n".join(lines)

    def list_providers_status(self) -> str:
        """Barcha provayderlarning holati (API kalit bor/yo'q)."""
        lines: list[str] = ["**Provayderlar holati:**\n"]
        for provider in self._config["providers"]:
            has_key = bool(self._api_keys.get(provider))
            status = "✅ API kalit bor" if has_key else "❌ API kalit yo'q"
            forced = " ◀ tanlangan" if provider == self._forced_provider else ""
            lines.append(f"  • **{provider}**: {status}{forced}")
        return "\n".join(lines)

    def _get_client(self, provider: str) -> Any:
        """Berilgan provayder uchun OpenAI-compatible client yaratish."""
        if not _OPENAI_AVAILABLE:
            raise ImportError("openai kutubxonasi o'rnatilmagan: pip install openai")

        provider_config = self._config["providers"].get(provider, {})
        base_url = provider_config.get("base_url", "")
        api_key = self._api_keys.get(provider, "")

        if not api_key:
            raise ValueError(f"{provider.upper()} API kaliti o'rnatilmagan")

        return OpenAI(api_key=api_key, base_url=base_url)

    def _select_model(self, provider: str, mode: str, model_override: Optional[str] = None) -> str:
        """Rejim va provayderga qarab modelni tanlash."""
        if model_override:
            return model_override
        provider_config = self._config["providers"].get(provider, {})
        models = provider_config.get("models", {})
        mode_key = mode.lower()
        return models.get(mode_key, models.get("pro", ""))

    def route_request(
        self,
        messages: list[dict],
        mode: str = "pro",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """So'rovni mos provayderga yo'naltirish.

        Agar _forced_provider o'rnatilgan bo'lsa — faqat shu providerni ishlatish
        (fallback QILMASLIK). Agar _forced_model o'rnatilgan bo'lsa — shu modelni
        ishlatish. Aks holda — fallback_order bilan ishlash.

        Args:
            messages: OpenAI-format xabarlar ro'yxati
            mode: "fast" | "code" | "pro"
            model: Model override (ixtiyoriy)
            temperature: Temperatura parametri
            max_tokens: Maksimal tokenlar soni

        Returns:
            AI javobi matni
        """
        effective_model = model or self._forced_model

        # Majburiy provayder tanlangan bo'lsa — faqat shuni ishlatish
        if self._forced_provider:
            provider = self._forced_provider
            api_key = self._api_keys.get(provider)
            if not api_key:
                raise RuntimeError(
                    f"'{provider}' provayderining API kaliti o'rnatilmagan. "
                    f"Avtomatik rejimga qaytish uchun /auto buyrug'ini ishlating."
                )
            client = self._get_client(provider)
            selected_model = self._select_model(provider, mode, effective_model)
            if not selected_model:
                raise RuntimeError(
                    f"'{provider}' provayderida '{mode}' rejimi uchun model topilmadi."
                )
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""
            except Exception:
                logger.exception(
                    f"Error in forced provider '{provider}' with model '{selected_model}'"
                )
                raise RuntimeError(
                    f"'{provider}' provayderida xatolik yuz berdi. "
                    f"Iltimos, API kalitini yoki provayder holatini tekshiring."
                ) from None

        # Avtomatik rejim — fallback_order bo'yicha
        fallback_order: list[str] = self._config.get(
            "fallback_order", ["gemini", "deepseek", "openrouter", "groq", "huggingface"]
        )
        last_error: Optional[Exception] = None

        for provider in fallback_order:
            api_key = self._api_keys.get(provider)
            if not api_key:
                continue

            try:
                client = self._get_client(provider)
                selected_model = self._select_model(provider, mode, effective_model)

                if not selected_model:
                    continue

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""

            except Exception as exc:
                last_error = exc
                continue

        # Hech qanday provayder ishlamasa
        if last_error:
            logger.error(f"All AI providers failed. Last error: {last_error}", exc_info=True)
            raise RuntimeError(
                "Hech qanday AI provayderi javob bermadi. "
                "API kalitlarini va internet ulanishini tekshiring."
            )
        raise RuntimeError(
            "API kalitlari topilmadi. Kamida bitta provayder API kalitini o'rnating: "
            "GEMINI_API_KEY_1, DEEPSEEK_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, "
            "yoki HUGGINGFACE_API_KEY."
        )

    def get_available_providers(self) -> list[str]:
        """API kaliti mavjud provayderlar ro'yxati."""
        return [p for p, key in self._api_keys.items() if key]

    def is_available(self) -> bool:
        """Kamida bitta provayder mavjudligini tekshirish."""
        return bool(self.get_available_providers())
