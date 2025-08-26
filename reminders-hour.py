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

def task_reminder_thour():
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
            email = user.email

            if user.email_notifications and task.set_today_reminder != False: # Checks if user set email notifications to on and that email has not already been sent
                task.set_today_reminder = False
                db.session.commit()
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title} Due Today",
                    recipients=[email],  # Send to user's email
                    body=f"Your task '{task.title}' is due today at {task.deadline.strftime('%I:%M %p')}."
                    f"Description: {task.description}" 
                )
                # Send the email via Flask-Mail
                mail.send(msg)
                
if __name__ == "__main__":
    task_reminder_hour()                            
