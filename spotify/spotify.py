import requests
import time
import webbrowser
from utils.logger import logger
from utils.env_manager import load_env_variables, save_env_variable

ACCESS_TOKEN_URL = "https://accounts.spotify.com/api/token"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "playlist-modify-private user-read-private"

class Spotify:
    def __init__(self, date, file_path):
        self.date = date
        self.file_path = file_path
        self.playlist_id = None
        self.song_uris = []

        self.env_vars = load_env_variables()

        if not self.env_vars["ACCESS_TOKEN"]:
            self._authorize_user()
        else:
            if not self._test_access_token():
                self._refresh_access_token()

        if not self.env_vars["USER_ID"]:
            self._get_user_id()

    def _authorize_user(self):
        auth_url = f"{AUTHORIZE_URL}?client_id={self.env_vars['CLIENT_ID']}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}"
        logger.info(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)
        auth_code = input("Enter the authorization code from the redirected URL: ")
        self._get_access_token(auth_code)

    def _get_access_token(self, code):
        access_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": self.env_vars["CLIENT_ID"],
            "client_secret": self.env_vars["CLIENT_SECRETE"]
        }
        self._request_token(ACCESS_TOKEN_URL, access_data, "Access and Refresh Tokens")

    def _refresh_access_token(self):
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.env_vars["REFRESH_TOKEN"],
            "client_id": self.env_vars["CLIENT_ID"],
            "client_secret": self.env_vars["CLIENT_SECRETE"]
        }
        self._request_token(ACCESS_TOKEN_URL, refresh_data, "Access Token refreshed")

    def _request_token(self, url, data, success_msg):
        try:
            response = requests.post(url=url, data=data)
            response.raise_for_status()
            response_data = response.json()
            save_env_variable("ACCESS_TOKEN", response_data.get("access_token"))
            if "refresh_token" in response_data:
                save_env_variable("REFRESH_TOKEN", response_data.get("refresh_token"))
            logger.info(f"{success_msg} and saved in .env successfully")
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")

    def _test_access_token(self):
        test_url = "https://api.spotify.com/v1/me"
        headers = {"Authorization": f"Bearer {self.env_vars['ACCESS_TOKEN']}"}
        response = requests.get(url=test_url, headers=headers)
        return response.status_code == 200

    def _get_user_id(self):
        user_id_url = "https://api.spotify.com/v1/me"
        headers = {"Authorization": f"Bearer {self.env_vars['ACCESS_TOKEN']}"}

        try:
            time.sleep(1)
            response = requests.get(url=user_id_url, headers=headers)
            response.raise_for_status()
            user_id = response.json().get("id")
            save_env_variable("USER_ID", user_id)
            logger.info("User ID saved in .env successfully.")
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred while getting user ID: {http_err}")
        except Exception as err:
            logger.error(f"An unexpected error occurred while getting user ID: {err}")

    def create_playlist(self):
        create_playlist_url = f"https://api.spotify.com/v1/users/{self.env_vars['USER_ID']}/playlists"
        headers = {"Authorization": f"Bearer {self.env_vars['ACCESS_TOKEN']}", "Content-Type": "application/json"}
        data = {"name": f"{self.date} / Top 100 Songs", "description": f"Top 100 songs on {self.date}", "public": False}

        try:
            response = requests.post(url=create_playlist_url, headers=headers, json=data)
            response.raise_for_status()
            playlist_id = response.json().get("id")
            return playlist_id
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred while creating playlist: {http_err}")
        except Exception as err:
            logger.error(f"An unexpected error occurred while creating playlist: {err}")
        return None

    def add_tracks(self, playlist_id):
        self.playlist_id = playlist_id
        logger.info("Starting the process to add tracks.")

        try:
            self._get_track_uris()
            time.sleep(5)
            self._add_tracks_to_playlist()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add tracks to playlist: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding tracks to playlist: {e}")

    def _get_track_uris(self):
        def search_song(track_name):
            search_url = f"https://api.spotify.com/v1/search?q={track_name}&type=track"
            headers = {"Authorization": f"Bearer {self.env_vars['ACCESS_TOKEN']}"}

            try:
                response = requests.get(search_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                if data["tracks"]["items"]:
                    return data["tracks"]["items"][0]["uri"]
                logger.warning(f"No tracks found for '{track_name}'")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for track '{track_name}': {e}")
                return None

        with open(self.file_path, "r", encoding="UTF-8") as file:
            songs = file.read().splitlines()

        self.song_uris = [uri for uri in (search_song(name) for name in songs) if uri]
        logger.info(f"Successfully retrieved URIs for {len(self.song_uris)} tracks")

    def _add_tracks_to_playlist(self):
        add_tracks_url = f"https://api.spotify.com/v1/playlists/{self.playlist_id}/tracks"
        headers = {"Authorization": f"Bearer {self.env_vars['ACCESS_TOKEN']}", "Content-Type": "application/json"}
        chunk_size = 100  # Spotify API allows adding max 100 tracks at once

        for i in range(0, len(self.song_uris), chunk_size):
            uris_chunk = self.song_uris[i:i + chunk_size]
            data = {"uris": uris_chunk}

            try:
                response = requests.post(url=add_tracks_url, headers=headers, json=data)
                response.raise_for_status()
                logger.info(f"Successfully added {len(uris_chunk)} tracks to playlist")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to add tracks to playlist: {e}")

