from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Status


def print_schedule(tasks: list[Task], owner_name: str) -> None:
    today = datetime.now().strftime("%A, %B %d, %Y")
    print(f"\n{'='*50}")
    print(f"  Today's Schedule for {owner_name} — {today}")
    print(f"{'='*50}")

    if not tasks:
        print("  No tasks scheduled for today.")
    else:
        for task in tasks:
            time_str = task.datetime.strftime("%I:%M %p")
            status_icon = "[x]" if task.status == Status.COMPLETED else "[ ]"
            overdue_flag = " !! OVERDUE" if task.is_overdue() else ""
            print(f"  {status_icon} {time_str}  [{task.priority.value.upper()}]  {task.title}{overdue_flag}")

    print(f"{'='*50}\n")


# --- Setup ---
owner = Owner(
    name="Alex Rivera",
    contact_info="alex@example.com",
    preferences={"preferred_walk_time": "08:00"},
)

buddy = Pet(name="Buddy", type="dog", age=3, breed="Golden Retriever", weight=65.0)
whiskers = Pet(name="Whiskers", type="cat", age=5, breed="Tabby", weight=10.2)

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Manual Tasks ---
today = datetime.now()

task1 = Task(
    datetime=today.replace(hour=7, minute=30, second=0, microsecond=0),
    title="Feed Buddy",
    details="Morning kibble — 2 cups.",
    priority=Priority.HIGH,
    status=Status.COMPLETED,
    pet_id=buddy.id,
    frequency="daily",
)

task2 = Task(
    datetime=today.replace(hour=8, minute=0, second=0, microsecond=0),
    title="Walk Buddy",
    details="30-minute morning walk around the park.",
    priority=Priority.HIGH,
    status=Status.PENDING,
    pet_id=buddy.id,
    frequency="daily",
)

task3 = Task(
    datetime=today.replace(hour=9, minute=0, second=0, microsecond=0),
    title="Feed Whiskers",
    details="Morning wet food — half can.",
    priority=Priority.HIGH,
    status=Status.PENDING,
    pet_id=whiskers.id,
    frequency="daily",
)

task4 = Task(
    datetime=today.replace(hour=14, minute=0, second=0, microsecond=0),
    title="Whiskers vet check-up",
    details="Annual wellness exam at Paws & Care Clinic.",
    priority=Priority.HIGH,
    status=Status.PENDING,
    pet_id=whiskers.id,
    frequency="once",
)

task5 = Task(
    datetime=today.replace(hour=18, minute=0, second=0, microsecond=0),
    title="Feed Buddy (evening)",
    details="Evening kibble — 2 cups.",
    priority=Priority.MEDIUM,
    status=Status.PENDING,
    pet_id=buddy.id,
    frequency="daily",
)

for task in [task1, task2, task3, task4, task5]:
    owner.schedule_task(task)

# --- Display ---
scheduler = Scheduler(owner)
todays_tasks = scheduler.get_all_tasks()
todays_tasks = [t for t in todays_tasks if t.datetime.date() == today.date()]

print_schedule(todays_tasks, owner.name)
