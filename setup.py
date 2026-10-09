"""
JARVIS-X — Universal Cross-Platform Auto-Setup Script.

Foydalanish:
    python setup.py        # To'liq sozlash
    python setup.py --help # Yordam

Talablar: Python 3.10+
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Minimal Python versiyasi
_MIN_PYTHON = (3, 10)

# Ranglar (colorama mavjud bo'lmasa oddiy matn)
try:
    from colorama import Fore, Style
    from colorama import init as colorama_init

    colorama_init(autoreset=True)
    _GREEN = Fore.GREEN
    _YELLOW = Fore.YELLOW
    _RED = Fore.RED
    _CYAN = Fore.CYAN
    _BOLD = Style.BRIGHT
    _RESET = Style.RESET_ALL
except ImportError:
    _GREEN = _YELLOW = _RED = _CYAN = _BOLD = _RESET = ""

ROOT = Path(__file__).parent.resolve()
VENV_DIR = ROOT / "runtime" / "venv"
REQ_FILE = ROOT / "requirements.txt"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

DATA_DIRS = [
    ROOT / "data",
    ROOT / "data" / "memory",
    ROOT / "data" / "documents",
    ROOT / "data" / "schedule",
]


def _print(msg: str, color: str = "", bold: bool = False) -> None:
    prefix = (_BOLD if bold else "") + color
    print(f"{prefix}{msg}{_RESET}")


def _ok(msg: str) -> None:
    print(f"{_GREEN}  ✅ {msg}{_RESET}")


def _warn(msg: str) -> None:
    print(f"{_YELLOW}  ⚠️  {msg}{_RESET}")


def _err(msg: str) -> None:
    print(f"{_RED}  ❌ {msg}{_RESET}")


def _info(msg: str) -> None:
    print(f"{_CYAN}  ℹ️  {msg}{_RESET}")


def _sep() -> None:
    print(f"{_CYAN}{'─' * 55}{_RESET}")


# ---------------------------------------------------------------------------
# 1. Python versiyasini tekshirish
# ---------------------------------------------------------------------------

def check_python_version() -> bool:
    _print("\n[1/6] Python versiyasini tekshirish...", _CYAN, bold=True)
    ver = sys.version_info
    if ver >= _MIN_PYTHON:
        _ok(f"Python {ver.major}.{ver.minor}.{ver.micro} — mos keladi.")
        return True
    _err(
        f"Python {ver.major}.{ver.minor} topildi, lekin {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}+ talab qilinadi."
    )
    _info("Python-ni yangilang: https://www.python.org/downloads/")
    return False


# ---------------------------------------------------------------------------
# 2. Virtual environment yaratish
# ---------------------------------------------------------------------------

def _venv_python() -> Path:
    """venv ichidagi Python yo'li."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def create_venv() -> bool:
    _print("\n[2/6] Virtual environment tekshirish / yaratish...", _CYAN, bold=True)
    if VENV_DIR.exists() and _venv_python().exists():
        _ok(f"venv mavjud: {VENV_DIR}")
        return True
    _info(f"venv yaratilmoqda: {VENV_DIR}")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
        _ok("venv muvaffaqiyatli yaratildi.")
        return True
    except subprocess.CalledProcessError as exc:
        _err(f"venv yaratishda xato: {exc}")
        return False


# ---------------------------------------------------------------------------
# 3. Dependencies o'rnatish
# ---------------------------------------------------------------------------

def install_dependencies() -> bool:
    _print("\n[3/6] Bog'liqliklarni o'rnatish...", _CYAN, bold=True)
    if not REQ_FILE.exists():
        _err(f"requirements.txt topilmadi: {REQ_FILE}")
        return False

    python_exec = _venv_python()
    if not python_exec.exists():
        _err("venv Python topilmadi. Avval virtual environment yarating.")
        return False

    _info("pip install -r requirements.txt ishga tushirilmoqda...")
    try:
        subprocess.run(
            [str(python_exec), "-m", "pip", "install", "--upgrade", "pip", "-q"],
            check=True,
        )
        subprocess.run(
            [str(python_exec), "-m", "pip", "install", "-r", str(REQ_FILE)],
            check=True,
        )
        _ok("Barcha bog'liqliklar o'rnatildi.")
        return True
    except subprocess.CalledProcessError as exc:
        _err(f"Bog'liqliklarni o'rnatishda xato: {exc}")
        return False


# ---------------------------------------------------------------------------
# 4. Ma'lumotlar papkalarini yaratish
# ---------------------------------------------------------------------------

