import { icons } from './lit-interval-timer-icons.js';
import { LitElement, css, html } from 'lit';

class LitIntervalTimer extends LitElement {
	static properties = {
		workTimeSecs: { attribute: 'work-time-secs', type: Number },
		breakTimeSecs: { attribute: 'break-time-secs', type: Number },
		timeRemaining: { state: true, type: Number },
		hasStarted: { state: true, type: Boolean },
		isPlaying: { state: true, type: Boolean },
		isWorkSession: { state: true, type: Boolean },
		timerId: { state: true, type: Number },
	};

	static styles = css`
		:host {
			display: flex;
			flex-direction: column;
			justify-content: center;
			align-items: center;
			width: 100%;
			gap: 0.8rem;
		}
		.time {
			font-size: 5rem;
		}
		button {
			border: none;
			background: none;
			color: currentColor;
		}
		button > svg {
			width: 5rem;
			height: auto;
		}
		.msg {
			font-size: 1.5rem;
		}
	`;

	constructor() {
		super();
		this.workTimeSecs = 3000;
		this.breakTimeSecs = 600;
		this.timeRemaining = 0;
		this.hasStarted = false;
		this.isPlaying = false;
		this.isWorkSession = true;
		this.timerId = 0;
	}

	connectedCallback() {
		super.connectedCallback();
		this.timeRemaining = this.getDefaultTime();
	}

	disconnectedCallback() {
		super.disconnectedCallback();
		if (this.timerId) {
			clearInterval(this.timerId);
		}
	}

	render() {
		return html`
			<span class="time">${this.getTime()}</span>
			<div class="btns">${this.getIcons()}</div>
			<span class="msg">${this.getMsg()}</span>
		`;
	}

	timerToggleEvent = () => {
		return new CustomEvent('timerToggled', {
			detail: {
				isWorkSession: this.isWorkSession,
				isPlaying: this.isPlaying,
			},
			bubbles: true,
			composed: true,
		});
	};

	timerDoneEvent = () => {
		return new CustomEvent('timerDone', {
			detail: {
				isWorkSession: this.isWorkSession,
				workTimeSecs: this.workTimeSecs,
				breakTimeSecs: this.breakTimeSecs,
			},
			bubbles: true,
			composed: true,
		});
	};

	startPlayback = () => {
		this.hasStarted = true;
		this.timerId = setInterval(() => {
			this.timeRemaining--;
			if (this.timeRemaining < 0) {
				this.dispatchEvent(this.timerDoneEvent());
				this.isWorkSession = !this.isWorkSession;
				this.timeRemaining = this.getDefaultTime() - 1;
			}
		}, 1000);
	};

	pausePlayback = () => {
		clearInterval(this.timerId);
		this.isPlaying = false;
	};

	toggleTimer = () => {
		this.isPlaying = !this.isPlaying;
		this.dispatchEvent(this.timerToggleEvent());
		if (this.isPlaying) {
			this.timeRemaining--;
			this.startPlayback();
		} else {
			this.pausePlayback();
		}
	};

	getDefaultTime = () => {
		return this.isWorkSession ? this.workTimeSecs : this.breakTimeSecs;
	};

	resetTimer = () => {
		if (this.isPlaying) {
			// If playing, restart time only
			clearInterval(this.timerId);
			this.timeRemaining = this.getDefaultTime() - 1;
			this.startPlayback();
		} else {
			// If not playing, do full reset
			this.pausePlayback();
			this.hasStarted = false;
			this.isWorkSession = true;
			this.timeRemaining = this.getDefaultTime();
		}
	};

	getIcons = () => {
		return html`
			<button @click=${this.toggleTimer}>
				${this.isPlaying ? icons.pauseBtn : icons.playBtn}
			</button>
			<button @click=${this.resetTimer}>${icons.resetBtn}</button>
		`;
	};

	fmtTime = (time) => {
		return time < 10 ? `0${time}` : time;
	};

	getTime = () => {
		const mins = Math.floor(this.timeRemaining / 60);
		const secs = this.timeRemaining % 60;
		return `${this.fmtTime(mins)}:${this.fmtTime(secs)}`;
	};

	messages = {
		notStarted: 'Begin work',
		work: 'Get working',
		break: 'Take a break',
		pause: 'Paused',
	};

	getMsg = () => {
		if (!this.hasStarted) {
			return this.messages.notStarted;
		} else {
			if (!this.isPlaying) {
				return this.messages.pause;
			} else {
				return this.isWorkSession
					? this.messages.work
					: this.messages.break;
			}
		}
	};
}

customElements.define('lit-interval-timer', LitIntervalTimer);
