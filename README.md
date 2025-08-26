# Task Manager Web App

A simple Task Manager web application built using Flask, Python, HTML, CSS, Jinja, and JavaScript. This project demonstrates basic web app functionality, including routing, templates, and features like kuser logins, email notifications, task scheduling.

---

## Features

- Flask-based backend with routing and templating
- Task management functionality: Ability to create, schedule, edit, and delete tasks
- Ability to organize and priotize Tasks by levels from low, medium, and high and check if they are completed or in-progress
- Ability to filter out tasks in the tasks table according to its categories by their date, deadline, status, priority, date of         creation, and etc.
- Email notifications for new user signup and optional task deadline using Flask-Mail
- Real-time Calendar with up-to date tasks's deadline
- Includes a progress bar and statistics table to track task info and usage
- Includes a summary section and reminders lists to showcase important tasks that are due for the user today or within that week


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

