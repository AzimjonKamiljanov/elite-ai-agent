"""
JARVIS Intelligence Modules — Cognitive, Focus, Procrastination, Narrative, Tutor, Personality.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta


class CognitiveLoadBalancer:
    """Monitors mental workload and suggests load-reduction strategies."""

    def calculate_load(self, pending_tasks: int, overdue_count: int) -> str:
        """Return load level: 'low', 'moderate', 'high', or 'critical'."""
        if overdue_count >= 3 or pending_tasks >= 10:
            return "critical"
        if overdue_count >= 1 or pending_tasks >= 6:
            return "high"
        if pending_tasks >= 3:
            return "moderate"
        return "low"

    def get_analysis(self, homework_mgr) -> dict:
        """Return cognitive load analysis dict with level and suggestion."""
        try:
            stats = homework_mgr.get_stats()
            pending = stats.get("pending_homework", 0) + stats.get("pending_tasks", 0)
            overdue = stats.get("overdue_homework", 0)
        except Exception:
            pending = 0
            overdue = 0

        level = self.calculate_load(pending, overdue)

        suggestions = {
            "low": "✅ Ish yuki past. Yangi maqsadlar qo'ying yoki chuqur o'qishga kirishing.",
            "moderate": "⚡ Ish yuki o'rtacha. Muhim vazifalarni avval bajaring.",
            "high": (
                "⚠️ Ish yuki yuqori! "
                "5-10 daqiqa dam oling, keyin eng muhim vazifadan boshlang."
            ),
            "critical": (
                "🚨 Kritik ish yuki! "
                "Ba'zi vazifalarni keyinga qoldiring yoki kimga topshiring. "
                "Dam olish zarur."
            ),
        }

        return {
            "level": level,
            "pending": pending,
            "overdue": overdue,
            "suggestion": suggestions[level],
        }

    def format_report(self, homework_mgr) -> str:
        """Return a formatted cognitive load report string."""
        analysis = self.get_analysis(homework_mgr)
        level_icons = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}
        icon = level_icons.get(analysis["level"], "⚪")
        lines = [
            "🧠 Kognitiv Yuk Tahlili",
            f"{icon} Daraja: {analysis['level'].upper()}",
            f"📋 Bajarilmagan vazifalar: {analysis['pending']}",
            f"⚠️  Muddati o'tgan: {analysis['overdue']}",
            f"💡 Tavsiya: {analysis['suggestion']}",
        ]
        return "\n".join(lines)


class TimePerceptionEngine:
    """Structures time using Pomodoro cycles and deep-work focus sessions."""

    def __init__(self) -> None:
        self._focus_start: float | None = None
        self._focus_duration: int = 25
        self._sessions_completed: int = 0

    @property
    def is_active(self) -> bool:
        return self._focus_start is not None

    def start_focus(self, minutes: int = 25) -> str:
        """Start a Pomodoro / focus session."""
        self._focus_start = time.time()
        self._focus_duration = minutes
        return (
            f"🍅 Pomodoro boshlandi! {minutes} daqiqa chuqur ish.\n"
            f"📵 Distraksiyalarni o'chiring.\n"
            f"Tugatish uchun: /focus stop"
        )

    def stop_focus(self) -> str:
        """Stop the current focus session."""
        if self._focus_start is None:
            return "⚠️ Faol focus sessiya yo'q."
        elapsed = int((time.time() - self._focus_start) / 60)
        self._focus_start = None
        self._sessions_completed += 1
        return (
            f"✅ Focus sessiya to'xtatildi.\n"
            f"⏱ Ishlagan vaqt: {elapsed} daqiqa.\n"
            f"☕ 5 daqiqa dam oling!"
        )

    def get_focus_stats(self) -> dict:
        """Return current focus session state and stats."""
        if self._focus_start is None:
            return {
                "active": False,
                "sessions_completed": self._sessions_completed,
            }
        elapsed = (time.time() - self._focus_start) / 60
        remaining = max(0.0, self._focus_duration - elapsed)
        return {
            "active": True,
            "elapsed_minutes": round(elapsed, 1),
            "remaining_minutes": round(remaining, 1),
            "duration_minutes": self._focus_duration,
            "sessions_completed": self._sessions_completed,
        }

    def format_status(self) -> str:
        """Return a human-readable focus status string."""
        stats = self.get_focus_stats()
        if not stats["active"]:
            return (
                f"😴 Focus sessiya yo'q. "
                f"Jami bajarilgan: {stats['sessions_completed']} sessiya.\n"
                f"Boshlash uchun: /focus [daqiqa]"
            )
        return (
            f"🔥 Focus faol! "
            f"{stats['remaining_minutes']} daqiqa qoldi "
            f"({stats['elapsed_minutes']} / {stats['duration_minutes']} daqiqa)."
        )


class AntiProcrastinationEngine:
    """Detects repeated delays and suggests strategies to overcome procrastination."""

    _STALE_DAYS = 3
    _MAX_DESCRIPTION_LENGTH = 30

    def check_procrastination(self, homework_mgr) -> str | None:
        """Check if any tasks have been pending for more than 3 days."""
        try:
            pending = homework_mgr.get_pending_homework()
            stale = []
            cutoff = datetime.now() - timedelta(days=self._STALE_DAYS)
            for hw in pending:
                # created_at is an ISO datetime string stored in the model
                created_str = getattr(hw, "created_at", None)
                if created_str:
                    try:
                        created_dt = datetime.fromisoformat(created_str)
                        if created_dt < cutoff:
                            stale.append(hw)
                    except (ValueError, TypeError):
                        pass
            if stale:
                names = ", ".join(
                    f"{h.subject}: {h.description[:self._MAX_DESCRIPTION_LENGTH]}" for h in stale[:3]
                )
                return (
                    f"⏳ {len(stale)} ta vazifa {self._STALE_DAYS}+ kundan beri bajarilmagan!\n"
                    f"📌 Ular: {names}\n"
                    f"💡 5 daqiqalik texnika: birinchi vazifani 5 daqiqada bajaring!"
                )
        except Exception:
            pass
        return None

    def get_suggestions(self) -> list[str]:
        """Return a list of anti-procrastination tips."""
        return [
            "⏱ 5-daqiqalik texnika: faqat 5 daqiqa boshla, to'xtash huquqing bor.",
            "🔪 Micro-qadam: vazifani eng kichik bosqichlarga bo'l.",
            "📵 Telefon va ijtimoiy tarmoqlarni 25 daqiqaga o'chir.",
            "🏆 Birinchi eng og'ir vazifani hal qil (Eat the Frog).",
            "🎯 Bugun faqat 1-3 ta muhim vazifaga e'tibor qarat.",
        ]


class LifeNarrativeEngine:
    """Weekly reflection and life narrative engine."""

    def get_weekly_reflection(self, homework_mgr) -> str:
        """Generate a weekly reflection summary."""
        try:
            stats = homework_mgr.get_stats()
            completed = stats.get("completed_homework", 0) + stats.get("completed_tasks", 0)
            pending = stats.get("pending_homework", 0) + stats.get("pending_tasks", 0)
            overdue = stats.get("overdue_homework", 0)
            rate = stats.get("completion_rate", 0)
        except Exception:
            completed = pending = overdue = 0
            rate = 0

        week_str = datetime.now().strftime("%Y — hafta %W")

        if rate >= 80:
            growth = "🚀 Ajoyib hafta! Siz o'z maqsadlaringizga sodiqsiz."
        elif rate >= 50:
            growth = "📈 Yaxshi taraqqiyot. Kelasi hafta yanada yaxshilanadi."
        else:
            growth = "💪 Qiyin hafta bo'ldi, lekin har qanday qadam oldinga!"

        lines = [
            f"📖 Haftalik Ko'rib Chiqish — {week_str}",
            "",
            f"🏆 Yutuqlar: {completed} ta vazifa bajarildi",
            f"⚡ Qiyinchiliklar: {overdue} ta muddati o'tgan vazifa",
            f"📋 Qolganlar: {pending} ta bajarilmamish",
            f"📊 Bajarilish darajasi: {rate}%",
            "",
            "🔍 Tahlil:",
            growth,
            "",
            "🌱 O'sish bo'yicha maslahat:",
            "  • Har kuni 1 ta muhim vazifani birinchi bajaring.",
            "  • Haftada 3 ta focus sessiya rejalang.",
            "  • Dam olish va o'qish o'rtasida muvozanat saqlang.",
        ]
        return "\n".join(lines)


class AITutorMode:
    """AI-powered tutoring: explains topics, creates summaries, generates quizzes."""

    def explain_topic_prompt(self, topic: str) -> str:
        """Return a prompt for explaining a topic using the Feynman technique."""
        return (
            f"Explain '{topic}' using the Feynman technique:\n"
            f"1. Simple explanation (as if to a 12-year-old)\n"
            f"2. Core concepts with examples\n"
            f"3. Common misconceptions to avoid\n"
            f"4. 3 practice questions to test understanding"
        )

    def create_study_plan_prompt(self, subject: str, days: int = 7) -> str:
        """Return a prompt for creating a study plan."""
        return (
            f"Create a {days}-day study plan for: {subject}\n"
            f"Include: daily topics, time blocks, review sessions, and milestones."
        )

    def generate_quiz_prompt(self, topic: str, count: int = 5) -> str:
        """Return a prompt for generating a quiz."""
        return (
            f"Generate {count} multiple-choice questions about: {topic}\n"
            f"For each question provide: question, 4 options (A-D), correct answer, brief explanation."
        )


class PersonalityAdapter:
    """Adapts JARVIS personality to user preferences."""

    _PREFERENCES = {
        "concise": "Be concise and direct. No extra explanations.",
        "detailed": "Be thorough and detailed. Provide full explanations with examples.",
        "motivational": "Be encouraging and motivational. Celebrate small wins.",
        "neutral": "Be neutral and objective. Stick to facts.",
        "technical": "Use technical language and precise terminology.",
        "simple": "Use simple language. Avoid jargon.",
    }

    def __init__(self) -> None:
        self._preference: str = "neutral"

    def set_preference(self, preference: str) -> bool:
        """Set personality preference. Returns True if valid."""
        key = preference.lower()
        if key in self._PREFERENCES:
            self._preference = key
            return True
        return False

    def get_instruction(self) -> str:
        """Return instruction text for system prompts."""
        return self._PREFERENCES.get(self._preference, "")

    def list_preferences(self) -> list[str]:
        """Return list of available preferences."""
        return list(self._PREFERENCES.keys())

    @property
    def current(self) -> str:
        return self._preference
