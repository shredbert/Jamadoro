'use strict';

// Theme can be 'light', 'dark', or 'auto' -- default is 'auto' if not set
// If set, available from localStorage
const getStoredTheme = () => {
	return localStorage.getItem('theme');
};

// Get theme
const getPreferredTheme = () => {
	// If set previously & found in localStorage, return preference
	const storedTheme = getStoredTheme();
	if (storedTheme) {
		return storedTheme;
	}

	// If not set, return browser preference
	return window.matchMedia('(prefers-color-scheme: dark)').matches
		? 'dark'
		: 'light';
};

// Set theme
const setTheme = (theme) => {
	document.documentElement.setAttribute('data-bs-theme', theme);
	const nav = document.getElementById('navDropdown');
	if (nav) {
		nav.setAttribute('data-bs-theme', theme);
	}
};

setTheme(getPreferredTheme());

// Select active theme in UI based on preference
const selectActiveTheme = (theme) => {
	document.querySelectorAll('[data-bs-theme-value]').forEach((btn) => {
		if (btn.dataset.bsThemeValue === theme) {
			btn.classList.add('active');
			btn.setAttribute('aria-pressed', 'true');
		} else {
			btn.classList.remove('active');
			btn.setAttribute('aria-pressed', 'false');
		}
	});
};

// Update when theme changed manually
const handleThemeChange = (event) => {
	const theme = event.target.dataset.bsThemeValue;
	localStorage.setItem('theme', theme);
	setTheme(theme);
	selectActiveTheme(theme);
};

window.addEventListener('DOMContentLoaded', () => {
	selectActiveTheme(getPreferredTheme());

	// Listen for & respond to clicking on themes
	document.querySelectorAll('[data-bs-theme-value]').forEach((btn) => {
		btn.addEventListener('click', handleThemeChange);
	});
});

const handleThemePrefChange = () => {
	const theme = getPreferredTheme();
	setTheme(theme);
	selectActiveTheme(theme);
};

// Change theme if user's preferred colour scheme changes while in app
window
	.matchMedia('(prefers-color-scheme: light)')
	.addEventListener('change', handleThemePrefChange);
window
	.matchMedia('(prefers-color-scheme: dark)')
	.addEventListener('change', handleThemePrefChange);
