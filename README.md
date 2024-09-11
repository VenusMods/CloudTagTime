# CloudTagTime
"To determine how you spend your time, TagTime literally randomly samples you. At random times it pops up and asks what you're doing right at that moment. You answer with tags."

![image](https://github.com/user-attachments/assets/b95860b8-7cf4-44ab-9dd5-1f2027ce548e)


# Installation
Windows:
--------
0. Download and run TagTime_2.0_setup.exe from the Releases page

MacOS:
--------
0. ____________________________________________________________

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
![image](https://github.com/user-attachments/assets/5521a844-4839-4350-8a20-828539ccb245)

* Search by tags and be able to edit any of your logs with ease.
* Option to replace individual tags.
* Transfer your logs from the old version to here, by just replacing log.log in the root folder of TagTime and renaming your file to log.log.

# Settings
![image](https://github.com/user-attachments/assets/e339e394-724a-4ee1-8074-5b60fe96ebd0)

* Log in to Beeminder
* Point tags to Beeminder goals in Edit Goals
* Assign a string of tags and/or comments to a number in Task Editor


* Note: If the gap is changed, it will take affect after the next ping, unless you restart the main file.

# Extra Features
* Without typing anything in the prompt, press enter, and the log editor will open.
* Enter a single double quote only (") to enter the same tags as last time.
* Enter a question mark only (?) to open up the settings from the prompt.
* Shift + Down/Up Arrow in the Log Editor will copy over the current tags line to line.
