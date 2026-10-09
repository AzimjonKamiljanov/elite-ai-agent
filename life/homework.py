from datetime import datetime, timedelta

from life.models import Homework, Task, TaskPriority, TaskStatus
from life.storage import LifeStorage

_PRIORITY_SCORE = {
    TaskPriority.URGENT: 4,
    TaskPriority.HIGH: 3,
    TaskPriority.MEDIUM: 2,
    TaskPriority.LOW: 1,
}


class HomeworkManager:
    """Uy vazifalari va vazifalar boshqaruvchisi."""

    def __init__(self):
        self.storage = LifeStorage()
        self._homework: list[Homework] = []
        self._tasks: list[Task] = []
        self._load_data()

    # === Ichki yordamchilar ===

    def _load_data(self) -> None:
        """Ma'lumotlarni saqlashdan yuklash."""
        self._homework = [Homework(**item) for item in self.storage.load_homework()]
        self._tasks = [Task(**item) for item in self.storage.load_tasks()]

    def _save_homework(self) -> None:
        self.storage.save_homework([h.model_dump() for h in self._homework])

    def _save_tasks(self) -> None:
        self.storage.save_tasks([t.model_dump() for t in self._tasks])

    def _today_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _tomorrow_str(self) -> str:
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # === Homework ===

    def add_homework(
        self,
        subject: str,
        description: str,
        deadline: str = "",
        priority: str = "medium",
    ) -> Homework:
        """Yangi uy vazifasini qo'shish."""
        hw = Homework(
            subject=subject,
            description=description,
            assigned_date=self._today_str(),
            deadline=deadline,
            priority=TaskPriority(priority.lower()),
        )
        self._homework.append(hw)
        self._save_homework()
        return hw

    def complete_homework(self, homework_id: str) -> bool:
        """Uy vazifasini bajarilgan deb belgilash."""
        for hw in self._homework:
            if hw.id == homework_id:
                hw.status = TaskStatus.COMPLETED
                self._save_homework()
                return True
        return False

    def get_pending_homework(self) -> list[Homework]:
        """Bajarilmagan uy vazifalari ro'yxati."""
        return [
            hw for hw in self._homework if hw.status != TaskStatus.COMPLETED
        ]

    def get_homework_by_subject(self, subject: str) -> list[Homework]:
        """Ma'lum fan bo'yicha uy vazifalari."""
        return [hw for hw in self._homework if hw.subject.lower() == subject.lower()]

    def get_overdue_homework(self) -> list[Homework]:
        """Muddati o'tgan uy vazifalari."""
        today = self._today_str()
        return [
            hw
            for hw in self._homework
            if hw.deadline and hw.deadline < today and hw.status != TaskStatus.COMPLETED
        ]

    def get_due_today(self) -> list[Homework]:
        """Bugun muddati tugaydigan vazifalar."""
        today = self._today_str()
        return [
            hw
            for hw in self._homework
            if hw.deadline == today and hw.status != TaskStatus.COMPLETED
        ]

    def get_due_tomorrow(self) -> list[Homework]:
        """Ertaga muddati tugaydigan vazifalar."""
        tomorrow = self._tomorrow_str()
        return [
            hw
            for hw in self._homework
            if hw.deadline == tomorrow and hw.status != TaskStatus.COMPLETED
        ]

    # === General Tasks ===

    def add_task(
        self,
        title: str,
        description: str = "",
        deadline: str = "",
        priority: str = "medium",
        category: str = "general",
    ) -> Task:
        """Yangi vazifa qo'shish."""
        task = Task(
            title=title,
            description=description,
            deadline=deadline,
            priority=TaskPriority(priority.lower()),
            category=category,
        )
        self._tasks.append(task)
        self._save_tasks()
        return task

    def complete_task(self, task_id: str) -> bool:
        """Vazifani bajarilgan deb belgilash."""
        for task in self._tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                self._save_tasks()
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Bajarilmagan vazifalar."""
        return [t for t in self._tasks if t.status != TaskStatus.COMPLETED]

    def get_all_pending(self) -> list[dict]:
        """Barcha bajarilmagan homework + tasks, priority bo'yicha tartiblangan.

        Returns:
            [{"type": "homework"|"task", "item": ..., "priority_score": int}]
        """
        combined: list[dict] = []
        for hw in self.get_pending_homework():
            combined.append(
                {
                    "type": "homework",
                    "item": hw,
                    "priority_score": _PRIORITY_SCORE.get(hw.priority, 2),
                }
            )
        for task in self.get_pending_tasks():
            combined.append(
                {
                    "type": "task",
                    "item": task,
                    "priority_score": _PRIORITY_SCORE.get(task.priority, 2),
                }
            )
        combined.sort(key=lambda x: x["priority_score"], reverse=True)
        return combined

    def find_homework_by_prefix(self, id_prefix: str) -> Homework | None:
        """ID prefiksi bo'yicha uy vazifasini topish."""
        for hw in self._homework:
            if hw.id.startswith(id_prefix):
                return hw
        return None

    def find_task_by_prefix(self, id_prefix: str) -> Task | None:
        """ID prefiksi bo'yicha vazifani topish."""
        for task in self._tasks:
            if task.id.startswith(id_prefix):
                return task
        return None

    # === Statistika ===

    def get_stats(self) -> dict:
        """Statistika ma'lumotlarini qaytarish."""
        total_hw = len(self._homework)
        completed_hw = sum(1 for h in self._homework if h.status == TaskStatus.COMPLETED)
        pending_hw = total_hw - completed_hw
        overdue_hw = len(self.get_overdue_homework())

        total_tasks = len(self._tasks)
        completed_tasks = sum(1 for t in self._tasks if t.status == TaskStatus.COMPLETED)

        total = total_hw + total_tasks
        completed_total = completed_hw + completed_tasks
        completion_rate = round(completed_total / total * 100, 1) if total > 0 else 0.0

        return {
            "total_homework": total_hw,
            "completed_homework": completed_hw,
            "pending_homework": pending_hw,
            "overdue_homework": overdue_hw,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
        }
