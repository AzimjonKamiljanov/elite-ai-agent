"""
JARVIS Terminal UI Renderer — Professional, clean, persistent UI.
"""
from __future__ import annotations

import os
import platform
from datetime import datetime, timedelta, timezone

TASHKENT_TZ = timezone(timedelta(hours=5))


class UIRenderer:
    """Terminal UI rendering engine."""

    def __init__(self) -> None:
        self._last_query: str = ""
        self._last_response: str = ""
        self._width: int = 60

    def clear_screen(self) -> None:
        """Terminal ekranini tozalash."""
        os.system("cls" if platform.system() == "Windows" else "clear")

    def get_tashkent_time(self) -> str:
        """Toshkent vaqtini olish."""
        now = datetime.now(TASHKENT_TZ)
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def render_header(self, mode: str = "PRO", ai_status: bool = True) -> str:
        """Persistent header matni yaratish.

        Args:
            mode: Joriy rejim nomi.
            ai_status: AI tayyor holati.

        Returns:
            Formatlangan header matni (Rich markup bilan).
        """
        ai_icon = "🟢 Tayyor" if ai_status else "🔴 Tayyor emas"
        sep = "═" * self._width
        lines = [
            f"[bold cyan]{sep}[/bold cyan]",
            f"[bold cyan]{'JARVIS • AI AGENT':^{self._width}}[/bold cyan]",
            f"[bold cyan]{sep}[/bold cyan]",
            f"  [dim]📍 Toshkent: {self.get_tashkent_time()}[/dim]",
            f"  [dim]🧭 Rejim: {mode.upper()} | {ai_icon}[/dim]",
            f"[bold cyan]{sep}[/bold cyan]",
        ]
        return "\n".join(lines)

    def render_startup(
        self, mode: str, ai_status: bool, providers: list[str]
    ) -> str:
        """Startup ekrani matnini yaratish.

        Args:
            mode: Joriy rejim nomi.
            ai_status: AI tayyor holati.
            providers: Mavjud provayder nomlari ro'yxati.

        Returns:
            Formatlangan startup ekrani matni (Rich markup bilan).
        """
        header = self.render_header(mode, ai_status)
        providers_str = ", ".join(providers) if providers else "yo'q"
        examples = "\n".join(
            [
                "  [dim]💬 \"Bugungi vazifalarim\"[/dim]",
                "  [dim]💬 \"Statusni ko'rsat\"[/dim]",
                "  [dim]💬 \"Dushanba 12:00 uchrashuv qo'sh\"[/dim]",
                "  [dim]💬 \"Bugun nimaga e'tibor berishim kerak?\"[/dim]",
                "  [dim]💬 \"50 ming ovqatga ketdi\"[/dim]",
                "  [dim]💬 \"Energiyam 4\"[/dim]",
            ]
        )
        lines = [
            header,
            "",
            f"  [bold]Provayderlar:[/bold] {providers_str}",
            "",
            "[bold cyan]Misol so'rovlar:[/bold cyan]",
            examples,
            "",
            "[dim]Tabiiy tilda yozing yoki /help buyrug'ini ishlating.[/dim]",
        ]
        return "\n".join(lines)

    def render_response(self, query: str, response: str) -> str:
        """Oxirgi savol-javobni formatlash.

        Args:
            query: Foydalanuvchi so'rovi.
            response: JARVIS javobi.

        Returns:
            Formatlangan savol-javob matni (Rich markup bilan).
        """
        if not query and not response:
            return ""
        lines = []
        if query:
            lines.append(f"\n[bold cyan]🧑 Siz:[/bold cyan] {query}\n")
        if response:
            lines.append("[bold green]🤖 JARVIS:[/bold green]")
            lines.append(response)
        return "\n".join(lines)

    def render_full_screen(
        self,
        mode: str,
        ai_status: bool,
        query: str = "",
        response: str = "",
    ) -> None:
        """To'liq ekranni qayta chizish.

        Args:
            mode: Joriy rejim nomi.
            ai_status: AI tayyor holati.
            query: Oxirgi foydalanuvchi so'rovi (ixtiyoriy).
            response: Oxirgi JARVIS javobi (ixtiyoriy).
        """
        try:
            from rich.console import Console

            console = Console()
            self.clear_screen()
            console.print(self.render_header(mode, ai_status))
            if query or response:
                console.print(self.render_response(query, response))
        except ImportError:
            self.clear_screen()
            print(f"JARVIS • {mode.upper()}")
            if query:
                print(f"🧑 Siz: {query}")
            if response:
                print(f"🤖 JARVIS: {response}")

    def full_redraw(
        self,
        mode: str = "JARVIS",
        ai_status: bool = True,
        query: str = "",
        response: str = "",
    ) -> None:
        """To'liq ekran qayta chizish (render_full_screen uchun qulay nom).

        Args:
            mode: Joriy rejim nomi.
            ai_status: AI tayyor holati.
            query: Oxirgi foydalanuvchi so'rovi (ixtiyoriy).
            response: Oxirgi JARVIS javobi (ixtiyoriy).
        """
        self.render_full_screen(mode, ai_status, query, response)

    def startup(
        self,
        mode: str = "JARVIS",
        ai_status: bool = True,
        providers: list[str] | None = None,
    ) -> None:
        """Startup ekranini ko'rsatish.

        Args:
            mode: Joriy rejim nomi.
            ai_status: AI tayyor holati.
            providers: Mavjud provayder nomlari ro'yxati.
        """
        try:
            from rich.console import Console

            console = Console()
            self.clear_screen()
            console.print(self.render_startup(mode, ai_status, providers or []))
        except ImportError:
            self.clear_screen()
            providers_str = ", ".join(providers) if providers else "yo'q"
            print(f"JARVIS • {mode.upper()} | Provayderlar: {providers_str}")
