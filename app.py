# import for random numbers
import random

import os
import calendar

from datetime import datetime, timedelta, date, timezone
from sqlalchemy import extract, func, case


# Import necessary Flask classes and functions to build the web app
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Import SQLAlchemy extension for database management
from flask_sqlalchemy import SQLAlchemy

# Import functions to securely hash passwords and check them
from werkzeug.security import generate_password_hash, check_password_hash

# Import email notifications
from flask_mail import Mail, Message

from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import pytz


# Create Flask app and set instance_relative_config to True so we can use the instance folder
app = Flask(__name__, instance_relative_config=True)
# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Secret key is needed to keep client sessions secure
app.secret_key = os.environ.get('SECRET_KEY') # 'SECRET_KEY' is the name of the environment variable you want to read, the next parameter is the actual secret key value

# Get the absolute path of the directory where the current file is located (e.g., app.py or reminders.py)
basedir = os.path.abspath(os.path.dirname(__file__))

# Define the full path to the 'instance' folder within the project
instance_path = os.path.join(basedir, 'instance')

# Ensure the instance folder exists (create it if not)
os.makedirs(instance_path, exist_ok=True)

# Build the full path to the SQLite database file inside the instance folder
db_path = os.path.join(instance_path, 'taskmanager.db')

# Configure SQLAlchemy to use SQLite with the absolute path to the database file
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'


load_dotenv()  # This loads the .env file and sets environment variables

# Email configuration (for example, using Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')      # Replace with website email (this will be the sender)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')    # Use an App Password (not your real Gmail password)
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# print("MAIL_USERNAME:", os.environ.get('MAIL_USERNAME'))
# print("MAIL_PASSWORD:", os.environ.get('MAIL_PASSWORD'))

# Scheduler config
app.config['SCHEDULER_API_ENABLED'] = True

# Initialize Flask-Mail
mail = Mail(app)

# Initialize SQLAlchemy with the Flask app, to handle database operations
db = SQLAlchemy(app)

# Define a User model representing users table in the database
class User(db.Model):
    # Primary key: unique id for each user
    id = db.Column(db.Integer, primary_key=True)
    
    # User's name, required field, default is 'User' if not provided
    username = db.Column(db.String(100), nullable=False, default='User')
    
    # User's first & last name
    first = db.Column(db.String(100), nullable=False)
    last = db.Column(db.String(100), nullable=False)

    # User's email, must be unique and cannot be null
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Stores email notifications, holds true or false, true is default
    email_notifications = db.Column(db.Boolean, nullable=False, default=True)
    
    # Stores hashed password (never store plaintext passwords!)
    password_hash = db.Column(db.String(128))

    # Stores User current Timezone
    timezone = db.Column(db.String, default="UTC")  # e.g., "America/New_York"

    # Method to set password: converts plain password to a secure hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check password: compares entered password with stored hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define a Task Model representing tasks table in the database
class Task(db.Model):
    # Primary key: unique id for each task, automatically assigned when task is created
    id = db.Column(db.Integer, primary_key=True)

    # Stores title of task
    title = db.Column(db.String(128), nullable=False)

    # Stores description of text, db.Text is a text field that can store large amounts of text
    description = db.Column(db.Text, nullable=True)

    # Stores level of priority for the task
    priority = db.Column(db.String(50), nullable=False)

    # Stores deadline for task with timezone info like UTC, EDT, nullable = true means it can be empty; Note: each month, day, and year would be integers
    deadline = db.Column(db.DateTime(timezone=True), nullable=True)

    # Stores status of task like complete and in-progress where in-progess is default.
    status = db.Column(db.String(50), nullable=False, default='In-Progress')

    # Stores reminder of task, if email notifications are on set today and tomorrow reminders to True as default
    set_today_reminder = db.Column(db.Boolean, nullable=False, default=True)
    set_tomorrow_reminder = db.Column(db.Boolean, nullable=False, default=True)

    # This line creates a column in the Task table called 'user_id'.
    # It stores an INTEGER that represents the ID of the user who owns this task.
    # The 'ForeignKey' tells SQLAlchemy that this column must match a value in the 'id' column of the 'user' table.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # This line sets up a relationship in SQLAlchemy between Task and User models.
    # - 'User' is the name of the model (class) you're linking to.
    # - 'backref' creates a virtual column/attribute on the User model called 'tasks'.
    #     So from a user instance, you can access their tasks via 'user.tasks'.
    # - 'lazy=True' means the tasks are loaded only when accessed (not loaded automatically when user is queried).
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))

    
# Define route for root URL '/', where code starts
# When users visit '/', redirect them to the login page '/login'
@app.route("/")
def root():
    return redirect(url_for('login'))

