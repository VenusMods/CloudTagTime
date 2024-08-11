# CloudTagTime
"To determine how you spend your time, TagTime literally randomly samples you. At random times it pops up and asks what you're doing right at that moment. You answer with tags."

![Screenshot 2024-08-11 030727](https://github.com/user-attachments/assets/12ba5127-96fd-4bc0-baf5-3cf5b72af996)

# Installation
Windows:
--------
0. Download and run TagTime_1.0_setup.exe

Linux:
------
Currently not tested, I made everything cross-platform compatable so correct me if i'm wrong, but you should be able to get it running by:

0. Cloning this GitHub repo
1. create a python virtual environment in the TagTime directory (python 3.8+)
2. pip installing requirements.txt
3. running "./tagtime.py &"

# Cloud Features
* Sign in with Google
* Export your Log from the cloud database in log viewer
* Save your log to the database after every ping

# Log Viewer/Editor
![Screenshot 2024-08-11 031219](https://github.com/user-attachments/assets/8049516d-af14-437d-9d1c-50498729cda8)

* Search by tags and be able to edit any of your logs with ease.
* You should be able to transfer your logs from the old version to here, by just replacing log.log in the root folder of TagTime and renaming your file to log.log.

# Settings
![Screenshot 2024-08-11 030835](https://github.com/user-attachments/assets/789584d0-8287-4987-a6fa-8e0f018b5b84)

* Note: If the gap is changed, it will take affect after the next ping, unless you restart the main file.

# Extra Features
* Without typing anything in the prompt, press enter, and the log editor will open.
* Enter a single double quote only (") to enter the same tags as last time.
* Enter a question mark only (?) to open up the settings from the prompt.
