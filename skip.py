import requests
import keyboard
import time
from flask import Flask, request
import webbrowser
import logging
from threading import Thread
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

delay = 0.01

access_token = ''
refresh_token = ''
expires_in = 0

url = 'https://api.spotify.com/v1/me/player'

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

webbrowser.open(f'https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:5000/&scope=user-modify-playback-state user-read-playback-state playlist-modify-private playlist-modify-public user-library-modify user-library-read')

def skip():
    print('Controls:\n[:previous\n]:next\n\\:play/pause\nctrl + \':toggle shuffle\nctrl + l:like current song\nctrl + d:unlike current song')
    header = {'Authorization' : f'Bearer {access_token}'}
    while True:
        if keyboard.is_pressed(']'):
            requests.post(f'{url}/next',headers=header)
        elif keyboard.is_pressed('['):
            requests.post(f'{url}/previous',headers=header)
        elif keyboard.is_pressed('\\'):
            resp = requests.get(f'{url}',headers=header)
            resp_json = resp.json()
            if(resp_json['is_playing']):
                requests.put(f'{url}/pause',headers=header)
            else:
                requests.put(f'{url}/play',headers=header) 
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('l'):
            modifyCurrent('like')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('d'):
            modifyCurrent('dislike')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('\''):
            shuffle_state = requests.get(url,headers=header).json()['shuffle_state']
            requests.put(f'{url}/shuffle?state={not shuffle_state}',headers=header)
        time.sleep(delay)

def refresh():
    global access_token
    global refresh_token
    global expires_in
    while True:
        time.sleep(expires_in)
        print('Auth token expired\nRequesting a new one!')
        auth_payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        auth_response = requests.post('https://accounts.spotify.com/api/token', data=auth_payload)
        json = auth_response.json()
        access_token = json['access_token']
        expires_in = json['expires_in']


def fliplikeCurrent():
    header = {'Authorization' : f'Bearer {access_token}'}
    player = requests.get('https://api.spotify.com/v1/me/player', headers=header)
    player_json = player.json()
    id = player_json["item"]["id"]
    track_url = 'https://api.spotify.com/v1/me/tracks?limit=50'
    like_url = f'https://api.spotify.com/v1/me/tracks/?ids={player_json["item"]["id"]}'
    while track_url != None:
        saved = requests.get(track_url,headers=header)
        saved_json = saved.json()
        track_url = saved_json['next']
        for item in saved_json['items']:
            # print(item)
            if id == item['track']['id']:
                requests.delete(like_url,headers=header)
    requests.put(like_url,headers=header)

def modifyCurrent(method):
    header = {'Authorization' : f'Bearer {access_token}'}
    player = requests.get('https://api.spotify.com/v1/me/player', headers=header)
    player_json = player.json()
    like_url = f'https://api.spotify.com/v1/me/tracks/?ids={player_json["item"]["id"]}'
    if method == 'like':
        requests.put(like_url,headers=header)
    else:
        requests.delete(like_url,headers=header)

@app.route('/',methods=['GET'])
def auth():
    args = request.args
    auth_payload = {
    'grant_type': 'authorization_code',
    'code': args['code'],
    'redirect_uri': 'http://localhost:5000/',
    'client_id': client_id,
    'client_secret': client_secret,
    }    
    auth_response = requests.post('https://accounts.spotify.com/api/token', data=auth_payload)
    # print(auth_response.json())
    json = auth_response.json()
    global access_token
    global refresh_token
    global expires_in
    access_token = json['access_token']
    refresh_token = json['refresh_token']
    expires_in = json['expires_in']
    # print(access_token)  
    thread = Thread(target=skip)
    thread.start()
    ref = Thread(target=refresh)
    ref.start()
    return 'Success!'

app.run()