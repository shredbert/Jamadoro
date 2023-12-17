import Tooltip from 'bootstrap/js/src/tooltip';

const tooltipElement = document.querySelector('[data-bs-toggle="tooltip"]');
if (tooltipElement) {
	new Tooltip(document.querySelector('[data-bs-toggle="tooltip"]'));
}

// Set notification state according to permission status
function displayBtn() {
	const notifStatus = document.querySelector('#notifStatus');

	if (!notifStatus) {
		return;
	}

	// Notifications can be default, granted, or disabled
	if (Notification.permission === 'granted') {
		notifStatus.innerHTML = 'Notifications enabled';
	} else if (Notification.permission === 'denied') {
		notifStatus.innerHTML = 'Notifications disabled';
	} else {
		// 'default' state == unselected, text already in element
		notifStatus.innerHTML = 'Notification preference not set';
	}
}

// Use container for events & appending buttons
const notifToggleContainer = document.querySelector('#notifToggleContainer');

if (notifToggleContainer) {
	notifToggleContainer.addEventListener('click', (e) => {
		// Re-display if toggle btn pressed & notifications in 'default' state
		console.log(Notification.permission);
		if (e.target.id !== 'notifToggleBtn') {
			return;
		}
		Notification.requestPermission().then(() => displayBtn());
	});
}

// Initial display on page
displayBtn();
