import streamlit as st
from datetime import datetime, timedelta
import hashlib
import json
import os

# File to store user data
USER_DATA_FILE = "user_data.json"

# Load user data from file
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    else:
        return {"user_accounts": {}, "workout_logs": {}, "exp": {}, "calorie_logs": {}, "water_logs": {}}

# Save user data to file
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# Utility functions for hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load persistent user data
user_data = load_user_data()

# Initialize Streamlit session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# Function to check login credentials
def check_login(username, password):
    hashed_password = hash_password(password)
    return username in user_data["user_accounts"] and user_data["user_accounts"][username] == hashed_password

# Function to create a new account
def create_account(username, password):
    if username in user_data["user_accounts"]:
        return False, "Username already exists. Please choose a different username."
    else:
        user_data["user_accounts"][username] = hash_password(password)
        user_data["workout_logs"][username] = {}
        user_data["exp"][username] = 0
        user_data["calorie_logs"][username] = {}
        user_data["water_logs"][username] = {}
        save_user_data(user_data)
        return True, "Account created successfully! You can now log in."

# Generate a 90-day workout plan
def generate_workout_plan():
    weekly_plan = [
        ["Push-ups: 3 sets of 15", "Squats: 3 sets of 20", "Planks: 3 sets of 30 seconds"],
        ["Burpees: 3 sets of 10", "Lunges: 3 sets of 20", "Mountain Climbers: 3 sets of 30 seconds"],
        ["Bicep Curls: 3 sets of 12", "Deadlifts: 3 sets of 10", "Leg Raises: 3 sets of 15"],
        ["Bench Press: 3 sets of 10", "Pull-ups: 3 sets of 8", "Tricep Dips: 3 sets of 12"],
        ["Jump Rope: 5 minutes", "Box Jumps: 3 sets of 12", "Sit-ups: 3 sets of 20"],
        ["Cardio: 30 minutes run", "Yoga: 15 minutes stretch", "Bodyweight Rows: 3 sets of 15"],
        ["Rest Day: Focus on recovery and stretching"],
    ]

    plan = []
    for i in range(90):
        day_index = i % 7
        plan.append({"day": i + 1, "workouts": weekly_plan[day_index]})
    return plan

# Helper function to get yesterday's data for a given log type
def get_yesterday_data(username, log_type):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if yesterday in user_data[log_type].get(username, {}):
        return user_data[log_type][username][yesterday]
    return 0

# Initialize the workout plan in session state
if "workout_plan" not in st.session_state:
    st.session_state["workout_plan"] = generate_workout_plan()

# Streamlit app layout
st.title("EXP Fitness App")

