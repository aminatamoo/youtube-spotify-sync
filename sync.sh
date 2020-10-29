#!/bin/bash

run_auth_server (){
  gunicorn -b localhost:5000 youtube_spotify_sync.entry_point:app -p gunicorn_pid -D
}

clean_up_with_gunicorn (){
  kill `cat gunicorn_pid`
  rm -f temp/*
}

clean_up (){
  rm -f temp/*
}

read -p "Provide the name of the YouTube Playlist you'd like to sync: " YOUTUBE_PLAYLIST
read -p "Provide the name of the Spotify Playlist you'd like to sync with $YOUTUBE_PLAYLIST: " SPOTIFY_PLAYLIST

if [[ -z $SPOTIFY_REFRESH_TOKEN ]] && [[ -z $YOUTUBE_REFRESH_TOKEN ]];
then
  run_auth_server
  echo Visit localhost:5000 to login to spotify and youtube and authenticate this program
  touch temp/youtube_code.txt
  until [ -s temp/spotify_code.txt ] && [[ $(wc -l <temp/youtube_code.txt) -gt 1 ]];
  do
    sleep 1
  done
  python -m youtube_spotify_sync.main "$YOUTUBE_PLAYLIST" "$SPOTIFY_PLAYLIST" 
  echo "Adding Spotify and YouTube refresh token environment variables for subsequent syncs"
  SPOTIFY_REFRESH_TOKEN=`cat temp/spotify_refresh.txt`
  YOUTUBE_REFRESH_TOKEN=`cat temp/youtube_refresh.txt`
  
  echo "export SPOTIFY_REFRESH_TOKEN=$SPOTIFY_REFRESH_TOKEN" >> ~/.bashrc
  echo "export YOUTUBE_REFRESH_TOKEN=$YOUTUBE_REFRESH_TOKEN" >> ~/.bashrc
  clean_up_with_gunicorn
else  
  python -m youtube_spotify_sync.main "$YOUTUBE_PLAYLIST" "$SPOTIFY_PLAYLIST" 
  clean_up
fi

