# Getting today's date
from datetime import date

# Only needed in production
from dotenv import load_dotenv

# Flask stuff
from flask import (
    flash,
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from flask_assets import Bundle, Environment

from flask_session import Session

# Fetch environment vaeiables from .env file, automatically supported by Flask
# if python-dotenv installed
# https://flask.palletsprojects.com/en/2.2.x/cli/#environment-variables-from-dotenv
import os

# Generate a randomized string for state monitoring with the Spotify API
import secrets

# Parse URL to Spotify API
# https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlencode
from urllib.parse import urlencode

from utils_db import (
    insert_jammer,
    insert_pomodoro,
    insert_todo,
    slct_jammer_pw,
    slct_jammer_info,
    slct_pomodoro_usr_cmplt_by_date,
    slct_jammer_usr_sets,
    slct_todo_next_for_jammer,
    slct_todo_todos,
    updt_jammer_pw,
    updt_jammer_pom_sets,
    updt_todo_cmplt_all,
    updt_todo_cmplt_one,
    updt_todo_lst_ord,
    delete_todo_all_incmplt,
    delete_todo_one,
)

from utils_general import (
    AppError,
    clear_spotify_session,
    clear_user_data,
    is_logged_in,
    is_valid_password,
)

from utils_spotify import (
    get_player_data,
    get_spotify_data,
    load_tokens,
    pause_playback,
    start_playback,
)

# TODO: Upgrade versions of Flask/Werkzeug when issue fixed -- can't do signed
# sessions with Werkzeug 3.0.0+
# https://github.com/pallets-eco/flask-session/pull/189
# Security stuff
# https://werkzeug.palletsprojects.com/en/2.2.x/utils/#module-werkzeug.security
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask
app = Flask(__name__)

# Configure static assets
assets = Environment(app)
js_all = Bundle("public/index.js", output="index.js")
assets.register("js", js_all)
css_all = Bundle("public/index.css", output="index.css")
assets.register("css", css_all)

# Do server-side sessions for Spotify API credentials -- more secure?
# https://security.stackexchange.com/questions/115695/when-should-server-side-sessions-be-used-instead-of-client-side-sessions

app.config.update(
    # TODO: use_signer seems more secure but not sure of benefits -- copied
    # from tutorial
    SESSION_USE_SIGNER=True,
    # Key required by use_signer -- comment out during dev, forces logout on
    # change
    # Use token_hex() for random string -- https://flask.palletsprojects.com/en/3.0.x/config/#SECRET_KEY
    SECRET_KEY=secrets.token_hex(32),
    # https://testdriven.io/blog/flask-server-side-sessions/
    # TODO: Look into using Redis/SQLAlchemy for session storage?
    SESSION_TYPE="filesystem",
    SESSION_PERMANENT=False,
    # https://flask.palletsprojects.com/en/2.3.x/security/#security-cookie
    SESSION_COOKIE_SECURE=True,
    # https://flask.palletsprojects.com/en/2.3.x/config/#SESSION_COOKIE_SAMESITE
    SESSION_COOKIE_SAMESITE="Lax",
    # Sets "Cache-Control" property when static files served
    # TODO: Only sets "max-age" directive -- find way to add "immutable" to tell browser not to revalidate after
    SEND_FILE_MAX_AGE_DEFAULT=2147483648,
)

Session(app)

# Load environment vars (necessary for prod only)
load_dotenv()

# Environment variables for accessing the Spotify API
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")
MAX_API_REQUEST_ATTEMPTS = 3

# TODO: Handle error pages
# https://flask.palletsprojects.com/en/2.3.x/errorhandling/

# TODO: Handle logging
# https://flask.palletsprojects.com/en/2.3.x/logging/


# Auth routes
# TODO: Unsuccessful registration/login create cookies weirdly since session
# state created but not set with correct params above? Getting error about
# SameSite attribute in Firefox console?


@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        # Return GET request immediately
        if request.method == "GET":
            return render_template("register.html")

        # POST request
        if (
            not request.form.get("email")
            or not request.form.get("password")
            or not request.form.get("confirm")
            or not request.form.get("username")
        ):
            raise AppError("Please submit all fields to register an account.")

        email = str(request.form.get("email"))
        password = str(request.form.get("password"))
        confirm = str(request.form.get("confirm"))
        username = str(request.form.get("username"))

        if password != confirm:
            raise AppError("Please ensure passwords match to register an account.")

        if not is_valid_password(password):
            raise AppError(
                "Please submit a password that is 8 to 30 characters & "
                + "includes at least 1 capital, 1 lowercase, 1 numeric, & "
                + "one non-alphanumeric character."
            )

        # User already exists
        if slct_jammer_info(email):
            raise AppError(
                "That email is already used by an account -- please try again."
            )

        # Attempt to register user
        insert_jammer(
            email=email,
            hashed_password=generate_password_hash(password),
            username=username,
        )

        flash(f"Registration successful -- welcome, {username}!", "success")
        return render_template("login.html")
    except AppError as e:
        print(type(e), e)
        flash(str(e), "danger")
        return render_template("register.html")
    except Exception as e:
        print(type(e), e)
        flash(
            "There was an error creating your account -- please try \
            again.",
            "danger",
        )
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "GET":
            return render_template("login.html")

        if not request.form.get("email") or not request.form.get("password"):
            raise AppError("Please submit an email & password to login.")

        email = str(request.form.get("email"))
        password = str(request.form.get("password"))

        user_data = slct_jammer_info(email=email)

        if not user_data or not check_password_hash(user_data["jammer_pw"], password):
            raise AppError("Invalid credentials -- please try again.")

        # Need ID, email, & name
        session["jammer_id"] = user_data["jammer_id"]
        session["email"] = user_data["email"]
        session["username"] = user_data["username"]

        # Default code of 302
        return redirect(url_for("index"))
    except AppError as e:
        print(type(e), e)
        flash(str(e), "danger")
        return redirect(url_for("login"))
    except Exception as e:
        print(type(e), e)
        flash("There was an error loggin you in -- please try again.", "danger")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    try:
        # Don't use session.clear() -- want to retain session itself for
        # passing messages?
        clear_user_data()
        clear_spotify_session()
    except Exception as e:
        print("Logout exception", type(e), str(e))
    finally:
        # Default code of 302
        return redirect(url_for("login"))


# Index routes


@app.route("/")
@is_logged_in
def index():
    try:
        is_first_load = not session.get("has_loaded_page")

        # Populate user/session info
        user_settings = slct_jammer_usr_sets(session.get("jammer_id"))
        user_daily_sessions = slct_pomodoro_usr_cmplt_by_date(
            session.get("jammer_id"), date.today()
        )

        if not user_settings or not user_daily_sessions:
            raise Exception("Issue retrieving user/session data from DB")

        # Default state for tracking timer -- required to sync with client when
        # changing Spotify playback states
        session["is_timing_started"] = False

        # To Do stuff
        next_todo = slct_todo_next_for_jammer(session.get("jammer_id"))

        # Spotify stuff

        # If session code submitted in request & Spotify tokens not present,
        # request tokens from API & load into session state
        if request.args.get("code") and not session.get("access_token"):
            load_tokens(
                redirect_uri=REDIRECT_URI,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                code=str(request.args.get("code")),
            )
            flash("Connecting to Spotify was successful!", "success")

        # Populate Spotify data if connected
        spotify_data = None
        player_data = None

        if session.get("access_token") and session.get("refresh_token"):
            spotify_data = get_spotify_data(
                max_attempts=MAX_API_REQUEST_ATTEMPTS,
                access_token=session.get("access_token"),
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
            )
            # Player data -- if not populated, not playing
            player_data = get_player_data(
                max_attempts=MAX_API_REQUEST_ATTEMPTS,
                access_token=session.get("access_token"),
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
            )

            # Spotify was connected to but no data = probably no player open
            if not spotify_data:
                raise AppError(
                    "Error connecting to Spotify -- please make sure you have a player open & try again"
                )
            else:
                if is_first_load:
                    flash("Connecting to Spotify was successful!", "success")
        else:
            if is_first_load:
                flash("Log in to Spotify to fully jam out!", "success")

        session["has_loaded_page"] = True
        return render_template(
            "index.html",
            next_todo=next_todo,
            user_settings=user_settings,
            user_daily_sessions=user_daily_sessions,
            spotify_data=spotify_data,
            player_data=player_data,
            is_timing_started=session.get("is_timing_started"),
        )
    except AppError as e:
        print(type(e), e)
        flash(str(e), "danger")
        return render_template("login.html")
    except Exception as e:
        print(type(e), e)
        flash("There was an error loading Jamadoro -- please try again.", "danger")
        return render_template("login.html")


# Increment number of sessions & return new number
@app.route("/add-pomodoro", methods=["POST"])
@is_logged_in
def add_pomodoro():
    """Accept a duration in seconds that has been completed for a Pomodoro &
    use it to increment the user's time worked for the day
    Return the HTML used to render the card displaying the user's daily
    progress
    """
    try:
        # Check seconds worked & return status code manually
        # https://flask.palletsprojects.com/en/2.3.x/api/#flask.Flask.make_response
        duration_secs = request.form.get("duration-secs")

        if not duration_secs:
            return "Please submit a duration", 400

        # Add new session
        insert_pomodoro(session.get("jammer_id"), date.today(), int(duration_secs))

        # Need user session goal & Pomodoros today to display progress card
        user_settings = slct_jammer_usr_sets(session.get("jammer_id"))
        user_daily_sessions = slct_pomodoro_usr_cmplt_by_date(
            session.get("jammer_id"), date.today()
        )

        if not user_settings or not user_daily_sessions:
            raise Exception("Could not get session data")

        return render_template(
            "index/progress-card.html",
            user_settings=user_settings,
            user_daily_sessions=user_daily_sessions,
        )
    except Exception as e:
        print(type(e), e)
        return "An issue was encountered adding your session -- please try again", 500


# Spotify routes


@app.route("/connect-spotify")
@is_logged_in
def connect_spotify():
    try:
        # Authenticate based on OAuth 2.0 & Spotify Web API
        # Requires connection request, response handler, & refresh request
        # https://developer.spotify.com/documentation/general/guides/authorization/code-flow/
        # https://datatracker.ietf.org/doc/html/rfc6749

        # Randomize session string to help prevent XSRF attacks
        # https://datatracker.ietf.org/doc/html/rfc6749#section-10.12
        # https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe
        # state = secrets.token_urlsafe(32)
        # session["spotify_auth_state"] = state

        # Scopes used to set API permissions
        scope = "user-read-private user-read-playback-state user-modify-playback-state"

        # TODO: Is it secure to just use cookie as state variable? Is unique &
        # must be valid to work? If not, how to combine randomized state &
        # session ID into single string that can be passed in URL but then
        # split when received (i.e., based on legal chars)?
        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "state": request.cookies["session"],
            "scope": scope,
        }

        return redirect(f"https://accounts.spotify.com/authorize?{urlencode(params)}")
    except Exception as e:
        print("Connection error:", type(e), e)
        # Don't need if something went wrong
        session.pop("spotify_auth_state", None)
        flash("There was an error connecting to Spotify -- please try again", "danger")
        return redirect(url_for("index"))


