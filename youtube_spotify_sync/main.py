import requests
import sys
import os
from youtube_spotify_sync.youtube_client import YoutubeClient
from youtube_spotify_sync.spotify_client import SpotifyClient
import json

def get_spotify_code():
    with open('temp/spotify_code.txt', 'r') as file:
        lines = file.read().split("\n")
        code = lines[0]
        error = lines[1]
        state = lines[2]
        return(code, error, state)

def get_youtube_code():
    with open('temp/youtube_code.txt', 'r') as file:
        lines = file.read().split("\n")
        code_verifier = lines[0]
        code = lines[1]
        error = lines[2]
        return(code_verifier, code, error)

def check_all_tracks_found(youtube_playlist, tracks_not_found):
    if tracks_not_found:
        print(f"The following tracks in the YouTube playlist {youtube_playlist} were not found on Spotify:")
        print("##########################################")
        for artist,track in tracks_not_found:
            print(f"{artist} - {track}")
        print("##########################################")


def check_and_sync(youtube_playlist, spotify_client, spotify_playlist, spotify_playlist_id, existing_track_uris, updated_track_uris):
    deleted_track_uris = list(set(existing_track_uris) - set(updated_track_uris))
    added_track_uris = list(set(updated_track_uris) - set(existing_track_uris))
    if added_track_uris and deleted_track_uris:
        print("New tracks found. Adding tracks...")
        grouped_added_track_uris = spotify_client.group_track_uris(added_track_uris)
        spotify_client.add_tracks_to_playlist(grouped_added_track_uris, spotify_playlist_id)
        print(f"WARNING Tracks also deleted from {youtube_playlist} therefore deleting tracks in {spotify_playlist}...")
        grouped_deleted_track_uris = spotify_client.group_track_uris(deleted_track_uris, True)
        spotify_client.delete_tracks_from_playlist(grouped_deleted_track_uris, spotify_playlist_id)
    elif added_track_uris:
        print("New tracks found. Adding tracks...")
        grouped_track_uris = spotify_client.group_track_uris(added_track_uris)
        spotify_client.add_tracks_to_playlist(grouped_track_uris, spotify_playlist_id)
    elif deleted_track_uris:
        print(f"WARNING Tracks deleted from {youtube_playlist} therefore sync will delete tracks in {spotify_playlist}")
        grouped_track_uris = spotify_client.group_track_uris(deleted_track_uris, True)
        spotify_client.delete_tracks_from_playlist(grouped_track_uris, spotify_playlist_id)
    else:
        print("No changes to sync")

def run():
    youtube_playlist = sys.argv[1]
    spotify_playlist = sys.argv[2]
    if ("SPOTIFY_REFRESH_TOKEN" in os.environ.keys()) and ("YOUTUBE_REFRESH_TOKEN" in os.environ.keys()):
        spotify_refresh_token = os.environ['SPOTIFY_REFRESH_TOKEN']
        youtube_refresh_token = os.environ['YOUTUBE_REFRESH_TOKEN']
        spotify = SpotifyClient(spotify_playlist, refresh_token=spotify_refresh_token)
        youtube = YoutubeClient(youtube_playlist, refresh_token=youtube_refresh_token)
    else:
        spotify_code, spotify_error,spotify_state = get_spotify_code()
        code_verifier, youtube_code, youtube_error = get_youtube_code()
        if spotify_error == "None" and youtube_error == "None":
            spotify = SpotifyClient(spotify_playlist, code=spotify_code)
            youtube = YoutubeClient(youtube_playlist, code=youtube_code, code_verifier=code_verifier)
        else:
            print("Unfortunately, You denied this program access to your Spotify or Youtube account. Exiting Program")
            raise SystemExit

    print("Starting Sync...")
    youtube.authenticate()
    print(f"Checking if YouTube playlist {youtube_playlist} exists...")
    if youtube.playlist_exists():
        print(f"Fetching videos from YouTube playlist {youtube_playlist}...")
        videos = youtube.get_playlist_videos()
        video_details = youtube.extract_videos_details(videos)
        print("Videos processed and track details extracted")
    else:
        print(f"The YouTube playlist you've provided ({youtube_playlist}) doesn't exist. Exiting Program")
        raise SystemExit

    spotify.authenticate()
    user_id = spotify.set_user_id()
    print(f"Checking if Spotify playlist {spotify_playlist} exists...")
    spotify_playlist_id = spotify.playlist_exists(user_id)
    if spotify_playlist_id:
        print(f"WARNING The Spotify playlist {spotify_playlist} already exists")
        existing_track_uris = spotify.get_tracks_in_playlist(spotify_playlist_id)
        print("Finding tracks on Spotify...")
        updated_track_uris, tracks_not_found = spotify.find_tracks_on_spotify(video_details)
        print("Checking for changes...")
    else:
        print(f"Creating the Spotify playlist {spotify_playlist}...")
        spotify_playlist_id = spotify.create_playlist(user_id)
        print(f"Spotify playlist {spotify_playlist} created")
        existing_track_uris = []
        print("Finding tracks on Spotify...")
        updated_track_uris, tracks_not_found = spotify.find_tracks_on_spotify(video_details)

    check_all_tracks_found(youtube_playlist, tracks_not_found)
    check_and_sync(youtube_playlist, spotify, spotify_playlist, spotify_playlist_id, existing_track_uris, updated_track_uris)
    print("Sync Complete")

if __name__ == "__main__":
    run()
