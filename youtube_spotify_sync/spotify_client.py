import requests
import youtube_spotify_sync.app_secrets as app_secrets
import json
import base64

class SpotifyClient:

    def __init__(self, playlist, code=None, refresh_token=None):
        self.code = code
        self.refresh_token = refresh_token
        self.playlist = playlist

    #Sync Authentication
    def _get_user_tokens(self):
        client_id = app_secrets.spotify_client_id
        client_key = app_secrets.spotify_client_key
        client_pair = f"{client_id}:{client_key}"
        encoded_client_pair = base64.b64encode(client_pair.encode())
        endpoint = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {encoded_client_pair.decode('utf-8')}"
        }
        exchange_data = {
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": "http://localhost:5000/callback"
        }
        res = requests.post(endpoint, headers=headers, data=exchange_data)

        with open("temp/spotify_tokens.json", "w", encoding="utf-8") as file:
            json.dump(res.json(), file, indent=4)

    def _refresh_access_token(self):
        client_id = app_secrets.spotify_client_id
        client_key = app_secrets.spotify_client_key
        client_pair = f"{client_id}:{client_key}"
        encoded_client_pair = base64.b64encode(client_pair.encode())
        endpoint = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {encoded_client_pair.decode('utf-8')}"
        }
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        res = requests.post(endpoint, headers=headers, data=refresh_data)
        res_dict = res.json()
        res_dict["refresh_token"] = self.refresh_token

        with open("temp/spotify_tokens.json", "w", encoding="utf-8") as file:
            json.dump(res_dict, file, indent=4)

    def _get_access_token(self):
        with open("temp/spotify_tokens.json", "r") as file:
            tokens_dict = json.load(file)
        access_token = tokens_dict["access_token"]
        return access_token

    def _get_refresh_token(self):
        with open("temp/spotify_tokens.json", "r") as file:
            tokens_dict = json.load(file)
        if "refresh_token" in tokens_dict.keys():
            refresh_token = tokens_dict["refresh_token"]
            return refresh_token

    def _create_refresh_token_file(self):
        with open("temp/spotify_refresh.txt", "w") as file:
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
    def set_user_id(self):
        endpoint = f"https://api.spotify.com/v1/me"
        headers = {
            "Authorization": "Bearer "+self.access_token,
        }
        res = requests.get(endpoint, headers=headers).json()
        return res["id"]

    def playlist_exists(self, user_id):
        endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Accept": "application/json",
            "Content-type": "application/json"
        }
        res = requests.get(endpoint, headers=headers).json()
        for playlist in res["items"]:
            if playlist["name"] == self.playlist:
                playlist_id = playlist["id"]
                return playlist_id
        return False

    def get_tracks_in_playlist(self, playlist_id):
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        payload = {
            "fields": "items(track(uri)),next",
        }
        res = requests.get(endpoint, headers=headers, params=payload)
        res = res.json()
        if res["items"]:
            track_list = res["items"]
            while res["next"]:
                next_page_res = self.add_tracks_on_next_page(res["next"])
                if next_page_res["items"]:
                    track_list += next_page_res["items"]
                res = next_page_res
            playlist_existing_track_uris = [track["track"]["uri"] for track in track_list]
            return playlist_existing_track_uris

    def add_tracks_on_next_page(self, next_link):
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        res = requests.get(next_link, headers=headers)
        return res.json()

    def create_playlist(self, user_id):
        endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        playlist_data = {
            "name": self.playlist,
            "description": "Spotify Playlist synced with Youtube",
            "public": "false"
        }
        res = requests.post(endpoint, headers=headers, json=playlist_data)
        playlist = res.json()
        return playlist["id"]

    def find_tracks_on_spotify(self, artist_track_pairs):
        track_uris = []
        tracks_not_found = []

        for artist,track in artist_track_pairs:
            res = self._send_search_request(f"?q={artist}%20{track}")
            if res["tracks"]["items"]:
                if self._track_details_correct(res["tracks"]["items"][0], artist, track):
                    track_uri = res["tracks"]["items"][0]["uri"]
                    track_uris.append(track_uri)
                else:
                    tracks_not_found.append([artist, track])
            else:
                tracks_not_found.append([artist, track])

        return track_uris, tracks_not_found

    def _track_details_correct(self, track_item, artist_name, track_name):
        artist_count = 0
        if (track_name.lower() in track_item["name"].lower()):
            for artist in track_item["artists"]:
                if artist_name.lower() == artist["name"].lower():
                    artist_count+=1
            if artist_count > 0:
                return True
        return False

    def _send_search_request(self, query):
        endpoint = f"https://api.spotify.com/v1/search"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        track_data = {
            "type": "track",
            "limit": 1
        }
        res = requests.get(endpoint+query, headers=headers, params=track_data)
        return(res.json())

    def group_track_uris(self, track_uris, delete=False):
        limit_per_request = 100
        grouped_track_uris = []
        tracks_counter = 0
        track_list_index = 0

        for track_uri in track_uris:
            if tracks_counter == 0:
                grouped_track_uris.append([])
            elif tracks_counter % limit_per_request == 0:
                grouped_track_uris.append([])
                track_list_index+=1
            if delete:
                grouped_track_uris[track_list_index].append({"uri":track_uri})
            else:
                grouped_track_uris[track_list_index].append(track_uri)
            tracks_counter+=1
        return grouped_track_uris

    def add_tracks_to_playlist(self, grouped_track_uris, playlist_id):
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        for track_uri_list in grouped_track_uris:
            tracks_data = {
                "uris": track_uri_list
            }
            res = requests.post(endpoint, headers=headers, json=tracks_data)

    def delete_tracks_from_playlist(self, grouped_track_uris, playlist_id):
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": "Bearer "+self.access_token,
            "Content-type": "application/json"
        }
        for track_uri_list in grouped_track_uris:
            tracks_data = {
                "tracks": track_uri_list
            }
            res = requests.delete(endpoint, headers=headers, json=tracks_data)