# Response is stateless use OAuth "state" parameter to set cookie in index if
# no errors found
# https://www.oauth.com/oauth2-servers/redirect-uris/redirect-uri-registration/
@app.route("/auth-response")
def spotify_response():
    """
    Cookie included in state parameter from Spotify API
    """
    try:
        if (
            request.args.get("error")
            or not request.args.get("state")
            or not request.args.get("code")
        ):
            raise Exception(f"Spotify API error: {request.args}")

        state = str(request.args.get("state"))
        code = str(request.args.get("code"))

        response = make_response(redirect(f"{url_for('index')}?code={code}"))
        response.set_cookie(
            "session",
            value=state,
            httponly=app.config["SESSION_COOKIE_SAMESITE"],
            secure=app.config["SESSION_COOKIE_SECURE"],
            samesite=app.config["SESSION_COOKIE_SAMESITE"],
        )

        return response
    except AppError as e:
        print(type(e), str(e))
        flash(str(e), "danger")
        return redirect(url_for("index"))
    except Exception as e:
        print(type(e), str(e))
        flash("There was an error connecting to Spotify -- please try again.", "danger")
        # Log user out
        return redirect(url_for("index"))


@app.route("/disconnect-spotify")
@is_logged_in
def disconnect_spotify():
    try:
        # Remove Spotify data in cookie -- don't need to remove spotify_auth_state
        # if connected successfully -- done during Spotify API response
        clear_spotify_session()
        flash("You successfully signed out of Spotify!", "success")
    except Exception as e:
        print("Spotify disconnect error", type(e), str(e))
        flash(
            "There was an error signing you out of Spotify -- please try again",
            "danger",
        )
    finally:
        # Even if error, still a redirect -- use default code of 302
        return redirect(url_for("index"))


