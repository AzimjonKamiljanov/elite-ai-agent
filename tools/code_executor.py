"""
Xavfsiz kod bajarish vositasi — subprocess va timeout himoyasi bilan.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

_DEFAULT_TIMEOUT = 10  # sekund
_MAX_OUTPUT_SIZE = 10_000  # belgi


class CodeExecutorTool:
    """Python kodni xavfsiz subprocess ichida bajarish."""

    def execute(self, code: str, timeout: int = _DEFAULT_TIMEOUT) -> str:
        """Python kodni bajarish.

        Args:
            code: Bajariladigan Python kodi
            timeout: Maksimal bajarish vaqti (sekund)

        Returns:
            Stdout + stderr natijasi
        """
        if not code.strip():
            return "Bo'sh kod."

        # Vaqtinchalik fayl yaratish
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8",
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir(),
            )

            output_parts = []
            if result.stdout:
                stdout = result.stdout[:_MAX_OUTPUT_SIZE]
                output_parts.append(f"Output:\n{stdout}")
            if result.stderr:
                stderr = result.stderr[:_MAX_OUTPUT_SIZE]
                output_parts.append(f"Stderr:\n{stderr}")
            if result.returncode != 0:
                output_parts.append(f"Return code: {result.returncode}")

            return "\n".join(output_parts) if output_parts else "✅ Kod muvaffaqiyatli bajarildi (natija yo'q)."

        except subprocess.TimeoutExpired:
            return f"⏱ Timeout: kod {timeout} sekund ichida bajarilmadi."
        except Exception as exc:
            return f"❌ Bajarish xatosi: {exc}"
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
