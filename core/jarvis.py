"""
JARVIS-X — Asosiy Orchestrator.
Barcha modullarni birlashtiradi va foydalanuvchi so'rovlarini qayta ishlaydi.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .ai_router import AIRouter
from .auto_mode import AutoModeSwitcher
from .education import SmartEducation
from .intelligence import (
    AITutorMode,
    AntiProcrastinationEngine,
    CognitiveLoadBalancer,
    LifeNarrativeEngine,
    PersonalityAdapter,
    TimePerceptionEngine,
)
from .language import LanguageDetector
from .memory import MemoryManager
from .modes import ModeManager
from .rag import RAGEngine
from .tools import ToolRegistry

_MODE_COMMANDS = {
    "/fast": "fast",
    "/code": "code",
    "/pro": "pro",
    "/study": "study",
    "/planner": "planner",
    "/analytics": "analytics",
    "/automation": "automation",
    "/default": "pro",
}

_PROVIDER_CMD = "/provider"
_PROVIDERS_CMD = "/providers"
_MODEL_CMD = "/model"
_MODELS_CMD = "/models"
_AUTO_CMD = "/auto"
_STATUS_CMD = "/status"

_SYSTEM_BASE = (
    "You are JARVIS, a professional AI life assistant designed to act as a second brain, "
    "strategic thinking partner, and productivity optimizer. "
    "You help the user think, learn, plan, and act more effectively.\n\n"
    "Core principles:\n"
    "- Always reduce mental effort\n"
    "- Provide structured outputs\n"
    "- Offer actionable steps\n"
    "- Adapt to user behavior\n"
    "- Never overcomplicate\n"
    "- Never overwhelm with notifications\n"
    "- Never provide generic advice"
)


def _load_system_prompt() -> str:
    """System promptlarni fayllardan yuklash.

    config/prompts/ papkasidagi system_prompt.md, core_behavior.md va
    ui_rules.md fayllarini birlashtiradi.  Fayl topilmasa o'tkazib yuboriladi.
    Hech qanday fayl topilmasa mavjud _SYSTEM_BASE ishlatiladi (backward compatible).

    Returns:
        System prompt matni.
    """
    prompts_dir = Path(__file__).parent.parent / "config" / "prompts"
    combined = ""
    for prompt_file in ["system_prompt.md", "core_behavior.md", "ui_rules.md"]:
        path = prompts_dir / prompt_file
        if path.exists():
            try:
                combined += path.read_text(encoding="utf-8") + "\n\n"
            except Exception:
                continue
    return combined.strip() or _SYSTEM_BASE


class Jarvis:
    """JARVIS-X — Asosiy AI Agent Orchestrator."""

    def __init__(
        self,
        default_mode: str = "pro",
        voice_enabled: bool = False,
        rag_dir: str | None = None,
    ) -> None:
        self.router = AIRouter()
        self.mode_manager = ModeManager(default_mode=default_mode)
        self.language = LanguageDetector()
        self.memory = MemoryManager()
        self.tools = ToolRegistry()
        self.rag = RAGEngine()
        self.education = SmartEducation()
        # Intelligence modules
        self.cognitive = CognitiveLoadBalancer()
        self.time_engine = TimePerceptionEngine()
        self.anti_procrastination = AntiProcrastinationEngine()
        self.narrative = LifeNarrativeEngine()
        self.tutor = AITutorMode()
        self.personality = PersonalityAdapter()
        self.auto_mode = AutoModeSwitcher()
        self._register_builtin_tools()

        # RAG hujjatlarini yuklash
        if rag_dir:
            try:
                self.rag.ingest_directory(rag_dir)
            except Exception:
                pass

    def _get_homework_manager(self):
        """Return a HomeworkManager instance, or None on failure."""
        try:
            from life import HomeworkManager
            return HomeworkManager()
        except Exception:
            return None

    def _register_builtin_tools(self) -> None:
        """O'rnatilgan vositalarni ro'yxatga olish."""
        try:
            from tools.web_search import WebSearchTool

            ws = WebSearchTool()
            self.tools.register("web_search", ws.search, "Internet qidiruvchi")
        except Exception:
            pass

        try:
            from tools.file_manager import FileManagerTool

            fm = FileManagerTool()
            self.tools.register("read_file", fm.read_file, "Faylni o'qish")
            self.tools.register("write_file", fm.write_file, "Faylga yozish")
            self.tools.register("list_dir", fm.list_directory, "Katalogni ko'rish")
        except Exception:
            pass

        try:
            from tools.code_executor import CodeExecutorTool

            ce = CodeExecutorTool()
            self.tools.register("run_code", ce.execute, "Python kodni bajarish")
        except Exception:
            pass

        try:
            from tools.terminal import TerminalTool

            term = TerminalTool()
            self.tools.register("terminal", term.execute, "Terminal buyrug'ini bajarish")
        except Exception:
            pass

    def process(self, user_input: str) -> str:
        """Foydalanuvchi kiritishini qayta ishlash va javob qaytarish.

        ReAct tsikli: Reason → Act → Observe → Respond

        Args:
            user_input: Foydalanuvchi matni

        Returns:
            JARVIS javobi
        """
        if not user_input.strip():
            return ""

        # Auto mode switching (slash buyruqlar uchun emas)
        if not user_input.startswith("/"):
            detected_mode = self.auto_mode.detect_mode(user_input)
            current_mode = self.mode_manager.get_current_mode_name()
            if self.auto_mode.should_switch(current_mode, detected_mode):
                self.mode_manager.set_mode(detected_mode)

        # Rejim almashtirish buyruqlarini tekshirish
        parts = user_input.strip().split()
        cmd = parts[0].lower() if parts else ""
        if cmd in _MODE_COMMANDS:
            mode_name = _MODE_COMMANDS[cmd]
            self.mode_manager.set_mode(mode_name)
            mode_info = self.mode_manager.get_mode()
            return f"✅ Rejim o'zgartirildi: **{mode_info['name']}**"

        # /provider yoki /providers — provayder holati yoki tanlash
        if cmd in (_PROVIDER_CMD, _PROVIDERS_CMD):
            if len(parts) >= 2:
                provider_name = parts[1].lower()
                try:
                    self.router.set_provider(provider_name)
                    return f"✅ Provayder tanlandi: **{provider_name}**\nAutomatik rejimga qaytish uchun /auto ishlating."
                except ValueError as exc:
                    return f"❌ {exc}"
            else:
                return self.router.list_providers_status()

        # /model yoki /models — model holati yoki tanlash
        if cmd in (_MODEL_CMD, _MODELS_CMD):
            if len(parts) >= 2:
                model_name = " ".join(parts[1:])
                self.router.set_model(model_name)
                return f"✅ Model tanlandi: **{model_name}**\nAutomatik rejimga qaytish uchun /auto ishlating."
            else:
                return self.router.list_all_models()

        # /auto — avtomatik rejimga qaytish
        if cmd == _AUTO_CMD:
            self.router.reset_auto()
            return "✅ Avtomatik rejimga qaytildi. Provider va model avtomatik tanlanadi."

        # /status — hozirgi holat
        if cmd == _STATUS_CMD:
            status = self.get_status()
            forced_provider = self.router.get_current_provider()
            forced_model = self.router.get_current_model()
            provider_str = forced_provider if forced_provider else "avtomatik (fallback)"
            model_str = forced_model if forced_model else "avtomatik (rejimga qarab)"
            available = ", ".join(status["providers"]) if status["providers"] else "yo'q"
            ai_icon = "✅" if status["ai_available"] else "❌"
            lines = [
                "**Hozirgi holat:**",
                f"  • Rejim: **{status['mode'].upper()}**",
                f"  • Provayder: **{provider_str}**",
                f"  • Model: **{model_str}**",
                f"  • Mavjud provayderlar: {available}",
                f"  • AI tayyor: {ai_icon}",
                f"  • Xotira: {status['memory']['storage_backend']}",
            ]
            study_stats = self.education.get_study_stats()
            if study_stats["total_sessions"] > 0:
                lines.append(
                    f"  • O'qish: {study_stats['total_hours']} soat "
                    f"({study_stats['total_sessions']} sessiya)"
                )
            focus_stats = self.time_engine.get_focus_stats()
            if focus_stats["active"]:
                lines.append(
                    f"  • Focus: 🔥 {focus_stats['remaining_minutes']} daqiqa qoldi"
                )
            else:
                lines.append(
                    f"  • Focus: 😴 Nofaol "
                    f"({focus_stats['sessions_completed']} sessiya bajarilgan)"
                )
            cog_level = status.get("cognitive_load", "unknown")
            lines.append(f"  • Kognitiv yuk: {cog_level.upper()}")
            return "\n".join(lines)

        # /focus [minutes] | /focus stop — Focus/Pomodoro boshlash yoki to'xtatish
        if cmd == "/focus":
            if len(parts) > 1 and parts[1].lower() == "stop":
                result = self.time_engine.stop_focus()
                # Also stop education focus tracker for backward compat
                self.education.end_focus()
                return result
            try:
                minutes = int(parts[1]) if len(parts) > 1 else 25
            except (ValueError, IndexError):
                minutes = 25
            self.mode_manager.set_mode("focus")
            self.time_engine.start_focus(minutes)
            return self.education.start_focus(minutes)

        # /focus_end — Focus ni tugatish (backward compat)
        if cmd == "/focus_end":
            self.time_engine.stop_focus()
            return self.education.end_focus()

        # /cognitive — kognitiv yuk tahlili
        if cmd == "/cognitive":
            hw = self._get_homework_manager()
            return self.cognitive.format_report(hw)

        # /reflect — haftalik aks ettirish
        if cmd == "/reflect":
            hw = self._get_homework_manager()
            return self.narrative.get_weekly_reflection(hw)

        # /study_start <subject> — O'qish sessiyasini boshlash
        if cmd == "/study_start":
            subject = " ".join(parts[1:]) if len(parts) > 1 else "Umumiy"
            return self.education.start_study_session(subject)

        # /study_end — O'qish sessiyasini tugatish
        if cmd == "/study_end":
            return self.education.end_study_session()

        # /study_stats — O'qish statistikasi
        if cmd == "/study_stats":
            stats = self.education.get_study_stats()
            lines = [
                "📊 O'qish Statistikasi",
                f"📚 Jami sessiyalar: {stats['total_sessions']}",
                f"⏱ Jami vaqt: {stats['total_hours']} soat ({stats['total_minutes']} daqiqa)",
                "",
                "📖 Fanlar bo'yicha:",
            ]
            for subj, mins in stats["by_subject"].items():
                lines.append(f"  • {subj}: {mins} daqiqa")
            if not stats["by_subject"]:
                lines.append("  Hali sessiya yo'q")
            return "\n".join(lines)

        # /hw_help <subject> <description> — Uy vazifasi bo'yicha AI yordam
        if cmd == "/hw_help":
            if len(parts) < 3:
                return "Foydalanish: /hw_help <fan> <tavsif>"
            subject = parts[1]
            description = " ".join(parts[2:])
            prompt = self.education.homework_help_prompt(subject, description)
            messages = [
                {"role": "system", "content": self.mode_manager.get_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            try:
                return self.router.route_request(messages=messages, mode="pro")
            except Exception as exc:
                return f"❌ Xato: {exc}"

        # /modes — barcha rejimlar ro'yxati
        if cmd == "/modes":
            modes = self.mode_manager.list_modes()
            current = self.mode_manager.get_current_mode_name()
            lines = ["🧭 Mavjud rejimlar:", ""]
            for m in modes:
                info = self.mode_manager.get_mode(m)
                marker = " ✅" if m == current else ""
                lines.append(f"  /{m} — {info['name']}{marker}")
            lines.append("")
            lines.append("O'zgartirish: /mode <nom> yoki /<nom>")
            return "\n".join(lines)

        # /mode <name> — rejim almashtirish
        if cmd == "/mode":
            if len(parts) < 2:
                return self.process("/modes")
            mode_name = parts[1].lower()
            if self.mode_manager.set_mode(mode_name):
                info = self.mode_manager.get_mode()
                return f"✅ Rejim o'zgartirildi: **{info['name']}**"
            return f"❌ Noma'lum rejim: {mode_name}. /modes ni ko'ring."

        # /overload — ish yuki tekshirish
        if cmd == "/overload":
            hw = self._get_homework_manager()
            if hw is not None:
                res = self.education.check_overload(hw)
                return str(res) if res else "✅ Hozircha ish yuki normal. Davom eting!"
            return "✅ Ish yuki tekshirildi — normal."

        # /today — bugungi to'liq plan
        if cmd == "/today":
            lines = [
                f"📅 Bugungi Reja — {datetime.now().strftime('%Y-%m-%d %A')}",
                "",
            ]
            try:
                from life import SmartScheduler

                sched = SmartScheduler()
                classes = sched.get_schedule()
                if classes:
                    lines.append(f"🏫 Darslar ({len(classes)} ta):")
                    for c in classes:
                        lines.append(
                            f"  {c.start_time}-{c.end_time}: {c.name} ({c.location or '-'})"
                        )
                else:
                    lines.append("🏫 Bugun dars yo'q")
            except Exception:
                lines.append("🏫 Jadval mavjud emas")
            lines.append("")
            hw = self._get_homework_manager()
            if hw is not None:
                pending = hw.get_pending_homework()
                if pending:
                    lines.append(f"📝 Uy vazifalari ({len(pending)} ta):")
                    for h in pending[:5]:
                        lines.append(f"  • {h.subject}: {h.description}")
                else:
                    lines.append("📝 Uy vazifalari yo'q ✅")
                # Kognitiv yuk
                cog = self.cognitive.get_analysis(hw)
                lines.append("")
                level_icons = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}
                icon = level_icons.get(cog["level"], "⚪")
                lines.append(f"{icon} Kognitiv yuk: {cog['level'].upper()}")
                lines.append(f"💡 {cog['suggestion']}")
            else:
                lines.append("📝 Vazifalar mavjud emas")
            stats = self.education.get_study_stats()
            if stats["total_sessions"] > 0:
                lines.append("")
                lines.append(f"📊 Bugungi o'qish: {stats['total_minutes']} daqiqa")
            return "\n".join(lines)

        # Tilni aniqlash
        detected_lang = self.language.detect(user_input)

        # Xotiraga qo'shish
        self.memory.add_to_short_term("user", user_input)

        # RAG qidiruvini amalga oshirish
        rag_context = ""
        try:
            rag_results = self.rag.query(user_input, k=3)
            if rag_results:
                rag_context = "\n\nMavjud hujjatlardan kontekst:\n" + "\n---\n".join(
                    f"[{r['source']}]: {r['content']}" for r in rag_results
                )
        except Exception:
            pass

        # Uzoq muddatli xotiradan qidirish
        memory_context = ""
        try:
            memory_results = self.memory.search_long_term(user_input, k=3)
            if memory_results:
                memory_context = "\n\nOldingi suhbatlardan:\n" + "\n".join(
                    r["content"] for r in memory_results
                )
        except Exception:
            pass

        # Tizim promptini yaratish
        system_prompt = f"{_load_system_prompt()}\n\n{self.mode_manager.get_system_prompt()}"
        personality_instruction = self.personality.get_instruction()
        if personality_instruction:
            system_prompt = f"{system_prompt}\n\n{personality_instruction}"
        lang_instruction = self.language.get_language_instruction()
        if lang_instruction:
            system_prompt = f"{system_prompt}\n\n{lang_instruction}"
        if rag_context:
            system_prompt += rag_context
        if memory_context:
            system_prompt += memory_context

        # Xabarlar ro'yxatini tayyorlash
        context_messages: list[dict] = [{"role": "system", "content": system_prompt}]
        context_messages.extend(self.memory.get_conversation_history())

        # AI ga so'rov yuborish
        mode = self.mode_manager.get_current_mode_name()
        try:
            response = self.router.route_request(
                messages=context_messages,
                mode=mode,
            )
        except Exception as exc:
            response = f"❌ AI provayderi bilan bog'lanishda xato: {exc}"

        # Javobni xotiraga saqlash
        self.memory.add_to_short_term("assistant", response)

        # Uzoq muddatli xotiraga saqlash (muhim suhbatlar)
        try:
            combined = f"Savol: {user_input}\nJavob: {response}"
            self.memory.add_to_long_term(combined, {"mode": mode, "lang": detected_lang})
        except Exception:
            pass

        return response

    def process_intent(self, intent: str, params: dict) -> str:
        """Intent parser natijasini qayta ishlash.

        Intent nomini mavjud slash buyruqqa moslab ``process()`` ga yuboradi.
        Noma'lum intent yoki ``"chat"`` bo'lsa original matn qaytariladi.

        Args:
            intent: IntentParser tomonidan aniqlangan intent nomi.
            params: IntentParser tomonidan ajratilgan parametrlar.

        Returns:
            JARVIS javobi.
        """
        _intent_to_command: dict[str, str] = {
            "show_status": "/status",
            "show_schedule": "/schedule",
            "show_week": "/week",
            "show_homework": "/homework",
            "show_tasks": "/tasks",
            "show_plan": "/plan",
            "show_today": "/today",
            "show_stats": "/stats",
            "show_reminders": "/reminders",
            "start_focus": "/focus",
            "stop_focus": "/focus stop",
            "show_help": "/help",
            "show_cognitive": "/cognitive",
            "show_reflect": "/reflect",
            "show_modes": "/modes",
            "change_mode": "/mode",
        }
        cmd = _intent_to_command.get(intent)
        if cmd:
            # Parametrlarni buyruqqa qo'shish
            if intent == "change_mode" and params.get("mode"):
                cmd = f"/mode {params['mode']}"
            elif intent == "start_focus" and params.get("minutes"):
                cmd = f"/focus {params['minutes']}"
            elif intent == "show_schedule" and params.get("day"):
                cmd = f"/schedule {params['day']}"
            return self.process(cmd)
        # Chat yoki noma'lum intent — original matni qaytarish
        return self.process(params.get("original", ""))

    def get_status(self) -> dict:
        """Joriy holat ma'lumotlari."""
        cog_level = "unknown"
        hw = self._get_homework_manager()
        if hw is not None:
            cog_level = self.cognitive.get_analysis(hw)["level"]
        return {
            "mode": self.mode_manager.get_current_mode_name(),
            "language": self.language.get_response_language(),
            "ai_available": self.router.is_available(),
            "providers": self.router.get_available_providers(),
            "memory": self.memory.get_stats(),
            "rag": self.rag.get_stats(),
            "tools": self.tools.get_tool_names(),
            "cognitive_load": cog_level,
            "focus_state": self.time_engine.get_focus_stats(),
        }