# Define route for '/signup' page, handles GET and POST requests
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get email, username, first name, last name, and password from the form submission by their input name
        email = request.form['email']
        username = request.form['username']
        first = request.form['first']
        last = request.form['last']
        password = request.form['password']
        timezone = request.form['timezone']

        # Check if a user with this email already exists
        if User.query.filter_by(email=email).first(): # Query the User table for a record with the matching email and return the first match or None if no user exists
            flash('Email already exists. Please log in.', 'error')
            return redirect(url_for('signup'))  # Redirect back to signup page if duplicate

        # Create a new User instance with email, username and set the password hash
        new_user = User(email=email, username=username) # Note: email(database column) = email(local variable)
        new_user.set_password(password)
        # Also assign first, and last names to User model properties
        new_user.first = first
        new_user.last = last

        # Sets default email notfications as true 
        new_user.email_notifications = True

        # Sets user's timezone
        new_user.timezone = timezone

        # Add the new user to the database session and commit(save) changes
        db.session.add(new_user)
        db.session.commit()

        # Send a Welcome email to User
        msg = Message("Welcome to Task Manager", recipients=[email], sender=app.config['MAIL_DEFAULT_SENDER'])
        msg.body = f"Thank you {first}, for signing up and using our app!" #format string represented by f"", where the content in {} is the placeholder
        mail.send(msg)

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login page after signup

    # If GET request, simply render the signup form
    return render_template('signup.html')

# Define route for '/generate_code
@app.route('/generate_code', methods=['POST'])
def generate_code():
    email = request.form['email'] # Gets the user's email from the given form
    session['email'] = email # Temporarily stores user's email within session

     # Check if a user with this email already exists
    if User.query.filter_by(email=email).first(): # Query the User table for a record with the matching email and return the first match or None if no user exists
        targetCode = random.randint(1000, 9999) # Generates a random number between 1000 and 9999 (inclusive)
        session['target_code'] = targetCode # Temporarily stores target code within session

        # Send a forgot email to User with random generated 4 digit-code
        msg = Message("Task Manager - Forgot Password:", recipients=[email], sender=app.config['MAIL_DEFAULT_SENDER'])
        msg.body = f"Here is your code: {targetCode}" #format string represented by f"", where the content in {} is the placeholder
        mail.send(msg)
        flash('Code sent to email, check your inbox', 'success')
    else:
        flash('Email does not exist. Please signup.', 'error')

    return redirect(url_for('forgot_password'))  

# Define route for '/check_code
@app.route('/check_code', methods=['POST'])
def check_code():
    inputCode = int(request.form['code']) # Gets the user's input code, converts to integer
    targetCode = session.get('target_code') # Gets random generated code from session
    # Checks if user's code matches the target code
    if inputCode == targetCode:
        session['code_verified'] = True # Stores an indicator that code was successful
        flash('Correct Code', 'success')
    else:
        session['code_verified'] = False
        flash('Incorrect Code', 'error') # Stores an indicator that code was unsuccessful
    
    return redirect(url_for('forgot_password')) 

