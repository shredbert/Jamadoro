'use strict';

import { togglePlayback } from './toggle-player.js';

// Spotify data can't be null or empty if no connection or undefined if login
// page
const timer = document.querySelector('lit-interval-timer');
if (timer) {
	timer.addEventListener('timerToggled', (event) => {
		console.log(event.detail);
		// Play if work session & timer active, pause if break session or timer
		// inactive
		if (event.detail.isWorkSession) {
			togglePlayback(event.detail.isPlaying);
		}
	});
}
