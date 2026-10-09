"""
Mode tizimi — FAST, CODE, PRO va kengaytirilgan rejimlarni boshqarish.
"""

from __future__ import annotations

_MODES: dict[str, dict] = {
    "fast": {
        "name": "FAST",
        "system_prompt": (
            "You are JARVIS-X, an ultra-fast AI assistant. "
            "Give concise, direct answers. No extra explanations. "
            "Max 2-3 sentences. Be precise and efficient."
        ),
        "preferred_models": ["fast"],
        "behavior_rules": [
            "ultra-concise responses",
            "no preamble or filler text",
            "direct answers only",
        ],
    },
    "code": {
        "name": "CODE",
        "system_prompt": (
            "You are JARVIS-X, an expert coding assistant. "
            "Provide working, production-ready code. "
            "Support multiple programming languages. "
            "Include brief comments only when necessary. "
            "Always provide complete, runnable code snippets."
        ),
        "preferred_models": ["code"],
        "behavior_rules": [
            "code-first responses",
            "use best coding models",
            "multi-language support",
            "working code only",
        ],
    },
    "pro": {
        "name": "PRO",
        "system_prompt": (
            "You are JARVIS-X, a professional AI research assistant. "
            "Provide detailed, well-researched, step-by-step responses. "
            "Think carefully before answering. "
            "Include reasoning, examples, and thorough explanations. "
            "Be comprehensive and accurate."
        ),
        "preferred_models": ["pro"],
        "behavior_rules": [
            "detailed explanations",
            "step-by-step reasoning",
            "research-grade quality",
            "comprehensive answers",
        ],
    },
    "study": {
        "name": "STUDY",
        "system_prompt": (
            "You are JARVIS-X, an intelligent study assistant. "
            "Help the user learn effectively. "
            "Create summaries, explain concepts, generate practice questions. "
            "Use the Feynman technique when explaining."
        ),
        "preferred_models": ["pro"],
        "behavior_rules": [
            "structured explanations",
            "generate quizzes on request",
            "exam preparation",
            "multi-language support",
        ],
    },
    "planner": {
        "name": "PLANNER",
        "system_prompt": (
            "You are JARVIS-X, a life planning assistant. "
            "Help organize daily routines, set priorities, manage time blocks, "
            "and create actionable plans."
        ),
        "preferred_models": ["fast"],
        "behavior_rules": [
            "time-aware responses",
            "schedule optimization",
            "proactive suggestions",
        ],
    },
    "focus": {
        "name": "FOCUS",
        "system_prompt": (
            "You are JARVIS-X in focus mode. "
            "Minimize distractions. Give ultra-brief responses. "
            "Only respond to the current task. No side conversations."
        ),
        "preferred_models": ["fast"],
        "behavior_rules": [
            "minimal responses",
            "focus-oriented",
            "pomodoro support",
            "distraction blocking",
        ],
    },
    "analytics": {
        "name": "ANALYTICS",
        "system_prompt": (
            "You are JARVIS analytics assistant. "
            "Provide productivity insights, study time analysis, "
            "task completion rates, and weekly reports. "
            "Use data to suggest improvements."
        ),
        "preferred_models": ["pro"],
        "behavior_rules": [
            "data-driven insights",
            "productivity tracking",
            "weekly reports",
            "improvement suggestions",
        ],
    },
    "automation": {
        "name": "AUTOMATION",
        "system_prompt": (
            "You are JARVIS automation assistant. "
            "Help automate repetitive tasks, create scripts, "
            "set up workflows, and reduce manual effort."
        ),
        "preferred_models": ["code"],
        "behavior_rules": [
            "task automation",
            "workflow creation",
            "efficiency optimization",
        ],
    },
}


class ModeManager:
    """Rejim boshqaruvchisi — FAST, CODE, PRO va kengaytirilgan rejimlar."""

    def __init__(self, default_mode: str = "pro") -> None:
        self._current_mode = default_mode if default_mode in _MODES else "pro"

    def get_mode(self, name: str | None = None) -> dict:
        """Berilgan yoki joriy rejim ma'lumotlarini qaytarish."""
        key = (name or self._current_mode).lower()
        return _MODES.get(key, _MODES["pro"])

    def set_mode(self, name: str) -> bool:
        """Rejimni o'zgartirish. Muvaffaqiyatli bo'lsa True qaytaradi."""
        key = name.lower()
        if key in _MODES:
            self._current_mode = key
            return True
        return False

    def get_current_mode_name(self) -> str:
        """Joriy rejim nomini qaytarish."""
        return self._current_mode

    def get_system_prompt(self) -> str:
        """Joriy rejim uchun tizim promptini qaytarish."""
        return _MODES[self._current_mode]["system_prompt"]

    def get_preferred_models(self) -> list[str]:
        """Joriy rejim uchun afzal modellarni qaytarish."""
        return _MODES[self._current_mode]["preferred_models"]

    def list_modes(self) -> list[str]:
        """Mavjud rejimlar ro'yxati."""
        return list(_MODES.keys())
