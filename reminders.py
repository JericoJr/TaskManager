from flask_mail import Message
from datetime import datetime, timedelta, timezone
from app import db, app, mail, Task, User

# Create a 24-hour reminder email notification for users' task
def task_reminders():
    with app.app_context():  # Create application context to access DB and Flask extensions
        now = datetime.now(timezone.utc)  # Returns timezone-aware UTC datetime
        
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

            # Check if user exists and has an email
            if user and user.email:
                # Prepare the reminder email message
                msg = Message(
                    subject=f"⏰ Task Reminder: {task.title}",
                    recipients=[user.email],  # Send to user's email
                    body=f"Your task '{task.title}' is due on {task.deadline.strftime('%B %d %Y @ %I:%M %p')}."
                )
                # Send the email via Flask-Mail
                mail.send(msg)


# This block runs the reminders only if this script is executed directly (not imported)
if __name__ == "__main__":
    with app.app_context():
        task_reminders() # functions checks task database for any upcoming deadlines, and sends email
