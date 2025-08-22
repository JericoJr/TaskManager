from flask_mail import Message                         # Import Message class to construct emails
from datetime import datetime, timedelta, timezone     # Import date/time utilities
from app import db, app, mail, Task, User               # Import app components and database models
from flask_apscheduler import APScheduler               # Import scheduler for periodic jobs
import time
from flask import jsonify

scheduler = APScheduler()                               # Create a scheduler instance

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

def start_scheduler():
    scheduler.init_app(app)                                # Initialize scheduler with Flask app context
    scheduler.start()                                      # Start the scheduler running
    # Schedule task_reminders to run every hour by interval trigger
    scheduler.add_job(func=task_reminders, trigger='interval', id='send_reminders', hours=1)


# Define a route /send_reminders that accepts GET requests
@app.route('/send_reminders', methods=['GET'])
def send_reminders():
    # Returns a JSON response indicating success or error.
    try:
        # Call your existing function to check tasks and send reminder emails
        task_reminders()
        
        # If successful, return a JSON response with status and message
        return jsonify({"status": "success", "message": "Reminders sent"}), 200
    
    except Exception as e:
        # If any error occurs, catch it and return JSON with error info
        return jsonify({"status": "error", "message": str(e)}), 500



# Run this block only if this script is executed directly (not imported)
if __name__ == "__main__":
    with app.app_context():
        task_reminders()                                   # Run reminders once immediately (for testing)
    start_scheduler()                                      # Then start the periodic scheduler
