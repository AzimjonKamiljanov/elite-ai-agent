"""
Til aniqlovchi va javob tili boshqaruvchisi.
Auto-detect: O'zbek, Ingliz, Rus.
"""

from __future__ import annotations

import re

# Uzbek-specific characters (NOT 'o' which is too common in English)
_UZ_CHARS = set("ʻʼ")  # Special apostrophe characters unique to Uzbek Latin
_UZ_UNIQUE_CHARS = set("qg")  # 'q' and 'g' are distinctive but not exclusive
_UZ_WORDS = {
    "va", "bu", "men", "sen", "u", "biz", "siz", "ular",
    "nima", "qanday", "qachon", "qayer", "nega", "kim",
    "ha", "yoʻq", "yo'q", "iltimos", "rahmat", "kerak",
    "bor", "qil", "qiling", "ber", "ko'r",
    "menga", "senga", "unga", "bizga", "sizga", "ularga",
    "kelajak", "bugun", "ertaga", "kecha", "hozir",
    "salom", "xayr", "yaxshi", "yomon", "katta", "kichik",
    "uyga", "maktab", "dars", "kitob", "ish",
}
_RU_CHARS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")


class LanguageDetector:
    """Matn tilini aniqlash va joriy til boshqaruvi."""

    def __init__(self) -> None:
        self._current_language: str = "uz"

    def detect(self, text: str) -> str:
        """Matn tilini aniqlash.

        Returns:
            "uz" — O'zbek
            "en" — Ingliz
            "ru" — Rus
        """
        if not text or not text.strip():
            return self._current_language

        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)

        # Rus harflari borligini tekshirish
        ru_char_count = sum(1 for ch in text if ch in _RU_CHARS)
        if ru_char_count > len(text) * 0.3:
            self._current_language = "ru"
            return "ru"

        # O'zbek-spetsifik harflar yoki so'zlar
        uz_word_matches = sum(1 for w in words if w in _UZ_WORDS)
        uz_char_matches = sum(1 for ch in text if ch in _UZ_CHARS)

        if uz_char_matches >= 1 or uz_word_matches >= 1:
            self._current_language = "uz"
            return "uz"

        # Ingliz tili — lotin harflari ko'p bo'lsa
        latin_count = sum(1 for ch in text if ch.isalpha() and ch.isascii())
        if latin_count > len(text) * 0.5:
            # O'zbek lotin alifbosidan farqlash (ko'p umumiy so'zlar)
            # Agar o'zbek so'zlari yo'q bo'lsa, ingliz
            self._current_language = "en"
            return "en"

        return self._current_language

    def get_response_language(self) -> str:
        """Joriy javob tilini qaytarish."""
        return self._current_language

    def set_language(self, lang: str) -> None:
        """Tilni qo'lda o'rnatish."""
        if lang in ("uz", "en", "ru"):
            self._current_language = lang

    def get_language_instruction(self) -> str:
        """Joriy til uchun tizim ko'rsatmasini qaytarish."""
        instructions = {
            "uz": "Foydalanuvchi O'zbek tilida yozmoqda. O'zbek tilida javob bering.",
            "en": "The user is writing in English. Respond in English.",
            "ru": "Пользователь пишет на русском. Отвечайте на русском языке.",
        }
        return instructions.get(self._current_language, "")
