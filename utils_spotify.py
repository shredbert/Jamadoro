from flask import (
    redirect,
    session,
    url_for,
)

# Make requests to Spotify API
# https://requests.readthedocs.io/en/latest/user/quickstart/#passing-parameters-in-urls
import requests

from utils_general import clear_spotify_session

# TODO: Research b64 encoding issue below
# import base64


def load_tokens(redirect_uri, client_id, client_secret, code):
    url = "https://accounts.spotify.com/api/token"
    # TODO: Passing encoded string in header not working -- use in body
    # instead:
    # https://stackoverflow.com/questions/53567858/spotify-api-error-invalid-client-authorization-code-flow-400
    # auth_encoded = base64.b64encode(f"{client_id}:{client_secret}".encode())
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        # "Authorization": f"Basic {auth_encoded}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    token_request = requests.post(url, headers=headers, data=data)
    if token_request.status_code != 200:
        raise Exception("Failed request from Spotify API")
    session["access_token"] = token_request.json()["access_token"]
    session["refresh_token"] = token_request.json()["refresh_token"]


def refresh_token(client_id, client_secret):
    # Call refresh function if any other request receives Spotify expiry error
    # Not own route since called by other routes after requests denied
    # https://www.oauth.com/oauth2-servers/making-authenticated-requests/refreshing-an-access-token/

    # Error if refresh token somehow deleted -- shouldn't be unless signed out
    if not session.get("refresh_token"):
        print("Spotify credentials missing -- re-connecting...")
        return redirect(url_for("connect_spotify"))

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": session.get("refresh_token"),
        "client_id": client_id,
        "client_secret": client_secret,
    }

    token_request = requests.post(url, headers=headers, data=data)

    # Bad response from token refresh request -- sign out
    if token_request.status_code != 200:
        clear_spotify_session()
        return

    data = token_request.json()

    session["access_token"] = data["access_token"]
    return


def get_spotify_data(max_attempts, access_token, client_id, client_secret):
    """
    Max attempts for how many times to try if fail, access token only -- refresh
    handled independently
    https://developer.spotify.com/documentation/web-api/reference/get-current-users-profile
    https://developer.spotify.com/documentation/web-api/reference/get-information-about-the-users-current-playback
    """
    spotify_data = {}
    attempts = 0

    # Do in loop in case have to repeat due to expired token
    while True:
        attempts += 1
        if attempts == max_attempts:
            break

        # Endpoints: Device checked for active player & user for Spotify
        # account info, plus most recently played for when no player context
        spotify_devices_endpoint = "https://api.spotify.com/v1/me/player/devices"
        spotify_user_endpoint = "https://api.spotify.com/v1/me"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Both return 200 for success, 401 for bad token, 403 for invalid
        # request, & 429 for exceeded rate limits
        spotify_devices_request = requests.get(
            spotify_devices_endpoint, headers=headers
        )
        spotify_user_request = requests.get(spotify_user_endpoint, headers=headers)

        # Refresh token if 401 status returned from any endpoints & try again
        if (
            spotify_devices_request.status_code == 401
            or spotify_user_request.status_code == 401
        ):
            refresh_token(client_id=client_id, client_secret=client_secret)
        # Break if any other server errors
        elif (
            spotify_devices_request.status_code > 399
            and spotify_devices_request.status_code < 600
        ) or (
            spotify_user_request.status_code > 399
            and spotify_user_request.status_code < 600
        ):
            break
        # Handle successful responses
        elif (
            spotify_devices_request.status_code == 200
            and spotify_user_request.status_code == 200
        ):
            # Available devices

            # Only return devices that aren't restricted
            # Sort by type to prioritize computer, then mobile, then others if
            # need to transfer playback
            spot_devices = sorted(
                [
                    d
                    for d in spotify_devices_request.json()["devices"]
                    if not d["is_restricted"]
                ],
                key=lambda d: (
                    d["type"].lower(),
                    d["type"].lower() == "smartphone",
                    d["type"].lower() == "computer",
                ),
            )

            # Check for active devices
            # TODO: Assuming only 1 connected device can be active at a time --
            # may need to verify
            spot_active = [d for d in spot_devices if d["is_active"]]
            # If none active, transfer playback to one of available & get
            # player data again
            if spot_devices and not spot_active:
                print(
                    "No active player but players available -- transferring playback..."
                )
                spotify_transfer_url = "https://api.spotify.com/v1/me/player"
                headers["Content-Type"] = "application/json"
                json = {
                    "device_ids": [
                        spot_devices[0]["id"],
                    ],
                }
                spotify_transfer_request = requests.put(
                    spotify_transfer_url, headers=headers, json=json
                )
                # If successful, re-try attempt
                if spotify_transfer_request.status_code == 204:
                    print("Playback transferred -- re-checking device stuff...")
                    attempts -= 1

            # User's username
            spot_user = spotify_user_request.json()["display_name"]

            if spot_active and spot_user:
                spotify_data["device"] = spot_active[0]["name"]
                spotify_data["user"] = spot_user
                break
        else:
            break
    return spotify_data


