import requests
import keyboard
import time
from flask import Flask, request
import webbrowser
import logging
from threading import Thread, Event
from dotenv import load_dotenv
import os
import pyperclip

load_dotenv()

exit = Event()

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

delay = 0.025

device = 'f95d5060c7e0de41cfd5fc64266bcfe84ec2fe17'

access_token = ''
refresh_token = ''
expires_in = 0
header = {'Authorization' : f'Bearer {access_token}'}

url = 'https://api.spotify.com/v1/me/player'

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

webbrowser.open(f'https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri=http://localhost:5000/&scope=user-modify-playback-state user-read-playback-state playlist-modify-private playlist-modify-public user-library-modify user-library-read user-top-read')

def skip():
    print('Controls:\n[:previous\n]:next\n\\:play/pause\nctrl + \':toggle shuffle\nctrl + l:like current song\nctrl + d:unlike current song\nctrl + =:copy access token to clipboard\nctrl + -:refresh auth token\nctrl + up:volume up\nctrl + down:volume down')
    global header
    header = {'Authorization' : f'Bearer {access_token}'}
    while True:
        if keyboard.is_pressed('ctrl') and keyboard.is_pressed(']'):
            requests.post(f'{url}/next',headers=header)
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('['):
            requests.post(f'{url}/previous',headers=header)
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('\\'):
            resp = requests.get(f'{url}',headers=header)
            try:
                resp_json = resp.json()
                if(resp_json['is_playing']):
                    requests.put(f'{url}/pause',headers=header)
                else:
                    requests.put(f'{url}/play',headers=header)
            except:
                requests.put(f'{url}/play?device_id={device}',headers=header)
                print('No active device, playing on PC') 
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('l'):
            modifyCurrent('like')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('d'):
            modifyCurrent('dislike')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('\''):
            try:
                shuffle_state = requests.get(url,headers=header).json()['shuffle_state']
                requests.put(f'{url}/shuffle?state={not shuffle_state}',headers=header)
            except:
                print('shuffle could not be toggled')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('='):
            pyperclip.copy(access_token)
            time.sleep(0.1)
            print('Access Token copied to clipboard')
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('-'):
            exit.set()
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('up arrow'):
            res = requests.get(f'{url}',headers=header).json()
            vol = res['device']['volume_percent']
            vol += 10
            if vol > 100:
                vol = 100
            requests.put(f'{url}/volume?volume_percent={vol}',headers=header)
        elif keyboard.is_pressed('ctrl') and keyboard.is_pressed('down arrow'):
            res = requests.get(f'{url}',headers=header).json()
            vol = res['device']['volume_percent']
            vol -= 10
            if vol < 0:
                vol = 0
            res = requests.put(f'{url}/volume?volume_percent={vol}',headers=header)
        time.sleep(delay)

#doesn't work, pls fix
def refresh():
    global access_token
    global refresh_token
    global expires_in
    global header
    while True:
        exit.wait(expires_in)
        print('Auth token expired\nRequesting a new one!')
        auth_payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        auth_response = requests.post('https://accounts.spotify.com/api/token', data=auth_payload)
        exit.clear()
        try:
            json = auth_response.json()
            # print(f'Old Access Token:{access_token}')
            access_token = json['access_token']
            header = {'Authorization' : f'Bearer {access_token}'}
            # print(f'New Access Token:{access_token}')
            expires_in = json['expires_in']
            # print('refresh succeeded')
        except:
            print('refresh failed')


#this method is very slow
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
    global header
    player = requests.get('https://api.spotify.com/v1/me/player', headers=header)
    try:
        player_json = player.json()
    except:
        print('something went wrong with the like/dislike')
        pass
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
