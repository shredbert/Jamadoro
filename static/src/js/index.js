'use strict';

// Would like to use Rollup to tree shake & just use Bootstrap ESM imports but
// doesn't work
// https://github.com/twbs/bootstrap/issues/37575
// Need to use the 'src' files for individual components
// https://github.com/twbs/bootstrap/issues/35352
// Components not accessed through JS, just required by HTML for interactions
import Alert from 'bootstrap/js/src/alert';
import Dropdown from 'bootstrap/js/src/dropdown';

// Colour theme toggler
import './modules/toggle-themes.js';

// Handle events triggered by timer
import './modules/toggle-player.js';
import './modules/timer-events.js';
import './modules/session-events.js';

// Handle notifications
import './modules/toggle-notifications.js';

// Mark To Dos complete as go from index
import './modules/complete-todo.js';

// Web components
import './web-components/lit-interval-timer.js';
