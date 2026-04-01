"""
JARVIS Energy & Mood Tracker.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_ENERGY_FILE = Path("data/energy.json")
_TASHKENT_TZ = timezone(timedelta(hours=5))

_LEVEL_LABELS = {
    1: "Juda past 😴",
    2: "Past 😔",
    3: "O'rtacha 😐",
    4: "Yaxshi 😊",
    5: "Juda yaxshi 🚀",
}

_SUGGESTIONS = {
    1: "Hozir dam olish vaqti. Eng muhim 1 vazifani bajaring, keyin istirehatlang.",
    2: "Engil ishlardan boshlang. Katta vazifalarni keyinga qoldiring.",
    3: "Normal ish sur'atida davom eting. Qisqa tanaffuslar foydali.",
    4: "Siz samarali ishlay olasiz. Muhim vazifalarni hozir bajaring.",
    5: "Juda yaxshi! Bu paytdan to'liq foydalaning — murakkab vazifalarni hal qiling.",
}


def _today_str() -> str:
    """Bugungi sanani ``YYYY-MM-DD`` formatida qaytarish."""
    return datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d")


def _now_str() -> str:
    """Hozirgi vaqtni ``YYYY-MM-DD HH:MM:SS`` formatida qaytarish."""
    return datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")


class EnergyTracker:
    """Kunlik energiya va kayfiyat kuzatuv."""

    def __init__(self) -> None:
        self._records: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Energiya yozuvlarini fayldan yuklash."""
        try:
            if _ENERGY_FILE.exists():
                with _ENERGY_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._records = data if isinstance(data, list) else []
        except Exception:
            self._records = []

    def _save(self) -> None:
        """Energiya yozuvlarini faylga saqlash."""
        try:
            _ENERGY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _ENERGY_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def log_energy(self, level: int, note: str = "") -> dict:
        """Energiya darajasini yozish (1-5).

        Args:
            level: Energiya darajasi (1 — juda past, 5 — juda yuqori).
            note: Ixtiyoriy izoh.

        Returns:
            Saqlangan yozuv.
        """
        level = max(1, min(5, int(level)))
        entry: dict = {
            "date": _today_str(),
            "created_at": _now_str(),
            "level": level,
            "label": _LEVEL_LABELS.get(level, ""),
            "note": note,
        }
        # Bugungi mavjud yozuvni yangilash yoki yangi qo'shish
        today = _today_str()
        for i, rec in enumerate(self._records):
            if rec.get("date") == today:
                self._records[i] = entry
                self._save()
                return entry
        self._records.append(entry)
        self._save()
        return entry

    def get_today_energy(self) -> Optional[dict]:
        """Bugungi energiya yozuvi."""
        today = _today_str()
        for rec in reversed(self._records):
            if rec.get("date") == today:
                return rec
        return None

    def get_weekly_average(self) -> float:
        """Haftalik o'rtacha energiya darajasi (0.0 — yozuv yo'q)."""
        now = datetime.now(_TASHKENT_TZ)
        week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
        week_records = [
            r for r in self._records if r.get("date", "") >= week_start
        ]
        if not week_records:
            return 0.0
        return sum(r.get("level", 0) for r in week_records) / len(week_records)

    def detect_burnout_risk(self) -> bool:
        """Ketma-ket 3+ kun past energiya (1-2) — burnout xavfi.

        Returns:
            ``True`` — burnout xavfi bor, ``False`` — yo'q.
        """
        now = datetime.now(_TASHKENT_TZ)
        low_streak = 0
        for i in range(1, 8):
            date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            found = next((r for r in self._records if r.get("date") == date_str), None)
            if found and found.get("level", 5) <= 2:
                low_streak += 1
            else:
                break
        return low_streak >= 3

    def get_suggestion(
        self, today: Optional[dict] = None, burnout: Optional[bool] = None
    ) -> str:
        """Bugungi energiyaga qarab taklif.

        Args:
            today: Bugungi energiya yozuvi (ixtiyoriy).
            burnout: Burnout xavfi bormi (ixtiyoriy).

        Returns:
            Tavsiya matni.
        """
        if today is None:
            today = self.get_today_energy()
        if today is None:
            return "Energiya darajangizni kiriting (1-5)."

        level = today.get("level", 3)
        if burnout is None:
            burnout = self.detect_burnout_risk()

        suggestion = _SUGGESTIONS.get(level, "")
        if burnout:
            suggestion += "\n⚠️  Burnout xavfi: bir necha kun dam oling!"
        return suggestion

    def format_report(self) -> str:
        """Formatlangan energiya hisoboti."""
        today = self.get_today_energy()
        weekly_avg = self.get_weekly_average()
        burnout = self.detect_burnout_risk()

        lines = ["⚡ Energiya Hisoboti", ""]
        if today:
            level = today.get("level", 0)
            label = today.get("label", "")
            lines.append(f"📅 Bugun: {level}/5 — {label}")
            if today.get("note"):
                lines.append(f"  Izoh: {today['note']}")
        else:
            lines.append("📅 Bugun: yozilmagan")

        if weekly_avg > 0:
            lines.append(f"📆 Haftalik o'rtacha: {weekly_avg:.1f}/5")

        if burnout:
            lines.append("⚠️  Burnout xavfi aniqlandi!")

        suggestion = self.get_suggestion(today=today, burnout=burnout)
        if suggestion:
            lines.append("")
            lines.append(f"💡 {suggestion}")

        return "\n".join(lines)
