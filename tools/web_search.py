"""
Web qidiruv vositasi — DuckDuckGo orqali bepul internet qidiruvchi.
"""

from __future__ import annotations


class WebSearchTool:
    """DuckDuckGo yordamida web qidiruvchi."""

    def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Internet qidiruvi.

        Args:
            query: Qidiruv so'rovi
            num_results: Natijalar soni (default: 5)

        Returns:
            [{"title": str, "url": str, "snippet": str}]
        """
        if not query.strip():
            return []

        try:
            from duckduckgo_search import DDGS  # type: ignore

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        }
                    )
            return results
        except ImportError:
            return [
                {
                    "title": "Xato",
                    "url": "",
                    "snippet": "duckduckgo-search o'rnatilmagan: pip install duckduckgo-search",
                }
            ]
        except Exception as exc:
            return [
                {
                    "title": "Qidiruv xatosi",
                    "url": "",
                    "snippet": str(exc),
                }
            ]

    def format_results(self, results: list[dict]) -> str:
        """Natijalarni matn formatiga o'girish."""
        if not results:
            return "Natija topilmadi."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**")
            lines.append(f"   {r['url']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")
        return "\n".join(lines).strip()
