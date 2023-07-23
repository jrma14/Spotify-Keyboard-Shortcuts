# Spotify Keyboard Shortcuts
Creates keyboard shortcuts to preform various actions on spotify.

Ever get annoyed of needing to switch windows just to find spotify just to skip the current song? This script fixes that issue. It allows you to set keyboard shortcuts to do various different tasks on spotify, without the need of switching windows.

# How to create an executable
Make sure you have pyinstaller installed
```cmd
pip install pyinstaller
```
then run
```cmd
pyinstaller --onefile skip.py
```

# Running the script
To run, you can just double click, or open the folder it's in with a terminal and run the executable from there, this is also how you add the flags described below.

Make sure there is a .env file in the same directory as the executable created in the dist folder created after running the command above
the .env should look like as follows
```
CLIENT_ID = <your spotify client id>
CLIENT_SECRET = <your spotify secret>
DEVICE_ID = <optional - the spotify id of the device you want to control>
```
You can get the device id above by running the python script with the --debug flag and pressing ctrl + 0, which will copy your current device id to the clipboard
## Options
Running the script with -h or --help will also show this
```
usage: skip.py [-h] [-d] [-v] [--controls-file CONTROLS_FILE]

This script allows for global keybindings to control spotify player using the spotify API

options:
  -h, --help            show this help message and exit
  -d, --debug           Enable debug mode
  -v, --version         Print current version
  --controls-file CONTROLS_FILE
                        A json file defining the controls
```

# Actions
```
next: skip to the next song
previous: go to the previous song/restart current song
play/pause: toggle play
like: like the current song
dislike: removes like from the current song
shuffle: toggles shuffle
volume_up: increases the volume by 10
volume_down: decreases the volume by 10
copy: copies the authentication token to clipboard *only available in debug
refresh: refreshes the authentication token *only available in debug
deviceID: copies the current device id to the clipboard *only available in debug
```
# Controls
The controls file is a json file formatted as in this repo, or as follows.

The key to each array is the name of the command as shown above, case sensitive. The strings in each array are the keycodes for the keys you wish to be pressed in order to run that command. 

The all is for every command, so in the example below, ctrl must be held in order for any other command to be run. So next is ctrl + right.
```json
{
    "all": [
        "ctrl"
    ],
    "next": [
        "right"
    ],
    "previous": [
        "left"
    ],
    "play/pause": [
        "\\"
    ],
    "like": [
        "l"
    ],
    "dislike": [
        "d"
    ],
    "shuffle": [
        "'"
    ],
    "volume_up": [
        "up"
    ],
    "volume_down": [
        "down"
    ],
    "copy": [
        "="
    ],
    "refresh": [
        "-"
    ]
}
```