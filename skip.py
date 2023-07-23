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
import argparse
from colorama import Fore
import sys
import json
import platform

# TODO comments for documentation

load_dotenv()

VERSION = '0.6'

exit = Event()

app = Flask(__name__)

debug = False

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

delay = 0.025

device = os.environ.get('DEVICE_ID') if os.environ.get('DEVICE_ID') != None else ''

access_token = ''
refresh_token = ''
expires_in = 0
header = {'Authorization' : f'Bearer {access_token}'}

REDIRECT = 'http://localhost:5000/'

baseUrl = 'https://api.spotify.com/v1/me/player'

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

ALL_DEFAULT = ['ctrl']

debugActions = ['copy','refresh','deviceID']

controls = {}
controls_file = "controls.json"

# TODO maybe fix padding if too long
# prints out the controls of the script
def printControls():
    global debug
    if debug: print(Fore.YELLOW + "Debug mode is enabled" + Fore.RESET)
    tableHeader = '''------------------------------------------------
|                  APP CONTROLS                |
------------------------------------------------'''
    table = ""
    tableFooter = '------------------------------------------------'
    for action in actions:
        control = ' + '.join(controls.get('all',ALL_DEFAULT)) + ' + ' + ' + '.join(controls.get(action['action'],action['default']))
        table += f"| {control:21}| {action['description']:21} |\n"
    print(tableHeader)
    print(table, end='')
    print(tableFooter)

def next():
    global debug
    requests.post(f'{baseUrl}/next',headers=header)

def previous():
    global debug
    requests.post(f'{baseUrl}/previous',headers=header)

def playPause():
    global debug
    resp = requests.get(f'{baseUrl}',headers=header)
    try:
        resp_json = resp.json()
        if(resp_json['is_playing']):
            requests.put(f'{baseUrl}/pause',headers=header)
        else:
            requests.put(f'{baseUrl}/play',headers=header)
    except:
        res = requests.put(f'{baseUrl}/play?device_id={device}',headers=header)
        if res.status_code != 204:
            exit.set()
        else:
            res = requests.put(f'{baseUrl}/play?device_id={device}',headers=header)
        if debug: print('No active device, playing on PC')

def shuffle():
    global debug
    try:
        shuffle_state = requests.get(baseUrl,headers=header).json()['shuffle_state']
        requests.put(f'{baseUrl}/shuffle?state={not shuffle_state}',headers=header)
    except:
        if debug: print('shuffle could not be toggled')

def copyAccessToken():
    global debug
    pyperclip.copy(access_token)
    time.sleep(0.1)
    if debug: print('Access Token copied to clipboard')

def volume(dir):
    global debug
    res = requests.get(f'{baseUrl}',headers=header).json()
    vol = res['device']['volume_percent']
    vol = min(vol + 10,100) if dir == 'up' else max(vol - 10, 0)
    requests.put(f'{baseUrl}/volume?volume_percent={vol}',headers=header)

# *Loop to refresh the authorization token once it expires
def refresh():
    global debug
    global access_token
    global refresh_token
    global expires_in
    global header
    while True:
        exit.wait(expires_in)
        if debug: print('Requesting a new auth token!')
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
            access_token = json['access_token']
            header = {'Authorization' : f'Bearer {access_token}'}
            expires_in = json['expires_in']
        except:
            if debug: print('refresh failed')

# method to like or dislike the currently playing song
# param: method
#    'like' or 'dislike'
# likes the current song if method == 'like'
# else removes from like
def modifyCurrent(method):
    global debug
    global header
    player = requests.get('https://api.spotify.com/v1/me/player', headers=header)
    try:
        player_json = player.json()
    except:
        if debug: print(f'Could not {method} current song')
        pass
    like_url = f'https://api.spotify.com/v1/me/tracks/?ids={player_json["item"]["id"]}'
    if method == 'like':
        requests.put(like_url,headers=header)
    else:
        requests.delete(like_url,headers=header)

