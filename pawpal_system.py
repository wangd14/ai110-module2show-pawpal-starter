from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    datetime: datetime
    title: str
    details: str
    priority: Priority
    status: Status
    pet_id: str  # matches Pet.id
    frequency: str = "once"  # "once", "daily", "weekly"

    def is_overdue(self) -> bool:
        """Returns True if the task is pending and its scheduled time has passed."""
        return self.status == Status.PENDING and self.datetime < datetime.now()

    def mark_complete(self) -> None:
        """Marks the task as completed."""
        self.status = Status.COMPLETED

    def next_occurrence(self) -> Optional["Task"]:
        """Returns a new pending Task for the next occurrence, or None if frequency is 'once'."""
        if self.frequency == "daily":
            delta = timedelta(days=1)
        elif self.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None
        return Task(
            datetime=self.datetime + delta,
            title=self.title,
            details=self.details,
            priority=self.priority,
            status=Status.PENDING,
            pet_id=self.pet_id,
            frequency=self.frequency,
        )

    def reschedule(self, new_datetime: datetime) -> None:
        """Reschedules the task to a new datetime and resets its status to pending."""
        self.datetime = new_datetime
        self.status = Status.PENDING


@dataclass
class Pet:
    name: str
    type: str
    age: int
    breed: str
    weight: float
    special_needs: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: list = field(default_factory=list)  # list[Task]

    def needs_walk(self) -> bool:
        """Returns True if the pet has no completed walk task today."""
        today = datetime.now().date()
        for task in self.tasks:
            if (
                "walk" in task.title.lower()
                and task.status == Status.COMPLETED
                and task.datetime.date() == today
            ):
                return False
        return self.type.lower() == "dog"

    def feed(self) -> "Task":
        """Creates and records a feeding task for now."""
        task = Task(
            datetime=datetime.now(),
            title=f"Feed {self.name}",
            details=f"Feed {self.name} their regular meal.",
            priority=Priority.HIGH,
            status=Status.COMPLETED,
            pet_id=self.id,
            frequency="daily",
        )
        self.tasks.append(task)
        return task

    def update_health_status(self, status: str) -> None:
        """Updates the pet's special needs field with the given health status."""
        self.special_needs = status


class Owner:
    def __init__(self, name: str, contact_info: str, preferences: dict):
        self.name = name
        self.contact_info = contact_info
        self.preferences = preferences
        self.pets: list[Pet] = []
        self.tasks: list[Task] = []
        self._plan_generator: Optional["Scheduler"] = None

    def set_plan_generator(self, generator: "Scheduler") -> None:
        """Sets the Scheduler instance used to generate this owner's plans."""
        self._plan_generator = generator

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to the owner's list of pets."""
        self.pets.append(pet)

    def get_pet_by_id(self, pet_id: str) -> Optional[Pet]:
        """Returns the pet matching the given ID, or None if not found."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        return None

    def schedule_task(self, task: Task) -> None:
        """Adds a task to the owner's task list and links it to the associated pet."""
        self.tasks.append(task)
        pet = self.get_pet_by_id(task.pet_id)
        if pet and task not in pet.tasks:
            pet.tasks.append(task)

    def view_todays_tasks(self) -> list[Task]:
        """Returns all tasks scheduled for today."""
        today = datetime.now().date()
        return [t for t in self.tasks if t.datetime.date() == today]

    def generate_plan(self) -> None:
        """Generates and schedules a daily plan using the configured plan generator."""
        if self._plan_generator:
            new_tasks = self._plan_generator.create_daily_plan(
                datetime.now(), constraints=self.preferences
            )
            for task in new_tasks:
                self.schedule_task(task)