# Define route for '/forgot_password'
@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    # For POST requests, generate random code to users and send to users. Once code is correct then change to new password
    if request.method == 'POST':
        email = session.get('email') # Gets user's email from session
        user = User.query.filter_by(email=email).first() # Finds user within database using their email

        password = request.form['password'] # get new password from form input

        # Set new password for user
        user.set_password(password)

        # Saves info    
        db.session.commit()

        # Remove email and code from session after successful reset, None ensures it doesn't raise an error if key doesn't exist
        session.pop('email', None)
        session.pop('target_code', None)

        flash('Password Changed! Please log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login page after signup
    
    # If GET request, render the form and pass code_verified flag from session to template
    return render_template('forgot-pass.html', code_verified=session.get('code_verified', False)) #code_verified holds a boolean and by default holds False


# Define route for '/login' page, handles GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get submitted email and password from login form
        email = request.form['email']
        password = request.form['password']

        # Look up user in database by email
        user = User.query.filter_by(email=email).first()

        # if user not found 
        if not user:
            flash('Account not found. Please sign up.', 'error')
            return redirect(url_for('login'))
        # If user exists and password is correct
        if user and user.check_password(password):
            # Store user's id in session to keep them logged in
            session['user_id'] = user.id
            return redirect(url_for('home'))  # Redirect to home page after login
        else:
            # If login failed, show error message and reload login page
            flash('Invalid email or password!','error')
            return redirect(url_for('login'))

    # For GET requests, just render the login page
    return render_template('login.html')

#-------------Home------------------------

# Define route for '/home' page - a protected page requiring login
@app.route('/home')
def home():
    # Check if user is logged in by looking for 'user_id' in session
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id'] # Grab the current logged-in user's ID from the session
    user = User.query.get(user_id)  # Used user_id to get the user object from database

    # Get current or selected month/year
    today = datetime.today()
    # Get the 'month' and 'year' value from the URL query parameters (e.g., /home?month=9, /home?year=2025)
    # If 'month' or 'year' is not provided in the URL, use the current month and year from today's date
    # 'type=int' converts the value to an integer
    month = request.args.get('month', default=today.month, type=int)
    year = request.args.get('year', default=today.year, type=int)

    # Generate calendar grid
    cal = calendar.Calendar(firstweekday=6)  # Create a calendar instance with weeks starting on Sunday (0=Monday, 6=Sunday)
    # Generate the full calendar grid for the selected month and year
    # Returns a list of weeks, where each week is a list of 7 integers
    # Each integer is a day number or 0 (if that slot is outside the month)
    # Example for August 2025:
    # [
    #   [0, 0, 0, 0, 1, 2, 3],
    #   [4, 5, 6, 7, 8, 9, 10],
    #   ...
    # ]
    month_days = cal.monthdayscalendar(year, month) # month_days is a 2D array list where rows are weeks and columns are days
    month_name = calendar.month_name[month] # Gets month as a string

    tasks_list = Task.query.filter( # MUST use .filter() for extract
        extract('month', Task.deadline) == month, # extracts the task that matches the variables month and year
        extract('year',Task.deadline) == year
    ).all() # Within Task database, filter all task with the same month and year and put it into list

    # Gets total count of tasks and count of completed tasks, used for progress bar
    tasks_count = Task.query.filter_by(user_id=user_id).count()
    tasks_complete_count = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'Complete'
    ).count()

    # Gets rest of values for stats
    high_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'High'
    ).count()

    medium_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'Medium'
    ).count()    

    low_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'Low'
    ).count()

    high_tasks_completed = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'High',
        Task.status == 'Complete'
    ).count()

    medium_tasks_completed = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'Medium',
        Task.status == 'Complete'
    ).count()    

    low_tasks_completed = Task.query.filter(
        Task.user_id == user_id,
        Task.priority == 'Low',
        Task.status == 'Complete'
    ).count()

    tasks_in_month = Task.query.filter(
        Task.user_id == user_id,
        extract('month', Task.deadline) == month # extracts the month from deadline
    ).count()

    completed_tasks_in_month = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'Complete',
        extract('month', Task.deadline) == month # extracts the month from deadline, checks if task's month equals today's month
    ).count()

    tasks_due_today = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'In-Progress',
        extract('month', Task.deadline) == today.month,
        extract('day', Task.deadline) == today.day,
        extract('year', Task.deadline) == today.year
    ).count()

    today = datetime.today().date() # force today to be a date object without time
    # Calculate the start and end of the current week (Monday to Sunday) of today's date; variables store date objects
    start_of_week = today - timedelta(days=today.weekday())        # Monday - today.weekday() calculates days passed since Mon. and subtracts by current day
    end_of_week = start_of_week + timedelta(days=6)                # Sunday - Adds 6 days to start of week

    tasks_due_week = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'In-Progress',
        func.date(Task.deadline) >= start_of_week, # func.date() gets the date portion and compares it tp the start_of_week date object
        func.date(Task.deadline) <= end_of_week,
        extract('year', Task.deadline) == today.year
    ).all()

    tasks_overdue = Task.query.filter(
        Task.user_id == user_id,
        Task.status == 'In-Progress',
        extract('month', Task.deadline) == today.month,
        extract('day', Task.deadline) < today.day,
        extract('year', Task.deadline) == today.year
    ).count()

    reminderTasks = reminderTasksList()

    # Render the home page template if logged in, while passing user and calendar values
    return render_template('home.html', user=user, month=month, year=year, month_name=month_name, month_days=month_days, 
        today=today, tasks_list=tasks_list, tasks_count=tasks_count, tasks_complete_count=tasks_complete_count, high_tasks=high_tasks,
        medium_tasks=medium_tasks, low_tasks=low_tasks, high_tasks_completed=high_tasks_completed, medium_tasks_completed=medium_tasks_completed,
        low_tasks_completed=low_tasks_completed, tasks_in_month=tasks_in_month, completed_tasks_in_month=completed_tasks_in_month, 
        tasks_due_today=tasks_due_today, tasks_due_week=tasks_due_week, tasks_overdue=tasks_overdue, reminderTasks=reminderTasks, timedelta=timedelta)