# listener for initial authorization
@app.route('/',methods=['GET'])
def auth():
    args = request.args
    auth_payload = {
    'grant_type': 'authorization_code',
    'code': args['code'],
    'redirect_uri': REDIRECT,
    'client_id': client_id,
    'client_secret': client_secret,
    }    
    auth_response = requests.post('https://accounts.spotify.com/api/token', data=auth_payload)
    json = auth_response.json()
    global access_token
    global refresh_token
    global expires_in
    access_token = json['access_token']
    refresh_token = json['refresh_token']
    expires_in = json['expires_in']
    thread = Thread(target=main)
    thread.start()
    ref = Thread(target=refresh)
    ref.start()
    return 'Success!'

def getCurrentDeviceId():
    try:
        resp = requests.get(f'{baseUrl}/devices',headers=header).json()
        for device in resp['devices']:
            if(str(device['name']).lower() == platform.node().lower()):
                pyperclip.copy(device['id'])
                print("Device ID copied to clipboard")
                break
    except Exception as e:
        print("Could not get current device ID")

# clears the screen
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

actions = [
    {
        'action':'next',
        'default':['right'],
        'description': "Next Track",
        'function':next
    },
    {
        'action':'previous',
        'default':['left'],
        'description': "Previous Track",
        'function':previous
    },
    {
        'action':'play/pause',
        'default':['\\'],
        'description': "Play/Pause",
        'function':playPause
    },
    {
        'action':'like',
        'default':['l'],
        'description': "Like Current Song",
        'function': lambda: modifyCurrent('like')
    },
    {
        'action':'dislike',
        'default':['d'],
        'description': "Dislike Current Song",
        'function':lambda: modifyCurrent('dislike')
    },
    {
        'action':'shuffle',
        'default':['\''],
        'description': "Toggle Shuffle",
        'function':shuffle
    },
    {
        'action':'volume_up',
        'default':['up'],
        'description': "Volume Up",
        'function':lambda: volume('up')
    },
    {
        'action':'volume_down',
        'default':['down'],
        'description': "Volume Down",
        'function':lambda: volume('down')
    },
    {
        'action':'deviceID',
        'default':['0'],
        'description':'Copy device id',
        'function':getCurrentDeviceId
    },
    {
        'action':'copy',
        'default':['='],
        'description': "Copy Auth Token",
        'function':copyAccessToken
    },
    {
        'action':'refresh',
        'default':['-'],
        'description': "Refresh Auth Token",
        'function': exit.set
    }
]

# TODO better error checking
def setControls():
    global controls
    global actions
    try:
        with open(controls_file,'r') as file:
            controls = json.load(file)
    except:
        print(Fore.RED + f"Unable to read {controls_file} ...\nUsing default controls" + Fore.RESET)
    if not debug:
        actions = [action for action in actions if not action['action'] in debugActions]

# main logic loop with all of the keyboard listeners
def main():
    setControls()
    printControls()
    global header
    header = {'Authorization' : f'Bearer {access_token}'}
    while True:
        if all(keyboard.is_pressed(key) for key in controls.get('all',ALL_DEFAULT)):
            for act in actions:
                action,default,func = act['action'],act['default'],act['function']
                if all(keyboard.is_pressed(key) for key in controls.get(action,default)):
                    func()
        time.sleep(delay)

def flask_thread():
    try:
        app.run()
    except KeyboardInterrupt:
        print('Exiting...')

# TODO add custom icon
# TODO think about adding delay to arguments
# TODO add consoleless mode/ make console a choice
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This script allows for global keybindings to control spotify player using the spotify API")
    parser.add_argument("-d", "--debug", action="store_true",help="Enable debug mode")
    parser.add_argument("-v", "--version", action="store_true",help="Print current version")
    parser.add_argument("--controls-file",dest="controls_file", default="controls.json",help="A json file defining the controls")
    args = parser.parse_args()
    controls_file = args.controls_file
    if args.version:
        print(VERSION)
    else:
        if client_id != None and client_secret != None:
            if args.debug: debug = True
            webbrowser.open(f'https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri={REDIRECT}&scope=user-modify-playback-state user-read-playback-state playlist-modify-private playlist-modify-public user-library-modify user-library-read user-top-read')
            t  = Thread(target=flask_thread)
            t.daemon = True
            t.start()
            cls()
            try:
                while True:
                    time.sleep(1)
            except:
                pass
        else:
            print(Fore.RED + "Environment variables not found" + Fore.RESET + "\nTry creating a .env file in the same directory with a CLIENT_ID and CLIENT_SECRET\nRead the README for more information",file=sys.stderr)