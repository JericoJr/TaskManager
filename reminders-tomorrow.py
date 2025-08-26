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
            extract('year', Task.deadline) == tomorrow.year,
            extract('month', Task.deadline) == tomorrow.month,
            extract('day', Task.deadline) == tomorrow.day
        ).all()

        # Loop through all matching tasks
        for task in tasks:
            # Fetch the user who owns the task
            user = User.query.get(task.user_id)

            if user.email_notifications and task.set_tomorrow_reminder != False: # Checks if user set email notifications to on 
                task.set_tomorrow_reminder = False
                db.session.commit()
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
    
                

if __name__ == "__main__":
    task_reminders_tomorrow()     
