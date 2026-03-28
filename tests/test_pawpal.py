from datetime import datetime

from pawpal_system import Pet, Priority, Status, Task


def make_task(pet_id: str) -> Task:
    return Task(
        datetime=datetime(2026, 3, 28, 8, 0),
        title="Walk Buddy",
        details="Morning walk",
        priority=Priority.MEDIUM,
        status=Status.PENDING,
        pet_id=pet_id,
    )


def test_mark_complete_changes_status():
    """mark_complete() should set the task status to COMPLETED."""
    pet = Pet(name="Buddy", type="dog", age=3, breed="Labrador", weight=30.0)
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
