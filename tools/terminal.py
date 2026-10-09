"""
Terminal buyruqlari vositasi — whitelist asosida xavfsiz buyruqlar.
"""

from __future__ import annotations

import re
import shlex
import subprocess

# Ruxsat etilgan buyruqlar (whitelist)
_ALLOWED_COMMANDS = {
    "ls", "dir", "cat", "echo", "python", "python3", "pip", "pip3",
    "git", "pwd", "whoami", "date", "which", "find", "head", "tail",
    "wc", "grep", "sort", "uniq", "diff", "tree",
}

# Taqiqlangan so'zlar (blacklist)
_BLOCKED_PATTERNS = [
    "rm -rf", "format", "mkfs", "dd if=", "shutdown", "reboot",
    "passwd", "sudo rm", "> /dev", "chmod 777 /", "kill -9 1",
]

# Shell metacharacterlar — injection xujumlarini oldini olish
_SHELL_META_PATTERN = re.compile(r"[;&|`$<>\\]|\$\(|&&|\|\|")

_DEFAULT_TIMEOUT = 15  # sekund
_MAX_OUTPUT = 5_000  # belgi


class TerminalTool:
    """Terminal buyruqlarini xavfsiz bajarish."""

    def execute(self, command: str, timeout: int = _DEFAULT_TIMEOUT) -> str:
        """Shell buyrug'ini bajarish.

        Args:
            command: Bajariladigan buyruq
            timeout: Maksimal vaqt (sekund)

        Returns:
            Buyruq natijasi yoki xato xabari
        """
        if not command.strip():
            return "Bo'sh buyruq."

        # Taqiqlangan naqshlarni tekshirish
        command_lower = command.lower()
        for blocked in _BLOCKED_PATTERNS:
            if blocked in command_lower:
                return "🚫 Xavfsizlik cheklovi: bu buyruqqa ruxsat yo'q."

        # Birinchi so'zni olish va whitelist tekshirish
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()

        if not parts:
            return "Bo'sh buyruq."

        base_cmd = parts[0].lower()
        # Windows da .exe qo'shimchasini olib tashlash (case-insensitive)
        base_cmd = re.sub(r"\.exe$", "", base_cmd, flags=re.IGNORECASE)

        if base_cmd not in _ALLOWED_COMMANDS:
            return (
                f"🚫 Buyruq '{base_cmd}' ruxsat etilmagan. "
                f"Ruxsat etilganlar: {', '.join(sorted(_ALLOWED_COMMANDS))}"
            )

        # Shell metacharacterlarni tekshirish (injection oldini olish)
        if _SHELL_META_PATTERN.search(command):
            return "🚫 Xavfsizlik cheklovi: maxsus belgilar ruxsat etilmagan."

        try:
            result = subprocess.run(
                parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout[:_MAX_OUTPUT])
            if result.stderr:
                output_parts.append(f"[stderr]: {result.stderr[:_MAX_OUTPUT]}")
            if result.returncode != 0:
                output_parts.append(f"[return code: {result.returncode}]")

            return "\n".join(output_parts) if output_parts else "✅ Buyruq bajarildi (natija yo'q)."

        except subprocess.TimeoutExpired:
            return f"⏱ Timeout: buyruq {timeout} sekund ichida bajarilmadi."
        except Exception as exc:
            return f"❌ Buyruq xatosi: {exc}"