def get_player_data(max_attempts, access_token, client_id, client_secret):
    """
    Max attempts for how many times to try if fail, access token only -- refresh
    handled independently
    https://developer.spotify.com/documentation/web-api/reference/get-current-users-profile
    https://developer.spotify.com/documentation/web-api/reference/get-information-about-the-users-current-playback
    """
    player_data = {}
    attempts = 0

    # Do in loop in case have to repeat due to expired token
    while True:
        attempts += 1
        if attempts == max_attempts:
            break

        # Player endpoint for currently playing if open
        spotify_player_endpoint = "https://api.spotify.com/v1/me/player"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Returns 200 for success, 204 if not playing, 401 for bad token, 403
        # for invalid request, & 429 for exceeded rate limits
        spotify_player_request = requests.get(spotify_player_endpoint, headers=headers)

        # Refresh token if 401 status returned from any endpoints & try again
        if spotify_player_request.status_code == 401:
            refresh_token(client_id=client_id, client_secret=client_secret)
        # TODO: Handle rate limit (429) errors explicitly by parsing
        # "Retry-After" value & trying again
        # Break if any other server errors
        elif (
            spotify_player_request.status_code > 399
            and spotify_player_request.status_code < 600
        ):
            break
        # Handle successful responses
        else:
            spotify_player_data = None

            # If request returns 204, nothing currently playing & no data
            # returned
            if spotify_player_request.status_code == 204:
                break

            # Player data if playing
            spotify_player_data = spotify_player_request.json()

            # Always available if data returned
            player_data["device"] = spotify_player_data["device"]["name"]
            player_data["is_playing"] = spotify_player_data["is_playing"]

            # Not always available -- device may be active but no song playing
            if spotify_player_data["item"]:
                player_data["song"] = spotify_player_data["item"]["name"]
                player_data["artists"] = list(
                    map(
                        lambda artist: artist["name"],
                        spotify_player_data["item"]["artists"],
                    )
                )
                player_data["album"] = spotify_player_data["item"]["album"]["name"]
                player_data["image"] = list(
                    filter(
                        lambda image: image["height"] == 300,
                        spotify_player_data["item"]["album"]["images"],
                    )
                )[0]
            break
    return player_data


def start_playback(max_attempts, access_token, client_id, client_secret):
    """
    Start track playback, either resuming if session started or starting new
    session with last played track if can't resume
    Client ID & Client Secret required for fetching most recent track in edge
    case
    """
    attempts = 0

    while True:
        attempts += 1
        if attempts == max_attempts:
            break

        url = "https://api.spotify.com/v1/me/player/play"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        change_request = requests.put(url, headers=headers)

        """
        204 = success
        401 = expired token
        403 = unknown error but quite common if changing state but
        state already exists (e.g., pause when already paused)
        404 = (likely) no player context found???
        429 = rate limit exceeded
        TODO: Handle 429 explicitly -- rate limit exceeded, need to monitor
        timeout
        """
        if change_request.status_code == 204:
            return True
        elif change_request.status_code == 401:
            refresh_token(client_id=client_id, client_secret=client_secret)
    return False


def pause_playback(max_attempts, access_token):
    """
    Pause playback and return whether successful or not
    TODO: If can't pause due to already paused, return True?
    """
    attempts = 0

    while True:
        attempts += 1
        if attempts == max_attempts:
            break
        url = "https://api.spotify.com/v1/me/player/pause"

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        change_request = requests.put(url, headers=headers)

        """
        204 = success
        401 = expired token
        403 = unknown error but quite common if changing state but
        state already exists (e.g., pause when already paused)
        404 = (likely) no player context found???
        429 = rate limit exceeded
        TODO: Handle 429 explicitly -- rate limit exceeded, need to monitor
        timeout
        """
        if change_request.status_code == 204:
            return True
    return False
