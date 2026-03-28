from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Status


def print_tasks(tasks: list[Task], label: str, owner: Owner) -> None:
    print(f"\n{'='*54}")
    print(f"  {label}")
    print(f"{'='*54}")
    if not tasks:
        print("  (no tasks)")
    else:
        for task in tasks:
            pet = owner.get_pet_by_id(task.pet_id)
            pet_name = pet.name if pet else "?"
            time_str = task.datetime.strftime("%I:%M %p")
            status_icon = "[x]" if task.status == Status.COMPLETED else "[ ]"
            overdue_flag = " !! OVERDUE" if task.is_overdue() else ""
            print(
                f"  {status_icon} {time_str}  [{task.priority.value.upper():6}]"
                f"  {pet_name:10}  {task.title}{overdue_flag}"
            )
    print(f"{'='*54}")


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

# --- Add tasks OUT OF ORDER intentionally ---
today = datetime.now()

task_evening_buddy = Task(
    datetime=today.replace(hour=18, minute=0, second=0, microsecond=0),
    title="Feed Buddy (evening)",
    details="Evening kibble — 2 cups.",
    priority=Priority.MEDIUM,
    status=Status.PENDING,
    pet_id=buddy.id,
    frequency="daily",
)

task_vet = Task(
    datetime=today.replace(hour=14, minute=0, second=0, microsecond=0),
    title="Whiskers vet check-up",
    details="Annual wellness exam at Paws & Care Clinic.",
    priority=Priority.HIGH,
    status=Status.PENDING,
    pet_id=whiskers.id,
    frequency="once",
)

task_walk = Task(
    datetime=today.replace(hour=8, minute=0, second=0, microsecond=0),
    title="Walk Buddy",
    details="30-minute morning walk around the park.",
    priority=Priority.HIGH,
    status=Status.PENDING,
    pet_id=buddy.id,
    frequency="daily",
)

task_feed_whiskers = Task(
    datetime=today.replace(hour=9, minute=0, second=0, microsecond=0),
    title="Feed Whiskers",
    details="Morning wet food — half can.",
    priority=Priority.HIGH,
    status=Status.COMPLETED,
    pet_id=whiskers.id,
    frequency="daily",
)

task_feed_buddy = Task(
    datetime=today.replace(hour=7, minute=30, second=0, microsecond=0),
    title="Feed Buddy",
    details="Morning kibble — 2 cups.",
    priority=Priority.HIGH,
    status=Status.COMPLETED,
    pet_id=buddy.id,
    frequency="daily",
)

# Schedule out of order: evening first, then vet, walk, etc.
for task in [task_evening_buddy, task_vet, task_walk, task_feed_whiskers, task_feed_buddy]:
    owner.schedule_task(task)

scheduler = Scheduler(owner)

# --- Demo 1: sort_by_time ---
sorted_tasks = scheduler.sort_by_time(owner.tasks)
print_tasks(sorted_tasks, "All Tasks — sorted by time (HH:MM)", owner)

# --- Demo 2: filter by COMPLETED ---
completed = scheduler.filter_tasks(status=Status.COMPLETED)
print_tasks(completed, "Filter: COMPLETED tasks only", owner)

# --- Demo 3: filter by PENDING ---
pending = scheduler.filter_tasks(status=Status.PENDING)
print_tasks(pending, "Filter: PENDING tasks only", owner)

# --- Demo 4: filter by pet name ---
buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
print_tasks(buddy_tasks, "Filter: Buddy's tasks only", owner)

# --- Demo 5: filter by pet name + status ---
buddy_pending = scheduler.filter_tasks(status=Status.PENDING, pet_name="Buddy")
print_tasks(buddy_pending, "Filter: Buddy's PENDING tasks", owner)

# --- Demo 6: complete a recurring task → auto-schedule next occurrence ---
print("\n>>> Completing 'Walk Buddy' (daily)...")
next_task = scheduler.complete_task(task_walk)
if next_task:
    print(f"    Auto-scheduled: '{next_task.title}' on {next_task.datetime.strftime('%A, %B %d at %I:%M %p')}")

print("\n>>> Completing 'Whiskers vet check-up' (once)...")
next_task = scheduler.complete_task(task_vet)
if next_task:
    print(f"    Auto-scheduled: '{next_task.title}'")
else:
    print("    No follow-up scheduled (frequency='once').")

all_tasks = scheduler.sort_by_time(owner.tasks)
print_tasks(all_tasks, "All Tasks after completing Walk Buddy + vet check-up", owner)

# --- Demo 7: conflict detection ---
# Add two tasks at the exact same time to trigger a conflict warning
task_conflict_a = Task(
    datetime=today.replace(hour=10, minute=0, second=0, microsecond=0),
    title="Buddy bath time",
    details="Rinse and dry.",
    priority=Priority.MEDIUM,
    status=Status.PENDING,
    pet_id=buddy.id,
)
task_conflict_b = Task(
    datetime=today.replace(hour=10, minute=0, second=0, microsecond=0),
    title="Whiskers grooming",
    details="Brush and trim nails.",
    priority=Priority.MEDIUM,
    status=Status.PENDING,
    pet_id=whiskers.id,
)
owner.schedule_task(task_conflict_a)
owner.schedule_task(task_conflict_b)

print(f"\n{'='*54}")
print("  Conflict Detection")
print(f"{'='*54}")
conflicts = scheduler.find_conflicts()
if conflicts:
    for task_a, task_b in conflicts:
        pet_a = owner.get_pet_by_id(task_a.pet_id)
        pet_b = owner.get_pet_by_id(task_b.pet_id)
        print(
            f"  WARNING: '{task_a.title}' ({pet_a.name if pet_a else '?'}) and"
            f" '{task_b.title}' ({pet_b.name if pet_b else '?'})"
            f" are both scheduled at {task_a.datetime.strftime('%I:%M %p')}."
        )
else:
    print("  No scheduling conflicts found.")
print(f"{'='*54}")
