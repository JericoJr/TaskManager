from flask_mail import Message, Mail                   # Import Email Support
from datetime import datetime, timedelta, timezone, date, time     # Import date/time utilities
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
def task_reminders_tomorrow():
    with app.app_context():  # Create application context to access DB and Flask extensions
        now = datetime.utcnow()  
        
        tomorrow = (now + timedelta(days=1)) # Adds current day by 1 day to get tomorrow's date

        tasks = Task.query.filter(
            Task.status == 'In-Progress',
            Task.deadline >= now,
            Task.deadline <= tomorrow,
        ).all()

        # Loop through all matching tasks
        for task in tasks:
            print(f"Found task: {task.title} | Deadline: {task.deadline}")
            time_until_deadline = task.deadline - now # Get leftover time

            # Fetch the user who owns the task
            user = User.query.get(task.user_id)

            if user.email_notifications and (timedelta(hours=22) <= time_until_deadline <= timedelta(hours=24)): # Checks if user set email notifications to on and that email reminder has not been set
                # Prepare the reminder email message
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title} Due Tomorrow",
                    recipients=[user.email],  # Send to user's email
                    body=f"Your task '{task.title}' is due tomorrow {task.deadline.strftime('%B %d %Y @ %I:%M %p')}."
                    f"Description: {task.description}"
                )
                print(f"Sending email to {user.email} for task {task.title}")
                # Send the email via Flask-Mail
                mail.send(msg)
        

def task_reminder_today():
    with app.app_context():  # Create application context to access DB and Flask extensions
        today = datetime.utcnow().date()
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

            if user.email_notifications: # Checks if user set email notifications to on and that email has not already been sent
                now = datetime.utcnow()
                curr_time = now.time() # Gets current time as time object
                email = user.email # Gets user's email from User Database
                # 1st Reminder
                if time(0,0) <= curr_time <= time(1,0): # Checks if current time is between 12am to 1am
                    msg = Message(
                        subject=f"⏰ Task Reminder: {task.title} Due Today",
                        recipients=[email],  # Send to user's email
                        body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                        f"Description: {task.description}" 
                    )
                    # Send the email via Flask-Mail
                    mail.send(msg)
                # 2nd Reminder
                if (time(5,0) <= curr_time <= time(6,0)): # Checks if current time is between 5am and 6am
                    time_left = task.deadline - now
                    if task.deadline.time() >= time(6,0) and time_left > timedelta(hours=1): # Checks if task's deadline is past 6am and there is more than a hour until task is due
                        msg = Message(
                            subject=f"⏰ Task Reminder: {task.title} Due Sometime Today",
                            recipients=[email],  # Send to user's email
                            body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                            f"Description: {task.description}" 
                        )
                        # Send the email via Flask-Mail
                        mail.send(msg)

                # 3rd Reminder
                time_left = task.deadline - now
                if (timedelta(minutes=0) < time_left <= timedelta(minutes=60)): # Checks if current time is 1 hour before or less than task's deadline
                    msg = Message(
                        subject=f"⏰ Task Reminder: {task.title} Due Soon",
                        recipients=[email],  # Send to user's email
                        body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                        f"Description: {task.description}" 
                    )
                    # Send the email via Flask-Mail
                    mail.send(msg)
                
                print(f"Deadline: {task.deadline}, Type: {type(task.deadline)}")
                print("Is task.deadline timezone aware?", task.deadline.tzinfo is not None and task.deadline.tzinfo.utcoffset(task.deadline) is not None)

                now = datetime.now()
                print(f"Now: {now}, Type: {type(now)}")
                print("Is datetime.now() timezone aware?", now.tzinfo is not None and now.tzinfo.utcoffset(now) is not None)
                
                

                

if __name__ == "__main__":
    task_reminders_tomorrow()     
    task_reminder_today()                            
