# SkipSpotify

Decrease overplaying and song burnout through being able to automatically skip specific songs when they play on Spotify.

The main use case is when you are not able to access Spotify, however, this application can run in the background and check which songs are being played and skip specific songs.

Needs to be run in a Flask environment
Execute the following commands for set up:

python -m venv myenv

source myenv/bin/activate

pip install flask

pip install requests

flask run

Add the app.py file to folder with the Flask environment before deploying with "flask run"
