import streamlit as st
from datetime import datetime
from pawpal_system import Priority, Status, Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state initialization (vault) ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        contact_info="",
        preferences={"preferred_walk_time": "08:00"},
    )

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
    st.session_state.owner.set_plan_generator(st.session_state.scheduler)

owner: Owner = st.session_state.owner

# --- Add a Pet ---
st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
    pet_type = st.selectbox("Species", ["dog", "cat", "other"])
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
with col2:
    pet_breed = st.text_input("Breed", value="Mixed")
    pet_weight = st.number_input("Weight (lbs)", min_value=0.1, max_value=300.0, value=15.0)

if st.button("Add Pet"):
    new_pet = Pet(
        name=pet_name,
        type=pet_type,
        age=pet_age,
        breed=pet_breed,
        weight=pet_weight,
    )
    owner.add_pet(new_pet)
    st.success(f"Added {new_pet.name} ({new_pet.type}) — ID: {new_pet.id[:8]}…")

if owner.pets:
    st.write("**Pets on file:**")
    st.table([
        {"Name": p.name, "Type": p.type, "Breed": p.breed, "Age": p.age, "ID": p.id[:8]}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Schedule a Task ---
st.subheader("Schedule a Task")

if not owner.pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    pet_options = {p.name: p for p in owner.pets}
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        selected_pet_name = st.selectbox("For pet", list(pet_options.keys()))
    with col2:
        task_details = st.text_input("Details", value="30-minute walk around the block")
        task_priority = st.selectbox("Priority", ["high", "medium", "low"], index=0)
    with col3:
        task_date = st.date_input("Date", value=datetime.now().date())
        task_time = st.time_input("Time", value=datetime.now().replace(hour=8, minute=0).time())

    if st.button("Add Task"):
        selected_pet = pet_options[selected_pet_name]
        new_task = Task(
            datetime=datetime.combine(task_date, task_time),
            title=task_title,
            details=task_details,
            priority=Priority(task_priority),
            status=Status.PENDING,
            pet_id=selected_pet.id,
        )
        owner.schedule_task(new_task)
        st.success(f"Scheduled '{new_task.title}' for {selected_pet_name}.")

    today_tasks = owner.view_todays_tasks()
    if today_tasks:
        st.write("**Today's tasks:**")
        st.table([
            {
                "Time": t.datetime.strftime("%H:%M"),
                "Title": t.title,
                "Priority": t.priority.value,
                "Status": t.status.value,
            }
            for t in today_tasks
        ])
    else:
        st.info("No tasks scheduled for today yet.")

st.divider()

# --- Generate Daily Plan ---
st.subheader("Generate Daily Plan")
st.caption("Auto-generates a full day of tasks for all pets based on owner preferences.")

if st.button("Generate schedule"):
    if not owner.pets:
        st.warning("Add at least one pet before generating a plan.")
    else:
        owner.generate_plan()
        plan = owner.view_todays_tasks()
        if plan:
            st.success(f"Generated {len(plan)} tasks for today.")
            st.table([
                {
                    "Time": t.datetime.strftime("%H:%M"),
                    "Pet": next((p.name for p in owner.pets if p.id == t.pet_id), "?"),
                    "Title": t.title,
                    "Priority": t.priority.value,
                    "Status": t.status.value,
                }
                for t in plan
            ])
        else:
            st.info("Plan generated but no tasks scheduled for today.")
