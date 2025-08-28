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
        today_tasks = Task.query.filter(
            Task.status == 'In-Progress'
        ).all()
        print(f"TASKS COLLECTED: {len(today_tasks)}")

        for task in today_tasks:
            print(f"Found task: {task.title} deadline={task.deadline} deadline_format={task.deadline.strftime('%B %d %Y @ %I:%M %p')} user={task.user_id}")
            user = User.query.get(task.user_id) # Get User Object of given task
            user_tz = ZoneInfo(user.timezone) # Get User's timezone

            # Current local date for the user
            user_today = datetime.now(timezone.utc).astimezone(user_tz).date()


            print(f"curr-day: {user_today} curr-day_format: {user_today.strftime('%B %d %Y')}")
            # Checks if current task deadline is today in user's timezone
            if task.deadline.date() == user_today:
                print(f"Matched today's task: {task.title} deadline={task.deadline} deadline_format={task.deadline.strftime('%B %d %Y @ %I:%M %p')} user={task.user_id}")
                if task.deadline.tzinfo is None:  # Naive → assume it's in UTC
                    task_deadline_local = task.deadline.replace(tzinfo=timezone.utc)
                else:
                    task_deadline_local = task.deadline

                # current_time = datetime.now(user_tz)
                print(f"task_deadline: {task_deadline_local}; current_time: {datetime.now(timezone.utc).astimezone(user_tz)}")
                # Now check if due within the next hour
                time_hour_left = task_deadline_local.hour - datetime.now(user_tz).hour
                time_min_left = task_deadline_local.minute - datetime.now(user_tz).minute

                time_left_total_minutes = (time_hour_left * 60) + time_min_left

                # time_left = task_deadline_local - current_time
                # time_left_total_minutes = int(time_left.total_seconds() / 60)
                print(f"Time left: {time_left_total_minutes}")
                # If time_left is <= 1 hour or between 0 to 60 minutes then send email
                if 0 <= time_left_total_minutes<= 60:
                    print(f"Matched 1-hour task: {task.title} deadline={task.deadline} user={task.user_id} time={time_left_total_minutes}")

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
