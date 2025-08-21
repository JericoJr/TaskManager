// this variable ensures that popups are shown one at a time  
let show = true;
// Shows the popup by adding the 'show' class
function openPopup(id) {
  if (show) {
      document.getElementById(id).classList.add('show');
      show = false;
  }
  // document            - Access the HTML document (DOM)
  // .getElementById(id) - Find the element with the specific `id` (e.g., "change-name")
  // .classList          - Access the element's list of CSS classes
  // .add('show');       - Add the class 'show' to it
}

// Popup for edit_task 
function openEditPopup(button, id) {
  // Get values passed from edit button
  const task_id = button.getAttribute('data-id');
  const title = button.getAttribute('data-title');
  const description = button.getAttribute('data-description');
  const priority = button.getAttribute('data-priority');
  const deadline = button.getAttribute('data-deadline');

  // Place the values from edit button onto the edit form fields
  document.getElementById('edit-title').value = title;
  document.getElementById('edit-description').value = description;
  document.getElementById('edit-priority-list').value = priority;
  document.getElementById('edit-deadline').value = deadline;

  // Dynamically set the form's action URL to the correct edit route for the selected task
  document.getElementById('edit-form').action = `/edit_task/${task_id}`;

  // Shows popup
  openPopup(id);
}

// Popup for edit_task 
function openEditPopup(button, id) {
  // Get values passed from edit button
  const task_id = button.getAttribute('data-id');
  const title = button.getAttribute('data-title');
  const description = button.getAttribute('data-description');
  const priority = button.getAttribute('data-priority');
  const deadline = button.getAttribute('data-deadline');

  // Place the values from edit button onto the edit form fields, .value used for form elements
  document.getElementById('edit-title').value = title;
  document.getElementById('edit-description').value = description;
  document.getElementById('edit-priority-list').value = priority;
  document.getElementById('edit-deadline').value = deadline;

  // Dynamically set the form's action URL to the correct edit route for the selected task
  document.getElementById('edit-form').action = `/edit_task/${task_id}`;

  // Shows popup
  openPopup(id);
}

// Popup for viewing task within calendar
function openTaskPopup(button, id) {
  // Get values passed from task button
  const task_id = button.getAttribute('task-id');
  const title = button.getAttribute('task-title');
  const description = button.getAttribute('task-description');
  const priority = button.getAttribute('task-priority');
  const deadline = button.getAttribute('task-deadline');

  // Place the values from task button onto the <p> within task popup, .textContent used for plain HTML elements
  document.getElementById('display-title').textContent = title;
  document.getElementById('display-description').textContent = description;
  document.getElementById('display-priority').textContent = priority;
  document.getElementById('display-deadline').textContent = deadline;

  // Shows popup
  openPopup(id);
}

// Hides the popup by removing the 'show' class
function closePopup(id) {
  document.getElementById(id).classList.remove('show');
  show = true;
}

