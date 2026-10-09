"""
Tool Registry — Vositalar reestri va bajaruv tizimi.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    """Vositalar reestri — dinamik ro'yxatga olish va bajarish."""

    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: dict | None = None,
    ) -> None:
        """Vositani ro'yxatga olish.

        Args:
            name: Vosita nomi
            func: Bajariladigan funksiya
            description: Vosita tavsifi
            parameters: Parametrlar sxemasi (ixtiyoriy)
        """
        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters or {},
        }

    def execute_tool(self, name: str, **kwargs: Any) -> Any:
        """Vositani bajarish.

        Args:
            name: Vosita nomi
            **kwargs: Vosita parametrlari

        Returns:
            Vosita natijasi
        """
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Vosita topilmadi: '{name}'")
        return tool["func"](**kwargs)

    def list_tools(self) -> list[dict]:
        """Ro'yxatga olingan vositalar ro'yxati."""
        return [
            {"name": t["name"], "description": t["description"]}
            for t in self._tools.values()
        ]

    def get_tool_names(self) -> list[str]:
        """Vositalar nomlari."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Vosita mavjudligini tekshirish."""
        return name in self._tools

    def register_from_module(self, module: Any) -> int:
        """Moduldan barcha Tool sinflarini ro'yxatga olish.

        Returns:
            Ro'yxatga olingan vositalar soni
        """
        count = 0
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and attr_name.endswith("Tool")
                and hasattr(obj, "execute")
            ):
                try:
                    instance = obj()
                    tool_name = attr_name.replace("Tool", "").lower()
                    self.register(
                        name=tool_name,
                        func=instance.execute if hasattr(instance, "execute") else lambda **kw: None,
                        description=obj.__doc__ or "",
                    )
                    count += 1
                except Exception:
                    pass
        return count
