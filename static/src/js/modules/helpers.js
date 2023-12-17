'use strict';

import Toast from 'bootstrap/js/src/toast';

// Spotify data injected into HTML template from server -- check if declared,
// populated, & valid object keys
export function isSpotifyConnected() {
	return typeof SpotifyData !== 'undefined' &&
		SpotifyData &&
		Object.keys(SpotifyData).length > 0
		? true
		: false;
}

export function displayToastMessage(type, msg) {
	const toastElement =
		type === 'success'
			? document.getElementById('toastSuccess')
			: document.getElementById('toastError');

	if (toastElement) {
		toastElement.innerHTML = `<span>${msg}</span>`;
		Toast.getOrCreateInstance(toastElement).show();
	}
}

export function displayNotification(msg) {
	if (Notification.permission === 'granted') {
		// TODO: Add Jamadoro icon to message -- https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API/Using_the_Notifications_API
		new Notification(msg);
	}
}
