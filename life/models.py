from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ClassStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class ClassSchedule(BaseModel):
    """Dars jadvali modeli."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str  # Fan nomi: "Matematika", "Fizika"
    day: DayOfWeek  # Hafta kuni
    start_time: str  # "09:00" format
    end_time: str  # "10:30" format
    location: str = ""  # Xona/Bino
    teacher: str = ""  # O'qituvchi
    notes: str = ""  # Qo'shimcha
    status: ClassStatus = ClassStatus.UPCOMING


class Homework(BaseModel):
    """Uy vazifasi modeli."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    subject: str  # Fan nomi
    description: str  # Vazifa tavsifi
    assigned_date: str  # "2026-02-28" format
    deadline: str = ""  # "2026-03-02" format
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    notes: str = ""


class Task(BaseModel):
    """Vazifa modeli."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    deadline: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    category: str = "general"  # "study", "personal", "project"


class DailyPlan(BaseModel):
    """Kundalik reja modeli."""

    date: str  # "2026-02-28"
    wake_up_time: str = "07:00"
    classes: list[dict] = []  # Bugungi darslar
    study_blocks: list[dict] = []  # O'qish vaqtlari
    tasks: list[dict] = []  # Bugungi vazifalar
    breaks: list[dict] = []  # Dam olish vaqtlari
    notes: str = ""