@app.route("/get-player-card")
@is_logged_in
def get_player_card():
    """
    Spotify player info can have 3 states: error, not playing, & playing
    Sync timer state on server to determine using property in session
    If is_timing_started (session state) & is_playing (Spotify state) out of
    sync, won't display inaccurate message in UI
    """
    try:
        if not session.get("access_token") and not session.get("refresh_token"):
            raise AppError("Spotify is not connected -- please connect & try again")

        # Need server timer state for UI
        if session.get("is_timing_started") == None:
            raise Exception("Timer state on server is effed")

        spotify_data = get_spotify_data(
            max_attempts=MAX_API_REQUEST_ATTEMPTS,
            access_token=session.get("access_token"),
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        player_data = get_player_data(
            max_attempts=MAX_API_REQUEST_ATTEMPTS,
            access_token=session.get("access_token"),
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        if not spotify_data or not player_data:
            raise AppError(
                "Spotify could not be loaded -- please ensure your credentials are correct & you have Spotify open & try again."
            )

        # Update every time player info updated to ensure timer synce with
        # player
        session["is_timing_started"] = player_data["is_playing"]

        return render_template(
            "index/spotify-card.html",
            spotify_data=spotify_data,
            player_data=player_data,
            is_timing_started=session.get("is_timing_started"),
        )
    except AppError as e:
        # TODO: Add prop to exception class for HTTP status
        # TODO: Return error HTML snippets somehow?
        print(type(e), e)
        return str(e), 400
    except Exception as e:
        print(type(e), e)
        return str(e), 500


@app.route("/toggle-playback", methods=["PUT"])
@is_logged_in
def toggle_playback():
    """Accept 'start' or 'stop' to toggle playback appropriately"""
    try:
        if not request.json or "should-start-playback" not in request.json:
            raise Exception("'should-start-playback' not submitted as JSON")

        # Whether to start or pause
        should_start_playback = request.json["should-start-playback"]

        is_spotify_connected = session.get("access_token") and session.get(
            "refresh_token"
        )

        if not is_spotify_connected:
            raise AppError(
                "Spotify is not connected -- please connect to Spotify & try again"
            )

        # Need server timer state to return
        if session.get("is_timing_started") == None:
            raise Exception("Timer state on server is effed")

        # Get current playback state
        player_state = get_player_data(
            max_attempts=MAX_API_REQUEST_ATTEMPTS,
            access_token=session.get("access_token"),
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )

        if not player_state:
            raise Exception("Player state not fetched")

        is_playing = player_state["is_playing"]
        is_toggle_necessary = should_start_playback != is_playing
        # Playback state after toggle
        final_player_state = is_playing if not is_toggle_necessary else not is_playing

        if is_toggle_necessary:
            # If opposite of desired state, call respective function to change
            toggle_status = (
                start_playback(
                    max_attempts=MAX_API_REQUEST_ATTEMPTS,
                    access_token=session.get("access_token"),
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                )
                if should_start_playback
                else pause_playback(
                    max_attempts=MAX_API_REQUEST_ATTEMPTS,
                    access_token=session.get("access_token"),
                )
            )
            if not toggle_status:
                raise Exception(f"Playback toggling unsuccessful: {toggle_status}")
            session["is_timing_started"] = not session.get("is_timing_started")

        # Toggle will be opposite of whether playing or not
        return {
            "isTimingStarted": final_player_state,
        }
    except AppError as e:
        print(type(e), e)
        return str(e), 400
    except Exception as e:
        print(type(e), e)
        return "Error toggling playback -- please try again", 500


# Settings routes

# Hard-coded vals for comparison opts
SESSION_OPTS = {
    1: {
        "work_time_secs": 750,
        "break_time_secs": 150,
    },
    2: {
        "work_time_secs": 1500,
        "break_time_secs": 300,
    },
    3: {
        "work_time_secs": 2250,
        "break_time_secs": 450,
    },
    4: {
        "work_time_secs": 3000,
        "break_time_secs": 600,
    },
}


@app.route("/settings")
@is_logged_in
def settings():
    # Populate page with session options, including work time in seconds,
    # break time in seconds, & daily session goal in seconds
    try:
        # Fetch current session goal, work time, & break time
        settings = slct_jammer_usr_sets(session.get("jammer_id"))
        if not settings:
            raise Exception("DB error")
        # Mod SESSION_OPTS to include a selected prop -- easier UI rendering
        mod_session_opts = {
            k: {
                "work_time_secs": v["work_time_secs"],
                "break_time_secs": v["break_time_secs"],
                "is_selected": (
                    True
                    if v["work_time_secs"] == settings["work_time_secs"]
                    and v["break_time_secs"] == settings["break_time_secs"]
                    else False
                ),
            }
            for k, v in SESSION_OPTS.items()
        }
        # Error if no modified opt is true -- someone effed up
        if not {k: v for k, v in mod_session_opts.items() if v["is_selected"] == True}:
            raise Exception("Invalid session option in DB")

        return render_template(
            "settings.html",
            session_opts=mod_session_opts,
            goal=settings["daily_goal_hrs"],
        )
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
    except Exception as e:
        flash("There was an error loading your settings -- please try again.", "danger")
        print(type(e), e)
    return render_template("settings.html")


@app.route("/change-password", methods=["POST"])
@is_logged_in
def change_password():
    # Generic error message for use in multiple exceptions that catch technical
    # issues
    try:
        if (
            not request.form.get("existing")
            or not request.form.get("new")
            or not request.form.get("confirm")
        ):
            raise AppError("Please submit all fields to change your password")

        existing = str(request.form.get("existing"))
        new = str(request.form.get("new"))
        confirm = str(request.form.get("confirm"))

        # Check new & confirmation match
        if new != confirm:
            raise AppError("Please ensure your confirmation matches your new password")

        # Check against regex
        if not is_valid_password(new):
            raise AppError(
                "Please enter a password between 8 & 30 chars with 1 capital, 1 lowercase, 1 numeric, & 1 non-alphanumeric characters"
            )

        # Get existing PW & compare
        existing_db = slct_jammer_pw(session.get("jammer_id"))
        if not existing_db or not existing_db["jammer_pw"]:
            raise Exception("Could not get password from DB")

        # Old PW invalid
        elif not check_password_hash(existing_db["jammer_pw"], existing):
            raise AppError("Please submit a valid existing password")

        # New PW identical to old
        elif check_password_hash(existing_db["jammer_pw"], new):
            raise AppError("Please submit a new password")

        # Hash for storage
        new_hashed = generate_password_hash(new)
        if not new_hashed:
            raise Exception("Could not hash password")

        # Update password -- will raise exception if error
        updt_jammer_pw(session.get("jammer_id"), new_hashed)

        # Handle errors
        flash("Password changed successfully", "success")

    # TODO: Don't log user out on errors -- can't flash messages, not necessary
    # for security, & not optimal UX?
    except AppError as e:
        flash(str(e), "danger")
        print("Logic error: ", type(e), e)
    # TODO: Handle any other exceptions differently? Like Syntax errors?
    except Exception as e:
        flash("There was an error changing your password -- please try again", "danger")
        print(type(e), e)

    # Uses default code of 302
    return redirect(url_for("settings"))


@app.route("/change-session-settings", methods=["POST"])
@is_logged_in
def change_session_settings():
    try:
        if not request.form.get("session-opt") or not request.form.get("daily-goal"):
            raise AppError(
                "Please submit a session time option & daily session goal to update your session settings."
            )

        session_opt = int(str(request.form.get("session-opt")))
        if session_opt not in SESSION_OPTS.keys():
            raise AppError(
                f"Please submit an option between 1 & {len(SESSION_OPTS)} to change your session duration"
            )
        selected_session = SESSION_OPTS[session_opt]

        # Ensure session goal valid
        new_daily_goal = int(str(request.form.get("daily-goal")))
        min_sesh_goal = 1
        max_sesh_goal = 8
        if new_daily_goal < min_sesh_goal or new_daily_goal > max_sesh_goal:
            raise AppError(
                f"Please submit a valid daily session goal between {min_sesh_goal} & {max_sesh_goal}"
            )

        # Update session settings
        updt_jammer_pom_sets(
            session.get("jammer_id"),
            selected_session["work_time_secs"],
            selected_session["break_time_secs"],
            new_daily_goal,
        )

        flash("Session settings updated successfully", "success")
    except AppError as e:
        flash(str(e), "danger")
        print("Biz logic error:", type(e), e)
    # TODO: Handle any other exceptions differently? Like Syntax errors?
    except Exception as e:
        flash(
            "There was an error updating your session settings -- please try again",
            "danger",
        )
        print(type(e), e)
    # Default code of 302
    return redirect(url_for("settings"))


# To Do routes


@app.route("/todos")
@is_logged_in
def todos():
    todos = slct_todo_todos(session.get("jammer_id"))
    return render_template(
        "todos.html", jammer_id=session.get("jammer_id"), todos=todos
    )


@app.route("/add-todo", methods=["POST"])
@is_logged_in
def add_todo():
    """Appends a form-submitted To Do to the user's list of active To Dos"""
    try:
        if not request.form.get("todo"):
            raise AppError("Please submit a valid To Do")

        new_todo = str(request.form.get("todo"))
        if len(new_todo) > 50:
            raise AppError("Please submit a valid To Do no more than 50 characters")

        insert_todo(session.get("jammer_id"), new_todo)

        flash("To Do added successfully!!!", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an error adding your To Do -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/complete-all-todos", methods=["POST"])
@is_logged_in
def complete_all_todos():
    try:
        if not request.form.get("jammer"):
            raise Exception("Jammer ID missing from request")
        jammer_id = str(request.form.get("jammer"))
        result = updt_todo_cmplt_all(jammer_id=jammer_id, completed_date=date.today())
        print(result)
        flash("To Dos updated successfully!!!", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an error updating your To Dos -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/delete-all-todos", methods=["POST"])
@is_logged_in
def delete_all_todos():
    try:
        if not request.form.get("jammer"):
            raise Exception("Jammer ID missing from request")
        jammer_id = str(request.form.get("jammer"))
        result = delete_todo_all_incmplt(jammer_id=jammer_id)
        print(result)
        flash("To Dos updated successfully!!!", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an error updating your To Dos -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/move-todo-first", methods=["POST"])
@is_logged_in
def move_todo_first():
    try:
        if not request.form.get("todo"):
            raise AppError("Please submit a valid To Do")
        todo_id = int(str(request.form.get("todo")))
        updt_todo_lst_ord(session.get("jammer_id"), todo_id, "first")
        flash("To Do moved successfully", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an moving your To Do -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/move-todo-up", methods=["POST"])
@is_logged_in
def move_todo_up():
    try:
        if not request.form.get("todo"):
            raise AppError("Please submit a valid To Do")
        todo_id = int(str(request.form.get("todo")))
        updt_todo_lst_ord(session.get("jammer_id"), todo_id, "up")
        flash("To Do moved successfully", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an moving your To Do -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/move-todo-down", methods=["POST"])
@is_logged_in
def move_todo_down():
    try:
        if not request.form.get("todo"):
            raise AppError("Please submit a valid To Do")
        todo_id = int(str(request.form.get("todo")))
        updt_todo_lst_ord(session.get("jammer_id"), todo_id, "down")
        flash("To Do moved successfully", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an moving your To Do -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/move-todo-last", methods=["POST"])
@is_logged_in
def move_todo_last():
    try:
        if not request.form.get("todo"):
            raise AppError("Please submit a valid To Do")
        todo_id = int(str(request.form.get("todo")))
        updt_todo_lst_ord(session.get("jammer_id"), todo_id, "last")
        flash("To Do moved successfully", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an moving your To Do -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))


@app.route("/complete-todo", methods=["POST", "PATCH"])
@is_logged_in
def complete_todo():
    """Mark a To Do as complete -- POST for HTML form, PUT for fetch request"""
    try:
        if not request.form.get("todo"):
            raise Exception("To Do ID not submitted")
        todo_id = int(str(request.form.get("todo")))
        updt_todo_cmplt_one(todo_id, date.today())
        if request.method == "POST":
            flash("To Do complete!!!", "success")
            return redirect(url_for("todos"))
        # Get next To Do in list
        next_todo = slct_todo_next_for_jammer(session.get("jammer_id"))
        return render_template("complete-todo.html", next_todo=next_todo)
    except AppError as e:
        print(type(e), e)
        if request.method == "POST":
            flash(str(e), "danger")
            return redirect(url_for("todos"))
        return 500
    except Exception as e:
        print(type(e), e)
        if request.method == "POST":
            flash(
                "There was an error updating your To Dos -- please try again", "danger"
            )
            return redirect(url_for("todos"))
        return 500


@app.route("/delete-todo", methods=["POST"])
@is_logged_in
def delete_todo():
    try:
        if not request.form.get("todo"):
            raise Exception("To Do ID not submitted")
        todo_id = int(str(request.form.get("todo")))
        delete_todo_one(todo_id)
        flash("To Do removed!!!", "success")
        return redirect(url_for("todos"))
    except AppError as e:
        flash(str(e), "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
    except Exception as e:
        flash("There was an error updating your To Dos -- please try again", "danger")
        print(type(e), e)
        return redirect(url_for("todos"))
