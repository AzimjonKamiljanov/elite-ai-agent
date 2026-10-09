import json
from pathlib import Path


class LifeStorage:
    """JSON fayl asosidagi doimiy saqlash."""

    def __init__(self, data_dir: str = "data/schedule"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.schedule_file = self.data_dir / "schedule.json"
        self.homework_file = self.data_dir / "homework.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.plans_file = self.data_dir / "daily_plans.json"

    def _read_file(self, path: Path) -> list[dict]:
        """JSON fayldan ro'yxat o'qish."""
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_file(self, path: Path, data: list[dict]) -> None:
        """JSON faylga ro'yxat yozish."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_dict_file(self, path: Path) -> dict:
        """JSON fayldan lug'at o'qish."""
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_dict_file(self, path: Path, data: dict) -> None:
        """JSON faylga lug'at yozish."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_schedule(self) -> list[dict]:
        """Dars jadvalini yuklash."""
        return self._read_file(self.schedule_file)

    def save_schedule(self, schedule: list[dict]) -> None:
        """Dars jadvalini saqlash."""
        self._write_file(self.schedule_file, schedule)

    def load_homework(self) -> list[dict]:
        """Uy vazifalarini yuklash."""
        return self._read_file(self.homework_file)

    def save_homework(self, homework: list[dict]) -> None:
        """Uy vazifalarini saqlash."""
        self._write_file(self.homework_file, homework)

    def load_tasks(self) -> list[dict]:
        """Vazifalarni yuklash."""
        return self._read_file(self.tasks_file)

    def save_tasks(self, tasks: list[dict]) -> None:
        """Vazifalarni saqlash."""
        self._write_file(self.tasks_file, tasks)

    def load_daily_plan(self, date: str) -> dict | None:
        """Ma'lum kun uchun rejani yuklash."""
        plans = self._read_dict_file(self.plans_file)
        return plans.get(date)

    def save_daily_plan(self, plan: dict) -> None:
        """Kundalik rejani saqlash."""
        plans = self._read_dict_file(self.plans_file)
        plans[plan["date"]] = plan
        self._write_dict_file(self.plans_file, plans)
