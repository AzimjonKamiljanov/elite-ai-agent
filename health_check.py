"""
JARVIS-X — Health Check & Diagnostic Script.

Foydalanish:
    python health_check.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

# ---------------------------------------------------------------------------
# Rich mavjudligini tekshirish
# ---------------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    _RICH = True
except ImportError:
    _RICH = False

console: "Console | None" = Console() if _RICH else None


def _print(msg: str) -> None:
    if console:
        console.print(msg)
    else:
        print(msg)


# ---------------------------------------------------------------------------
# Yordamchi funksiyalar
# ---------------------------------------------------------------------------

def _status_icon(ok: bool) -> str:
    return "✅" if ok else "❌"


def _warn_icon() -> str:
    return "⚠️ "


# ---------------------------------------------------------------------------
# Tekshiruvlar
# ---------------------------------------------------------------------------

def check_python() -> tuple[bool, str]:
    ver = sys.version_info
    ok = ver >= (3, 10)
    return ok, f"Python {ver.major}.{ver.minor}.{ver.micro}"


def check_venv() -> tuple[bool, str]:
    in_venv = (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )
    return in_venv, "Virtual environment aktiv" if in_venv else "venv topilmadi"


def check_dependencies() -> list[tuple[str, bool, str]]:
    packages = [
        ("pydantic", "pydantic"),
        ("rich", "rich"),
        ("python-dotenv", "dotenv"),
        ("httpx", "httpx"),
        ("chromadb", "chromadb"),
        ("duckduckgo-search", "duckduckgo_search"),
        ("openai", "openai"),
        ("google-generativeai", "google.generativeai"),
        ("groq", "groq"),
        ("huggingface-hub", "huggingface_hub"),
        ("colorama", "colorama"),
        ("platformdirs", "platformdirs"),
    ]
    results = []
    for name, import_name in packages:
        try:
            mod = __import__(import_name.split(".")[0])
            ver = getattr(mod, "__version__", "?")
            results.append((name, True, f"v{ver}"))
        except ImportError:
            results.append((name, False, "O'rnatilmagan"))
    return results


def check_env_keys() -> list[tuple[str, bool, str]]:
    env_file = ROOT / ".env"

    results = []
    if not env_file.exists():
        results.append((".env fayli", False, "Topilmadi (setup.py ni ishlating)"))
    else:
        results.append((".env fayli", True, "Mavjud"))

    # Optional load dotenv
    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(str(env_file)) if env_file.exists() else {}
    except ImportError:
        env_vals = {}

    keys = [
        "GEMINI_API_KEY_1",
        "GEMINI_API_KEY_2",
        "DEEPSEEK_API_KEY",
        "OPENROUTER_API_KEY",
        "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY",
    ]
    for key in keys:
        val = env_vals.get(key) or os.getenv(key, "")
        if val and not val.startswith("your_"):
            results.append((key, True, "O'rnatilgan (yashirin)"))
        else:
            results.append((key, False, "O'rnatilmagan"))
    return results


def check_data_dirs() -> list[tuple[str, bool, str]]:
    dirs = [
        ROOT / "data",
        ROOT / "data" / "memory",
        ROOT / "data" / "documents",
        ROOT / "data" / "schedule",
    ]
    results = []
    for d in dirs:
        exists = d.exists() and d.is_dir()
        rel = str(d.relative_to(ROOT))
        results.append((rel, exists, "Mavjud" if exists else "Topilmadi"))
    return results


def check_chromadb() -> tuple[bool, str]:
    try:
        import chromadb  # noqa: F401
        client = chromadb.Client()
        client.heartbeat()
        return True, "ChromaDB ulandi"
    except ImportError:
        return False, "chromadb o'rnatilmagan"
    except Exception as exc:
        return False, f"Ulanish xatosi: {exc}"


def check_providers() -> list[tuple[str, bool, str]]:
    providers = [
        ("Gemini", ["GEMINI_API_KEY_1", "GEMINI_API_KEY_2"]),
        ("DeepSeek", ["DEEPSEEK_API_KEY"]),
        ("OpenRouter", ["OPENROUTER_API_KEY"]),
        ("Groq", ["GROQ_API_KEY"]),
        ("HuggingFace", ["HUGGINGFACE_API_KEY"]),
    ]

    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(str(ROOT / ".env")) if (ROOT / ".env").exists() else {}
    except ImportError:
        env_vals = {}

    results = []
    for name, keys in providers:
        # check both env_vals (if we could load them) and os.getenv
        has_key = False
        for k in keys:
            val = env_vals.get(k) or os.getenv(k, "")
            if val and not val.startswith("your_"):
                has_key = True
                break
        results.append((name, has_key, "API kalit mavjud" if has_key else "API kalit yo'q"))
    return results


# ---------------------------------------------------------------------------
# Natijalarni chiqarish
# ---------------------------------------------------------------------------

def _make_table(title: str) -> "Table":
    t = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t.add_column("Tekshiruv", style="bold")
    t.add_column("Holat", justify="center")
    t.add_column("Ma'lumot")
    return t


def _row_style(ok: bool) -> str:
    return "green" if ok else "red"


def run_health_check() -> None:
    if not _RICH:
        print("Rich kutubxonasi topilmadi. O'rnatish: pip install rich")
        _run_plain()
        return

    _print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    _print("[bold cyan]   JARVIS-X — Tizim Diagnostikasi[/bold cyan]")
    _print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # 1. Python va venv
    t1 = _make_table("Muhit")
    py_ok, py_msg = check_python()
    t1.add_row("Python versiyasi", _status_icon(py_ok), py_msg, style=_row_style(py_ok))
    venv_ok, venv_msg = check_venv()
    t1.add_row("Virtual environment", _status_icon(venv_ok), venv_msg, style=_row_style(venv_ok))
    console.print(t1)  # type: ignore[union-attr]

    # 2. Dependencies
    t2 = _make_table("Bog'liqliklar")
    for name, ok, msg in check_dependencies():
        t2.add_row(name, _status_icon(ok), msg, style=_row_style(ok))
    console.print(t2)  # type: ignore[union-attr]

    # 3. API Kalitlar
    t3 = _make_table("API Kalitlar (.env)")
    env_results = check_env_keys()
    for name, ok, msg in env_results:
        t3.add_row(name, _status_icon(ok), msg, style=_row_style(ok))
    console.print(t3)  # type: ignore[union-attr]

    # 4. Data papkalar
    t4 = _make_table("Data Papkalar")
    for name, ok, msg in check_data_dirs():
        t4.add_row(name, _status_icon(ok), msg, style=_row_style(ok))
    console.print(t4)  # type: ignore[union-attr]

    # 5. ChromaDB
    t5 = _make_table("ChromaDB")
    chroma_ok, chroma_msg = check_chromadb()
    t5.add_row("ChromaDB ulanish", _status_icon(chroma_ok), chroma_msg, style=_row_style(chroma_ok))
    console.print(t5)  # type: ignore[union-attr]

    # 6. AI Provayderlar
    t6 = _make_table("AI Provayderlar")
    providers = check_providers()
    for name, ok, msg in providers:
        t6.add_row(name, _status_icon(ok), msg, style=_row_style(ok))
    console.print(t6)  # type: ignore[union-attr]

    # Umumiy xulosa
    active_providers = sum(1 for _, ok, _ in providers if ok)
    all_ok = py_ok and venv_ok
    if not all_ok:
        _print("\n[red]❌ Muhit muammolari aniqlandi. Qayta sozlang: python setup.py[/red]\n")
    elif active_providers == 0:
        _print("\n[yellow]⚠️  Hech qanday AI provider API kaliti o'rnatilmagan. .env faylini tahrirlang.[/yellow]\n")
    else:
        _print(f"\n[green]✅ Tizim tayyor! {active_providers} ta AI provider faol.[/green]\n")


def _run_plain() -> None:
    """Rich mavjud bo'lmaganda oddiy matn chiqishi."""
    print("\n=== JARVIS-X Health Check ===\n")

    py_ok, py_msg = check_python()
    print(f"{_status_icon(py_ok)} Python: {py_msg}")

    venv_ok, venv_msg = check_venv()
    print(f"{_status_icon(venv_ok)} venv: {venv_msg}")

    print("\n--- Bog'liqliklar ---")
    for name, ok, msg in check_dependencies():
        print(f"  {_status_icon(ok)} {name}: {msg}")

    print("\n--- API Kalitlar ---")
    for name, ok, msg in check_env_keys():
        print(f"  {_status_icon(ok)} {name}: {msg}")

    print("\n--- Data Papkalar ---")
    for name, ok, msg in check_data_dirs():
        print(f"  {_status_icon(ok)} {name}: {msg}")

    chroma_ok, chroma_msg = check_chromadb()
    print(f"\n{_status_icon(chroma_ok)} ChromaDB: {chroma_msg}")

    print("\n--- AI Provayderlar ---")
    for name, ok, msg in check_providers():
        print(f"  {_status_icon(ok)} {name}: {msg}")

    print()


if __name__ == "__main__":
    run_health_check()