def reminderTasksList():
    user_id = session.get('user_id')
    today = date.today()
    top3 = [] # Holds a list of the top 3 tasks due
    allTasks = Task.query.filter_by(user_id=user_id).order_by(Task.deadline.asc()).all() # Filters tasks by user's id in database, and sort by deadline (earliest to latest)
    # Loops through tasks one by
    for task in allTasks:
        if len(top3) < 3:
            if task.status == 'In-Progress' and task.deadline.date() >= today:
                top3.append(task)
        else:
            break

    return top3


# Define route for '/prev_calendar' and passes the value month and year as integers
@app.route('/prev_month/<int:month>/<int:year>')
def prev_month(month, year):
    # Checks if 1st month or Jan., then move to December and previous year, otherwise move to previous month
    if month == 1:
        new_month = 12
        new_year = year - 1
    else:
        new_month = month - 1
        new_year = year

    # Redirects to 'home' route while passing new month and year into the URL
    return redirect(url_for('home', month=new_month, year=new_year))


# Define route for '/next_calendar' and passes the value month and year as integers
@app.route('/next_month/<int:month>/<int:year>')
def next_month(month, year):
    # Checks if 12th month or Dec., then move to Jan. and next year, otherwise move to next month
    if month == 12:
        new_month = 1
        new_year = year + 1
    else:
        new_month = month + 1
        new_year = year

    # Redirects to 'home' route while passing new month and year into the URL
    return redirect(url_for('home', month=new_month, year=new_year))

# Define route for '/change_date'
@app.route('/change_date', methods=['POST'])
def change_date():
    date_string = request.form['date'] # Gets the string date from form
    # Parse the string into a datetime object
    dt = datetime.strptime(date_string, '%Y-%m-%d')

    new_month = dt.month # gets the month
    new_year = dt.year # gets the year

    # Redirects to 'home' route while passing new month and year into the URL
    return redirect(url_for('home', month=new_month, year=new_year))

# Define route for '/view_more_tasks'
@app.route('/view_more_tasks/<deadline>')
def view_more_tasks(deadline):
    date = datetime.strptime(deadline, '%Y-%m-%d') # Convert deadline parameter from string into datetime object

    # Gets components from datetime object, each variable stores an integer
    month = date.month # exa. 1 -> January
    year = date.year
    day = date.day

    # Sets corresponding session and variables with correct values, will be used as filters for tasks() and display in tasks.html
    session['filter_months'] = [month] # Store month within a list
    session['filter_year'] = year
    session['filter_day'] = day

    return redirect(url_for('tasks'))
    

#------------Tasks-----------------------

