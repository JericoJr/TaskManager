from flask_mail import Message, Mail                   # Import Email Support
from datetime import datetime, timedelta, timezone, date, time     # Import date/time utilities
from app import db, app, mail, Task, User               # Import app components and database models
from flask_apscheduler import APScheduler               # Import scheduler for periodic jobs
from sqlalchemy import extract, func, case
from zoneinfo import ZoneInfo

import os

# Email config (for GitHub Actions environment)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Set in GitHub Actions
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Set in GitHub Actions
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# Create a 24-hour reminder email notification for users' task
def task_reminders_tomorrow():
    with app.app_context():  # Create application context to access DB and Flask extensions
        tasks = Task.query.filter(
            Task.status == 'In-Progress'
        ).all()
        print(f"TASKS COLLECTED: {len(tasks)}")

        for task in tasks:
            print(f"Found task: {task.title} deadline={task.deadline} deadline_format={task.deadline.strftime('%B %d %Y @ %I:%M %p')} user={task.user_id}")
            user = User.query.get(task.user_id) # Get User Object of given task
            user_tz = ZoneInfo(user.timezone) # Get User's timezone

            # Current local date of tomorrow for the user
            user_tomorrow = datetime.now(timezone.utc).astimezone(user_tz).date() + timedelta(days=1)
            print(f"tomorrow-day: {user_tomorrow}")
            # Checks if current task deadline is tomorrow in user's timezone
            if task.deadline.date() == user_tomorrow:
                print(f"Matched today's task: {task.title} deadline={task.deadline} deadline_format={task.deadline.strftime('%B %d %Y @ %I:%M %p')} user={task.user_id}")

                user_id = task.user_id # Get the user_id associated with the task
                user = User.query.get(user_id) # Get User from User Database using their ID
                email = user.email

                if user.email_notifications: # Checks if user set email notifications to on
                    # Prepare the reminder email message
                    msg = Message(
                        subject=f"⏰ Task Reminder: {task.title} Due Tomorrow",
                        recipients=[email],  # Send to user's email
                        body=f"Your task '{task.title}' is due tomorrow {task.deadline.strftime('%B %d %Y @ %I:%M %p')}.\n\n"
                        f"Description: {task.description}"
                    )
                    print(f"Sending email to {user.email} for task {task.title}")
                    # Send the email via Flask-Mail
                    mail.send(msg)
    
                

if __name__ == "__main__":
    task_reminders_tomorrow()     
