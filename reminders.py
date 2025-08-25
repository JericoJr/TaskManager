from flask_mail import Message, Mail                   # Import Email Support
from datetime import datetime, timedelta, timezone, date     # Import date/time utilities
from app import db, app, mail, Task, User               # Import app components and database models
from flask_apscheduler import APScheduler               # Import scheduler for periodic jobs
from sqlalchemy import extract, func, case

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
def task_reminders_tomorow():
    with app.app_context():  # Create application context to access DB and Flask extensions
        now = datetime.now()  # Returns timezone-aware UTC datetime
        
        # Define a small window around 24 hours from now
        # This allows catching tasks with deadline about 24 hours away
        reminder_window_start = now + timedelta(hours=23, minutes=59)
        reminder_window_end = now + timedelta(hours=24, minutes=1)

        # Query tasks:
        # - Status is 'In-Progress' (not completed)
        # - Deadline falls within the reminder window (approx 24 hours from now)
        tasks = Task.query.filter(
            Task.status == 'In-Progress',
            Task.deadline >= reminder_window_start,
            Task.deadline <= reminder_window_end
        ).all()

        # Loop through all matching tasks
        for task in tasks:
            # Fetch the user who owns the task
            user = User.query.get(task.user_id)

            if user.email_notifications: # Checks if user set email notifications to on
                # Prepare the reminder email message
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title}",
                    recipients=[user.email],  # Send to user's email
                    body=f"Your task '{task.title}' is due tomorow {task.deadline.strftime('%B %d %Y @ %I:%M %p')}."
                )
                print(f"Sending email to {user.email} for task {task.title}")
                # Send the email via Flask-Mail
                mail.send(msg)

def task_reminder_today():
    with app.app_context():  # Create application context to access DB and Flask extensions
        today = date.today() # format MM/DD/YYYY
        today_tasks = Task.query.filter( # Gets a list of all tasks that are not completed and due today
            Task.status == 'In-Progress',
            extract('year', Task.deadline) == today.year,
            extract('month', Task.deadline) == today.month,
            extract('day', Task.deadline) == today.day
        ).all()

        # Loops through all tasks that are due today, and sends email to users' email according to their id
        for task in today_tasks:
            user_id = task.user_id # Get the user_id associated with the task
            user = User.query.get(user_id) # Get User from User Database using their ID

            if user.email_notifications: # Checks if user set email notifications to on
                email = user.email
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title}",
                    recipients=[email],  # Send to user's email
                    body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                )
                # Send the email via Flask-Mail
                mail.send(msg)
                

if __name__ == "__main__":
    task_reminders_tomorow()     
    task_reminder_today()                            