def create_data_dirs() -> None:
    _print("\n[4/6] Ma'lumotlar papkalarini yaratish...", _CYAN, bold=True)
    for d in DATA_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            _ok(f"Yaratildi: {d.relative_to(ROOT)}")
        else:
            _info(f"Mavjud: {d.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# 5. .env faylini sozlash
# ---------------------------------------------------------------------------

def setup_env() -> None:
    _print("\n[5/6] .env faylini sozlash...", _CYAN, bold=True)
    if ENV_FILE.exists():
        _ok(".env fayli allaqachon mavjud.")
        return

    if not ENV_EXAMPLE.exists():
        _warn(".env.example topilmadi, .env yaratilmadi.")
        return

    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    _ok(".env fayli .env.example dan nusxalandi.")
    _warn("Muhim: .env faylini oching va API kalitlarini kiriting!")
    _info(f"  Fayl: {ENV_FILE}")

    # Foydalanuvchiga asosiy API kalitlarini kiritishni taklif qilish
    try:
        choice = input(f"\n  {_YELLOW}API kalitlarini hozir kiritishni xohlaysizmi? [y/N]: {_RESET}").strip().lower()
        if choice in ("y", "yes", "ha"):
            _collect_api_keys()
    except (KeyboardInterrupt, EOFError):
        print()
        _info("API kalitlarini keyinroq .env faylida sozlang.")


def _collect_api_keys() -> None:
    """Foydalanuvchidan API kalitlarini so'rash va .env ga yozish."""
    providers = [
        ("GEMINI_API_KEY_1", "Gemini API Key (Google AI Studio)"),
        ("DEEPSEEK_API_KEY", "DeepSeek API Key"),
        ("OPENROUTER_API_KEY", "OpenRouter API Key"),
        ("GROQ_API_KEY", "Groq API Key"),
        ("HUGGINGFACE_API_KEY", "HuggingFace API Key"),
    ]
    updates: dict[str, str] = {}
    print()
    for env_var, label in providers:
        try:
            val = input(f"  {label} (bo'sh qoldirish mumkin): ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if val:
            updates[env_var] = val

    if not updates:
        return

    # .env faylini yangilash
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    new_lines: list[str] = []
    written_keys: set[str] = set()
    for line in lines:
        updated = False
        for key, value in updates.items():
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                written_keys.add(key)
                updated = True
                break
        if not updated:
            new_lines.append(line)

    # Faylda topilmagan kalitlarni oxiriga qo'shish
    for key, value in updates.items():
        if key not in written_keys:
            new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    _ok(f"{len(updates)} ta API kaliti .env ga saqlandi.")


# ---------------------------------------------------------------------------
# 6. Launcher skriptlarga ruxsat berish va OS ko'rsatmalari
# ---------------------------------------------------------------------------

def setup_launchers() -> None:
    _print("\n[6/6] Launcher skriptlarni sozlash...", _CYAN, bold=True)
    current_os = platform.system()

    if current_os in ("Linux", "Darwin"):
        jarvis_sh = ROOT / "jarvis"
        if jarvis_sh.exists():
            jarvis_sh.chmod(jarvis_sh.stat().st_mode | 0o111)
            _ok("Execute ruxsat berildi: jarvis")
        else:
            _warn("jarvis skripti topilmadi.")
    elif current_os == "Windows":
        jarvis_bat = ROOT / "jarvis.bat"
        if jarvis_bat.exists():
            _ok("jarvis.bat tayyor (Windows).")
        else:
            _warn("jarvis.bat topilmadi.")


# ---------------------------------------------------------------------------
# ChromaDB tizim kutubxonalarini tekshirish
# ---------------------------------------------------------------------------

def check_chromadb_system_deps() -> None:
    _print("\n  ChromaDB tizim talablari...", _CYAN)
    current_os = platform.system()
    if current_os == "Linux":
        missing = []
        for lib in ("libsqlite3", "libstdc++"):
            result = subprocess.run(
                ["ldconfig", "-p"],
                capture_output=True,
                text=True,
            )
            if lib not in result.stdout:
                missing.append(lib)
        if missing:
            _warn(
                f"ChromaDB uchun tizim kutubxonalari kerak bo'lishi mumkin: {', '.join(missing)}"
            )
            _info("  sudo apt-get install -y libsqlite3-dev build-essential")
        else:
            _ok("ChromaDB tizim kutubxonalari topildi.")
    else:
        _ok(f"ChromaDB tizim talablari ({current_os}): odatda muammo yo'q.")


# ---------------------------------------------------------------------------
# Yakuniy ko'rsatma
# ---------------------------------------------------------------------------

def print_final_guide() -> None:
    current_os = platform.system()
    _sep()
    _print("\n🎉 JARVIS-X sozlash muvaffaqiyatli yakunlandi!\n", _GREEN, bold=True)
    _print("Keyingi qadamlar:", _CYAN, bold=True)
    print(f"  1. {_YELLOW}.env{_RESET} faylida API kalitlarini sozlang")
    print(f"     {_CYAN}{ENV_FILE}{_RESET}\n")
    print("  2. JARVIS-X ni ishga tushiring:")
    if current_os == "Windows":
        print(f"     {_GREEN}jarvis.bat{_RESET}       — Windows launcher")
    else:
        print(f"     {_GREEN}./jarvis{_RESET}          — Linux/macOS launcher")
    print(f"     {_GREEN}python start.py{_RESET}  — To'g'ridan-to'g'ri ishga tushirish")
    print(f"     {_GREEN}python start.py --life-only{_RESET}  — Faqat Life Assistant\n")
    print("  3. Diagnostika:")
    print(f"     {_GREEN}python health_check.py{_RESET}  — Tizim salomatligini tekshirish\n")
    _sep()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JARVIS-X — Universal Auto-Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Misol: python setup.py",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Bog'liqliklarni o'rnatishni o'tkazib yuborish",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    _sep()
    _print(" JARVIS-X — Auto Setup", _CYAN, bold=True)
    _print(f" OS: {platform.system()} {platform.release()}", _CYAN)
    _print(f" Python: {sys.version.split()[0]}", _CYAN)
    _sep()

    # 1. Python versiyasi
    if not check_python_version():
        sys.exit(1)

    # 2. Virtual environment
    if not create_venv():
        sys.exit(1)

    # 3. Dependencies
    if not args.skip_deps:
        if not install_dependencies():
            _warn("Bog'liqliklarni o'rnatishda xato yuz berdi. Keyinroq qayta urinib ko'ring.")

    # ChromaDB tizim kutubxonalari
    check_chromadb_system_deps()

    # 4. Data papkalar
    create_data_dirs()

    # 5. .env sozlash
    setup_env()

    # 6. Launcher skriptlar
    setup_launchers()

    # Yakuniy ko'rsatma
    print_final_guide()


if __name__ == "__main__":
    main()
