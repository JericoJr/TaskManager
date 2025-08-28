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

def task_reminder_hour():
    with app.app_context():  # Create application context to access DB and Flask extensions
        today_tasks = Task.query.filter(Task.status == 'In-Progress').all()
        print(f"TASKS COLLECTED: {len(today_tasks)}")

        for task in today_tasks:
            user = User.query.get(task.user_id) # Get User Object of given task
            user_tz = ZoneInfo(user.timezone) # Get User's timezone

            # Current local date for the user
            user_today = datetime.now(timezone.utc).astimezone(user_tz).date()

            # Convert given task deadline into user's tz
            if task.deadline.tzinfo is None:
                    # Assume UTC if naive
                    task_deadline = task.deadline.replace(tzinfo=timezone.utc).astimezone(user_tz)
            else:
                task_deadline = task.deadline.astimezone(user_tz)

            # Checks if current task deadline is today in user's timezone
            if task_deadline.date() == user_today:
                # Now check if due within the next hour
                time_left = task_deadline - datetime.now(timezone.utc).astimezone(user_tz)
   
                # If time_left is <= 1 hour then send email
                if timedelta(0) <= time_left <= timedelta(hours=1):
                    print(f"Found task: {task.title} deadline={task.deadline} user={task.user_id} time={time_left}")

                    email = user.email

                    if user.email_notifications and task.set_today_reminder != False: # Checks if user set email notifications to on and that email has not already been sent
                        task.set_today_reminder = False
                        db.session.commit()

                        msg = Message(
                            subject=f"⏰ Task Reminder: {task.title} Due in Less than an Hour",
                            recipients=[email],  # Send to user's email
                            body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}.\n\n"
                            f"Description: {task.description}" 
                        )
                        # Send the email via Flask-Mail
                        mail.send(msg)
                
if __name__ == "__main__":
    task_reminder_hour()                            
