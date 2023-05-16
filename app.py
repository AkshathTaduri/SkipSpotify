from flask import Flask, redirect, url_for, request, session
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_spotify_auth_url():
    # Set the necessary parameters
    client_id = "0e5f3f9d809947ac852061c20cf62a7d"
    redirect_uri = "http://127.0.0.1:8080/callback"
    scope = "user-read-private user-read-email user-read-currently-playing user-read-playback-state user-modify-playback-state"  # Add the 'user-read-currently-playing' scope
    state = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")

    # Store the state in the session
    session["state"] = state

    # Construct the authorization URL
    auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}&state={state}"

    return auth_url


def get_access_token(auth_code):
    # Set the necessary parameters
    client_id = "0e5f3f9d809947ac852061c20cf62a7d"
    client_secret = "302ffe05915c4ac5bc614def43ff8ac1"
    redirect_uri = "http://127.0.0.1:8080/callback"

    # Construct the POST request to exchange the authorization code for an access token
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic "
        + base64.b64encode((client_id + ":" + client_secret).encode("utf-8")).decode(
            "utf-8"
        )
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
    }

    # Send the POST request to exchange the authorization code for an access token
    response = requests.post(token_url, headers=headers, data=data)
    response_data = response.json()

    # Retrieve the access token from the response
    access_token = response_data.get("access_token")

    return access_token


def skip_current_song(access_token, device_id):
    # Set the headers with the access token
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get the currently playing track
    current_track_url = "https://api.spotify.com/v1/me/player/currently-playing"
    response = requests.get(current_track_url, headers=headers)
    response_data = response.json()

    # Check if a track is currently playing
    if "item" in response_data:
        track_name = response_data["item"]["name"]

        # Check if the current track name matches "ORANGE SODA"
        if track_name.lower() == "orange soda":
            # Skip the current track
            skip_url = (
                f"https://api.spotify.com/v1/me/player/next?device_id={device_id}"
            )
            skip_response = requests.post(skip_url, headers=headers)

            # Check if the song was skipped successfully
            if skip_response.status_code == 204:
                return True
            else:
                return False

    return False


@app.route("/")
def index():
    # Generate the Spotify authorization URL
    auth_url = get_spotify_auth_url()

    # Redirect the user to the Spotify authorization URL
    return redirect(auth_url)


@app.route("/callback")
def callback():
    # Verify the state parameter to prevent CSRF attacks
    if request.args.get("state") != session["state"]:
        return "Error: Invalid state parameter"

    # Retrieve the authorization code from the query parameters
    auth_code = request.args.get("code")

    # Exchange the authorization code for an access token
    access_token = get_access_token(auth_code)

    # Store the access token in the session
    session["access_token"] = access_token

    # Redirect the user to a new page after successful login
    return redirect(url_for("dashboard"))


from apscheduler.schedulers.background import BackgroundScheduler


def skip_current_song(access_token, device_id):
    print("Starting scheduler...")
    headers = {"Authorization": f"Bearer {access_token}"}

    def check_and_skip_song():
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing", headers=headers
        )
        response_data = response.json()

        if "item" in response_data:
            track_name = response_data["item"]["name"]

            if track_name.lower() == "orange soda":
                print("Found ORANGE SODA")
                skip_url = (
                    f"https://api.spotify.com/v1/me/player/next?device_id={device_id}"
                )
                skip_response = requests.post(skip_url, headers=headers)

                if skip_response.status_code == 204:
                    print("Skipped the current song: ORANGE SODA")
                else:
                    print("Failed to skip the current song: ORANGE SODA")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_and_skip_song, "interval", seconds=5
    )  # Adjust the interval as needed
    scheduler.start()


@app.route("/dashboard")
def dashboard():
    # Retrieve the access token from the session
    access_token = session.get("access_token")

    # Set the headers with the access token
    headers = {"Authorization": f"Bearer {access_token}"}

    # Make the GET request to retrieve the user's available devices
    response = requests.get(
        "https://api.spotify.com/v1/me/player/devices", headers=headers
    )
    response_data = response.json()

    # Check the response for available devices
    if "devices" in response_data:
        devices = response_data["devices"]
        # only use the first device
        device_id = devices[0]["id"]
        skip_current_song(access_token, device_id)

    if access_token:
        # Make a GET request to the Spotify API to get the user's currently playing track
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing", headers=headers
        )

        if response.status_code == 200:
            # The user is currently playing a song
            song_data = response.json()
            song_name = song_data["item"]["name"]
            artists = ", ".join(
                [artist["name"] for artist in song_data["item"]["artists"]]
            )
            return f"Currently playing: {song_name} by {artists}"
        else:
            # The user is not currently playing a song
            return "No song is currently playing."
    else:
        return "Error: Access token not found"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
