"""
JARVIS Life Assistant — Kundalik hayot boshqaruvchisi.
Real vaqtda dars monitoring, homework tracking, kundalik rejalashtirish.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Rich kutubxonasi topilmadi. O'rnating: pip install rich")
    sys.exit(1)

from core.intelligence import (
    CognitiveLoadBalancer,
    LifeNarrativeEngine,
    TimePerceptionEngine,
)
from life import DailyPlanner, HomeworkManager, ReminderEngine, SmartScheduler

console = Console()

# Toshkent vaqt zonasi (UTC+5)
_TASHKENT_TZ = timezone(timedelta(hours=5))

_BANNER = r"""
     _   _   ____    _____  __     __ ___   ____         _      _   _____  _____
    | | / \ |  _ \  |_   _| \ \   / /|_ _| / ___|       | |    | | |  ___|| ____|
 _  | |/ _ \| |_) |   | |    \ \ / /  | |  \___ \       | |    | | | |_   |  _|
| |_| / ___ \  _ <    | |     \ V /   | |   ___) |      | |___ | | |  _|  | |___
 \___/_/   \_\_| \_\  |_|      \_/   |___| |____/       |_____||_| |_|    |_____|

                    Smart Life Assistant — Hayot yordamchisi
"""


def _clear_screen() -> None:
    """Terminalni tozalash (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def _tashkent_now() -> str:
    """Hozirgi Toshkent vaqtini ``YYYY-MM-DD HH:MM:SS`` formatida qaytarish."""
    return datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _render_header() -> None:
    """Persistent header-ni render qilish."""
    sep = "═" * 42
    console.print(f"[bold cyan]{sep}[/bold cyan]")
    console.print(f"[bold cyan]{'JARVIS • LIFE ASSISTANT':^42}[/bold cyan]")
    console.print(f"[bold cyan]{sep}[/bold cyan]")
    console.print(f"  [dim]📍 Toshkent: {_tashkent_now()}[/dim]")
    console.print(f"[bold cyan]{sep}[/bold cyan]")


def _log_interaction(user_input: str, response: str) -> None:
    """Suhbatni data/chat_history.log faylga saqlash."""
    log_file = Path(__file__).parent / "data" / "chat_history.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(_TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [MODE: life]\n")
        f.write(f"🧑 Siz: {user_input}\n")
        f.write(f"🤖 JARVIS: {response}\n")
        f.write("-" * 40 + "\n")


def print_banner() -> None:
    """JARVIS Life Assistant banner."""
    console.print(f"[bold cyan]{_BANNER}[/bold cyan]")
    console.print(
        "[dim]Kundalik dars jadvali, uy vazifalari va rejalashtirish tizimi[/dim]\n"
    )


def show_schedule(scheduler: SmartScheduler, day: str | None = None) -> None:
    """Jadvalini chiroyli jadval ko'rinishida ko'rsatish."""
    classes = scheduler.get_schedule(day)
    title = f"📅 {day.capitalize() if day else 'Bugungi'} Dars Jadvali"
    if not classes:
        console.print(Panel("[yellow]Dars topilmadi.[/yellow]", title=title))
        return
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Boshlanish", style="cyan", no_wrap=True)
    table.add_column("Tugash", style="cyan", no_wrap=True)
    table.add_column("Fan", style="bold")
    table.add_column("Xona")
    table.add_column("O'qituvchi")
    table.add_column("ID", style="dim", no_wrap=True)
    for c in classes:
        table.add_row(c.start_time, c.end_time, c.name, c.location, c.teacher, c.id[:8])
    console.print(table)


def show_weekly_schedule(scheduler: SmartScheduler) -> None:
    """Haftalik jadval."""
    weekly = scheduler.get_weekly_schedule()
    table = Table(title="📆 Haftalik Dars Jadvali", show_header=True, header_style="bold magenta")
    table.add_column("Kun", style="bold")
    table.add_column("Darslar")
    day_names_uz = {
        "monday": "Dushanba",
        "tuesday": "Seshanba",
        "wednesday": "Chorshanba",
        "thursday": "Payshanba",
        "friday": "Juma",
        "saturday": "Shanba",
        "sunday": "Yakshanba",
    }
    for day, classes in weekly.items():
        if classes:
            class_str = "\n".join(
                f"{c.start_time}-{c.end_time}: {c.name}" for c in classes
            )
        else:
            class_str = "[dim]Dars yo'q[/dim]"
        table.add_row(day_names_uz.get(day, day), class_str)
    console.print(table)


