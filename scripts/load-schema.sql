-- schema creation script
-- drops
DROP TABLE IF EXISTS pomodoro;

DROP TABLE IF EXISTS todo;

DROP TABLE IF EXISTS jammer;

CREATE TABLE jammer (
	jammer_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	-- Email address max = 254 chars
	email VARCHAR(254) UNIQUE NOT NULL,
	jammer_pw VARCHAR(255) NOT NULL,
	username VARCHAR(30) NOT NULL,
	work_time_secs INTEGER NOT NULL DEFAULT 3000,
	break_time_secs INTEGER NOT NULL DEFAULT 600,
	daily_goal_hrs INTEGER NOT NULL DEFAULT 1,
	-- work time can be 12.5, 25, 37.5, or 50 min
	CONSTRAINT valid_work_time CHECK (work_time_secs IN (750, 1500, 2250, 3000)),
	-- break time can be 2.5, 5, 7.5, or 10 min
	CONSTRAINT valid_break_time CHECK (break_time_secs IN (150, 300, 450, 600)),
	-- min 1, max 8
	CONSTRAINT valid_daily_goal_hrs CHECK (
		daily_goal_hrs > 0
		AND daily_goal_hrs < 9
	)
);

CREATE TABLE pomodoro (
	pomodoro_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	jammer_id INTEGER NOT NULL REFERENCES jammer,
	completed_date DATE NOT NULL,
	-- total time with timer going -- i.e., work + break -> easier for fitting
	-- in schedule
	duration_secs INTEGER NOT NULL,
	CONSTRAINT valid_duration_secs CHECK (duration_secs IN (900, 1800, 2700, 3600))
);

CREATE TABLE todo (
	todo_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
	jammer_id INTEGER NOT NULL REFERENCES jammer,
	todo_description VARCHAR(50) NOT NULL,
	-- TODO: Currently setting order to 0 if complete -- is that best, or just
	-- NULL? Order not useful after completion since list will always be up to
	-- date? Or just increment order each time a record is added? If so, how to
	-- reorder? Sorting on server equal amounts of work either way?
	list_order INTEGER NOT NULL,
	is_complete BOOLEAN NOT NULL DEFAULT FALSE,
	completed_date DATE,
	CONSTRAINT valid_list_order CHECK (
		(
			list_order > 0
			AND is_complete = FALSE
		)
		OR (
			list_order = 0
			AND is_complete = TRUE
		)
	),
	CONSTRAINT valid_completion_date CHECK (
		(
			completed_date IS NULL
			AND is_complete = FALSE
		)
		OR (
			completed_date IS NOT NULL
			AND is_complete = TRUE
		)
	)
);
