'use strict';

import { displayToastMessage, displayNotification } from './helpers';

import { togglePlayback } from './toggle-player.js';

// TODO: Issue with injecting raw HTML into DOM?
function updateProgressCard(html) {
	document.getElementById('progressCard').innerHTML = html;
}

const timerElement = document.querySelector('lit-interval-timer');
if (timerElement) {
	timerElement.addEventListener('timerDone', (event) => {
		console.log('Session done', event.detail, event.target.dataset.goal);

		// Start player after break completed but don't log work
		if (!event.detail.isWorkSession) {
			displayNotification('Break finished -- begin working!');
			togglePlayback(true);
			return;
		}

		const sessionGoalElement = document.querySelector('#sessionGoal');
		const sessionsTodayElement = document.querySelector('#sessionsToday');

		if (!sessionGoalElement || !sessionsTodayElement) {
			console.error('Error getting session progress data');
			return;
		}

		// Progress & goal when last updated from server
		const goalHrs = parseFloat(sessionGoalElement.dataset.goal);
		const startProgHrs = parseFloat(sessionsTodayElement.dataset.progress);
		const workTimeSecs = parseInt(event.detail.workTimeSecs);
		const breakTimeSecs = parseInt(event.detail.breakTimeSecs);
		// // TEST
		// const workTimeSecs = parseInt(750);
		// const breakTimeSecs = parseInt(150);
		const hrsWorked = startProgHrs + (workTimeSecs + breakTimeSecs) / 3600;
		console.log(goalHrs, hrsWorked);

		// Pause player after work session finished
		if (hrsWorked === goalHrs) {
			displayNotification(
				"You've met your session goal for the day -- congratulations!!! 🥳🥳🥳🎉🎉🎉"
			);
		} else {
			displayNotification('Work finished -- take a break!!!☺☺☺');
		}

		// Stop playback once work done
		togglePlayback(false);

		const requestForm = new FormData();
		// // TEST -- required if using custom timer lengths for dev
		// requestForm.append('duration-secs', 900);
		requestForm.append('duration-secs', event.detail.workTimeSecs + event.detail.breakTimeSecs);
		const requestUrl = '/add-pomodoro';
		const requestProps = {
			method: 'POST',
			body: requestForm,
		};

		// Update sessions in UI
		fetch(requestUrl, requestProps)
			.then((response) => {
				if (!response.ok) {
					throw new Error(`HTTP error: ${response.status}`);
				}
				return response.text();
			})
			.then((html) => {
				updateProgressCard(html);
				displayToastMessage(
					'success',
					'Pomodoro complete -- rock on!!! 🤘🤘🤘'
				);
			})
			.catch((err) => {
				console.error(`Error: ${err}`);
				displayToastMessage(
					'error',
					'An error was encountered & your jam was not logged... 👎👎👎'
				);
			});
	});
}
