from datetime import datetime

from pawpal_system import Owner, Pet, Priority, Scheduler, Status, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pet(name="Buddy", type="dog"):
    return Pet(name=name, type=type, age=3, breed="Labrador", weight=30.0)


def make_task(pet_id: str, dt: datetime = None, priority: Priority = Priority.MEDIUM,
              status: Status = Status.PENDING, frequency: str = "once", title: str = "Walk Buddy") -> Task:
    return Task(
        datetime=dt or datetime(2026, 3, 28, 8, 0),
        title=title,
        details="Morning walk",
        priority=priority,
        status=status,
        pet_id=pet_id,
        frequency=frequency,
    )


def make_owner_with_scheduler(preferences=None):
    owner = Owner(name="Alice", contact_info="alice@example.com",
                  preferences=preferences or {})
    scheduler = Scheduler(owner)
    return owner, scheduler


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should set the task status to COMPLETED."""
    pet = make_pet()
    task = make_task(pet.id)

    assert task.status == Status.PENDING
    task.mark_complete()
    assert task.status == Status.COMPLETED


def test_add_task_increases_pet_task_count():
    """Appending a task to a Pet's task list should increase its count by 1."""
    pet = Pet(name="Whiskers", type="cat", age=2, breed="Tabby", weight=4.5)

    assert len(pet.tasks) == 0
    pet.tasks.append(make_task(pet.id))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_optimize_schedule_chronological_order():
    """Tasks should be sorted by datetime ascending."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    t1 = make_task(pet.id, dt=datetime(2026, 3, 28, 12, 0))
    t2 = make_task(pet.id, dt=datetime(2026, 3, 28, 7, 0))
    t3 = make_task(pet.id, dt=datetime(2026, 3, 28, 9, 0))

    sorted_tasks = scheduler.optimize_schedule([t1, t2, t3])
    times = [t.datetime for t in sorted_tasks]
    assert times == sorted(times)


def test_optimize_schedule_priority_tiebreak():
    """Tasks at the same time should be ordered HIGH → MEDIUM → LOW."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    dt = datetime(2026, 3, 28, 8, 0)
    low  = make_task(pet.id, dt=dt, priority=Priority.LOW)
    high = make_task(pet.id, dt=dt, priority=Priority.HIGH)
    med  = make_task(pet.id, dt=dt, priority=Priority.MEDIUM)

    result = scheduler.optimize_schedule([low, high, med])
    assert [t.priority for t in result] == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_sort_by_time_uses_hhmm():
    """sort_by_time should order tasks by wall-clock time regardless of date."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    t_late  = make_task(pet.id, dt=datetime(2026, 3, 28, 18, 0))
    t_early = make_task(pet.id, dt=datetime(2026, 3, 29,  7, 0))  # next day but earlier time

    result = scheduler.sort_by_time([t_late, t_early])
    assert result[0].datetime.hour == 7
    assert result[1].datetime.hour == 18


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_occurrence():
    """Completing a daily task should produce a new PENDING task 24 h later."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    task = make_task(pet.id, dt=datetime(2026, 3, 28, 8, 0), frequency="daily")
    owner.schedule_task(task)

    next_task = scheduler.complete_task(task)

    assert next_task is not None
    assert next_task.status == Status.PENDING
    assert next_task.datetime == datetime(2026, 3, 29, 8, 0)
    assert next_task in owner.tasks


def test_complete_weekly_task_creates_next_week_occurrence():
    """Completing a weekly task should produce a new PENDING task 7 days later."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    task = make_task(pet.id, dt=datetime(2026, 3, 28, 8, 0), frequency="weekly")
    owner.schedule_task(task)

    next_task = scheduler.complete_task(task)

    assert next_task is not None
    assert next_task.datetime == datetime(2026, 4, 4, 8, 0)


def test_complete_once_task_returns_none():
    """Completing a 'once' task should not create a follow-up task."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    task = make_task(pet.id, frequency="once")
    owner.schedule_task(task)

    next_task = scheduler.complete_task(task)

    assert next_task is None
    assert len(owner.tasks) == 1  # no new task added


def test_complete_task_twice_does_not_duplicate():
    """Completing the same daily task twice should not add two recurrences."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    task = make_task(pet.id, frequency="daily")
    owner.schedule_task(task)

    scheduler.complete_task(task)
    scheduler.complete_task(task)  # second call on already-completed task

    # Only one follow-up should exist
    follow_ups = [t for t in owner.tasks if t is not task]
    assert len(follow_ups) == 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_find_conflicts_detects_same_time():
    """Two PENDING tasks at identical datetimes should be flagged as a conflict."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    dt = datetime(2026, 3, 28, 8, 0)
    t1 = make_task(pet.id, dt=dt, title="Walk Buddy")
    t2 = make_task(pet.id, dt=dt, title="Vet Visit")
    owner.schedule_task(t1)
    owner.schedule_task(t2)

    conflicts = scheduler.find_conflicts()

    assert len(conflicts) == 1
    assert (t1, t2) in conflicts or (t2, t1) in conflicts


def test_find_conflicts_cross_pet():
    """Conflicts should be detected between tasks for different pets."""
    owner, scheduler = make_owner_with_scheduler()
    buddy   = make_pet(name="Buddy")
    whiskers = make_pet(name="Whiskers", type="cat")
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    dt = datetime(2026, 3, 28, 9, 0)
    t1 = make_task(buddy.id,    dt=dt, title="Walk Buddy")
    t2 = make_task(whiskers.id, dt=dt, title="Feed Whiskers")
    owner.schedule_task(t1)
    owner.schedule_task(t2)

    conflicts = scheduler.find_conflicts()
    assert len(conflicts) == 1


def test_find_conflicts_three_tasks_same_time():
    """Three PENDING tasks at the same time should produce 3 conflict pairs."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    dt = datetime(2026, 3, 28, 8, 0)
    tasks = [make_task(pet.id, dt=dt, title=f"Task {i}") for i in range(3)]
    for t in tasks:
        owner.schedule_task(t)

    conflicts = scheduler.find_conflicts()
    assert len(conflicts) == 3


def test_find_conflicts_ignores_completed_tasks():
    """Completed tasks at the same time as a PENDING task should not be a conflict."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    dt = datetime(2026, 3, 28, 8, 0)
    t_done    = make_task(pet.id, dt=dt, status=Status.COMPLETED)
    t_pending = make_task(pet.id, dt=dt, status=Status.PENDING)
    owner.schedule_task(t_done)
    owner.schedule_task(t_pending)

    assert scheduler.find_conflicts() == []


def test_no_conflicts_different_times():
    """Tasks at different times should not be flagged."""
    owner, scheduler = make_owner_with_scheduler()
    pet = make_pet()
    owner.add_pet(pet)

    t1 = make_task(pet.id, dt=datetime(2026, 3, 28, 8, 0))
    t2 = make_task(pet.id, dt=datetime(2026, 3, 28, 9, 0))
    owner.schedule_task(t1)
    owner.schedule_task(t2)

    assert scheduler.find_conflicts() == []