# Define a route for '/tasks'
@app.route('/tasks')
def tasks():
    user_id = session['user_id']

    # Get sort values from session and assign to these variables, if no values return None as Default
    sort_title = session.get('sort_title')
    sort_type = session.get('sort_type') 

    # Get filter values from session, if no values set '[]' as empty list or None as default
    filter_priorities = session.get('filter_priorities', [])
    filter_status = session.get('filter_status', [])
    filter_months = session.get('filter_months', [])
    filter_year = session.get('filter_year', None)
    filter_day = session.get('filter_day', None)

    # Order the priorities from high to low
    priority_order_descending = case(
        (Task.priority == 'High', 1),
        (Task.priority == 'Medium', 2),
        (Task.priority == 'Low', 3),
    )

    # Order the priorities from low to high
    priority_order_ascending = case(
        (Task.priority == 'Low', 1),
        (Task.priority == 'Medium', 2),
        (Task.priority == 'High', 3),
    )

    # Order status from complete to in-progress
    status_order_complete = case(
        (Task.status == 'Complete', 1),
        (Task.status == 'In-Progress', 2)
    )

    # Order status from in-progress to complete
    status_order_in_progress = case(
        (Task.status == 'In-Progress', 1),
        (Task.status == 'Complete', 2)
    )

    # Start base query on user id
    query = Task.query.filter_by(user_id=user_id)

    # Checks if any filters are selected, changed query to include only elements with that filter or attribute, otherwise does nothing
    if filter_priorities: # Only true if not empty
        query = query.filter(Task.priority.in_(filter_priorities)) # Filter by checked priorities within given priority list
    if filter_status:
        query = query.filter(Task.status.in_(filter_status)) # Filter by checked status within given status list
    if filter_months:
        query = query.filter(extract('month', Task.deadline).in_(filter_months)) # Filter by checked months within given months list; extract(...) - returns month number from Task columns and matches to filter months list
    if filter_year:
        query = query.filter(extract('year', Task.deadline) == filter_year) # Filter by typed year; extracts year from deadline column in database
    if filter_day:
        query = query.filter(extract('day', Task.deadline) == filter_day) # Filter by typed day; extracts day from deadline column in database

    # If there is no sort, set user_id as default
    if sort_title:
        if sort_title == 'priority':
            if sort_type == 'descending':
                query = query.order_by(priority_order_descending) # Order priority from high to low
            elif sort_type == 'ascending':
                query = query.order_by(priority_order_ascending) # Order priority from low to high
        if sort_title == 'deadline':
            if sort_type == 'descending':
                query = query.order_by(Task.deadline.desc()) # Order deadline from latest to earliest
            elif sort_type == 'ascending':
                query = query.order_by(Task.deadline.asc()) # Order deadline from earliest to latest
        if sort_title == 'status':
            if sort_type == 'complete':
                query = query.order_by(status_order_complete) # Order status from complete to in-progress
            elif sort_type == 'in-progress':
                query = query.order_by(status_order_in_progress) # Order status from in-progress to complete
        if sort_title == 'latest':
            query = query.order_by(Task.id.desc()) # Order deadline from latest to earliest, newest first
        if sort_title == 'earliest':
            query = query.order_by(Task.id.asc()) # Order deadline from latest to earliest, oldest first
      
    user_tasks = query.all()  # Get all tasks for this user according to the id, default order is by date task was created from earliest to latest
    user_tasks_count = query.count() # Gets the total count of tasks of the user

    # This function runs when someone visits '/tasks', also passes other values like user_tasks so it can be accessed in tasks.html
    return render_template('tasks.html', tasks=user_tasks, count=user_tasks_count, sort_title=sort_title, sort_type=sort_type, filter_priorities=filter_priorities, filter_status=filter_status, filter_months=filter_months, filter_year=filter_year, filter_day=filter_day)

#Define a route for'/add_task'
@app.route('/add_task', methods=['POST'])
def add_task():
    # Get task eleemnts from form inputs
    title = request.form['title']
    description = request.form['description']
    priority = request.form['priority']
    date = request.form['deadline']
    user_id = session['user_id'] # Grab the current logged-in user's ID from the session
    user = User.query.get(user_id) # Gets User object

    #Convert date string into datetime object
    deadline = datetime.strptime(date, '%Y-%m-%dT%H:%M') # typical date string is '2025-08-12T15:30'
    # Attach user's timezone to the deadline
    deadline = deadline.replace(tzinfo=ZoneInfo(user.timezone))
    
    # Create a new Task instance with its elements like title, description, priority, deadline, status
    new_task = Task(title=title) # Note: title(database column) = title(local variable)
    new_task.description = description
    new_task.priority = priority
    new_task.deadline = deadline
    new_task.status = 'In-Progress' # Set status as In-Progress as default

    # Set email reminders for task to true by default, only works if user turns on email notifications
    new_task.set_today_reminder = True
    new_task.set_tomorrow_reminder = True

    new_task.user_id = user_id # Assigns task with user id
    
    # Add the new task to the database session and commit(save) changes
    db.session.add(new_task)
    db.session.commit()

    flash('Task successfully created', 'success')
    
    return redirect(url_for('tasks'))

