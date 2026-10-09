"""
Fayl boshqaruvi vositasi — xavfsiz fayl operatsiyalari.
"""

from __future__ import annotations

from pathlib import Path

# Himoyalangan yo'llar — o'zgartirishga ruxsat yo'q
_BLOCKED_PATHS = [
    "/etc",
    "/sys",
    "/boot",
    "/usr/bin",
    "/usr/sbin",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
]
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _is_safe_path(path_str: str) -> bool:
    """Yo'lning xavfsizligini tekshirish."""
    path = Path(path_str).resolve()
    path_str_resolved = str(path)
    return not any(path_str_resolved.startswith(bp) for bp in _BLOCKED_PATHS)


class FileManagerTool:
    """Xavfsiz fayl operatsiyalari."""

    def read_file(self, path: str) -> str:
        """Faylni o'qish.

        Args:
            path: Fayl yo'li

        Returns:
            Fayl mazmuni yoki xato xabari
        """
        if not _is_safe_path(path):
            return f"Xavfsizlik cheklovi: bu yo'lga ruxsat yo'q: {path}"

        file_path = Path(path)
        if not file_path.exists():
            return f"Fayl topilmadi: {path}"
        if not file_path.is_file():
            return f"Bu fayl emas: {path}"
        if file_path.stat().st_size > _MAX_FILE_SIZE:
            return f"Fayl hajmi juda katta (>{_MAX_FILE_SIZE // (1024*1024)} MB): {path}"

        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return f"Fayl o'qish xatosi: {exc}"

    def write_file(self, path: str, content: str) -> str:
        """Faylga yozish.

        Args:
            path: Fayl yo'li
            content: Yoziladigan mazmun

        Returns:
            Muvaffaqiyat yoki xato xabari
        """
        if not _is_safe_path(path):
            return f"Xavfsizlik cheklovi: bu yo'lga ruxsat yo'q: {path}"

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"✅ Muvaffaqiyatli yozildi: {path}"
        except OSError as exc:
            return f"Fayl yozish xatosi: {exc}"

    def list_directory(self, path: str = ".") -> str:
        """Katalog tarkibini ko'rsatish.

        Args:
            path: Katalog yo'li

        Returns:
            Katalog tarkibi yoki xato xabari
        """
        if not _is_safe_path(path):
            return f"Xavfsizlik cheklovi: bu yo'lga ruxsat yo'q: {path}"

        dir_path = Path(path)
        if not dir_path.exists():
            return f"Katalog topilmadi: {path}"
        if not dir_path.is_dir():
            return f"Bu katalog emas: {path}"

        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            if not items:
                return "Katalog bo'sh."
            lines = []
            for item in items:
                icon = "📂" if item.is_dir() else "📄"
                size_info = ""
                if item.is_file():
                    size = item.stat().st_size
                    if size < 1024:
                        size_info = f" ({size} B)"
                    elif size < 1024 * 1024:
                        size_info = f" ({size // 1024} KB)"
                    else:
                        size_info = f" ({size // (1024 * 1024)} MB)"
                lines.append(f"{icon} {item.name}{size_info}")
            return "\n".join(lines)
        except OSError as exc:
            return f"Katalog ko'rish xatosi: {exc}"