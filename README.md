# Task Manager Web App

A modern Task Manager Web Application built with Flask, Python, HTML, CSS, Jinja, and JavaScript.

This project helps users create, edit, organize, and track tasks efficiently through a task table that stores key details such as the title, description, deadline, priority, and status. Tasks can be sorted and filtered by date, priority, status, or other fields, making it easier to manage both short- and long-term goals.

To keep users on track, the app supports automated email reminders scheduled with GitHub Actions (cron workflow):

-9 AM UTC (5 AM EDT) → Sends reminders for tasks due today

-12 AM UTC (8 PM EDT) → Sends reminders for tasks due tomorrow

All user accounts and tasks are stored locally in an SQLite database. Users can register with their email and password, and multiple accounts are supported—ensuring each user’s tasks remain securely linked to their profile.

For better visualization, the app includes a real-time calendar that dynamically updates with task deadlines, allowing users to view tasks by day, week, or month and drill down into specific dates.

---

## 🚀 Features
- 🔐 **User Authentication** – Register, log in, and manage personal tasks.
- 🗂️ **Task Management** – Create, edit, delete, and mark tasks as completed or in-progress.
- ⚡ **Prioritization & Filtering** – Organize and filter tasks within tasks table by priority (low, medium, high), status, deadlines, or creation date.
- 📬 **Email Notifications** – For new user signup and forgot-password including optional email task deadline reminders.
- 📅 **Real-time Calendar** – Visualize task deadlines by the day, week, and month.
- 📊 **Progress Tracking** – Includes a progress bar, statistics table, and summary of urgent tasks.
- ⏰ **Reminders** – Highlight the top 3 important tasks due today or next following tasks by their deadline.

---

## 🛠️ Tech Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Jinja2
- **Database**: SQLite (default)  

---

## Getting Started

Follow these steps to get the project up and running locally:

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/task_manager.git
   cd task_manager

3. **Create Virtual Environment (Recommended)**
    i. "-"python -m venv venv"
	ii. Activate: "venv\Scripts\activate""

2. **Install Dependencies**
    i. "pip install -r requirements.txt"

3. **Run Flask App**
    i. "python app.py"
    ii. Access App by clicking on this link: "http://127.0.0.1:5000" (Click on using CTRL)

---

## Important Notes
- This project uses a local SQLite database (`taskmanager.db`) to store tasks and user data.  
- Since GitHub Actions runs on the repository version of the database, **you must commit and push the database file whenever you add or update tasks and users** to ensure reminders for GitHub Actions work correctly.  
- Example workflow:
  ```bash
  git add instance/taskmanager.db
  git commit -m "Update tasks"
  git push