#Define a route for'/edit_task' that accepts an integer task_id from the URL
@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    # Gets task from database
    task = Task.query.get(task_id)

    # Get task eleemnts from form inputs
    title = request.form['title']
    description = request.form['description']
    priority = request.form['priority']
    date = request.form['deadline']

    deadline = datetime.strptime(date, '%Y-%m-%dT%H:%M') # typical date string is '2025-08-12T15:30'

    if title and title != task.title: # Checks if title is not empty and title is different from previous title, change title
        task.title = title
    if description and description != task.description: # Checks if description is not empty and description is different from previous, change description
        task.description = description
    if priority and priority != task.priority: # Checks if priority is not empty and priority is differrent, change priority
        task.priority = priority
    if deadline and deadline != task.deadline: # Checks if date is not empty and date is different, change date
        task.deadline = deadline

    # Saves info    
    db.session.commit()

    return redirect(url_for('tasks'))

# Define a route for '/change_task_status that accepts an integer task_id from the URL
@app.route('/change_task_status/<int:task_id>')
def change_task_status(task_id):
    task = Task.query.get(task_id)   # Finds task in database
    status = task.status # Gets task current status: either In-Progress or Complete

    if status == 'In-Progress':
        task.status = 'Complete'
    else:   
        task.status = 'In-Progress'
        
    db.session.commit()  # Save changes

    return redirect(url_for('tasks'))

# Define a route for '/delete_task that accepts an integer task_id from the URL
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    delete_single_task(task_id) # Calls a function to delete task

    return redirect(url_for('tasks'))

# Helper function
def delete_single_task(task_id):
    # Finds task in database
    task = Task.query.get(task_id)
    user_id = session['user_id'] # Gets current user_id from session

    # If the task_user_id matches the user_id of current session, deletes task
    if user_id == task.user_id:
        # Delete the task of the user
        db.session.delete(task)
        db.session.commit()

    return

# Define a route for '/filter_task'
@app.route('/filter_sort_task', methods=['POST'])
def filter_sort_task():
    action = request.form['action']
    # Checks user's action, if reset - deselects all filters and sort order to default, otherwise continue to applying filters
    if action == 'reset':
        # Clear all sort values to None, and set filter values to empty string
        session['filter_priorities'] = []
        session['filter_status'] = []
        session['filter_months'] = []
        session['filter_year'] = None
        session['filter_day'] = None
        session.pop('sort_title', None)
        session.pop('sort_type', None)
    else:
        # Gets selected sort and filter from form
        select_sort = request.form['sort']
        session['sort_title'] = select_sort
        
        # Assigns sort_title and sort_type within session with correct values
        if select_sort == 'priority-descending':
            session['sort_title'] = 'priority'
            session['sort_type'] = 'descending'
        if select_sort == 'priority-ascending':
            session['sort_title'] = 'priority'
            session['sort_type'] = 'ascending'
        
        if select_sort == 'deadline-descending':
            session['sort_title'] = 'deadline'
            session['sort_type'] = 'descending'
        if select_sort == 'deadline-ascending':
            session['sort_title'] = 'deadline'
            session['sort_type'] = 'ascending'
        if select_sort == 'status-complete':
            session['sort_title'] = 'status'
            session['sort_type'] = 'complete'
        if select_sort == 'status-in-progress':
            session['sort_title'] = 'status'
            session['sort_type'] = 'in-progress'

        # Gets selected filter from form and saves as a list
        session['filter_priorities'] = request.form.getlist('priority') # Stores list of checked priorities within session
        session['filter_status'] = request.form.getlist('status') # Stores list of checked status within session
        session['filter_months'] = list(map(int, request.form.getlist('month'))) # Converts string list as integers and stores list of checked months (1-12) within session
        # Gets year and day filter from form and save to variable
        year_filled = request.form.get('year-filter')
        day_filled = request.form.get('day-filter')
        
        # Checks if input for year and day are filled or non-empty, if filled then saved to session, otherwise set is as None
        if year_filled:    
            session['filter_year'] = int(year_filled)
        else: 
            session['filter_year'] = None
        if day_filled:
            session['filter_day'] = int(day_filled)
        else:
            session['filter_day'] = None

    # Redirects users to task route 
    return redirect(url_for('tasks')) 


