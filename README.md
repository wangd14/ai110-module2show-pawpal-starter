# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class includes several features beyond basic task generation:

**Auto-rescheduling recurring tasks** — When `Scheduler.complete_task(task)` is called on a `daily` or `weekly` task, it automatically creates and schedules the next occurrence (shifted by 1 day or 7 days). Tasks with `frequency="once"` are simply marked complete with no follow-up.

**Time-based sorting** — `Scheduler.sort_by_time(tasks)` returns tasks sorted by their scheduled `datetime`, making it easy to display a chronological view independent of insertion order.

**Flexible filtering** — `Scheduler.filter_tasks(status, pet_name)` accepts optional parameters to narrow tasks by completion status (`PENDING`, `COMPLETED`, `CANCELLED`), by pet name, or both combined.

**Conflict detection** — `Scheduler.find_conflicts()` scans all pending tasks and returns every pair scheduled at the exact same time, whether for the same pet or different pets. It never raises an exception — callers receive an empty list when no conflicts exist and display a warning message otherwise.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
