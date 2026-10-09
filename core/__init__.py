from .ai_router import AIRouter
from .education import SmartEducation
from .jarvis import Jarvis
from .language import LanguageDetector
from .memory import MemoryManager
from .modes import ModeManager
from .rag import RAGEngine
from .tools import ToolRegistry

try:
    from .auto_mode import AutoModeSwitcher
except Exception:
    AutoModeSwitcher = None  # type: ignore[assignment,misc]

try:
    from .calendar_system import CalendarSystem
except Exception:
    CalendarSystem = None  # type: ignore[assignment,misc]

try:
    from .class_automation import ClassAutomation
except Exception:
    ClassAutomation = None  # type: ignore[assignment,misc]

try:
    from .energy_tracker import EnergyTracker
except Exception:
    EnergyTracker = None  # type: ignore[assignment,misc]

try:
    from .expense_tracker import ExpenseTracker
except Exception:
    ExpenseTracker = None  # type: ignore[assignment,misc]

try:
    from .intent_parser import IntentParser
except Exception:
    IntentParser = None  # type: ignore[assignment,misc]

try:
    from .smart_features import SmartFeatures
except Exception:
    SmartFeatures = None  # type: ignore[assignment,misc]

try:
    from .ui_renderer import UIRenderer
except Exception:
    UIRenderer = None  # type: ignore[assignment,misc]

try:
    from .voice import VoiceEngine
except Exception:
    VoiceEngine = None  # type: ignore[assignment,misc]

try:
    from .telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = None  # type: ignore[assignment,misc]

__all__ = [
    "AIRouter",
    "AutoModeSwitcher",
    "CalendarSystem",
    "ClassAutomation",
    "EnergyTracker",
    "ExpenseTracker",
    "IntentParser",
    "Jarvis",
    "LanguageDetector",
    "MemoryManager",
    "ModeManager",
    "RAGEngine",
    "SmartEducation",
    "SmartFeatures",
    "TelegramNotifier",
    "ToolRegistry",
    "UIRenderer",
    "VoiceEngine",
]
