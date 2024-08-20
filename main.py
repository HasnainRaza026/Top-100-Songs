import os
import json
from songs.get_songs import Songs
from spotify.spotify import Spotify
from utils.logger import logger

PLAYLIST_ID_PATH = "./playlist_id.json"


def main():
    date = input("Enter date in the format YYYY-MM-DD: ")
    file_path = f"./{date}_top_100_songs.txt"

    if not os.path.isfile(file_path):
        songs = Songs(date)
        song_titles = songs.get_100_songs()
        if not song_titles:
            logger.info("Program returned empty song titles")
            return
        save_songs_to_file(file_path, song_titles)
    else:
        logger.info(f"List of top 100 songs on {date} already exists")

    playlist_id = get_playlist_id(date)
    if not playlist_id:
        spotify = Spotify(date, file_path)
        playlist_id = spotify.create_playlist()
        if playlist_id:
            save_playlist_id(date, playlist_id)
            spotify.add_tracks(playlist_id)
        else:
            logger.info("Program returned empty playlist id")
    else:
        logger.info(f"Playlist for {date} already exists in Spotify.")


def save_songs_to_file(file_path, songs):
    with open(file_path, "w", encoding="UTF-8") as file:
        for song in songs:
            file.write(song + "\n")


def get_playlist_id(date):
    with open(PLAYLIST_ID_PATH, 'r') as file:
        data = json.load(file)
    return data.get(date)


def save_playlist_id(date, playlist_id):
    with open(PLAYLIST_ID_PATH, 'r+') as file:
        data = json.load(file)
        data[date] = playlist_id
        file.seek(0)
        json.dump(data, file, indent=4)


if __name__ == '__main__':
    main()
