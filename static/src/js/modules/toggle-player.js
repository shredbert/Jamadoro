'use strict';

import { displayToastMessage, isSpotifyConnected } from './helpers';

function updatePlayerCard(html) {
	document.getElementById('spotifyCard').innerHTML = html;
}

function displayPlayerState() {
	const url = '/get-player-card';
	const urlProps = {
		method: 'get',
	};
	fetch(url, urlProps)
		.then((response) => {
			if (!response.ok) {
				throw new Error(`HTTP error: ${response.status}`);
			}
			return response.text();
		})
		.then((html) => {
			// TODO: If paused in player while timer going, will just keep
			// updating player state, even though redundant -- issue?
			updatePlayerCard(html);
		})
		.catch((err) => {
			console.error(`Issue getting Spotify card: ${err}`);
			displayToastMessage(
				'error',
				'Sorry, there was an issue getting your Spotify player data -- please try again'
			);
		});
}

// Refresh Spotify player data every second while working
let playerInterval;

function startUiUpdates() {
	playerInterval = setInterval(() => {
		try {
			displayPlayerState();
		} catch (err) {
			console.error('Issue updating player UI...');
			stopUiUpdates();
		}
	}, 1000);
	console.info('Starting player interval', playerInterval);
}

function stopUiUpdates() {
	console.info('Stopping player interval', playerInterval);
	clearInterval(playerInterval);
	displayPlayerState();
}

// Toggle playback if true, otherwise false
export function togglePlayback(shouldStartPlayback) {
	console.log(
		'Toggling playback',
		'Start:',
		shouldStartPlayback,
		'Connected:',
		isSpotifyConnected()
	);

	// Can't toggle if not connected
	if (!isSpotifyConnected()) {
		return;
	}

	const url = '/toggle-playback';
	// Use JSON because using boolean on server
	const urlProps = {
		method: 'put',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ 'should-start-playback': shouldStartPlayback }),
	};
	fetch(url, urlProps)
		.then((response) => {
			if (!response.ok) {
				throw new Error(`HTTP error: ${response.status}`);
			}
			return response.json();
		})
		.then((data) => {
			console.log('Toggle response:', data);
			if (data.isTimingStarted) {
				startUiUpdates();
			} else {
				stopUiUpdates();
			}
		})
		.catch((err) => {
			console.error(`Could not toggle playback: ${err}`);
			displayToastMessage(
				'error',
				'Sorry, there was an error triggering Spotify playback -- please try again'
			);
		});
}

// Display Spotify player status on initial load
if (isSpotifyConnected()) {
	console.log('Spotify connected!', SpotifyData);
} else {
	console.warn('Spotify not available -- no player state to update...');
}
