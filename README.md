# Timedivers Manager
Version manager for Helldivers 2

# Usage
1. In the Steam properties for Helldivers 2, disable all DLC and set the game to only update when you launch it.
2. Create a new folder anywhere for timediversverman.exe
3. Download the latest windows-x64 version of the [DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases) and place the exe in the same folder.
4. Open Microsoft Edge, go to [steamdb.info](https://steamdb.info) and log into your steam account. Make sure to check 'Remember Me'.
5. Run timediversverman.exe and update the list.
6. Browse and navigate to the Common folder that already contains Helldivers 2.
7. Enter your steam username, choose whether or not to remember your password, and then download a version.

# Things to Know
1. Always check for game updates on Steam. If an update comes out, make sure that the Steam version is active in the version manager and then download the update. Updates cannot be easily skipped, and downloading an update while an old version is active will cause issues.
2. The scraping process for updating the list may appear stuck at some points. If it appears stuck for longer than a minute or two, close everything and try again.
3. This program does not prompt you for, or store, your password. That is all handled with the DepotDownloader and choosing to remember your password just passes the remember-password flag to it.
4. The April 16th version, 1.000.203, is currently the oldest version that can still connect to the servers. Any versions older than that will not continue past the title screen.

# Building
1. Install Python 3 from [python.org](https://python.org)
2. Install the dependencies with `pip install -r requirements.txt`
3. Run `pyinstaller --onefile --clean --noconsole --add-data "meridia.ico;." --icon=meridia.ico timediversverman.py`

<img width="525" height="407" alt="Control-V" src="https://i.imgur.com/pyFDqow.png"/>