#-------------Settings------------------------------

# Define a route for '/settings'
@app.route('/settings')
def settings():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    user_timezone = user.timezone

    email_notifications = user.email_notifications
    if email_notifications:
        notifications = 'On'
    else:
        notifications = 'Off'
    # This function runs when someone visits '/settings'
    return render_template('settings.html', timezone=user_timezone, notifications=notifications)

# Define a route for '/change_name'
@app.route('/change_name', methods=['POST'])
def change_name():
    user = User.query.get(session['user_id'])  # get current user from session using the id

    # Creates new local variables and assigns user input from the form and by their input name
    username = request.form['username']
    first = request.form['first']
    last = request.form['last']


    # Check if not null or empty, update user's name if needed
    if username: 
        user.username = username
    if first:
        user.first = first
    if last:
        user.last = last

    # Saves info    
    db.session.commit()
    # Shows saved changes
    flash('Saved New Changes','success')
    return redirect(url_for('settings'))

# Define a route for '/change_password'
@app.route('/change_password', methods=['POST'])
def change_password():
    user = User.query.get(session['user_id'])  # get current user from session using the id

    password = request.form['password'] # get new password from form

    # Set new password
    user.set_password(password)

    # Saves info    
    db.session.commit()
    # Shows saved changed
    flash('Saved New Password','success')
    return redirect(url_for('settings'))

# Define a route for '/delete_account
@app.route('/delete_account', methods=['POST'])
def delete_account():
    # Gets user id
    user_id = session.get('user_id')

    # Finds user in database
    user = User.query.get(user_id)
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()

    # 4. Clear the session (logs user out)
    session.clear()
    flash('Account Deleted','error')
    return redirect(url_for('login'))

# Define a route for '/change_timezone'
@app.route('/change_timezone', methods=['POST'])
def change_timezone():
    timezone_request = request.form['timezone']
    user_id = session.get('user_id') # Gets user id from session
    user = User.query.get(user_id) # Gets User object from user_id

    old_timezone = user.timezone # Gets previous timezone
    # Change user's timezone
    user.timezone = timezone_request

    # Change all tasks deadline to fit new timezone deadline
    user_tasks = Task.query.filter_by(user_id=user_id).all()
    for task in user_tasks:
        # NEEDS TO BE FIXED
        old_deadline = task.deadline.replace(tzinfo=ZoneInfo(old_timezone))  
        # Convert into new timezone
        new_deadline = old_deadline.astimezone(ZoneInfo(timezone_request))  
        task.deadline = new_deadline
    db.session.commit()
    session['user_timezone'] = timezone_request
    return redirect(url_for('settings'))

            

# Define a route for '/notifications'
@app.route('/notifications', methods=['POST']) 
def notifications():
    result = request.form['result']
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if result == 'yes':
        user.email_notifications = False
        #WORK IN PROGRESS - needs code to turn email notifications off when tasks portion is complete
        flash('Email Notifications turned off (IP)', 'error')
    else:
        user.email_notifications = True
        flash('Email Notifications turned on (IP)', 'success')

    db.session.commit()
    return redirect(url_for('settings'))

# Define a route for '/delete_data
@app.route('/delete_data', methods=['POST'])
def delete_data():
    # Gets user id
    user_id = session['user_id']

    # Gets user's tasks within database by their id
    user_tasks = Task.query.filter_by(user_id=user_id).all()

    # Used for loop through iterate all user's tasks and delete them from database
    for task in user_tasks:
        delete_single_task(task.id)
    

    flash('All Data Cleared','error')
    return redirect(url_for('settings'))

# Define a route for '/signout'
@app.route('/signout', methods=['POST'])
def signout():
    session.pop('user_id', None)  # Logs the user out
    return redirect(url_for('login'))  # Redirect to login if not logged in

# This block runs the app only if this script is executed directly (not imported)
if __name__ == "__main__":
    # Create the database tables (only creates tables if they don't exist)
    with app.app_context():
        db.create_all()

    # Start the Flask development server with debug mode on
    # Debug mode reloads server on code changes and shows errors in browser
    app.run(debug=True)