def show_homework(homework_mgr: HomeworkManager) -> None:
    """Bajarilmagan uy vazifalari."""
    pending = homework_mgr.get_pending_homework()
    if not pending:
        console.print(Panel("[green]✅ Barcha uy vazifalari bajarilgan![/green]", title="📝 Uy Vazifalari"))
        return
    table = Table(title="📝 Bajarilmagan Uy Vazifalari", show_header=True, header_style="bold yellow")
    table.add_column("Fan", style="bold")
    table.add_column("Vazifa")
    table.add_column("Muddat", style="cyan")
    table.add_column("Ustuvorlik", style="magenta")
    table.add_column("ID", style="dim", no_wrap=True)
    for hw in pending:
        table.add_row(hw.subject, hw.description, hw.deadline or "-", hw.priority.value, hw.id[:8])
    console.print(table)


def show_tasks(homework_mgr: HomeworkManager) -> None:
    """Barcha vazifalar."""
    all_pending = homework_mgr.get_all_pending()
    if not all_pending:
        console.print(Panel("[green]✅ Barcha vazifalar bajarilgan![/green]", title="✅ Vazifalar"))
        return
    table = Table(title="📋 Barcha Bajarilmagan Vazifalar", show_header=True, header_style="bold blue")
    table.add_column("Turi", style="cyan")
    table.add_column("Sarlavha/Fan", style="bold")
    table.add_column("Tavsif")
    table.add_column("Ustuvorlik", style="magenta")
    table.add_column("ID", style="dim", no_wrap=True)
    for entry in all_pending:
        item = entry["item"]
        if entry["type"] == "homework":
            title_col = item.subject
            desc_col = item.description
        else:
            title_col = item.title
            desc_col = item.description
        table.add_row(entry["type"], title_col, desc_col, item.priority.value, item.id[:8])
    console.print(table)


def show_stats(homework_mgr: HomeworkManager) -> None:
    """Statistika."""
    stats = homework_mgr.get_stats()
    lines = [
        f"📚 Jami uy vazifalari: {stats['total_homework']}",
        f"✅ Bajarilgan: {stats['completed_homework']}",
        f"⏳ Qolgan: {stats['pending_homework']}",
        f"⚠️  Muddati o'tgan: {stats['overdue_homework']}",
        "",
        f"📋 Jami vazifalar: {stats['total_tasks']}",
        f"✅ Bajarilgan: {stats['completed_tasks']}",
        "",
        f"📈 Bajarilish darajasi: {stats['completion_rate']}%",
    ]
    console.print(Panel("\n".join(lines), title="📊 Statistika"))


def show_help() -> None:
    """Yordam matnini ko'rsatish."""
    help_text = """
## JARVIS Life Assistant — Buyruqlar

### Jadval
- `/schedule` — bugungi jadval
- `/week` — haftalik jadval
- `/add_class <fan> <kun> <boshlanish> <tugash> [xona]` — dars qo'shish
- `/remove_class <id>` — dars o'chirish

### Uy Vazifalari
- `/homework` — bajarilmagan uy vazifalari
- `/add_hw <fan> <tavsif> [muddat]` — uy vazifasi qo'shish
- `/done_hw <id>` — uy vazifasini bajarilgan qilish

### Vazifalar
- `/tasks` — barcha vazifalar
- `/add_task <sarlavha> [tavsif] [muddat]` — vazifa qo'shish
- `/done_task <id>` — vazifani bajarilgan qilish

### Reja va Eslatmalar
- `/plan` — bugungi reja
- `/reminders` — eslatmalar
- `/stats` — statistika
- `/summary` — kun oxiri xulosasi

### Intellekt Modullari
- `/today` — bugungi to'liq sharh (dars, vazifalar, kognitiv yuk)
- `/focus [daqiqa]` — Pomodoro/focus sessiyani boshlash (default 25 min)
- `/focus stop` — focus sessiyani to'xtatish
- `/cognitive` — kognitiv yuk tahlili
- `/reflect` — haftalik aks ettirish va tahlil

### Boshqa
- `/load_sample` — namuna jadval yuklash
- `/help` — yordam
- `/exit` — chiqish
"""
    console.print(Markdown(help_text))


