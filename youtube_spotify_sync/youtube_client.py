import requests
import youtube_spotify_sync.app_secrets as app_secrets
import json
import re

class YoutubeClient:

    def __init__(self, playlist, code=None, refresh_token=None, code_verifier=None):
        self.code = code
        self.refresh_token = refresh_token
        self.code_verifier = code_verifier
        self.playlist = playlist

    #Sync Authentication
    def _get_user_tokens(self):
        client_id = app_secrets.youtube_client_id
        client_secret = app_secrets.youtube_client_secret
        endpoint = "https://oauth2.googleapis.com/token"
        exchange_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": self.code,
            "code_verifier": self.code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": "http://127.0.0.1:5000"
        }
        res = requests.post(endpoint, data=exchange_data)

        with open("temp/youtube_tokens.json", "w", encoding="utf-8") as file:
            json.dump(res.json(), file, indent=4)

    def _refresh_access_token(self):
        client_id = app_secrets.youtube_client_id
        client_secret = app_secrets.youtube_client_secret
        endpoint = "https://oauth2.googleapis.com/token"
        refresh_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        res = requests.post(endpoint, data=refresh_data)
        res_dict = res.json()

        #May not need if refresh token saved in environment variable
        res_dict["refresh_token"] = self.refresh_token

        with open("temp/youtube_tokens.json", "w", encoding="utf-8") as file:
            json.dump(res_dict, file, indent=4)

    def _get_access_token(self):
        with open("temp/youtube_tokens.json", "r") as file:
            tokens_dict = json.load(file)
        access_token = tokens_dict["access_token"]
        return access_token

    def _get_refresh_token(self):
        with open("temp/youtube_tokens.json", "r") as file:
            tokens_dict = json.load(file)
        if "refresh_token" in tokens_dict.keys():
            refresh_token = tokens_dict["refresh_token"]
            return refresh_token

    def _create_refresh_token_file(self):
        with open("temp/youtube_refresh.txt", "w") as file:
            refresh_token = self._get_refresh_token()
            file.write(refresh_token)

    def authenticate(self):
        if self.code:
            self._get_user_tokens()
            self._create_refresh_token_file()
        else:
            self._refresh_access_token()
        self.access_token = self._get_access_token()

    #Sync Implementation

    def playlist_exists(self):
        endpoint = f"https://www.googleapis.com/youtube/v3/playlists"
        headers = {
            "Authorization": "Bearer "+self.access_token,
        }
        payload = {
            "part": "id,snippet",
            "mine": "true"
        }
        res = requests.get(endpoint, headers=headers, params=payload)
        res =  res.json()
        for playlist in res["items"]:
            if playlist["snippet"]["title"] == self.playlist:
                self.playlist_id = playlist["id"]
                return True
        return False

    def get_playlist_videos(self):
        endpoint = f"https://www.googleapis.com/youtube/v3/playlistItems"
        headers = {
            "Authorization": "Bearer "+self.access_token,
        }
        payload = {
            "part": "snippet",
            "playlistId": self.playlist_id,
            "maxResults": 50
        }
        res = requests.get(endpoint, headers=headers, params=payload)
        res = res.json()
        if res["items"]:
            video_list = res["items"]
            while "nextPageToken" in res.keys():
                next_page_res = self._add_videos_on_next_page(res["nextPageToken"])
                if next_page_res["items"]:
                    video_list += next_page_res["items"]
                res = next_page_res
            videos = [video["snippet"]["title"] for video in video_list]
            return videos

    def _add_videos_on_next_page(self, next_page_token):
        endpoint = f"https://www.googleapis.com/youtube/v3/playlistItems"
        headers = {
            "Authorization": "Bearer "+self.access_token,
        }
        payload = {
            "part": "snippet",
            "playlistId": self.playlist_id,
            "maxResults": 50,
            "pageToken": next_page_token
        }
        res = requests.get(endpoint, headers=headers, params=payload)
        return(res.json())

    def extract_videos_details(self, videos_list):
        videos = []
        for video in videos_list:
            title_split = re.split(" - | – ", video)
            artists = title_split[0]
            song_title = title_split[1]
            artist = artists.split(",")[0]
            if ("[" in song_title) or ("(" in song_title):
                song_title = re.split(" \(| \[", song_title)[0]
            if " ft. " in song_title:
                song_title = song_title.split( " ft. " )[0]
            videos.append([artist, song_title])
        return(videos)

