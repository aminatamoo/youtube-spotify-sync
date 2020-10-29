# youtube-spotify-sync
A program to sync a Youtube playlist with a Spotify Playlist

Pre-requisites:

1. Need to have a Spotify Client ID, Spotify Client Key, Youtube Client ID and Youtube Client Secret 

Setup:

1. Rename app_secrets_example.py to app_secrets.py
2. Add Spotify Client ID, Spotify Client Key, Youtube Client ID and Youtube Client Secret to app_secrets.py and save

Once you're set up run sync.sh script

##################################
RULES
##################################
Video title on YouTube has to have a specific format where it starts with Artist/s - Track

WHERE:

  Artist/s = an artist's name or a list of artists' names that is comma separated
  Track = Name of song THEN followed by features or an Official video tag

Examples:

  Sebastian Mikael - Rain (feat. $ean Wire) [Official Music Video]
  Mario - Pretty Mouth Magick (Official Video)
  Beyoncé - Superpower ft. Frank Ocean
  Frank Ocean - Self Control
  Frank Ocean - There Will Be Tears - Download & Lyrics

###################################
Authentication
###################################

When you first run this program you will need to login in and give this app permission to access your YouTube and Spotify accounts' data. However, once you have given this app access, you won't be asked to provide permission again as a SPOTIFY_REFRESH_TOKEN and YOUTUBE_REFRESH_TOKEN will be saved to your environment variables and used to access your data.

If you want to switch the Spotify or YouTube accounts this app has access to you'll need to delete the SPOTIFY_REFRESH_TOKEN and YOUTUBE_REFRESH_TOKEN from ~/.bashrc and provide this app with permission to access data associated with the new accounts. 