class Scheduler:
    """Retrieves, organizes, and manages tasks across all pets for an owner."""

    def __init__(self, owner: Owner, model_config: dict = None):
        self.owner = owner
        self.model_config = model_config or {}

    def create_daily_plan(self, date: datetime, constraints: dict) -> list[Task]:
        """Generate a default daily task list for every pet owned."""
        tasks: list[Task] = []
        preferred_walk_time = constraints.get("preferred_walk_time", "08:00")
        walk_hour, walk_minute = (int(x) for x in preferred_walk_time.split(":"))

        for pet in self.owner.pets:
            # Morning feeding
            tasks.append(Task(
                datetime=date.replace(hour=7, minute=0, second=0, microsecond=0),
                title=f"Feed {pet.name}",
                details=f"Morning meal for {pet.name}.",
                priority=Priority.HIGH,
                status=Status.PENDING,
                pet_id=pet.id,
                frequency="daily",
            ))

            # Walk (dogs only)
            if pet.type.lower() == "dog":
                tasks.append(Task(
                    datetime=date.replace(hour=walk_hour, minute=walk_minute, second=0, microsecond=0),
                    title=f"Walk {pet.name}",
                    details=f"Daily walk for {pet.name}.",
                    priority=Priority.HIGH,
                    status=Status.PENDING,
                    pet_id=pet.id,
                    frequency="daily",
                ))

            # Evening feeding
            tasks.append(Task(
                datetime=date.replace(hour=18, minute=0, second=0, microsecond=0),
                title=f"Feed {pet.name} (evening)",
                details=f"Evening meal for {pet.name}.",
                priority=Priority.MEDIUM,
                status=Status.PENDING,
                pet_id=pet.id,
                frequency="daily",
            ))

        return self.optimize_schedule(tasks)

    def generate_weekly_plan(self) -> list[Task]:
        """Generate a daily plan for the next 7 days."""
        all_tasks: list[Task] = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for day_offset in range(7):
            day = today + timedelta(days=day_offset)
            all_tasks.extend(
                self.create_daily_plan(day, constraints=self.owner.preferences)
            )
        return all_tasks

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by their scheduled time (HH:MM) using a lambda key."""
        return sorted(tasks, key=lambda t: t.datetime.strftime("%H:%M"))

    def optimize_schedule(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by datetime, then by priority (high first)."""
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(tasks, key=lambda t: (t.datetime, priority_order[t.priority]))

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks across every pet, sorted by schedule."""
        return self.optimize_schedule(self.owner.tasks)

    def get_overdue_tasks(self) -> list[Task]:
        """Returns all tasks across the owner's pets that are past due and still pending."""
        return [t for t in self.owner.tasks if t.is_overdue()]

    def get_tasks_for_pet(self, pet_id: str) -> list[Task]:
        """Returns all tasks for the specified pet, sorted by schedule."""
        return self.optimize_schedule(
            [t for t in self.owner.tasks if t.pet_id == pet_id]
        )

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and auto-schedule the next occurrence for recurring tasks.

        Returns the newly created follow-up Task, or None if the task is 'once'.
        """
        if task.status == Status.COMPLETED:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task:
            self.owner.schedule_task(next_task)
        return next_task

    def filter_tasks(
        self,
        status: Optional[Status] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Filter tasks by completion status and/or pet name.

        Args:
            status: If provided, only return tasks with this status.
            pet_name: If provided, only return tasks belonging to the pet with this name.
        """
        results = self.owner.tasks

        if status is not None:
            results = [t for t in results if t.status == status]

        if pet_name is not None:
            name_lower = pet_name.lower()
            matching_ids = {p.id for p in self.owner.pets if p.name.lower() == name_lower}
            results = [t for t in results if t.pet_id in matching_ids]

        return self.optimize_schedule(results)

    def find_conflicts(self) -> list[tuple[Task, Task]]:
        """Return pairs of pending tasks that share the exact same scheduled time.

        Detects both same-pet conflicts (e.g. two walks at 08:00 for Buddy) and
        cross-pet conflicts (e.g. Buddy's walk and Whiskers' vet visit at 08:00).
        Each conflicting pair is returned once (no duplicates).
        """
        pending = [t for t in self.owner.tasks if t.status == Status.PENDING]
        conflicts: list[tuple[Task, Task]] = []
        for i, task_a in enumerate(pending):
            for task_b in pending[i + 1:]:
                if task_a.datetime == task_b.datetime:
                    conflicts.append((task_a, task_b))
        return conflicts
