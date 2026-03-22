# Timedivers Manager
Version manager for Helldivers 2

# Usage
1. In the Steam properties for Helldivers 2, disable all DLC and set the game to only update when you launch it.
2. Opt out of any betas and ensure you're using the default version.
3. Create a new folder anywhere and place timediversverman.exe into it. You can grab that from the [releases](https://github.com/leem919/timedivers-manager/releases) or build it yourself.
4. Download the latest windows-x64 version of the [Depot Downloader](https://github.com/SteamRE/DepotDownloader/releases) and place the exe in the same folder.
5. Open Microsoft Edge, go to [steamdb.info](https://steamdb.info) and log into your steam account. Make sure to check 'Remember Me'.
6. Run timediversverman.exe and update the list.
7. Browse and navigate to the Common folder that contains the Helldivers 2 folder. (Don't select the Helldivers 2 folder itself)
8. Enter your steam username, choose whether or not to remember your password, and then download a version.

# Things to Know
1. If you're unable to update your list, or don't want Edge to be restarted in debug mode, I've uploaded a manifests.json file in the v1.0 release that was scraped as of 9/21/2025. It can be placed in the same folder as the exe.
2. Always check for game updates on Steam. If an update comes out, make sure that the Steam version is active in the version manager and then download the update. Updates cannot be easily skipped, and downloading an update while an old version is active will cause issues.
3. Unfortunately, most versions of the game won't be able to connect to the servers anymore after a recent change in the API.
4. Your Helldivers 2 game files, along with any downloaded versions, will all be stored in separate folders with names indicating what version they are. A junction point will then be used in place of the original Helldivers 2 folder to point to game versions of your choosing. Selecting "Revert Folders" will undo this and quit out.
5. It is recommended to switch back to the steam version when not actively playing for a while in case steam does a file check.
6. The scraping process for updating the list may appear stuck at some points. If it appears stuck for longer than a minute or two, close everything and try again.
7. This program does not prompt you for, or store, your password. That is all handled with the Depot Downloader and choosing to remember your password just passes the remember-password flag to it.

# Steam Console
Some users have reported issues with the Depot Downloader and instead used the Steam Console. I believe the main issues come from unusual ownership situations, such as game sharing on the local machine or across a steam family. As such, I've implemented a method for using the steam console with this manager in the event that the game forces an update or crashes occur before getting ingame. This should download the files in the same way they would be normally through steam. I still suggest using the Depot Downloader as it's dedicated to the functionality and generally works better.
1. Select a version and select "Use Steam Console".
2. Browse and navigate to the Content folder. It should be in the steamapps folder where steam is installed. If you have trouble finding it, you can download a depot and see where the console says the content folder is.
3. If any depots are already downloaded, they might be for a different version and should be deleted to be safe. 
4. Select "Open Steam Console" and wait for the Steam window to open and switch to the console tab.
5. Select "Copy" next to the first command, paste it into the console, and hit enter to start the download.
6. Wait for the console to say the depot download is complete, then repeat for the next two depots.
7. Once the console says they're all downloaded, refresh and then select "Import Version".
8. Wait a moment, and a confirmation window should appear.

# Building
1. Install Python 3 from [python.org](https://python.org)
2. Install the dependencies with `pip install -r requirements.txt`
3. Run `pyinstaller --onefile --clean --noconsole --add-data "meridia.ico;." --icon=meridia.ico timediversverman.py`

<img width="525" height="407" alt="Control-V" src="https://i.imgur.com/pyFDqow.png"/>
