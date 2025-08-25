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
        now = datetime.now()  
        
        tomorrow = (now + timedelta(days=1)).date() # Adds current day by 1 day to get tomorrow's date

        # # Gives an 1 hour window to check task's time. exa. task due @ 3pm tomorrow, checks for task between 3pm - 4pm
        # Start of tomorrow and its time, exa. 3pm 
        window_start = datetime.combine(tomorrow, time.min)
        # End of 1st hour after window start, exa. 4pm,
        window_end = datetime.combine(tomorrow, time.max) 

        tasks = Task.query.filter(
            Task.status == 'In-Progress',
            Task.deadline >= window_start,
            Task.deadline <= window_end,
            Task.set_tomorrow_reminder == True
        ).all()

        # Loop through all matching tasks
        for task in tasks:
            # Fetch the user who owns the task
            user = User.query.get(task.user_id)

            if user.email_notifications: # Checks if user set email notifications to on and that email reminder has not been set
                task.set_tomorrow_reminder = False # Set to False to indicate the email reminder for tomorrow has been sent once
                db.session.commit() # Saves any new changes to database

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
        today = date.today() # format MM/DD/YYYY
        today_tasks = Task.query.filter( # Gets a list of all tasks that are not completed and due today
            Task.status == 'In-Progress',
            extract('year', Task.deadline) == today.year,
            extract('month', Task.deadline) == today.month,
            extract('day', Task.deadline) == today.day,
            Task.set_today_reminder == True
        ).all()

        # Loops through all tasks that are due today, and sends email to users' email according to their id
        for task in today_tasks:
            user_id = task.user_id # Get the user_id associated with the task
            user = User.query.get(user_id) # Get User from User Database using their ID

            if user.email_notifications: # Checks if user set email notifications to on and that email has not already been sent
                task.set_today_reminder = False
                db.session.commit() # Saves any new changes to database

                email = user.email # Gets user's email from User Database
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title} Due Today",
                    recipients=[email],  # Send to user's email
                    body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                    f"Description: {task.description}" 
                )
                # Send the email via Flask-Mail
                mail.send(msg)

                

if __name__ == "__main__":
    task_reminders_tomorrow()     
    task_reminder_today()                            