def load_sample_schedule(scheduler: SmartScheduler) -> None:
    """config/schedule_config.json dan namuna jadval yuklash."""
    try:
        with open("config/schedule_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        sample = config.get("sample_schedule", [])
        for item in sample:
            scheduler.add_class(
                name=item["name"],
                day=item["day"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                location=item.get("location", ""),
                teacher=item.get("teacher", ""),
            )
        console.print(f"[green]✅ {len(sample)} ta namuna dars yuklandi.[/green]")
    except FileNotFoundError:
        console.print("[red]config/schedule_config.json topilmadi.[/red]")
    except Exception as exc:
        console.print(f"[red]Xato: {exc}[/red]")


# Intent → slash buyruq mapping
_INTENT_CMD_MAP: dict[str, str] = {
    "show_help": "/help",
    "show_schedule": "/schedule",
    "show_week": "/week",
    "add_class": "/add_class",
    "show_homework": "/homework",
    "add_homework": "/add_hw",
    "done_homework": "/done_hw",
    "show_tasks": "/tasks",
    "add_task": "/add_task",
    "done_task": "/done_task",
    "show_plan": "/plan",
    "show_today": "/today",
    "show_stats": "/stats",
    "show_reminders": "/reminders",
    "start_focus": "/focus",
    "stop_focus": "/focus stop",
    "show_cognitive": "/cognitive",
    "show_reflect": "/reflect",
    "exit": "/exit",
}


def _intent_to_cmd(intent_info: dict, raw_input: str) -> str:
    """Intent ma'lumotlarini slash buyruqqa aylantirish.

    Agar intent ``chat`` yoki noma'lum bo'lsa raw_input qaytariladi.
    """
    intent = intent_info.get("intent", "chat")
    if intent == "chat" or intent not in _INTENT_CMD_MAP:
        return raw_input

    base_cmd = _INTENT_CMD_MAP[intent]

    # stop_focus maxsus holatini to'g'ri qaytarish
    if intent == "stop_focus":
        return base_cmd

    params = intent_info.get("params", {})

    # Parametrlarni qo'shish
    extras: list[str] = []
    if params.get("mode"):
        extras.append(params["mode"])
    if params.get("minutes"):
        extras.append(str(params["minutes"]))
    if params.get("day") and intent in ("show_schedule",):
        extras.append(params["day"])
    if params.get("title"):
        extras.append(params["title"])

    if extras:
        return f"{base_cmd} {' '.join(extras)}"
    return base_cmd


def main() -> None:
    """Asosiy tsikl."""
    from core.ui_renderer import UIRenderer

    # Intent parser
    try:
        from core.intent_parser import IntentParser
        intent_parser = IntentParser()
    except Exception:
        intent_parser = None  # type: ignore[assignment]

    scheduler = SmartScheduler()
    homework_mgr = HomeworkManager()
    planner = DailyPlanner()
    reminder_engine = ReminderEngine()
    cognitive = CognitiveLoadBalancer()
    time_engine = TimePerceptionEngine()
    narrative = LifeNarrativeEngine()

    ui = UIRenderer()

    # Startup ekrani
    ui.startup()

    # Ertalabki xulosa
    console.print(Panel(planner.get_morning_briefing(), title="🌅 Ertalabki Xulosa"))

    # Eslatmalarni tekshirish
    reminders = reminder_engine.check_all()
    if reminders:
        console.print(
            Panel(reminder_engine.format_notifications(reminders), title="🔔 Eslatmalar")
        )

    console.print("\n[dim]Tabiiy tilda yozing yoki /help buyrug'ini ishlating.[/dim]\n")

    last_output: str | None = None
    last_query: str | None = None

    while True:
        ui.full_redraw(query=last_query or "", response=last_output or "")

        try:
            user_input = console.input("[bold cyan]🧑 Siz:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Xayr! Yaxshi kun tilaymiz! 👋[/yellow]")
            break

        if not user_input:
            continue

        # Intent tahlili (tabiiy til + slash)
        intent_info: dict = {}
        if intent_parser is not None:
            try:
                intent_info = intent_parser.parse(user_input)
            except Exception:
                intent_info = {}

        mapped_cmd = _intent_to_cmd(intent_info, user_input)
        parts = mapped_cmd.split()
        cmd = parts[0].lower() if parts else user_input.split()[0].lower()

        output: str = ""

        if cmd in ("/exit", "/quit"):
            console.print("[yellow]Xayr! Yaxshi kun tilaymiz! 👋[/yellow]")
            break

        elif cmd == "/help":
            show_help()
            output = "Yordam ko'rsatildi."

        elif cmd == "/schedule":
            day_arg = parts[1] if len(parts) > 1 else None
            show_schedule(scheduler, day_arg)
            output = "Jadval ko'rsatildi."

        elif cmd == "/week":
            show_weekly_schedule(scheduler)
            output = "Haftalik jadval ko'rsatildi."

        elif cmd == "/add_class":
            if len(parts) < 5:
                console.print("[red]Foydalanish: /add_class <fan> <kun> <boshlanish> <tugash> [xona][/red]")
                output = "Noto'g'ri format."
            else:
                name, day, start, end_ = parts[1], parts[2], parts[3], parts[4]
                location = parts[5] if len(parts) > 5 else ""
                teacher = parts[6] if len(parts) > 6 else ""
                try:
                    cls = scheduler.add_class(name, day, start, end_, location, teacher)
                    output = f"✅ Dars qo'shildi: {cls.name} ({cls.id[:8]})"
                    console.print(f"[green]{output}[/green]")
                except Exception as e:
                    output = f"Xato: {e}"
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/remove_class":
            if len(parts) < 2:
                console.print("[red]Foydalanish: /remove_class <id>[/red]")
                output = "Noto'g'ri format."
            else:
                found = scheduler.find_class_by_prefix(parts[1])
                if found:
                    result = scheduler.remove_class(found.id)
                    output = "✅ Dars o'chirildi." if result else "Dars topilmadi."
                    color = "green" if result else "red"
                    console.print(f"[{color}]{output}[/{color}]")
                else:
                    output = "Dars topilmadi."
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/homework":
            show_homework(homework_mgr)
            output = "Uy vazifalari ko'rsatildi."

        elif cmd == "/add_hw":
            if len(parts) < 3:
                console.print("[red]Foydalanish: /add_hw <fan> <tavsif> [muddat] [ustuvorlik][/red]")
                output = "Noto'g'ri format."
            else:
                subject = parts[1]
                description = parts[2]
                deadline = parts[3] if len(parts) > 3 else ""
                priority = parts[4] if len(parts) > 4 else "medium"
                try:
                    hw = homework_mgr.add_homework(subject, description, deadline, priority)
                    output = f"✅ Uy vazifasi qo'shildi: {hw.subject} ({hw.id[:8]})"
                    console.print(f"[green]{output}[/green]")
                except Exception as e:
                    output = f"Xato: {e}"
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/done_hw":
            if len(parts) < 2:
                console.print("[red]Foydalanish: /done_hw <id>[/red]")
                output = "Noto'g'ri format."
            else:
                found = homework_mgr.find_homework_by_prefix(parts[1])
                if found:
                    result = homework_mgr.complete_homework(found.id)
                    output = "✅ Bajarilgan deb belgilandi!" if result else "Topilmadi."
                    color = "green" if result else "red"
                    console.print(f"[{color}]{output}[/{color}]")
                else:
                    output = "Vazifa topilmadi."
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/tasks":
            show_tasks(homework_mgr)
            output = "Vazifalar ko'rsatildi."

        elif cmd == "/add_task":
            if len(parts) < 2:
                console.print("[red]Foydalanish: /add_task <sarlavha> [tavsif] [muddat][/red]")
                output = "Noto'g'ri format."
            else:
                title = parts[1]
                description = parts[2] if len(parts) > 2 else ""
                deadline = parts[3] if len(parts) > 3 else ""
                priority = parts[4] if len(parts) > 4 else "medium"
                category = parts[5] if len(parts) > 5 else "general"
                try:
                    task = homework_mgr.add_task(title, description, deadline, priority, category)
                    output = f"✅ Vazifa qo'shildi: {task.title} ({task.id[:8]})"
                    console.print(f"[green]{output}[/green]")
                except Exception as e:
                    output = f"Xato: {e}"
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/done_task":
            if len(parts) < 2:
                console.print("[red]Foydalanish: /done_task <id>[/red]")
                output = "Noto'g'ri format."
            else:
                found = homework_mgr.find_task_by_prefix(parts[1])
                if found:
                    result = homework_mgr.complete_task(found.id)
                    output = "✅ Bajarilgan deb belgilandi!" if result else "Topilmadi."
                    color = "green" if result else "red"
                    console.print(f"[{color}]{output}[/{color}]")
                else:
                    output = "Vazifa topilmadi."
                    console.print(f"[red]{output}[/red]")

        elif cmd == "/plan":
            plan = planner.generate_daily_plan()
            lines = [f"📅 Sana: {plan.date}", f"⏰ Uyg'onish: {plan.wake_up_time}", ""]
            if plan.classes:
                lines.append(f"🏫 Darslar ({len(plan.classes)} ta):")
                for c in plan.classes:
                    lines.append(f"  {c.get('start_time', '')}-{c.get('end_time', '')} — {c.get('name', '')}")
            if plan.study_blocks:
                lines.append(f"\n📖 O'qish vaqtlari ({len(plan.study_blocks)} ta):")
                for sb in plan.study_blocks:
                    lines.append(f"  {sb['start']}-{sb['end']}: {sb.get('suggestion', '')}")
            if plan.tasks:
                lines.append(f"\n📝 Bugungi vazifalar ({len(plan.tasks)} ta):")
                for t in plan.tasks:
                    lines.append(f"  - {t.get('subject', t.get('title', ''))}")
            console.print(Panel("\n".join(lines), title="📋 Bugungi Reja"))
            output = "Reja ko'rsatildi."

        elif cmd == "/reminders":
            reminders = reminder_engine.check_all()
            text = reminder_engine.format_notifications(reminders)
            console.print(Panel(text, title="🔔 Eslatmalar"))
            output = "Eslatmalar ko'rsatildi."

        elif cmd == "/stats":
            show_stats(homework_mgr)
            output = "Statistika ko'rsatildi."

        elif cmd == "/summary":
            summary = planner.get_end_of_day_summary()
            console.print(Panel(summary, title="📊 Kun Oxiri Xulosasi"))
            output = "Xulosa ko'rsatildi."

        elif cmd == "/load_sample":
            load_sample_schedule(scheduler)
            output = "Namuna jadval yuklandi."

        elif cmd == "/today":
            lines = [f"📅 Bugungi Ko'rinish — {datetime.now(_TASHKENT_TZ).strftime('%Y-%m-%d %A')}", ""]
            classes = scheduler.get_schedule()
            if classes:
                lines.append(f"🏫 Darslar ({len(classes)} ta):")
                for c in classes:
                    lines.append(f"  {c.start_time}-{c.end_time}: {c.name}")
            else:
                lines.append("🏫 Bugun dars yo'q")
            lines.append("")
            pending = homework_mgr.get_pending_homework()
            if pending:
                lines.append(f"📝 Bajarilmagan uy vazifalari ({len(pending)} ta):")
                for h in pending[:5]:
                    lines.append(f"  • {h.subject}: {h.description}")
            else:
                lines.append("📝 Uy vazifalari yo'q ✅")
            lines.append("")
            cog = cognitive.get_analysis(homework_mgr)
            level_icons = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}
            icon = level_icons.get(cog["level"], "⚪")
            lines.append(f"{icon} Kognitiv yuk: {cog['level'].upper()}")
            lines.append(f"💡 {cog['suggestion']}")
            console.print(Panel("\n".join(lines), title="🌅 Bugungi To'liq Sharh"))
            output = "Bugungi sharh ko'rsatildi."

        elif cmd == "/focus":
            if len(parts) > 1 and parts[1].lower() == "stop":
                msg = time_engine.stop_focus()
                console.print(Panel(msg, title="⏹ Focus To'xtatildi"))
                output = msg
            else:
                try:
                    minutes = int(parts[1]) if len(parts) > 1 else 25
                except (ValueError, IndexError):
                    minutes = 25
                msg = time_engine.start_focus(minutes)
                console.print(Panel(msg, title="🍅 Focus Boshlandi"))
                output = msg

        elif cmd == "/cognitive":
            report = cognitive.format_report(homework_mgr)
            console.print(Panel(report, title="🧠 Kognitiv Yuk"))
            output = report

        elif cmd == "/reflect":
            reflection = narrative.get_weekly_reflection(homework_mgr)
            console.print(Panel(reflection, title="📖 Haftalik Aks Ettirish"))
            output = reflection

        else:
            msg = f"Noma'lum buyruq: {cmd}. Yordam uchun 'yordam' yoki /help yozing."
            console.print(f"[yellow]{msg}[/yellow]")
            output = msg

        # Terminal beep
        print("\a", end="", flush=True)

        # Chat history log
        _log_interaction(user_input, output)

        last_query = user_input
        last_output = output


if __name__ == "__main__":
    main()
