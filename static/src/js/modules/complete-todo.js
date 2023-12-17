'use strict';

import { displayToastMessage } from './helpers';

// Add to whole page & use event bubbling
document.addEventListener('click', (e) => {
	if (e.target.id === 'completeTodoBtn') {
		completeToDo(e.target.dataset.todoId);
	}
});

// Enable button if available
setupCmpltBtn();

function completeToDo(todoId) {
	console.log(todoId);
	const url = '/complete-todo';
	const form = new FormData();
	form.append('todo', todoId);
	fetch(url, {
		method: 'PATCH',
		body: form,
	})
		.then((response) => {
			if (!response.ok) {
				throw Error(`Server error: ${response.status}`);
			}
			return response.text();
		})
		.then((html) => {
			replaceTodo(html);
			displayToastMessage(
				'success',
				'To Do successfully completed!!! 🤘🤘🤘'
			);
		})
		.catch((e) => {
			console.error(e);
			displayToastMessage(
				'error',
				`There was an error completing your To Do... 👎👎👎`
			);
		});
}

function replaceTodo(html) {
	const crntTodo = document.getElementById('crntTodo');
	if (!crntTodo) {
		throw Error('Issue replacing To Do');
	}
	crntTodo.innerHTML = html;
	setupCmpltBtn();
}

// Enable Add btn since requires JS -- user can't use if not loaded
function setupCmpltBtn() {
	const cmpltBtn = document.querySelector('#completeTodoBtn');
	// Don't throw error if not found -- won't be available if no To Dos left
	if (cmpltBtn) {
		// Remove disabled attribute for button if populated in component --
		// progressive enhancement solution since useless without JS
		cmpltBtn.disabled = false;
	}
}
