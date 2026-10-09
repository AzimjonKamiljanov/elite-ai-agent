"""
JARVIS Lightweight Expense Tracker.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_EXPENSE_FILE = Path("data/expenses.json")
_TASHKENT_TZ = timezone(timedelta(hours=5))

# Xarajat kategoriyalari
_CATEGORIES = {
    "ovqat": "food",
    "food": "food",
    "transport": "transport",
    "ko'ngilochar": "entertainment",
    "entertainment": "entertainment",
    "kiyim": "clothing",
    "clothing": "clothing",
    "sog'liq": "health",
    "health": "health",
    "ta'lim": "education",
    "education": "education",
}


def _today_str() -> str:
    """Bugungi sanani ``YYYY-MM-DD`` formatida qaytarish."""
    return datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d")


def _now_str() -> str:
    """Hozirgi vaqtni ``YYYY-MM-DD HH:MM:SS`` formatida qaytarish."""
    return datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")


class ExpenseTracker:
    """Oddiy xarajat kuzatuv tizimi."""

    def __init__(self) -> None:
        self._expenses: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Xarajatlarni fayldan yuklash."""
        try:
            if _EXPENSE_FILE.exists():
                with _EXPENSE_FILE.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._expenses = data if isinstance(data, list) else []
        except Exception:
            self._expenses = []

    def _save(self) -> None:
        """Xarajatlarni faylga saqlash."""
        try:
            _EXPENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _EXPENSE_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._expenses, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_expense(
        self,
        amount: int,
        description: str,
        category: str = "general",
    ) -> dict:
        """Xarajat qo'shish.

        Args:
            amount: Miqdor (so'mda).
            description: Tavsif.
            category: Kategoriya (default ``"general"``).

        Returns:
            Qo'shilgan xarajat yozuvi.
        """
        normalized_cat = _CATEGORIES.get(category.lower(), category)
        entry: dict = {
            "id": str(uuid.uuid4()),
            "amount": max(0, amount),
            "description": description,
            "category": normalized_cat,
            "date": _today_str(),
            "created_at": _now_str(),
        }
        self._expenses.append(entry)
        self._save()
        return entry

    def get_today_expenses(self) -> list[dict]:
        """Bugungi xarajatlar ro'yxati."""
        today = _today_str()
        return [e for e in self._expenses if e.get("date") == today]

    def get_weekly_summary(self) -> dict:
        """Haftalik xulosa.

        Returns:
            ``{"total": int, "by_category": dict, "daily_average": int}``
        """
        now = datetime.now(_TASHKENT_TZ)
        week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
        week_expenses = [
            e for e in self._expenses if e.get("date", "") >= week_start
        ]
        total = sum(e.get("amount", 0) for e in week_expenses)
        by_category: dict[str, int] = {}
        for e in week_expenses:
            cat = e.get("category", "general")
            by_category[cat] = by_category.get(cat, 0) + e.get("amount", 0)
        daily_average = total // 7 if total else 0
        return {"total": total, "by_category": by_category, "daily_average": daily_average}

    def get_monthly_summary(self) -> dict:
        """Oylik xulosa.

        Returns:
            ``{"total": int, "by_category": dict, "count": int}``
        """
        now = datetime.now(_TASHKENT_TZ)
        month_prefix = now.strftime("%Y-%m")
        month_expenses = [
            e for e in self._expenses if e.get("date", "").startswith(month_prefix)
        ]
        total = sum(e.get("amount", 0) for e in month_expenses)
        by_category: dict[str, int] = {}
        for e in month_expenses:
            cat = e.get("category", "general")
            by_category[cat] = by_category.get(cat, 0) + e.get("amount", 0)
        return {"total": total, "by_category": by_category, "count": len(month_expenses)}

    def format_summary(self) -> str:
        """Chiroyli formatlangan xulosa matni."""
        today_exp = self.get_today_expenses()
        today_total = sum(e.get("amount", 0) for e in today_exp)
        weekly = self.get_weekly_summary()
        monthly = self.get_monthly_summary()

        lines = [
            "💰 Xarajat Xulosasi",
            "",
            f"📅 Bugun: {today_total:,} so'm ({len(today_exp)} ta xarajat)",
        ]
        if today_exp:
            for e in today_exp[-5:]:
                lines.append(f"  • {e.get('description', '-')}: {e.get('amount', 0):,} so'm")

        lines.append("")
        lines.append(f"📆 Haftalik jami: {weekly['total']:,} so'm")
        lines.append(f"  Kunlik o'rtacha: {weekly['daily_average']:,} so'm")
        if weekly["by_category"]:
            lines.append("  Kategoriyalar:")
            for cat, amt in sorted(weekly["by_category"].items(), key=lambda x: -x[1]):
                lines.append(f"    • {cat}: {amt:,} so'm")

        lines.append("")
        lines.append(f"🗓  Oylik jami: {monthly['total']:,} so'm ({monthly['count']} ta xarajat)")
        return "\n".join(lines)