# Tabs for Login and Create Account
if not st.session_state["logged_in"]:
    tab = st.radio("Choose an option:", ["Login", "Create Account"])

    if tab == "Login":
        st.subheader("Login")
        username = st.text_input("Enter your username:")
        password = st.text_input("Enter your password:", type="password")

        if st.button("Login"):
            if check_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome back, {username}!")
            else:
                st.error("Login Failed! Invalid username or password.")

    elif tab == "Create Account":
        st.subheader("Create Account")
        new_username = st.text_input("Choose a username:")
        new_password = st.text_input("Choose a password:", type="password")
        confirm_password = st.text_input("Confirm your password:", type="password")

        if st.button("Create Account"):
            if new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            elif not new_username or not new_password:
                st.error("Username and password cannot be empty.")
            else:
                success, message = create_account(new_username, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
else:
    # Logged-in view
    username = st.session_state["username"]
    st.sidebar.title(f"Welcome, {username}!")
    st.sidebar.write("Use the navigation below to explore your workout plan.")

    # Navigation options
    st.sidebar.title("Workout Navigation")
    current_day = st.sidebar.slider("Select Day", 1, 90, 1)

    # Display selected day's workout
    selected_day_workout = st.session_state["workout_plan"][current_day - 1]
    st.header(f"Day {selected_day_workout['day']} Workout Plan")

    for exercise in selected_day_workout["workouts"]:
        st.subheader(exercise)

        # Show previous logs for the exercise
        previous_logs = [
            log for day, logs in user_data["workout_logs"][username].items()
            if int(day) < current_day for log in logs if log["exercise"] == exercise
        ]
        if previous_logs:
            last_log = previous_logs[-1]
            st.write(f"Previous: {last_log['weight']} lbs x {last_log['reps']} reps on {last_log['date']}")

        # Input fields for reps and weight
        weight = st.number_input(f"Weight for {exercise} (lbs):", min_value=0.0, step=1.0, key=f"weight_{exercise}_{current_day}")
        reps = st.number_input(f"Reps for {exercise}:", min_value=0, step=1, key=f"reps_{exercise}_{current_day}")

        # Save log button
        if st.button(f"Log {exercise}", key=f"log_{exercise}_{current_day}"):

            if str(current_day) not in user_data["workout_logs"][username]:
                user_data["workout_logs"][username][str(current_day)] = []
            user_data["workout_logs"][username][str(current_day)].append({
                "exercise": exercise,
                "weight": weight,
                "reps": reps,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_user_data(user_data)

            # Earn EXP by logging exercise
            user_data["exp"][username] += 10
            save_user_data(user_data)
            st.success(f"Logged {exercise}: {weight} lbs x {reps} reps. Gained 10 EXP!")

    # Display logged exercises for the current day
    st.subheader(f"Logged Exercises for Day {current_day}")
    if str(current_day) in user_data["workout_logs"][username]:
        for log in user_data["workout_logs"][username][str(current_day)]:
            st.text(f"{log['date']} - {log['exercise']}: {log['weight']} lbs x {log['reps']} reps")
    else:
        st.info("No exercises logged yet for this day.")

    # Track Daily Intake
    st.header("Track Your Daily Intake")

    # Water Intake
    st.subheader("Water Intake")
    water_goal = st.number_input("Set your water intake goal (liters):", min_value=0.0, step=0.01, value=2.0, key="water_goal")
    water_intake = st.number_input("Enter water intake (liters):", min_value=0.0, step=0.01, key="water_intake")
    if st.button("Log Water Intake"):
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in user_data["water_logs"][username]:
            user_data["water_logs"][username][today] = 0
        user_data["water_logs"][username][today] += water_intake * 33.814  # Save in oz
        save_user_data(user_data)
        if water_intake >= water_goal:
            st.success("You have reached your water goal for the day!")
        else:
            deficit = water_goal - water_intake
            st.warning(f"You are under your water intake. You need to drink more: {deficit:.2f} liters remaining.")

    # Calorie Intake
    st.subheader("Calorie Intake")
    calorie_goal = st.number_input("Set your calorie intake goal:", min_value=0, step=100, value=2500, key="calorie_goal")
    calorie_intake = st.number_input("Enter calorie intake (cal):", min_value=0, step=1, key="calorie_intake")
    if st.button("Log Calorie Intake"):
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in user_data["calorie_logs"][username]:
            user_data["calorie_logs"][username][today] = 0
        user_data["calorie_logs"][username][today] += calorie_intake
        save_user_data(user_data)
        
        if calorie_intake < calorie_goal:
            deficit = calorie_goal - calorie_intake
            st.warning(f"You are under your calorie intake. You need to consume more: {deficit} calories remaining.")
        elif calorie_intake > calorie_goal:
            excess = calorie_intake - calorie_goal
            st.warning(f"You are over your calorie intake by {excess} calories. Try again tomorrow.")
        else:
            st.success("You have reached your calorie goal for the day!")

    # EXP and Level System
    st.header("Your Level and Experience")

    current_exp = user_data["exp"][username]
    level = int(current_exp // 100)  # Assuming level up at every 100 EXP
    next_level_exp = (level + 1) * 100

    st.write(f"Current Level: {level}")
    st.write(f"EXP: {current_exp}")
    st.write(f"EXP until next level: {next_level_exp - current_exp}")

