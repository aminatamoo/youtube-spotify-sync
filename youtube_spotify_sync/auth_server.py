from flask import Flask, render_template, request, jsonify, redirect, url_for
import youtube_spotify_sync.app_secrets as app_secrets
import string
import requests
import random
import sys
import pkce

app = Flask("MyApp")
code_verifier = pkce.generate_code_verifier(length=128)
with open('temp/youtube_code.txt', 'a') as file:
    file.write(f"{code_verifier}\n")

def generate_state():
    letters = string.ascii_letters
    numbers = string.digits
    chars = letters + numbers

    return "".join(random.choice(chars) for i in range(16))

def get_spotify_auth_url():
    state = generate_state()
    endpoint = "https://accounts.spotify.com/authorize"
    payload = {
        "client_id"  : app_secrets.spotify_client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:5000/callback",
        "state": state,
        "scope": "playlist-read-collaborative playlist-modify-private playlist-read-private",
        "show_dialog": "false"
    }
    res = requests.head(endpoint, params=payload)
    return res.url

def get_youtube_auth_url():
    state = generate_state()
    code_challenge = pkce.get_code_challenge(code_verifier)
    endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    payload = {
        "client_id"  : app_secrets.youtube_client_id,
        "redirect_uri": "http://127.0.0.1:5000",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline"
    }
    res = requests.head(endpoint, params=payload)
    print(res.url)
    return res.url

def write_spotify_res_to_file(code, error, state):
    with open('temp/spotify_code.txt', 'w') as file:
        file.write(f"{code}\n{error}\n{state}")

def write_youtube_res_to_file(code, error):
    with open('temp/youtube_code.txt', 'a') as file:
        file.write(f"{code}\n{error}\n")

@app.route("/",methods=['GET'])
def index():
    if request.args.get('error'):
        code = None
        error = request.args.get('error')
        write_youtube_res_to_file(code, error)
        return redirect("https://youtube.com")
    elif request.args.get('code'):
        code = request.args.get('code')
        error = None
        write_youtube_res_to_file(code, error)
        return redirect("https://youtube.com")
    spotify_auth_url=get_spotify_auth_url()
    return render_template('index.html', spotify_auth_url=spotify_auth_url)

@app.route("/callback",methods=['GET'])
def callback():
    youtube_auth_url=get_youtube_auth_url()
    if request.args.get('state') and request.args.get('error'):
        code = None
        error = request.args.get('error')
        state = request.args.get('state')
        write_spotify_res_to_file(code, error, state)
        return render_template('callback.html', youtube_auth_url=youtube_auth_url)
    elif request.args.get('state') and request.args.get('code'):
        code = request.args.get('code')
        error = None
        state = request.args.get('state')
        write_spotify_res_to_file(code, error, state)
        return render_template('callback.html', youtube_auth_url=youtube_auth_url)
    return render_template('callback.html', youtube_auth_url=youtube_auth_url)
